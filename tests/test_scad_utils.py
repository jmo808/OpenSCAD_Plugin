import os
import pytest
import tempfile
import shutil

from scad_utils import discover_parts

@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    if os.path.exists(d):
        shutil.rmtree(d)

def test_imports():
    assert discover_parts is not None

def test_discover_parts_multipart(temp_dir):
    scad_content = """
    part = "all";
    
    if (part == "side_panel") {
        cube([10, 20, 30]);
    } else if (part == "back_panel") {
        cylinder(r=5, h=20);
    } else if (part=='cleat_left') {
        sphere(r=10);
    }
    """
    scad_path = os.path.join(temp_dir, "model.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)
        
    parts = discover_parts(scad_path)
    assert set(parts) == {"side_panel", "back_panel", "cleat_left"}

def test_discover_parts_none(temp_dir):
    scad_content = """
    cube([10, 20, 30]);
    """
    scad_path = os.path.join(temp_dir, "model.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)
        
    parts = discover_parts(scad_path)
    assert parts == []

def test_discover_parts_duplicates(temp_dir):
    scad_content = """
    if (part == "side_panel") {
        cube([10, 20, 30]);
    }
    
    // Duplicate selector in comments or code
    if (part == "side_panel") {
        sphere(r=5);
    }
    """
    scad_path = os.path.join(temp_dir, "model.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)
        
    parts = discover_parts(scad_path)
    assert parts == ["side_panel"]
