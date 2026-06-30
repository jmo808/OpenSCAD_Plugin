# Specification: Part Splitting with Joining Mechanisms for 3D Printing (`split_for_printing`)

## Overview
This track implements a new MCP tool (`split_for_printing`) that automatically splits oversized 3D parts along optimal planes to fit within a given printer bed volume, generating interlocking joining features at each split interface and exporting individual STL files per segment.

## Problem Statement
Many parametric assemblies produce individual parts that exceed the build volume of consumer 3D printers (typically 220×220×250mm). Currently, the user must:
- Manually determine where to split the part
- Hand-code Boolean operations to cut the geometry
- Design and position joining features (screw holes, dovetails) by hand
- Export each segment as a separate STL

This is error-prone, especially when tolerances for press-fit joints and fastener pockets must be precise.

## Functional Requirements

### FR-1: Split Strategies
The tool MUST support two split modes:

1. **Manual split** (`mode="manual"`):
   - User specifies a split plane: axis (`"x"`, `"y"`, or `"z"`) and coordinate (mm).
   - The part is cut into two halves at the specified plane.
   - Multiple manual splits can be chained (split A at Z=125, then split A_top at Z=250).

2. **Automatic split** (`mode="auto"`):
   - The tool analyzes the part's bounding box against the printer bed dimensions.
   - If any axis exceeds the bed, the tool determines the minimum number of cuts needed.
   - Splits are placed at evenly-spaced intervals along the oversize axis.
   - If multiple axes are oversize, splits are applied to each independently.

Default mode: `"auto"`.

### FR-2: Printer Bed Configuration
- The tool MUST accept `bed_x`, `bed_y`, `bed_z` parameters (in mm).
- Default: `bed_x=220`, `bed_y=220`, `bed_z=250` (common consumer FDM printers).
- The tool MUST subtract a safety margin (default 5mm per side) from the bed dimensions to account for bed clips, purge lines, and adhesion brims.

### FR-3: Joining Mechanisms
The tool MUST support four joining mechanism types, generated as CSG features at each split interface:

1. **`"dovetail"`**: Interlocking wedge-shaped fingers.
   - Parameters: `finger_count`, `finger_width`, `finger_depth`, `taper_angle`.
   - Best for: Vertical splits, high shear strength, no fasteners needed.

2. **`"flange"`**: Overlapping flat tabs with recessed M3 screw holes and hex nut traps.
   - Parameters: `flange_width`, `flange_thickness`, `screw_size` (M2, M3, M4), `screw_count`.
   - Generates: Counterbored clearance holes on one half, hex nut pockets on the other.
   - Best for: Horizontal splits, serviceable (disassemble/reassemble).

3. **`"tongue_groove"`**: Protruding ridge on one half, matching slot on the other.
   - Parameters: `tongue_width`, `tongue_depth`, `clearance`.
   - Best for: Alignment-critical joints, simple geometry.

4. **`"pin"`**: Cylindrical dowel alignment holes on both halves.
   - Parameters: `pin_diameter`, `pin_depth`, `pin_count`.
   - Best for: Simple alignment, requires glue or external pins.

### FR-4: Automatic Joint Selection
- When `joint_type` is not specified, the tool MUST auto-select based on:
  - **Z-axis splits** (horizontal): `"flange"` (gravity-friendly, serviceable)
  - **X/Y-axis splits** (vertical): `"dovetail"` (shear-resistant)
- The user MAY override with an explicit `joint_type` parameter.

### FR-5: Tolerance & Clearance
- All joining features MUST include a configurable `clearance` parameter (default: 0.2mm).
- This clearance is applied to the female side of each joint (holes enlarged, slots widened) to account for FDM printing tolerances.

### FR-6: Output — STL Files
- The tool MUST export each segment as a separate, manifold STL file.
- File naming convention: `<original_name>_part_1.stl`, `<original_name>_part_2.stl`, etc.
- Each STL MUST be oriented for optimal print orientation (largest flat face on the build plate).

### FR-7: Output — Assembly Preview
- The tool MUST generate a preview PNG showing all segments in an exploded view (offset along the split axis) with joining features visible.
- The preview MUST be returned inline (base64) in the MCP response.

### FR-8: Output — Structured JSON
The tool MUST return structured JSON:
```json
{
  "segments": [
    {
      "name": "bracket_part_1",
      "stl_path": "/abs/path/to/bracket_part_1.stl",
      "dimensions_mm": {"x": 110, "y": 85, "z": 125},
      "fits_bed": true,
      "joint_type": "flange",
      "joint_face": "top"
    }
  ],
  "summary": {
    "total_segments": 2,
    "split_axes": ["z"],
    "split_coordinates_mm": [125.0],
    "joint_types_used": ["flange"],
    "printer_bed_mm": {"x": 220, "y": 220, "z": 250},
    "preview_image_path": "/abs/path/to/exploded_preview.png"
  }
}
```

### FR-9: Human-Readable Summary
- Conversational summary with absolute file paths.
- Example: "Split 'bracket' into 2 segments along Z at 125mm. Joint type: flange (M3 screws × 4). Both segments fit within 220×220×250mm bed. STLs exported to /path/to/bracket_part_1.stl and /path/to/bracket_part_2.stl."

## Non-Functional Requirements

### NFR-1: Standard OpenSCAD CLI
- All CSG operations (splitting, joint generation) MUST be implemented as OpenSCAD code generated dynamically and compiled via the CLI.

### NFR-2: MCP Pattern Compliance
- `@mcp.tool()` FastMCP decorator pattern. Returns text + images + JSON.

### NFR-3: Performance
- Splitting a single part into 2-4 segments with joints should complete within 60 seconds.

## Tool Interface

```python
@mcp.tool()
def split_for_printing(
    scad_path: str,
    part_name: str = None,
    output_dir: str = None,
    mode: str = "auto",
    split_axis: str = None,
    split_coord: float = None,
    joint_type: str = None,
    bed_x: float = 220,
    bed_y: float = 220,
    bed_z: float = 250,
    clearance: float = 0.2
) -> list:
```

## Acceptance Criteria
1. Tool is registered via `@mcp.tool()` and appears in the MCP schema.
2. Manual split correctly bisects a test part at the specified plane.
3. Auto split correctly determines split planes for an oversized test part.
4. Dovetail joints interlock correctly (verified by intersection volume ≈ 0).
5. Flange joints have correct counterbored holes and hex nut pockets.
6. Tongue-and-groove joints have correct clearance.
7. Pin holes are correctly positioned and sized.
8. Each exported STL is manifold and fits within the specified bed.
9. Exploded preview PNG renders correctly.
10. Unit test coverage exceeds 80% for all new code.

## Out of Scope
- Non-planar splits (curved or angled cutting surfaces).
- Thread generation for screws (uses clearance holes + nut traps instead).
- Automatic print orientation optimization beyond flat-face-down.
- Multi-part assembly splitting (only single parts, not full assemblies).
- G-code generation or slicer integration.
