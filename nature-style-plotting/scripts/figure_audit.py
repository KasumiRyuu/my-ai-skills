#!/usr/bin/env python3
"""Mechanically audit PDF, SVG, and raster scientific figure files.

The checks are intentionally conservative.  Passing does not establish journal
compliance or visual quality; inspect the figure at final physical size.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

PT_PER_INCH = 72.0
MM_PER_INCH = 25.4


def _round(value: float | None, digits: int = 3) -> float | None:
    return None if value is None else round(float(value), digits)


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lo = math.floor(position)
    hi = math.ceil(position)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - position) + ordered[hi] * (position - lo)


def inspect_pdf(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    try:
        import fitz
    except ImportError as exc:
        return {"path": str(path), "kind": "pdf", "errors": [f"PyMuPDF unavailable: {exc}"], "warnings": []}

    result: dict[str, Any] = {"path": str(path), "kind": "pdf", "errors": [], "warnings": [], "pages": []}
    try:
        doc = fitz.open(path)
    except Exception as exc:
        result["errors"].append(f"Cannot open PDF: {exc}")
        return result

    all_fonts: set[str] = set()
    type3_fonts: set[str] = set()
    all_sizes: list[float] = []
    all_widths: list[float] = []
    raster_dpis: list[float] = []

    if doc.page_count != 1:
        result["warnings"].append(f"PDF has {doc.page_count} pages; a standalone figure is usually one page.")

    for page_index in range(doc.page_count):
        page = doc.load_page(page_index)
        rect = page.rect
        width_mm = rect.width / PT_PER_INCH * MM_PER_INCH
        height_mm = rect.height / PT_PER_INCH * MM_PER_INCH
        page_fonts: set[str] = set()
        sizes: list[float] = []
        try:
            text = page.get_text("dict")
            for block in text.get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if str(span.get("text", "")).strip():
                            size = float(span.get("size", 0.0))
                            if size > 0:
                                sizes.append(size)
                                all_sizes.append(size)
                            font = str(span.get("font", "")).strip()
                            if font:
                                page_fonts.add(font)
                                all_fonts.add(font)
        except Exception as exc:
            result["warnings"].append(f"Page {page_index + 1}: text inspection failed: {exc}")

        widths: list[float] = []
        try:
            for drawing in page.get_drawings():
                value = drawing.get("width")
                if isinstance(value, (int, float)) and value > 0:
                    widths.append(float(value))
                    all_widths.append(float(value))
        except Exception as exc:
            result["warnings"].append(f"Page {page_index + 1}: vector-line inspection failed: {exc}")

        image_info = []
        try:
            for item in page.get_image_info(xrefs=True):
                bbox = item.get("bbox")
                width_px = item.get("width")
                height_px = item.get("height")
                if bbox and width_px and height_px:
                    display_w_pt = max(float(bbox[2]) - float(bbox[0]), 1e-9)
                    display_h_pt = max(float(bbox[3]) - float(bbox[1]), 1e-9)
                    dpi_x = float(width_px) / (display_w_pt / PT_PER_INCH)
                    dpi_y = float(height_px) / (display_h_pt / PT_PER_INCH)
                    dpi = min(dpi_x, dpi_y)
                    raster_dpis.append(dpi)
                    image_info.append({"pixels": [width_px, height_px], "effective_dpi": _round(dpi, 1)})
        except Exception as exc:
            result["warnings"].append(f"Page {page_index + 1}: raster inspection failed: {exc}")

        try:
            for font in doc.get_page_fonts(page_index, full=True):
                subtype = str(font[2]) if len(font) > 2 else ""
                base_name = str(font[3]) if len(font) > 3 else ""
                if "type3" in subtype.lower():
                    type3_fonts.add(base_name or subtype)
        except Exception as exc:
            result["warnings"].append(f"Page {page_index + 1}: embedded-font inspection failed: {exc}")

        result["pages"].append(
            {
                "number": page_index + 1,
                "size_mm": [_round(width_mm, 2), _round(height_mm, 2)],
                "font_size_min_pt": _round(min(sizes) if sizes else None),
                "font_size_p10_pt": _round(_percentile(sizes, 0.10)),
                "fonts": sorted(page_fonts),
                "vector_width_min_pt": _round(min(widths) if widths else None),
                "vector_width_p10_pt": _round(_percentile(widths, 0.10)),
                "raster_images": image_info,
            }
        )

    doc.close()
    result["fonts"] = sorted(all_fonts)
    result["type3_fonts"] = sorted(type3_fonts)
    result["font_size_min_pt"] = _round(min(all_sizes) if all_sizes else None)
    result["font_size_p10_pt"] = _round(_percentile(all_sizes, 0.10))
    result["vector_width_min_pt"] = _round(min(all_widths) if all_widths else None)
    result["vector_width_p10_pt"] = _round(_percentile(all_widths, 0.10))
    result["raster_dpi_min"] = _round(min(raster_dpis) if raster_dpis else None, 1)

    if all_sizes and min(all_sizes) < args.min_font_pt:
        result["warnings"].append(
            f"Detected text as small as {min(all_sizes):.2f} pt (< {args.min_font_pt:g} pt). "
            "Confirm that it is meaningful figure text rather than metadata."
        )
    if all_widths and min(all_widths) < args.min_line_pt:
        result["warnings"].append(
            f"Detected vector stroke as thin as {min(all_widths):.3f} pt (< {args.min_line_pt:g} pt)."
        )
    if raster_dpis and min(raster_dpis) < args.min_raster_dpi:
        result["warnings"].append(
            f"At least one embedded raster is about {min(raster_dpis):.0f} dpi at placed size "
            f"(< {args.min_raster_dpi:g} dpi)."
        )
    if type3_fonts:
        result["warnings"].append("Type 3 font(s) detected: " + ", ".join(sorted(type3_fonts)))
    if args.max_width_mm is not None:
        for page in result["pages"]:
            if page["size_mm"][0] > args.max_width_mm + 0.1:
                result["warnings"].append(
                    f"Page {page['number']} width {page['size_mm'][0]:.2f} mm exceeds {args.max_width_mm:g} mm."
                )
    return result


def inspect_raster(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    try:
        from PIL import Image
    except ImportError as exc:
        return {"path": str(path), "kind": "raster", "errors": [f"Pillow unavailable: {exc}"], "warnings": []}

    result: dict[str, Any] = {"path": str(path), "kind": "raster", "errors": [], "warnings": []}
    try:
        with Image.open(path) as image:
            width, height = image.size
            dpi = image.info.get("dpi")
            result.update({"pixels": [width, height], "mode": image.mode, "dpi_metadata": dpi})
            if dpi and dpi[0] and dpi[1]:
                result["size_mm"] = [
                    _round(width / float(dpi[0]) * MM_PER_INCH, 2),
                    _round(height / float(dpi[1]) * MM_PER_INCH, 2),
                ]
                if min(float(dpi[0]), float(dpi[1])) < args.min_raster_dpi:
                    result["warnings"].append(
                        f"DPI metadata {dpi} is below {args.min_raster_dpi:g} dpi."
                    )
            else:
                result["warnings"].append("No reliable DPI metadata; physical size cannot be verified.")
    except Exception as exc:
        result["errors"].append(f"Cannot inspect raster: {exc}")
    return result


def inspect_svg(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    import xml.etree.ElementTree as ET

    result: dict[str, Any] = {"path": str(path), "kind": "svg", "errors": [], "warnings": []}
    try:
        root = ET.parse(path).getroot()
        result["width"] = root.attrib.get("width")
        result["height"] = root.attrib.get("height")
        result["viewBox"] = root.attrib.get("viewBox")
        text_nodes = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "text"]
        result["editable_text_elements"] = len(text_nodes)
        if not text_nodes:
            result["warnings"].append(
                "No SVG <text> elements detected; text may have been converted to paths."
            )
    except Exception as exc:
        result["errors"].append(f"Cannot inspect SVG: {exc}")
    return result


def inspect(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if not path.is_file():
        return {"path": str(path), "kind": "unknown", "errors": ["File not found"], "warnings": []}
    if path.stat().st_size == 0:
        return {"path": str(path), "kind": "unknown", "errors": ["File is empty"], "warnings": []}
    if suffix == ".pdf":
        return inspect_pdf(path, args)
    if suffix == ".svg":
        return inspect_svg(path, args)
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        return inspect_raster(path, args)
    return {"path": str(path), "kind": "unknown", "errors": [f"Unsupported extension: {suffix}"], "warnings": []}


def print_human(result: dict[str, Any]) -> None:
    print(f"\n{result['path']} [{result['kind']}]")
    for key in ("pages", "pixels", "size_mm", "font_size_min_pt", "font_size_p10_pt", "vector_width_min_pt", "vector_width_p10_pt", "raster_dpi_min", "fonts", "type3_fonts", "editable_text_elements"):
        if key in result:
            value = result[key]
            if key == "pages" and isinstance(value, list):
                print(f"  page_count: {len(value)}")
                for page in value:
                    print(
                        "  page {number}: size={size_mm} mm, font_min={font_size_min_pt} pt, "
                        "line_min={vector_width_min_pt} pt, raster_images={count}".format(
                            count=len(page.get("raster_images", [])), **page
                        )
                    )
            else:
                print(f"  {key}: {value}")
    for error in result.get("errors", []):
        print(f"  ERROR: {error}")
    for warning in result.get("warnings", []):
        print(f"  WARNING: {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--min-font-pt", type=float, default=5.0)
    parser.add_argument("--min-line-pt", type=float, default=0.25)
    parser.add_argument("--min-raster-dpi", type=float, default=300.0)
    parser.add_argument("--max-width-mm", type=float)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--fail-on-warning", action="store_true")
    args = parser.parse_args()

    results = [inspect(path, args) for path in args.paths]
    if args.as_json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for result in results:
            print_human(result)

    has_errors = any(result.get("errors") for result in results)
    has_warnings = any(result.get("warnings") for result in results)
    if has_errors:
        return 2
    if args.fail_on_warning and has_warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
