# 电子温度、占据与能量：ABACUS v3.10.1 源码口径

适用于本地 `/mnt/e/Software/ABACUS/soucecode/abacus_v3.10.1` 的 KS-DFT 路径。
以下结论来自参数解析、占据函数和能量汇总代码；版本改变后必须重新核对。
本版本的 `smearing_sigma_temp` 转换存在约 2 倍的物理温标偏差，不能直接把该关键词数值当成实际 FD 电子温度。

## 1. 先区分物理电子温度与数值展宽

- 要计算指定电子温度下的 Fermi-Dirac 占据及电子熵，用 `smearing_method fd`（或 `fermi-dirac`）。
  `Occupy::wgauss(x,-99)` 返回 `1/(1+exp(-x))`，其中 `x=(E_F-ε)/sigma`。
  因此物理电子温度必须满足 **`sigma=k_B*T_e`，sigma 与本征能均用 Ry**。
- `gauss`/`gaussian`、`mp`/`mp2`、`cold`/`mv` 是不同的数值展宽函数。
  它们也产生名为 `E_entropy(-TS)` 的修正项，但不能将其直接解释为真实 FD 电子熵。
  将温度参数写在高斯或 MP 后面不会自动切换成 FD。
- 本版本默认是 `smearing_method gauss`、`smearing_sigma 0.015` Ry；默认并非 `fixed`。
  已确认带隙和整数填充的零温绝缘体可显式用 `fixed`；此时展宽被忽略。
- 本地参数合法性列表在 `"mp3"` 与 `"marzari-vanderbilt"` 之间漏逗号；
  `mp3`、`marzari-vanderbilt` 以及 `methfessel-paxton` 不能作为该版本的可靠输入值。
  使用上面列出的短名；不要输入拼接形成的异常字符串。

依据：`source/module_parameter/input_parameter.h:94–98`；
`source/module_io/read_input_item_elec_stru.cpp:382–414`；
`source/module_io/input_conv.cpp:465–466`；
`source/module_elecstate/occupy.cpp:29–111,231–245,428–549`。

## 2. 两个参数实际如何赋值

`smearing_sigma` 直接写入以 Ry 计的宽度；`smearing_sigma_temp` 不保存独立温度，而执行：

```cpp
para.input.smearing_sigma = 3.166815e-6 * doublevalue;
```

这是该版本的**实际转换**。这里的系数约等于 Hartree/K 的 `k_B`，
但后续 `Occupy::gweights` 直接将结果当成 Ry 宽度，并没有再乘 2。
源码自己的 SI 常数给出：

```text
k_B/Ry = K_BOLTZMAN_SI / RYDBERG_SI
       = 6.33363068565903e-6 Ry/K
sigma(T_e=4000 K) = 0.0253345227426361 Ry ≈ 0.344694 eV
```

因此，应区分两类“4000”：

| 意图或输入 | 实际 sigma（Ry） | FD 占据对应的物理温度 |
|---|---:|---:|
| 字面设置 `smearing_sigma_temp 4000` | 0.01266726 | 约 2000 K |
| 物理电子温度 4000 K，直接设 sigma | 约 0.02533452 | 约 4000 K |
| 物理电子温度 4000 K，设本版本 `smearing_sigma_temp` 约 8000 | 约 0.02533452 | 约 4000 K |

优先使用明确的 Ry 写法：

```text
smearing_method   fd
smearing_sigma    0.02533452
```

若必须用温度关键词，在**这份源码**中与上述 sigma 等价的片段为：

```text
smearing_method     fd
smearing_sigma_temp 8000
```

这里的 8000 是补偿该版本转换偏差的输入值，不是宣称体系的物理电子温度为 8000 K。
按源码 SI 常数精确反求为约 `8000.000866`；这一微小差别来自常数舍入。
升级或修补转换代码后不能继续套用倍数补偿。`smearing_sigma` 必须为正；`fixed` 是零温固定填充路径，
不能用 `fd` 加零宽度模拟零温。

依据：`source/module_io/read_input_item_elec_stru.cpp:406–413`；
`source/module_base/constants.h:42–45,80–88`；
`source/module_elecstate/occupy.cpp:64–69,237,449–463`。

## 3. 同时设置时：后出现的那一行覆盖前一行

两个不同关键词不会因同时出现而被拒绝。解析器先按 INPUT 的出现顺序收集 `readvalue_items`，
再按该顺序执行赋值；二者没有后续重置逻辑。因此：

```text
smearing_sigma      0.03
smearing_sigma_temp 4000
# 最终 sigma = 0.01266726 Ry
```

```text
smearing_sigma_temp 4000
smearing_sigma      0.03
# 最终 sigma = 0.03 Ry
```

建议只写一个以避免歧义，但不要把建议说成“程序禁止同时设置”，也不要宣称 temp 总有优先权。
同一关键词重复出现则直接报错。`OUT.<suffix>/INPUT` 会输出转换后的 `smearing_sigma`，
不会输出仅用于转换的 `smearing_sigma_temp`，可据此检查实际宽度；输出字符串有默认数值精度，
不应将其舍入值当作内部浮点精度。

依据：`source/module_io/read_input.cpp:224–237,271–299,304–318`；
`source/module_io/read_input_item_elec_stru.cpp:400–413`。

## 4. 有电子熵时，日志中的“总能”是什么

对 FD 占据，`demet = sigma * Σ wk [f ln f + (1-f) ln(1-f)] = -T_e*S_s`。
这里的 `S_s` 是由 KS 占据产生的电子熵。能量汇总已经加上 `demet`，无需另开“电子熵贡献”开关，
也不能将 `-TS` 再加一次。

| 日志项 | 源码值 | FD + 通常不显含温度的 XC 时的含义 |
|---|---|---|
| `!FINAL_ETOT_IS`、`E_KohnSham`、屏幕 `ETOT` | `etot` | 含 `-T_e*S_s` 的电子自由能 F（固定离子构型，含离子间静态能） |
| `E_entropy(-TS)` | `demet` | `-T_e*S_s`，通常非正 |
| 由日志计算 `F - E_entropy(-TS)` | `etot-demet` | 同一温度占据/密度下的内能 U；不是另算的零温总能 |
| `E_KS(sigma->0)` | `etot-demet/(2+max(0,gaussian_type))` | 程序的展宽外推估计；FD 下是 `F+TS_s/2`，不是 U，也不保证等于真实零温能 |

详细分项可设 `printe 1`；默认 `printe` 会重置到 `scf_nmax`，收敛或到上限时也会打印分项。
Ry/eV 两列必须选同一列做加减。FD 下 `S_s=-demet/T_e`（若 demet 用 eV，则熵为 eV/K）。
仅有 `!FINAL_ETOT_IS` 不证明 SCF 收敛。

依据：`source/module_elecstate/occupy.cpp:237–245,522–548`；
`source/module_elecstate/fp_energy.cpp:18–28`；
`source/module_elecstate/elecstate_print.cpp:314–343`；
`source/module_io/read_input_item_output.cpp:88–97`；
`source/module_esolver/esolver_ks_pw.cpp:793–800`。

## 5. 有限温度计算还需要什么

1. **给足空带。** 默认 `nbands` 仅为起点，温度升高时尾部占据需要更多空带。
   增加 `nbands` 直到 F、U、`-TS`、费米能以及需要的力收敛，同时检查最高带占据。
   `istate.info` 的占据列是 `wg=wk*f`，包含 k 点权重与自旋约定，不能机械地把该列当成 0–1 的 f。
   LCAO 还受 `nbands<=NLOCAL` 限制；达到上限后需检查轨道基组而不是继续增加 `nbands`。
2. **固定目标温度做数值收敛。** 测试 k 网格、截断能/轨道与 SCF 阈值时保持物理 `T_e` 和 FD 方法一致。
   增大温度可能改善迭代，却改变了物理问题；返回目标温度后必须重新收敛。
3. **电子温度与离子温度不同。** 单点 SCF 无需 MD 温控；`md_tfirst`/`md_tlast` 不能替代电子占据参数。
4. **热 XC 是独立选择。** `xc_temperature` 默认 0，代码仅对 LibXC 的 KSDT、CORRKSDT、GDSMFB 等指定热泛函
   传入 `xc_temperature*0.5` Hartree，因此该参数按 Ry 温度能标设置，且不自动跟随 smearing。
   只要求 FD 占据电子熵时不必切换热 XC。若研究包含显式温度依赖的 XC 自由能，应另核其热力学定义：
   `E_entropy(-TS)` 只给占据熵，`F-demet` 不能被直接宣称为已含全部 XC 熵修正的热力学内能。

依据：`source/module_elecstate/cal_nelec_nband.cpp:61–161`；
`source/module_io/write_istate_info.cpp:40–48,64–75`；
`source/module_parameter/input_parameter.h:82`；
`source/module_hamilt_general/module_xc/xc_functional_libxc.cpp:129–133`。

审计验证：对这份源码提取并编译未修改的 INPUT 读取函数、三个 smearing 参数注册块及 FD 占据/熵函数，
验证了两种输入顺序、4000/8000 转换、重复关键词拒绝、方法合法性和 FD 函数值。
这是关键分支验证，不是完整 ABACUS 构建或材料体系端到端计算。
