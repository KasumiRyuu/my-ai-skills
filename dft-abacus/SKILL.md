---
name: dft-abacus
description: >-
  Prepare, review and troubleshoot ABACUS v3.10.1 DFT calculations using
  source-verified input rules. Use for INPUT/STRU/KPT, PW/LCAO accuracy,
  SCF, electronic temperature and entropy, relax/cell-relax, AIMD,
  bands/DOS, magnetism/SOC, advanced functionals, outputs, and performance/OOM.
  中文：ABACUS 输入、电子温度与展宽、收敛、结构优化、分子动力学及结果判读。
  Excludes other DFT programs and software installation or source development.
license: LGPL-3.0
metadata:
  version: 0.2.1
  author: D. Liu
  source: ABACUS v3.10.1 implementation
  source-commit: f71921fe848659deac8db319cd4311b55b5ad480
  source-repository: https://github.com/deepmodeling/abacus-develop
  source-license: LGPL-3.0
  audited-on: 2026-09-21
  abacus.bundle-id: bundle.abacus-dft
  abacus.capability-count: 12
---
# ABACUS v3.10.1

以 v3.10.1 的参数解析器、运行分支和输出实现为准。版本基线与代码定位见
[源码依据](references/source-audit.md)。遇到其他版本或本地补丁，应重新核对相关代码，不能把本版缺陷推广为通用用法。

## 使用方式

按实际任务读取对应子技能；跨域任务按需补读相关卡，不设固定数量上限。
参数含义的短问直接查相关条目，不必要求用户先提供完整结构。
准备可运行计算时检查结构、赝势、轨道和目标精度；用户已给出晶格与坐标信息时可据此生成 STRU。
缺数据时可以交付明确标注的骨架，但不可声称占位符模板已能运行。

| 任务 | 先读 |
|---|---|
| INPUT/STRU/KPT、文件解析、坐标、路径 | [inputs](inputs/SKILL.md) |
| PW/LCAO、截断能、k 点、赝势与轨道、精度收敛 | [accuracy](accuracy/SKILL.md) |
| SCF、初始化、总能、求解器 | [static](static/SKILL.md) |
| 电子温度、电子熵、sigma 与 sigma_temp、4000 K | [有限电子温度](references/finite-temperature.md)，结合 [static](static/SKILL.md) |
| 原子或晶胞优化 | [relax](relax/SKILL.md) |
| AIMD、系综、轨迹、续算 | [md](md/SKILL.md) |
| 能带、DOS/PDOS、电荷/势/波函数、Berry phase、Wannier90、H/S | [electronic](electronic/SKILL.md) |
| SCF 振荡、混合、占据、对角化失败 | [convergence](convergence/SKILL.md) |
| 磁性、SOC、磁约束 | [磁性卡](references/capabilities/abacus-magnetism-soc.md) |
| 速度、内存、MPI/OpenMP、GPU | [性能卡](references/capabilities/abacus-performance.md) |
| DFT+U、杂化泛函、vdW、外场、OFDFT/SDFT/TDDFT | [高级功能卡](references/capabilities/abacus-advanced-functionals.md) |
| DeePKS、DeePMD、训练标签、外部工具接口 | [生态卡](references/capabilities/abacus-ml-ecosystem.md) |
| 日志、是否收敛、能量/力/应力含义 | [输出卡](references/capabilities/abacus-output-reading.md) |

## 共同约束

1. `INPUT` 使用 `INPUT_PARAMETERS` 标记，每行一个参数；未知参数和重复的同名参数报错。`ntype` 可以自动从 STRU 推断，显式指定时必须一致。
2. 普通 DFT 需要结构和实际赝势文件；LCAO 还需相配的数值轨道。KPT 可由有效的 `gamma_only` 或 `kspacing` 生成，这会改写所选 k 点文件。路径计算必须关闭这些自动网格设置。
3. `ecutwfc`、`ecutrho`、`smearing_sigma` 用 Ry；`force_thr_ev` 用 eV/Å，`stress_thr` 用 kbar。`scf_thr` 是密度残差阈值，其定义随 `scf_thr_type` 变化，不能统一写成能量或 Ry 阈值。
4. 区分数值展宽和物理电子温度。有限电子温度用 `fd`，检查高能端占据和 `nbands` 收敛；本版 `smearing_sigma_temp` 有半温度问题，按[专门说明](references/finite-temperature.md)处理。
5. `calculation` 切换必须重新检查初始化、输出依赖、k 点、对称性、基组和求解器；不能只改一行就假定所有后处理或续算成立。
6. SCF 排障先判断密度、能量、占据、磁态、基组和对角化证据；不要固定认为所有问题都是混合参数造成。保持目标电子温度不变。
7. `!FINAL_ETOT_IS` 不证明已收敛；常规 KS 路径的该量包含展宽修正，FD 时含 `-TS`。用日志里的收敛状态与完整能量定义共同判断。
8. `OUT.<suffix>/INPUT` 记录解析、默认和重置后的可序列化参数，不是原始输入副本，也不是所有后续运行状态。应同时保存用户 INPUT 和运行日志。
9. 本版普通串行 LCAO 的 `ks_solver lapack` 有波函数未回写等实现缺陷，不能只因为它是默认值就推荐；MPI 构建单 rank 与非 MPI 构建不同，见[性能卡](references/capabilities/abacus-performance.md)。
10. 读取/写出成功不证明数据语义正确。投影、Berry、部分电荷、磁态续算和优化训练标签须先读各自卡片的构建、自旋、并行及输出时序限制。

## 交付与验证

按请求给出文件、关键物理假设、精度收敛方案和结果验收方式。只有用户要求执行时才安排实际计算；依据现有资源选择运行规模，不虚构赝势或轨道文件名。

[模板](templates/README.md)仅作为起点；替换全部占位符并检查目标分支。
[运行说明](references/commands-and-workflow.md)解释 `--check-input` 的能力边界。
[术语表](references/glossary.md)用于短问，[决策速查](references/cheatsheet.md)用于定位重点。
