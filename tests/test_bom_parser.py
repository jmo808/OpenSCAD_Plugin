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
