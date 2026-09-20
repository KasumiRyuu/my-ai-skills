# 运行与核验

在独立任务目录准备 `INPUT`、`STRU`（或 `stru_file`）以及所需 k 点文件和实际数据路径。`pseudo_dir`、`orbital_dir` 与 STRU 中的文件名应共同指向真实文件；占位符不是可执行输入。生成 KPT 的配置可能覆盖磁盘文件，保留原始路径文件。

## 启动

以下是启动形式示意，进程数和线程数应按安装方式、调度资源及求解器确定：

```bash
abacus --version
abacus --check-input
OMP_NUM_THREADS=1 mpirun -n 4 abacus
```

`parse_args.cpp:12` 实现版本参数与 `--check-input`；程序从工作目录读取 INPUT。
MPI 启动参数属于 MPI 实现，不能把某个 OpenMPI 绑定选项作为所有机器的默认修复。使用 MPI 数 × 每进程线程数评估 CPU 资源；求解器另有矩阵分块与并行约束，见[性能卡](capabilities/abacus-performance.md)。

## `--check-input` 的边界

`read_input.cpp:113` 在 `read_txt_input` 完成后退出。它读取参数，应用默认与重置，读取 STRU 统计 `ntype`，执行各参数的检查；因此通常也需 STRU，不能把它当成只检查单独 INPUT 文本的工具。

它不会完成一般运行中的完整结构、KPT、赝势、轨道初始化与 SCF，成功信息不代表完整输入可运行。部分参数检查仍可能检查外部文件；PW 的 `gamma_only` 重置还会写所选 KPT（`read_input_item_elec_stru.cpp:543`）。在复制出的任务目录进行检查。

## 输出与续算

- 常规输出目录为 `OUT.<suffix>/`，日志为 `running_<calculation>.log`，具体产物与开关、基组、任务相关。
- `Driver::reading`（`driver.cpp:108`）先解析，再建输出目录、写参数快照，随后执行 `Input_Conv::Convert`。因此 `OUT.<suffix>/INPUT` 包含已解析/重置参数，后续改变还要读日志；它不是“全为初始默认值”。
- 换输出目录或 `suffix` 后检查 `read_file_dir`。显式给出已收敛阶段的目录，核对密度、结构、自旋、赝势、泛函和网格是否适配。
- 后处理与 MD 续算有不同的状态文件要求，分别读[电子结构](../electronic/SKILL.md)与[MD](../md/SKILL.md)。

交付时说明实际生成的文件、必需的外部数据、物理参数及单位、验证结果。没有真实运行时写明仅进行了静态检查；结束行或总能行不能替代收敛判定。
