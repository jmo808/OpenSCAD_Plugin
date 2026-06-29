# Implementation Plan: BOM Extraction & Hardware Shopping List Tool

## Phase 1: BOM Annotation Parser

- [x] [e43c0a7] Task: Write tests for inline comment BOM parser
    - [x] Create test SCAD fixture with multiple `// BOM:` annotations (varying fields, categories)
    - [x] Write test: parses a single inline `// BOM:` annotation with all fields
    - [x] Write test: parses annotations with only required fields (name, qty, category)
    - [x] Write test: parses annotations with optional supplier and part_number fields
    - [x] Write test: captures correct `source_line` number for each annotation
    - [x] Write test: warns on malformed annotation (missing `name`) without crashing
    - [x] Write test: returns empty list for SCAD file with no BOM annotations
    - [x] Run tests and confirm they all fail (Red phase)

- [x] [1c2c92f] Task: Implement inline comment BOM parser
    - [x] Create `bom_parser.py` module
    - [x] Implement `parse_inline_bom(scad_path: str) -> list[dict]` using regex to match `// BOM:` lines
    - [x] Parse comma-separated key=value pairs after the `// BOM:` prefix
    - [x] Handle required vs optional fields with validation
    - [x] Collect warnings for malformed lines (store line number + raw text)
    - [x] Run tests and confirm they all pass (Green phase)
    - [x] Commit: `feat(bom): Implement inline comment BOM annotation parser`

- [x] [326a288] Task: Write tests for module-level metadata block parser
    - [x] Create test SCAD fixture with `/* BOM: ... */` blocks above module definitions
    - [x] Write test: parses a single multi-line BOM metadata block
    - [x] Write test: parses multiple BOM blocks in the same file
    - [x] Write test: correctly handles mixed inline and block annotations in one file
    - [x] Write test: captures correct `source_line` for block annotations
    - [x] Run tests and confirm they all fail (Red phase)

- [~] Task: Implement module-level metadata block parser
    - [ ] Add `parse_block_bom(scad_path: str) -> list[dict]` to `bom_parser.py`
    - [ ] Use regex to match `/* BOM:` ... `*/` blocks with YAML-like `key: value` lines
    - [ ] Implement unified `parse_bom_annotations(scad_path: str) -> tuple[list[dict], list[str]]` that combines both parsers and returns (entries, warnings)
    - [ ] Run tests and confirm they all pass (Green phase)
    - [ ] Commit: `feat(bom): Implement module-level metadata block parser`

- [ ] Task: Conductor - User Manual Verification 'Phase 1: BOM Annotation Parser' (Protocol in workflow.md)

## Phase 2: Aggregation & Grouping Engine

- [ ] Task: Write tests for BOM aggregation and grouping
    - [ ] Write test: aggregates identical items (same name + category) and sums quantities
    - [ ] Write test: case-insensitive name matching ("M3x12 Screw" == "m3x12 screw")
    - [ ] Write test: groups entries by category
    - [ ] Write test: sorts entries alphabetically by name within each category
    - [ ] Write test: preserves supplier and part_number from first occurrence
    - [ ] Write test: computes correct `total_unique_items` and `total_quantity`
    - [ ] Run tests and confirm they all fail (Red phase)

- [ ] Task: Implement BOM aggregation engine
    - [ ] Add `aggregate_bom(entries: list[dict]) -> dict` to `bom_parser.py`
    - [ ] Implement case-insensitive grouping key: `(name.lower(), category.lower())`
    - [ ] Sum `qty` across duplicates, keep first `supplier` and `part_number`
    - [ ] Return dict with `categories` (grouped/sorted entries) and `summary` (totals)
    - [ ] Run tests and confirm they all pass (Green phase)
    - [ ] Commit: `feat(bom): Implement aggregation and category grouping engine`

- [ ] Task: Conductor - User Manual Verification 'Phase 2: Aggregation & Grouping Engine' (Protocol in workflow.md)

## Phase 3: Multi-Format Export

- [ ] Task: Write tests for JSON, Markdown, and CSV export
    - [ ] Write test: JSON output is valid and contains all required fields
    - [ ] Write test: JSON includes `total_unique_items` and `total_quantity` summary
    - [ ] Write test: Markdown output has correct table headers and category group headings
    - [ ] Write test: CSV output is parseable with Python `csv.reader` and has correct headers
    - [ ] Write test: all three files are written to the specified `output_dir`
    - [ ] Write test: only requested formats are exported when `formats` parameter is specified
    - [ ] Run tests and confirm they all fail (Red phase)

- [ ] Task: Implement multi-format BOM export
    - [ ] Add `export_bom_json(aggregated: dict, output_path: str)` function
    - [ ] Add `export_bom_markdown(aggregated: dict, output_path: str)` function with category headers and table formatting
    - [ ] Add `export_bom_csv(aggregated: dict, output_path: str)` function using `csv.writer`
    - [ ] Run tests and confirm they all pass (Green phase)
    - [ ] Commit: `feat(bom): Implement JSON, Markdown, and CSV export formats`

- [ ] Task: Conductor - User Manual Verification 'Phase 3: Multi-Format Export' (Protocol in workflow.md)

## Phase 4: MCP Tool Integration & Documentation

- [ ] Task: Write tests for `extract_bom` MCP tool
    - [ ] Write test: tool is registered and appears in MCP schema
    - [ ] Write test: returns structured JSON with aggregated BOM for annotated fixture
    - [ ] Write test: returns human-readable summary with file paths
    - [ ] Write test: returns "no annotations found" message for clean SCAD file
    - [ ] Write test: includes warnings for malformed annotations in response
    - [ ] Run tests and confirm they all fail (Red phase)

- [ ] Task: Implement `extract_bom` MCP tool
    - [ ] Add `@mcp.tool()` decorated `extract_bom` function to `server.py`
    - [ ] Wire up annotation parsing, aggregation, and multi-format export
    - [ ] Build conversational human-readable summary text
    - [ ] Include absolute file paths for all generated files
    - [ ] Include warnings for malformed annotations
    - [ ] Run tests and confirm they all pass (Green phase)
    - [ ] Commit: `feat(server): Implement extract_bom MCP tool`

- [ ] Task: Update documentation and installer
    - [ ] Update `instructions.md` with `extract_bom` tool documentation and annotation format guide
    - [ ] Update `skills/openscad-mcp/SKILL.md` to include new tool description
    - [ ] Run `install.py` to verify schema exports correctly
    - [ ] Commit: `docs(plugin): Add extract_bom to instructions and skill`

- [ ] Task: Final coverage verification
    - [ ] Run `pytest --cov=. --cov-report=term` and verify >80% coverage
    - [ ] Fix any coverage gaps with targeted tests
    - [ ] Run full test suite one final time
    - [ ] Commit: `test(coverage): Ensure >80% coverage for BOM module`

- [ ] Task: Conductor - User Manual Verification 'Phase 4: MCP Tool Integration & Documentation' (Protocol in workflow.md)
