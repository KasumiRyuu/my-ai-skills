<!-- capability_id: cap.abacus.magnetism-soc | revision: 3 | source-audited: ABACUS v3.10.1 -->

# 磁性、非共线与 SOC

先分清初始磁矩、总自旋差约束、局域磁矩约束和固定带占据。它们不是同一个功能。此卡核对的是 ABACUS v3.10.1 执行代码，不能把旧文档中“只有 nspin=2 才读磁矩”“SOC 无力/应力”当作本版限制。

## 自旋空间与初值

| 目标 | 设置与实际行为 |
|---|---|
| 非自旋极化 | `nspin 1`；单份总密度，不会因 STRU 写了 mag 就自动打开磁性 |
| 共线极化 | `nspin 2`；分别求 up/down，内部 k 点索引包含两套自旋通道；STRU 中逐原子 `mag` 是初始 z 磁矩 |
| 非共线、无 SOC | `noncolin true`、`lspinorb false`；自动 `nspin=4`，密度分量为总密度及 mx/my/mz |
| SOC、磁矩仅 z | `lspinorb true`、`noncolin false`；自动 `nspin=4`，保留 z 磁化 |
| SOC、任意磁矩方向 | `lspinorb true`、`noncolin true`；自动 `nspin=4` |

显式 `nspin 4` 而两个布尔开关均 false 并非“等价非磁计算”：实现仍打开 z 磁化分量，使用双分量旋量。只需共线无 SOC 时通常选 nspin=2；有特定 PW +U 路径需求时按 [高级功能](abacus-advanced-functionals.md) 选择。

STRU 元素块的磁矩提供类型默认值，坐标行 `mag` 可逐原子覆盖；共线 AFM 可在同一元素块内写 `mag 2` 与 `mag -2`。非共线可写 `mag 0 0 2`，或磁矩大小配 `angle1/angle2`。`nspin=4` 且 `noncolin=false` 会把初始 x/y 分量清零。这些是初值，SCF 可收敛到不同磁序。比较 FM/AFM 时保留相同电子温度、基组、k 点和精度，并检查最终局域/总磁矩，而非只看初值标签。

**全零磁矩不一定保留为零初值。** 若所有原子的 `abs(mag)<=1e-5`，且 `!lspinorb || noncolin`，程序对 nspin=2 自动写每原子 `mag=1`；对 nspin=4 写 `m_loc=(1,1,1)`、`mag=sqrt(3)`，却没有同步更新角度。对类型/逐原子磁矩全零且没有角度、使用 `init_chg atomic` 的非共线任务，初始密度实际按原来的零角度沿 z 构造，不能把日志的 `(1,1,1)` 当成密度方向。微小非零类型默认值还可能被 atomic_rho 的类型分支优先使用，因此应显式给出目标非零逐原子磁矩/方向并核对密度。`lspinorb true`、`noncolin false` 是不自动加磁的例外；成功读取兼容磁化密度也不等于重走 atomic 初值。此处只说明初始化，不保证最终磁态，更不能把零初磁当作非磁态约束。

依据：`source/module_cell/read_atoms.cpp:539–542,610–622,678–715,850–895`；`source/module_elecstate/module_charge/charge.cpp:325–334,509–533,572–608`；`source/module_elecstate/module_charge/charge_init.cpp:181–187`。

旋量每带占据容量与非极化两重简并不同；检查自动生成的 `nbands` 和高能尾部占据。不要机械把任意 nspin=2 任务的 nbands 乘二作为通用规则。

## SOC 前置与实际限制

- 赝势必须包含解析器识别的 `has_so` 与 j 分辨投影子信息。`lspinorb=true` 遇到 `has_so=false` 会在赝势处理返回错误并**终止**，不是悄悄忽略。此版 `has_so && tvanp` 同样在 `average_p` 中返回错误，因此不能凭“全相对论”标签就承诺 FR-USPP 可运行；优先验证实际 NC 赝势。
- `soc_lambda` 默认 1，用于缩放 SOC 赝势的分裂；它不是电子温度或磁矩幅度。要得到标量相对论平均还应按 `lspinorb` 的独立分支理解，不能把所有 `soc_lambda=0` 与无 SOC 的内部表示视为完全相同。
- `lspinorb=true` 在 `input_conv.cpp` 中把运行时 `symm_flag` **强制设为 -1**，即使 INPUT 显式写了 0 或 1；不能只把 -1 说成建议或未指定时默认。
- LCAO `nspin=4` 与 `gamma_only=true` 明确互斥；仍可用 `gamma_only false` 加单个 Γ k 点，这与实数 Γ 算法不同。
- PW 与 LCAO 均有自旋器/SOC 的非局域力和应力执行分支；**不能笼统禁止 SOC relax/MD/应力**。但任意泛函、赝势、设备及额外修正的组合并非自动都可用。确定组合后核查求解器分支，必要时以能量有限差分验证力；例如本版 meta-GGA 与 `nspin=4` 在 XC 检查中直接退出。

## 约束与输出

- `nupdown` 用于共线 `nspin=2` 的总电子数差。**显式写 `nupdown 0` 也会开启双费米能模式**，这和省略参数、让总磁化自行优化不同；非零 nupdown 在 nspin=1 被拒绝。保证上下自旋电子数非负并有足够能带。该机制不约束各原子磁矩方向/大小。
- `ocp 1` / `ocp_set` 固定占据是另一种电子态构造，需按自旋、k 点和能带顺序及权重检查电子数。不要把 `ocp_set` 简单当作各带整数电子数列表；见 [电子结构](abacus-electronic.md) 与 [收敛](abacus-convergence.md)。
- `sc_mag_switch true`（DeltaSpin 局域自旋约束）在本版 `ReadInput::item_others` **无条件 WARNING_QUIT**，提示功能不稳定；不能根据存在的模块/历史示例承诺用户可直接开启。不要修改软件源码跳过检查来冒充本版支持。
- `TMAG` 是总磁化；`AMAG` 是磁化密度绝对值的空间积分，**不是每原子平均磁矩**。nspin=4 时总磁化是向量。`out_mul` 的原子分区磁矩是投影/分区结果，不能与连续磁化密度积分不加说明地混用。
- 从密度续算时，nspin=2 的分量是 up/down，nspin=4 的分量是总密度和磁化分量。不要把文件数相同或文件能读入等同于表示相同；按 [输出与续算](abacus-output-reading.md) 核对二进制/cube 的实际读取优先级、分量与成功日志。

**几何输出不自动保存磁态。** 默认 `out_mul false` 时，relax 的 `STRU_ION_D` 和 MD 的 `STRU_MD_*` 不写逐原子磁矩；原输入有逐原子 `mag`/角度时，类型默认磁矩还已被清零。同元素 AFM 的 `mag +2/-2` 因而可能变成“类型零、无逐原子 mag”，用这个结构和 atomic 初值重开会触发上述同向加磁。恢复几何后须补回目标初磁/方向，或成功复用适配的磁化密度。LCAO `out_mul true` 写的是 Mulliken 分区磁矩，MD 更新还受输出间隔影响，不是原初值的原样备份；PW 会拒绝 out_mul，不能靠这个开关解决。

依据：`source/module_cell/read_atoms.cpp:844–847,1031–1054`；`source/module_relax/relax_driver.cpp:103–128`；`source/module_md/run_md.cpp:110–117`；`source/module_parameter/input_parameter.h:330`；`source/module_io/read_input_item_output.cpp:147–155`；`source/module_esolver/esolver_ks_lcao.cpp:1157–1189`。

磁性后处理还须读[电子结构卡](abacus-electronic.md)：Gamma-only nspin=2 的 PDOS 下自旋能级索引有缺陷；LCAO nspin=4 的 Berry 电子相位未实现；PW 部分电荷和部分实空间波函数导出也不能直接当成完整旋量密度。这些限制不等于禁止正常磁性 SCF 或 SOC 力/应力计算。

最小非共线 SOC 片段（仍需完整 STRU、KPT、赝势与收敛参数）：

```text
noncolin          true
lspinorb          true
gamma_only        false
symmetry          -1
```

## 源码定位

- `source/module_io/read_input_item_elec_stru.cpp:257-277,305-320,538-564,670-687`；`source/module_io/read_set_globalv.cpp:66-89`：nupdown、nspin、Γ 限制和磁化模式。
- `source/module_cell/read_atoms.cpp:678-751`：磁矩表示与 z 分量约束。
- `source/module_cell/read_pp.cpp:123-150`、`source/module_elecstate/read_pseudo.cpp:258-285`：SOC 赝势检查、错误传播。
- `source/module_io/input_conv.cpp:430-453`：EXX/SOC 运行时对称性。
- `source/module_hamilt_pw/hamilt_pwdft/fs_nonlocal_tools.cpp:452-531,739-820`：旋量非局域 stress/force；`source/module_hamilt_lcao/hamilt_lcaodft/operator_lcao/nonlocal_force_stress.hpp:230-363`：LCAO SOC 力/应力分支。
- `source/module_hamilt_general/module_xc/xc_functional.cpp:318-345`：meta-GGA + nspin=4 限制。
- `source/module_io/read_input_item_other.cpp:16-43`：禁用 sc_mag_switch。
- `source/module_elecstate/magnetism.cpp:19-79`：总磁化和绝对磁化定义；`source/module_elecstate/cal_nelec_nband.cpp:61-153`：能带数处理。
