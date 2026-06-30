import os
import pytest
from splitting import get_part_bbox, calculate_split_planes, validate_manual_split

@pytest.fixture
def oversized_scad_file(local_tmp_path):
    content = """
    part = "all";
    module oversized_box() {
        cube([300, 150, 400]);
    }
    
    module normal_box() {
        cube([100, 100, 100]);
    }
    
    if (part == "oversized_box") {
        oversized_box();
    } else if (part == "normal_box") {
        normal_box();
    } else {
        oversized_box();
    }
    """
    scad_path = os.path.join(local_tmp_path, "oversized.scad")
    with open(scad_path, "w") as f:
        f.write(content)
    return scad_path

def test_get_part_bbox(oversized_scad_file):
    # Try to extract bounding box. It will fail during RED phase as get_part_bbox doesn't exist.
    bbox = get_part_bbox(oversized_scad_file, "oversized_box")
    assert bbox == {
        "x_min": 0.0, "x_max": 300.0,
        "y_min": 0.0, "y_max": 150.0,
        "z_min": 0.0, "z_max": 400.0
    }

def test_calculate_split_planes_auto_single_axis():
    # Z as oversize axis for a 100x100x400 part on 220x220x250 bed with 5mm margin.
    # Bed size: 220x220x250. Safety margin on each side (meaning effective bed size is 210x210x240).
    bbox = {
        "x_min": 0.0, "x_max": 100.0,
        "y_min": 0.0, "y_max": 100.0,
        "z_min": 0.0, "z_max": 400.0
    }
    splits = calculate_split_planes(bbox, bed_x=220, bed_y=220, bed_z=250, margin=5)
    assert len(splits) == 1
    assert splits[0]["axis"] == "z"
    assert abs(splits[0]["coordinate"] - 200.0) < 1e-2

def test_calculate_split_planes_auto_multiple_segments():
    # Part is 600mm tall in Z. Effective bed_z = 240.
    # Splits should be at evenly-spaced intervals: 200.0, 400.0.
    bbox = {
        "x_min": 0.0, "x_max": 100.0,
        "y_min": 0.0, "y_max": 100.0,
        "z_min": 0.0, "z_max": 600.0
    }
    splits = calculate_split_planes(bbox, bed_x=220, bed_y=220, bed_z=250, margin=5)
    assert len(splits) == 2
    assert splits[0]["axis"] == "z"
    assert splits[1]["axis"] == "z"
    coords = sorted([s["coordinate"] for s in splits])
    assert abs(coords[0] - 200.0) < 1e-2
    assert abs(coords[1] - 400.0) < 1e-2

def test_calculate_split_planes_auto_multiple_axes():
    # Part is 300x300x100. Effective bed: 210x210x240.
    # Oversize axes: X (300 > 210), Y (300 > 210).
    bbox = {
        "x_min": 0.0, "x_max": 300.0,
        "y_min": 0.0, "y_max": 300.0,
        "z_min": 0.0, "z_max": 100.0
    }
    splits = calculate_split_planes(bbox, bed_x=220, bed_y=220, bed_z=250, margin=5)
    assert len(splits) == 2
    axes = {s["axis"] for s in splits}
    assert axes == {"x", "y"}
    
    x_split = next(s for s in splits if s["axis"] == "x")
    y_split = next(s for s in splits if s["axis"] == "y")
    assert abs(x_split["coordinate"] - 150.0) < 1e-2
    assert abs(y_split["coordinate"] - 150.0) < 1e-2

def test_validate_manual_split():
    bbox = {
        "x_min": 0.0, "x_max": 300.0,
        "y_min": 0.0, "y_max": 150.0,
        "z_min": 0.0, "z_max": 400.0
    }
    # Valid split
    split = validate_manual_split(bbox, axis="z", coord=150.0)
    assert split["axis"] == "z"
    assert split["coordinate"] == 150.0

    # Invalid axis
    with pytest.raises(ValueError):
        validate_manual_split(bbox, axis="w", coord=150.0)
        
    # Coordinate out of bounds
    with pytest.raises(ValueError):
        validate_manual_split(bbox, axis="z", coord=450.0)
    with pytest.raises(ValueError):
        validate_manual_split(bbox, axis="z", coord=-50.0)

def test_raises_error_if_fits():
    # Part fits within bed
    bbox = {
        "x_min": 0.0, "x_max": 100.0,
        "y_min": 0.0, "y_max": 100.0,
        "z_min": 0.0, "z_max": 100.0
    }
    with pytest.raises(ValueError, match="Part already fits within printer bed"):
        calculate_split_planes(bbox, bed_x=220, bed_y=220, bed_z=250, margin=5)
