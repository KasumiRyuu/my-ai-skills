# 单点 SCF：按 v3.10.1 源码设置和验收

本卡适用于固定晶胞和原子位置的 KS-DFT 自洽计算。指定非零电子温度时，目标是相应占据下的电子自由能与密度。源码依据均以本地 ABACUS v3.10.1 的 `source/` 为根，不以 README 或示例参数代替实现。

## 先确定物理问题

从已有 STRU、INPUT、赝势/轨道和日志读取结构、电子数、磁性、基组、精度要求以及后续用途；仅缺少会阻止有效配置的信息时询问用户。数值展宽和物理电子温度必须明确区分。对真实有限温度及电子熵，先读 [电子温度与能量](../finite-temperature.md)。

- 默认 `smearing_method gauss`、`smearing_sigma 0.015` Ry，**默认并非固定占据**。已确认有带隙且整数填充时可显式设 `fixed`；其固定填充算法不适合一般金属。
- 金属、窄带隙或近简并问题通常需要分数占据和 k 点收敛测试。用于数值积分的高斯/MP 展宽不能解释为物理 FD 电子温度。
- 物理 4000 K 的 FD 单点优先写 `smearing_method fd`、`smearing_sigma 0.02533452`。这份源码的 `smearing_sigma_temp 4000` 实际给约 2000 K 的 FD 占据；等价 4000 K 的温度关键词需约 8000，见专门说明。两个宽度关键词同时写时后出现的行覆盖前者。
- 不同初始密度或磁矩可能收敛到不同局域自洽解；不能承诺“好初值只改步数、不改答案”。

## 基组、求解器与精度

| 分支 | 实现与选择 |
|---|---|
| PW | 默认 `ks_solver cg`；合法值 `cg`、`dav`、`dav_subspace`、`bpcg`。性能与内存随算法、基组规模及并行布局变化，没有统一最快值。 |
| LCAO CPU | 编译了 ELPA 时默认 `genelpa`；未编译 ELPA 的 MPI 版本默认 `scalapack_gvx`；串行默认 `lapack`，但本版该实现有波函数未回写/带数较小时越界问题，见[性能卡](abacus-performance.md)，不能把默认值当作可靠支持。 |
| LCAO GPU/特殊求解器 | 默认 GPU 分支选择 `cusolver`；`cusolver`/`cusolvermp` 需要相应 CUDA/MPI 支持，后者还需专门构建支持。`pexsi` 需 PEXSI 构建；`cg_in_lcao` 虽通过参数检查并标为测试中，但普通 LCAO `hamiltSolvePsiK` 没有对应分派，会进入报错路径，不应当作可用替代求解器。 |

LCAO 的合法集合还有 `elpa`，但编译支持仍需核对。不要对未知构建强制指定 `genelpa`。本卡的普通 SCF 流程以默认 `esolver_type ksdft` 为范围，`sdft`、`ofdft`、TDDFT、机器学习势等需要各自算法条件。

`ecutwfc` 用 Ry；LCAO 仍依赖 FFT 网格，同时需要检查数值原子轨道质量。`nbands` 不是统一的 8：默认值按 `nspin`、电子数与 `nbands_mul`（默认 1.2）及代码取整逻辑计算，非 PW 还截到 `NLOCAL`。分数电荷体系应显式核验实际带数；温度高时默认空带余量未必够，需要对占据尾部、自由能和熵收敛。LCAO 显式 `nbands>NLOCAL` 报错。

`dft_functional default` 使用赝势给定泛函，并检查不同原子类型的泛函一致性。显式指定可覆盖内部标签并给出警告，但不会重新生成赝势或消除赝势与目标泛函的不一致；必须保留科学上的兼容性检查。

依据：`source/module_io/read_input_item_elec_stru.cpp:12–163`；`source/module_hsolver/hsolver_lcao.cpp:118–170`；`source/module_elecstate/cal_nelec_nband.cpp:61–161`；`source/module_elecstate/read_pseudo.cpp:141–151,329–345`。

## 初始化与续算

- 首次算默认 `init_chg atomic`。`init_chg auto` 尝试文件，失败后回退原子密度；`file` 读取失败则报错，适合要求严格使用指定密度的续算。
- `file`/`auto` 先读 `read_file_dir/{suffix}-CHARGE-DENSITY.restart`，失败后才读 `SPIN*_CHG.cube`。`read_file_dir` 默认 `OUT.<suffix>/`，显式 `./` 则是工作目录。旧二进制文件可能优先于刚换入的 cube；要检查日志中实际读入文件名。
- 默认 `out_chg 0` 在选定电子步/收敛时仍输出上述二进制密度；`out_chg 1 10` 还输出高精度 cube，`-1` 关闭该电子步密度输出。不能断言续算一定以先设置 `out_chg 1` 为前提；需要的是兼容且已验证收敛的密度文件。
- **本版 LCAO Gamma-only 二进制陷阱**：普通 FP 路径的电荷 PW 基组以 `gamma_only=false` 初始化，但二进制写出标志使用 `gamma_only_local || gamma_only_pw`；LCAO `gamma_only 1` 因而写出 true，读取时与电荷基组的 false 不一致并返回失败。不能保证只有该 binary 就能续算，包括切换到多 k NSCF。第一步保留 `out_chg 1 10` 的全部必要 cube，确认日志成功回退读取；若只有不兼容 binary，先重新生成收敛且可读取的密度，不能靠改 suffix 或手改文件头证明兼容。依据：`source/module_esolver/esolver_fp.cpp:84,109,303`；`source/module_io/rhog_io.cpp:52–80,232–252`。
- 标准 cube 排布：`nspin=1` 一份密度；`nspin=2` 两份自旋密度；`nspin=4` 四分量电荷/磁化密度。meta-GGA 还需要检查相应 `TAU` 密度读取，否则该实现会从密度估计初始动能密度。
- PW `init_wfc` 实现了 `atomic`、`atomic+random`、`random`、`nao`、`nao+random`、`file`；NAO 方案要有轨道资源，原子波函数不足的情形需留意随机补充/回退。PW 文件初始化读 `WAVEFUNC<k>.dat`；`init_chg wfc` 仅支持 PW-KSDFT，和 `init_wfc file` 是不同开关。
- **PW `init_chg wfc` 还读取 `istate.info` 中的加权占据**，只有 binary WFC 不够。本版 reader 每 k 按三列解析，而 nspin=2 的原生 writer 将上下自旋写成五列并合并 k 块，两者不兼容；不要用这条路径恢复共线磁性密度，优先用已核验的 `init_chg file`。其他自旋也须核验配套文件、结构/基组、nbands、k 点和占据；这一格式缺陷不能机械推广到独立的 `init_wfc file`。依据：`source/module_io/read_wfc_to_rho.cpp:35–50,71–119`；`source/module_io/write_istate_info.cpp:55–79`。
- LCAO `init_wfc file` 可从保存的 LCAO 系数/占据构造起始密度，先验证文件与结构、基组、k 点、自旋兼容。
- `restart_load` 读取 `read_file_dir/restart/` 的独立重启机制，可能涉及交换矩阵；不等同于单纯 `init_chg file`，也不保证恢复完整混合历史。

本版 cube loader 的成功日志不是完整性验证：它不比较实际几何/原子元数据，网格不同时可自动插值，数据尾部截断也未检查失败状态。迁移或改写文件时独立核对数量、有限值、网格/几何/自旋和积分，见[输出判读](abacus-output-reading.md)。磁性优化/MD 的输出 STRU 还可能丢失逐原子磁矩，不能只恢复几何便宣称恢复原磁态，见[磁性卡](abacus-magnetism-soc.md)。

依据：`source/module_io/read_input_item_system.cpp:481–535,653–669`；`source/module_elecstate/module_charge/charge_init.cpp:41–118,120–207,241–251`；`source/module_esolver/esolver_fp.cpp:143–183,289–311`；`source/module_psi/psi_init.cpp:43–74`；`source/module_psi/psi_initializer_file.cpp:34–37`；`source/module_esolver/esolver_ks_lcao.cpp:584–613`；`source/module_io/input_conv.cpp:300–351`。

## SCF 判据：必须记录类型

| 参数 | v3.10.1 的实际含义 |
|---|---|
| `scf_thr_type 1` | 倒空间密度残差的库仑加权二次型，含自旋相关项，具有能量量纲；PW 默认。不是相邻两步总能差。 |
| `scf_thr_type 2` | 实空间 `sum(abs(rho_out-rho_in))*Omega/Ngrid/nelec`，按实际自旋分量求和，为无量纲归一化 L1 残差；LCAO 默认。 |
| `scf_thr` | 对上述残差作严格 `<` 比较；普通 PW SCF 默认 `1e-9`，LCAO 默认 `1e-7`。不能把所有分支都标成 Ry，也不能横向等同两种范数。 |
| `scf_ene_thr` | 默认 -1，只有正值启用；密度已收敛且 `iter>1` 时，额外要求 `abs(DeltaE_womix)<阈值`，单位 eV。它是附加条件，不是替代密度条件。 |

`DeltaE_womix` 在同一次迭代中比较输入密度能与未经混合的输出密度能；它与屏幕上相邻迭代能差 `EDIFF` 不同。混合重启步和 U-ramping 未完成时还会阻止宣布收敛。

依据：`source/module_io/read_input_item_elec_stru.cpp:581–668`；`source/module_elecstate/module_charge/charge_mixing_residual.cpp:8–67,111–248`；`source/module_esolver/esolver_ks.cpp:553–600,652–657`。

## 执行和验收

1. 从 [PW 模板](../../templates/INPUT.scf-pw.tpl) 或 [LCAO 模板](../../templates/INPUT.scf-lcao.tpl) 填入真实资源。选择电子温度/占据、初始自旋态、基组、k 网格与空带数；模板数值只作起点。
2. 运行前检查赝势、轨道、STRU/KPT 和资源预算。授权范围内运行；不因为打开本卡而自动开始昂贵计算。
3. 运行后保留原始 INPUT、`OUT.<suffix>/INPUT`、实际读取资源和日志。输出 INPUT 是解析及重置后的参数快照，不是“全是默认值”；结构读取后才确定的 `NBANDS`、实际网格/k 点等仍需看运行日志。
4. 在本次单点对应的最后一个 SCF 块检查 `charge density convergence is achieved`，并排除 `convergence has not been achieved`、提前中止和无效数值。`!FINAL_ETOT_IS` 与时间尾行都不能单独证明收敛。
5. 交付最终残差及 `scf_thr_type`、收敛步数、自由能/能量名称和单位。FD 情形同时记录 sigma、推得的物理温度、`E_entropy(-TS)`；常用不显含温度的 XC 下可计算 `U=F-demet`，热 XC 的额外限制见 [温度说明](../finite-temperature.md)。力/应力只在用户要求且确实输出时验收。
6. 对所需能差、力或应力收紧 SCF 阈值并测试稳定性；不能用固定 `1e-7` 对所有基组/体系保证力准确。未收敛时转 [SCF 排障](abacus-convergence.md)；已收敛仍需 [精度测试](abacus-accuracy.md)。

输出源码：`source/driver.cpp:114–128`；`source/module_io/read_input.cpp:304–318`；`source/module_io/output_log.cpp:10–21`；`source/module_esolver/esolver_ks_pw.cpp:793–800`。更多文件和单位见 [输出判读](abacus-output-reading.md)。

本次审核是源码及关键分支验证；未将历史示例的收敛步数或总能冒充本次实测。
