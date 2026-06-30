# Implementation Plan: Part Splitting with Joining Mechanisms for 3D Printing

## Phase 1: Split Plane Calculation [checkpoint: 28e1bda]

- [x] [b07058f] Task: Write tests for bounding box extraction and split plane calculation
    - [x] Create test SCAD fixture with a known oversized part (e.g., 300×150×400mm box)
    - [x] Write test: extracts correct bounding box dimensions from a part via OpenSCAD CLI
    - [x] Write test: auto mode identifies Z as oversize axis for a 400mm tall part on 250mm bed
    - [x] Write test: auto mode computes correct split coordinate (midpoint) for single split
    - [x] Write test: auto mode computes multiple split coordinates for very large parts (3+ segments)
    - [x] Write test: auto mode identifies multiple oversize axes and splits each
    - [x] Write test: manual mode uses user-specified axis and coordinate
    - [x] Write test: safety margin (5mm) is subtracted from bed dimensions
    - [x] Write test: raises error if part already fits within bed (no split needed)
    - [x] Run tests and confirm they all fail (Red phase)

- [x] [5cfc3ab] Task: Implement split plane calculator
    - [x] Create `splitting.py` module
    - [x] Implement `get_part_bbox(scad_path, part_name) -> dict` using OpenSCAD STL export + vertex parsing (reuse `stl_utils.py` bounding box extractor)
    - [x] Implement `calculate_split_planes(bbox, bed_x, bed_y, bed_z, margin) -> list[dict]` for auto mode
    - [x] Implement `validate_manual_split(bbox, axis, coord) -> dict` for manual mode
    - [x] Run tests and confirm they all pass (Green phase)
    - [x] Commit: `feat(splitting): Implement split plane calculation and bounding box extraction`

- [x] [28e1bda] Task: Conductor - User Manual Verification 'Phase 1: Split Plane Calculation' (Protocol in workflow.md)

## Phase 2: Joining Mechanism Generators [checkpoint: af5b37c]

- [x] [0b863d1] Task: Write tests for dovetail joint generator
    - [x] Write test: generates valid OpenSCAD code for dovetail fingers on a flat face
    - [x] Write test: male and female halves interlock (intersection volume > 0 when mated)
    - [x] Write test: clearance parameter widens female slots correctly
    - [x] Write test: finger count and dimensions are configurable
    - [x] Run tests and confirm they all fail (Red phase)

- [x] [d5146e7] Task: Implement dovetail joint generator
    - [x] Add `generate_dovetail_scad(face_width, face_height, params) -> tuple[str, str]` to `splitting.py`
    - [x] Generate OpenSCAD code for male (protruding) and female (recessed) dovetail geometry
    - [x] Apply clearance to female side
    - [x] Return SCAD code strings for union with each half
    - [x] Run tests and confirm they all pass (Green phase)
    - [x] Commit: `feat(splitting): Implement dovetail joint generator`

- [x] [b0eea10] Task: Write tests for flange joint generator
    - [x] Write test: generates overlapping tab geometry with correct dimensions
    - [x] Write test: counterbored clearance holes on one half, hex nut pockets on the other
    - [x] Write test: screw count and size (M2, M3, M4) are configurable
    - [x] Write test: clearance parameter applied to hole diameters
    - [x] Run tests and confirm they all fail (Red phase)

- [x] [98b25db] Task: Implement flange joint generator
    - [x] Add `generate_flange_scad(face_width, face_height, params) -> tuple[str, str]` to `splitting.py`
    - [x] Generate tab geometry with M3 counterbored holes and hex nut traps
    - [x] Use standard metric fastener dimensions (M3: 3.0mm shaft, 5.5mm head, 6.4mm nut width)
    - [x] Run tests and confirm they all pass (Green phase)
    - [x] Commit: `feat(splitting): Implement flange joint with screw/nut pockets`

- [x] [170572b] Task: Write tests for tongue-and-groove and pin joint generators
    - [x] Write test: tongue-and-groove produces matching ridge and slot geometry
    - [x] Write test: pin holes are correctly sized and positioned on both halves
    - [x] Write test: clearance applied correctly to both joint types
    - [x] Run tests and confirm they all fail (Red phase)

- [x] [8dd1f5b] Task: Implement tongue-and-groove and pin joint generators
    - [x] Add `generate_tongue_groove_scad(face_width, face_height, params) -> tuple[str, str]`
    - [x] Add `generate_pin_scad(face_width, face_height, params) -> tuple[str, str]`
    - [x] Run tests and confirm they all pass (Green phase)
    - [x] Commit: `feat(splitting): Implement tongue-groove and pin joint generators`

- [x] [af5b37c] Task: Conductor - User Manual Verification 'Phase 2: Joining Mechanism Generators' (Protocol in workflow.md)

## Phase 3: Part Splitting Engine & STL Export [checkpoint: 8cf0a4c]

- [x] [1a7560b] Task: Write tests for part splitting engine
    - [x] Write test: splits a box into 2 halves at Z midpoint and exports 2 STL files
    - [x] Write test: each exported STL is manifold (non-zero volume)
    - [x] Write test: each segment fits within the specified bed dimensions
    - [x] Write test: joint features are correctly applied to split faces
    - [x] Write test: auto joint selection picks flange for Z-splits and dovetail for X/Y-splits
    - [x] Write test: explicit `joint_type` parameter overrides auto selection
    - [x] Write test: file naming follows `<name>_part_N.stl` convention
    - [x] Run tests and confirm they all fail (Red phase)

- [x] [30173f2] Task: Implement part splitting engine
    - [x] Add `split_part(scad_path, part_name, split_planes, joint_configs) -> list[dict]` to `splitting.py`
    - [x] For each split plane, generate temporary SCAD code that:
      1. Intersects the original part with a half-space (cube positioned above/below the split plane)
      2. Unions the appropriate joint geometry onto the split face
    - [x] Invoke OpenSCAD CLI to export each segment as STL
    - [x] Verify each STL has non-zero volume
    - [x] Implement `auto_select_joint(axis) -> str` for automatic joint selection
    - [x] Run tests and confirm they all pass (Green phase)
    - [x] Commit: `feat(splitting): Implement part splitting engine with joint application`

- [x] [8cf0a4c] Task: Conductor - User Manual Verification 'Phase 3: Part Splitting Engine & STL Export' (Protocol in workflow.md)

## Phase 4: Exploded Preview & MCP Tool Integration

- [x] [12b8f97, c7138b4] Task: Write tests for exploded preview and MCP tool
    - [x] Write test: generates exploded preview SCAD with parts translated outwards from center
    - [x] Write test: MCP tool schema matches the expected parameters
    - [x] Write test: MCP tool correctly calls `split_part` and handles output serialization
    - [x] Run tests and confirm they all fail (Red phase)

- [~] Task: Implement exploded preview render
    - [ ] Add `generate_exploded_scad(scad_path, part_name, split_planes, joint_configs, offset) -> str` to `splitting.py`
    - [ ] Generate temporary SCAD that translates each segment along the split axis with offset gaps
    - [ ] Run tests and confirm they all pass (Green phase)
    - [ ] Commit: `feat(splitting): Implement exploded view preview render`

- [x] [c7138b4] Task: Write tests for `split_for_printing` MCP tool
    - [x] Write test: tool is registered and appears in MCP schema
    - [x] Write test: auto mode returns structured JSON with correct segments for oversized part
    - [x] Write test: manual mode returns correct split at specified coordinate
    - [x] Write test: returns human-readable summary with file paths
    - [x] Write test: returns inline exploded preview PNG
    - [x] Run tests and confirm they all fail (Red phase)

- [ ] Task: Implement `split_for_printing` MCP tool
    - [ ] Add `@mcp.tool()` decorated `split_for_printing` function to `server.py`
    - [ ] Wire up split plane calculation, joint generation, splitting engine, and preview
    - [ ] Build structured JSON response matching the schema
    - [ ] Build conversational human-readable summary
    - [ ] Include absolute file paths for all exported STLs and preview
    - [ ] Run tests and confirm they all pass (Green phase)
    - [ ] Commit: `feat(server): Implement split_for_printing MCP tool`

- [ ] Task: Conductor - User Manual Verification 'Phase 4: Exploded Preview & MCP Tool Integration' (Protocol in workflow.md)

## Phase 5: Documentation & Final Verification

- [ ] Task: Update documentation and installer
    - [ ] Update `instructions.md` with `split_for_printing` tool documentation
    - [ ] Update `skills/openscad-mcp/SKILL.md` to include new tool description
    - [ ] Run `install.py` to verify schema exports correctly
    - [ ] Commit: `docs(plugin): Add split_for_printing to instructions and skill`

- [ ] Task: Final coverage verification
    - [ ] Run `pytest --cov=. --cov-report=term` and verify >80% coverage
    - [ ] Fix any coverage gaps with targeted tests
    - [ ] Run full test suite one final time
    - [ ] Commit: `test(coverage): Ensure >80% coverage for splitting module`

- [ ] Task: Conductor - User Manual Verification 'Phase 5: Documentation & Final Verification' (Protocol in workflow.md)
