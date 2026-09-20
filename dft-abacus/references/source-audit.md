# ABACUS v3.10.1 源码依据与复核入口

本包针对 tag `v3.10.1`，commit `f71921fe848659deac8db319cd4311b55b5ad480`。
2026-09-21 核查的本地目录为 `/mnt/e/Software/ABACUS/soucecode/abacus_v3.10.1`；起始时 git 工作区干净，`source/version.h` 为 v3.10.1。以下路径相对此源码根目录。迁移到其他版本时重新核对，不沿用本版的已知缺陷处理方法。

## 怎样核对一个结论

1. 在 `source/module_parameter/input_parameter.h` / `md_parameter.h` 找成员及初始值。
2. 在 `source/module_io/read_input_item_*.cpp` 找 `read_value`、`reset_value`、`check_value`。成员初始值不等于最终默认值，解析通过也不等于运行分支支持。
3. 追踪 `read_input.cpp` 的执行顺序与 `input_conv.cpp`、`read_set_globalv.cpp` 的后续转换。
4. 追到求解器/占据/力/输出实现，核对单位、文件名和真正使用的变量。注释、报错文案、死代码都不能单独证明行为。
5. 把调用链与适用基组、求解器、编译条件一起记录。外部软件解析器、实际材料精度和耗时不由本仓源码单独证明。

## 关键结论与实现定位

| 主题 | 实现事实或纠正点 | 源码定位 |
|---|---|---|
| INPUT 读取 | 参数名转小写；同名重复报错；各 read_value 依输入出现顺序执行 | `source/module_io/read_input.cpp:178`，特别是 224、230、231、271 |
| 参数值长度 | 参数值由 getline 读整行；150 字符限制是其他跳过分支，不能泛化 | `source/module_io/read_input.cpp:69,199,249` |
| ntype | 默认0从STRU计数；显式数目不符报错 | `source/module_io/read_input.cpp:400` |
| 自检 | --check-input 在参数解析/重置/检查及物种计数后退出，不完成完整初始化/SCF | `source/module_io/parse_args.cpp:12`；`source/module_io/read_input.cpp:113` |
| 参数快照 | get_final_value 输出当时参数，不是纯初始默认值；随后还有 Input_Conv | `source/module_io/read_input.cpp:304`；`source/driver.cpp:108` |
| 4000 K、FD | sigma_temp×3.166815e-6直接写入Ry sigma；FD指数为(EF−E)/sigma，未补2倍 | `source/module_io/read_input_item_elec_stru.cpp:382`；`source/module_io/input_conv.cpp:465`；`source/module_elecstate/occupy.cpp:237,428` |
| 两种 sigma | 写同一变量、后出现者覆盖；区别于同名重复报错 | `source/module_io/read_input.cpp:230,271`；`source/module_io/read_input_item_elec_stru.cpp:400` |
| 展宽别名 | 输入合法列表中mp3与marzari-vanderbilt缺逗号，不能按低层支持推断可输入 | `source/module_io/read_input_item_elec_stru.cpp:382`；`source/module_elecstate/occupy.cpp:29` |
| 电子熵与能量 | FD的demet为−TS，常规etot加demet；显示的sigma→0量另有公式 | `source/module_elecstate/occupy.cpp:237,510`；`source/module_elecstate/fp_energy.cpp:18`；`source/module_elecstate/elecstate_print.cpp:314` |
| 热XC | xc_temperature独立，LibXC热泛函接收其Hartree换算；不自动跟随占据展宽 | `source/module_parameter/input_parameter.h:82`；`source/module_hamilt_general/module_xc/xc_functional_libxc.cpp:129` |
| SCF判据 | 类型1倒空间度量、类型2电子数归一化L1；能量阈值为附加条件 | `source/module_elecstate/module_charge/charge_mixing_residual.cpp:7`；`source/module_io/read_input_item_elec_stru.cpp:581`；见[收敛卡](capabilities/abacus-convergence.md) |
| 默认带数 | 自旋分支、取整、LCAO轨道维数上限；默认带数不保证高温尾部收敛 | `source/module_elecstate/cal_nelec_nband.cpp:61` |
| KPT自动生成 | LCAO gamma_only和正kspacing会改写选定文件；PW gamma_only被重置并写Γ文件 | `source/module_cell/klist.cpp:197`；`source/module_io/read_input_item_elec_stru.cpp:538` |
| 截断能 | 默认ecutrho=4×ecutwfc；较小比值超出容差会报错 | `source/module_io/read_input_item_system.cpp:274` |
| NSCF初始化 | init_chg被重置为file；不是遗漏关键词就回退原子密度 | `source/module_io/read_input_item_system.cpp:510` |
| out_chg | 2经布尔解析会报错；-1是特殊值；不能因下游有==2分支就推荐输入2 | `source/module_io/read_input_item_output.cpp:41`；`source/module_io/read_input.cpp:24` |
| 密度读写 | 默认0仍可写二进制备份，读取优先二进制再cube | `source/module_esolver/esolver_fp.cpp:143,289`；`source/module_elecstate/module_charge/charge_init.cpp:41` |
| Γ密度重启缺陷 | LCAO Gamma-only binary头为true，FP电荷基组为false，read_rhog拒绝；需核验cube回退 | `source/module_esolver/esolver_fp.cpp:84,109,303`；`source/module_io/rhog_io.cpp:52–80,232–252` |
| DOS/PDOS/Berry | 多k与Γ分支不同；累计DOS列、Berry占据维数均需按实现解释 | 见[电子结构卡](capabilities/abacus-electronic.md)的逐分支定位 |
| Wannier90 | nnkp逐点匹配、有效KPAR=1；LCAO方法2的out_unk为空 | `source/module_io/to_wannier90.cpp:14–40,134–237`；`source/module_io/to_wannier90_lcao.cpp:262` |
| 外压与应力 | PW/LCAO KS在扣外压前打印应力，返回值已扣外压；MD_dump写返回应力且不含离子动能 | [输出卡](capabilities/abacus-output-reading.md)与[MD卡](capabilities/abacus-md.md) |
| 两种力阈值 | reset中force_thr优先，不按INPUT行顺序竞争；默认约0.0257112eV/Å | `source/module_io/read_input_item_relax.cpp:96` |
| 优化算法 | 非cg关闭relax_new；FIRE不是relax_method合法值 | `source/module_io/read_input_item_relax.cpp:11`；[优化卡](capabilities/abacus-relax.md) |
| MD与续算 | 离子温度、频率、状态文件/路径、总步数和FIRE阈值有独立实现 | [MD卡](capabilities/abacus-md.md)的完整定位 |
| DFT+U | 有受限PW路线，不能统一说仅LCAO；需投影与自旋条件 | `source/module_io/read_input_item_exx_dftu.cpp:342`；`source/module_esolver/esolver_ks_pw.cpp:384`；[高级卡](capabilities/abacus-advanced-functionals.md) |
| 自旋约束 | sc_mag_switch开关在输入检查中被阻止；显式nupdown=0也会启用双费米能，见磁性卡 | `source/module_io/read_input_item_other.cpp:16`；[磁性卡](capabilities/abacus-magnetism-soc.md) |
| 并行 | 非SDFT重设bndpar=1；部分LCAO求解器有k点池，输入警告不能单独作“不支持”的证据 | `source/module_io/read_input_item_system.cpp:245`；`source/module_hsolver/hsolver_lcao.cpp:48`；[性能卡](capabilities/abacus-performance.md) |
| 数据接口 | 输出单位与熵口径由ABACUS核对，外部包行为需核对其版本与实现 | [生态卡](capabilities/abacus-ml-ecosystem.md) |

## 实现限制与适用条件

下表列出执行代码中的限制与适用条件，相关说明见任务卡和模板。源码确认与提取执行的验证方式及覆盖范围见[验证记录](../test-results.md)。

| ID | 结论与限制 | 源码入口与任务说明 |
|---|---|---|
| IN-01 | 普通串行 LCAO LAPACK 未回写 psi，并将 nlocal 个本征值写入 nbands 行 | `source/module_hsolver/diago_lapack.cpp:19–55,58–250`；[性能](capabilities/abacus-performance.md) |
| IN-02 | LCAO 双网格的局域势与电荷/势容器混用平滑和稠密基组 | `source/module_esolver/esolver_ks_lcao.cpp:136–142,204–217`；[精度](capabilities/abacus-accuracy.md) |
| IN-03 | ndz 重置误检查 ndy，仅 z 加密可能未启用 double_grid | `source/module_io/read_input_item_system.cpp:374–427`；[精度](capabilities/abacus-accuracy.md) |
| IN-04 | stod/stoi 不验证消费完字符串，d 指数/整数科学计数法可静默取前缀 | `source/module_io/read_input_tool.h:8–11,138–150`；[输入](capabilities/abacus-input-files.md) |
| RO-01 | Gamma-only nspin=2 PDOS/TDOS 下自旋错用上自旋能级 | `source/module_io/write_dos_lcao.cpp:121–141`；[电子结构](capabilities/abacus-electronic.md) |
| RO-02 | 非 MPI PDOS/PBANDS 投影全零，LCAO get_pchg 则拒绝 | `source/module_io/write_dos_lcao.cpp:149–189`；`source/module_io/write_proj_band_lcao.cpp:60–95` |
| RO-03 | PW init_chg=wfc 依赖 istate.info，nspin=2 原生读写格式不兼容 | `source/module_io/read_wfc_to_rho.cpp:35–50`；`source/module_io/write_istate_info.cpp:55–79` |
| RO-04 | PW 多 k NSCF mem_saver=1 后只留最后 k 波函数，影响后处理 | `source/module_psi/psi_init.cpp:191–203`；`source/module_esolver/esolver_ks_pw.cpp:633–699` |
| RO-05 | PW bands_to_print 多池遗漏贡献，spinor 第一分量及 k 编号处理不完整 | `source/module_io/get_pchg_pw.h:92–149`；`source/module_io/write_cube.cpp:37–48` |
| RO-06 | 部分电荷的 PW/LCAO、Γ/多 k 权重与占据规则不同 | `source/module_io/get_pchg_pw.h:101–148`；`source/module_io/get_pchg_lcao.cpp:466–533` |
| RO-07 | PW out_wfc_r 是未除 Ω 的原始模平方，未含完整 spinor | `source/module_io/write_wfc_r.cpp:102–143,179–188`；[电子结构](capabilities/abacus-electronic.md) |
| RO-08 | LCAO spinor Berry 电子相位为空；PW Berry 需要实际 KPAR=1 和全部 k 态 | `source/module_io/berryphase.cpp:248–397`；`source/module_io/unk_overlap_pw.cpp:32–59` |
| RO-09 | PW/方法1 UNK 仅 MPI writer，spinor 仅写第一分量 | `source/module_io/to_wannier90_pw.cpp:188–352`；[电子结构](capabilities/abacus-electronic.md) |
| RO-10 | bxsf writer 留网格占位、混用 Ry/eV、未筛选自旋，不能直接用于费米面 | `source/module_io/nscf_fermi_surf.cpp:17–87`；`source/module_io/dos_nao.cpp:42–59` |
| RO-11 | cube 成功返回不保证数据完整或几何相容 | `source/module_io/read_cube.cpp:35–73,145–193`；[输出](capabilities/abacus-output-reading.md) |
| C1 | 全零磁矩自动替换存在开关/阈值条件，非共线向量与角度可不一致 | `source/module_cell/read_atoms.cpp:850–895`；`source/module_elecstate/module_charge/charge.cpp:572–608` |
| C2 | 默认几何输出丢失逐原子磁矩，AFM atomic 重开可能变同向初磁 | `source/module_cell/read_atoms.cpp:844–847,1031–1054`；[磁性](capabilities/abacus-magnetism-soc.md) |
| C3 | FIRE 判停和速度混合没有按可动分量投影 | `source/module_md/fire.cpp:155–205`；[MD](capabilities/abacus-md.md) |
| C4 | MSST 专用速度推进未屏蔽冻结方向，仍计入动能/温度/应力 | `source/module_md/msst.cpp:272–300`；[MD](capabilities/abacus-md.md) |
| C5 | NPT/MSST 不执行 relax 晶胞约束，冻结原子仍随变胞仿射移动 | `source/module_md/nhchain.cpp:26–79,722–812`；`source/module_cell/update_cell.cpp:327–331` |
| C6 | 每个发生位移的优化步，STRU/JSON 的新几何可配上旧力能 | `source/module_relax/relax_driver.cpp:51–140`；[生态](capabilities/abacus-ml-ecosystem.md) |
| AP-01 | 独立 LR 需要文本 NAO WFC 与 cube，不套普通密度 binary 优先规则 | `source/module_lr/esolver_lrtd_lcao.cpp:309–339`；[高级](capabilities/abacus-advanced-functionals.md) |
| AP-02 | spectrum 态文件从当前输出目录按 rank 读取，另受维数/并行布局约束 | `source/module_lr/esolver_lrtd_lcao.cpp:439–446,521–537`；[高级](capabilities/abacus-advanced-functionals.md) |
| AP-03 | LR 态文件 read/write 放在 assert 中，NDEBUG 会移除这些 I/O | `source/module_lr/esolver_lrtd_lcao.cpp:439–446,521–537`；[高级](capabilities/abacus-advanced-functionals.md) |
| AP-04 | RT 传播主体需 MPI，实际步长用 md_dt，td_force_dt 无该执行用途 | `source/module_hamilt_lcao/module_tddft/evolve_psi.cpp:34–99`；`source/module_hamilt_lcao/module_tddft/propagator.h:19–25` |
| AP-05 | precision single 不是所有求解器的 float/内存减半保证 | `source/module_esolver/esolver.cpp:129–215`；[性能](capabilities/abacus-performance.md) |
| AP-06 | PW +U 的布尔式分派不同于 LCAO 1/2，值2不自动初始化 onsite_radius | `source/module_io/read_input_item_exx_dftu.cpp:342`；[高级](capabilities/abacus-advanced-functionals.md) |
| AP-07 | LR I/O helper 不检查流状态，Debug 断言也可在文件缺失/截断/写失败时通过 | `source/module_lr/utils/lr_util_print.h:15–55`；[高级](capabilities/abacus-advanced-functionals.md) |
| AP-08 | spectrum 只给 rank0 读激发能却不广播，多 rank velocity 谱会除零 | `source/module_lr/esolver_lrtd_lcao.cpp:437,521–565`；`source/module_lr/lr_spectrum_velocity.cpp:69–107` |

电子温度的数值示例、公式与版本限定见[有限电子温度](finite-temperature.md)；实际执行的检查及边界见[验证记录](../test-results.md)。本索引不是所有组合已运行成功的声明。
