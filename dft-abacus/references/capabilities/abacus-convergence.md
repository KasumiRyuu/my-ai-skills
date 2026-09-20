# SCF 收敛与排障：v3.10.1 源码约束

本卡处理 KS-DFT 的电子自洽迭代。结构优化或 MD 中先区分“内层 SCF 未收敛”和“外层力/晶胞/轨迹问题”；`nscf` 没有密度自洽循环，调整 mixing 不能解决其本征求解精度问题。

## 先读证据，再改参数

从现有输入、日志和 `istate.info` 获取基组、求解器、自旋、泛函、k 点、空带、展宽、初始密度与所有 `mixing_*`。保存本次 SCF 的 `DRHO`、`EDIFF`、磁矩、对角化警告及实际生效参数；无需为已有信息再次询问用户，也不必先重跑一个“默认基线”。

先排除本版已确认的执行/输入缺陷：普通串行 LCAO lapack 不回写波函数，LCAO 双网格有数据尺寸问题，`scf_thr 1d-9` 还可能被解析成 1。它们不能靠混合参数修复；按[性能](abacus-performance.md)、[精度](abacus-accuracy.md)、[输入](abacus-input-files.md)选择有效分支后再诊断 SCF。磁性初态全零及从输出 STRU 重开时，也核对[磁性卡](abacus-magnetism-soc.md)的自动初磁与逐原子值丢失条件。

密度残差是**本轮输出密度与输入密度的差**，并非简单的相邻输出密度之差。默认 PW 的 `scf_thr_type 1` 是倒空间加权二次型；默认 LCAO 的类型 2 是无量纲归一化实空间 L1 残差，阈值不能直接横向比较。普通 SCF 默认阈值分别为 `1e-9` 和 `1e-7`。`scf_ene_thr>0` 另加对 `DeltaE_womix`（eV）的要求，且只在密度已收敛、`iter>1` 时检查；这不是屏幕 `EDIFF`。

日志最终 SCF 块的 `charge density convergence is achieved` 是程序收敛标志。`!FINAL_ETOT_IS`、小 `EDIFF` 和运行结束时间都不能单独证明收敛。到 `scf_nmax` 才停但无收敛，结果不可按收敛结果交付。详见 [静态 SCF 判据](abacus-static.md) 与 [输出判读](abacus-output-reading.md)。

依据：`source/module_elecstate/module_charge/charge_mixing_residual.cpp:8–67,111–248`；`source/module_esolver/esolver_ks.cpp:553–600,652–657`；`source/module_io/output_log.cpp:10–21`。

## 按现象安排排障

| 现象 | 优先检查与可做的对照 |
|---|---|
| 残差整体持续下降但达到上限 | 看距离阈值还有多少、对角化是否足够准；预算允许时增加 `scf_nmax` 或兼容续算是合理的。不能一律禁止增加上限。 |
| 残差大幅往返或持续增长 | 排除结构/赝势/占据错误，再减小 `mixing_beta`；分开观察电荷与磁化响应，必要时尝试另一混合方法。 |
| 费米面附近占据变化大 | 检查空带、k 点和展宽；近简并绝缘体/小带隙体系也会发生，不能称为金属专属问题。 |
| 总磁矩反复跳变 | 检查初始磁矩、磁性亚稳态、`mixing_beta_mag` 和 `mixing_gg0_mag`；与电荷混合系数分别调节，不要求二者永远相等。 |
| 残差停滞并伴随本征求解警告 | 先检查求解器、对角化精度和带数；混合不是唯一干预对象。 |
| DFT+U 或 meta-GGA | 检查相应占据矩阵/动能密度路径及参数兼容性；不要给所有体系统一套 U-ramping 或 DMR 混合配方。 |

改变参数时保留原始日志、记录差异和代价，尽可能一次检验一个假设。比较磁性初态时也要记录最终磁态和能量，不以收敛步数更少作为基态正确性的证据。

## 混合参数的实际行为

- 默认 `mixing_type broyden`、`mixing_ndim 8`。`plain`、`pulay` 可做对照。历史更多不保证更稳定，也增加内存；错误历史、线性相关和不恰当 beta 不能靠无限增大 `mixing_ndim` 解决。
- `mixing_beta` 未指定时，`nspin=1` 为 0.8，`nspin=2/4` 为 0.4。磁性默认分支还将 `mixing_beta_mag` 设成 1.6、`mixing_gg0_mag` 设成 0。若只写磁化参数却省略 beta，这个默认重置会覆盖它们；要定制磁化混合时同时显式给出 `mixing_beta`，再检查输出 INPUT。
- **Kerker 压制小 G 的长波长变化，不是高频变化。** 实际滤波还包含 `max(G²/(G²+G0²),mixing_gg0_min/beta)` 下限，默认 `mixing_gg0_min 0.1`。`mixing_gg0` 在代码中按长度单位换算，不能直接等同 FFT 索引。
- `mixing_beta<=0.1` 会跳过 Kerker；所以 `beta=0.1` 与 `gg0=1` 并不代表“强 Kerker 已启用”。`mixing_gg0 0` 可明确关闭电荷预处理。孤立体系可对比开/关的收敛表现，但不能保证关闭一定更快。
- 非共线 `mixing_angle>0` 进入只对磁化模长混合的特殊分支；源码注明按 `mixing_angle=1` 实现。不能把任意正数解释为已实现的连续角度插值。
- meta-GGA 可评估 `mixing_tau true`（默认 false）；它不免除动能密度与目标量的精度检查。

依据：`source/module_parameter/input_parameter.h:100–111`；`source/module_io/read_input_item_elec_stru.cpp:422–535`；`source/module_elecstate/module_charge/charge_mixing_preconditioner.cpp:7–56,62–127`；`source/module_elecstate/module_charge/charge_mixing_rho.cpp:139–142,424–427`。

## 展宽不能偷换物理问题

先读 [电子温度、展宽与能量](../finite-temperature.md)：

- 默认是 `gauss 0.015 Ry`，不是 `fixed`。金属积分可比较 gauss、mp/mp2、cold/mv 等数值展宽和 k 网格；热电子熵计算用 FD。
- 给定物理温度时保持该温度，优先调数值求解；为启动 SCF 暂时改变温度后，必须回到目标温度重新收敛。
- `smearing_sigma` 用 Ry。本版本 `smearing_sigma_temp` 按 `3.166815e-6*T` 写入 sigma；字面 4000 对应 0.01266726 Ry，实际 FD 温度约 2000 K。物理 4000 K 优先直接写 `smearing_sigma 0.02533452`（Ry）。
- 两个不同宽度关键词同时存在时**后写覆盖先写**。推荐二选一以保证可读性，程序并非禁止共存。
- 增大 `nbands` 直至尾部占据、F、熵项和其他目标量稳定；LCAO 同时受 `NLOCAL` 限制。宽展宽收敛只是所选占据问题的数值收敛，不能仅凭宽度断言“假收敛”。

## 早停、混合重启和文件续算

`scf_os_stop` 默认 false。设 true 后，程序对最近 `scf_os_ndim` 个 `log10(DRHO)` 拟合斜率；默认窗口随 `mixing_ndim`，当斜率大于负阈值 `scf_os_thr`（默认 -0.01）时标记停滞/振荡并早停。它是趋势启发式，会把缓慢下降也判断为需要停止；不是振荡的物理证明，也不是成功收敛。对平稳下降的困难问题，按实际趋势调整或关闭它。

```text
# 可选诊断片段，合入已核验的 INPUT；不是完整体系输入
scf_os_stop  true
scf_os_thr   -0.01
scf_os_ndim  8
```

`mixing_restart` 是触发重建混合历史的残差阈值，**不是从磁盘续跑开关**。LCAO 的 `mixing_dmr` 路径要等 `mixing_restart>0` 且已发生重启后才启用。普通重启与 U-ramping 行为不同：后者在 U 未到目标时可重复重启，且 U 未收敛时不允许宣布 SCF 收敛。

DFT+U 的物理输入必须先完整设置相关轨道与 U；没有相关轨道时解析器会关闭 DFT+U/U-ramping。`uramping` 输入单位是 eV，但 LCAO 更新分支内部以 Ry 判断 `>0.01` 才执行爬坡，不能把任意微小正值当作有效爬坡步长。`mixing_restart`+`mixing_dmr`+`uramping` 是可选策略，不是所有 DFT+U 计算的必要三件套，也不应直接照搬给 PW。

文件续算使用 [静态卡的初始化步骤](abacus-static.md)：确认密度来源收敛且与当前体系兼容，设 `init_chg file` 和实际 `read_file_dir`。默认二进制密度优先于 cube。`restart_load` 是另一套 `restart/` 文件机制；不能把两者或 `mixing_restart` 混为一谈。

依据：`source/module_elecstate/module_charge/charge_mixing.cpp:193–242`；`source/module_io/read_input_item_elec_stru.cpp:615–641`；`source/module_esolver/esolver_ks_lcao.cpp:530–575,700–705,865–867`；`source/module_esolver/esolver_ks.cpp:553–598`；`source/module_io/read_input_item_exx_dftu.cpp:320–350,379–404`。

## 完成标准

交付最终 SCF 收敛证据、残差类型与数值、迭代数、实际参数差异、磁态/占据和能量定义；未收敛要清楚标明。达到收敛后按目标量做阈值/基组/k 点/空带测试，不能只把迭代收敛等同于物理可靠。

相关任务：[单点 SCF](abacus-static.md)、[输出判读](abacus-output-reading.md)、[数值精度](abacus-accuracy.md)、[结构优化](abacus-relax.md)、[MD](abacus-md.md)。本卡不引用示例收敛步数作为已验证性能结论。
