<!-- capability_id: cap.abacus.performance | revision: 3 | source-audited: ABACUS v3.10.1 -->

# 并行、求解器与设备

先读取实际编译配置、任务的基组/自旋/泛函、k 点与基函数规模和可用资源，再选启动命令及求解器。性能调整须在同一物理模型、电子温度和精度下比较时间、内存与数值误差；加核、单精度或更少 k 点不能自动视为等价加速。

## 设备与求解器

`device` 初始默认是 **auto**，初始化依据编译支持和可见 GPU 选择设备；要求可复现实验时显式写 `cpu` 或 `gpu` 并检查日志 `RUNNING WITH DEVICE`。没有 GPU 支持时显式 gpu 会退出，auto 可退回 CPU。`lcao_in_pw` 不支持 GPU。

| 基组/条件 | 3.10.1 选择规则 |
|---|---|
| PW | 默认 `cg`；解析器允许 `cg\|dav\|dav_subspace\|bpcg`，实现按设备实例化；具体 PAW/特殊计算限制另核对 |
| LCAO + CPU | 未指定时优先 `genelpa`（编译有 ELPA）；否则 MPI 版 `scalapack_gvx`，串行版 `lapack` |
| LCAO + GPU | 未指定时 `cusolver`；需要 MPI 与 CUDA，`cusolvermp` 还需对应编译支持；ELPA 是否使用 GPU 由其构建/运行路径决定 |
| `genelpa` / `elpa` | 需要 ELPA 构建，不能把 genelpa 写成任何二进制都可用的通用模板值 |
| `lapack` | 普通 LCAO 仅非 MPI 编译进入；本版实现还有下述波函数回写和越界缺陷，不能作为可靠生产路径推荐 |
| `pexsi` | 需要 PEXSI 构建，当前复数/多 k 分支明确退出，使用 LCAO `gamma_only true` 的实数路径 |
| `cg_in_lcao` | 输入枚举保留且提示 testing，不应作为生产推荐；下游普通 LCAO 求解器分派并无对应实现 |

GPU **没有“全局只能 gamma_only=1”限制**：PW 有一般 k 点 GPU 实现，LCAO cuSolver 也实例化了复数矩阵求解。LCAO 网格部分按任务选择 CUDA 或 CPU 分支，不意味着所有模块与组合均已得到同样加速。多卡收益依赖体系、库、显存与通信，须测量，不能先验写成“多卡一定更慢/更快”。

**普通串行 LCAO 的本版缺陷**：默认 `ks_solver lapack` 调用的实数/复数 `DiagoLapack` 将 `nlocal` 个本征值复制到仅有 `nbands` 个元素的行中，`nbands<nlocal` 时越界；活跃的 LAPACK 调用只更新局部 H 副本，没有把本征向量写回 `psi`，后续密度却使用该 `psi`。提取原函数、链接 LAPACK 的最小执行已复现两者。因此增大 nbands 至 nlocal 也不能修好波函数；使用经验证的 MPI 构建与 ELPA/ScaLAPACK 等实现，或修复后经过测试的版本。这里指 `ks_solver lapack`，不扩张为所有名称含 lapack 的算法均有问题。

依据：`source/module_hsolver/diago_lapack.cpp:19–55,58–150,154–250`；`source/module_elecstate/elecstate.cpp:245–257`；`source/module_hsolver/hsolver_lcao.cpp:60–91,160–168`。非 MPI 的 PDOS/PBANDS 另有输出限制，见[电子结构卡](abacus-electronic.md)。

`precision single` 也不是通用内存减半开关：普通 PW-KS 与 LCAO_IN_PW 的工厂有 float 实例；普通 LCAO 与 SDFT 仍实例化 double（SDFT 的 float 分派被注释掉）。CPU single 还会在转换阶段检查 `__ENABLE_FLOAT_FFTW`。核对实际求解器类型、构建和误差，不只看 INPUT 是否接受 single。依据：`source/module_esolver/esolver.cpp:129–215`；`source/module_io/input_conv.cpp:195–204`。

## 并行维度与实际约束

- MPI × OpenMP 使用调度器分配的核数，避免超订。`OMP_NUM_THREADS=1 mpirun -n 4 abacus` 只是四核资源可用时的起点。超订会警告并可能变慢，不能把 pending、挂起或 SIGKILL 的原因直接归为线程数；分别检查调度器状态、启动日志与资源记录。
- **LCAO 要求 `nbands <= nlocal`，允许相等**。不存在对所有求解器都成立的 `MPI进程数 < nbands < nlocal` 规则；分块矩阵、进程网格及每池工作量才决定可用并行度。不能为满足旧 FAQ 的不等式随意增加物理能带。
- PW `kpar` 把进程分为 k 点池。3.10.1 的 DAV 与 DAV-subspace 接收 `POOL_WORLD` 通信器，不能把旧文档“Davidson 不可与 kpar 同用”当成通用硬禁令。使用代表任务测试目标组合，并保证每池基组足够容纳 Davidson 子空间。
- **LCAO 也实现了 `kpar>1` 的对角化并行**，仅 `genelpa|elpa|scalapack_gvx` 进入 `parakSolve`；其他普通求解器组合退出。网格等其他部分仍使用 `KPAR=1`。解析器存在“LCAO 尚不支持”的过时 WARNING，执行分派才是判断依据。
- PW GPU 有效 `KPAR=NPROC/bndpar`；普通 KS 中 `bndpar` 自动重置为 1，故通常是每 MPI rank 一个 k 池。不要宣称用户输入的 kpar 总原样生效。GPU 绑定按节点内 rank 对可见设备数取模，应设计每卡进程数并检查绑定。
- Wannier90、PW Berry phase、PW `bands_to_print` 等后处理需要实际 KPAR=1，不能把普通 PW 对角化的 k 并行能力直接推广给这些输出。PW 多 k NSCF 的 `mem_saver 1` 只留下本池最后一个 k 的波函数；需要完整 WFC 的导出/后处理用 `mem_saver 0`。纯能级/总 DOS 的本征值另外存储，区别及源码见[电子结构卡](abacus-electronic.md)。
- `bndpar` 仅 SDFT 保留；必须整除进程数，联合分组还检查 `NPROC` 对 `kpar*bndpar` 的可分性。给普通 KS 写 bndpar 不会产生带并行。
- 对 CPU kpar，选正数且不大于可用进程数；不超过有效 k 点数通常更有用，整除是便于均衡的选择，不能把所有 CPU k 池都限定为等大小。
- LCAO `bx/by/bz` 是网格分组参数，默认 0 自动选；解析器拒绝 >10，PW/lcao_in_pw 自动设为 1。调整时核对最终 FFT 网格和能量/力精度；保留自动设置通常更合适，不能为负载均衡随意旋转含场/SOC/方向约束的物理体系。

## 验证与 PEXSI

先记录一个能正常运行的基线，逐次改变 MPI/OMP/设备或求解器，比较总能/自由能、力、应力在目标容差内的差异及 wall time、峰值内存。`device`、`ks_solver`、有效 kpar 等应从输出反查；不能只保存 INPUT。

PEXSI 通过密度矩阵计算电子密度，普通求解分支不生成对角化本征对，不能直接承诺与 `out_band`/波函数后处理等价。其 `pexsi_temp` 是 PEXSI 自身温度参数，不应将常规 smearing 的能量/熵解析规则未经核查直接套用。任务需要热力学能量或能带时，先核实对应后端的输出定义。

`KILLED BY SIGNAL 9` 可能由 OOM、作业时限或外部信号造成；以调度器/系统记录判别。减少进程数对复制数据内存可能有帮助，对分布式矩阵每进程内存则可能相反；按内存来源调整。

## 源码定位

- `source/module_parameter/input_parameter.h:69,139`；`source/module_base/module_device/device.cpp:129-219`：auto 设备选择、GPU 限制与绑定、有效 kpar。
- `source/module_io/read_input_item_elec_stru.cpp:12-162,753-795`：求解器默认/编译约束、网格参数。
- `source/module_hsolver/hsolver_lcao.cpp:48-114,127-169,175-275`：LCAO kpar、实际 solver 分派与 PEXSI；`source/module_hsolver/diago_pexsi.cpp:64-96`：复数路径拒绝。
- `source/module_hsolver/diago_cusolver.cpp:201-203`、`source/module_hamilt_lcao/module_gint/gint.cpp:40-81`：复数 GPU 求解与网格设备分支。
- `source/module_elecstate/cal_nelec_nband.cpp:148-153`：nbands 允许等于 nlocal。
- `source/module_hsolver/hsolver_pw.cpp:423-430,586-597,651-661`、`source/module_hsolver/diago_dav_subspace.cpp:16-34`：DAV 池通信器及子空间尺寸。
- `source/module_io/input_conv.cpp:179-194`、`source/module_io/read_input_item_system.cpp:232-264`；`source/module_base/parallel_global.cpp:109-174,318-362`：LCAO kpar 与 bndpar 重置、资源警告、分组。

相关：[静态 SCF](abacus-static.md)、[精度](abacus-accuracy.md)、[MD](abacus-md.md)。
