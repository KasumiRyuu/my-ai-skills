---
name: nature-style-plotting
description: >-
  Create, revise, and audit reproducible Matplotlib scientific figures with a
  clean Nature-style visual system and Nature-compatible publication
  constraints. Use for line, scatter, error-bar, bar, distribution, heatmap,
  multipanel, inset, logarithmic, band-structure, phonon-dispersion, and other
  data figures when users ask for Nature style, Nature风格, 期刊风格,
  投稿级绘图, 论文配图美化, 多面板排版, or a Nature figure compliance check.
  Distinguish a Nature-inspired appearance from strict final-submission
  requirements, and never imply that a figure is accepted or compliant without
  checking the current instructions for the exact target journal.
---

# Nature-Style Plotting

## 核心目标

生成数据诚实、信息紧凑、可复现且适合最终物理尺寸阅读的科研图。把“Nature 风格”理解为
克制的视觉系统，不要把外观相似直接称为 Nature 官方合规。

保留通用数据绘图流程中的稳定路径、无界面渲染、耐久脚本、多格式输出和结果验证；在严格
投稿模式下，再用目标期刊的现行规则覆盖字体、单位写法、尺寸和交付格式。

## 判定工作模式

- 使用 `nature-inspired` 处理普通论文、报告、中文图或仅要求“Nature 风格”的任务。默认
  保留用户语言；中文优先使用 PingFang SC。
- 使用 `nature-submission` 处理明确面向 Nature 旗舰刊最终投稿、正式 artwork、编辑要求或
  合规审查的任务。核对目标期刊当前官方说明，英文图优先使用 Arial 或 Helvetica。
- 用户未说明目标期刊时，默认使用 `nature-inspired`，记录该假设，不声称正式合规。
- 用户只要求审查时，只检查并报告问题；用户要求生成、修改或重画时，再编辑并运行脚本。

## 按需读取参考资料

- 写或改 Matplotlib 脚本前，读取
  [references/matplotlib-recipes.md](references/matplotlib-recipes.md)。
- 涉及正式投稿、尺寸、字体、线宽、交付格式或合规结论时，读取
  [references/nature-specifications.md](references/nature-specifications.md)，并核对目标期刊的
  当前官方页面。
- 只加载与当前图型和投稿阶段有关的章节，不要把全部参考资料复制进生成的脚本。

## 工作流程

1. **定位输入。** 用 `rg --files` 查找数据、现有脚本、目标图和预期输出目录。读取现有的
   数据定义、单位、统计方法和绘图入口，避免仅凭截图重建可获得的逻辑。
2. **确定语义。** 明确每个视觉编码代表的变量、组别、误差定义、归一化、参考零点和坐标
   变换。统计量使用完整数据计算；降采样只服务于显示。
3. **先定最终尺寸。** 按论文中的最终毫米尺寸创建 Figure，再选择字号、线宽、标记和面板
   布局。不要在 Word、LaTeX 或排版软件中二次拉伸成图。
4. **选择图型。** 根据比较任务选择线、点、区间、分布或二维场。减少不必要的颜色、标题、
   图例、网格和装饰；不要为了“像期刊”而隐藏原始数据或不确定度。
5. **保存实现。** 创建或修改耐久的 Python 脚本，使用 `pathlib.Path`、Matplotlib `Agg`
   后端和脚本相对路径。在导入 Matplotlib 前设置可写的项目内 `MPLCONFIGDIR`。
6. **应用样式。** 使用白底、黑色文字、细轴框、明确刻度、紧凑留白和无边框图例。普通
   直角坐标图默认关闭网格并使用四边向内主次刻度；特殊坐标系按可读性调整并说明原因。
7. **处理布局。** 单面板只调用一次 `tight_layout`；复杂多面板优先使用
   `layout="constrained"`。不要混用两套自动布局，也不要依赖未经复核的
   `bbox_inches="tight"` 改变最终物理尺寸。
8. **导出产物。** 至少保存论文用矢量文件和高分辨率预览图。正式 Nature 主图优先交付
   可编辑 PDF，并按当前官方规则选择其他格式；不要把 PNG 预览误当作主图投稿文件。
9. **验证结果。** 运行保存的脚本，确认文件存在且非空，在最终尺寸下目视检查，并核对
   字体、裁切、重叠、面板顺序、共享尺度、色条、图例和可访问性。

## 默认视觉基线

- 使用 89 mm 单栏或 183 mm 双栏；只有内容确实需要时才使用 120--136 mm 中间宽度。
- 在严格模式中使用 5--7 pt 普通文字、8 pt 粗体正体小写面板标签，以及最终尺寸下
  0.25--1 pt 的线和描边。
- 将普通图的项目默认值设为 6.5 pt 轴标签、5.5--6.5 pt 刻度与图例、0.35 pt 轴框、
  0.75 pt 主线和 3 pt 左右标记，再根据信息密度微调。
- 优先使用色觉友好色板，并同时用线型、标记或填充状态提供第二种区分方式。不要只依赖
  红绿差异，不要使用 `jet` 或无科学意义的彩虹色表。
- 仅在零点、相界、高对称点或拟合基准具有科学意义时添加参考线；保持其视觉层级低于数据。
- 将面板内标题视为可选项。图注能说明的信息不要重复塞进狭小面板。

## 与通用绘图规则的优先级

- 继续使用 `~/software/bin/python` 运行校园内外网服务器上的脚本；本地不存在时报告替代
  解释器。
- 继续把脚本和图保存在项目耐久目录，不把 `/tmp` 作为唯一产物位置。
- 继续使用 PingFang SC 处理中文工作图；严格英文投稿图改用目标期刊要求的标准字体。
- 继续为能带、声子谱等路径图拆分不连续段并标记高对称点。
- 让目标期刊当前规则优先于通用的 PNG DPI、字体和格式偏好，并明确任何冲突或替代。

## 质量门槛

- 不得修改、平滑、截断或筛选数据而不在代码和报告中说明。
- 不得用柱形图替代需要展示分布的样本数据；样本量允许时叠加原始点或区间。
- 不得让不同面板用不可比较的色标或坐标范围来暗示差异。
- 不得出现文字重叠、标签裁切、单位缺失、图例遮挡数据或小于最终可读尺寸的文字。
- 不得将位图放大伪装为更高分辨率；大量散点可在矢量容器中局部栅格化，但文字和线稿保持
  矢量与可编辑。
- 不得仅凭脚本参数宣布“符合 Nature”。正式合规结论必须包含目标期刊、核对日期和仍需
  人工确认的项目。

## 完成时报告

报告保存的脚本、所有输出图、运行命令、最终毫米尺寸、实际字体、工作模式，以及字体回退、
缺失数据、未完成的人工检查或目标期刊规则差异。
