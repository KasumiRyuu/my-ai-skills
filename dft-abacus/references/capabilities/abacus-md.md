<!-- capability_id: cap.abacus.md | revision: 3 | source-audited: ABACUS v3.10.1 -->

# 分子动力学：系综、离子温度与续算

先确定力的来源（默认 `esolver_type ksdft` 为 DFT；`dp` 是外部势）和物理系综，再选择积分、控温、控压参数。`md_tfirst/md_tlast` 控制**离子温度**；电子占据由独立的 `smearing_*` 控制，不能自动认为二者相等。真实有限电子温度请读 [有限电子温度](../finite-temperature.md)，其中记录此版本 `smearing_sigma_temp` 的单位转换缺陷。

## 执行分支

`calculation md` 下 `md_type` 是字符串，没有旧版整数系综映射：

| `md_type` | 实际路径与配套参数 |
|---|---|
| `nve` | Velocity Verlet，无热浴；用于检查积分与 SCF 引入的能量漂移 |
| `nvt` + `md_thermostat nhc` | Nose–Hoover 链；`md_tfreq`、`md_tchain` |
| `nvt` + `rescaling` | 温差超过 `md_tolerance`（K）时直接速度缩放 |
| `nvt` + `rescale_v` | 每 `md_nraise` 步直接速度缩放 |
| `nvt` + `berendsen` | 每步按 `md_nraise` 控制的耦合强度缩放；不能当成严格正则涨落采样 |
| `nvt` + `anderson` | 代码拼写是 anderson；每原子每步概率 `1/md_nraise` 重抽速度，抽样温度用 `md_tlast`，不是线性变温函数 |
| `langevin` | 朗之万，阻尼时间 `md_damp`（fs），支持 `md_tfirst→md_tlast` 目标变温 |
| `npt` | 总是进入 Nose–Hoover 路径，`md_pmode iso\|aniso\|tri`、`md_pfirst/md_plast`、`md_pfreq` 等；不是把 NVT 任意 thermostat 与控压器组合 |
| `msst` | 冲击波模型，需按物理问题给 `msst_direction/vel/qmass/vis/tscale` |
| `fire` | 力驱动最小化，不是有限温平衡采样；见下文版本限制 |

NHC 不能保证任何短轨迹都已遍历正则分布；有热浴的轨迹不应以“原子动能+势能严格守恒”为验收标准。做无热浴能量漂移试验用 NVE，并保持电子温度/数值设置不变。普通 KS 的 MD 势能来自包含熵项的 etot；固定 Fermi–Dirac 电子温度时应检查 **离子动能 K + 电子自由能 F** 的漂移，不是去掉熵项后的内能 U + K。

## 参数与默认行为

| 参数 | 输入单位与默认/限制 |
|---|---|
| `md_dt` | fs，默认 1；使用正值，按最快振动尺度做步长收敛测试 |
| `md_nstep` | 默认 10；显式 0 会被改成 50，不能做 dry run；循环含初始第 0 帧，因此全新作业通常有 `N+1` 次力评估 |
| `md_tfirst/md_tlast` | K；初值哨兵 -1，未设末温时设为输入初温；NHC 要求正温 |
| `md_tfreq` | **fs⁻¹**；输入 0 时设为 `1/(40*md_dt)`，用于 NHC 热浴质量 |
| `md_pfreq` | **fs⁻¹**，不是 kbar⁻¹；输入 0 时设为 `1/(400*md_dt)` |
| `md_pfirst/md_plast` | kbar；首压默认 -1，未设末压时复制首压。NPT 应显式给目标压力，0 kbar 不等于省略 |
| `md_damp` | fs，默认 1；按目标热浴耦合时间调整 |
| `md_tchain/md_pchain` | 默认各 1；粒子链长度必须正；`md_pchain=0` 有独立处理 |
| `md_dumpfreq/md_restartfreq` | 默认 1 / 5；使用正整数，代码用取模操作 |
| `md_seed` | 默认 -1；非负值调用 `srand`，用于可记录的初速/随机过程配置 |
| `md_prec_level` | 已启用的变量晶胞精度参数，仅 NPT/MSST 保留；其他任务重置 0 |
| `msst_qmass` | 默认 1.0，必须 >0；不是无默认值。单位 g²/(mol²·Å⁴)；`msst_vel` Å/fs，`msst_vis` g/(mol·Å·fs) |

热浴/压浴的默认时间尺度是实现默认值，不是适用于所有体系的硬约束或稳定性保证。`tri` 要求输入晶格矢量矩阵严格下三角；`iso` 把 `md_pcouple` 设为 `xyz`；`aniso + md_pcouple xyz` 会退出。

`cal_force` 在 MD 中自动为 true。NPT/MSST 以及 DP/LJ MD 自动启用 `cal_stress`，其他 DFT MD 想输出应力需显式启用。`symmetry` 在 MD 中设为 0（SOC 还有后续重置），不要把空间群约化用于扰动后的非对称构型。`gamma_only` 只是 LCAO 的 Γ 点实数算法开关；大胞仍需验证 k 点误差，不能因原子数多就自动用 Γ 点。

## 初速度

- `init_vel false` 且非负 `md_tfirst`：按目标温度生成随机初速；`STRU` 的原子质量、移动标志影响动能和自由度。
- `init_vel true`：读取 STRU 中的原子速度（原子单位，约 21.877 Å/fs）。**全新作业同时给定初温时会缩放速度到该温度，不因不一致而退出**；未给初温则从速度推算初温。
- `md_tfirst < 0` 或 `md_restart true` 会自动打开 `init_vel`。恒温作业建议明确给初温和末温；只靠速度推算初温时，末温的早期默认处理不能保证随之自动更新。
- 续算不在此步骤按输入初温重缩放速度；热浴状态还从重启数据恢复。

## 冻结原子与晶胞的适用范围

- 普通公共位置/速度更新按 STRU 移动标志屏蔽分量，但 **MSST 的专用速度更新没有这个屏蔽**。部分冻结方向若有非零力，速度可重新变为非零，随后计入动能、温度和动能应力，而相应非仿射位置更新仍被阻止；不能仅凭 `m=0` 宣称 MSST 正确支持固定边界。
- NPT/MSST **不执行 relax 的 `fixed_axes` / `fixed_ibrav` 约束**。NPT 晶胞自由度由 `md_pmode` 等控制，MSST 按冲击方向伸缩；`fixed_axes abc` 不能把 NPT 变成固定胞动力学，`fixed_axes c` 也不能保证真空层不变。
- 变胞后会对所有原子重算 `tau=taud*latvec`；部分完全冻结原子仍随晶胞仿射改变笛卡尔位置，不能当作实验室坐标固定。`fixed_atoms true` 又把所有移动标志清零，普通 MD 会因无可动原子报错，不是实现固定边界的替代办法。

依据：`source/module_md/md_base.cpp:90–133`；`source/module_md/msst.cpp:100–151,251–300`；`source/module_md/md_func.cpp:41–49,185–209,448–479`；`source/module_md/nhchain.cpp:26–79,722–812`；`source/module_cell/update_cell.cpp:327–331`；`source/module_cell/read_atoms.cpp:832–843,898–902`。

## 输出与续算

`OUT.<suffix>/MD_dump` 按 `md_dumpfreq` 输出。坐标 Å、力 eV/Å、速度 Å/fs；晶格是 `LATTICE_CONSTANT`（Å）乘无量纲 `LATTICE_VECTORS`。`dump_force/dump_vel/dump_virial` 默认 true，但 **`VIRIAL (kbar)` 还要求 `cal_stress true`**。此块是压力/应力维度，不是能量单位的 virial，且不含离子动能应力；日志里的 MD Pressure 则包含动能项。此外，返回给 MD 的应力已扣除 `press1/2/3` 外压，普通 PW/LCAO KS 日志的 TOTAL-STRESS 却在扣除前打印；非零外压时两者不能直接等同。不能把该块原样交给要求 eV 维里的训练格式。`MD_dump` 本身不含能量，需要按步号关联日志能量。

续算配置与文件必须成套：

1. `md_restart true` 读取 `read_file_dir/Restart_md.dat` 的累计步数与积分器状态。默认 `read_file_dir=OUT.<suffix>`。
2. 读入目录等于当前默认输出目录时，结构读 `OUT.<suffix>/STRU/STRU_MD_<step>`；**自定义其他 `read_file_dir` 时结构读该目录直属的 `STRU_MD_<step>`**，与 Restart_md.dat 同级，不自动加 `STRU/`。此时 `stru_file` 被忽略。
3. 重启文件每 `md_restartfreq` 步写一次，并非总在最后一步额外补写；若末步不是频率倍数，只能从上一个 checkpoint 恢复。保留一致的结构、速度、积分器状态，不能跨系综随意混用 Restart_md.dat。
4. `md_nstep` 是目标**累计**步号，续算应大于已完成步号；不是本次追加步数。实现会重新评估起始 checkpoint 的力并可能再输出同一步号，拼接轨迹时去重。恒温程序按累计步号作温度插值，延长变温运行会改变温度调度，需设计清楚后再续算。
5. Langevin/Anderson 的公共 checkpoint 不保存随机数生成器状态；相同 md_seed 不能保证分段续算与一次性运行逐位一致。PW +U 使用 onsite 轨道时，还须检查 STRU_MD 保留 NUMERICAL_ORBITAL：本版输出判定未包含 onsite_radius，非 nao 初始波函数的 PW 任务需从原始 STRU 补回该块。
6. 默认 `out_mul false` 的 STRU_MD 不保存逐原子磁矩，不能把几何/积分器 checkpoint 当成完整磁态 checkpoint。AFM/非共线任务须保留目标初磁或兼容磁化密度并核对实际初始化；LCAO 的 out_mul 是分区磁矩输出，PW 则不支持该开关，详见[磁性续算](abacus-magnetism-soc.md)。

## FIRE 的 3.10.1 限制

`FIRE` 构造函数先读取输入力阈值，随后又硬编码 `force_thr=1e-3`（Ry/Bohr）；`check_force` 实际按它停止，而打印阈值仍来自用户输入。**不能承诺改 `force_thr_ev` 会改变 FIRE 停止精度。** 对指定力精度的优化优先使用 [relax](abacus-relax.md)。FIRE 仍使用公共初速度初始化，既可读速度也可通过初温生成，无须强制用户提供 STRU 速度。

FIRE 的最大力判停和速度混合还遍历**全部分量**，没有按移动标志投影。冻结方向的反作用力可阻止判停，即使可动自由度已经达到受约束极小值；不能照搬 relax 的“只检查可动梯度”来解释 FIRE。依据：`source/module_md/fire.cpp:155–205`。

## 建议流程

从 [MD 模板](../../templates/INPUT.md.tpl) 生成短程输入；先确保选定 DFT 设置的力已收敛，再检查积分稳定性、温度/压力行为和所需采样长度。不要为了加速自动放松 `scf_thr` 或改变金属电子温度；使用更松阈值须以力误差和轨迹漂移验证。交付输入、系综与电子/离子温度、时间步/累计时长、轨迹、checkpoint 位置及实际结束步号。

## 源码定位

- `source/module_md/run_md.cpp:23-126`：系综分派、含初始帧的循环、输出/checkpoint 频率。
- `source/module_parameter/md_parameter.h:11-70`；`source/module_io/read_input_item_md.cpp:23-103,279-299,334-402`：默认值与重置。
- `source/module_md/md_base.cpp:9-42,144-215`；`source/module_md/md_func.cpp:185-243,247-281,319-408,441-445`：温度、速度、输出单位和目标插值。
- `source/module_md/nhchain.cpp:9-125`、`source/module_md/verlet.cpp:50-125`、`source/module_md/langevin.cpp:86-107`、`source/module_md/msst.cpp:10-14`：各积分器语义。
- `source/module_io/read_set_globalv.cpp:25-45`、`source/module_io/read_input_item_system.cpp:186-228,587-598,653-662`：自动设置与续算路径。
- `source/module_md/md_base.cpp:9-17,225-250`、`source/module_md/langevin.cpp:72-83`、`source/module_md/verlet.cpp:136-147`：随机种子与公共 checkpoint；`source/module_md/run_md.cpp:104-118`：轨道块写出条件。
- `source/module_md/fire.cpp:9-22,75-80,154-173`：输入阈值覆盖与真实判停。
- `source/module_esolver/esolver_ks_pw.cpp:781-790`、`source/module_hamilt_lcao/hamilt_lcaodft/FORCE_STRESS.cpp:830-842`：日志应力与 MD 返回应力的外压处理时点。
- `source/module_esolver/esolver_ks_pw.cpp:725-727`、`source/module_esolver/esolver_ks_lcao.cpp:288-292`、`source/module_elecstate/fp_energy.cpp:18-28`：MD 所用 etot 包含熵项。
