# Implementation Plan: Panel Nesting & Sheet Layout Optimization Tool

## Phase 1: Panel Dimension Extraction [checkpoint: 67292da]

- [x] [b3990bc] Task: Write tests for panel dimension extraction
    - [x] Create test SCAD fixture with 3-4 parts of known dimensions
    - [x] Write test: extracts correct width and height for a rectangular panel
    - [x] Write test: extracts dimensions for all parts when no `parts` filter is given
    - [x] Write test: extracts dimensions for only specified parts when `parts` filter is provided
    - [x] Write test: raises FileNotFoundError for missing SCAD file
    - [x] Write test: returns empty list for SCAD file with no part selector
    - [x] Run tests and confirm they all fail (Red phase)

- [x] [c130cfd] Task: Implement panel dimension extraction
    - [x] Create `nesting.py` module
    - [x] Implement `extract_panel_dimensions(scad_path: str, parts: list[str] | None) -> list[dict]` that exports each part's 2D projection via OpenSCAD CLI and computes bounding box dimensions
    - [x] Reuse `discover_parts()` from `scad_utils.py` (created in check_interference track) or implement locally if that track hasn't been completed yet
    - [x] Return list of `{part_name, width_mm, height_mm}` dicts
    - [x] Run tests and confirm they all pass (Green phase)
    - [x] Commit: `feat(nesting): Implement panel dimension extraction from SCAD`

- [x] [67292da] Task: Conductor - User Manual Verification 'Phase 1: Panel Dimension Extraction' (Protocol in workflow.md)

## Phase 2: Packing Algorithms

- [x] [68ec82e] Task: Write tests for shelf packing algorithm (simple)
    - [x] Write test: packs 3 rectangles onto a sheet without overlap
    - [x] Write test: kerf gaps are applied between panels and from sheet edges
    - [x] Write test: starts a new shelf when current shelf is full
    - [x] Write test: allocates a second sheet when first sheet overflows
    - [x] Write test: all placed panels are within sheet bounds
    - [x] Write test: returns correct `utilization_percent` for known layout
    - [x] Run tests and confirm they all fail (Red phase)

- [x] [7824a1d] Task: Implement shelf packing algorithm (simple)
    - [x] Add `pack_shelf(panels: list[dict], sheet_w: float, sheet_h: float, kerf: float) -> list[dict]` to `nesting.py`
    - [x] Place panels left-to-right on horizontal shelves with kerf spacing
    - [x] Track current shelf height, advance to next shelf or next sheet as needed
    - [x] Calculate `utilization_percent` and `waste_area_mm2` per sheet
    - [x] Run tests and confirm they all pass (Green phase)
    - [x] Commit: `feat(nesting): Implement simple shelf packing algorithm`

- [~] Task: Write tests for optimized packing algorithm (FFD with rotation)
    - [ ] Write test: sorts panels by area descending before packing
    - [ ] Write test: rotates panels 90° when it yields a better fit
    - [ ] Write test: achieves equal or better utilization than shelf algorithm for the same input
    - [ ] Write test: kerf gaps are correctly applied
    - [ ] Write test: multi-sheet allocation works correctly
    - [ ] Run tests and confirm they all fail (Red phase)

- [ ] Task: Implement FFD packing algorithm
    - [ ] Add `pack_ffd(panels: list[dict], sheet_w: float, sheet_h: float, kerf: float) -> list[dict]` to `nesting.py`
    - [ ] Sort panels by area (largest first)
    - [ ] For each panel, try both orientations and place in first available position
    - [ ] Use a free-rectangle tracking approach for available space
    - [ ] Compute utilization percentage per sheet
    - [ ] Run tests and confirm they all pass (Green phase)
    - [ ] Commit: `feat(nesting): Implement FFD (optimized) packing algorithm`

- [ ] Task: Conductor - User Manual Verification 'Phase 2: Packing Algorithms' (Protocol in workflow.md)

## Phase 3: Visual Layout Rendering

- [ ] Task: Write tests for layout PNG generation
    - [ ] Write test: generates a PNG file for a valid nesting layout
    - [ ] Write test: PNG contains labeled rectangles (verify file is non-empty and correct size)
    - [ ] Write test: returns inline base64 image data
    - [ ] Write test: generates separate PNGs for multi-sheet layouts
    - [ ] Run tests and confirm they all fail (Red phase)

- [ ] Task: Implement layout PNG rendering
    - [ ] Add `render_layout_png(sheet: dict, output_path: str, img_size: int) -> bytes` to `nesting.py`
    - [ ] Use Pillow (PIL) to draw sheet outline, panel rectangles, kerf gaps, and text labels
    - [ ] Scale drawing to fit `img_size` while preserving aspect ratio
    - [ ] Draw dimension labels for the sheet edges
    - [ ] Return base64-encoded image data for inline MCP response
    - [ ] Run tests and confirm they all pass (Green phase)
    - [ ] Commit: `feat(nesting): Implement visual layout PNG rendering with Pillow`

- [ ] Task: Conductor - User Manual Verification 'Phase 3: Visual Layout Rendering' (Protocol in workflow.md)

## Phase 4: MCP Tool Integration & Documentation

- [ ] Task: Write tests for `nest_panels` MCP tool
    - [ ] Write test: tool is registered and appears in MCP schema
    - [ ] Write test: returns structured JSON matching the schema for a valid SCAD file
    - [ ] Write test: returns human-readable summary with file paths and utilization
    - [ ] Write test: returns inline base64 PNG layout image
    - [ ] Write test: `strategy="simple"` uses shelf algorithm
    - [ ] Write test: `strategy="optimized"` uses FFD algorithm
    - [ ] Write test: custom `sheet_width` and `sheet_height` override preset
    - [ ] Run tests and confirm they all fail (Red phase)

- [ ] Task: Implement `nest_panels` MCP tool
    - [ ] Add `@mcp.tool()` decorated `nest_panels` function to `server.py`
    - [ ] Wire up panel extraction, packing algorithm selection, and layout rendering
    - [ ] Build structured JSON response matching the schema
    - [ ] Build conversational human-readable summary text
    - [ ] Include absolute file paths for all generated layout PNGs
    - [ ] Run tests and confirm they all pass (Green phase)
    - [ ] Commit: `feat(server): Implement nest_panels MCP tool`

- [ ] Task: Update documentation and installer
    - [ ] Update `instructions.md` with `nest_panels` tool documentation
    - [ ] Update `skills/openscad-mcp/SKILL.md` to include new tool description
    - [ ] Run `install.py` to verify schema exports correctly
    - [ ] Commit: `docs(plugin): Add nest_panels to instructions and skill`

- [ ] Task: Final coverage verification
    - [ ] Run `pytest --cov=. --cov-report=term` and verify >80% coverage
    - [ ] Fix any coverage gaps with targeted tests
    - [ ] Run full test suite one final time
    - [ ] Commit: `test(coverage): Ensure >80% coverage for nesting module`

- [ ] Task: Conductor - User Manual Verification 'Phase 4: MCP Tool Integration & Documentation' (Protocol in workflow.md)
