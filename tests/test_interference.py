import os
import pytest
import tempfile
import shutil

from interference import (
    generate_intersection_scad,
    check_pair,
    run_pairwise_check
)



def test_imports():
    assert generate_intersection_scad is not None
    assert check_pair is not None
    assert run_pairwise_check is not None

def test_generate_intersection_scad():
    scad_code = generate_intersection_scad("temp_a.stl", "temp_b.stl")
    # Verify wrapper code structure
    assert 'intersection()' in scad_code
    assert 'import(' in scad_code
    assert 'temp_a.stl' in scad_code
    assert 'temp_b.stl' in scad_code

def test_check_pair_overlapping(overlapping_scad_file):
    # cube_a (10x10x10) and cube_b (10x10x10 at [5,0,0]) overlap by 5x10x10 = 500 mm3
    try:
        res = check_pair(overlapping_scad_file, "cube_a", "cube_b")
        assert res is not None
        assert res["part_a"] == "cube_a"
        assert res["part_b"] == "cube_b"
        assert abs(res["intersection_volume_mm3"] - 500.0) < 1.0
        
        bbox = res["bounding_box"]
        assert abs(bbox["x_min"] - 5.0) < 0.1
        assert abs(bbox["x_max"] - 10.0) < 0.1
        assert abs(bbox["y_min"] - 0.0) < 0.1
        assert abs(bbox["y_max"] - 10.0) < 0.1
        assert abs(bbox["z_min"] - 0.0) < 0.1
        assert abs(bbox["z_max"] - 10.0) < 0.1
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found")

def test_check_pair_non_overlapping(overlapping_scad_file):
    # cube_a and cube_c (at [20,20,20]) do not overlap
    try:
        res = check_pair(overlapping_scad_file, "cube_a", "cube_c")
        assert res is None
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found")

def test_run_pairwise_check_all(overlapping_scad_file):
    # cube_a vs cube_b (collides)
    # cube_a vs cube_c (clean)
    # cube_b vs cube_c (clean)
    try:
        parts = ["cube_a", "cube_b", "cube_c"]
        collisions = run_pairwise_check(overlapping_scad_file, parts, fail_fast=False)
        assert len(collisions) == 1
        assert collisions[0]["part_a"] == "cube_a"
        assert collisions[0]["part_b"] == "cube_b"
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found")

def test_run_pairwise_check_fail_fast(overlapping_scad_file):
    # We should stop at first collision
    try:
        parts = ["cube_a", "cube_b", "cube_c"]
        collisions = run_pairwise_check(overlapping_scad_file, parts, fail_fast=True)
        assert len(collisions) == 1
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found")

def test_missing_file():
    with pytest.raises(FileNotFoundError):
        check_pair("nonexistent.scad", "cube_a", "cube_b")

def test_generate_highlight_scad(local_tmp_path):
    from interference import generate_highlight_scad
    # Mock collision dict
    collisions = [
        {
            "part_a": "cube_a",
            "part_b": "cube_b",
            "intersection_volume_mm3": 500.0,
            "bounding_box": {}
        }
    ]
    scad_code = generate_highlight_scad("model.scad", collisions, local_tmp_path)
    assert "color(" in scad_code
    assert "import(" in scad_code
    assert "cube_a_cube_b_intersection.stl" in scad_code

def test_render_collision_highlight(overlapping_scad_file, local_tmp_path):
    from interference import render_collision_highlight, run_pairwise_check
    parts = ["cube_a", "cube_b", "cube_c"]
    collisions = run_pairwise_check(overlapping_scad_file, parts)
    
    output_png = os.path.join(local_tmp_path, "highlight.png")
    try:
        img_b64 = render_collision_highlight(overlapping_scad_file, collisions, output_png, img_size=200)
        assert img_b64 is not None
        assert len(img_b64) > 0
        assert os.path.exists(output_png)
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found")

