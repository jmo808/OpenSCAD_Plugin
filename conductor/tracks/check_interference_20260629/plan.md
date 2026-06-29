# Implementation Plan: Collision Detection & Interference Checking Tool

## Phase 1: STL Volume Parser & Shared Utilities [checkpoint: b3b0eaa]

- [x] [e8ce1df] Task: Write tests for STL volume calculation utility
    - [ ] Create a test STL file with known volume (e.g., unit cube = 1000 mm³)
    - [ ] Write test: correctly computes volume of a unit cube STL
    - [ ] Write test: correctly computes volume of a complex mesh (e.g., sphere approximation)
    - [ ] Write test: returns 0.0 for an empty/degenerate STL file
    - [ ] Write test: correctly extracts bounding box (min/max XYZ) from STL vertex data
    - [ ] Write test: raises error for invalid/corrupt STL file
    - [ ] Run tests and confirm they all fail (Red phase)

- [x] [411df53] Task: Implement STL volume parser and bounding box extractor
    - [ ] Create `stl_utils.py` module with `compute_stl_volume(stl_path: str) -> float` function
    - [ ] Implement signed tetrahedron volume formula for binary STL parsing
    - [ ] Implement `extract_bounding_box(stl_path: str) -> dict` function returning `{x_min, x_max, y_min, y_max, z_min, z_max}`
    - [ ] Handle both binary and ASCII STL formats
    - [ ] Run tests and confirm they all pass (Green phase)
    - [ ] Commit: `feat(stl-utils): Implement STL volume and bounding box parser`

- [x] [e66c4e0] Task: Write tests for SCAD part name discovery utility
    - [ ] Create test SCAD fixture with multiple `if (part == "...")` branches
    - [ ] Write test: discovers all part names from a multi-part SCAD file
    - [ ] Write test: returns empty list for SCAD file with no part selector
    - [ ] Write test: handles single-part SCAD files correctly
    - [ ] Run tests and confirm they all fail (Red phase)

- [x] [6293a19] Task: Implement SCAD part name discovery
    - [ ] Create `scad_utils.py` module with `discover_parts(scad_path: str) -> list[str]` function
    - [ ] Use regex to extract part names from `if (part == "...")` and `} else if (part == "...")` patterns
    - [ ] Run tests and confirm they all pass (Green phase)
    - [ ] Commit: `feat(scad-utils): Implement part name discovery from SCAD files`

- [x] [b3b0eaa] Task: Conductor - User Manual Verification 'Phase 1: STL Volume Parser & Shared Utilities' (Protocol in workflow.md)

## Phase 2: Core Interference Detection Logic [checkpoint: ca3e65e]

- [x] [a38fbf5] Task: Write tests for interference detection engine
    - [ ] Create test SCAD fixture with two overlapping cubes (known intersection volume)
    - [ ] Create test SCAD fixture with two non-overlapping cubes (zero intersection)
    - [ ] Write test: detects collision between overlapping components and returns correct volume
    - [ ] Write test: reports zero collisions for non-overlapping components
    - [ ] Write test: pairwise mode checks all N*(N-1)/2 unique pairs
    - [ ] Write test: `fail_fast=true` stops after first collision
    - [ ] Write test: `fail_fast=false` returns complete report for all pairs
    - [ ] Write test: bounding box coordinates are correct for known collision geometry
    - [ ] Write test: raises FileNotFoundError for missing SCAD file
    - [ ] Run tests and confirm they all fail (Red phase)

- [x] [e39a0a7] Task: Implement interference detection engine
    - [ ] Create `interference.py` module with core detection logic
    - [ ] Implement `generate_intersection_scad(scad_path, part_a, part_b) -> str` to generate temporary SCAD code for `intersection() { part_a; part_b; }`
    - [ ] Implement `check_pair(scad_path, part_a, part_b) -> dict | None` that exports intersection to STL and computes volume/bbox
    - [ ] Implement `run_pairwise_check(scad_path, parts, fail_fast) -> list[dict]` that iterates all unique pairs
    - [ ] Use volume threshold (0.001 mm³) to filter noise from floating-point precision
    - [ ] Run tests and confirm they all pass (Green phase)
    - [ ] Commit: `feat(interference): Implement pairwise collision detection engine`

- [x] [ca3e65e] Task: Conductor - User Manual Verification 'Phase 2: Core Interference Detection Logic' (Protocol in workflow.md)

## Phase 3: Visual Highlight Render [checkpoint: 410e70f]

- [x] [177b008] Task: Write tests for collision highlight render
    - [ ] Write test: generates a PNG file for overlapping components with collision highlighted
    - [ ] Write test: PNG file exists at expected output path
    - [ ] Write test: returns inline base64 image data
    - [ ] Write test: no PNG generated when no collisions detected
    - [ ] Run tests and confirm they all fail (Red phase)

- [x] [0fd21b8] Task: Implement collision highlight render
    - [ ] Add `generate_highlight_scad(scad_path, collisions) -> str` to generate SCAD that renders assembly with red intersection overlays
    - [ ] Use existing camera presets and `run_openscad()` helper to render PNG
    - [ ] Return base64-encoded image data for inline MCP response
    - [ ] Save PNG to disk and include file path in response
    - [ ] Run tests and confirm they all pass (Green phase)
    - [ ] Commit: `feat(interference): Add visual collision highlight render`

- [x] [410e70f] Task: Conductor - User Manual Verification 'Phase 3: Visual Highlight Render' (Protocol in workflow.md)

## Phase 4: MCP Tool Integration & Documentation

- [x] [08d5b5e] Task: Write tests for `check_interference` MCP tool
    - [ ] Write test: tool is registered and appears in MCP schema
    - [ ] Write test: returns structured JSON with collision data for overlapping fixture
    - [ ] Write test: returns human-readable summary with file paths
    - [ ] Write test: returns inline base64 PNG for collisions
    - [ ] Write test: returns clean 'no collisions' message for non-overlapping fixture
    - [ ] Run tests and confirm they all fail (Red phase)

- [x] [da6beb0] Task: Implement `check_interference` MCP tool
    - [ ] Add `@mcp.tool()` decorated `check_interference` function to `server.py`
    - [ ] Wire up part discovery, pairwise check, and highlight render
    - [ ] Build structured JSON response with collision array
    - [ ] Build human-readable summary text (conversational tone per product guidelines)
    - [ ] Include absolute file paths for all generated artifacts
    - [ ] Run tests and confirm they all pass (Green phase)
    - [ ] Commit: `feat(server): Implement check_interference MCP tool`

- [x] [bcb040f] Task: Update documentation and installer
    - [ ] Update `instructions.md` with `check_interference` tool documentation
    - [ ] Update `skills/openscad-mcp/SKILL.md` to include new tool description
    - [ ] Run `install.py` to verify schema exports correctly
    - [ ] Commit: `docs(plugin): Add check_interference to instructions and skill`

- [x] Task: Final coverage verification
    - [ ] Run `pytest --cov=. --cov-report=term` and verify >80% coverage
    - [ ] Fix any coverage gaps with targeted tests
    - [ ] Run full test suite one final time
    - [ ] Commit: `test(coverage): Ensure >80% coverage for interference module`

- [ ] Task: Conductor - User Manual Verification 'Phase 4: MCP Tool Integration & Documentation' (Protocol in workflow.md)
