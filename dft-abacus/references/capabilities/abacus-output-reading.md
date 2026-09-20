# 输出判读：v3.10.1 的参数、收敛、能量和文件

本卡以实际写出代码为依据，适用于通常的 KS-DFT PW/LCAO 流程；特殊求解器、构建开关与任务会改变输出。先确定本次工作目录、`suffix`、`calculation`、自旋和实际时间段，避免读取旧任务结果。

## 目录和输入快照

默认输出目录为 `OUT.<suffix>/`（默认 suffix 为 `ABACUS`）；默认日志为 `running_<calculation>.log`，`out_alllog true` 时按进程写 `running_<calculation>_<rank+1>.log`。警告文件通常为 rank 0 的 `warning.log`；同时检查标准输出、标准错误和退出状态，不能假定所有异常都在 warning.log。

**`OUT.<suffix>/INPUT` 不是纯默认值清单。** `Driver::reading` 先解析输入并执行重置/合法性检查，再写当前 `Parameter` 的最终 getter 值。它可用于核对转换后的 `smearing_sigma`、求解器和参数默认重置；但写出发生在后续结构/基组初始化之前，自动计算的实际电子数、NBANDS、FFT 网格和 k 点仍应以运行阶段记录交叉核对。仅转换用途的 `smearing_sigma_temp` 不会写出，原始输入仍需保留。

依据：`source/driver.cpp:114–128`；`source/module_io/read_input.cpp:271–318`；`source/module_io/read_input_item_elec_stru.cpp:400–413`；`source/module_base/global_file.cpp:156–182`。

## 先验证状态，再取数值

1. 找到**本次最后一个对应 SCF 块**，记录最终 `Density error is ...` 与 `scf_thr_type`；relax/MD 要逐离子步检查，不能用早期某次收敛行证明后续所有步骤正常。
2. `charge density convergence is achieved` 表示程序认为 SCF 收敛；`convergence has not been achieved` 是明确失败标记。早停、到步数上限、异常退出和无效数值需单独排除。
3. `!FINAL_ETOT_IS` 由结果汇总代码写出，并没有以 SCF 收敛为前提。它的存在以及 `Total Time` 等运行尾行只能作为运行阶段的线索，不能单独当成成功条件，也不应要求某一版本的时间字符串必须恰为最后一行。
4. 验证实际使用的赝势/轨道、基组、泛函、温度/展宽、电子数、k 点和 NBANDS 与目标相符。SCF 收敛仍不能替代目标量的精度测试。

`DRHO` 类型 1 是倒空间加权残差二次型，类型 2 是无量纲实空间归一化 L1 残差；不可统一标成 Ry。`scf_ene_thr` 的 `DeltaE_womix` 和屏幕相邻迭代的 `EDIFF` 不是同一量。

依据：`source/module_io/output_log.cpp:10–21`；`source/module_esolver/esolver_ks_pw.cpp:793–800`；`source/module_esolver/esolver_ks_lcao.cpp:375`；`source/module_esolver/esolver_ks.cpp:581–600,652–657`；`source/module_elecstate/module_charge/charge_mixing_residual.cpp:8–67`。

## 能量、熵、磁矩与单位

| 输出 | 应如何读取 |
|---|---|
| `!FINAL_ETOT_IS` | eV，每个计算晶胞；值为 `etot`。FD 情形已含电子占据熵项，是所选模型的电子自由能 F。 |
| `E_KohnSham` | 同一 `etot`；分项表中列出 Ry/eV 两列，按标题取对应单位。 |
| `E_entropy(-TS)` | `demet`；FD 时为真实占据熵的 `-T_e*S_s`，gauss/MP/cold 下不能直接解释为物理电子熵。 |
| `E_KS(sigma->0)` | `etot-demet/(2+max(0,gaussian_type))`；是外推估计，不是同温内能。通常不显含温度的 XC 下同温内能为 `U=F-demet`。 |
| `E_Fermi` / `EFERMI` | 费米能或化学势；明确写 `EFERMI = ... eV` 时用 eV。其他输出可能标 Ry；two-fermi 模式应读 `E_Fermi_up/dw`。不能拿费米能与总能数值作相等核验。 |
| `TOTAL-FORCE` | 常用最终输出为 eV/Angstrom；调试路径也可能出现 Ry/Bohr 块，按实际标题取单位。只在相应计算/输出路径存在，普通单点没有力并不等于失败。 |
| `TOTAL-STRESS` / `TOTAL-PRESSURE` | 常用输出为 KBAR（1 kbar = 0.1 GPa），也有标 a.u. 的内部单位分支，必须读标题。晶胞约束、外压和任务类型会影响解释。 |
| `TMAG` / `AMAG` | 总磁矩/绝对磁化的积分，通常为每晶胞 Bohr magneton；AMAG **不是平均磁矩**。非共线还会有总磁矩三分量。 |
| `H` / `S` / `r` 矩阵 | Hamiltonian 为 Ry，overlap S 无量纲，位置矩阵通常为 Bohr；不能统一把 H 和 S 都标成 Ry。 |

有限温度的完整公式、4000 K 的本版本转换偏差、热 XC 区别见 [电子温度与能量](../finite-temperature.md)。需要逐步能量分项时可加 `printe 1`。内能差、自由能差和外推零展宽能差不能在同一张比较表中混用。

外压非零时不要混同应力输出：普通 PW/LCAO KS 的 `TOTAL-STRESS` 在扣除 `press1/2/3` 前打印，返回给优化/MD 的应力及 `MD_dump` 的 `VIRIAL (kbar)` 已扣除对应对角外压；DP 路径则在扣除后打印。MD_dump 这一量是应力张量，不是 eV 的维里，也不含离子动能项。依据：`source/module_hamilt_pw/hamilt_pwdft/stress_pw.cpp:137`；`source/module_esolver/esolver_ks_pw.cpp:783–790`；`source/module_hamilt_lcao/hamilt_lcaodft/FORCE_STRESS.cpp:832–840`；`source/module_esolver/esolver_dp.cpp:133–147`；具体标签换算见[生态卡](abacus-ml-ecosystem.md)。

依据：`source/module_elecstate/fp_energy.cpp:18–28`；`source/module_elecstate/elecstate_print.cpp:314–343,393–403`；`source/module_io/output_log.cpp:46–52,208–218,252–301`；`source/module_elecstate/magnetism.cpp:25–44,60–79`；`source/module_hamilt_pw/hamilt_pwdft/forces.cpp:415,483`；`source/module_io/cal_r_overlap_R.cpp:335–370`。

## 能级与占据

`istate.info` 按 k 点写出 band index、能级（eV）和占据；`nspin=2` 的一行还包括两个自旋通道。**占据列写的是 `wg`，即带 k 点权重与自旋约定的占据，不是原始 0–1 的 FD 函数值。** 多 k 点时不能因最高带的加权值小就断言空带足够；需结合相应权重/能级/费米能检查 FD 尾部，并做 NBANDS 收敛。

有些特殊算法不求显式本征态，不保证输出与普通对角化相同。文件缺失时检查任务、求解器、开关、输出频率、构建条件、I/O 错误及运行是否到达写出阶段，不能一律归因于“开关没开”。

`istate.info` 也是 PW `init_chg wfc` 的依赖，但该 reader 的三列格式与 nspin=2 原生五列文件不兼容；“程序自己写的文件”仍不能证明这条续算路径可用，见[静态初始化](abacus-static.md)。

依据：`source/module_io/write_istate_info.cpp:31–75`；`source/module_elecstate/occupy.cpp:231–245`。

## 常用文件及续算约束

| 开关/场景 | 主要产物及条件 |
|---|---|
| `out_chg 0`（默认） | 在选定电子步/收敛等条件下仍写 `{suffix}-CHARGE-DENSITY.restart` 二进制密度；不是彻底关闭密度输出。 |
| `out_chg 1 10` | 还写 `SPIN*_CHG.cube`，第二个整数控制电荷 cube 精度，缺省为 3。`out_chg -1` 才关闭上述电子步二进制密度写出。`out_chg 2` 不合法，首值是布尔/特殊 -1。 |
| meta-GGA 密度输出 | 对应 `SPIN*_TAU.cube` / `{suffix}-TAU-DENSITY.restart`；续算要一起检查。 |
| `out_pot 1` / `out_pot 2` | 前者写 `SPIN*_POT.cube` 有效势；后者写 `ElecStaticPot.cube` 静电势，数值为 Ry。 |
| LCAO `out_mul` | `mulliken.txt`；Mulliken 分析依赖轨道基组。 |
| LCAO `out_mat_hs` | H(k)/S(k) 矩阵族，按求解器与 k 点/自旋分支命名。 |
| LCAO `out_mat_hs2` | `data-HR-sparse_SPIN*.csr` 和 `data-SR-sparse_SPIN0.csr` 等；检查 gamma-only 等限制。 |
| LCAO `out_mat_r` | `data-rR-sparse.csr`；旧卡写的 `data-rR-tr` 不是本版本该输出的文件名。 |
| 结构优化 `out_stru` | 分步 `STRU_ION<istep>_D`；最终/当前结构路径另有 `STRU_ION_D`、`STRU_NOW.cif`，不要把普通单点强行要求为优化输出。 |
| `out_band` / `out_dos` | 按 [电子结构卡](abacus-electronic.md) 配置；带路径与 DOS 积分网格用途不同，不能默认共用一次沿路径 NSCF。 |

`init_chg file`/`auto` 在 `read_file_dir` 先尝试 `{suffix}-CHARGE-DENSITY.restart`，再尝试 cube。默认目录为 `OUT.<suffix>/`；写 `read_file_dir ./` 指向工作目录而非输出目录。迁移重启数据后应检查日志的实际读取文件名，特别防止旧二进制优先于新 cube。`file` 读取失败报错；`auto` 可退回原子初值，不能把这种回退当成已经成功续算。

本版普通 FP 路径中，LCAO Gamma-only 写出 binary 的 gamma 标志与读取电荷基组的标志不一致，`read_rhog` 会返回失败；不能只凭该文件存在证明可续算。用 `out_chg 1 10` 另存 cube，核对实际回退成功；只有不兼容 binary 时先重新生成可读的收敛密度。实现链及适用条件见[静态初始化](abacus-static.md)。

**cube 成功读入不代表文件完整、几何相容。** 本版读取器不比较 origin、晶胞或原子元数据；网格尺寸不同时会插值。读网格数值时不检查 fail/eof，合法标头后截断的数据也可能返回 true、留下零值，之后归一化并不能恢复缺失形状。因此搬运或改写文件后，独立核对网格数据数量、有限数值、晶格/原子/自旋、密度积分及来源；严格 NSCF 势复用仍用相同几何与兼容网格。依据：`source/module_io/read_cube.cpp:35–73,145–193`；`source/module_elecstate/module_charge/charge_init.cpp:61–70`。

输出 STRU 也应检查完整性：本版 PW+U 使用 `onsite_radius>0` 时需要 `NUMERICAL_ORBITAL`，但优化/MD 的 `need_orb` 写出判断未包含这一条件；若用 atomic/random 波函数初始化，输出 STRU 可能缺少轨道段。续算前按原物种顺序恢复已验证的轨道条目，见[优化](abacus-relax.md)与[MD](abacus-md.md)的源码依据。

磁性输出结构默认也不保存逐原子磁矩。`out_mul false` 时 STRU_ION/STRU_MD 可丢失 AFM/非共线初值，不能把几何 checkpoint 等同于磁态恢复；详见[磁性卡](abacus-magnetism-soc.md)。优化中间步的结构在位移之后写出，而该步能量/力在位移之前求得，JSON 也有相同时序；取训练标签时须核对构型，而非按相同编号配对，见[生态卡](abacus-ml-ecosystem.md)。

投影和波函数文件还须按[电子结构卡](abacus-electronic.md)检查本版实现限制：非 MPI 的 PDOS/PBANDS 可全零，Gamma-only 共线磁性 PDOS 下自旋可能错位；PW mem_saver=1 多 k NSCF 未保留全部波函数。文件存在和电子自洽收敛都不能单独证明这些后处理数据正确。

`out_interval` 在不同调用点控制部分离子步输出（包括该 SCF 后处理路径的密度/势，以及 MD 矩阵），不是所有日志的统一节流器。`out_app_flag` 和 `out_ndigits` 主要控制矩阵输出方式/精度，不能视为电荷 cube 或所有文件的全局设置。

依据：`source/module_io/read_input_item_output.cpp:23–60,339–360`；`source/module_esolver/esolver_fp.cpp:143–220,289–333`；`source/module_elecstate/module_charge/charge_init.cpp:41–118`；`source/module_io/read_input_item_system.cpp:653–662`；`source/module_io/write_HS_R.h:26–28`；`source/module_io/cal_r_overlap_R.cpp:455–459`；`source/module_io/output_mulliken.cpp:35`；`source/module_relax/relax_driver.cpp:102–128`。

## 交付结果

交付一张含证据位置的结果表：任务/步骤、收敛状态、残差类型与数值、F/U/外推能的明确选择、电子温度与熵、用户要求的力/应力、警告及产物路径。对无输出或未收敛项明确标记，不填造数值。

`TIME STATISTICS` 和 `MEMORY STATISTICS` 可定位模块开销，但模块记账不等于作业实际峰值内存。单独对 `mpirun` 使用 `/usr/bin/time -v` 的进程记账也不等于所有 MPI ranks 的峰值总和；要报告作业级峰值，应取调度系统或各进程的对应监测，并说明统计范围。

本次审核没有把旧文档或例子的总能/耗时当作当前体系的实测基准。
