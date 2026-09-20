# Nature 图件技术规范

本文件记录 2026-08-01 核对的 Nature 旗舰刊与 Nature Research Figure Guide 要点。它是
执行基线，不替代目标期刊、稿件阶段或编辑发来的最新说明。Nature Portfolio 各刊可能采用
不同尺寸、格式和命名规则；出现冲突时，以编辑直接要求和目标期刊当前页面为准。

## 目录

- [适用范围与优先级](#适用范围与优先级)
- [主图基线](#主图基线)
- [文字、单位与线条](#文字单位与线条)
- [颜色与可访问性](#颜色与可访问性)
- [文件与可编辑性](#文件与可编辑性)
- [Extended Data](#extended-data)
- [本项目默认值如何映射](#本项目默认值如何映射)
- [核对清单](#核对清单)
- [官方来源](#官方来源)

## 适用范围与优先级

按以下顺序解释要求：

1. 编辑针对当前稿件发来的直接要求。
2. 目标 Nature Portfolio 期刊当前的 author/artwork instructions。
3. Nature Research Figure Guide 的主图或 Extended Data 页面。
4. 本 skill 的 Nature-inspired 视觉基线。

把两类任务分开：

| 模式 | 目标 | 是否可称官方合规 |
|---|---|---|
| `nature-inspired` | 获得克制、紧凑、清晰的 Nature 风格科研图 | 否 |
| `nature-submission` | 满足明确目标期刊和投稿阶段的技术要求 | 仅在逐项核对后 |

## 主图基线

- 使用 89 mm 单栏宽或 183 mm 双栏宽。
- 内容确有需要时使用 120--136 mm 的一栏半宽度；不要把它当作每本期刊都固定提供的版式。
- 将 Nature Research Figure Guide 给出的最大图高 170 mm 作为稳妥上限，以保留图注空间。
- 按预计最终印刷尺寸创建图，不要先画大图再由 Word、LaTeX 或 Illustrator 任意缩放。
- 以最小且仍清晰的版式组织面板，减少空白，面板尽量按 `a, b, c, ...` 阅读顺序排列。
- 根据内容分配不等宽或不等高面板；不要为了矩形整齐而让低信息面板占据过多空间。

## 文字、单位与线条

- 严格英文投稿图使用一致的无衬线标准字体，优先 Arial 或 Helvetica。
- 将面板标签设为 8 pt、粗体、正体、小写字母。
- 将其他文字保持在 5--7 pt，所有尺寸均指最终排版尺寸。
- 将线条和描边保持在 0.25--1 pt；小于 0.25 pt 的线可能在印刷中消失。
- 保留坐标轴线和刻度，并为坐标轴标明物理量和单位。
- 严格模式采用 Nature Figure Guide 示例的 `Quantity (unit)`，例如 `Time (s)`、
  `Energy (eV)`。`时间 / s` 或 `Energy / eV` 可继续用于 Nature-inspired 或其他期刊风格，
  但不要默认把它称为 Nature house style。
- 避免在繁忙图像或阴影上直接放置文字。必须叠加时使用高对比黑字或白字，并复核可读性。
- 不要使用彩色正文标签。用黑色文字配合图例、keyline、线型或标记表达组别。
- 不要把文字转成轮廓；保证文字仍可编辑，并嵌入 TrueType 2 或 42 字体。
- 使用 Matplotlib 时设置 `pdf.fonttype = 42`，并用 `pdffonts` 或矢量编辑器检查结果。

中文标签不是 Nature 旗舰刊英文主图的常规交付场景。中文工作图可使用 PingFang SC，但如要
提交含非英文文字的正式图，必须先确认编辑要求和字体可编辑性。

## 颜色与可访问性

Nature Research Figure Guide 给出的色觉友好示例色板为：

| 名称 | Hex | 建议用途 |
|---|---|---|
| Black | `#000000` | 正文、轴线、主要高对比线 |
| Orange | `#E69F00` | 离散组别 |
| Sky blue | `#56B4E9` | 离散组别或浅色辅助 |
| Bluish green | `#009E73` | 离散组别，避免单独与红色配对 |
| Yellow | `#F0E442` | 填充或深色背景；白底细线需谨慎 |
| Blue | `#0072B2` | 默认主系列 |
| Vermillion | `#D55E00` | 与蓝色配对的次系列 |
| Reddish purple | `#CC79A7` | 第三或第四系列 |

实施规则：

- 优先使用蓝色与朱红色区分两组，并同时改变 marker 或 linestyle。
- 避免把红色与绿色作为唯一差别；避免彩虹色表。
- 连续数据使用感知均匀的 `viridis`、`cividis` 或 `magma`。
- 正负偏差使用有明确物理中点的发散色表，并固定 `vmin`、`vcenter`、`vmax`。
- 在白底上检查黄色、浅蓝和半透明区域的对比度；必要时增加深色边线。
- 用黑白或灰度预览检查信息是否仍能通过位置、形状、线型或明度辨认。
- 让文字与背景达到高对比。官方指南将 4.5:1 作为文字对比参考。

## 文件与可编辑性

主图优先交付含可编辑图层的矢量文件：

- 首选 `.ai`、`.eps` 或 `.pdf`。
- 当前 Research Figure Guide 还列出 plain `.svg`、`.ps`、Excel 和由 PowerPoint 先导出的
  PDF 等可接受格式。
- 保持文字、比例尺、箭头、线条和框为矢量与可编辑对象；不要把整张主图扁平化为位图。
- 将字体和所有组成部分嵌入文件，不要只保留外部链接。
- 尽量把主图文件控制在 50 MB 以内。
- 对照片或显微图使用真实采集分辨率。当前 Figure Guide 要求图像至少 450 dpi；某些目标
  页面仍写 300--600 dpi，因此必须核对稿件对应页面，不得通过插值制造分辨率。
- 将 RGB 作为工作色彩空间，除非目标期刊或编辑明确要求其他色彩空间。

Matplotlib 建议：

```python
plt.rcParams.update({
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
})
```

`svg.fonttype="none"` 保留文字，但接收方仍需拥有对应字体；正式 PDF 必须另外检查字体是否
嵌入、是否出现 Type 3，以及文字是否仍能编辑。

PNG 适合本地预览、幻灯片和视觉检查，但当前 Research Figure Guide 不把 PNG 列为 Nature
主图交付格式。不要只生成 PNG，也不要把高 DPI PNG 等同于可编辑矢量图。

## Extended Data

Extended Data 与印刷主图采用不同交付约束。当前官方页面给出的基线包括：

- 最大页面尺寸 180 mm 宽、170 mm 高，并为图注预留空间。
- 普通文字 5--7 pt，线条 0.25--1 pt，面板紧凑对齐。
- 使用 RGB，单个文件不超过 10 MB。
- 按当前页面导出单独的 JPEG、TIFF 或 EPS；页面对 JPEG/TIFF 的偏好与主图不同。
- 当前 Building and Exporting 页面要求 Extended Data 位图最高 300 dpi。
- 遵循目标期刊的文件名规则；Nature 旗舰刊示例为
  `CorrespondingAuthorSurname_EDfig1.jpg`。

不要把主图的矢量交付规则机械套到 Extended Data，也不要把 Extended Data 的 JPEG 规则
反向套到主图。

## 本项目默认值如何映射

当前项目已有基线与 Nature 官方要求的关系如下：

| 项目现有设置 | 处理方式 |
|---|---|
| 89 / 136 / 183 mm | 保留；严格模式优先 89 或 183 mm |
| 普通文字 6.5 pt | 保留，位于官方 5--7 pt 范围内 |
| 刻度与图例 5.5 pt | 保留，但在最终尺寸下目视检查 |
| 面板标签 8 pt 粗体正体 | 保留 |
| 轴框 0.35 pt、次刻度 0.25 pt | 保留，位于官方 0.25--1 pt 范围内 |
| 四边向内主次刻度、无网格 | 作为本 skill 的默认视觉系统保留 |
| PingFang SC | 中文 Nature-inspired 图保留；严格英文投稿改用 Arial/Helvetica |
| `物理量 / unit` | Nature-inspired 可保留；严格模式改为 `Quantity (unit)` |
| 项目蓝 `#3161AF` 与红 `#CF3946` | 可作延续色；严格可访问性优先官方示例色板 |
| PDF + SVG + 600 dpi PNG | 保留为工作产物；正式交付按主图或 Extended Data 规则筛选 |

## 核对清单

正式声称完成合规审查前逐项确认：

- 已记录目标期刊、图件类型、投稿阶段和核对日期。
- 最终宽高以毫米设定，插入稿件后没有二次缩放。
- 所有普通文字为 5--7 pt，面板标签为 8 pt 粗体正体。
- 所有线和描边为 0.25--1 pt。
- 坐标轴有物理量与单位，文本无重叠、裁切或低对比。
- 颜色可访问，关键信息不只依赖颜色。
- 主图的文字和线稿保持矢量、可编辑，字体正确嵌入。
- 位图分辨率来自原始数据，不是人工放大。
- 文件格式、大小、色彩空间和命名符合当前目标页面。
- 已在最终物理尺寸下目视检查 PDF 和栅格预览。

## 官方来源

核对日期：2026-08-01。

- Nature Research Figure Guide, Building and exporting figure panels:
  <https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/>
- Nature Research Figure Guide, Preparing figures - our specifications:
  <https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/>
- Nature, Final submission:
  <https://www.nature.com/nature/for-authors/final-submission>
- Nature Research Figure Guide, Extended data formatting guidelines:
  <https://research-figure-guide.nature.com/figures/extended-data-formatting-guidelines/>

每次正式投稿前重新打开这些页面。网页之间可能因图件类型或更新节奏存在差异，不要只依赖
本地摘录。
