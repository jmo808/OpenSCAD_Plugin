# Implementation Plan: 2D Fabrication Pipeline

## Phase 1: Foundation & Project Setup [checkpoint: 8881c70]

- [x] [65e2025] Task: Set up testing infrastructure and project dependencies
    - [x] Add `pytest-cov` and `Pillow` to `pyproject.toml` dependencies
    - [x] Create `tests/` directory with `conftest.py` and shared fixtures (temp dirs, sample SCAD files)
    - [x] Verify `pytest --cov=. --cov-report=term` runs cleanly against existing code
    - [x] Commit: `chore(setup): Add testing infrastructure and Pillow dependency`

- [x] [6c41667] Task: Refactor `server.py` to extract shared utilities
    - [x] Write tests for `get_openscad_binary()` and a new `run_openscad()` helper
    - [x] Extract common OpenSCAD CLI invocation logic into a `run_openscad(args: list) -> subprocess.CompletedProcess` helper function
    - [x] Extract file validation logic into a `validate_scad_path(path: str) -> str` helper
    - [x] Ensure all existing tools use the new shared helpers
    - [x] Run tests to confirm no regressions
    - [x] Commit: `refactor(server): Extract shared OpenSCAD CLI utilities`

- [x] [8881c70] Task: Conductor - User Manual Verification 'Phase 1: Foundation & Project Setup' (Protocol in workflow.md)

## Phase 2: `export_2d_templates` Tool [checkpoint: 82eb332]

- [x] Task: Write tests for `export_2d_templates`
    - [x] Create a minimal test SCAD file with a `part` selector (e.g., `side_panel` and `back_panel`)
    - [x] Write test: exports DXF for a single named part
    - [x] Write test: exports SVG for a single named part
    - [x] Write test: exports both DXF and SVG when format="both"
    - [x] Write test: returns structured JSON with part_name, format, file_path, width_mm, height_mm
    - [x] Write test: raises FileNotFoundError for missing SCAD file
    - [x] Write test: returns human-readable summary with file paths
    - [x] Run tests and confirm they all fail (Red phase)

- [x] [bdee8ce] Task: Implement `export_2d_templates` tool
    - [x] Add `@mcp.tool()` decorated `export_2d_templates` function to `server.py`
    - [x] Implement SCAD part name parsing (regex for `if (part == "...")` branches)
    - [x] Implement per-part OpenSCAD CLI export (`-D "part=\"<name>\""` with `-o <output>.<ext>`)
    - [x] Build structured JSON response with file metadata
    - [x] Build human-readable summary text
    - [x] Run tests and confirm they all pass (Green phase)
    - [x] Commit: `feat(export): Implement export_2d_templates MCP tool`

- [x] [82eb332] Task: Conductor - User Manual Verification 'Phase 2: export_2d_templates Tool' (Protocol in workflow.md)

## Phase 3: `add_dimensions` Tool

- [x] Task: Write tests for `add_dimensions`
    - [x] Create test SCAD fixture with a simple rectangular panel and a panel with cutouts
    - [x] Write test: dimension lines are placed at negative X/Y coordinates (outside panel outline)
    - [x] Write test: output file is generated at specified path in DXF format
    - [x] Write test: output file is generated at specified path in SVG format
    - [x] Write test: font size scales dynamically based on panel dimensions
    - [x] Write test: `units="inches"` produces inch-formatted labels
    - [x] Write test: custom `offset` parameter controls dimension line placement distance
    - [x] Write test: raises error for missing SCAD file
    - [x] Run tests and confirm they all fail (Red phase)

- [x] [22f9648] Task: Implement `add_dimensions` tool
    - [x] Add `@mcp.tool()` decorated `add_dimensions` function to `server.py`
    - [x] Implement dynamic font sizing: `max(3.5, min(6.0, span * 0.04))`
    - [x] Implement `draw_dim_x` and `draw_dim_y` OpenSCAD module generation (extension lines, tick marks, text labels)
    - [x] Generate wrapper SCAD code that unions the panel projection with dimension annotations
    - [x] Invoke OpenSCAD CLI to render the dimensioned 2D output
    - [x] Return structured response with file path and dimensions
    - [x] Run tests and confirm they all pass (Green phase)
    - [x] Commit: `feat(dimensions): Implement add_dimensions MCP tool`

- [ ] Task: Conductor - User Manual Verification 'Phase 3: add_dimensions Tool' (Protocol in workflow.md)

## Phase 4: `generate_multiview` Tool

- [ ] Task: Write tests for `generate_multiview`
    - [ ] Create test SCAD fixture with simple 3D geometry
    - [ ] Write test: generates a combined PNG with 4 quadrants
    - [ ] Write test: output image dimensions are correct (img_size x img_size)
    - [ ] Write test: returns inline base64 image in MCP response
    - [ ] Write test: returns human-readable summary listing rendered views
    - [ ] Write test: custom `views` parameter overrides default quadrant layout
    - [ ] Write test: raises error for missing SCAD file
    - [ ] Run tests and confirm they all fail (Red phase)

- [ ] Task: Implement `generate_multiview` tool
    - [ ] Add `Pillow` import and image compositing logic
    - [ ] Add `@mcp.tool()` decorated `generate_multiview` function to `server.py`
    - [ ] Render each view individually using existing camera presets via `run_openscad()`
    - [ ] Composite views into a 2x2 grid using Pillow with separator lines and view labels
    - [ ] Return the composite image inline (base64) plus file path and summary text
    - [ ] Run tests and confirm they all pass (Green phase)
    - [ ] Commit: `feat(multiview): Implement generate_multiview MCP tool`

- [ ] Task: Conductor - User Manual Verification 'Phase 4: generate_multiview Tool' (Protocol in workflow.md)

## Phase 5: Documentation & Integration

- [ ] Task: Write tests for updated installer and schema export
    - [ ] Write test: `install.py` exports schemas for all 6 tools (3 existing + 3 new)
    - [ ] Write test: `instructions.md` references all new tools
    - [ ] Run tests and confirm they fail (Red phase)

- [ ] Task: Update documentation and installer
    - [ ] Update `instructions.md` with documentation for all three new tools
    - [ ] Update `skills/openscad-mcp/SKILL.md` to include new tool descriptions
    - [ ] Update `install.py` if needed to handle any new file exports
    - [ ] Run `install.py` to verify schemas export correctly
    - [ ] Run tests and confirm they pass (Green phase)
    - [ ] Commit: `docs(plugin): Update instructions, skill, and installer for new tools`

- [ ] Task: Final coverage verification and cleanup
    - [ ] Run `pytest --cov=. --cov-report=term` and verify >80% coverage
    - [ ] Fix any coverage gaps by adding targeted tests
    - [ ] Run full test suite one final time
    - [ ] Commit: `test(coverage): Ensure >80% coverage for all modules`

- [ ] Task: Conductor - User Manual Verification 'Phase 5: Documentation & Integration' (Protocol in workflow.md)
