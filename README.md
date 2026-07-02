# OpenSCAD MCP Server 🚀

An advanced Model Context Protocol (MCP) server that empowers AI coding agents (like Antigravity, GitHub Copilot, Claude Code, and AWS Kiro) to design, visualize, and manufacture 3D parts using OpenSCAD.

## About 📖

This plugin bridges the gap between text-based parametric 3D modeling and real-world fabrication. While standard AI agents struggle with spatial reasoning and cannot physically "see" the 3D models they generate, this MCP server provides a full CAD/CAM toolchain. It allows the agent to:
1. Generate and iteratively edit OpenSCAD geometry.
2. Render visual previews inside the chat window for immediate geometric feedback.
3. Check for physical interferences and collisions between components.
4. Extract structured Bill of Materials (BOM) for hardware procurement.
5. Automatically layout, nest, and export 2D templates for laser cutting or CNC routing.
6. Intelligently split oversized 3D prints into interlocking segments.

Whether you are designing a complex cyberdeck enclosure for laser cutting or a 3D-printable replacement bracket, this server provides the necessary tools for an AI assistant to act as your autonomous engineering co-pilot.

## Installation 🛠️

We provide a universal multi-agent installer out of the box.

1. Ensure you have `uv` installed (`pip install uv`).
2. Clone this repository.
3. Run the installer script:
   ```bash
   uv run python3 install.py
   ```

The installer will automatically detect and configure the MCP server for:
- **Antigravity** (CLI, IDE)
- **Claude Code** (`~/.claude.json`)
- **GitHub Copilot CLI** (`~/.config/github-copilot/mcp.json`)
- **AWS Kiro** (`~/.aws/kiro/mcp.json`)

## Tools & Features 🧰

The server exposes 10 distinct tools via MCP:

- `generate_scad`: Writes and modifies OpenSCAD source files with parameter injection.
- `compile_and_preview`: Renders high-quality orthographic or perspective previews (isometric, top, front, etc.).
- `export_stl`: Finalizes verified geometry into 3D-printable `.stl` files.
- `export_2d_templates`: Flattens selected components onto the Z=0 plane and exports them to `.dxf` or `.svg`.
- `add_dimensions`: Injects blueprint-style extension lines and text annotations for 2D engineering drawings.
- `generate_multiview`: Generates a unified 4-quadrant engineering drawing (front, right, top, isometric).
- `check_interference`: Runs 3D CSG intersection logic to detect and highlight collisions between parts in red.
- `extract_bom`: Parses tagged hardware in comments into a structured JSON/CSV Bill of Materials.
- `nest_panels`: Performs 2D bin-packing to layout parts onto standard material sheets (e.g., 4x8 plywood) accounting for kerf.
- `split_for_printing`: Splits large models along optimal axes and applies interlocking joints (dovetails, flanges, pins).

---

## Sample Conversation 💬

Here is an example of an AI agent using this MCP server to iteratively design a cyberdeck enclosure:

**User:**
> I want to design an enclosure for my cyberdeck. It needs a top panel, a bottom panel, and some structural cleats to hold them together. Make it 250mm wide and 150mm deep. Render a preview so I can see it.

**Agent:**
> I'll use `generate_scad` to write the initial layout with those dimensions, and then use `compile_and_preview` to show you what it looks like.
> *(Agent calls `generate_scad` and `compile_and_preview`)*
> Here is the initial design:
> 
> ![Cyberdeck Isometric](assets/cyberdeck_isometric.png)
> ![Cyberdeck Top](assets/cyberdeck_top.png)
> ![Cyberdeck Front](assets/cyberdeck_front.png)

**User:**
> Looks good, but I think the side cleats are colliding with the top panel. Can you run an interference check?

**Agent:**
> I'll run the `check_interference` tool to verify if there are any overlaps.
> *(Agent calls `check_interference`)*
> Ah, you are correct. The tool found an intersection volume of 3200mm³ between `top_panel` and `cleat_left`. I will adjust the Z-translation of the top panel to add a 0.2mm tolerance gap and fix the collision.

**User:**
> Great, please fix it. Also, can you extract the 2D DXF templates for the top and bottom panels so I can laser cut them? And show me the 2D preview of the cleats.

**Agent:**
> I've applied the fixes. Now, I'll extract the vector files.
> *(Agent calls `generate_scad` to fix the clearance)*
> *(Agent calls `export_2d_templates` with `format="dxf"`)*
> The DXF files have been successfully exported for laser cutting. Here is the 2D layout of the cleats for your reference:
>
> ![Cleats 2D Profile](assets/cleats.png)

**User:**
> This is perfect! Let's extract the BOM so I know how many M3 screws I need, and we can wrap up.

**Agent:**
> *(Agent calls `extract_bom`)*
> Based on the annotations in the design, I've exported `bom.csv`. You will need **16x M3x12 socket head cap screws** to assemble the enclosure.

---
*Built with ❤️ for OpenSCAD & the MCP ecosystem.*
