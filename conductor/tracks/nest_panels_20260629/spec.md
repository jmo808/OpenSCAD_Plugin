# Specification: Panel Nesting & Sheet Layout Optimization Tool (`nest_panels`)

## Overview
This track implements a new MCP tool (`nest_panels`) that performs 2D bin-packing of flattened panel projections onto standard stock sheet sizes to minimize material waste. It takes the panel dimensions from an OpenSCAD assembly (via the existing part selector pattern) and produces an optimized cutting layout with kerf allowance, part labels, and material utilization reporting.

## Problem Statement
After extracting 2D panel templates from a 3D assembly, the user must manually arrange them onto stock sheet material for cutting. This involves:
- Estimating how many sheets are needed
- Manually positioning panels to minimize waste
- Accounting for saw blade kerf between cuts
- Labeling each panel on the sheet for identification during assembly

This is a classic 2D bin-packing problem that can be automated to save time and reduce material waste.

## Functional Requirements

### FR-1: Panel Dimension Extraction
- The tool MUST accept a SCAD file path and extract panel dimensions using the existing part selector pattern (`if (part == "...")`).
- The tool MUST use OpenSCAD CLI to export each part as a 2D projection and determine its bounding box width and height.
- The tool MUST support an optional `parts` parameter to nest only a subset of panels.

### FR-2: Stock Sheet Configuration
- The tool MUST support the following preset sheet size:
  - `"half_sheet"`: 609.6mm × 1219.2mm (24" × 48")
- The tool MUST support custom sheet dimensions via `sheet_width` and `sheet_height` parameters (in mm).
- The tool MUST default to `"half_sheet"` if no sheet size is specified.

### FR-3: Kerf Allowance
- The tool MUST support a configurable `kerf` parameter (default: 3.175mm / ⅛").
- The kerf value MUST be added as spacing between all nested panels (both horizontal and vertical gaps).
- The kerf MUST also be applied as a margin from the sheet edges.

### FR-4: Packing Algorithms
The tool MUST support two packing strategies via a `strategy` parameter:

1. **`"simple"` (Shelf Algorithm)**:
   - Place panels left-to-right on horizontal shelves.
   - Start a new shelf when the current shelf is full.
   - Deterministic, fast, easy to verify.

2. **`"optimized"` (First-Fit Decreasing)**:
   - Sort panels by area (largest first).
   - For each panel, try to place it in the first position where it fits.
   - Try both orientations (original and 90° rotated) and pick the best fit.
   - Better material utilization.

Default strategy: `"optimized"`.

### FR-5: Panel Rotation
- The packing algorithm MUST allow 90° rotation of panels to find better fits.
- Rotation is always enabled.

### FR-6: Multi-Sheet Support
- If all panels do not fit on a single sheet, the tool MUST automatically allocate additional sheets.
- Each sheet MUST be independently laid out and exported.

### FR-7: Output — Visual Layout
- The tool MUST generate a visual layout image (PNG) for each sheet showing:
  - Sheet outline (with dimensions labeled)
  - Nested panel rectangles with part names rendered as text labels inside each rectangle
  - Kerf gaps visualized as thin lines between panels
- The layout image MUST be returned inline (base64) in the MCP response.
- The layout image MUST also be saved to disk.

### FR-8: Output — Structured JSON
The tool MUST return a structured JSON response containing:
```json
{
  "sheets": [
    {
      "sheet_number": 1,
      "sheet_width_mm": 609.6,
      "sheet_height_mm": 1219.2,
      "panels": [
        {
          "part_name": "side_panel",
          "x": 3.175,
          "y": 3.175,
          "width": 150.0,
          "height": 200.0,
          "rotated": false
        }
      ],
      "utilization_percent": 72.3,
      "waste_area_mm2": 205432.1,
      "layout_image_path": "/abs/path/to/sheet_1_layout.png"
    }
  ],
  "summary": {
    "total_sheets": 1,
    "total_panels": 8,
    "average_utilization_percent": 72.3,
    "strategy": "optimized"
  }
}
```

### FR-9: Human-Readable Summary
- The tool MUST return a conversational summary.
- Example: "Nested 8 panels onto 1 half-sheet (24×48") with 72.3% material utilization using the optimized packing strategy. Kerf allowance: 3.175mm (⅛"). Layout saved to /path/to/sheet_1_layout.png."
- The summary MUST include absolute file paths for all generated files.

## Non-Functional Requirements

### NFR-1: Pure Python Implementation
- The packing algorithms MUST be implemented in pure Python (standard library only). No external bin-packing libraries.

### NFR-2: MCP Pattern Compliance
- The tool MUST follow the existing `@mcp.tool()` FastMCP decorator pattern.
- The tool MUST return structured results (text + images + JSON).

### NFR-3: Performance
- For assemblies with up to 20 panels, nesting should complete within 10 seconds.

## Tool Interface

```python
@mcp.tool()
def nest_panels(
    scad_path: str,
    output_dir: str = None,
    sheet_preset: str = "half_sheet",
    sheet_width: float = None,
    sheet_height: float = None,
    kerf: float = 3.175,
    strategy: str = "optimized",
    parts: list = None
) -> list:
```

## Acceptance Criteria
1. Tool is registered via `@mcp.tool()` and appears in the MCP schema.
2. Correctly nests panels from a test SCAD file onto a sheet without overlap.
3. Kerf gaps are correctly applied between all panels and sheet edges.
4. Both `"simple"` and `"optimized"` strategies produce valid layouts.
5. Panels are rotated 90° when it improves packing.
6. Multi-sheet allocation works when panels exceed one sheet.
7. Layout PNG has labeled panel rectangles and sheet dimensions.
8. Material utilization percentage is accurate.
9. Structured JSON matches the schema above.
10. Unit test coverage exceeds 80% for all new code.

## Out of Scope
- Irregular (non-rectangular) panel nesting.
- Nested cutout optimization (nesting small parts inside larger part cutouts).
- Wood grain direction constraints.
- Cost estimation based on sheet material prices.
- DXF/SVG export of the nesting layout (only PNG for now).
