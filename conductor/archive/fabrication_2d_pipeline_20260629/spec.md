# Specification: 2D Fabrication Pipeline

## Overview
This track implements three new MCP tools that automate the transition from a 3D OpenSCAD assembly model to production-ready 2D fabrication outputs. These tools address the most critical workflow bottlenecks identified during real-world usage designing a multi-panel woodworking cyberdeck enclosure.

## Problem Statement
When using the current OpenSCAD MCP Plugin to design assemblies with multiple flat panels (side walls, top/bottom panels, angled bezels), the user must:
1. **Manually rotate** each vertical or angled panel to lie flat on the XY plane before calling `projection()` to get a 2D template.
2. **Hand-code** dimension annotation routines using OpenSCAD's 2D primitives (`square`, `text`), carefully positioning them outside cutouts and adjusting font sizes dynamically.
3. **Run separate CLI commands** for each camera angle when verifying the 3D assembly, then mentally composite the views.

## Proposed Tools

### 1. `export_2d_templates`
**Purpose:** Extract individual panels from a 3D OpenSCAD assembly and export them as flat 2D DXF/SVG vector files, automatically handling rotation of vertical/angled panels to the XY plane.

**Inputs:**
- `scad_path` (str): Path to the source `.scad` file.
- `part_name` (str, optional): Name of a specific part/module to export. If omitted, exports all parts defined in the file's part selector.
- `output_dir` (str): Directory where DXF/SVG files will be written.
- `format` (str, default `"both"`): Output format — `"dxf"`, `"svg"`, or `"both"`.

**Outputs:**
- Human-readable summary listing each exported panel with dimensions.
- JSON array of `{ part_name, format, file_path, width_mm, height_mm }` objects.

**Technical Approach:**
- Parse the SCAD file for `part` selector branches (e.g., `if (part == "side_panel")`).
- For each part, invoke OpenSCAD CLI with `-D "part=\"<name>\""` and `-o <output>.<ext>`.
- Return structured results with file paths and bounding dimensions extracted from the generated files.

### 2. `add_dimensions`
**Purpose:** Inject external blueprint-style dimension annotations onto 2D panel projections, positioned outside the panel outline to avoid cutout interference.

**Inputs:**
- `scad_path` (str): Path to the source `.scad` file.
- `part_name` (str): Name of the part to dimension.
- `output_path` (str): Path where the dimensioned DXF/SVG will be written.
- `units` (str, default `"mm"`): Dimension units — `"mm"` or `"inches"`.
- `offset` (float, default `12.0`): Distance in mm from the panel edge to place dimension lines.

**Outputs:**
- The dimensioned DXF/SVG file with external tick marks, extension lines, and text labels.
- Human-readable summary with the panel dimensions.

**Technical Approach:**
- Generate temporary OpenSCAD code that wraps the panel projection in a `union()` with calls to `draw_dim_x()` and `draw_dim_y()` helper modules.
- The helpers are dynamically generated with font sizes scaled to `max(3.5, min(6.0, span * 0.04))`.
- Dimension lines are placed at negative X/Y coordinates (outside the panel outline) with witness/extension lines bridging to the panel corners.

### 3. `generate_multiview`
**Purpose:** Render a single combined quadrant image containing front, side, top, and isometric orthographic views in one MCP call.

**Inputs:**
- `scad_path` (str): Path to the source `.scad` file.
- `output_path` (str): Path where the combined PNG will be written.
- `img_size` (int, default `1024`): Total resolution of the combined image (each quadrant is `img_size/2` pixels).
- `colorscheme` (str, default `"Sunset"`): Color palette.
- `views` (list, optional): Override the default quadrant layout. Default: `["front", "right", "top", "isometric"]`.

**Outputs:**
- A single combined PNG image with labeled quadrants.
- Inline base64 image in the MCP response payload.
- Human-readable summary listing the views rendered.

**Technical Approach:**
- Render each view individually using the existing `compile_and_preview` camera presets.
- Use Pillow (PIL) to composite the four images into a 2x2 grid with thin separator lines and view labels.
- Return the composite as a single inline image.

## Acceptance Criteria
1. All three tools are registered via `@mcp.tool()` and appear in the MCP schema.
2. `export_2d_templates` correctly exports vertical panels (like back_panel) as full-face 2D projections, not thin strips.
3. `add_dimensions` places dimension annotations entirely outside the panel outline, with no overlap with cutouts.
4. `generate_multiview` returns a single composite image with all four views correctly laid out.
5. All tools return structured JSON alongside human-readable summaries.
6. All tools include absolute file paths in their responses.
7. Unit test coverage exceeds 80% for all new code.
