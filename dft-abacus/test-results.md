# ABACUS v3.10.1 源码审核与验证记录

日期：2026-09-21。审核产物：本目录 `dft-abacus`，版本 0.2.1。
源码基线：`/mnt/e/Software/ABACUS/soucecode/abacus_v3.10.1`，tag `v3.10.1`，commit `f71921fe848659deac8db319cd4311b55b5ad480`。

审核以 `source/` 内的参数注册、解析、自动重置、合法性检查、求解器分派和实际读写/计算函数为依据，没有以 README 或 examples 的用法作为正确性证明。覆盖全部 8 个技能入口、12 张能力卡、导航/术语/工作流文档和模板，并检查交叉依赖。上游源码未修改。

本文保留核查结论、执行结果和验证边界，相关技术说明及源码索引均位于技能包内。

## 实现限制核查

源码审阅覆盖输入、求解器、续算、后处理、动力学及高级功能的执行路径。具体触发条件和例外见技能说明，不能把某分支缺陷推广到全部 ABACUS 计算。

| 范围 | 核查要点 | 相关说明 |
|---|---|---|
| 输入与精度 | 串行普通 LCAO LAPACK 未回写 psi/可能越界；LCAO 双网格混用；ndz 重置笔误；数值前缀解析 | [输入](references/capabilities/abacus-input-files.md)、[精度](references/capabilities/abacus-accuracy.md)、[求解器](references/capabilities/abacus-performance.md) |
| 续算与输出 | 自旋 PDOS 索引、非 MPI 投影全零、PW WFC 占据格式、mem_saver、部分电荷权重/并行/旋量、实空间模平方、Berry、UNK、bxsf、cube 完整性 | [电子结构](references/capabilities/abacus-electronic.md)、[输出](references/capabilities/abacus-output-reading.md) |
| 磁性与动力学 | 零磁初值覆盖、几何输出丢失逐原子磁矩、FIRE/MSST 冻结分量、NPT/MSST 晶胞约束、每个优化位移步的标签错位 | [磁性](references/capabilities/abacus-magnetism-soc.md)、[MD](references/capabilities/abacus-md.md)、[优化](references/capabilities/abacus-relax.md) |
| 高级功能与分派 | LR 基态文件、spectrum 目录/rank、NDEBUG 消除 LR I/O、流状态未检查、激发能未广播、RT MPI/步长、single 精度工厂、PW +U=2 的 onsite 前提 | [高级功能](references/capabilities/abacus-advanced-functionals.md)、[性能](references/capabilities/abacus-performance.md) |

逐项源码索引见[源码依据](references/source-audit.md)。结论以实际触发条件为限：未确认的 GPU 部分电荷问题不能断言为必然崩溃，“普通 DOS 不受投影 bug 直接影响”也不等于“串行 LCAO 求解可靠”。

### 源码提取与执行验证

| 提取检查 | 实际观测 | 验证边界 |
|---|---|---|
| 原样 DiagoLapack 实/复数函数，链接系统 LAPACK | H 的对角为 1/2/3/4、nbands=2 时，psi 哨兵不变；本征值写出4项，超过逻辑容量2 | 物理缓冲区刻意留6项以安全观察越界范围，不声称运行了材料 SCF 或实际堆破坏 |
| 原样4个 FFT 重置 lambda | 手工32³、dense32×32×64、ecutrho480时 double_grid=0；自动网格同截断为1 | 确认开关重置行为，不是完整 FFT/材料能量测试 |
| 原样 LR 的路径/读写4个 lambda | 未定义 NDEBUG：读2次、写2次；定义 NDEBUG：读0次、写0次 | 外围 I/O 用计数桩，只验证调用是否发生 |
| 数字转换 | std::stod("1d-9")=1；std::stoi("1e2")=1 | 与 LAPACK 探针同次实际执行；参数如何进入转换另由完整 read/reset/check 调用链核对 |
| 原样 LR 数值 I/O helper，保留 assert | 缺失文件、只含2值却请求4值、写入不存在父目录，均报告处理4值；缺失数据未恢复、失败写出无文件 | 验证流状态未检查，不是完整 LR 或 MPI 光谱测试 |

这些检查验证了源码缺陷的局部行为，**不是修复 ABACUS 软件后的通过测试**；本任务修订的是 skill。其他问题的判定基于源码调用链，公式演示没有计为 DFT 或 MPI 实测。

### 电子结构与动力学场景验收

独立审阅者在未读测试预期或审计报告的条件下，按 skill 回答组合任务，并结合源码核对。

| 实际任务 | 原始应答结果 | 核查与处理 |
|---|---|---|
| 非 MPI、Gamma-only、nspin=2 的 DOS/PDOS/PBANDS | 通过 | 正确合并求解器、构建和自旋索引限制，先重建可信 SCF |
| PW 多 k mem_saver/kpar、WFC/空带密度、Berry、后续非共线 LCAO | 通过 | 区分完整波函数、能级数组、权重、自旋与实际并行布局 |
| AFM slab 续算、零初磁、FIRE/NPT/MSST 冻结边界、优化训练标签 | 通过 | 未将几何恢复等同磁态恢复，正确识别冻结分量及标签时序 |
| 独立 LR/spectrum 重启与非 MPI RT 步长 | 部分通过 | Debug 流状态未检查、多 rank velocity 谱未广播激发能的说明已补齐，并执行 helper 探针 |

LR 相关说明已纳入[高级功能](references/capabilities/abacus-advanced-functionals.md)，经**有背景的定向复核**确认完整，触发条件未过度泛化；该复核不计为独立盲测或实际 DFT 验证。

## 主要参数与查证入口

| 领域 | 关键结论 | 完整依据 |
|---|---|---|
| 物理 4000 K | 选 FD，sigma=0.0253345227426361 Ry；本版字面 sigma_temp=4000 实为约 2000 K，占据要等效 4000 K 则 temp 输入约 8000 | [有限温度](references/finite-temperature.md) |
| 宽度覆盖与方法名 | 两个不同 sigma 关键词后出现者覆盖；同名重复报错；mp3/marzari-vanderbilt 等输入别名有实现缺陷 | [有限温度](references/finite-temperature.md) |
| 能量与电子熵 | 常规 KS 的 etot 已含 demet；FD 时为 F。通常不显含温度的 XC 下 U=F−demet，显示的 sigma→0 外推量不是 U；热 XC 另有熵边界 | [输出](references/capabilities/abacus-output-reading.md) |
| INPUT/STRU/KPT | 纠正重复参数、150 字符泛化、ntype 推断、坐标/速度单位、自动 KPT 覆盖与 Line 点数；检查模式不是完整运行验证 | [输入](references/capabilities/abacus-input-files.md) |
| 精度与带数 | ecutrho 比值下限是输入约束；LCAO 的轨道空间与网格要分别收敛；nbands 可等于 NLOCAL，高温须检验占据尾部 | [精度](references/capabilities/abacus-accuracy.md) |
| SCF | scf_thr_type 决定残差定义，不能都标成 Ry；scf_ene_thr 是额外 DeltaE_womix 条件；混合、早停和 U-ramping 按分支解释 | [SCF](references/capabilities/abacus-static.md)、[排障](references/capabilities/abacus-convergence.md) |
| 密度与 NSCF | out_chg=0 仍可写 binary，2 却被解析拒绝；NSCF 强制 file。Gamma-only LCAO binary 的读写标志不一致，需准备兼容密度/cube 回退 | [电子结构](references/capabilities/abacus-electronic.md) |
| 后处理 | 修正 PDOS 分支、DOS 累计列缺步长因子、能带未减费米能、波函数文件格式、get_S 无需预收敛密度、Berry 占据子空间限制 | [电子结构](references/capabilities/abacus-electronic.md) |
| Wannier90 | nnkp 的晶格/k 点/顺序须匹配；接口要求有效 KPAR=1；LCAO 方法 2 的 UNK 输出函数为空 | [电子结构](references/capabilities/abacus-electronic.md) |
| 结构优化 | 两种力阈值同时给时 force_thr 固定优先；新旧算法与约束判据不同；达到上限时末尾结构可能尚无对应能量/力 | [优化](references/capabilities/abacus-relax.md) |
| MD | 电子与离子温度独立；频率用 fs⁻¹；重启是累计步号且目录布局有分支；随机状态不完整保存；FIRE 硬编码停止阈值 | [MD](references/capabilities/abacus-md.md) |
| 磁性 | SOC 强制运行时 symmetry=-1；按赝势/基组检查力和应力，不能统一禁止；显式 nupdown=0 也有约束；sc_mag_switch 被检查阻止 | [磁性](references/capabilities/abacus-magnetism-soc.md) |
| 高级模块 | 受限 PW +U、MPI/投影/轨道依赖、占据矩阵路径；EXX/D3、场/溶剂、OF/SDFT/TDDFT、QO/RDMFT、电导率按实际实现修订 | [高级功能](references/capabilities/abacus-advanced-functionals.md) |
| 输出 STRU | PW +U 的 onsite 轨道要求未完全进入优化/MD 结构写出的 need_orb 判断，续算可能需恢复 NUMERICAL_ORBITAL | [优化](references/capabilities/abacus-relax.md)、[MD](references/capabilities/abacus-md.md) |
| 并行 | 部分 LCAO 求解器实现 kpar；cg_in_lcao 无普通执行分派；非 SDFT 重置 bndpar；GPU/PEXSI 依构建和实际路径判断 | [性能](references/capabilities/abacus-performance.md) |
| 标签和外部接口 | 固定 Te 的力匹配 F，NVE 检查 K+F；应力扣外压时点依输出来源，MD_dump VIRIAL 是 kbar；DeePKS 能量 npy 用 Ry；外部 API 不作未经验证的保证 | [生态](references/capabilities/abacus-ml-ecosystem.md) |

逐项函数入口见[源码索引](references/source-audit.md)。上述是审核覆盖和修订内容，不是这些组合已在真实材料上运行成功的清单。

## 输入解析与全包检查

### 1. 提取真实源码并编译执行关键分支

验证时提取原样的 INPUT 读取/拆词函数、三个 smearing 注册块、out_chg 注册及布尔解析、FD 占据和熵函数，用 g++ 编译执行。仅对日志/错误处理、全局设置和 STRU 计数等外围依赖使用桩实现；没有编译完整 ABACUS。

执行了 27 份 INPUT 场景及 FD 函数值断言，覆盖：4000/8000 转换、直接 Ry 宽度、两种行序、默认值、大小写、同名重复拒绝、合法/非法方法别名、out_chg=0/1/−1/2、参数值长行与过长独占注释。用源码 SI 常数另核算温标。

执行结果：通过；字面 temp=4000 得到 0.01266726 Ry，对应 1999.99978348626 K。输出中未知参数 x 的提示来自预期失败的过长注释用例。

### 2. 参数与续算场景验收

独立审阅者先仅读 skill 回答四个实际任务，再读取源码查证；未读取本包的测试预期或其他审核结果。

| 场景 | 原始应答结果 | 核查与处理 |
|---|---|---|
| 4000 K、两种宽度、电子熵与能量 | 通过 | 保留版本限定和空带/热 XC 边界 |
| Gamma-only LCAO binary 接能带/PDOS | 发现关键遗漏 | 追到 FP 电荷基组 false、writer 头 true、read_rhog 拒绝与 cube 回退；已同步 static/electronic/output、入口、模板和速查 |
| 重复参数、out_chg=2、ecutrho 下限、自检边界 | 通过 | 保留错误发生顺序与检查范围说明 |
| LCAO 残差、cg_in_lcao 和 kpar | 通过 | 区分解析接受、运行分派与实测性能 |

Gamma-only 密度读取的相关说明已同步至入口和模板，具体条件见[电子结构](references/capabilities/abacus-electronic.md)。上述验收发现的遗漏已修订，文档修订不等于实际 NSCF 验证。

### 3. 全包静态检查与一致性核对

静态检查覆盖 8 个 SKILL.md 的前置元数据、Markdown 本地链接、完整 source 引用的路径和全部列出的行号范围、表格列数、7 个 INPUT 模板的参数注册/重复/缺值，以及独占注释不超过保守的 140 UTF-8 字节。

上述静态检查通过，未报告错误。此项不检查所有参数值组合的运行支持，也不等于执行 `abacus --check-input`。参数名共 124 个模板出现项，而非 124 个完整计算。

已核对主入口、任务入口、能力卡、术语/速查/工作流和 INPUT 模板的交叉条件，以及源码路径、行号和手工网格实际截断的表述。结论限于审核范围，不代表全部科学/构建组合已经证明无误。

已核对 NSCF 截断/带数继承、Wannier90 方法2 UNK 空实现、外压应力、PW +U 输出结构和随机 MD 重启等适用边界。静态检查与人工复核不能替代实际计算验证。

[行为用例](test-prompts.json)列出回归场景。**用例定义不表示已完成独立模型应答或真实 DFT 执行**；实际验证见上述记录。

## 验证边界

- 当前 PATH 中没有 abacus/abacus_serial，因此未执行完整 `--check-input`、SCF、优化、MD、DOS/能带或性能基准。局部源码编译成功不能证明完整 ABACUS 可构建。
- 没有替用户选择并运行真实材料的赝势/轨道；模板数值是起点，不保证目标精度，外部数据文件仍需实际提供。
- 没有测试外部 dpdata/ASE/Wannier90 等安装版本的接口，也没有穷举编译开关、设备和高级模块的全部组合。
- 没有旧/新/无技能对照实验，不报告整体质量提升百分比或全组合无误保证。
