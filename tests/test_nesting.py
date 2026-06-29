import os
import pytest
import tempfile
import shutil

from nesting import extract_panel_dimensions

@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    if os.path.exists(d):
        shutil.rmtree(d)

@pytest.fixture
def sample_nesting_scad(temp_dir):
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
    scad_path = os.path.join(temp_dir, "nesting_model.scad")
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

def test_extract_panel_dimensions_no_parts(temp_dir):
    scad_content = """
    cube([10, 10, 10]);
    """
    scad_path = os.path.join(temp_dir, "no_parts.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)
    try:
        dims = extract_panel_dimensions(scad_path)
        assert len(dims) == 0
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")
