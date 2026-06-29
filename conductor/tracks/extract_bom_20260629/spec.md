# Specification: BOM Extraction & Hardware Shopping List Tool (`extract_bom`)

## Overview
This track implements a new MCP tool (`extract_bom`) that parses tagged hardware annotations embedded in OpenSCAD source files and compiles them into a structured, aggregated Bill of Materials (BOM). The tool produces output in multiple formats (JSON, Markdown table, CSV) suitable for procurement, documentation, and downstream tooling.

## Problem Statement
When designing assemblies with fasteners, standoffs, connectors, and other off-the-shelf hardware, there is no automated way to extract a shopping list from the SCAD source code. The AI agent adds hardware components during the design process (e.g., mounting screws, press-fit inserts), but these are scattered across hundreds of lines as ad-hoc comments. Manually inventorying them is tedious and error-prone, especially when quantities change during iteration.

## Functional Requirements

### FR-1: Dual Annotation Parsing
The tool MUST support two annotation formats:

**Inline comment annotations** (anywhere in the file):
```
// BOM: M3x12 socket head cap screw, qty=4, category=fastener
// BOM: M2.5 brass heat-set insert, qty=8, category=fastener, supplier=McMaster, part_number=94180A321
```

**Module-level metadata blocks** (inside or above module definitions):
```
/* BOM:
 *   name: M3 hex nut
 *   qty: 4
 *   category: fastener
 */
module bracket_hardware() { ... }
```

The parser MUST handle both formats simultaneously in the same file.

### FR-2: BOM Entry Fields
Each parsed BOM entry MUST capture the following fields:
- `name` (str, required): Part name/description (e.g., "M3x12 Socket Head Cap Screw")
- `qty` (int, required): Quantity per instance
- `category` (str, required): Hardware category (e.g., "fastener", "connector", "bearing", "standoff", "electronic")
- `supplier` (str, optional): Supplier name (e.g., "McMaster", "DigiKey")
- `part_number` (str, optional): Supplier part number
- `source_line` (int): Line number in the SCAD file where the annotation was found

### FR-3: Aggregation
- The tool MUST aggregate identical items by matching on `name` (case-insensitive) and `category`.
- Aggregated entries MUST sum `qty` across all instances.
- The tool MUST group the final output by `category`.
- Within each category, entries MUST be sorted alphabetically by `name`.

### FR-4: Multi-Format Output
The tool MUST produce output in all three formats:

1. **Structured JSON** (`bom.json`): Array of aggregated BOM entries grouped by category, with a `total_unique_items` and `total_quantity` summary.
2. **Markdown Table** (`bom.md`): Human-readable table with columns: Category | Part Name | Qty | Supplier | Part # — with category group headers.
3. **CSV** (`bom.csv`): Spreadsheet-compatible flat export with headers: `category,name,qty,supplier,part_number`.

All three files MUST be written to the specified `output_dir`.

### FR-5: Human-Readable Summary
- The tool MUST return a conversational summary in the MCP response.
- Example: "Found 14 hardware items across 4 categories (23 total parts). BOM exported to 3 formats: bom.json, bom.md, bom.csv."
- The summary MUST include absolute file paths for all generated files.

### FR-6: Error Handling
- If no BOM annotations are found, return a clear message: "No BOM annotations found in the SCAD file. To add hardware items, use `// BOM: <name>, qty=<n>, category=<cat>` comments."
- If a BOM annotation is malformed (missing required fields), warn with line number but continue parsing remaining annotations.

## Non-Functional Requirements

### NFR-1: No External Dependencies
- The parser MUST use only Python standard library (regex, csv, json). No third-party parsing libraries.

### NFR-2: MCP Pattern Compliance
- The tool MUST follow the existing `@mcp.tool()` FastMCP decorator pattern.
- The tool MUST return structured results (text + JSON).

## Tool Interface

```python
@mcp.tool()
def extract_bom(
    scad_path: str,
    output_dir: str = None,
    formats: list = None  # default: ["json", "md", "csv"]
) -> str:
```

**Inputs:**
- `scad_path` (str): Path to the OpenSCAD source file to parse.
- `output_dir` (str, optional): Directory for output files. Defaults to `~/.openscad_bom/`.
- `formats` (list, optional): Which formats to export. Default: `["json", "md", "csv"]`.

**Returns:** Human-readable summary + structured JSON in response.

## Acceptance Criteria
1. Tool is registered via `@mcp.tool()` and appears in the MCP schema.
2. Correctly parses inline `// BOM:` comment annotations.
3. Correctly parses multi-line `/* BOM: ... */` metadata blocks.
4. Aggregates identical items and sums quantities.
5. Groups output by category, sorted alphabetically.
6. Produces valid JSON, well-formatted Markdown table, and valid CSV.
7. Returns conversational summary with absolute file paths.
8. Warns on malformed annotations without crashing.
9. Unit test coverage exceeds 80% for all new code.

## Out of Scope
- Price lookup or cost estimation.
- Automatic supplier API integration.
- BOM diffing between file versions.
- Recursive parsing of `include<>` / `use<>` referenced files.
