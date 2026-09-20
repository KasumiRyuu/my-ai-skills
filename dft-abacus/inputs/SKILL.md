---
name: inputs
description: 为 ABACUS 3.10.1 创建、检查或修复 INPUT、STRU、KPT，核对参数解析、坐标单位、元素/轨道顺序和外部文件路径。
license: LGPL-3.0
metadata:
  version: 0.2.1
  author: D. Liu
  audited-on: 2026-09-21
  source: ABACUS v3.10.1 source implementation
  source-repository: https://github.com/deepmodeling/abacus-develop
  source-license: LGPL-3.0
  abacus.capability-id: cap.abacus.input-files
---

# 输入文件

先读 [输入格式与解析规则](../references/capabilities/abacus-input-files.md)。本卡针对本地 v3.10.1 源码；不要用旧版“重复参数最后一次生效”或“所有参数行截断为 150 字符”的规则。

1. 从用户提供的结构、已有输入和目录中取得晶格、坐标、赝势、轨道及任务设置；先检查已有文件，只有实际缺少且影响计算的问题才询问。示例文件名不能当成已经安装的数据。
2. 普通 PW 用 [STRU.pw.tpl](../templates/STRU.pw.tpl)，LCAO 用 [STRU.lcao.tpl](../templates/STRU.lcao.tpl)。核对元素顺序、坐标类型、质量、移动标记以及赝势与轨道配套。
3. 确定 k 点来源：显式 [网格](../templates/KPT.mp.tpl)、[单 Γ 点](../templates/KPT.gamma-only.tpl)、正值 `kspacing` 或 LCAO 的 `gamma_only 1`。后两者会重写 `kpoint_file` 指定的文件；能带路径必须关掉自动网格和 gamma 优化。
4. `INPUT_PARAMETERS` 必须存在。未知参数和重复参数都报错；`ntype` 可省略自动统计，显式值必须匹配 STRU。浮点指数写 `e/E`，整数写完整十进制，不写 D 指数、单位后缀或普通标量算式；本版可能只解析数值前缀而不报错。行尾注释之前留空格。
5. 在具备本版可执行程序时运行 `abacus --check-input`；它需要 STRU 并检查参数与种类数，不验证完整结构、KPT、赝势/轨道、SCF 收敛或物理精度。若尚无可执行程序，交付静态检查结果并说明未运行。

输入完整后按用户任务进入 [SCF](../static/SKILL.md)、[优化](../relax/SKILL.md)、[MD](../md/SKILL.md) 或 [电子结构](../electronic/SKILL.md)。数值是否足够由 [accuracy](../accuracy/SKILL.md) 验证。试跑的能量行或正常结束行本身不能证明 SCF 已收敛。
