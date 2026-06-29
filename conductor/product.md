# Initial Concept

An MCP server plugin that enables AI coding assistants to design, preview, and export 3D printable and machinable parts using OpenSCAD's programmatic CAD engine. The plugin currently provides three core tools: `generate_scad` (write/modify OpenSCAD source files with parameter injection), `compile_and_preview` (render multi-view PNG previews), and `export_stl` (export 3D-printable STL files).

Based on real-world usage designing a complex woodworking cyberdeck enclosure, the following enhancements have been identified:

1. **Automated Planar Flattening & Nesting (Sheet Layout Tool)** — automatically extract planar sheets from a 3D assembly, rotate them flat, and nest them optimally onto standard stock sheet sizes.
2. **Collision & Interference Detection Tool** — check for intersections between different component groups and report colliding coordinates/volumes.
3. **Automated 2D Blueprinting / Dimensioning Library** — a built-in library of drafting tools that handle external tick marks, extension lines, and text offsets relative to bounding boxes.
4. **Multiview Render Generator** — a single command that exports a combined quadrant image containing front, side, top, and isometric views.
5. **Automated Hardware Bill of Materials (BOM) Parser** — parse tagged hardware components in SCAD files to compile a shopping list of fasteners and off-the-shelf components.

---

# Product Guide: OpenSCAD MCP Plugin

## Vision
The OpenSCAD MCP Plugin is a Model Context Protocol server that empowers AI coding assistants to serve as full-stack CAD/CAM co-pilots. It bridges the gap between parametric 3D modeling in OpenSCAD and real-world fabrication — from 3D printing to CNC routing, laser cutting, and hand woodworking — entirely within an AI chat session.

## Target Users
- **Makers & Hobbyists**: Designing 3D-printable parts, woodworking enclosures, and mixed-material builds with AI assistance. They benefit from automated template generation, dimensioning, and cut lists without needing deep OpenSCAD expertise.
- **Professional Engineers**: Using OpenSCAD for parametric mechanical design in CI/CD pipelines, automated QA, and batch fabrication. They require structured collision reports, BOM extraction, and deterministic export workflows.

## Core Goals
1. **Bridge 3D Assembly to 2D Fabrication**: Automatically extract, flatten, dimension, and nest planar panels from a 3D assembly model into production-ready DXF/SVG cutting templates optimized for stock sheet sizes.
2. **Automate Tedious Workflows**: Eliminate manual multi-view rendering, hand-coded dimensioning routines, and visual-only collision detection with purpose-built MCP tools that return structured, actionable results.
3. **Complete Design-to-Fabrication Pipeline**: Provide an end-to-end workflow from initial concept through parametric modeling, visual verification, interference checking, dimensioned blueprinting, BOM generation, and final export — all within a single AI conversation.
4. **Intelligent 3D Print Preparation**: Support STL export with the ability to automatically split oversized parts and generate sane joining mechanisms (dovetails, overlapping flanges with recessed M2/M3 machine screw and nut pockets) for parts that exceed printer bed dimensions.

## Key Features (Next Release)

### Existing Tools (v0.1.0)
- `generate_scad`: Write/modify OpenSCAD source files with parameter injection.
- `compile_and_preview`: Render multi-view PNG previews (isometric, top, front, right, bottom, back) with configurable camera, projection, and color schemes.
- `export_stl`: Export verified 3D geometry to STL for 3D printing.

### New Tools (Planned)
1. **`export_2d_templates`**: Flatten and export individual panels or all panels from a 3D assembly as DXF/SVG vector files, with automatic rotation of vertical/angled panels to the XY plane.
2. **`nest_panels`**: 2D bin-packing of flattened panel projections onto standard stock sheet sizes (e.g., 24"×48", 4'×8') to minimize material waste, with kerf allowance.
3. **`check_interference`**: Detect and report intersections between named component groups (by color or module name), returning collision coordinates, volumes, and affected module names as structured JSON.
4. **`generate_multiview`**: Render a single combined quadrant image containing front, side, top, and isometric orthographic views in one call.
5. **`add_dimensions`**: Inject external blueprint-style dimension annotations (tick marks, extension lines, text labels with dynamic font sizing) onto 2D panel projections, positioned outside the panel outline to avoid cutout interference.
6. **`extract_bom`**: Parse tagged hardware annotations in SCAD comments (e.g., `// BOM: M3x12 socket head cap screw, qty=4`) and compile a structured JSON bill of materials.
7. **`split_for_printing`**: Automatically split oversized parts along optimal planes, generating interlocking joining features (dovetails, overlapping flanges with recessed M2/M3 screw/nut pockets) and exporting individual STL files per segment.

## Technical Constraints
- **Standard OpenSCAD CLI**: Must work with the unmodified OpenSCAD command-line binary (no custom forks or patches required).
- **MCP FastMCP Pattern**: All new tools must follow the existing `FastMCP` decorator pattern (`@mcp.tool()`) and return structured results (text + optional images/JSON).
- **Dual Output Workflows**: Must support both 3D printing (STL) and 2D fabrication (DXF/SVG) output pipelines as first-class citizens.
- **No External Services**: All processing runs locally using the OpenSCAD binary and Python standard library. No cloud APIs or network dependencies.
