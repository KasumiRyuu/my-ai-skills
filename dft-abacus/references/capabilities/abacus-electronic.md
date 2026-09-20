# ABACUS 3.10.1：电子结构、数据复用与输出

本卡核对 `abacus_v3.10.1/source/` 的实际读写与调用路径。能带、DOS 的常规半局域泛函流程是收敛 SCF 后在所需 k 点做 NSCF；电荷、势、矩阵、Mulliken 可直接由 SCF 产出，`get_S` 只构造重叠矩阵。不要为所有输出强制两步计算。

## SCF → NSCF 的前置数据

1. 确认 SCF 的收敛状态，不能用 `!FINAL_ETOT_IS`、正常退出或文件存在代替。需要 cube 时第一步设置 `out_chg 1 10`（第二个数是文本输出精度，默认仅 3）。
2. 复用收敛时的晶胞/原子位置、赝势、轨道、XC、自旋、电子数、温度/占据设定、基组和密度网格。优化后必须使用最终结构；通常 NSCF 只改变 k 点、需要的空带数、输出及求解精度。
3. NSCF 输入阶段**强制** `init_chg=file`，即使未写也不从原子密度起步；找不到可读密度会终止。`scf_nmax` 被置为 1。显式写 `init_chg file` 便于读者理解，而非声称遗漏该行会变成原子密度。
4. `read_file_dir` 默认 `OUT.<当前 suffix>/`。改变 suffix 或工作目录时显式指向 SCF 数据；推荐每阶段保存独立输入与日志。程序先查 `<read_file_dir>/<当前 suffix>-CHARGE-DENSITY.restart`，再查 `SPIN1_CHG.cube` 等；若保留 binary，当前 suffix 必须与该 binary 文件名对应。
5. 普通 KS-SCF 默认 `out_chg 0` 仍写二进制密度，`out_chg 1` 另写 cube；`out_chg -1` 关闭此 binary 输出。读取时 binary 优先，编辑/复制 cube 后若留下同名旧 binary，实际读入的可能仍是旧数据。依据日志确认真实读入文件。
6. `nspin=1` 保存 SPIN1；`nspin=2` 保存 SPIN1、SPIN2 的上下自旋密度；`nspin=4` 常规保存四个分量（总密度与三个磁化分量），不能只带一个 SPIN1。代码存在由两份共线密度转为四分量的分支，但这不等价于完整复用任意非共线磁态。
7. meta-GGA 还需 `*-TAU-DENSITY.restart` 或 `SPIN*_TAU.cube`；缺失时程序可能用密度近似初始化 TAU，这不是原收敛势的严格复用。DFT+U 与杂化/EXX 还涉及局域占据矩阵或交换相关的额外状态，先读 [高级泛函](abacus-advanced-functionals.md)，不能保证一个 cube 就够。

读取成功日志只确认进入了读取分支。此版 cube reader 不校验几何一致性或数据尾部是否完整；搬运文件后须独立核对网格值数量、有限数值、晶胞/原子/自旋、密度积分和来源，见[输出判读](abacus-output-reading.md)。

**本版输入陷阱**：`out_chg 2` 经 `assume_as_boolean` 报错；虽然运行代码仍保留 `==2` 的初始密度输出分支，不能据此把 2 当成可用输入。只用已验证的 `0/1/-1` 与可选精度。

**Gamma-only → 多 k 的密度陷阱**：LCAO `gamma_only 1` 的普通 FP 路径将二进制头写成 gamma=true，但电荷 PW 基组以 false 初始化，`read_rhog` 检查不符后拒绝该 binary。目录、suffix 正确仍可能读失败。SCF 应保存 `out_chg 1 10` 的必要 cube，NSCF 确认已成功回退读取它们；只有不兼容 binary 时先重新生成兼容的收敛密度，不能直接保证运行。此缺陷不只是在改 k 点后才需要检查，详见[静态初始化](abacus-static.md)。证据：`source/module_esolver/esolver_fp.cpp:84,109,303`；`source/module_io/rhog_io.cpp:52–80,232–252`。

证据：`source/module_io/read_input_item_system.cpp:510,653`；`read_input_item_elec_stru.cpp:572`；`read_input_item_output.cpp:41` 与 `read_input.cpp:24`；`source/module_esolver/esolver_fp.cpp:146,292`；`source/module_elecstate/module_charge/charge_init.cpp:42,123`。

## 能带与能量零点

使用 [NSCF 能带模板](../../templates/INPUT.nscf-band.tpl)，从 SCF 输入继承物理设置；给够所需空带。`kpoint_file KLINES` 对应 [Line 语法示例](../../templates/KLINES.example)：第二行是特殊点数，第四列是各段含起点、不含终点的点数，最后一个为 1。路径必须由实际晶格确定。

```text
calculation       nscf
init_chg          file
read_file_dir     ./OUT.Si2
suffix            Si2
kpoint_file       KLINES
kspacing          0
gamma_only        0
symmetry          0
out_band          1
```

这段是需合并到已有物理设置中的片段，不是完整计算输入。`symmetry` 可为 0 或 -1，1 会拒绝 Line 模式。关闭 `kspacing` 与 gamma 优化，否则它们会覆盖路径文件。

- `out_band 1` 输出 `BANDS_1.dat`，`nspin=2` 再有 `BANDS_2.dat`；`nspin=4` 是一套自旋量子态的能带文件，不按共线上下自旋各给一份。
- 每行：k 点序号、累计路径长度、`nbands` 个本征能（eV）。长度来自笛卡尔 k 坐标，缩放单位是 `2π/lat0`；路径断点不增加跨段跳跃长度。
- 本版 PW/LCAO 调用 `nscf_band` 时传入 `fermie=0.0`，所以能量**没有自动减费米能**。绘图时显式选择收敛规则网格的费米能、VBM 或其他统一参考，避免重复减零点。Line 采样不适合求可靠的布里渊区填充费米能。
- LCAO `out_proj_band 1` 输出 XML 风格的 **`PBANDS_1`**（nspin=2 还有 `PBANDS_2`），不是 `PBAND_1`；PW 开此参数会报错。
- PW NSCF 还要检查本征求解阈值和残差，可显式测试 `pw_diag_thr`；默认阈值附近有根据 `scf_thr/nelec` 自动收紧的分支，不能用“只迭代一次 SCF”推断本征问题已充分求解。

证据：`source/module_cell/klist.cpp:360,405`；`source/module_io/nscf_band.cpp:9`；`write_proj_band_lcao.cpp:100,284`；`source/module_esolver/esolver_ks_lcao.cpp:419`、`esolver_ks_pw.cpp:866`；`source/module_hsolver/hsolver.cpp:24`。

## DOS/PDOS

用规则 k 网格，按目标能量窗口增加 `nbands`，验证网格与谱线展宽；可以在足够密的收敛 SCF 上直接输出，也可以读该 SCF 密度做更密网格 NSCF。需要固定此前物理模型并避免 Line 路径。

| 设置 | 本版行为 |
|---|---|
| PW `out_dos 1` | 输出总 DOS；`out_dos 2` 不会凭空提供 NAO 投影 |
| 普通多 k/复数 LCAO `out_dos 1` | 总 DOS |
| 普通多 k/复数 LCAO `out_dos 2` | 总 DOS、`PDOS`、`TDOS` 等轨道分解数据 |
| LCAO gamma-only 实数分支 | 只要触发 DOS 就也计算 PDOS，包括 `out_dos 1`；做谱分析仍应验证 Γ 采样是否充分 |
| LCAO `out_dos 3` | 有 `.bxsf` 写出入口，但实现不完整，不能作为可直接使用的费米面工作流；PW 或 `symmetry 1` 会拒绝 |

`dos_sigma` 是 **eV** 单位的高斯标准差，`dos_edelta_ev` 是采样步长；`dos_emin_ev/dos_emax_ev` 设置能量范围。它们与 `smearing_method/smearing_sigma/smearing_sigma_temp` 的电子占据及电子熵是两组独立参数。DOS 文件的能量轴也不自动减费米能。

`DOS1_smearing.dat`（共线磁性再有 DOS2）的三列是：能量 eV、平滑 DOS（states/eV/cell，含本版 k 权重的自旋简并）、**第二列的逐行累计和**。源码只执行 `sum2 += dos_smearing[i]`，没有乘 `dos_edelta_ev`，故第三列不能直接叫积分态数或电子数；需乘步长得到近似积分，还应检查窗口截断、展宽尾部与自旋计数。DOS 是可用态密度，不等于占据电子密度，计算电子数还涉及占据函数。自旋 down 列不会为了画图自动加负号。

`PDOS` 是基于非正交 NAO 重叠矩阵的轨道投影，依赖轨道空间和分区定义。`TDOS`/PDOS 使用直接对本征值展宽，`DOS*_smearing.dat` 先分能量箱再展宽，两者的网格端点和离散误差可能不同；求和/比较应先对齐能量轴。谱线平滑不等于 k 点已收敛。

### 投影谱的构建与自旋限制

- **PDOS/TDOS 和 PBANDS 轨道权重要求 MPI 构建。** 未定义 `__MPI` 时，投影乘法/归约没有串行替代，仍可能写出全零投影文件；MPI 构建只运行一个 rank 不属此限制。普通 DOS 的能级分箱不直接受这个投影缺陷影响，但普通串行 LCAO 另有 [LAPACK 求解缺陷](abacus-performance.md)，不能因此推荐该串行流程。
- **LCAO `gamma_only 1`、`nspin 2` 的 PDOS/TDOS 下自旋使用了上自旋能级作为展宽中心。** 下自旋谱与 `DOS2_smearing.dat` 的明显峰位差不能只归因于离散误差。可用 MPI 构建，改为 `gamma_only 0`、显式 Γ KPT 或所需规则网格、`out_dos 2`，核验密度读取和谱求和；Γ 采样是否充分另做精度检查。不要把该缺陷推广为所有磁性 DOS 均不可用。
- **`.bxsf` 输出不完整。** 此 writer 仅在 MPI 构建中执行，网格尺寸仍写字面串 `NKX NKY NKZ`；费米能用内部 Ry，能级却转 eV，两个自旋输出还没有正确筛选通道。需要费米面时，从完整规则网格的本征能和 k 坐标生成经验证的目标格式，统一能量单位、通道及费米能；只补尺寸或改后缀不足以修复。

依据：`source/module_io/write_dos_lcao.cpp:105–189,420–536`；`source/module_io/write_proj_band_lcao.cpp:43–95,196–278`；`source/module_io/cal_dos.cpp:84–95`；`source/module_io/dos_nao.cpp:42–59`；`source/module_io/nscf_fermi_surf.cpp:17–87`。

证据：`source/module_io/dos_nao.cpp:22`；`write_dos_lcao.cpp:28`（实数分支）、`:414`（复数分支 PDOS）、`:430`（高斯）、`:586`（PDOS）；`write_dos_pw.cpp:8`；`cal_dos.cpp:81,117,145`；`read_input_item_output.cpp:121`。

## 电荷与势

这些输出可以随 SCF 产生，不要求 NSCF。

| 参数 | 文件与含义 |
|---|---|
| `out_chg 1 10` | `SPIN*_CHG.cube`；10 为建议复用精度，不是物理收敛阈值 |
| `out_pot 1` | `SPIN*_POT.cube`，有效局域势，通常含局域赝势、Hartree 和 XC 等实际启用贡献 |
| `out_pot 2` | `ElecStaticPot.cube`，Hartree + 固定局域势；代码还会加入已启用的偶极电场修正、隐式溶剂静电项 |
| `out_pot 3` | 除最终有效势外，初始化阶段还输出 `SPIN*_POT_INI.cube` |

cube 的位置/网格向量单位 Bohr；势值沿用内部 Ry（不是 Hartree）。普通模守恒密度的值是电子数/Bohr³，积分以晶胞体积/网格点数加权得到电子数；nspin=4 的磁化分量不应按普通正密度解读，超软的增强电荷也需另核对。cube 的原子电荷字段是赝势价电子数，不是核电荷；格式本身不足以证明电子结构已收敛。

功函数使用有明确真空平台的静电势与一致能量单位的费米能；不能把势的任意空间平均或有效 XC 势直接叫真空能级。差分密度需相同晶格、网格、原子参照与单位。

证据：`source/module_esolver/esolver_fp.cpp:146,188`；`esolver_ks_pw.cpp:312`、`lcao_before_scf.cpp:283`；`source/module_io/write_elecstat_pot.cpp:32`；`write_cube.cpp:81`；`source/module_elecstate/module_charge/charge.cpp:198`。

## 波函数与部分电荷

- PW `out_wfc_pw 1` 写 `WAVEFUNC{k}.txt`，2 写 binary `.dat`，k 从 1 编号；保留其配套基组与 k 点信息。PW `out_wfc_r 1` 以 `square=true` 写 `wfc_realspace/`：这是逆 FFT 周期部分的原始模平方，没有复相位，scalar 情况未除晶胞体积 Ω，也未乘占据/k 权重，不能直接当成积分为 1 的概率密度。其自定义结构/网格文本的晶格标度是 Å，并非 charge cube 的 Bohr 标头；`nspin=4` 只取第一旋量分量，不能作为完整旋量密度。
- LCAO `out_wfc_lcao 1` 是文本 **`WFC_NAO_K{k}.txt`** 或 `WFC_NAO_GAMMA{k}.txt`，2 才是 binary `.dat`；MD/非追加模式可能含 `_ION{step}`。这些是 NAO 系数，不是实空间波函数。
- LCAO `calculation get_wf/get_pchg` 强制 `init_wfc file`，从 `read_file_dir` 读取已保存 NAO 波函数；因此须先有匹配结构、轨道、基组、nbands、k 点与自旋的系数，只有 charge cube 不够。当前 `read_wfc_nao` 只读文本 `.txt`，因此第一步用 `out_wfc_lcao 1`；不能把 binary `.dat` 改扩展名冒充文本。
- `get_wf` 的 `out_wfc_norm/out_wfc_re_im` 是带选择列表，元素 0/1，长度不能超过 `nbands`；与 `nbands_istate` 的默认费米能附近选带规则区分。实空间 cube 的 `_ENV`、`_REAL`、`_IMAG` 根据所选支路产生，详细文件名以实际写出代码/日志为准；旧 `write_wfc_r` 接口在源码已标待弃用，不能保证其旧格式包含完整复数信息。
- LCAO 的 `get_pchg` 使用 `out_pchg` 选带，要求 MPI 构建；PW 在 SCF/NSCF 波函数处理路径使用 `bands_to_print` 选带，而不支持 `calculation get_pchg`。两者都是 0/1 列表，可用 `N*x` 缩写，不能互换。建议显式 `symmetry -1` 并记录 `if_separate_k`，实际权重见下表。

**PW 波函数后处理须保留全部 k 态。** 多 k NSCF 的 `mem_saver 1` 只分配一个波函数槽，求解后只剩本池最后一个 k 的态；随后写 WFC、实空间模平方、部分电荷、Wannier 或 Berry 时会错配、缺失或非法访问。此类任务用 `mem_saver 0`，并检查实际保存的 k 数。纯能级/总 DOS 的本征值另有完整数组，不因这个覆盖缺陷直接失效。

**PW `bands_to_print` 的范围。** 使用 scalar `nspin=1/2`、有效 `KPAR=1` 和完整波函数。多个池时合并输出只汇集 pool 0 的 k 贡献，逐 k 输出也使用局部编号。`nspin=4` 只处理第一旋量分量，且单 k 等情形的 `ik % (nks/nspin)` 可出现除零，不能作为可靠的 SOC 总密度/磁化输出。GPU 路径需另外核对，尤其有效 KPAR 可能被设备配置改写。

选带输出通常是轨道分布，**不总是该带实际占据的电子密度**。以下权重来自本版实现，针对 scalar、兼容基组的比较；`wg` 已含占据与 k/自旋因子，`wk` 是 k 权重。

| 分支 | 实际乘数/占据规则 |
|---|---|
| PW 合并 k | `wk(ik)/Ω`，不使用所选带占据；空带也可非零 |
| PW 逐 k | 该通道 k 权重和除 Ω；有效 KPAR=1 时 nspin=1 权重和为 2，nspin=2 每通道为 1 |
| LCAO Gamma-only | 带索引小于 `int((nelec+1)/2+1e-8)` 时用该带 `wg`，否则用此阈值前一带的 `wg`；磁性/有限温度时该阈值不等于真实逐通道 HOMO |
| LCAO 复数多 k，逐 k | 固定权重 1 |
| LCAO 复数多 k，合并 | 用第一带 `wg(ik,0)`，并非所选带的占据 |

因此 PW 与 LCAO 的逐 k cube 不能无条件用相同积分归一化比较，也不能由“空带 cube 非零”推断空带实际被占据。PW `out_wfc_r` 的原始模平方又不同于上述部分电荷：普通模守恒 scalar 态须先除 Ω，再按用途加入相应权重。

依据：`source/module_psi/psi_init.cpp:191–203`；`source/module_psi/psi.cpp:314–342,387–392`；`source/module_hsolver/hsolver_pw.cpp:341–405`；`source/module_esolver/esolver_ks_pw.cpp:633–699,907–909`；`source/module_io/write_wfc_pw.cpp:24–78`；`source/module_io/write_wfc_r.cpp:41–58,102–143,179–188`；`source/module_io/get_pchg_pw.h:92–149`；`source/module_io/write_cube.cpp:37–48`；`source/module_io/get_pchg_lcao.cpp:89–96,215–223,466–533`；`source/module_cell/klist.cpp:144–146,1125–1140`。

证据：`source/module_io/write_wfc_pw.cpp:14`；`write_wfc_nao.cpp:16`；`write_wfc_r.cpp:26,53`；`source/module_esolver/esolver_ks_pw.cpp:907`；`lcao_others.cpp:172,321`；`source/module_io/read_wfc_nao.cpp:34`、`get_wf_lcao.cpp:506`、`get_pchg_lcao.cpp`、`get_pchg_pw.h:46`；`read_input_item_system.cpp:481`。

## Wannier90 接口

先有兼容的收敛 SCF 密度，再用 `calculation nscf`、`towannier90 true` 和对应 `nnkpfile seed.nnkp`。由匹配的外部 Wannier90 版本提供 `.nnkp`；其中实/倒晶格、k 点数、逐点坐标及顺序必须与实际 ABACUS 计算一致。通常设置 `gamma_only 0`、`kspacing 0`、`symmetry -1`，提供与 nnkp 一致的完整规则 k 网格；不要使用能带 Line 路径。

- 接口构造函数要求**有效** `GlobalV::KPAR=1`、`bndpar=1`。GPU 可改写有效 KPAR，不能只凭 INPUT 写了 `kpar 1` 就判定满足。
- `nspin=2` 用 `wannier_spin up` 或 `down` 分别导出，分别保存文件以免覆盖。其他自旋情形仍需与 nnkp 投影/自旋约定相符，不能把共线两通道用法照搬 SOC。
- LCAO `wannier_method 1`（默认）使用 LCAO_IN_PW 接口；2 使用 LCAO 直接实现。按实际精度和任务选已实现分支，不把任意整数当有效方法。输入 `basis_type lcao_in_pw` 在此工作流还会触发基组重置，核对运行值。
- 默认 `out_wannier_mmn/amn/eig=true`，`out_wannier_unk=false`。文件名基于 nnkp 去掉 `.nnkp` 的 seed；`.eig` 能量用 eV。**LCAO 方法 2 的 `out_unk` 是空函数**；PW/方法 1 的 UNK writer 又仅在 MPI 构建中执行，并且 `nspin=4` 只写第一旋量分量。需要 UNK 时使用经验证的 scalar MPI 路径，不能把这些分支当成完整 SOC UNK 导出。该限制不等于否定整个 mmn/amn/eig 接口，许多任务也不需要 UNK。
- PW 多 k NSCF 设 `mem_saver 0`，防止后处理访问已被覆盖的波函数；有效 KPAR 和完整存储须同时满足。

UNK 依据：`source/module_io/to_wannier90_pw.cpp:188–352`；`source/module_io/to_wannier90_lcao_in_pw.cpp:102–104`。

依据：`source/module_io/read_input_item_postprocess.cpp:149–237`；`source/module_io/read_input_item_elec_stru.cpp:166–175`；`source/module_parameter/input_parameter.h:398–408`；`source/module_io/to_wannier90.cpp:14–40,98–116,134–237`；`source/module_io/to_wannier90_lcao.cpp:262–264`；`source/module_esolver/esolver_ks_lcao.cpp:1259–1295`。外部 Wannier90 预处理、局域化和收敛验收由其实际版本另核对。

## 矩阵与 Mulliken

以下为 LCAO 路径，不是 PW 的通用输出。

- `out_mat_hs 1`：`OUT.<suffix>/data-{k}-H`、`data-{k}-S`，默认文本上三角，H 为 Ry、S 无量纲；k 从 0 编号。自旋、基组顺序、复数约定和可能的离子步前缀必须一并记录，下游不可凭文件名猜约定。
- `out_mat_hs2 1`：R 空间稀疏 `data-HR-sparse_SPIN0.csr`（共线磁性另有 SPIN1）、`data-SR-sparse_SPIN0.csr`；必须 `gamma_only 0`，可用显式 Γ KPT 保留单点。`gamma_only 1` 与 R 空间矩阵组合会报错，而非悄悄不生成文件。
- `calculation get_S`：LCAO、`gamma_only 0`，输出 **`OUT.<suffix>/SR.csr`**；不需要预先收敛 charge cube。虽然输入层把 `init_chg` 置为 file，这个专用求解器不走密度初始化与 SCF。
- `out_dm` 为 gamma-only 的密度矩阵路径；`out_dm1` 为多 k 路径。不要把 H/S、密度矩阵和 WFC 文件互相替代。
- `out_mul 1`：`mulliken.txt`，PW 开此项会拒绝。文件的 `Total Charge on atom` 表示分配到该原子的电子布居；净电荷通常需用价电子数减布居，并声明参考。布居依赖 NAO 基组，不是唯一的可观测原子电荷；MD 输出间隔受 `out_interval` 控制。

证据：`source/module_esolver/esolver_ks_lcao.cpp:997,1157`；`source/module_io/write_HS.hpp:84`、`write_HS_R.h:26`；`read_input_item_output.cpp:145,196,380`；`source/module_esolver/esolver.cpp:190`、`esolver_gets.cpp:28,135`；`source/module_io/output_mulliken.cpp:30,121`。

## Berry phase 极化

常规验证路线针对有能隙且占据子空间明确的晶体：先收敛 SCF，再 NSCF，设置 `berry_phase 1`、`gdir 1/2/3`、`symmetry -1`、`gamma_only 0`。本版输入层会强制 Berry 的 symmetry 为 -1，仍建议写出以表达意图。基组仅接受 `pw/lcao`；使用 `Gamma/MP` 规则网格，沿 gdir 有足够点形成 k 字符串，不能用 Line 或任意无序显式点表代替。

PW 还要求**实际 `KPAR=1`、`mem_saver 0`**：Berry 使用全局网格索引访问本池的 k/波函数，重叠通信只有 `POOL_WORLD`，没有跨池取远端态的实现。GPU 须核查实际 KPAR，不能只看 INPUT 的 `kpar 1`。

结果在 `running_nscf.log` 的 `POLARIZATION CALCULATION`，会输出 `(e/Omega).bohr`、`e/bohr^2`、`C/m^2`，并带极化量子。gdir 是晶格矢量方向而非一般意义的笛卡尔 x/y/z；完整矢量要按晶格方向组合，并对结构路径连续选择极化分支。单次数值不唯一，铁电极化差必须处理极化量子。

**本版自旋限制**：解析器并未统一拒绝 nspin=4，但 **LCAO 的 nspin=4 电子相位分支为空**，`zeta` 保持 1，得到电子相位 0；不能用该结果报告 SOC/非共线物理极化。PW 有旋量重叠实现，但公共 `get_occupation_bands()` 仍固定取 `ceil(nelec/2)`，没有按各自旋通道或旋量态重新确定占据数。常规 nspin=1 绝缘体之外须独立核对占据子空间与可靠基准；仅切 PW 不能保证 SOC 极化正确。金属/有限温度部分占据也不能直接套用此绝缘体公式。

依据：`source/module_io/berryphase.cpp:25–110,248–259,350–397`；`source/module_io/unk_overlap_pw.cpp:32–59`；`source/module_cell/klist.cpp:1214–1229`。

证据：`source/module_io/read_input_item_postprocess.cpp:113`；`read_input_item_system.cpp:165`；`source/module_io/berryphase.cpp:25`（占据带数）、`:58`（规则网格字符串）、`:269`（自旋分支）、`:472`（主流程）、`:611`（输出单位）。
