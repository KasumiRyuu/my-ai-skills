<!-- capability_id: cap.abacus.advanced-functionals | revision: 3 | source-audited: ABACUS v3.10.1 -->

# 高级泛函与修正

按“参数读取 → 自动重置/检查 → 求解器分派 → 实际能量、力和输出”确认功能。下列片段各自独立，不能把不同求解器或泛函的片段拼成一个 INPUT。先完成同一体系的基线 SCF 与精度检查；修正前后有能隙或能量变化本身不能证明实现已正确启用。

## DFT+U：LCAO 与 PW 的不同条件

**3.10.1 已有 PW +U 实现。** 不应沿用“仅 LCAO、PW 下静默无效”的旧结论。

- `dft_plus_u 0` 关闭；LCAO 中 `1` 走 onsite 投影新实现，`2` 走旧 `OperatorDFTU` 实现，二者投影定义不能无条件互换。源码没有为任意其他整数给出可靠的独立方法定义，使用 0/1/2。
- PW 的输入检查要求 **`nspin=4`**；`nspin=1/2` 会退出。推荐核对 `dft_plus_u 1` 的 onsite 路径，提供 STRU 的 `NUMERICAL_ORBITAL` 和对应 `orbital_dir` 文件，虽然波函数基组仍是 PW。`onsite_radius` 单位 Bohr，+U=1 时输入 0 自动设为 3.0；半径及投影轨道会影响 U 的定义和结果，默认值不代替验证。PW +U 从优化/MD 输出结构重开时检查轨道块是否仍在：该版写出判定遗漏 onsite_radius 条件，见 [结构优化](abacus-relax.md)。
- PW 的 Hamiltonian 按 `dft_plus_u>0` 启用同一个 onsite 算符，**不按 1/2 选择 LCAO 的两套实现**。`dft_plus_u 2` 不会自动设置正的 onsite_radius；若沿用默认 0，投影初始化被跳过但后续仍调用投影。PW 使用上述已核对的 `1` 路线并确认实际半径为正，不能直接移植 LCAO 旧法输入。
- +U 初始化要求 MPI 构建；串行构建会输出“不支持”并 `exit(0)`，因此仅看退出码 0 不足以判断计算成功。
- `orbital_corr`、`hubbard_u` 各按 STRU **类型顺序**给 `ntype` 项。前者允许 `-1`（不修正）、`0/1/2/3`（s/p/d/f）；全为 -1 时程序把 +U 关闭并警告。`hubbard_u` 输入 eV、内部转 Ry；简化 U 修正使用 Ueff 形式，不能同时把该数理解为两个独立的 U、J。
- `omc 1` 从工作目录 `initial_onsite.dm` 初始化占据矩阵；`omc 2` 还固定该矩阵。默认 `omc=0` 配 `init_chg file` 时，+U 另读 **当前 `OUT.<suffix>/onsite.dm`**，不是自动随 `read_file_dir` 迁移。密度、占据矩阵、投影与电子态必须匹配。
- `uramping` 输入 eV，需由 `mixing_restart>0` 的迭代重启触发。此版将其转 Ry 后按 **`>0.01 Ry`（约 0.136 eV）**决定从 U=0 启动递增；更小步幅不能当作正常 U-ramping 使用。检查日志中的实际 U 已达到目标，不以中途 SCF 停止替代此检查。

以下仅演示两类型 LCAO 参数对应关系；U=5 eV 不是材料推荐值：

```text
basis_type        lcao
nspin             2
dft_plus_u        1
orbital_corr      2 -1
hubbard_u         5.0 0.0
```

## 杂化泛函与 EXX

常规工作流使用 LCAO；源码也保留 `lcao_in_pw` 分支，其限制需按实际任务另查。**PW 中杂化泛函会明确退出**，不是静默退回 GGA。需要 `__EXX`/LibRI；HSE、SCAN0 等还受 LibXC 检查。meta-GGA（包括 SCAN0）与 `nspin=4` 在此版直接拒绝。

```text
basis_type        lcao
dft_functional    hse
```

`exx_hybrid_alpha` 自动默认：hf=1、pbe0/hse/scan0=0.25、b3lyp=0.20；允许范围 0–1。`exx_hse_omega` 默认 0.11（Bohr⁻¹）；`exx_separate_loop` 控内外循环。保留自动默认并检查实际泛函/EXX 收敛，再针对目标精度收敛截断阈值。若调整 `exx_distribute_type`，合法拼写为 `htime|kmeans2|kmeans1|order`。

**不能宣称所有 EXX 都禁止 symmetry=1。** `input_conv.cpp` 的相关自动处理仅对非 NSCF、EXX、nspin=4、symm_flag=1 组合改为 -1；SOC 另有无条件设为 -1 的分支。见 [自旋/SOC](abacus-magnetism-soc.md)。

## 色散修正

`vdw_method` 执行工厂仅接受 `none|d2|d3_0|d3_bj`。参数表内部出现其他 D3 名称，并不代表执行工厂支持它们。

```text
dft_functional    pbe
vdw_method        d3_bj
```

显式给泛函便于核对，但 **D3 并非必须显式给 `dft_functional`**：值为 default 时会从所有赝势推断一致的 XC 名称；无赝势或名称不一致会退出。自动参数表没有该 XC 时也会退出。`vdw_s6/s8/a1/a2` 可部分覆盖自动值；全部给定才跳过参数表查找，但并不跳过前面的 XC 名称推断。记录自动匹配表，避免无声混用另一泛函的 D3 系数。

`vdw_cutoff_type radius|period` 分别使用半径与周期范围；半径要一起记录 `vdw_radius_unit`（Bohr 或 A）。D3 的配位数截断另有 `vdw_cn_thr` / `vdw_cn_thr_unit`，`vdw_abc` 控三体项。D2 的外部 C6/R0 文件也有独立单位参数。对力、晶胞、截断半径做一致的精度验证。

## 溶剂化、静态电场和 gate

| 功能 | 参数和已核实的含义/限制 |
|---|---|
| 隐式溶剂 | `imp_sol true`；`eb_k` 体相相对介电常数、`sigma_k` 无量纲空腔宽度、`nc_k` 电子密度阈值 Bohr⁻³、`tau` 表面张力 Ry/Bohr²。默认分别 80、0.6、0.00037、1.0798e-5，不是所有溶剂的通用参数 |
| 锯齿电场 | `efield_flag true`；`efield_dir 0/1/2` 对应倒格矢方向，默认 2；`efield_pos_max/dec` 是周期分数位置/回落宽度；`efield_amp` 用 Hartree 原子电场单位，约 5.1422e11 V/m |
| 偶极修正 | `dip_cor_flag true` 必须同时 `efield_flag true`；只做修正时令 `efield_amp 0`。选择有真空区的 slab，使势的回落区落在真空，并收敛真空厚度 |
| Gate | `gate_flag true` 在 `zgate` 放补偿电荷板，电量由 `nelec−离子价电荷` 决定；方向仍用 efield_dir；可选势垒参数 `block`、`block_down`、`block_up`、`block_height`，高度 Ry。位置按周期分数坐标理解 |

Gate 和外场同时开时必须开启偶极修正，否则输入检查退出。`efield_flag` 会将输入 symmetry 设为 0，SOC 后续还有独立重置。静态场参数不同于 TDDFT 的 `td_*` 外场。不要承诺任意几何/边界条件都有正确的均匀外场物理含义。

溶剂化能量已进入 `etot`（`esol_el + esol_cav`）；比较有/无溶剂的能量须明确几何、电荷、电子温度与参考态是否相同。不同优化几何的差还包含结构弛豫贡献，不能把任意两次运行之差无条件称为同一种溶剂化自由能。代码在电场中处理了溶剂诱导偶极，不能仅因旧文档未写就宣称两者完全不兼容；具体组合仍需检查对应的力和边界条件。

## 其他求解器与后处理

| 目标 | 可执行入口及关键边界 |
|---|---|
| PEXSI | `basis_type lcao`、`ks_solver pexsi`、相应编译支持；此版复数多 k 路径明确拒绝，需要实数 Γ 路径。密度矩阵输出与对角化本征对不同；温度/熵也不能直接套常规 KS 解析，见 [性能](abacus-performance.md) |
| OFDFT | `basis_type pw`、`esolver_type ofdft`、`nspin 1`；实际自旋极化分支拒绝 nspin=2/4，XC 拒绝 meta-GGA/杂化。需要适用的局域赝势模型，不能把一般含非局域投影子的 KS 赝势不加判断地照搬 |
| OFDFT 控制 | `of_kinetic wt\|tf\|vw\|tf+\|lkt`；`of_method tn\|cg1\|cg2`，bfgs 未实现；`of_conv energy\|potential\|both`；`of_tole` 默认 2e-6 Ry，`of_tolp` 默认 1e-5，是代码势梯度判据，不能简单等同总能误差。`of_wt_rho0` 单位 Bohr⁻³，非零自动开 `of_hold_rho0` |
| 随机/混合随机 DFT | `basis_type pw`、`esolver_type sdft`，确定性子空间用 nbands，随机轨道用 `nbands_sto`，切比雪夫阶数 `nche_sto`。误差还需对随机轨道数/种子和阶数收敛；显式 `nbands_sto 0` 会改为 ksdft，字面值 `all` 虽内部也存 0，却保留 sdft 调用 `init_com_orbitals` 构造完整基，二者不可混写 |
| LR-TDDFT | LCAO `esolver_type ks-lr` 先 KS 再响应，`lr` 从所需基态数据初始化；只支持 nspin=1/2。`xc_kernel rpa\|lda\|pwlda\|pbe\|hf\|hse`；`lr_solver dav\|dav_subspace\|cg\|lapack\|spectrum`。独立 lr 的数据依赖及 spectrum 的读写缺陷见下文 |
| LR 维数/谱 | 核对 `nocc/nvirt/nbands/lr_nstates` 的占据与虚轨道空间、`lr_thr` 收敛；`abs_wavelen_range` 单位 nm。**`abs_gauge` 是此版有效参数**，执行代码包含 length/velocity 分支；并非“文档查不到所以不可用”。尚无 LR 激发态解析力，不能据此安排激发态 relax |
| RT-TDDFT | `basis_type lcao`、`esolver_type tddft`，常规时间推进走 `calculation md`。本版电子传播主体只在 MPI 编译分支执行；非 MPI 路径不能因打印 evolve 时间就认为推进了波函数。传播步长实际使用 `md_dt`（fs），`td_force_dt` 仅赋值、未被传播器消费；起止 td_tstart/td_tend 为步号。另核对 td_propagator、空间/时间场型及输出，不套普通 AIMD 的步长 |
| QO | `qo_switch true`，源码有 `qo_basis szv\|pswfc\|hydrogen` 构造分支。pswfc 要实际赝势含所需轨道，不能仅凭赝势品牌判断；策略/屏蔽系数按类型给，允许的自动扩展与基组相关，不是一律填一个值 |
| 电导率 | `cal_cond true` 的 Kubo–Greenwood 路径实现在 PW KS/SDFT 中；`cond_dw/cond_wcut/cond_fwhm` 用 eV，`cond_smear 1/2` 分别 Gaussian/Lorentzian（错误文本仍误写 0/1）。`cond_dt` 是 **Ry⁻¹ 时间单位，约 0.0483777 fs**，与 MD 的 fs 和 Hartree 时间单位不同；谱展宽不等同电子占据温度 |
| RDMFT | LCAO 源码有 `rdmft` 后续计算分支；`rdmft_power_alpha` 初值 0.656，hf/pbe0 自动设 1、muller 自动设 0.5。实际 `run` 在传入的 KS 轨道/占据上计算能量及梯度，没有迭代优化循环，不能宣称已完成 RDMFT 轨道与占据优化 |

### LR-TDDFT 的文件与构建边界

- 独立 `esolver_type lr` 的常规 ABACUS 基态读入需要 `read_file_dir` 下的**文本 NAO 波函数**及各自旋 `SPIN*_CHG.cube`。基态应保存 `out_wfc_lcao 1`、`out_chg 1 10`，并核对结构、轨道、k 点、带空间、自旋与记录精度；只有 charge binary 或 `out_wfc_lcao 2` 的二进制系数不够。LR 的 `read_ks_chg` 直接读 cube，不走普通 KS 的 binary 优先回退流程。
- `lr_solver spectrum` 还需前次 `out_wfc_lr` 产生的激发能/振幅。实际在**当前输出目录**找 `Excitation_Energy_<label>.dat` 与 `Excitation_Amplitude_<label>_<rank>.dat`，不随 `read_file_dir` 自动迁移；振幅按 rank 分块，复用需保持相同维数、k 点和并行分布，不能只复制一个文件。
- **本版缺陷**：上述激发能/振幅的 `read_value/write_value` 被放进 `assert(...)`。定义 `NDEBUG` 的构建会完全移除这些读写调用；打开 `out_wfc_lr` 或设置 spectrum 都不能保证真正存取状态，打印的读取提示也不能证明成功。未修复时不能把这条重启路线当作可靠流程；可使用同一次已验证的 LR 求解及其直接光谱输出，或使用修复后验证过的实现。`ks_solver lapack` 的普通串行基态缺陷另见[性能卡](abacus-performance.md)，不要与 `lr_solver lapack` 混为一谈。
- **保留 assert 也不证明文件读写成功。** `LR_Util::read_value/write_value` 不检查文件打开、fail/eof 或写出状态，只返回请求/循环计数，断言因此可在文件缺失、截断或写出失败时仍通过。须独立检查所有文件的数据量、有限值、维数与来源；只改 Debug 构建不是完整修复。
- **独立 spectrum 的多 rank velocity 路径另有缺陷。** 激发能只在 rank 0 读取，未广播；其他 rank 的新建 ekb 保持零。`abs_gauge velocity` 在各 rank 用本地激发能作除数，再归约偶极，会引入非有限结果。即使保留 assert 且文件齐全，也不能推荐这个组合。优先在同次已验证的 LR 求解后直接求谱，或使用已修复并验证的重启实现；不能把这一特定除零机制扩张成所有 length 或单 rank 路径同样失效的证明。

依据：`source/module_lr/esolver_lrtd_lcao.cpp:309–339,439–446,521–537,595–599,671–726`；`source/module_io/read_wfc_nao.cpp:34–59`。NDEBUG 的调用消除已用原样提取的四个 lambda 编译验证；这不等于运行了完整 LR-TDDFT。

流状态及并行谱依据：`source/module_lr/utils/lr_util_print.h:15–55`；`source/module_lr/esolver_lrtd_lcao.cpp:437,521–537,560–565`；`source/module_lr/lr_spectrum.h:20–34`；`source/module_lr/lr_spectrum_velocity.cpp:69–107`；`source/module_base/matrix.h:34`、`source/module_base/matrix.cpp:122–146`。未检查流状态已用原样辅助函数执行复现；多 rank 光谱问题为调用链确认，未作 MPI 材料实测。

## 交付与复核

保留原始 INPUT、最终运行参数、编译信息、实际激活的能量/势项和必要的独立收敛测试。DFT+U 要核对投影及最终 U、EXX 核对双循环、D3 核对所选 XC 参数表、外场核对方向/真空/电荷、响应计算核对基态和激发子空间。某个开关被解析不代表任何求解器都会消费它；不要向用户给未经分派核实的组合保证。

## 源码定位

以下路径相对 ABACUS v3.10.1 根目录。

- `source/module_parameter/input_parameter.h:192,437-440,472,601`：势梯度阈值、溶剂、HSE 与 RDMFT 默认值。
- `source/module_io/read_input_item_exx_dftu.cpp:11-60,235-248,316-491`：EXX 默认、+U 检查、U 单位与 onsite 参数。
- `source/module_hamilt_lcao/hamilt_lcaodft/hamilt_lcao.cpp:218-240,360-383`；`source/module_hamilt_lcao/module_dftu/dftu.cpp:39-52,195-221,280-337,384-410`：+U 分支、MPI、占据矩阵及 Ueff 能量。
- `source/module_cell/read_atoms.cpp:97-123`；`source/module_esolver/esolver_ks_pw.cpp:348-387,411-461`；`source/module_hamilt_lcao/module_dftu/dftu_pw.cpp:15-78,145-203`：PW 投影、占据与势；`source/module_io/input_conv.cpp:241-254`、`source/module_esolver/esolver_ks_lcao.cpp:532-567`：U-ramping。
- `source/module_hamilt_pw/hamilt_pwdft/hamilt_pw.cpp:118–121`、`source/module_hamilt_pw/hamilt_pwdft/operator_pw/onsite_proj_pw.cpp:51–63`：PW +U 的布尔分派与投影调用。
- `source/module_hamilt_general/module_xc/xc_functional.cpp:318-345`；`source/module_io/input_conv.cpp:430-453`：泛函、编译和对称性限制。
- `source/module_hamilt_general/module_vdw/vdw.cpp:9-76`、`source/module_hamilt_general/module_vdw/vdwd3_autoset_xcparam.cpp:424-507`；`source/module_io/read_input_item_model.cpp:133-342`：vdW 工厂、XC 推断与参数覆盖。
- `source/module_io/read_input_item_model.cpp:10-130`；`source/module_elecstate/potentials/efield.cpp:68-104,290-318`、`source/module_elecstate/potentials/gatefield.cpp:25-127`：场、gate 和溶剂设置。
- `source/module_hamilt_general/module_surchem/cal_epsilon.cpp:8-17`、`source/module_hamilt_general/module_surchem/cal_vcav.cpp:43-57,99-153`；`source/module_elecstate/fp_energy.cpp:18-28`：空腔参数量纲、能量项。
- `source/module_esolver/esolver.cpp:27-95,218-274`；`source/module_io/read_input_item_ofdft.cpp:10-134`、`source/module_esolver/esolver_of.cpp:66-82`、`source/module_esolver/esolver_of_interface.cpp:16-209,246-248,376-378,486-488`：求解器分派与 OF 限制。
- `source/module_io/read_input_item_sdft.cpp:29-70`、`source/module_esolver/esolver_sdft_pw.cpp:45-72`：nbands_sto 0/all 的不同语义。
- `source/module_io/read_input_item_tddft.cpp:9-127,299-373`、`source/module_lr/esolver_lrtd_lcao.cpp:84-92,155-161,253-291`：TD 参数与 LR 限制。
- `source/module_hamilt_lcao/module_tddft/evolve_psi.cpp:34–99`、`source/module_hamilt_lcao/module_tddft/propagator.h:19–25`、`source/module_io/input_conv.cpp:77,278`：RT 传播的 MPI 条件与实际时间步。
- `source/module_io/read_input_item_other.cpp:143-258,500-528`、`source/module_io/to_qo_kernel.cpp:155-178,265-297`、`source/module_esolver/esolver_ks_lcao.cpp:263-276,1084-1105`、`source/module_rdmft/rdmft.cpp:414-435`：QO/RDMFT。
- `source/module_hamilt_pw/hamilt_pwdft/elecond.cpp:39-93`、`source/module_hamilt_pw/hamilt_stodft/sto_elecond.cpp:487-510`：电导率单位与真实 smear 枚举。
