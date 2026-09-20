# ABACUS 3.10.1 输入模板

模板已按本地 v3.10.1 `source/` 核对。它们是可修改的格式骨架，没有附带赝势/轨道，也不是已通过数值收敛验证的计算结果。复制成程序读取的名称（如 INPUT、STRU、KPT），先替换体系、目录和实际文件名；KLINES.example 复制为 KLINES 后还要重建实际晶格的路径。

| 文件 | 用途 |
|---|---|
| INPUT.scf-pw.tpl / INPUT.scf-lcao.tpl | PW / LCAO 单点 |
| INPUT.relax.tpl / INPUT.cell-relax.tpl | 固定晶胞 / 晶胞与原子优化 |
| INPUT.md.tpl | AIMD |
| INPUT.nscf-band.tpl / INPUT.nscf-dos.tpl | 从 SCF 数据读取的能带 / DOS |
| STRU.pw.tpl / STRU.lcao.tpl | 示例 Si 结构；LCAO 带轨道声明 |
| KPT.mp.tpl | Gamma 中心规则网格（可按需改 MP） |
| KPT.gamma-only.tpl | 显式 Γ 点，默认可配 gamma_only 0 |
| KLINES.example | Line 语法与点数约定；路径非通用 |

- `ecutwfc/ecutrho/smearing_sigma` 是 Ry；`smearing_sigma_temp` 名义输入为 K，但本版转换使 FD 物理温度约减半，必须按[温度说明](../references/finite-temperature.md)换算；`dos_sigma` 是 eV。`scf_thr` 是与 `scf_thr_type` 关联的密度残差阈值，不能一律标作能量 Ry。
- `LATTICE_CONSTANT` 是 Bohr，`Cartesian` 原子坐标单位是该常数；质量为原子质量单位。STRU 的移动标记会影响优化/MD，按任务检查。
- INPUT 重复参数和未知参数都会报错。用 `#` 或 `!` 行尾注释时前面留空格；参数值行没有通用的 150 字符截断。STRU 的轨道文件列表不要夹行尾注释。
- 浮点数用 `e/E` 科学计数法，不用 Fortran `d` 指数；整数参数用十进制整数，不写表达式。部分 reader 只转换数值前缀，`scf_thr 1d-9` 会被读成 1。
- 普通串行 LCAO `ks_solver lapack` 有本版波函数/本征值缺陷，优先已验证的 MPI 构建与求解器；MPI 单 rank 与非 MPI 构建不同。PDOS/PBANDS 另需 MPI 构建，见[性能卡](../references/capabilities/abacus-performance.md)。
- LCAO 双网格有混用数据缺陷；手工网格仅增大 ndz 又可能未启用双网格，不能仅从 INPUT 判断实际截断，见[精度卡](../references/capabilities/abacus-accuracy.md)。
- LCAO `gamma_only 1` 或有效正值 `kspacing` 会覆盖 `kpoint_file`。PW gamma_only 没有该优化，会警告并重写 Γ 文件；PW 单 Γ 推荐显式 KPT。能带用 `gamma_only 0`、`kspacing 0`、`symmetry 0/-1`。
- NSCF 强制读文件密度；`read_file_dir` 与 suffix 决定寻找位置，binary 优先。LCAO Gamma-only binary 有读写标志不一致问题，须按[电子结构卡](../references/capabilities/abacus-electronic.md)保存 cube 并核验回退读取。多自旋、meta-GGA、DFT+U/EXX 需保留对应额外状态。`out_chg 1 10` 可写高精度 cube，`out_chg 2` 在本版不被解析器接受。
- `abacus --check-input` 需要 STRU，只验证部分参数与类型数；不证明赝势、坐标、KPT 或 SCF 已正确/收敛。
- 优化输出的结构可能已位移而同一步力能属于旧几何；默认 STRU_ION/STRU_MD 还不保存逐原子磁矩。NPT/MSST 不沿用优化的 fixed_axes/fixed_ibrav；按对应能力卡核对数据与约束。

实际规则与源码证据见 [输入参考](../references/capabilities/abacus-input-files.md)、[精度参考](../references/capabilities/abacus-accuracy.md)、[电子结构参考](../references/capabilities/abacus-electronic.md)。按用户授权运行所需检查；未运行的计算不得描述为验证通过。
