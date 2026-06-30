# OpenSCAD MCP Server Instructions

This MCP server provides advanced 3D modeling, rendering, and export capabilities powered by OpenSCAD.

## Available Tools

### 1. `generate_scad`
Writes or modifies an OpenSCAD `.scad` source code file, allowing parameter injection.
- **When to use:** Use this tool to write the initial geometry of a model or update variables/parameters (e.g. clearance tolerances, length, width).
- **Parameters:**
  - `scad_code` (string): The complete OpenSCAD source code body.
  - `output_path` (string): Local path where the `.scad` file should be written.
  - `parameters` (object, optional): Dictionary of key-value design parameters to inject at the top of the file.

### 2. `compile_and_preview`
Compiles an OpenSCAD model and renders orthogonal or perspective views to preview PNGs. The rendered images are returned directly in the response payload.
- **When to use:** Use this tool to visually inspect the geometry, verify alignments and clearances, or perform visual checks inside the model loop before exporting to STL.
- **Parameters:**
  - `scad_path` (string): Path to the source `.scad` file.
  - `output_dir` (string, optional): Directory where preview PNG files will be written. Defaults to `/tmp/openscad_previews`.
  - `img_size` (number, default 512): Resolution of the square PNG previews.
  - `projection` (string, default "ortho"): Camera projection type ('ortho' or 'perspective').
  - `colorscheme` (string, default "Sunset"): Color scheme (e.g., 'Cornfield', 'Sunset', 'Metallic', 'DeepOcean').
  - `views` (array of strings, default `["isometric", "top", "front"]`): View angles to render.

### 3. `export_stl`
Compiles the final OpenSCAD geometry and exports it into a 3D-printable STL file.
- **When to use:** Use this tool to finalize a verified, manifold model for 3D printing or downstream CAD usage.
- **Parameters:**
  - `scad_path` (string): Path to the source `.scad` file.
  - `output_path` (string): Path where the output `.stl` file should be saved.

### 4. `export_2d_templates`
Selects targeted panels using a top-level `part` variable, rotates them flat to the Z=0 plane using projection, and exports them directly into production-ready DXF and SVG formats.
- **When to use:** Use this tool to generate 2D patterns for laser cutting, CNC routing, or manual woodworking/machining layout templates.
- **Parameters:**
  - `scad_path` (string): Path to the source `.scad` file.
  - `output_dir` (string): Output directory where vector files will be saved.
  - `part_name` (string, optional): Specific part to export. Defaults to 'all', exporting all parts discovered in the model.
  - `format` (string, default "both"): Vector export format ('dxf', 'svg', or 'both').

### 5. `add_dimensions`
Injects blueprint-style dimension lines, tick marks, extension lines, and scaling text labels into a 2D panel template, automatically offset in negative coordinates.
- **When to use:** Use this tool to generate human-readable engineering templates and diagrams for workshop fabrication, with auto-scaling annotations.
- **Parameters:**
  - `scad_path` (string): Path to the source `.scad` file.
  - `part_name` (string): Name of the part to annotate.
  - `output_path` (string): Destination path for the dimensioned file (DXF or SVG).
  - `units` (string, default "mm"): Dimensions units ('mm' or 'inches').
  - `offset` (number, default 12.0): Distance in mm from the panel boundary to place the dimension lines.

### 6. `generate_multiview`
Renders a single combined quadrant image containing front, side, top, and isometric views in one MCP call.
- **When to use:** Use this tool to instantly generate a unified engineering multiview drawing of a 3D model for presentation or design verification.
- **Parameters:**
  - `scad_path` (string): Path to the source `.scad` file.
  - `output_path` (string): Path where the combined PNG will be saved.
  - `img_size` (number, default 1024): Resolution of the combined image.
  - `colorscheme` (string, default "Sunset"): Rendering color scheme.
  - `views` (array of strings, optional): Custom list of up to 4 views to render. Defaults to ['front', 'right', 'top', 'isometric'].

### 7. `check_interference`
Detects and reports geometric intersections (collisions) between components in an OpenSCAD assembly model. It performs 3D CSG intersections to compute volume overlap and exports a PNG visual highlight showing collisions in red against a semi-transparent assembly.
- **When to use:** Use this tool to verify assembly clearance and identify mechanical collisions, overlaps, or improper fits between parts before fabrication.
- **Parameters:**
  - `scad_path` (string): Path to the source `.scad` file.
  - `fail_fast` (boolean, default false): If true, halts checking after the first collision is found.
  - `img_size` (number, default 512): Resolution of the visual highlight PNG preview.
  - `colorscheme` (string, default "Sunset"): Rendering color scheme.
  - `output_path` (string, optional): Optional path to save the highlight PNG. Defaults to `<scad_dir>/<scad_basename>_interference.png`.

### 8. `extract_bom`
Parses tagged hardware annotations embedded in OpenSCAD source files and compiles them into a structured, aggregated Bill of Materials (BOM) exported in JSON, Markdown table, and CSV formats.
- **When to use:** Use this tool to extract a shopping list or procurement inventory of off-the-shelf components (e.g. fasteners, bearings, connectors) directly from the SCAD design file.
- **Annotation Formats:**
  - **Inline comment annotations:** `// BOM: Part Name, qty=N, category=Cat[, supplier=Sup, part_number=PN]`
  - **Module-level metadata blocks:**
    ```
    /* BOM:
     *   name: Part Name
     *   qty: N
     *   category: Cat
     *   supplier: Sup
     *   part_number: PN
     */
    ```
- **Parameters:**
  - `scad_path` (string): Path to the OpenSCAD source file to parse.
  - `output_dir` (string, optional): Directory where the output files (`bom.json`, `bom.md`, `bom.csv`) will be saved. Defaults to `~/.openscad_bom/`.
  - `formats` (array of strings, optional): Which formats to export. Defaults to `["json", "md", "csv"]`.

### 9. `nest_panels`
Nests 2D panel templates from an OpenSCAD assembly model onto stock sheets, optimizing material utilization.
- **When to use:** Use this tool to plan sheet layout, determine how many sheets are needed for fabrication, and generate a cutting layout with visual preview and utilization percentage.
- **Parameters:**
  - `scad_path` (string): Path to the source `.scad` file.
  - `sheet_preset` (string, default "2x4"): Preset sheet size: "4x8" (1219.2 x 2438.4 mm) or "2x4" (609.6 x 1219.2 mm).
  - `sheet_width` (number, optional): Custom sheet width override in mm.
  - `sheet_height` (number, optional): Custom sheet height override in mm.
  - `kerf` (number, default 3.175): Cut width/spacing between panels in mm.
  - `parts` (array of strings, optional): Specific parts to nest. If omitted, nests all discovered parts.
  - `strategy` (string, default "optimized"): Packing algorithm: "simple" (shelf packing) or "optimized" (First-Fit Decreasing with 90° rotation).
  - `output_dir` (string, optional): Directory where the PNG layout previews will be saved. Defaults to `<scad_dir>/nesting_previews/`.
### 10. `split_for_printing`
Splits a large 3D part into segments fitting the specified printer bed, applying interlocking joining mechanisms (dovetail, flange, tongue-and-groove, or alignment pins) on the split interface.
- **When to use:** Use this tool when a part exceeds the build volume of a 3D printer bed and needs to be partitioned into print-safe interlocking segments.
- **Parameters:**
  - `scad_path` (string): Path to the source `.scad` file.
  - `part_name` (string, optional): Specific module name to split.
  - `bed_width` (number, default 220.0): Printer bed limit in X (mm).
  - `bed_depth` (number, default 220.0): Printer bed limit in Y (mm).
  - `bed_height` (number, default 250.0): Printer build height in Z (mm).
  - `safety_margin` (number, default 10.0): Margin subtracted from bed limits (mm).
  - `split_axis` (string, default "auto"): Axis to split on ("x", "y", "z", or "auto").
  - `joint_type` (string, default "auto"): Joining geometry ("dovetail", "flange", "tongue_groove", "pin", or "auto").
  - `manual_coordinate` (number, optional): Coordinate value to split at (requires explicit `split_axis`).
  - `joint_configs` (object, optional): Custom overrides for specific joints.
  - `output_dir` (string, optional): Directory to save split STL segments and exploded SCAD/PNG previews.

## Environment Variables
- `OPENSCAD_BINARY_PATH`: Path to the OpenSCAD command-line executable. Defaults to `/home/jules/.local/bin/openscad`.
- `OPENSCAD_DEFAULT_TOLERANCE`: Default design tolerance (for clearances/fits). Defaults to `0.05`.

