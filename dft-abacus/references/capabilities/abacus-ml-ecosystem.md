<!-- capability_id: cap.abacus.ml-ecosystem | revision: 3 | source-audited: ABACUS v3.10.1 -->

# ML 势、训练标签与外部接口

本卡核对 ABACUS v3.10.1 的输入分派、输出格式和单位。dpdata、DP-GEN、ASE、Phonopy、ShengBTE、DeepH、DeePTB、TB2J、PYATB、Hefei-NAMD、CANDELA 等的版本/API 由各自安装包决定；不能用 ABACUS 旧文档中的版本号、JSON 字段或 Python 构造函数作为当前兼容性保证。实际对接时读已安装转换器实现及版本信息，并用一个可手算核对的构型验证数据。

## 从 DFT 生成训练标签

选择 `calculation scf`、`cal_force true`，需要应力时加 `cal_stress true`，对每个指定构型独立求已收敛电子态。位移超胞标签不能先 relax，否则力不再属于指定构型。AIMD 可提供连续轨迹，但必须逐步关联构型、能量和力；不能把运行末尾的唯一最终能量复制给所有帧。

优化轨迹另有本版时序问题：每次实际位移发生在能量/力计算之后、STRU/JSON 写出之前，因此同一步号的输出几何与力能可能不属于同一构型，**不限于末步或达到上限的情况**。不要直接把 STRU_IONi_D 或 JSON 对象当成可用训练样本；按求解器输入几何核对，或对选中结构重新做标签 SCF。依据：`source/module_relax/relax_driver.cpp:51–140`；`source/module_io/json_output/output_info.cpp:43–125`。

| 数据 | ABACUS 侧口径与检查 |
|---|---|
| 能量 | 普通 KS `!FINAL_ETOT_IS ... eV` 来自 `f_en.etot`；它只表示该次最终电子能量。MD 每帧能量须从对应步号日志提取，MD_dump 本身不含能量 |
| 电子熵 | 有 Fermi–Dirac 有限电子温度时，etot 含 `−TS`，是电子自由能 F；与相应力匹配的势面也是固定电子温度的 F。不要将 U 或零温外推能量与这些力混作同一保守势标签。跨电子温度数据须记录温度及模型条件，见 [有限电子温度](../finite-temperature.md) |
| 原子力 | 日志 `TOTAL-FORCE (eV/Angstrom)` 与 MD_dump 力列均 eV/Å；核对类型、原子顺序、冻结自由度、SCF 收敛及实际构型 |
| 应力 | 日志 TOTAL-STRESS 和 MD_dump 的 `VIRIAL (kbar)` 是应力/压力维度；不含离子动能项。普通 PW/LCAO KS 的 TOTAL-STRESS 在扣 `press1/2/3` 外压前打印，MD_dump 则使用扣除后的返回应力；DP 的日志也在扣除后打印。制标签时通常将外压设零，否则按实际来源处理，不能统一再加或再减一次 |
| 训练 virial | 下游若要 eV，需以体积及单位转换并核对正负号；`1 kbar·Å³ ≈ 0.0006241509 eV`。ABACUS DP 回读分支使用 `stress=virial/volume`，不能据此假设所有外部包采用相同符号 |
| 坐标/晶格 | MD_dump 坐标 Å，晶格为 `LATTICE_CONSTANT`（Å）乘 `LATTICE_VECTORS`；转换前不要把两者任意一项当作完整晶格 |
| 旋转 | 如转换器旋转晶胞，须同步旋转坐标、力及应力张量；不能一概禁止某个转换包，也不能只旋转晶格后直接沿用原力分量 |

固定有限电子温度的 NVE 验证检查 `K_ion + F_electronic` 漂移；带热浴时不能要求此量严格守恒。数据转换验收至少核对原子数/类型/顺序、晶胞体积、一帧能量、全部力分量和完整应力张量，并用有限位移/应变核验所选能量、力和 virial 的导数与符号约定。外部转换成功不等于标签语义正确。

## 用 DP 模型直接计算能量、力或 MD

`esolver_type dp` 选择 DeePMD 势，独立于 DFT 的波函数基组。构建须有 `__DPMD` 及相容的 DeePMD 库；`pot_file` 交给其 `DeepPot` 构造器读取，默认 graph.pb，但合法模型格式由所链接库决定。模型类型映射按 STRU 元素标签匹配，缺失标签会明确退出。

以下是加在匹配 STRU 的任务片段；温度和时长仅作短程核验起点：

```text
calculation       md
esolver_type      dp
basis_type        pw
pot_file          graph.pb
md_type           nvt
md_thermostat     nhc
md_tfirst         300
md_tlast          300
md_dt             1
md_nstep          10
```

这里 `basis_type pw` 避免引入 LCAO 轨道输入需求，并不让 DP 模型使用平面波。`dp_fparam/dp_aparam` 原样传入模型，维数和物理意义必须匹配模型定义；它们不是自动识别电子温度的开关。`dp_rescaling` 默认 1，统一乘在能量、力与 virial 上，不能把任意缩放宣称为正确的温度修正。

ABACUS 送入 DeePMD 的坐标和晶格用 Å，接收能量 eV、力 eV/Å、virial eV，再转内部 Ry/Bohr。核对模型训练单位、type_map、截断及适用状态范围；输出出现 MD_dump 不足以证明模型准确。积分、系综、checkpoint 和累计步数的规则见 [MD](abacus-md.md)。

## DeePKS：模型修正与标签输出

DeePKS 执行点在 LCAO Hamiltonian/ESolver 路径；使用相应编译支持及 STRU 的 `NUMERICAL_DESCRIPTOR` 投影文件，不能把相同开关放到 PW INPUT 就宣称有效。`deepks_scf true` 加模型修正，`deepks_out_labels true` 导出描述符/标签；二者是独立用途。

```text
basis_type        lcao
deepks_scf        true
deepks_model      model.ptg
# deepks_out_labels true
```

模型通过 `torch::jit::load` 读取，文件扩展名不是兼容性证明。`deepks_equiv` 与 `deepks_bandgap` 同时打开在本版会退出；不要把该条件扩张为“所有 equiv 功能都未实现”。标签文件按开关产生，例如 `deepks_etot.npy`、`deepks_ebase.npy`；其中能量数组直接保存内部 etot，**单位 Ry**，不同于日志的 eV。每类张量必须检查写出代码，不要假设全部 npy 文件共享日志单位。

生成球贝塞尔描述符是另一次 `calculation gen_bessel` 作业：`bessel_descriptor_lmax`、`bessel_descriptor_ecut`（Ry）、`bessel_descriptor_rcut`（Bohr）、`bessel_descriptor_tolerence`（源码就这样拼写），输出位于 OUT 目录的 `jle.orb`。生成的投影轨道须与模型训练时的定义匹配。

## 矩阵与后处理对接

- DeepH / DeePTB / TB2J / PYATB 等所需的 LCAO H(R)、S(R)、位置矩阵及自旋表示，见 [电子结构输出](abacus-electronic.md)。`out_mat_hs2` 的 R 空间输出走复数 k 路径，输入检查拒绝与 `gamma_only true` 组合；下游实数输出函数也为空，不能期待自动转换。单 Γ 点可用 `gamma_only false` 走所需路径。
- 只需要 S(R) 时 `calculation get_S` 有独立求解器，要求 LCAO 且不走 gamma_only；输出 SR.csr。它不提供自洽 H(R)、占据或费米能，不能把它与完整 SCF 放在同一片段当成等价任务。
- Phonopy / ShengBTE 的 ABACUS 侧入口是指定构型的 SCF 力。下游力常数单位由转换器使用的位移单位和力单位共同决定；不要无条件套用旧版 `eV/(Å·Bohr)` 再乘固定换算。核对实际 parser 与 force-constant 文件定义，并保留构型编号和原子映射。
- Wannier90 所需 SCF/NSCF、k 点、nnkp、波函数及格式设置见 [电子结构输出](abacus-electronic.md)。外部程序生成和消费哪些文件，由其安装版本核对。
- ASE、DP-GEN、dpdata 等驱动/转换层不能改变 ABACUS INPUT 的实际含义。先生成并检查具体 INPUT/STRU/KPT；启动命令、环境变量、JSON/Python API 从安装版本读取，不在本卡硬编码未经核验的接口。

## 源码定位

路径相对 ABACUS v3.10.1 根目录。

- `source/module_esolver/esolver_ks_pw.cpp:725-727,781-799`、`source/module_esolver/esolver_ks_lcao.cpp:288-292,375-376`、`source/module_elecstate/fp_energy.cpp:18-28`：返回能量与最终 eV 日志；`source/module_hamilt_lcao/hamilt_lcaodft/FORCE_STRESS.cpp:830-847`：LCAO 外压扣除。
- `source/module_md/md_func.cpp:247-281,319-408`、`source/module_md/md_base.cpp:144-215`：MD 势能来源、dump 单位和压力动能项。
- `source/module_esolver/esolver.cpp:82-94,270-274`、`source/module_esolver/esolver_dp.h:17-29`、`source/module_esolver/esolver_dp.cpp:34-121,129-147,158-205`：DP 分派、模型读取、单位、缩放和类型映射。
- `source/module_io/read_input_item_md.cpp:215-252`、`source/module_parameter/md_parameter.h:31-39`：模型输入参数。
- `source/module_io/read_input_item_deepks.cpp:10-82,85-137`、`source/module_cell/read_atoms.cpp:115-123`：DeePKS 开关检查和描述符。
- `source/module_hamilt_lcao/module_deepks/LCAO_deepks_torch.cpp:142-158`、`source/module_hamilt_lcao/module_deepks/LCAO_deepks_interface.cpp:40-57,162-248`、`source/module_hamilt_lcao/module_deepks/LCAO_deepks_io.cpp:239-254`：模型加载、npy 输出及原始能量单位。
- `source/module_esolver/pw_others.cpp:60-72`、`source/module_io/bessel_basis.cpp:221-235`：gen_bessel 输出。
- `source/module_io/read_input_item_output.cpp:380-393`、`source/module_io/output_mat_sparse.cpp:15-88`、`source/module_esolver/esolver_gets.cpp:135-137`、`source/module_esolver/esolver.cpp:188-199`：R 空间矩阵限制与 get_S 的实际输出路径。
