# Specification: Collision Detection & Interference Checking Tool (`check_interference`)

## Overview
This track implements a new MCP tool (`check_interference`) that detects and reports geometric intersections (collisions) between components in an OpenSCAD assembly model. It addresses a critical gap in the current plugin: the inability to programmatically verify that components do not overlap, which currently requires manual visual inspection of rendered previews.

## Problem Statement
When designing multi-component assemblies (e.g., a cyberdeck enclosure with side panels, cleats, keyboard plates, and display bezels), components can unintentionally overlap due to:
- Incorrect translation offsets after parameter changes
- Tolerance miscalculations between mating parts
- Copy-paste errors in component positioning

Currently, the only way to detect these overlaps is to visually inspect rendered previews from multiple angles — a tedious, error-prone process that misses internal collisions entirely.

## Functional Requirements

### FR-1: Component Discovery
- The tool MUST parse the SCAD source file to discover all available components by extracting part selector branches (e.g., `if (part == "side_panel")`).
- The tool MUST support the existing part selector pattern used by the codebase.
- The tool MUST list discovered components in its response.

### FR-2: Pairwise Interference Detection
- The tool MUST check every unique pair of discovered components for geometric intersection.
- For each pair, the tool MUST use OpenSCAD's `intersection()` CSG operation to compute the overlapping volume.
- The tool MUST determine whether the intersection is non-empty (i.e., the intersection produces geometry with non-zero volume).

### FR-3: Collision Report — Structured JSON
For each detected collision, the tool MUST return a structured JSON object containing:
- `part_a` (str): Name of the first component.
- `part_b` (str): Name of the second component.
- `intersection_volume_mm3` (float): Volume of the overlapping region in cubic millimeters.
- `bounding_box` (object): Min/max XYZ coordinates of the collision zone (`x_min`, `x_max`, `y_min`, `y_max`, `z_min`, `z_max`).

### FR-4: Visual Collision Highlight
- The tool MUST generate a preview PNG render that highlights colliding regions in red (`color("red")`) against the full assembly rendered in a neutral/transparent style.
- The highlight render MUST be returned inline (base64) in the MCP response.
- The highlight render MUST also be saved to disk, with the file path included in the response.

### FR-5: Early Exit (Fail Fast)
- The tool MUST support an optional `fail_fast` parameter (default `false`).
- When `fail_fast=true`, the tool MUST stop checking after the first detected collision and return immediately with that collision's full report.
- When `fail_fast=false` (default), the tool MUST check all pairs and return a complete report.

### FR-6: Human-Readable Summary
- The tool MUST return a conversational human-readable summary alongside the JSON.
- If no collisions: `"Great news! All N components passed interference checking — no collisions detected."`
- If collisions found: List each collision pair with volume and a brief description.

## Non-Functional Requirements

### NFR-1: Performance
- For assemblies with up to 10 components (45 pairs), the tool should complete within 120 seconds on a typical workstation.

### NFR-2: Standard OpenSCAD CLI
- The tool MUST work with the unmodified OpenSCAD CLI binary. No custom forks or patches.

### NFR-3: MCP Pattern Compliance
- The tool MUST follow the existing `@mcp.tool()` FastMCP decorator pattern.
- The tool MUST return structured results (text + images + JSON).

## Technical Approach

### Volume Calculation
For each pair (A, B):
1. Generate a temporary SCAD file that computes `intersection() { A(); B(); }` and exports it to STL.
2. Use OpenSCAD CLI to export the intersection as STL.
3. Parse the STL to compute mesh volume using the signed tetrahedron formula (Python, no external library).
4. If volume > tolerance threshold (e.g., 0.001 mm³), flag as collision.

### Bounding Box Extraction
1. Export the intersection geometry to STL.
2. Parse the STL vertex data to extract min/max XYZ coordinates.

### Visual Highlight
1. Generate a temporary SCAD file that renders the full assembly in neutral colors with `intersection() { A(); B(); }` overlaid in `color("red")`.
2. Render a preview PNG using the existing camera presets.

## Acceptance Criteria
1. Tool is registered via `@mcp.tool()` and appears in the MCP schema.
2. Correctly detects known overlapping components in a test SCAD file.
3. Correctly reports zero collisions for a test SCAD file with no overlaps.
4. Returns structured JSON with volume, bounding box, and part names for each collision.
5. Returns inline base64 PNG highlight render when collisions are found.
6. `fail_fast=true` stops after the first collision.
7. Human-readable summary is conversational and includes file paths.
8. Unit test coverage exceeds 80% for all new code.

## Out of Scope
- Tolerance/clearance analysis (checking that parts maintain a minimum gap).
- Automatic fix suggestions (moving parts to resolve collisions).
- Animation of collision zones.
- Non-part-selector component identification (color-based, module name-based).
