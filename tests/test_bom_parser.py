import os
import pytest
import tempfile
import shutil

# In TDD, these functions do not exist yet in bom_parser
from bom_parser import parse_inline_bom

@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    if os.path.exists(d):
        shutil.rmtree(d)

def test_parse_inline_bom_all_fields(temp_dir):
    scad_content = """
    // BOM: M2.5 brass heat-set insert, qty=8, category=fastener, supplier=McMaster, part_number=94180A321
    module test() {}
    """
    scad_path = os.path.join(temp_dir, "model.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)

    entries, warnings = parse_inline_bom(scad_path)
    assert len(entries) == 1
    assert len(warnings) == 0

    entry = entries[0]
    assert entry["name"] == "M2.5 brass heat-set insert"
    assert entry["qty"] == 8
    assert entry["category"] == "fastener"
    assert entry["supplier"] == "McMaster"
    assert entry["part_number"] == "94180A321"
    # Line numbers in python are 1-indexed. The comment is on line 2 (first is empty line).
    assert entry["source_line"] == 2

def test_parse_inline_bom_required_only(temp_dir):
    scad_content = """// BOM: M3 hex nut, qty=4, category=fastener"""
    scad_path = os.path.join(temp_dir, "model.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)

    entries, warnings = parse_inline_bom(scad_path)
    assert len(entries) == 1
    assert len(warnings) == 0

    entry = entries[0]
    assert entry["name"] == "M3 hex nut"
    assert entry["qty"] == 4
    assert entry["category"] == "fastener"
    assert "supplier" not in entry or entry["supplier"] is None
    assert "part_number" not in entry or entry["part_number"] is None
    assert entry["source_line"] == 1

def test_parse_inline_bom_malformed(temp_dir):
    # Missing name, but has qty and category
    # Or missing qty
    scad_content = """
    // BOM: qty=4, category=fastener
    // BOM: M3 hex nut, category=fastener
    // BOM: M3 hex nut, qty=four, category=fastener
    """
    scad_path = os.path.join(temp_dir, "model.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)

    entries, warnings = parse_inline_bom(scad_path)
    assert len(entries) == 0
    assert len(warnings) == 3
    assert "line 2" in warnings[0].lower()
    assert "line 3" in warnings[1].lower()
    assert "line 4" in warnings[2].lower()

def test_parse_inline_bom_empty(temp_dir):
    scad_content = """
    module test() {
        cube([10, 10, 10]);
    }
    """
    scad_path = os.path.join(temp_dir, "model.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)

    entries, warnings = parse_inline_bom(scad_path)
    assert len(entries) == 0
    assert len(warnings) == 0

# Import block parser functions for testing
from bom_parser import parse_block_bom, parse_bom_annotations

def test_parse_block_bom_all_fields(temp_dir):
    scad_content = """
    /* BOM:
     *   name: M3 hex nut
     *   qty: 4
     *   category: fastener
     *   supplier: McMaster
     *   part_number: 90590A005
     */
    module bracket_hardware() { }
    """
    scad_path = os.path.join(temp_dir, "model.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)

    entries, warnings = parse_block_bom(scad_path)
    assert len(entries) == 1
    assert len(warnings) == 0

    entry = entries[0]
    assert entry["name"] == "M3 hex nut"
    assert entry["qty"] == 4
    assert entry["category"] == "fastener"
    assert entry["supplier"] == "McMaster"
    assert entry["part_number"] == "90590A005"
    # Block starts on line 2 (/* BOM:)
    assert entry["source_line"] == 2

def test_parse_block_bom_required_only(temp_dir):
    scad_content = """
    /* BOM:
       name: M3 hex nut
       qty: 4
       category: fastener
    */
    """
    scad_path = os.path.join(temp_dir, "model.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)

    entries, warnings = parse_block_bom(scad_path)
    assert len(entries) == 1
    assert len(warnings) == 0

    entry = entries[0]
    assert entry["name"] == "M3 hex nut"
    assert entry["qty"] == 4
    assert entry["category"] == "fastener"
    assert "supplier" not in entry or entry["supplier"] is None
    assert "part_number" not in entry or entry["part_number"] is None

def test_parse_block_bom_malformed(temp_dir):
    scad_content = """
    /* BOM:
       qty: 4
       category: fastener
    */
    /* BOM:
       name: M3 hex nut
       qty: four
       category: fastener
    */
    """
    scad_path = os.path.join(temp_dir, "model.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)

    entries, warnings = parse_block_bom(scad_path)
    assert len(entries) == 0
    assert len(warnings) == 2
    assert "line 2" in warnings[0].lower()
    assert "line 6" in warnings[1].lower()

def test_parse_bom_annotations_mixed(temp_dir):
    scad_content = """
    // BOM: M2.5 screw, qty=8, category=fastener
    
    /* BOM:
     *   name: M3 hex nut
     *   qty: 4
     *   category: fastener
     */
    module bracket_hardware() { }
    
    // BOM: Malformed annotation without category, qty=2
    """
    scad_path = os.path.join(temp_dir, "model.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)

    entries, warnings = parse_bom_annotations(scad_path)
    assert len(entries) == 2
    assert len(warnings) == 1
    assert entries[0]["name"] == "M2.5 screw"
    assert entries[1]["name"] == "M3 hex nut"
    assert "line 11" in warnings[0].lower()

# Import aggregation function for testing
from bom_parser import aggregate_bom

def test_aggregate_bom():
    entries = [
        {"name": "M3x12 Screw", "qty": 4, "category": "fastener", "supplier": "McMaster", "part_number": "91292A111", "source_line": 1},
        {"name": "m3x12 screw", "qty": 2, "category": "Fastener", "supplier": "McMaster", "part_number": "91292A111", "source_line": 2},
        {"name": "M3 Nut", "qty": 6, "category": "fastener", "source_line": 3},
        {"name": "M3x12 Screw", "qty": 1, "category": "fastener", "source_line": 4},
        {"name": "5mm LED", "qty": 2, "category": "electronic", "supplier": "Adafruit", "part_number": "307", "source_line": 5}
    ]
    
    res = aggregate_bom(entries)
    
    # Check structure
    assert "categories" in res
    assert "summary" in res
    
    # Check categories grouping (normalized to lowercase or original lowercase group)
    # We expect 'fastener' and 'electronic' keys
    cats = res["categories"]
    assert len(cats) == 2
    assert "fastener" in cats
    assert "electronic" in cats
    
    # Check sorting within fastener category: "M3 Nut" then "M3x12 Screw" (sorted alphabetically by name)
    fasteners = cats["fastener"]
    assert len(fasteners) == 2
    assert fasteners[0]["name"] == "M3 Nut"
    assert fasteners[0]["qty"] == 6
    
    # Check aggregation and sum for M3x12 Screw (4 + 2 + 1 = 7)
    assert fasteners[1]["name"] == "M3x12 Screw"  # preserves casing of first or just uses it
    assert fasteners[1]["qty"] == 7
    # Preserves supplier and part_number from first occurrence
    assert fasteners[1]["supplier"] == "McMaster"
    assert fasteners[1]["part_number"] == "91292A111"
    
    # Check electronic category
    electronics = cats["electronic"]
    assert len(electronics) == 1
    assert electronics[0]["name"] == "5mm LED"
    assert electronics[0]["qty"] == 2
    
    # Check summary
    summary = res["summary"]
    assert summary["total_unique_items"] == 3
    assert summary["total_quantity"] == 15

# Import exporters for testing
import json
import csv
from bom_parser import (
    export_bom_json,
    export_bom_markdown,
    export_bom_csv,
    export_bom
)

def test_exporters(temp_dir):
    aggregated = {
        "categories": {
            "fastener": [
                {"name": "M3 Nut", "qty": 6, "category": "fastener"},
                {"name": "M3x12 Screw", "qty": 7, "category": "fastener", "supplier": "McMaster", "part_number": "91292A111"}
            ],
            "electronic": [
                {"name": "5mm LED", "qty": 2, "category": "electronic", "supplier": "Adafruit", "part_number": "307"}
            ]
        },
        "summary": {
            "total_unique_items": 3,
            "total_quantity": 15
        }
    }
    
    json_path = os.path.join(temp_dir, "bom.json")
    md_path = os.path.join(temp_dir, "bom.md")
    csv_path = os.path.join(temp_dir, "bom.csv")
    
    # 1. Test JSON export
    export_bom_json(aggregated, json_path)
    assert os.path.exists(json_path)
    with open(json_path, "r") as f:
        data = json.load(f)
    assert data["summary"]["total_unique_items"] == 3
    assert data["categories"]["fastener"][1]["name"] == "M3x12 Screw"
    
    # 2. Test MD export
    export_bom_markdown(aggregated, md_path)
    assert os.path.exists(md_path)
    with open(md_path, "r") as f:
        md_content = f.read()
    assert "# Bill of Materials" in md_content
    assert "## fastener" in md_content or "## Fastener" in md_content
    assert "| M3 Nut | 6 |" in md_content or "| M3 Nut | 6" in md_content
    assert "| M3x12 Screw | 7 | McMaster | 91292A111 |" in md_content or "91292A111" in md_content
    
    # 3. Test CSV export
    export_bom_csv(aggregated, csv_path)
    assert os.path.exists(csv_path)
    with open(csv_path, "r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    # Headers: category,name,qty,supplier,part_number
    assert rows[0] == ["category", "name", "qty", "supplier", "part_number"]
    assert rows[1] == ["electronic", "5mm LED", "2", "Adafruit", "307"]
    assert rows[2] == ["fastener", "M3 Nut", "6", "", ""]
    assert rows[3] == ["fastener", "M3x12 Screw", "7", "McMaster", "91292A111"]

def test_unified_export(temp_dir):
    aggregated = {
        "categories": {
            "fastener": [
                {"name": "M3 Nut", "qty": 6, "category": "fastener"}
            ]
        },
        "summary": {
            "total_unique_items": 1,
            "total_quantity": 6
        }
    }
    
    out_dir = os.path.join(temp_dir, "nested_dir")
    
    # Test all formats
    paths = export_bom(aggregated, out_dir, formats=["json", "md", "csv"])
    assert set(paths.keys()) == {"json", "md", "csv"}
    assert os.path.exists(os.path.join(out_dir, "bom.json"))
    assert os.path.exists(os.path.join(out_dir, "bom.md"))
    assert os.path.exists(os.path.join(out_dir, "bom.csv"))
    
    # Test subset of formats
    shutil.rmtree(out_dir)
    paths = export_bom(aggregated, out_dir, formats=["json"])
    assert set(paths.keys()) == {"json"}
    assert os.path.exists(os.path.join(out_dir, "bom.json"))
    assert not os.path.exists(os.path.join(out_dir, "bom.md"))



