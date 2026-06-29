---
name: openscad-mcp
description: Design, preview, and export 3D printable mechanical and functional parts in OpenSCAD.
---
Please use the openscad-mcp MCP server tools to design, render, and export 3D models in OpenSCAD based on the user's request.

Available tools:
- `generate_scad(scad_code: str, output_path: str, parameters: dict = None)`: Writes or modifies OpenSCAD code, supporting parameter injections at the top.
- `compile_and_preview(scad_path: str, output_dir: str = None, img_size: int = 512, projection: str = "ortho", colorscheme: str = "Sunset", views: list = None)`: Compiles the SCAD file and returns images from multiple perspective cameras (e.g. isometric, top, front) directly back into the context window for visual verification.
- `export_stl(scad_path: str, output_path: str)`: Exports the verified 3D manifold geometry to a standard STL file ready for 3D printing.
- `export_2d_templates(scad_path: str, output_dir: str, part_name: str = "all", format: str = "both")`: Flattens and projects 3D panels down to Z=0 and exports them directly to production-ready DXF and SVG formats.
- `add_dimensions(scad_path: str, part_name: str, output_path: str, units: str = "mm", offset: float = 12.0)`: Injects dimension lines, tick marks, and scaling text annotations onto a 2D panel template, automatically placed outside the part outline in negative coordinate space.
- `generate_multiview(scad_path: str, output_path: str, img_size: int = 1024, colorscheme: str = "Sunset", views: list = None)`: Generates a single combined quadrant preview image containing front, side, top, and isometric views in one MCP call.
- `check_interference(scad_path: str, fail_fast: bool = False, img_size: int = 512, colorscheme: str = "Sunset", output_path: str = None)`: Detects geometric collisions between parts, returning overlap volumes, bounding boxes, and an inline highlight image showing intersections in red.
- `extract_bom(scad_path: str, output_dir: str = None, formats: list = None)`: Parses inline comment annotations and block metadata from the SCAD file to compile a structured, aggregated Bill of Materials (BOM) exported in JSON, Markdown, and CSV formats.

Always perform visual verification using `compile_and_preview` before finalizing the geometry to ensure correct manifold properties and alignments.

User request: {{args}}
