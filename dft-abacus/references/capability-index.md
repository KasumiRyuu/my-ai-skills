# 能力索引

| 能力 | 意图与关键词 | 参考卡 |
|---|---|---|
| input-files | INPUT_PARAMETERS、STRU 坐标/物种、ntype、KPT、数据路径、解析 | [输入文件](capabilities/abacus-input-files.md) |
| accuracy | PW/LCAO、ecutwfc/ecutrho、kspacing、gamma_only、赝势/轨道、收敛测试 | [精度](capabilities/abacus-accuracy.md) |
| static | scf、init_chg/init_wfc、ks_solver、nbands、电子温度/熵 | [单点](capabilities/abacus-static.md)，[有限电子温度](finite-temperature.md) |
| relax | relax/cell-relax、force_thr_ev、stress_thr、约束、优化续算 | [优化](capabilities/abacus-relax.md) |
| md | AIMD、md_type/md_dt、离子温度、NVE/NVT/NPT、MD_dump、续算 | [分子动力学](capabilities/abacus-md.md) |
| electronic | nscf、能带、DOS/PDOS、波函数、电荷/势、Berry phase、Wannier90、矩阵 | [电子结构](capabilities/abacus-electronic.md) |
| convergence | DRHO、scf_thr_type、混合、占据、磁态、对角化 | [收敛排障](capabilities/abacus-convergence.md) |
| magnetism-soc | nspin、FM/AFM、初始磁矩、noncolin、SOC、nupdown、约束 | [磁性](capabilities/abacus-magnetism-soc.md) |
| performance | kpar/bndpar、MPI/OpenMP、GPU、OOM、耗时 | [性能](capabilities/abacus-performance.md) |
| ml-ecosystem | DeePKS、DPMD、dpdata、DP-GEN、phonopy、ASE、训练标签 | [生态](capabilities/abacus-ml-ecosystem.md) |
| advanced-functionals | DFT+U、HSE/EXX、vdW、外场/溶剂、PEXSI、OFDFT/SDFT/TDDFT | [高级功能](capabilities/abacus-advanced-functionals.md) |
| output-reading | OUT.<suffix>、日志、FINAL_ETOT_IS、能量/力/应力、完成与收敛 | [输出](capabilities/abacus-output-reading.md) |

具体任务子技能见[主入口](../SKILL.md)。需要参数来源时读[源码依据](source-audit.md)。
