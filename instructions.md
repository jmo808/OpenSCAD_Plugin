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

## Environment Variables
- `OPENSCAD_BINARY_PATH`: Path to the OpenSCAD command-line executable. Defaults to `/home/jules/.local/bin/openscad`.
- `OPENSCAD_DEFAULT_TOLERANCE`: Default design tolerance (for clearances/fits). Defaults to `0.05`.
