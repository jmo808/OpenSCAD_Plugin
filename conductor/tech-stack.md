# Tech Stack: OpenSCAD MCP Plugin

## Language
- **Python 3.12+**: Primary implementation language for the MCP server, installer, and all tool logic.

## Server Framework
- **MCP SDK (`mcp` package)**: Provides the Model Context Protocol transport layer.
- **FastMCP**: High-level decorator-based API (`@mcp.tool()`) for defining tools with automatic schema generation and structured response handling.

## Build & Dependency Management
- **uv**: Fast Python package installer and resolver. Manages the virtual environment (`.venv/`) and lockfile (`uv.lock`).
- **pyproject.toml**: PEP 621 project metadata and dependency declarations.

## Testing
- **pytest**: Unit and integration testing framework (dev dependency).

## External Tools
- **OpenSCAD CLI**: Headless command-line 3D CAD engine. Used for compiling `.scad` source files, rendering PNG previews, and exporting STL/DXF/SVG output. Must be the standard unmodified binary (no forks).

## Planned Dependencies
- **Pillow (PIL)**: Image compositing library for the `generate_multiview` tool (combining multiple rendered views into a single quadrant image).
- **Standard Library Only**: For 2D geometry operations (panel flattening, nesting, collision detection), prefer Python standard library (`math`, `json`, `subprocess`, `tempfile`) to minimize external dependencies. Only add third-party packages when the standard library is demonstrably insufficient.

## Architecture
- **Single-file server** (`server.py`): All MCP tool definitions in one module.
- **Installer** (`install.py`): Copies schemas, instructions, and plugin config to the Gemini agent's config directories.
- **Skill definition** (`skills/openscad-mcp/SKILL.md`): Describes the plugin's capabilities and usage for the AI agent.
- **Instructions** (`instructions.md`): Detailed tool documentation installed alongside the MCP schemas.

## File Structure
```
openscadPlugin/
├── server.py              # MCP server with all tool definitions
├── install.py             # Schema and plugin installer
├── instructions.md        # Tool usage documentation
├── plugin.json            # Plugin identity metadata
├── mcp_config.json        # MCP server launch configuration
├── pyproject.toml         # Project metadata and dependencies
├── uv.lock                # Locked dependency versions
├── skills/
│   └── openscad-mcp/
│       └── SKILL.md       # AI agent skill definition
└── conductor/             # Project management artifacts
```
