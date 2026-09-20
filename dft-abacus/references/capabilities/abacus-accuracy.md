# ABACUS 3.10.1：数值精度

依据本地 v3.10.1 的 `source/` 实现。源码规则保证参数的定义与约束；适合某体系的精度数值必须通过计算验证。下文提供工作流，不把默认值或算例值当成推荐精度。

## 基组与求解器

| 路线 | 需要验证的内容 | 本版限制 |
|---|---|---|
| `pw`（默认） | 波函数截断 `ecutwfc`、密度截断 `ecutrho`、k 点、空带及对角化精度 | 默认求解器 `cg`；还接受 `dav/bpcg/dav_subspace`；没有可直接启用的 PW gamma-only 优化 |
| `lcao` | `.orb` 的径向函数、ζ 数、角动量与截断半径；实空间网格和两中心积分数值 | 要数值轨道；CPU 默认按编译条件选 `genelpa`、`scalapack_gvx` 或 `lapack`，GPU 默认 `cusolver`，依赖相应构建支持 |
| `lcao_in_pw` | 专门的 NAO 在 PW 中表示路线 | 正常路径仅接受 `ks_solver lapack`，要轨道并强制 `init_wfc nao`；不是自动兼得两种基组优点的常规开关 |

PW/LCAO 切换要同时检查求解器、轨道依赖、gamma 优化、输出功能和数值收敛，不能仅修改 `basis_type`。`towannier90` 的 `lcao_in_pw` 是另一个会改写基组的分支，见 [生态接口](abacus-ml-ecosystem.md)。

本版普通串行 LCAO 的默认 `lapack` 实现不能据此作为可靠基线：存在波函数未回写及 `nbands<nlocal` 时本征值越界，见[性能卡](abacus-performance.md)。先选择已验证的可执行分支，再做数值收敛测试。

证据：`source/module_parameter/input_parameter.h:74`；`source/module_io/read_input_item_elec_stru.cpp:12`（solver defaults/checks）、`:166`（basis reset）、`:538`（gamma）；`read_input_item_system.cpp:481`（init_wfc）。

## 截断能与轨道

- `ecutwfc` 单位 Ry：未设置或设置为 0，LCAO 默认 100，其他路线默认 50；负值拒绝。PW 截断决定平面波空间，但不能保证每个派生量随数值单调趋好。
- `ecutrho` 单位 Ry：未设置或非正值时重置为 `4*ecutwfc`。**正值比率小于 4 会报错**（数值容差约 `1e-8`）。大于 4 且未显式固定 FFT 网格时会启用双网格；这条解析规则不代表 LCAO 的双网格执行正确，见下述限制。
- 模守恒常以 4 倍作为起点；超软增强电荷可能需要更高密度截断，独立测试总能、力、应力等目标。8–12 倍至多是经验扫描范围，源码没有保证这些倍数一定足够；4 倍也不是自动错误。
- LCAO 的 `ecutwfc` 控制数值网格，因此仍影响局域积分、能量、力、应力；不是“提高只会浪费机时”。而且 `lcao_ecut` 未显式设置时等于 `ecutwfc`，它影响轨道倒空间积分表的网格。提高 `ecutwfc` 不会添加新的 ζ/角动量轨道，轨道完备性要另外测试。
- 如果显式指定 `nx/ny/nz` 或密度 FFT 网格，记录实际网格，避免做了截断扫描却固定了关键离散化尺度。

**LCAO 双网格的本版限制**：`double_grid=true` 时，LCAO 的电荷和局域赝势表仍按较小 `pw_rho` 分配，Potential 却接收 `pw_rhod` 并按稠密 G 索引访问该表；出现额外 G 壳/网格点时会造成尺寸不匹配和越界。不能把 PW 的独立 ecutrho 扫描照搬 LCAO。普通已验证的 NC-LCAO 路线保持单网格关系 `ecutrho=4*ecutwfc`，通过提高 ecutwfc 同时收敛网格；需独立稠密网格时选择经过验证的 PW 路线或修复版本。

**手工 FFT 网格的另一处缺陷（PW 也受影响）**：设置非零 `nx/ny/nz` 后，仅增大 ecutrho 不自动打开双网格；`ndz` 的 reset 又误检查 `ndy>ny`。例如小网格 32³、稠密网格 32×32×64、ecutwfc=60/ecutrho=480，其他条件不触发开关时仍用小网格，密度基组初始化传入的截断仍为 240 Ry，实际承载能力还受手工网格限制。INPUT 快照中的 ndz/ecutrho 不证明实际采用。普通 PW 优先由截断自动生成网格，必须手设时核对实际初始化日志与基组，或使用已修复并验证的实现。

依据：`source/module_io/read_input_item_system.cpp:301–310,374–427`；`source/module_esolver/esolver_fp.cpp:31–37,75–109`；`source/module_esolver/esolver_ks_lcao.cpp:136–142,204–217`；`source/module_hamilt_pw/hamilt_pwdft/VL_in_pw.cpp:31–34,88`；`source/module_elecstate/potentials/potential_types.cpp:30`；`source/module_elecstate/potentials/pot_local.cpp:20–40`。

证据：`source/module_io/read_input_item_system.cpp:274,298,323`；`read_input_item_elec_stru.cpp:710`；`source/module_basis/module_ao/ORB_read.cpp:55,211`；`source/module_esolver/esolver_fp.cpp:90`。

赝势需核对元素、价电子/半芯态、XC、相对论及生成质量；LCAO 轨道需与赝势和用途相容。程序能识别一些标签/XC 不一致，但不能证明整个配套在物理上可靠。UPF/UPF201 的读入路径支持超软数据，PW 具有增强电荷与力/应力实现；这不等于每个基组、SOC、后处理组合都完整支持超软。LCAO 常规流程优先使用有验证的模守恒赝势与配套轨道；特殊组合应核对实际计算路径，不能凭“文件能读取”认定支持。

程序可由赝势求中性电子数，也允许 `nelec`、`nelec_delta` 改变电子数；“电子数不能在 INPUT 设置”是错误的。不同赝势或不同芯价划分的绝对总能零点不同，不能直接用总能差评价精度。

证据：`source/module_elecstate/read_pseudo.cpp:65,140,329`（标签/XC）；`source/module_cell/read_pp_upf100.cpp:150`、`read_pp_upf201.cpp:227`；`source/module_elecstate/cal_nelec_nband.cpp:10`；PW 超软路径见 `source/module_elecstate/elecstate_pw.cpp`、`module_hamilt_pw/hamilt_pwdft/forces_us.cpp`、`stress_func_us.cpp`。

## k 点、展宽与空带

先按 [输入规则](abacus-input-files.md) 确定 k 点来源。`kspacing` 单位 Bohr⁻¹，减小它可加密，程序会重写 KPT；LCAO `gamma_only 1` 优先于它。PW 只算 Γ 应使用 `gamma_only 0` + 显式 Γ 网格。对于 slab/线状体系各方向分别测试，不因真空方向只有 1 点就把周期方向也都取 1。

金属的 k 点和展宽误差往往耦合；热电子计算则要固定真实电子温度，增加 k 点和空带数检验目标量。`dos_sigma` 仅改变后处理谱线，不改变 SCF 电子温度；Gaussian/MP/cold 的数值展宽不能直接当作费米狄拉克热平衡。热电子设定及熵对应能量见 [SCF](abacus-static.md)。

`nbands=0` 时程序自动估算，但不是满足任意高温或高能 DOS 的保证。普通 `nspin=1` 分支使用 `max(Nocc+10, int(nbands_mul*Nocc)+1)`，`nbands_mul` 默认 1.2；其他自旋分支采用不同余量，LCAO 还会截到 `nlocal`。实际值以日志为准。

- 非固定占据需多于占据带数；有限温度下增加 `nbands`，检查最高带占据已足够小，且自由能/力等目标不再变化。
- LCAO 的限制是 **`nbands <= nlocal`**（相等允许）；更多空带若超过现有轨道空间，需扩大基组。不存在普遍的“nbands 必须大于 MPI 总进程数”物理约束，并行布局限制应按具体求解器处理。
- 能带/DOS 需覆盖所需能量窗口。能带路径不是布里渊区积分网格，不能把沿路径算出的费米能作为可靠的整体填充基准。

证据：`source/module_elecstate/cal_nelec_nband.cpp:61`；`source/module_io/read_input_item_elec_stru.cpp:223,235`；`source/module_cell/klist.cpp:208`。

## 收敛测试流程

1. 明确目标量与误差。例如 1 meV/atom、0.01 eV/Å 可作为用户认可后采用的项目目标，绝非 ABACUS 的默认验收标准；应力、能垒和能隙另设对应目标。
2. 固定结构、电子温度、磁态、赝势/轨道与 XC。先让 SCF 残差和本征求解误差低于目标精度，避免将迭代误差混进网格测试。`scf_thr` 是密度残差判据，取决于 `scf_thr_type`，不能一律标成 Ry 能量阈值；详见 [收敛](abacus-convergence.md)。
3. PW 先围绕赝势的验证值扫描截断；LCAO 分开扫描数值网格与轨道空间；超软额外扫描密度截断。保持其他误差已足够小，记录每点实际 FFT 网格。
4. 按晶格方向加密 k 网格，固定所研究温度；必要时交叉检查 k 点与展宽、k 点与截断的耦合。
5. 增加空带检验能量窗口或高温尾占据，逐点确认 SCF 已收敛。只有某个输出文件存在或打印了 `!FINAL_ETOT_IS` 不算收敛证据。
6. 比较同一目标量的多次变化而非只凭两个点，记录实际 k 点、基组、截断、残差和输出能量口径。最后用选定组合复核；无需机械重复已经通过且未受改动影响的测试。

交付收敛表、选定参数及其适用结构/温度/物理量范围，并记录赝势与轨道文件名、来源及校验和（条件允许时）。程序未实际运行时明确标为待运行方案，不编造扫描结果。
