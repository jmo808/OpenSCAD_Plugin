import os
import pytest
import tempfile
import shutil

from nesting import extract_panel_dimensions

@pytest.fixture
def sample_nesting_scad(local_tmp_path):
    scad_content = """
    part = "all";
    
    module part_a() { square([10, 20]); }
    module part_b() { square([30, 40]); }
    module part_c() { square([50, 60]); }
    
    if (part == "part_a") {
        part_a();
    } else if (part == "part_b") {
        part_b();
    } else if (part == "part_c") {
        part_c();
    }
    """
    scad_path = os.path.join(local_tmp_path, "nesting_model.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)
    return scad_path

def test_extract_panel_dimensions_all(sample_nesting_scad):
    try:
        dims = extract_panel_dimensions(sample_nesting_scad)
        assert len(dims) == 3
        # Check part_a
        part_a = next(d for d in dims if d["part_name"] == "part_a")
        assert part_a["width_mm"] == 10.0
        assert part_a["height_mm"] == 20.0
        
        # Check part_b
        part_b = next(d for d in dims if d["part_name"] == "part_b")
        assert part_b["width_mm"] == 30.0
        assert part_b["height_mm"] == 40.0
        
        # Check part_c
        part_c = next(d for d in dims if d["part_name"] == "part_c")
        assert part_c["width_mm"] == 50.0
        assert part_c["height_mm"] == 60.0
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")

def test_extract_panel_dimensions_filtered(sample_nesting_scad):
    try:
        dims = extract_panel_dimensions(sample_nesting_scad, parts=["part_a", "part_c"])
        assert len(dims) == 2
        part_names = {d["part_name"] for d in dims}
        assert part_names == {"part_a", "part_c"}
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")

def test_extract_panel_dimensions_missing_file():
    with pytest.raises(FileNotFoundError):
        extract_panel_dimensions("non_existent_file.scad")

def test_extract_panel_dimensions_no_parts(local_tmp_path):
    scad_content = """
    cube([10, 10, 10]);
    """
    scad_path = os.path.join(local_tmp_path, "no_parts.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)
    try:
        dims = extract_panel_dimensions(scad_path)
        assert len(dims) == 0
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")

from nesting import pack_shelf

def test_pack_shelf_basic():
    # 3 panels: 100x200, 150x200, 200x200
    panels = [
        {"part_name": "p1", "width_mm": 100.0, "height_mm": 200.0},
        {"part_name": "p2", "width_mm": 150.0, "height_mm": 200.0},
        {"part_name": "p3", "width_mm": 200.0, "height_mm": 200.0}
    ]
    # Sheet: 500 x 500. Kerf: 10.0
    sheets = pack_shelf(panels, sheet_w=500.0, sheet_h=500.0, kerf=10.0)
    
    assert len(sheets) == 1
    sheet = sheets[0]
    assert sheet["sheet_number"] == 1
    assert len(sheet["panels"]) == 3
    
    # Check positions:
    # Margin: 10.0
    # p1 at (10, 10), width=100, height=200
    # p2 at (10 + 100 + 10 = 120, 10), width=150, height=200
    # p3 at (120 + 150 + 10 = 280, 10), width=200, height=200
    p1 = next(p for p in sheet["panels"] if p["part_name"] == "p1")
    assert p1["x"] == 10.0
    assert p1["y"] == 10.0
    
    p2 = next(p for p in sheet["panels"] if p["part_name"] == "p2")
    assert p2["x"] == 120.0
    assert p2["y"] == 10.0
    
    p3 = next(p for p in sheet["panels"] if p["part_name"] == "p3")
    assert p3["x"] == 280.0
    assert p3["y"] == 10.0
    
    # Check utilization: Total area of panels = 100*200 + 150*200 + 200*200 = 20000 + 30000 + 40000 = 90000
    # Sheet area = 500 * 500 = 250000
    # Util = 90000 / 250000 = 36%
    assert sheet["utilization_percent"] == 36.0
    assert sheet["waste_area_mm2"] == 160000.0

def test_pack_shelf_new_shelf():
    # 3 panels: 200x100, 200x150, 200x200
    # Sheet: 500 x 500. Kerf: 10.0
    panels = [
        {"part_name": "p1", "width_mm": 200.0, "height_mm": 100.0},
        {"part_name": "p2", "width_mm": 200.0, "height_mm": 150.0},
        {"part_name": "p3", "width_mm": 200.0, "height_mm": 200.0}
    ]
    sheets = pack_shelf(panels, sheet_w=500.0, sheet_h=500.0, kerf=10.0)
    
    assert len(sheets) == 1
    sheet = sheets[0]
    assert len(sheet["panels"]) == 3
    
    # p1 at (10, 10), next x is 220.
    # p2 at (220, 10), next x is 430.
    # p3 would need 430 + 200 + 10 = 640 > 500, so p3 starts a new shelf!
    # Shelf 1 height = max(100, 150) = 150.
    # Shelf 2 y = 10 + 150 + 10 = 170.
    # p3 at (10, 170)
    p3 = next(p for p in sheet["panels"] if p["part_name"] == "p3")
    assert p3["x"] == 10.0
    assert p3["y"] == 170.0

def test_pack_shelf_multiple_sheets():
    # Sheet: 300 x 300. Kerf: 10.0. Max width/height available for part: 280
    panels = [
        {"part_name": "p1", "width_mm": 200.0, "height_mm": 200.0},
        {"part_name": "p2", "width_mm": 200.0, "height_mm": 200.0}
    ]
    sheets = pack_shelf(panels, sheet_w=300.0, sheet_h=300.0, kerf=10.0)
    
    assert len(sheets) == 2
    assert sheets[0]["sheet_number"] == 1
    assert sheets[1]["sheet_number"] == 2
    assert len(sheets[0]["panels"]) == 1
    assert len(sheets[1]["panels"]) == 1
