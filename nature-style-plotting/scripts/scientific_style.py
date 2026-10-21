#!/usr/bin/env python3
"""Reusable Matplotlib helpers for publication-grade scientific figures.

Import this module before creating figures.  It provides conservative starting
values, not journal compliance.  Inspect every result at its final physical size.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable, Literal, Sequence

MM_PER_INCH = 25.4

# Okabe-Ito-derived accessible palette plus neutral reference colors.
COLORS = {
    "black": "#000000",
    "dark_gray": "#4D4D4D",
    "gray": "#8A8A8A",
    "light_gray": "#C8C8C8",
    "orange": "#E69F00",
    "sky_blue": "#56B4E9",
    "bluish_green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "reddish_purple": "#CC79A7",
}

SERIES_COLORS = (
    COLORS["blue"],
    COLORS["vermillion"],
    COLORS["bluish_green"],
    COLORS["orange"],
    COLORS["reddish_purple"],
    COLORS["sky_blue"],
    COLORS["gray"],
)

FrameStyle = Literal["open", "boxed"]
Profile = Literal["general", "physics", "earth"]


def mm_to_inches(value_mm: float) -> float:
    """Convert a positive millimetre value to inches."""
    if value_mm <= 0:
        raise ValueError("Figure dimensions must be positive.")
    return value_mm / MM_PER_INCH


def size_mm(width_mm: float, height_mm: float) -> tuple[float, float]:
    """Return a Matplotlib ``figsize`` tuple from millimetres."""
    return mm_to_inches(width_mm), mm_to_inches(height_mm)


def configure_cache(root: Path | str) -> Path:
    """Set a writable, project-local Matplotlib cache directory.

    Call before importing ``matplotlib.pyplot`` in restricted environments.
    """
    cache = Path(root).resolve() / ".matplotlib_cache"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache))
    return cache


def _resolve_font(candidates: Sequence[str]) -> tuple[str, bool]:
    from matplotlib import font_manager

    installed = {entry.name for entry in font_manager.fontManager.ttflist}
    for candidate in candidates:
        if candidate in installed:
            return candidate, True
    return "DejaVu Sans", False


def apply_style(
    profile: Profile = "general",
    *,
    language: Literal["en", "zh"] = "en",
    font_candidates: Sequence[str] | None = None,
) -> dict[str, object]:
    """Apply a compact, accessible Matplotlib baseline.

    ``profile`` changes axis conventions, not the scientific content:
    ``physics`` favors a boxed frame with inward ticks; ``earth`` and
    ``general`` favor an open frame with outward ticks.  Call ``style_axis`` on
    each axis after plotting to apply the chosen frame.
    """
    import matplotlib as mpl

    if font_candidates is None:
        if language == "zh":
            font_candidates = (
                "PingFang SC",
                "Source Han Sans CN",
                "Noto Sans CJK SC",
                "Microsoft YaHei",
                "Arial Unicode MS",
            )
        else:
            font_candidates = ("Arial", "Helvetica", "Liberation Sans")
    font_name, exact_match = _resolve_font(font_candidates)
    direction = "in" if profile == "physics" else "out"

    mpl.rcParams.update(
        {
            "font.family": font_name,
            "font.size": 7.0,
            "axes.labelsize": 7.0,
            "axes.titlesize": 7.0,
            "xtick.labelsize": 6.2,
            "ytick.labelsize": 6.2,
            "legend.fontsize": 6.2,
            "figure.titlesize": 8.0,
            "text.color": "0.08",
            "axes.labelcolor": "0.08",
            "axes.edgecolor": "0.22",
            "axes.linewidth": 0.45,
            "axes.grid": False,
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.edgecolor": "none",
            "axes.prop_cycle": mpl.cycler(color=SERIES_COLORS),
            "lines.linewidth": 0.8,
            "lines.markersize": 3.2,
            "patch.linewidth": 0.45,
            "xtick.direction": direction,
            "ytick.direction": direction,
            "xtick.major.width": 0.45,
            "ytick.major.width": 0.45,
            "xtick.minor.width": 0.3,
            "ytick.minor.width": 0.3,
            "xtick.major.size": 2.6,
            "ytick.major.size": 2.6,
            "xtick.minor.size": 1.4,
            "ytick.minor.size": 1.4,
            "xtick.major.pad": 2.0,
            "ytick.major.pad": 2.0,
            "axes.labelpad": 2.5,
            "legend.frameon": False,
            "legend.handlelength": 1.8,
            "legend.handletextpad": 0.5,
            "legend.columnspacing": 1.0,
            "axes.unicode_minus": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    return {
        "profile": profile,
        "font": font_name,
        "requested_fonts_found": exact_match,
        "recommended_frame": "boxed" if profile == "physics" else "open",
    }


def style_axis(
    ax,
    *,
    frame: FrameStyle = "open",
    minor: bool = True,
    grid: bool = False,
) -> None:
    """Apply an open or boxed scientific axis without changing data limits."""
    boxed = frame == "boxed"
    ax.spines["left"].set_visible(True)
    ax.spines["bottom"].set_visible(True)
    ax.spines["top"].set_visible(boxed)
    ax.spines["right"].set_visible(boxed)
    for spine in ax.spines.values():
        spine.set_linewidth(0.45)
        spine.set_color("0.22")

    direction = "in" if boxed else "out"
    ax.tick_params(
        axis="both",
        which="major",
        direction=direction,
        top=boxed,
        right=boxed,
        width=0.45,
        length=2.6,
        pad=2.0,
    )
    if minor:
        ax.minorticks_on()
        ax.tick_params(
            axis="both",
            which="minor",
            direction=direction,
            top=boxed,
            right=boxed,
            width=0.3,
            length=1.4,
        )
    else:
        ax.minorticks_off()
    if grid:
        ax.grid(True, which="major", color="0.90", linewidth=0.35, zorder=0)
    else:
        ax.grid(False)


def panel_label(
    ax,
    label: str,
    *,
    x: float = -0.12,
    y: float = 1.04,
    fontsize: float = 8.5,
) -> None:
    """Place a consistent bold panel label in axes coordinates."""
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=fontsize,
        fontweight="bold",
        fontstyle="normal",
        color="black",
        clip_on=False,
    )


def save_figure(
    fig,
    output_dir: Path | str,
    stem: str,
    *,
    formats: Iterable[str] = ("pdf", "svg", "png"),
    png_dpi: int = 600,
    transparent: bool = False,
) -> list[Path]:
    """Save all formats from one figure and verify non-empty outputs."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for raw_format in formats:
        fmt = raw_format.lower().lstrip(".")
        if fmt not in {"pdf", "svg", "png", "tif", "tiff", "eps"}:
            raise ValueError(f"Unsupported output format: {raw_format}")
        path = out_dir / f"{stem}.{fmt}"
        kwargs = {"transparent": transparent}
        if fmt in {"png", "tif", "tiff"}:
            kwargs["dpi"] = png_dpi
        fig.savefig(path, **kwargs)
        if not path.is_file() or path.stat().st_size == 0:
            raise OSError(f"Missing or empty output: {path}")
        outputs.append(path)
    return outputs


def _demo(output_dir: Path) -> list[Path]:
    configure_cache(output_dir)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    apply_style("general")
    x = np.linspace(0.0, 8.0, 80)
    y = 1.0 - np.exp(-x / 2.2)
    err = 0.04 + 0.01 * np.cos(x)
    fig, ax = plt.subplots(figsize=size_mm(89.0, 58.0), layout="constrained")
    ax.fill_between(x, y - err, y + err, color=COLORS["sky_blue"], alpha=0.28, linewidth=0)
    ax.plot(x, y, color=COLORS["blue"], label="Model")
    ax.scatter(x[::8], y[::8], s=11, facecolor="white", edgecolor=COLORS["blue"], linewidth=0.55, label="Samples")
    ax.axhline(1.0, color=COLORS["gray"], linestyle="--", linewidth=0.55, label="Reference")
    ax.set(xlabel="Pressure (GPa)", ylabel="Normalized response")
    style_axis(ax, frame="open", minor=True)
    panel_label(ax, "a")
    ax.legend(ncols=3, loc="lower right")
    try:
        return save_figure(fig, output_dir, "scientific-style-demo", formats=("pdf", "svg", "png"))
    finally:
        plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", type=Path, metavar="OUTPUT_DIR", help="write a small PDF/PNG smoke-test figure")
    args = parser.parse_args()
    if args.demo:
        for path in _demo(args.demo):
            print(path)
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
