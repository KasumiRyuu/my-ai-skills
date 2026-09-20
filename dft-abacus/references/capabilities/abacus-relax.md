<!-- capability_id: cap.abacus.relax | revision: 3 | source-audited: ABACUS v3.10.1 -->

# 结构优化：relax 与 cell-relax

按 3.10.1 的参数读取与执行代码选择优化分支，不能把旧示例中的双层循环套用于所有计算。先明确基组、可动原子/晶胞自由度、目标力/应力精度及电子态，再从模板生成输入。

## 算法与收敛

- `calculation relax` 固定晶胞；`cell-relax` 允许晶胞更新。两者自动打开 `cal_force`；后者自动打开 `cal_stress`。
- 默认 `relax_method cg`、`relax_new true` 使用新版共轭梯度，`cell-relax` 在同一优化流程中更新晶胞与原子。`relax_method` 合法值是 `cg|bfgs|sd|cg_bfgs|bfgs_trad`；任何非 `cg` 值都会把 `relax_new` 重置为 false。`fire` **不是**合法的 `relax_method`，它属于 MD 路径，而且此版本有阈值覆盖问题，见 [MD](abacus-md.md)。
- 旧版 `relax_new false` 的 `cell-relax` 先使原子弛豫收敛，再改晶胞，随后重新弛豫原子。不要把旧日志 `RELAX CELL/IONS` 的编号解释套到新版 CG。
- `force_thr`（Ry/Bohr）与 `force_thr_ev`（eV/Å）只设一个。默认 `0.001 Ry/Bohr ≈ 0.0257112 eV/Å`；**两者都设时 `force_thr` 覆盖 `force_thr_ev`，与 INPUT 行次序无关**。
- 新版力判据取允许移动分量的**最大绝对分量**，不是每个原子的向量模长或平均力。晶胞判据取施加晶胞约束后的最大应力梯度分量，默认 `stress_thr 0.5` kbar。`TOTAL-PRESSURE` 是迹的平均，不能代替应力张量/梯度的收敛检查；也没有“相邻两步都满足”这一通用要求。
- 旧版离子公共判据还检查 `|ΔE| < 1e-3 Ry`（最大梯度为零有独立分支）。旧版有固定晶轴时，晶胞公共判据用转换后的梯度并比较 **`10*stress_thr`**；因此不能把所有旧版优化都宣称为严格逐应力分量小于 `stress_thr`。
- `press1/2/3` 是三个方向的外压（kbar），在求解器返回应力前从对角分量减去；有外压时检查的是相对目标的残余应力。
- `scf_thr` 控制电子自洽，**不能一律标为 Ry 能量阈值**，须结合 `scf_thr_type` 和基组理解。可从 `1e-7` 等较紧设置试算，再收紧以检查力/应力变化是否小于目标误差；没有适用于所有体系的硬性数值。见 [收敛](abacus-convergence.md)。

## 约束与输入

`STRU` 的 `m` / 三个 0、1 移动标志控制原子自由度。固定胞下按实际坐标变化验证约束；对非正交晶胞、部分冻结及变胞组合，勿笼统承诺所有笛卡尔坐标或分数坐标都保持不变：新版代码同时对力分量和转换后的位移应用标志。

| 参数 | 3.10.1 行为 |
|---|---|
| `fixed_axes` | `None\|volume\|shape\|a\|b\|c\|ab\|ac\|bc\|abc`；字母指冻结对应晶格矢量，`abc` 全固定 |
| `volume` / `shape` | 仅支持 `relax_new true`；因此不能与自动切旧版的 BFGS 等组合 |
| `fixed_ibrav true` | 要求 `relax_new true` 且提供 `latname`；检查其与其他约束是否仍留自由度 |
| `fixed_atoms true` | 读取 STRU 时把所有原子移动标志置零；变胞时保持分数坐标，不能用于 `calculation relax` |
| `relax_nmax` | relax/cell-relax 未设时 50；0 会跳过优化循环，仍有初始化，不能代替 SCF/力精度验证 |
| `chg_extrap` | relax/cell-relax 默认 `first-order`，MD 默认 `second-order`；外推影响初值，不能补偿未收敛 SCF |
| `cell_factor` | 一般初值 1.2，cell-relax 中低于 2.0 会自动设为 2.0；它用于赝势表范围，不是晶胞步长 |

最小任务片段（完整骨架见模板；数值仅为需收敛测试的起点）：

```text
calculation       cell-relax
relax_method      cg
relax_new         true
relax_nmax        100
force_thr_ev      0.01
stress_thr        0.5
scf_thr           1e-8
out_stru          true
```

仅优化原子时改 `calculation relax`，无需应力阈值；若有真实电子温度，电子自由能/展宽必须按 [有限电子温度](../finite-temperature.md) 设定，不能从离子优化推定温度。

## 输出、停止与重开

- 每次优化步骤后都写 `OUT.<suffix>/STRU_ION_D` 与 `STRU_NOW.cif`；`out_stru true` 额外写 `STRU_ION<istep>_D`。这些并非 PW 专属。后续计算优先复用 ABACUS 格式 `STRU_ION_D`，并检查赝势、轨道路径及约束；CIF 不保留完整 ABACUS 输入语义。PW +U 依赖 onsite 数值轨道，但此版输出的 `need_orb` 判定未包含 onsite_radius；若 init_wfc 不是 nao 开头，输出结构可能漏掉 NUMERICAL_ORBITAL。续用时从原始 STRU 恢复该块并核对轨道文件。
- **每个发生位移的优化步都可能有几何与标签错位。** 驱动先求旧几何的能量/力/应力，再更新位置或晶胞，最后写 `STRU_ION_D`、`STRU_ION<istep>_D`；同一步号不证明它们属于同一构型。启用 JSON 时也会把旧标签与已更新的 ucell 一起写出。抽取训练数据须追踪进入求解器的实际几何，或对选中输出结构另做同设置 SCF/力/应力；不要机械平移旧版局部步号。已收敛且没有再次移动的步骤不受此错位条件影响。
- **“程序结束”与“结构收敛”必须分别判断。** 旧版在 `istep == relax_nmax` 直接返回 stop；新版上限处还可能完成下一次位移。到达上限或手停后，核验所选最终结构及其对应的已收敛力/应力，不要把末尾能量自动贴给输出坐标。
- `EXIT` 文件写 `stop_ion true`，驱动在当前离子步的结构输出之后检查并停止；它不说明已达到阈值。重开前移走该停止文件，防止下一次又停。
- 从输出结构开始新的 relax 是恢复几何，不是恢复 BFGS/CG 历史；电荷重用另需匹配 `out_chg`、`init_chg file` 与读入目录；LCAO Γ 的二进制密度头兼容性及 cube 回退限制见 [输出与续算](abacus-output-reading.md)，不能保证仅保存二进制就能恢复。
- 磁性任务核查输出 STRU 的逐原子磁矩：默认 `out_mul false` 会丢失这些初值，同元素 AFM 用 atomic 密度重开时可能被自动设成同向初磁。恢复目标磁矩/方向或匹配的磁化密度；PW 不能靠开启 out_mul 修复。详见[磁性续算](abacus-magnetism-soc.md)。
- 交付：输入、最终结构、优化分支、电子收敛证据、最大可动方向力和相对目标的应力、结束原因。冻结自由度的非零力可存在，需报告而不能伪称“全体系所有力都收敛”。

## 源码定位

以下路径相对 ABACUS v3.10.1 根目录；结论来自执行代码，未用旧版 example 日志作为当前行为证据。

- `source/module_io/read_input_item_relax.cpp:10-134,171-210`：算法枚举、`relax_new` 自动重置、力阈值优先级及约束。
- `source/module_parameter/input_parameter.h:155-175`；`source/module_io/read_input_item_system.cpp:186-228,445-453,562-582`：默认值、自动力/应力、cell_factor 和电荷外推。
- `source/module_relax/relax_new/relax.cpp:57-94,97-283,484-636`：联合更新、投影梯度判据与约束。
- `source/module_relax/relax_old/relax_old.cpp:25-147`；`source/module_relax/relax_old/ions_move_basic.cpp:119-183`、`source/module_relax/relax_old/lattice_change_basic.cpp:163-245`：旧版循环、能量和约束应力判据。
- `source/module_cell/unitcell.cpp:821-884`、`source/module_cell/read_atoms.cpp:832-843`：固定晶轴与冻结原子。
- `source/module_esolver/esolver_ks_pw.cpp:781-790`、`source/module_hamilt_lcao/hamilt_lcaodft/FORCE_STRESS.cpp:830-842`：先输出内部应力，再从返回的应力扣外压。
- `source/module_relax/relax_driver.cpp:34-150`、`source/module_io/read_exit_file.cpp:14-108`：输出时点、上限和 EXIT。
- `source/module_io/json_output/output_info.cpp:43–125`：JSON 直接使用传入的当前几何，不能消除优化更新前后错位。

配套：[relax 模板](../../templates/INPUT.relax.tpl)、[cell-relax 模板](../../templates/INPUT.cell-relax.tpl)。
