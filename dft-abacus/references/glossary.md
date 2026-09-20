# 关键术语与参数口径（v3.10.1）

本表是导航和易错点索引，具体参数组合读链接中的任务说明；代码入口汇总于[源码依据](source-audit.md)。

## 输入与基组

| 术语 | 本版口径与使用要点 |
|---|---|
| `INPUT` / `INPUT_PARAMETERS` | 参数名转小写匹配；重复同名参数报错。参数值行用 `getline` 读取，不能套用“每行 150 字符截断”的旧说法。标记前/注释行的跳过逻辑另有长度限制，宜保持简短。[输入](../inputs/SKILL.md) |
| 数字格式 | 浮点指数用 e/E；整数用十进制整数。部分 parser 只取数值前缀，`1d-9` 可读成 1，整数 `1e2` 可读成 1；不直接写算式。[输入](capabilities/abacus-input-files.md) |
| `ntype` | 默认 0 时从 STRU 的物种条目计数，非零值与计数不符会报错；不是原子总数。 |
| `STRU` | `LATTICE_CONSTANT` 用 Bohr；晶格矢量乘该尺度。`Direct` 为无量纲分数坐标；`Cartesian` 用该晶格常数，`Cartesian_angstrom` 才是 Å。[输入格式](capabilities/abacus-input-files.md) |
| `basis_type` | 普通计算选 `pw` 或 `lcao`；`lcao_in_pw` 是受限路线，不当作通用第三套流程。LCAO 需要数值轨道且仍有积分网格精度问题。[精度](../accuracy/SKILL.md) |
| 赝势、UPF、SG15/PseudoDojo/APNS、`.orb` | 赝势提供价电子和势等数据；轨道有自身完备性和生成条件。文件名不能证明相配，显式指定泛函也不能消除赝势模型不一致。[数据选型](capabilities/abacus-accuracy.md) |
| `ecutwfc` / `ecutrho` | Ry。解析默认分别为 PW 50 / LCAO 100 Ry 和 4×ecutwfc；ecutrho/ecutwfc 小于 4（超出代码容差）报错。默认值不保证收敛，LCAO 增大截断不增加轨道数。 |
| 双网格 / `ndz` | 本版 LCAO 平滑/稠密网格混用可产生越界；手工仅增大 ndz 又可能不触发双网格。输入数值不证明实际截断，见[精度卡](capabilities/abacus-accuracy.md)。 |
| `KPT` | 包含网格、显式点或路径；使用 `kpoint_file` 指定时应给实际文件名。`KLINES` 不是会自动识别的特殊文件名。[电子结构](../electronic/SKILL.md) |
| `gamma_only` | LCAO Γ 优化路径会重写所选 KPT；PW 中该开关被重置为 false，同时写 Γ 网格，并非实现 PW Γ 优化。PW 推荐显式 1×1×1 Γ KPT。 |
| `kspacing` | 单位 Bohr⁻¹；接受一个或三个值，须全零或全正。正值生成并覆盖 Γ 中心网格，不能与手工能带路径混用；有效 LCAO gamma_only 优先。[采样](capabilities/abacus-accuracy.md) |
| `suffix` / `read_file_dir` | 前者决定常规输出目录，后者决定读取旧状态的位置；改变 suffix 也可能影响按 suffix 命名的二进制密度，需核对具体文件。 |

## 电子态、温度和 SCF

| 术语 | 本版口径与使用要点 |
|---|---|
| `calculation` | 工作流类型，如 scf、relax、cell-relax、md、nscf。变更时检查整个文件依赖与参数组合，不只是改一行。 |
| `esolver_type` / `ks_solver` | 能量求解路线与电子求解方法是不同层次。ksdft/sdft/ofdft/tddft/lj/dp 等有独立条件；PW、LCAO 求解器不可任意互换。[静态](../static/SKILL.md)、[高级](capabilities/abacus-advanced-functionals.md) |
| `ks_solver lapack` | 普通非 MPI LCAO 的本版实现未回写波函数，nbands 小于 nlocal 时还会越界写本征值；不能因默认选择就认为可靠。不泛化到其他算法的同名后端。[性能](capabilities/abacus-performance.md) |
| `dft_functional` | 默认沿用赝势的 XC 标识，显式值选择运行的 XC 计算；它不重新生成赝势。核对编译库支持与实际模型。 |
| `smearing_method` | 默认 `gauss`，不是 fixed。物理电子温度用 `fd`；Gaussian/MP/cold 是数值积分展宽，其修正不能直接作为物理电子熵。[完整温度说明](finite-temperature.md) |
| `smearing_sigma` | 占据函数用的能量宽度，Ry；FD 时对应物理 kBT。4000 K 约为 0.0253345 Ry。 |
| `smearing_sigma_temp` | 本版将输入乘 `3.166815e-6` 写入同一个 sigma，约为正常 Ry 温度换算的一半。两个不同 sigma 关键词同时出现时后写者覆盖；不要据名字直接等同于实际电子温度。 |
| `xc_temperature` | 热交换关联泛函的独立参数，不随展宽温度自动同步；普通 PBE+FD 的占据熵与热 XC 是不同模型。[温度说明](finite-temperature.md) |
| `nbands` / `nbands_mul` | 决定计算带数及默认带数的倍率；默认公式有整数取整和自旋分支，LCAO 还受轨道维数上限约束。高温必须检验最高带占据和能量/熵随带数的收敛，不能只满足“多于占据带”。[SCF 卡](capabilities/abacus-static.md) |
| `nelec` / `nelec_delta` / `nupdown` | 总电子数、电子数增量与共线自旋电子数差是不同量；默认 nelec 从赝势价电子统计，nelec_delta 再改变它。共线计算显式 `nupdown 0` 也会启用双费米能，和省略该参数不同；带电体系的边界条件及修正需另评估。[磁性](capabilities/abacus-magnetism-soc.md) |
| `nspin` / `noncolin` / `lspinorb` | nspin=1 自旋简并，2 共线，4 自旋量子态/密度多分量。noncolin/SOC 可重设 nspin；初始磁矩不是收敛磁矩约束。[磁性](capabilities/abacus-magnetism-soc.md) |
| `init_chg` / `init_wfc` | 电荷与波函数分别初始化。NSCF 重置 init_chg 为 file；LCAO Gamma-only binary 存在读写标志不一致，需核对 cube 回退。读取优先级、二进制名和各自旋 cube 文件见[静态](../static/SKILL.md)。 |
| `scf_thr` / `scf_thr_type` | 密度残差判据：类型 1 为倒空间库仑度量，类型 2 为电子数归一化的实空间 L1 残差（无量纲）。不得统一注明 Ry，也不是总能差。 |
| `scf_ene_thr` | eV 的额外能量条件，启用后不能替代密度条件。[收敛](../convergence/SKILL.md) |
| `mixing_beta` / `mixing_ndim` / `mixing_gg0` | 混合步长、历史维度和 Kerker 预条件参数；Kerker 主要抑制小波矢/长波残差，不是高频滤波。不同路径、自旋及最小截断有差别，不能保证 beta 越小或 ndim 越大就越好。 |
| `symmetry` | -1 关闭约化，0 保留基本时间反演处理，1 请求点群分析；某些工作流强制重置。SOC 运行时强制 -1，MD/电场的参数重置为 0，Berry/QO 重置为 -1。读最终 k 点与运行分支，不只读输入字面值。 |

## 输出、动力学与高级功能

| 术语 | 本版口径与使用要点 |
|---|---|
| `running_scf.log` / `!FINAL_ETOT_IS` | 常规日志和最终能量标记；标记本身不保证收敛。FD 的总能含 -TS，需区分自由能与去除占据熵项的能量。[输出](capabilities/abacus-output-reading.md) |
| `istate.info` | 各 k 点本征值及占据信息；占据带 k 权重，检查高能尾部时须结合权重/自旋解释，不能机械用固定阈值比较所有点。 |
| `mem_saver` | PW 多 k NSCF 设 1 时波函数只有一个 k 存储槽；需要全部 WFC 的后处理设 0。纯能级/总 DOS 的本征值另行保存。[电子结构](capabilities/abacus-electronic.md) |
| `out_chg` / `out_*` | 每个开关有各自语法。推荐可重读密度用 `out_chg 1 10`；本版 `out_chg 2` 被布尔解析拒绝，-1 特殊值关闭二进制密度备份。0 不等于完全不写密度文件。[电子结构](capabilities/abacus-electronic.md) |
| `out_mat_hs2` | 输出 LCAO 的实空间 H(R)/S(R)，与 out_mat_hs 的 k 空间矩阵不同；必须满足非 gamma_only 等分支要求。H 用 Ry，S 无量纲。[电子结构](capabilities/abacus-electronic.md) |
| `force_thr` / `force_thr_ev` / `stress_thr` | 分别 Ry/Bohr、eV/Å、kbar；默认力阈值 0.001 Ry/Bohr ≈0.0257112 eV/Å。两种力关键词同时给时 force_thr 优先，和两种 sigma 的覆盖规则不同。[优化](../relax/SKILL.md) |
| `TOTAL-STRESS` / `MD_dump VIRIAL` | 后者实际单位 kbar，是不含离子动能的应力。PW/LCAO KS 前者在扣外压前打印，后者用扣外压后的返回值；非零 press1/2/3 时不能直接混用。[输出](capabilities/abacus-output-reading.md) |
| `relax_method` / `relax_new` / `relax_nmax` | 方法、算法分支和最多离子步数；非 cg 会关闭新优化分支，FIRE 通过 calculation=md/md_type=fire 进入。达到步数上限不等于优化收敛。 |
| STRU_ION / STRU_MD | 几何输出不自动保存逐原子磁态；优化中间步还可能输出更新后结构，不能直接配更新前的力能/JSON标签。[磁性](capabilities/abacus-magnetism-soc.md)、[优化](capabilities/abacus-relax.md) |
| `fixed_axes` / `fixed_ibrav` | 优化约束不能直接用于本版 NPT/MSST；冻结原子仍可能随变胞仿射移动，MSST 速度和 FIRE 判停还各有未屏蔽冻结分量的限制。[MD](capabilities/abacus-md.md) |
| `md_type` / `md_dt` / `md_nstep` | 系综/积分器、fs 时间步及步数；步长需按体系频率与能量漂移验证。[MD](../md/SKILL.md) |
| `md_tfirst` / `md_tlast` / `md_thermostat` | 离子目标温度与温控器，不指定电子温度。初始速度和续算温控状态的处理见[MD 卡](capabilities/abacus-md.md)。 |
| `kpar` / `bndpar` / GPU | k 点与随机轨道并行不能互换；普通非 SDFT 会重设 bndpar=1；LCAO 虽有陈旧的 kpar>1 警告，部分矩阵求解器已有 k 点池实现。GPU 和进程数按具体求解器检查。[性能](capabilities/abacus-performance.md) |
| DFT+U、`orbital_corr`、`hubbard_u` | 附加投影与 U 参数组；不能概括为仅 LCAO，本版存在有约束的 PW 分支。按方法核对投影、nspin、U 的定义及续算数据。[高级](capabilities/abacus-advanced-functionals.md) |
| PEXSI | `ks_solver pexsi` 的非对角化路线，依赖编译和实现分支；不要将其说成不是 ks_solver 取值。[高级](capabilities/abacus-advanced-functionals.md) |
| OFDFT | 无轨道路线，动能密度泛函、局域赝势和自身收敛判据需独立设置，不套普通 KS 模板。[高级](capabilities/abacus-advanced-functionals.md) |
| DeePKS / Deep Potential / dpdata | 分别涉及电子结构修正、原子势和外部数据转换；模型与标签不能互换。确认能量是否含熵、应力/维里口径及解析器版本。[生态](capabilities/abacus-ml-ecosystem.md) |
