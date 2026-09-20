# 决策速查（v3.10.1）

| 问题 | 处理规则 |
|---|---|
| 4000 K 电子温度与电子熵 | 选 `fd`，优先 `smearing_sigma ≈ 0.0253345` Ry；本版 `smearing_sigma_temp 4000` 实际约为 2000 K，详见[温度说明](finite-temperature.md)。 |
| 两种 sigma 都写了 | 两个不同关键词依 INPUT 顺序写入同一变量，后出现者生效；推荐只写一个。同名参数重复则报错。 |
| scf_thr 是什么单位 | 看 `scf_thr_type`：类型 1 为倒空间残差的库仑度量，类型 2 为电子数归一化的实空间 L1 残差；不是总能差。 |
| KPT 是否必须存在 | 有效 LCAO `gamma_only` 或正 `kspacing` 会生成并覆盖 k 点文件；普通手工网格/能带路径需提供所选 KPT。 |
| ecutrho 能否低于 4 倍 ecutwfc | 本版解析器拒绝该比值；默认 4 倍不保证所有赝势和目标量已收敛。 |
| 只增大 ecutrho / ndz 是否足够 | LCAO 双网格混用、手工 ndz 重置各有本版缺陷；先核对实际网格及可用分支。[精度](capabilities/abacus-accuracy.md) |
| 用 `1d-9` 写阈值 | 不可；部分 parser 会取前缀 1。用 `1e-9`，整数参数不用科学计数法或算式。[输入](capabilities/abacus-input-files.md) |
| 串行 LCAO 默认 lapack 是否可靠 | 本版未回写波函数且可能越界；选已验证的 MPI 求解路径。[性能](capabilities/abacus-performance.md) |
| 总能行能否直接用 | 先确认 SCF 收敛，区分自由能、去除熵项的能量及外推量；FD 下不能把含 `-TS` 的总能当内能。 |
| 能带和 DOS | SCF 电荷接 NSCF；能带用路径，DOS 用均匀网格。PDOS 支持依赖基组和分支，见[电子结构](capabilities/abacus-electronic.md)。 |
| 只有 Gamma-only LCAO binary 能否续算 | 本版读写 gamma 标志不一致，可能被读取器拒绝；先取得兼容收敛密度或高精度 cube，并核对实际读取成功。[续算限制](capabilities/abacus-static.md) |
| 电荷、势是否必须 NSCF | 很多输出可直接在 SCF 末尾生成，按输出分支设置。 |
| PDOS 全零或自旋峰位相同 | 先排查非 MPI 投影空路径、Gamma-only nspin=2 错用上自旋能级；不能直接判定无磁性。[电子结构](capabilities/abacus-electronic.md) |
| PW mem_saver=1 接波函数后处理 | 多 k NSCF 只留最后 k 态；用 0，Berry/部分电荷/Wannier 还要实际 KPAR=1。[电子结构](capabilities/abacus-electronic.md) |
| LCAO SOC Berry 有数值就可用 | nspin=4 的电子相位分支为空，不能用作物理极化；PW 也须另核对占据子空间。[电子结构](capabilities/abacus-electronic.md) |
| relax/cell-relax | 检查离子力/晶胞应力和电子收敛；两种 force 阈值同时给时 `force_thr` 优先。 |
| AIMD 温度 | `md_tfirst/md_tlast` 控离子，电子温度单独控制；续算保留结构、速度、控温/压状态及匹配步数。 |
| 磁性结构续算 | 默认输出 STRU 丢失逐原子磁矩；恢复目标初值或兼容磁化密度，不能只恢复几何。[磁性](capabilities/abacus-magnetism-soc.md) |
| 冻结边界与变胞 MD | NPT/MSST 不执行优化的晶轴约束，FIRE/MSST 也有冻结分量限制。[MD](capabilities/abacus-md.md) |
| SCF 振荡 | 根据残差、占据、磁态和求解器定位；有限温度计算不能为收敛随意提高目标温度。 |
| SOC/DFT+U/GPU/并行 | 按源代码支持的组合判断，不使用“所有 SOC 无力”“DFT+U 仅 LCAO”“MPI 必须少于 nbands”等通用断言。 |
| 外部 ML 数据 | 核对能量定义、力、应力/维里单位与符号；ABACUS 源码不能证明外部版本解析器的行为。 |
| 优化结构与同一步力能配对 | 每个实际位移步都可能错位，JSON 也有此问题；核对求解器输入几何或重新算标签。[生态](capabilities/abacus-ml-ecosystem.md) |
| LR 重启 / RT 步长 | 独立 LR 要文本 NAO WFC 和 cube，spectrum 状态读当前输出目录且受 assert/NDEBUG 缺陷影响；RT 需 MPI，实际步长来自 md_dt。[高级](capabilities/abacus-advanced-functionals.md) |

具体输入及代码定位见各任务子技能与[源码依据](source-audit.md)。
