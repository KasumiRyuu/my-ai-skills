# Nature 风格 Matplotlib 配方

本文件把当前项目的 `plot_template.py`、6.5 pt 独立图库、公式与对数坐标专项，以及
`data-analysis-plotting` 的稳定做法压缩成可迁移配方。按图型读取相关章节，不要机械复制
全部代码。

## 目录

- [脚本骨架](#脚本骨架)
- [字体与 rcParams](#字体与-rcparams)
- [尺寸与布局](#尺寸与布局)
- [坐标轴与面板标签](#坐标轴与面板标签)
- [颜色与编码](#颜色与编码)
- [常见图型](#常见图型)
- [能带、声子谱与对数轴](#能带声子谱与对数轴)
- [大数据与 HDF5](#大数据与-hdf5)
- [导出与验证](#导出与验证)

## 脚本骨架

将缓存目录、后端和稳定路径放在最前面：

```python
from __future__ import annotations

from pathlib import Path
import os

SCRIPT_DIR = Path(__file__).resolve().parent
MPL_CACHE_DIR = SCRIPT_DIR / ".matplotlib_cache"
MPL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np

OUT_DIR = SCRIPT_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
```

遵循以下结构：

```text
parse arguments
-> resolve stable paths
-> load and validate data
-> compute statistics from full data
-> prepare display data
-> build figure at final physical size
-> export
-> verify outputs
-> close figure
```

优先使用 `Axes` 对象接口，不在长脚本中依赖状态式 `plt.plot(...)`。为演示数据固定随机种子，
但不要把演示数据和用户真实数据混在同一个不可辨认的入口中。

## 字体与 rcParams

### 字体选择

- 严格英文投稿：依次查找 Arial、Helvetica；缺失时报告实际回退字体，不要静默声称合规。
- 中文 Nature-inspired：从 `~/.local/share/fonts/PingFangSC` 注册 PingFang SC，再依次回退
  到 Source Han Sans CN、Noto Sans CJK SC、DejaVu Sans。
- 多面板整篇使用同一字体族。避免某些面板由 MathText、LaTeX 或后处理软件偷偷换字体。
- 不要默认启用 `text.usetex=True`；它可能引入字体替换、Type 3 字体或不可编辑文本。

项目默认参数：

```python
plt.rcParams.update({
    "font.family": selected_font,
    "font.size": 6.5,
    "font.weight": 400,
    "axes.labelsize": 6.5,
    "axes.labelweight": 400,
    "axes.titlesize": 6.5,
    "xtick.labelsize": 5.5,
    "ytick.labelsize": 5.5,
    "legend.fontsize": 5.5,
    "text.color": "0.08",
    "axes.unicode_minus": False,
    "axes.grid": False,
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "axes.edgecolor": "0.25",
    "axes.labelcolor": "0.08",
    "axes.linewidth": 0.35,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
    "xtick.major.width": 0.35,
    "ytick.major.width": 0.35,
    "xtick.minor.width": 0.25,
    "ytick.minor.width": 0.25,
    "xtick.major.size": 2.2,
    "ytick.major.size": 2.2,
    "xtick.minor.size": 1.2,
    "ytick.minor.size": 1.2,
    "axes.labelpad": 2.0,
    "xtick.major.pad": 2.0,
    "ytick.major.pad": 2.0,
    "legend.frameon": False,
    "lines.linewidth": 0.75,
    "lines.markersize": 3.0,
    "patch.linewidth": 0.35,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "savefig.facecolor": "white",
    "savefig.edgecolor": "none",
})
```

中文公式图需要显式配置 MathText 变体时，可延续当前项目的 PingFang SC 自定义设置；严格
英文投稿则优先让数学符号和正文标准无衬线字体协调，并实际检查导出的 PDF 字体。不要仅凭
`rcParams` 推断最终嵌入结果。

## 尺寸与布局

使用毫米定义最终尺寸：

```python
MM_PER_INCH = 25.4

def mm_to_inches(value_mm: float) -> float:
    if value_mm <= 0:
        raise ValueError("Figure dimensions must be positive.")
    return value_mm / MM_PER_INCH

fig, ax = plt.subplots(
    figsize=(mm_to_inches(89.0), mm_to_inches(62.0))
)
```

选择规则：

- 简单单面板：通常使用 76--89 mm 宽，按数据纵横比确定高度。
- 信息较多的单面板或横向柱形图：可使用 120--136 mm。
- 真正需要多列信息的多面板：使用 183 mm 或略小于双栏宽度的固定尺寸。
- 不要直接把简单单面板拉到 183 mm；这会让 5--7 pt 文字相对画布显得过小。
- 单面板执行一次 `fig.tight_layout(pad=0.55, rect=...)`。
- 多面板、共享色条或复杂 inset 使用 `layout="constrained"`，并微调 `w_pad`、`h_pad`、
  `wspace`、`hspace`。
- 不要同时使用 constrained layout 和 `tight_layout`。
- 避免在 `savefig` 时使用 `bbox_inches="tight"` 改变批量图的物理尺寸；确需使用时重新
  测量输出边界。

## 坐标轴与面板标签

普通直角坐标轴使用统一函数：

```python
def style_axis(ax: plt.Axes, panel_label: str = "") -> None:
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("0.25")
        spine.set_linewidth(0.35)

    ax.grid(False)
    ax.minorticks_on()
    ax.tick_params(
        axis="both", which="major", direction="in", top=True, right=True,
        length=2.2, width=0.35, pad=2.0, labelsize=5.5, colors="0.10",
    )
    ax.tick_params(
        axis="both", which="minor", direction="in", top=True, right=True,
        length=1.2, width=0.25, colors="0.10",
    )

    if panel_label:
        ax.text(
            -0.075, 1.025, panel_label,
            transform=ax.transAxes,
            fontsize=8.0, fontweight=600, fontstyle="normal",
            ha="right", va="bottom", color="black", clip_on=False,
        )
```

使用原则：

- 严格模式用 `Energy (eV)`；Nature-inspired 中文图可按项目传统用 `能量 / eV`。
- 对共享 x 或 y 的多面板只在外侧保留轴标签，避免重复信息。
- 在同一物理量的比较面板中共享范围、刻度和色标。
- 用固定的科学含义决定范围；不要用裁切放大差异而不说明。
- 仅在能提高解释力时显示次刻度。分类轴、热图单元边界和极坐标不必机械调用
  `minorticks_on()`。
- 面板标签放在一致位置并按阅读顺序排列。标签在 Axes 外时设置 `clip_on=False`，并检查
  自动布局是否留出空间。

## 颜色与编码

默认离散色板使用官方示例色：

```python
NATURE_ACCESSIBLE = {
    "black": "#000000",
    "orange": "#E69F00",
    "sky_blue": "#56B4E9",
    "bluish_green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "reddish_purple": "#CC79A7",
    "gray": "#7F7F7F",
}
```

两组数据优先用 blue + vermillion，并叠加 circle + square 或 solid + dashed。基准、拟合或
参考数据使用灰色细虚线。不要给轴标签染成曲线颜色；图例、直接黑字标注或 keyline 更稳妥。

连续色表优先 `viridis`、`cividis`、`magma`。发散数据仅在存在有意义的中心值时使用发散
色表，并用 `TwoSlopeNorm(vcenter=...)` 固定中心。不同面板共享同一量时共享 norm 和色条。

## 常见图型

### 线图

- 主线从 0.75 pt 起，参考线从 0.5 pt 起；最终线宽必须保持在目标期刊范围内。
- 多条曲线密集时减少 marker，只在稀疏位置使用 `markevery`。
- 零点有物理意义时用 `ax.axhline(0, color="0.72", lw=0.3)`，保持低层级。
- 不连接路径重置、缺失区间、不同实验批次或不连续能带段。

### 散点与拟合

- 89 mm 图中可从 `s=9`、`alpha=0.65--0.8`、白色 0.25 pt 边线起步。
- 拟合线约 0.65--0.75 pt；一比一参考线用灰色细虚线。
- 对边界 marker 检查裁切；必要时只对已确认的边界点使用 `clip_on=False`。
- 大量散点在 PDF/SVG 中设 `rasterized=True`，文字、轴和拟合线继续保持矢量。

### 误差棒与区间

- 使用约 0.7 pt 主线、0.5 pt 误差线、1.5--2 pt cap 和 3 pt marker 作为起点。
- 明确误差是 SD、SE、置信区间还是其他量；图注和数据处理代码必须一致。
- 连续趋势的密集不确定度优先用 `fill_between`，并保持透明度适中、边界清楚。

### 柱形图

- 仅用于基线有意义的聚合量，并从零基线开始，除非科学理由明确且已说明。
- 分组宽度可从 0.34--0.36 起步；使用实色、误差线和简洁无边框图例。
- 不使用 3D、渐变、阴影或装饰纹理。
- 少量样本的组间比较优先点图、箱线图或小提琴图加原始点，而不是只画均值柱。

### 分布图

- 箱线图使用约 0.45 pt 箱体与须线、0.75 pt 中位线，并说明 whisker 定义。
- 样本量允许时叠加固定随机种子的 jitter 原始点，使用低透明度和无边线。
- 比较多个直方分布时优先 `histtype="step"`，长尾计数按需要使用 log y。

### 热图与二维场

- 规则等间距矩阵用 `imshow`；物理网格或非等间距坐标用 `pcolormesh`。
- 关闭插值或明确选择插值方式，避免制造不存在的空间结构。
- 色条使用与轴一致的 5.5--6.5 pt 文字和 0.35 pt 外框。
- 不要在每个单元格都写数字，除非矩阵很小且文字仍满足最终字号。

### 多面板与 inset

- 按 `a, b, c, ...` 排列，优先共享轴、图例和色条。
- 根据内容决定 GridSpec 比例，不强迫所有面板同宽同高。
- 将公共图例放在不遮挡数据的位置，避免每个面板重复相同图例。
- 只在 inset 提供不同尺度、局部放大或补充物理关系时使用 inset；不要复制主图信息。
- inset 中的文字仍不得低于严格模式 5 pt。

## 能带、声子谱与对数轴

### 能带与声子谱

- 按路径重置或数据块切分曲线，禁止跨段错误连线。
- 用灰色 0.4--0.6 pt 虚线标高对称点，并设置对应 x tick label。
- 能带以统一费米能为零点；声子谱保留水平零线以显示虚频。
- 参考数据先画成灰色细虚线，拟合或插值结果再用主色绘制。
- 自旋通道比较时共享 y 轴，并用颜色之外的面板标签、线型或标题区分。

```python
for xpos in hsp_x:
    ax.axvline(xpos, color="0.65", lw=0.5, ls="--", zorder=0)
ax.set_xticks(hsp_x, hsp_labels)
ax.axhline(0.0, color="0.45", lw=0.4, zorder=0)
ax.grid(False)
```

### 对数轴

- 直接使用 `ax.set_xscale("log")`、`ax.set_yscale("log")` 或 `symlog`，不要先对数据取 log
  再用线性轴却不标明。
- 纯对数轴不传入零或负值；跨零数据使用 `symlog` 并报告 `linthresh`。
- 主刻度只标整十次幂时使用 `LogLocator(base=10, subs=(1.0,))` 和
  `LogFormatterMathtext(labelOnlyBase=True)`；保留无标签次刻度。
- 需要在对数轴显示普通数字时显式使用 `FixedLocator` 和 formatter，不依赖版本相关的自动
  选择。
- 插图与主图使用不同尺度时，明确标注两者的坐标类型和单位。

## 大数据与 HDF5

- 将分析数组和显示数组分开。拟合、积分、RMSE、P95、误差与统计检验使用完整有效数据。
- 长曲线优先按区间保留局部最小值和最大值，避免固定步长抽样丢失窄峰。
- 对超大 NPY 使用 `mmap_mode="r"`；文本只读必要列；重复使用的大文本转为 NPY/NPZ。
- 读取 HDF5 时先检查 group、dataset、shape、dtype 和轴语义，再在 dataset 上切片；不要先
  加载完整高维矩阵后才截取能带、q 点或自旋。
- 对大量矢量点使用局部栅格化，并检查 PDF/SVG 文件大小和渲染时间。
- 固定图例位置，避免 `loc="best"` 为大数据扫描布局。

## 导出与验证

同一个 Figure 生成所有格式，避免 PDF、SVG 和 PNG 来自不同代码路径：

```python
def save_outputs(fig, output_dir: Path, stem: str, png_dpi: int = 600) -> list[Path]:
    if png_dpi < 220:
        raise ValueError("PNG dpi must be at least 220 for project previews.")
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = [
        output_dir / f"{stem}.pdf",
        output_dir / f"{stem}.svg",
        output_dir / f"{stem}.png",
    ]
    fig.savefig(outputs[0])
    fig.savefig(outputs[1])
    fig.savefig(outputs[2], dpi=png_dpi)
    for path in outputs:
        if not path.is_file() or path.stat().st_size == 0:
            raise OSError(f"Missing or empty output: {path}")
    return outputs
```

严格 Nature 主图将 PDF 作为投稿候选，SVG 和 PNG 作为编辑或预览产物；Extended Data 则按
目标页面另行导出。关闭 Figure：

```python
try:
    outputs = save_outputs(fig, OUT_DIR, "figure_1")
finally:
    plt.close(fig)
```

完成前执行以下检查：

1. 运行耐久脚本并记录实际 Python 命令和字体回退。
2. 确认所有输出存在且非空，尺寸与预期毫米值一致。
3. 将 PDF 渲染为位图，在最终排版宽度下检查文字、线宽、标记、重叠和裁切。
4. 检查面板顺序、共享坐标、色条范围、图例含义和误差定义。
5. 用灰度或色觉缺陷模拟检查关键信息是否仍可区分。
6. 在可用时运行 `pdffonts figure.pdf`，确认没有意外 Type 3 字体或未嵌入字体。
7. 对重要图比较 PDF 与 PNG，确认透明度、局部栅格化、MathText 和图像层一致。
8. 正式投稿前重新读取目标期刊当前说明，不把本地默认参数当作永久规则。
