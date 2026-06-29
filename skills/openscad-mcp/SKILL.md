---
name: openscad-mcp
description: Design, preview, and export 3D printable mechanical and functional parts in OpenSCAD.
---
Please use the openscad-mcp MCP server tools to design, render, and export 3D models in OpenSCAD based on the user's request.

Available tools:
- `generate_scad(scad_code: str, output_path: str, parameters: dict = None)`: Writes or modifies OpenSCAD code, supporting parameter injections at the top.
- `compile_and_preview(scad_path: str, output_dir: str = None, img_size: int = 512, projection: str = "ortho", colorscheme: str = "Sunset", views: list = None)`: Compiles the SCAD file and returns images from multiple perspective cameras (e.g. isometric, top, front) directly back into the context window for visual verification.
- `export_stl(scad_path: str, output_path: str)`: Exports the verified 3D manifold geometry to a standard STL file ready for 3D printing.

Always perform visual verification using `compile_and_preview` before finalizing the geometry to ensure correct manifold properties and alignments.

User request: {{args}}
