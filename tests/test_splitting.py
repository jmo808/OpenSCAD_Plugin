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

def test_dovetail_scad_generation():
    from splitting import generate_dovetail_scad
    params = {
        "finger_count": 2,
        "finger_width": 10.0,
        "finger_depth": 5.0,
        "taper_angle": 20.0,
        "clearance": 0.2
    }
    male_scad, female_scad = generate_dovetail_scad(face_width=50.0, face_height=10.0, params=params)
    assert isinstance(male_scad, str) and len(male_scad) > 0
    assert isinstance(female_scad, str) and len(female_scad) > 0
    
    # Test with params=None to ensure default params are used
    male_scad_def, female_scad_def = generate_dovetail_scad(face_width=50.0, face_height=10.0)
    assert isinstance(male_scad_def, str) and len(male_scad_def) > 0
    assert isinstance(female_scad_def, str) and len(female_scad_def) > 0

def test_dovetail_interlock_and_clearance(local_tmp_path):
    from splitting import generate_dovetail_scad
    from stl_utils import compute_stl_volume
    from scad_utils import run_openscad
    
    # 1. Test interlock (intersection volume > 0 when mated)
    params_no_clearance = {
        "finger_count": 2,
        "finger_width": 10.0,
        "finger_depth": 5.0,
        "taper_angle": 20.0,
        "clearance": 0.0
    }
    male_scad, female_scad = generate_dovetail_scad(
        face_width=50.0, face_height=10.0, params=params_no_clearance
    )
    
    # Write a SCAD file to compute intersection
    scad_content = f"""
    module male() {{
        {male_scad}
    }}
    module female() {{
        {female_scad}
    }}
    intersection() {{
        male();
        female();
    }}
    """
    scad_path = os.path.join(local_tmp_path, "dovetail_test.scad")
    stl_path = os.path.join(local_tmp_path, "dovetail_test.stl")
    with open(scad_path, "w") as f:
        f.write(scad_content)
        
    try:
        run_openscad(["-o", stl_path, scad_path])
        vol = compute_stl_volume(stl_path)
        assert vol > 0.0
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not available")

def test_dovetail_clearance_difference(local_tmp_path):
    from splitting import generate_dovetail_scad
    from stl_utils import compute_stl_volume
    from scad_utils import run_openscad
    
    # Compare volume of female pocket with and without clearance
    params_no_clearance = {
        "finger_count": 2,
        "finger_width": 10.0,
        "finger_depth": 5.0,
        "taper_angle": 20.0,
        "clearance": 0.0
    }
    params_clearance = {
        "finger_count": 2,
        "finger_width": 10.0,
        "finger_depth": 5.0,
        "taper_angle": 20.0,
        "clearance": 0.2
    }
    
    _, female_no_clearance = generate_dovetail_scad(
        face_width=50.0, face_height=10.0, params=params_no_clearance
    )
    _, female_clearance = generate_dovetail_scad(
        face_width=50.0, face_height=10.0, params=params_clearance
    )
    
    scad_content = f"""
    module pocket_no_clearance() {{
        {female_no_clearance}
    }}
    module pocket_clearance() {{
        {female_clearance}
    }}
    // Render them separately using part selection
    part = "clearance";
    if (part == "no_clearance") {{
        pocket_no_clearance();
    }} else {{
        pocket_clearance();
    }}
    """
    scad_path = os.path.join(local_tmp_path, "clearance_test.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)
        
    stl_no_clearance = os.path.join(local_tmp_path, "no_clearance.stl")
    stl_clearance = os.path.join(local_tmp_path, "clearance.stl")
    
    try:
        run_openscad(["-D", "part=\"no_clearance\"", "-o", stl_no_clearance, scad_path])
        run_openscad(["-D", "part=\"clearance\"", "-o", stl_clearance, scad_path])
        
        vol_no_clearance = compute_stl_volume(stl_no_clearance)
        vol_clearance = compute_stl_volume(stl_clearance)
        
        # Female pocket with clearance should be larger (wider slots)
        assert vol_clearance > vol_no_clearance
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not available")

def test_flange_scad_generation():
    from splitting import generate_flange_scad
    params = {
        "flange_width": 20.0,
        "flange_thickness": 5.0,
        "screw_size": "M3",
        "screw_count": 2,
        "clearance": 0.2
    }
    male_scad, female_scad = generate_flange_scad(face_width=50.0, face_height=10.0, params=params)
    assert isinstance(male_scad, str) and len(male_scad) > 0
    assert isinstance(female_scad, str) and len(female_scad) > 0
    
    # Test with params=None to ensure defaults are used
    male_def, female_def = generate_flange_scad(face_width=50.0, face_height=10.0)
    assert isinstance(male_def, str) and len(male_def) > 0
    assert isinstance(female_def, str) and len(female_def) > 0

def test_flange_screw_configurability():
    from splitting import generate_flange_scad
    params_m2 = {
        "flange_width": 15.0,
        "flange_thickness": 4.0,
        "screw_size": "M2",
        "screw_count": 3,
        "clearance": 0.1
    }
    params_m4 = {
        "flange_width": 15.0,
        "flange_thickness": 4.0,
        "screw_size": "M4",
        "screw_count": 3,
        "clearance": 0.1
    }
    male_m2, female_m2 = generate_flange_scad(60.0, 12.0, params_m2)
    male_m4, female_m4 = generate_flange_scad(60.0, 12.0, params_m4)
    # The generated SCAD should be different for M2 vs M4 (e.g. cylinder radius)
    assert male_m2 != male_m4
    assert female_m2 != female_m4

def test_flange_clearance_holes(local_tmp_path):
    from splitting import generate_flange_scad
    from stl_utils import compute_stl_volume
    from scad_utils import run_openscad
    
    params_no_clearance = {
        "flange_width": 20.0,
        "flange_thickness": 5.0,
        "screw_size": "M3",
        "screw_count": 2,
        "clearance": 0.0
    }
    params_clearance = {
        "flange_width": 20.0,
        "flange_thickness": 5.0,
        "screw_size": "M3",
        "screw_count": 2,
        "clearance": 0.5
    }
    
    _, female_no_clearance = generate_flange_scad(50.0, 10.0, params_no_clearance)
    _, female_clearance = generate_flange_scad(50.0, 10.0, params_clearance)
    
    scad_content = f"""
    module pocket_no_clearance() {{
        {female_no_clearance}
    }}
    module pocket_clearance() {{
        {female_clearance}
    }}
    part = "clearance";
    if (part == "no_clearance") {{
        pocket_no_clearance();
    }} else {{
        pocket_clearance();
    }}
    """
    scad_path = os.path.join(local_tmp_path, "flange_clearance.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)
        
    stl_no_clearance = os.path.join(local_tmp_path, "no_clearance.stl")
    stl_clearance = os.path.join(local_tmp_path, "clearance.stl")
    
    try:
        run_openscad(["-D", "part=\"no_clearance\"", "-o", stl_no_clearance, scad_path])
        run_openscad(["-D", "part=\"clearance\"", "-o", stl_clearance, scad_path])
        
        vol_no_clearance = compute_stl_volume(stl_no_clearance)
        vol_clearance = compute_stl_volume(stl_clearance)
        
        # Pocket with clearance should be larger (wider holes/pockets)
        assert vol_clearance > vol_no_clearance
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not available")

def test_tongue_groove_scad_generation():
    from splitting import generate_tongue_groove_scad
    params = {
        "tongue_width": 5.0,
        "tongue_depth": 3.0,
        "clearance": 0.2
    }
    male_scad, female_scad = generate_tongue_groove_scad(face_width=50.0, face_height=10.0, params=params)
    assert isinstance(male_scad, str) and len(male_scad) > 0
    assert isinstance(female_scad, str) and len(female_scad) > 0
    
    # Test with params=None to ensure defaults are used
    male_def, female_def = generate_tongue_groove_scad(face_width=50.0, face_height=10.0)
    assert isinstance(male_def, str) and len(male_def) > 0
    assert isinstance(female_def, str) and len(female_def) > 0

def test_tongue_groove_clearance(local_tmp_path):
    from splitting import generate_tongue_groove_scad
    from stl_utils import compute_stl_volume
    from scad_utils import run_openscad
    
    params_no_clearance = {
        "tongue_width": 5.0,
        "tongue_depth": 3.0,
        "clearance": 0.0
    }
    params_clearance = {
        "tongue_width": 5.0,
        "tongue_depth": 3.0,
        "clearance": 0.4
    }
    
    _, female_no_clearance = generate_tongue_groove_scad(50.0, 10.0, params_no_clearance)
    _, female_clearance = generate_tongue_groove_scad(50.0, 10.0, params_clearance)
    
    scad_content = f"""
    module pocket_no_clearance() {{
        {female_no_clearance}
    }}
    module pocket_clearance() {{
        {female_clearance}
    }}
    part = "clearance";
    if (part == "no_clearance") {{
        pocket_no_clearance();
    }} else {{
        pocket_clearance();
    }}
    """
    scad_path = os.path.join(local_tmp_path, "tongue_clearance.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)
        
    stl_no_clearance = os.path.join(local_tmp_path, "no_clearance.stl")
    stl_clearance = os.path.join(local_tmp_path, "clearance.stl")
    
    try:
        run_openscad(["-D", "part=\"no_clearance\"", "-o", stl_no_clearance, scad_path])
        run_openscad(["-D", "part=\"clearance\"", "-o", stl_clearance, scad_path])
        
        vol_no_clearance = compute_stl_volume(stl_no_clearance)
        vol_clearance = compute_stl_volume(stl_clearance)
        
        # Female groove with clearance should be larger
        assert vol_clearance > vol_no_clearance
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not available")

def test_pin_scad_generation():
    from splitting import generate_pin_scad
    params = {
        "pin_diameter": 4.0,
        "pin_depth": 6.0,
        "pin_count": 3,
        "clearance": 0.2
    }
    male_scad, female_scad = generate_pin_scad(face_width=50.0, face_height=10.0, params=params)
    assert isinstance(male_scad, str) and len(male_scad) > 0
    assert isinstance(female_scad, str) and len(female_scad) > 0
    
    # Test with params=None to ensure defaults are used
    male_def, female_def = generate_pin_scad(face_width=50.0, face_height=10.0)
    assert isinstance(male_def, str) and len(male_def) > 0
    assert isinstance(female_def, str) and len(female_def) > 0

def test_pin_clearance(local_tmp_path):
    from splitting import generate_pin_scad
    from stl_utils import compute_stl_volume
    from scad_utils import run_openscad
    
    params_no_clearance = {
        "pin_diameter": 4.0,
        "pin_depth": 6.0,
        "pin_count": 2,
        "clearance": 0.0
    }
    params_clearance = {
        "pin_diameter": 4.0,
        "pin_depth": 6.0,
        "pin_count": 2,
        "clearance": 0.4
    }
    
    # In pin joint, both male and female are hole subtractions.
    # We will test female clearance
    _, female_no_clearance = generate_pin_scad(50.0, 10.0, params_no_clearance)
    _, female_clearance = generate_pin_scad(50.0, 10.0, params_clearance)
    
    scad_content = f"""
    module pocket_no_clearance() {{
        {female_no_clearance}
    }}
    module pocket_clearance() {{
        {female_clearance}
    }}
    part = "clearance";
    if (part == "no_clearance") {{
        pocket_no_clearance();
    }} else {{
        pocket_clearance();
    }}
    """
    scad_path = os.path.join(local_tmp_path, "pin_clearance.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)
        
    stl_no_clearance = os.path.join(local_tmp_path, "no_clearance.stl")
    stl_clearance = os.path.join(local_tmp_path, "clearance.stl")
    
    try:
        run_openscad(["-D", "part=\"no_clearance\"", "-o", stl_no_clearance, scad_path])
        run_openscad(["-D", "part=\"clearance\"", "-o", stl_clearance, scad_path])
        
        vol_no_clearance = compute_stl_volume(stl_no_clearance)
        vol_clearance = compute_stl_volume(stl_clearance)
        
        # Female pin holes with clearance should be larger
        assert vol_clearance > vol_no_clearance
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not available")

def test_split_part_basic(local_tmp_path, oversized_scad_file):
    from splitting import split_part
    
    split_planes = [{"axis": "z", "coordinate": 200.0}]
    try:
        segments = split_part(
            scad_path=oversized_scad_file,
            part_name="oversized_box",
            split_planes=split_planes,
            joint_configs=None,
            output_dir=local_tmp_path
        )
        
        assert len(segments) == 2
        assert segments[0]["name"] == "oversized_box_part_1"
        assert segments[1]["name"] == "oversized_box_part_2"
        
        stl_1 = segments[0]["stl_path"]
        stl_2 = segments[1]["stl_path"]
        assert os.path.exists(stl_1)
        assert os.path.exists(stl_2)
        
        from stl_utils import compute_stl_volume
        assert compute_stl_volume(stl_1) > 0
        assert compute_stl_volume(stl_2) > 0
        
        # Z-split should auto select flange
        assert segments[0]["joint_type"] == "flange"
        
        # Dimensions check
        assert "dimensions_mm" in segments[0]
        assert "fits_bed" in segments[0]
        
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not available")

def test_split_part_override_joint(local_tmp_path, oversized_scad_file):
    from splitting import split_part
    
    split_planes = [{"axis": "z", "coordinate": 200.0}]
    joint_configs = {
        "z": {
            "joint_type": "dovetail",
            "finger_count": 2,
            "finger_width": 10,
            "finger_depth": 5,
            "taper_angle": 20,
            "clearance": 0.2
        }
    }
    
    try:
        segments = split_part(
            scad_path=oversized_scad_file,
            part_name="oversized_box",
            split_planes=split_planes,
            joint_configs=joint_configs,
            output_dir=local_tmp_path
        )
        assert len(segments) == 2
        assert segments[0]["joint_type"] == "dovetail"
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not available")




