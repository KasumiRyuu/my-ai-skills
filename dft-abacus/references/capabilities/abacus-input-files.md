# ABACUS 3.10.1：输入文件

依据本地 `abacus_v3.10.1/source/` 的实现核对，源码版本 `f71921fe848659deac8db319cd4311b55b5ad480`。下文 `source/...` 路径相对此源码根目录；默认值与规则不外推到其他版本。

## INPUT 的真实解析规则

- 表头为区分大小写的 `INPUT_PARAMETERS`；其前文本跳过。参数名转换为小写，参数值一般不做统一大小写转换，使用源码规定的拼写。
- 未知参数报错。**同名参数重复出现立即报错**，不是最后一项覆盖前一项。两个不同参数改写同一内部变量的情形另论，例如 `smearing_sigma` 与 `smearing_sigma_temp`，见 [SCF](abacus-static.md)。
- 每个参数独占一行。值由 `getline` 读取后按空白拆分；遇到以 `#` 或 `!` 起头的 token 停止，所以写 `60 # Ry`，不要依赖 `60#Ry`。整行 `#`、`!`、`/` 开头会跳过；`/` 不是参数值的行尾注释标记，绝对路径可正常作为值。
- 数值使用 C++ `std::stod/std::stoi`，多数标量不检查整个 token 是否消费。**不要写 Fortran D 指数、单位后缀或算式**：`scf_thr 1d-9` 可能被读成 1，整数 `scf_nmax 1e2` 被读成 1，`ecutrho 4*60` 被读成 4；只有明确支持向量缩写的参数另论。浮点用 `1e-9`，整数写 `100`，单位放到分隔后的注释中；不能把未报解析错误当成数值无误。依据：`source/module_io/read_input_tool.h:8–11,138–150`。
- **参数值行没有通用 150 字符截断规则**。`ignore(150,'\n')` 仍出现在表头搜索和整行注释跳过等分支，长注释仍应避免。不能把 INPUT 规则推广给 STRU/KPT 的所有段。
- 先按文件出现顺序执行读取，再按注册顺序执行默认值/条件重置，最后校验。因此用户显式值有时仍会被任务分支重置；应核对日志和输出 INPUT，而非只看原始 INPUT。
- `ntype` 默认 0，可省略：程序扫描 STRU 的 `ATOMIC_SPECIES` 得到种类数；显式非零值若不一致会报错。它是原子**类型数**，同一元素也可用不同标签区分初始磁态。
- `abacus --check-input` 会读取 INPUT 并统计 STRU 种类数，故需要可访问的 STRU。它通过后立即退出，不完成原子坐标、KPT、赝势/轨道内容、SCF 与物理精度验证。PW `gamma_only 1` 的参数重置可能在此阶段重写 KPT，检查并非绝对无文件副作用。

证据：`source/module_io/read_input.cpp:24`（布尔值）、`:69`（`read_information`）、`:113`（check mode）、`:178`（`read_txt_input`）、`:400`（`check_ntype`）；`read_input_item_system.cpp:653`（读入目录）。

## STRU：顺序、单位与外部数据

常用段顺序如下；每种元素/类型的数量与顺序在各列表间一致。

```text
ATOMIC_SPECIES
Si 28.0855 Si.pz-vbc.UPF

NUMERICAL_ORBITAL
Si_lda_8.0au_50Ry_2s2p1d

LATTICE_CONSTANT
10.2

LATTICE_VECTORS
0.5 0.5 0.0
0.5 0.0 0.5
0.0 0.5 0.5

ATOMIC_POSITIONS
Cartesian
Si
0.0
2
0.00 0.00 0.00 m 1 1 1
0.25 0.25 0.25 m 1 1 1
```

这只是结构语法示例，文件名不是已安装资源，也不代表选定赝势/轨道已适合目标问题。普通 PW 可不含 `NUMERICAL_ORBITAL`；LCAO、`lcao_in_pw` 以及 PW 的 NAO 初始化或 `onsite_radius>0` 等路径需要它。

- `ATOMIC_SPECIES`：标签、原子质量、赝势文件名，可选类型 `auto/upf/upf201/vwr/blps`。质量是原子质量单位（数值等同 g/mol），MD 必须真实，不能沿用演示的 `Si 1.000`。
- `pseudo_dir`、`orbital_dir` 指目录，STRU 给文件名。核对实际存在、元素、价电子组态、相对论形式与 XC，不能仅凭扩展名判断配套。`NUMERICAL_ORBITAL` 按 token 顺序读取，建议每行只有一个文件名，**不要夹行尾注释**，否则下一类型可能读到 `#`。
- `ATOMIC_POSITIONS` 的类型标签必须与 `ATOMIC_SPECIES` 顺序一致，源码会校验。每类依次是标签、初始磁矩、原子个数及坐标行；轨道列表也遵从此顺序。
- `LATTICE_CONSTANT=lat0` 必须正数，单位 **Bohr**。`LATTICE_VECTORS` 每行为一个无量纲晶格矢量，实际晶格 = `lat0 × latvec`。使用 `latname` 时按对应 Bravais 类型给 `LATTICE_PARAMETERS`，不能同时混用任意 `LATTICE_VECTORS`。

| 坐标标记 | 每个原子前三列含义 |
|---|---|
| `Direct` | 分数坐标，相对实际晶格矢量 |
| `Cartesian` | 笛卡尔坐标，单位 **lat0**，不是 Å |
| `Cartesian_angstrom` | 笛卡尔坐标，单位 Å |
| `Cartesian_au` | 笛卡尔坐标，单位 Bohr |
| `Cartesian_angstrom_center_xy/xz/yz/xyz` | 先把 Å 坐标转换，再沿指定笛卡尔分量加晶胞中心偏移 |

源码坐标转换使用 `0.529177 Å/Bohr`；要从 Å 晶胞生成 STRU，可保持正 `lat0` 并相应缩放三个晶格行，勿把晶格与原子坐标重复缩放。

原子行可写 `x y z m 1 1 0`（旧式 `x y z 1 1 0` 也支持）；1 可移动、0 固定，省略时默认为三个 1。`fixed_atoms` 会将全部标记置零。标记用于原子移动，不是单点 SCF 收敛参数。

可选 `v/vel/velocity vx vy vz` 是原子单位的速度（Bohr/原子时间），不随坐标类型改为 Å/fs；MD 的有效 `init_vel` 必须为 true 才使用它；可显式写 `init_vel 1`，而 `md_tfirst<0` 或续跑会自动开启。初温设置可能再缩放速度。`mag`/`magmom` 可给标量或三分量，`angle1/angle2` 输入为度；逐原子磁矩可覆盖类型初值。`nspin=2/4` 全零初始磁矩可能被自动改为非零，不能用全零初值保证不磁化；SOC/非共线细节见 [磁性](abacus-magnetism-soc.md)。

证据：`source/module_cell/read_atoms.cpp:13`（类型/轨道/晶格），`:428`（标签匹配），`:530`（移动、速度、磁矩），`:755`（坐标转换），`:850`（自动磁矩）；`source/module_md/md_func.cpp:78,185,412`（速度与质量使用）。

使用优化/MD 输出 STRU 续算时也要核对上述轨道段。本版 PW+U 的 `onsite_radius>0` 要求轨道，但输出端的 `need_orb` 未覆盖所有这类条件，atomic/random 初始化时可能遗漏 `NUMERICAL_ORBITAL`；按原物种顺序恢复原有已验证条目，见[优化卡](abacus-relax.md)与[MD 卡](abacus-md.md)。

默认输出 STRU 还不保留逐原子磁矩；同元素 AFM/非共线几何重开要恢复目标磁矩/方向或兼容磁化密度。优化约束也不能直接沿用到 NPT/MSST：晶轴约束和冻结原子各有分支限制，见[磁性](abacus-magnetism-soc.md)与[MD](abacus-md.md)。

## KPT：文件是否必需及覆盖优先级

`kpoint_file` 默认 `KPT`。若使用正值 `kspacing` 或有效的 LCAO `gamma_only 1`，程序会生成它，运行前不必已有该文件。生成会**覆盖同名文件**，所以不能把 `kpoint_file KLINES` 与自动生成混用。

| 设置 | 本版实际行为 |
|---|---|
| LCAO `gamma_only 1` | 采用 Γ 实数算法，生成 `1 1 1` 的 Gamma KPT；优先于 `kspacing`；不支持 `nspin=4` |
| `gamma_only 0`，`kspacing` 三分量均正 | 由晶格生成 Gamma 网格并覆盖 `kpoint_file` |
| `gamma_only 0`，`kspacing 0` | 读取用户的 `kpoint_file` |
| PW `gamma_only 1` | 输入阶段警告、将开关置 0、生成 Γ KPT；随后正 `kspacing` 仍可能重新生成多 k 网格 |

PW 只算 Γ，或 LCAO 需要复数算法的单 Γ（例如 SOC、R 空间矩阵），应使用 `gamma_only 0`、`kspacing 0` 与显式 Γ 网格，不用上述 PW 自动降级副作用。

```text
K_POINTS
0
Gamma
4 4 4 0 0 0
```

第二行 0 表示自动规则网格；第三行 `Gamma` 或 `MP`，第四行三个正整数和三个偏移。偏移不是统一的“0/1 平移开关”：沿一方向，源码 `n=1..N` 的分数坐标为 Gamma `(offset+n-1)/N`，MP `(offset+2n-N-1)/(2N)`。零偏移的偶数 MP 网格通常不含 Γ。

显式点表第二行为点数，第三行 `Direct` 或 `Cartesian`，随后每行 `kx ky kz weight`。Direct 相对倒格矢；Cartesian 单位为 `2π/lat0`（Bohr⁻¹ 的缩放坐标），不是直接的 Å⁻¹。

`kspacing` 接受一个或三个数，单位 Bohr⁻¹，使用含 `2π` 的倒格矢长度；全部 0 表示关闭，混合零与正数或负数报错。各方向 `N_i=max(1,int(|b_i|/spacing_i+1))`，因此值越小通常网格越密，它不是“最小允许间距”。

能带 `Line`/`Line_Direct` 或 `Line_Cartesian`：第二行是特殊点数；第 i 行第四列 N 表示从该点起、下一特殊点前生成 N 个点（含本点，不含下一端点），不等于插入 N 个内部点。最后一行必须是 1；中间的 1 可作为路径断点标记。推荐段内 N≥2；总点数为第四列之和。`symmetry 1` 会拒绝 Line 模式，设 0 或 -1。路径坐标和高对称点名称须根据实际晶胞推导，不能把演示路径普遍用于其他晶格。

`symmetry 0` 对规则网格仍可用 k↔−k 约化，`symmetry -1` 才完全关闭 k 点约化；NSCF 默认 0（显式值除外）。需要完整网格的 Berry phase/Wannier 等工作流按各自要求处理。

证据：`source/module_cell/klist.cpp:197`（`read_kpoints`）、`:405`（路径插值）、`:470`（MP 公式）、`:755`（仅规则网格的反演约化）；`source/module_io/read_input_item_elec_stru.cpp:538`（gamma reset），`read_input_item_system.cpp:135,714`（symmetry/kspacing）。

## 完成检查

核对所有实际文件与模板占位值，确认 INPUT 无重复/旧语法；核对 STRU 单位、类型顺序和坐标；查看生成后的 KPT。具备可执行文件时再做参数检查；正常运行的结构、赝势和轨道读取检查不能由 `--check-input` 替代。

手工 `nx/ny/nz` 与 `ndx/ndy/ndz` 还需核验运行时实际网格：本版有 ndz 重置检查笔误，且 LCAO 双网格存在尺寸不匹配，见[精度卡](abacus-accuracy.md)。

[STRU PW 模板](../../templates/STRU.pw.tpl) · [STRU LCAO 模板](../../templates/STRU.lcao.tpl) · [k 网格](../../templates/KPT.mp.tpl) · [Γ 点](../../templates/KPT.gamma-only.tpl) · [Line 路径](../../templates/KLINES.example)
