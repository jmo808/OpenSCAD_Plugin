import os
import uuid
import shutil
import math
from scad_utils import run_openscad, validate_scad_path
from stl_utils import extract_bounding_box

def get_part_bbox(scad_path: str, part_name: str | None = None) -> dict:
    """Compiles the specified part to STL and extracts its bounding box.

    Args:
        scad_path: Path to the source .scad file.
        part_name: Optional name of the part to extract. If None, compiles the
          entire model.

    Returns:
        A dictionary containing bounding box coordinates:
        {x_min, x_max, y_min, y_max, z_min, z_max}.

    Raises:
        FileNotFoundError: If the scad_path does not exist.
        RuntimeError: If OpenSCAD compilation fails.
    """
    validate_scad_path(scad_path)
    scad_dir = os.path.dirname(os.path.abspath(scad_path))
    tmpdir = os.path.join(scad_dir, f".tmp_split_{uuid.uuid4().hex}")
    os.makedirs(tmpdir, exist_ok=True)
    out_name = part_name if part_name else "model"
    temp_stl = os.path.join(tmpdir, f"{out_name}.stl")
    try:
        cmd_args = []
        if part_name:
            cmd_args.extend(["-D", f'part="{part_name}"'])
        cmd_args.extend(["-o", temp_stl, scad_path])
        run_openscad(cmd_args)
        bbox = extract_bounding_box(temp_stl)
        return bbox
    finally:
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)

def calculate_split_planes(
    bbox: dict,
    bed_x: float = 220.0,
    bed_y: float = 220.0,
    bed_z: float = 250.0,
    margin: float = 5.0
) -> list[dict]:
    """Calculates optimal split planes for a part based on printer bed limits.

    Args:
        bbox: Bounding box dictionary of the part.
        bed_x: Printer bed width in X direction (mm).
        bed_y: Printer bed depth in Y direction (mm).
        bed_z: Printer build height in Z direction (mm).
        margin: Safety margin to subtract from bed dimensions (mm).

    Returns:
        A list of dictionaries specifying the split axis and coordinate:
        [{"axis": "z", "coordinate": 200.0}, ...]

    Raises:
        ValueError: If the part already fits within the bed (no split needed).
    """
    eff_x = bed_x - 2 * margin
    eff_y = bed_y - 2 * margin
    eff_z = bed_z - 2 * margin
    
    x_len = bbox["x_max"] - bbox["x_min"]
    y_len = bbox["y_max"] - bbox["y_min"]
    z_len = bbox["z_max"] - bbox["z_min"]
    
    if x_len <= eff_x and y_len <= eff_y and z_len <= eff_z:
        raise ValueError("Part already fits within printer bed (accounting for safety margin).")
        
    splits = []
    
    for axis, length, limit, min_val in [
        ("x", x_len, eff_x, bbox["x_min"]),
        ("y", y_len, eff_y, bbox["y_min"]),
        ("z", z_len, eff_z, bbox["z_min"])
    ]:
        if length > limit:
            num_segments = math.ceil(length / limit)
            segment_length = length / num_segments
            for i in range(1, num_segments):
                coord = min_val + i * segment_length
                splits.append({
                    "axis": axis,
                    "coordinate": round(coord, 4)
                })
                
    return splits

def validate_manual_split(bbox: dict, axis: str, coord: float) -> dict:
    """Validates if a manual split axis and coordinate is valid for the bounding box.

    Args:
        bbox: Bounding box dictionary of the part.
        axis: Axis to split along ("x", "y", or "z").
        coord: Coordinate of the split plane.

    Returns:
        A dictionary containing the validated split details:
        {"axis": "z", "coordinate": 150.0}

    Raises:
        ValueError: If the axis is invalid or coordinate is out of bounds.
    """
    axis = axis.lower()
    if axis not in ["x", "y", "z"]:
        raise ValueError(f"Invalid axis: {axis}. Must be 'x', 'y', or 'z'.")
        
    min_val = bbox[f"{axis}_min"]
    max_val = bbox[f"{axis}_max"]
    
    if not (min_val < coord < max_val):
        raise ValueError(
            f"Split coordinate {coord} is out of bounds for axis {axis} ({min_val} to {max_val})."
        )
        
    return {
        "axis": axis,
        "coordinate": float(coord)
    }

def generate_dovetail_scad(
    face_width: float,
    face_height: float,
    params: dict | None = None
) -> tuple[str, str]:
    """Generates OpenSCAD code for interlocking dovetail joint fingers.

    Args:
        face_width: Width of the cut interface face (mm).
        face_height: Height of the cut interface face (mm).
        params: Dictionary of joint parameters:
          {finger_count, finger_width, finger_depth, taper_angle, clearance}.

    Returns:
        A tuple of (male_scad, female_scad) strings.
    """
    if params is None:
        params = {}
    finger_count = params.get("finger_count", 2)
    finger_width = params.get("finger_width", 10.0)
    finger_depth = params.get("finger_depth", 5.0)
    taper_angle = params.get("taper_angle", 20.0)
    clearance = params.get("clearance", 0.2)
    
    angle_rad = math.radians(taper_angle)
    w_base = finger_width
    w_tip = finger_width + 2 * finger_depth * math.tan(angle_rad)
    
    points_male = f"[[-{w_base}/2, 0], [{w_base}/2, 0], [{w_tip}/2, {finger_depth}], [-{w_tip}/2, {finger_depth}]]"
    points_female = f"[[-{w_base}/2, -0.1], [{w_base}/2, -0.1], [{w_tip}/2, {finger_depth}], [-{w_tip}/2, {finger_depth}]]"
    
    translates_male = []
    translates_female = []
    
    for i in range(finger_count):
        x_pos = -face_width / 2.0 + (i + 0.5) * (face_width / finger_count)
        
        # Male finger
        translates_male.append(
            f"translate([{x_pos:.4f}, 0, 0]) rotate([90, 0, 0]) "
            f"linear_extrude(height={face_height:.4f}, center=true) "
            f"polygon(points={points_male});"
        )
        
        # Female pocket (with clearance)
        # Note: height is extended slightly so it cuts completely through extrusion boundaries
        translates_female.append(
            f"translate([{x_pos:.4f}, 0, 0]) rotate([90, 0, 0]) "
            f"linear_extrude(height={face_height + clearance*2 + 0.2:.4f}, center=true) "
            f"offset(delta={clearance}) "
            f"polygon(points={points_female});"
        )
        
    male_scad = "union() {\n    " + "\n    ".join(translates_male) + "\n}"
    female_scad = "union() {\n    " + "\n    ".join(translates_female) + "\n}"
    
    return male_scad, female_scad

def generate_flange_scad(
    face_width: float,
    face_height: float,
    params: dict | None = None
) -> tuple[str, str]:
    """Generates OpenSCAD code for overlapping flange tabs with screw and nut holes.

    Args:
        face_width: Width of the cut interface face (mm).
        face_height: Height of the cut interface face (mm).
        params: Dictionary of joint parameters:
          {flange_width, flange_thickness, screw_size, screw_count, clearance}.

    Returns:
        A tuple of (male_scad, female_scad) strings.
    """
    if params is None:
        params = {}
    flange_width = params.get("flange_width", 20.0)
    flange_thickness = params.get("flange_thickness", 5.0)
    screw_size = params.get("screw_size", "M3")
    screw_count = params.get("screw_count", 2)
    clearance = params.get("clearance", 0.2)
    
    # Fastener dimensions
    screw_dims = {
        "M2": {"shaft": 2.2, "head": 4.0, "nut": 4.5},
        "M3": {"shaft": 3.2, "head": 6.0, "nut": 6.4},
        "M4": {"shaft": 4.2, "head": 8.0, "nut": 8.1}
    }
    dims = screw_dims.get(screw_size.upper(), screw_dims["M3"])
    
    sh_m = dims["shaft"]
    hd_m = dims["head"]
    
    sh_f = dims["shaft"] + clearance
    nt_f = dims["nut"] + clearance
    
    t = flange_thickness
    w = flange_width
    
    # Generate translates for screw holes
    screw_holes_male = []
    screw_holes_female = []
    
    for i in range(screw_count):
        x_pos = -face_width / 2.0 + (i + 0.5) * (face_width / screw_count)
        
        # Male screw: shaft and head counterbore
        # Head counterbore is at Z = -t to Z = -t/2
        screw_holes_male.append(
            f"translate([{x_pos:.4f}, 0, -{t:.4f} - 0.1]) "
            f"cylinder(d={sh_m:.4f}, h={2*t + 0.2:.4f}, $fn=16);"
        )
        screw_holes_male.append(
            f"translate([{x_pos:.4f}, 0, -{t:.4f} - 0.1]) "
            f"cylinder(d={hd_m:.4f}, h={t/2 + 0.1:.4f}, $fn=16);"
        )
        
        # Female screw: shaft and hex nut trap
        # Nut trap is at the back (Z = t to Z = 2t), say Z = 1.5t to 2t
        screw_holes_female.append(
            f"translate([{x_pos:.4f}, 0, -0.1]) "
            f"cylinder(d={sh_f:.4f}, h={2*t + 0.2:.4f}, $fn=16);"
        )
        screw_holes_female.append(
            f"translate([{x_pos:.4f}, 0, {1.5*t:.4f}]) "
            f"cylinder(d={nt_f:.4f}, h={t/2 + 0.1:.4f}, $fn=6);"
        )
        
    holes_male_str = "\n        ".join(screw_holes_male)
    holes_female_str = "\n        ".join(screw_holes_female)
    
    # Male: wrapper that adds tab and subtracts screw head holes
    male_scad = f"""difference() {{
    union() {{
        if ($children > 0) children(0);
        translate([-{face_width/2:.4f}, -{w/2:.4f}, 0])
            cube([{face_width:.4f}, {w:.4f}, {t:.4f}]);
    }}
    union() {{
        {holes_male_str}
    }}
}}"""

    # For female, the pocket is subtracted, and the nut traps are subtracted
    female_scad = f"""difference() {{
    if ($children > 0) children(0);
    union() {{
        // Overlap pocket to be subtracted
        translate([-{face_width/2 + 0.1:.4f}, -{w/2 + clearance:.4f}, -0.1])
            cube([{face_width + 0.2:.4f}, {w + 2*clearance:.4f}, {t + clearance + 0.1:.4f}]);
        // Screw holes and nut traps
        {holes_female_str}
    }}
}}"""

    return male_scad, female_scad

def generate_tongue_groove_scad(
    face_width: float,
    face_height: float,
    params: dict | None = None
) -> tuple[str, str]:
    """Generates OpenSCAD code for tongue-and-groove alignment joints.

    Args:
        face_width: Width of the cut interface face (mm).
        face_height: Height of the cut interface face (mm).
        params: Dictionary of joint parameters:
          {tongue_width, tongue_depth, clearance}.

    Returns:
        A tuple of (male_scad, female_scad) strings.
    """
    if params is None:
        params = {}
    t_width = params.get("tongue_width", 5.0)
    t_depth = params.get("tongue_depth", 3.0)
    clearance = params.get("clearance", 0.2)
    
    # Male tongue (protruding ridge)
    male_scad = f"""union() {{
    if ($children > 0) children(0);
    translate([-{(face_width + 0.1)/2:.4f}, -{t_width/2:.4f}, 0])
        cube([{face_width + 0.1:.4f}, {t_width:.4f}, {t_depth:.4f}]);
}}"""

    # Female groove (pocket with clearance)
    female_scad = f"""difference() {{
    if ($children > 0) children(0);
    translate([-{(face_width + 0.2)/2:.4f}, -{(t_width + 2*clearance)/2:.4f}, -0.1])
        cube([{face_width + 0.2:.4f}, {t_width + 2*clearance:.4f}, {t_depth + clearance + 0.1:.4f}]);
}}"""

    return male_scad, female_scad

def generate_pin_scad(
    face_width: float,
    face_height: float,
    params: dict | None = None
) -> tuple[str, str]:
    """Generates OpenSCAD code for pin alignment holes.

    Args:
        face_width: Width of the cut interface face (mm).
        face_height: Height of the cut interface face (mm).
        params: Dictionary of joint parameters:
          {pin_diameter, pin_depth, pin_count, clearance}.

    Returns:
        A tuple of (male_scad, female_scad) strings.
    """
    if params is None:
        params = {}
    pin_diam = params.get("pin_diameter", 4.0)
    pin_depth = params.get("pin_depth", 6.0)
    pin_count = params.get("pin_count", 2)
    clearance = params.get("clearance", 0.2)
    
    holes_male = []
    holes_female = []
    
    for i in range(pin_count):
        x_pos = -face_width / 2.0 + (i + 0.5) * (face_width / pin_count)
        
        # Male holes: Nominal diameter and depth, cutting downwards
        holes_male.append(
            f"translate([{x_pos:.4f}, 0, -{pin_depth:.4f}]) "
            f"cylinder(d={pin_diam:.4f}, h={pin_depth + 0.1:.4f}, $fn=32);"
        )
        
        # Female holes: Enlarged diameter and depth, cutting upwards
        holes_female.append(
            f"translate([{x_pos:.4f}, 0, -0.1]) "
            f"cylinder(d={pin_diam + clearance:.4f}, h={pin_depth + clearance + 0.1:.4f}, $fn=32);"
        )
        
    holes_male_str = "\n        ".join(holes_male)
    holes_female_str = "\n        ".join(holes_female)
    
    male_scad = f"""difference() {{
    if ($children > 0) children(0);
    union() {{
        {holes_male_str}
    }}
}}"""

    female_scad = f"""difference() {{
    if ($children > 0) children(0);
    union() {{
        {holes_female_str}
    }}
}}"""

    return male_scad, female_scad

def get_joint_config(axis: str, joint_configs: dict | None) -> dict:
    """Helper to retrieve joint config for a given axis, applying defaults."""
    config = {}
    if joint_configs and axis in joint_configs:
        config = joint_configs[axis]
        
    joint_type = config.get("joint_type")
    if not joint_type:
        joint_type = "flange" if axis == "z" else "dovetail"
        
    params = {
        "joint_type": joint_type,
        "clearance": config.get("clearance", 0.2)
    }
    
    if joint_type == "dovetail":
        params.update({
            "finger_count": config.get("finger_count", 2),
            "finger_width": config.get("finger_width", 10.0),
            "finger_depth": config.get("finger_depth", 5.0),
            "taper_angle": config.get("taper_angle", 20.0)
        })
    elif joint_type == "flange":
        params.update({
            "flange_width": config.get("flange_width", 20.0),
            "flange_thickness": config.get("flange_thickness", 5.0),
            "screw_size": config.get("screw_size", "M3"),
            "screw_count": config.get("screw_count", 2)
        })
    elif joint_type == "tongue_groove":
        params.update({
            "tongue_width": config.get("tongue_width", 5.0),
            "tongue_depth": config.get("tongue_depth", 3.0)
        })
    elif joint_type == "pin":
        params.update({
            "pin_diameter": config.get("pin_diameter", 4.0),
            "pin_depth": config.get("pin_depth", 6.0),
            "pin_count": config.get("pin_count", 2)
        })
        
    return params

def generate_joint_geometry(
    joint_type: str,
    face_width: float,
    face_height: float,
    params: dict
) -> tuple[str, str]:
    """Routes joint generation to the correct SCAD generator function."""
    if joint_type == "dovetail":
        return generate_dovetail_scad(face_width, face_height, params)
    elif joint_type == "flange":
        return generate_flange_scad(face_width, face_height, params)
    elif joint_type == "tongue_groove":
        return generate_tongue_groove_scad(face_width, face_height, params)
    elif joint_type == "pin":
        return generate_pin_scad(face_width, face_height, params)
    else:
        raise ValueError(f"Unknown joint type: {joint_type}")

def split_part(
    scad_path: str,
    part_name: str | None,
    split_planes: list[dict],
    joint_configs: dict | None = None,
    output_dir: str | None = None
) -> list[dict]:
    """Splits a part into multiple segments along split planes and applies joints.

    Args:
        scad_path: Path to the source .scad file.
        part_name: Optional name of the part to split.
        split_planes: List of dictionaries defining split planes:
          [{"axis": "x"|"y"|"z", "coordinate": float}].
        joint_configs: Optional dictionary overriding joint parameters.
        output_dir: Optional directory to write exported STL files to.

    Returns:
        A list of dictionaries containing segment details:
        [{"name", "stl_path", "dimensions_mm", "fits_bed", "joint_type", "joint_face"}].
    """
    validate_scad_path(scad_path)
    
    # 1. Get bounding box
    bbox = get_part_bbox(scad_path, part_name)
    
    X_min, X_max = bbox["x_min"], bbox["x_max"]
    Y_min, Y_max = bbox["y_min"], bbox["y_max"]
    Z_min, Z_max = bbox["z_min"], bbox["z_max"]
    
    # 2. Setup partitions
    x_coords = sorted(list({
        s["coordinate"] for s in split_planes
        if s["axis"].lower() == "x" and X_min < s["coordinate"] < X_max
    }))
    y_coords = sorted(list({
        s["coordinate"] for s in split_planes
        if s["axis"].lower() == "y" and Y_min < s["coordinate"] < Y_max
    }))
    z_coords = sorted(list({
        s["coordinate"] for s in split_planes
        if s["axis"].lower() == "z" and Z_min < s["coordinate"] < Z_max
    }))
    
    x_splits = [X_min] + x_coords + [X_max]
    y_splits = [Y_min] + y_coords + [Y_max]
    z_splits = [Z_min] + z_coords + [Z_max]
    
    x_intervals = [(x_splits[i], x_splits[i+1]) for i in range(len(x_splits)-1)]
    y_intervals = [(y_splits[i], y_splits[i+1]) for i in range(len(y_splits)-1)]
    z_intervals = [(z_splits[i], z_splits[i+1]) for i in range(len(z_splits)-1)]
    
    if not output_dir:
        output_dir = os.path.dirname(os.path.abspath(scad_path))
        
    os.makedirs(output_dir, exist_ok=True)
    
    segments = []
    idx = 1
    
    # Generate all segments
    for z_min, z_max in z_intervals:
        for y_min, y_max in y_intervals:
            for x_min, x_max in x_intervals:
                p_name = part_name if part_name else "model"
                seg_name = f"{p_name}_part_{idx}"
                stl_path = os.path.abspath(os.path.join(output_dir, f"{seg_name}.stl"))
                
                module_defs = []
                chain_calls = []
                
                applied_joint_type = None
                applied_joint_face = None
                
                joint_idx = 1
                
                for axis, val, is_min, face_name in [
                    ("x", x_min, True, "left"),
                    ("x", x_max, False, "right"),
                    ("y", y_min, True, "front"),
                    ("y", y_max, False, "back"),
                    ("z", z_min, True, "bottom"),
                    ("z", z_max, False, "top")
                ]:
                    is_split = False
                    if axis == "x" and val in x_coords:
                        is_split = True
                    elif axis == "y" and val in y_coords:
                        is_split = True
                    elif axis == "z" and val in z_coords:
                        is_split = True
                        
                    if is_split:
                        config = get_joint_config(axis, joint_configs)
                        j_type = config["joint_type"]
                        applied_joint_type = j_type
                        applied_joint_face = face_name
                        
                        if axis == "x":
                            fw = y_max - y_min
                            fh = z_max - z_min
                            pos = [val, (y_min + y_max)/2.0, (z_min + z_max)/2.0]
                            rot = [0, 90, 90]
                        elif axis == "y":
                            fw = x_max - x_min
                            fh = z_max - z_min
                            pos = [(x_min + x_max)/2.0, val, (z_min + z_max)/2.0]
                            rot = [-90, 0, 0]
                        else:  # z
                            fw = x_max - x_min
                            fh = y_max - y_min
                            pos = [(x_min + x_max)/2.0, (y_min + y_max)/2.0, val]
                            rot = [0, 0, 0]
                            
                        male_raw, female_raw = generate_joint_geometry(j_type, fw, fh, config)
                        raw_scad = female_raw if is_min else male_raw
                        
                        mod_name = f"joint_mod_{joint_idx}"
                        module_defs.append(f"""module {mod_name}() {{
    translate([{pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f}])
        rotate([{rot[0]:.4f}, {rot[1]:.4f}, {rot[2]:.4f}])
            {raw_scad}
}}""")
                        chain_calls.append(f"{mod_name}()")
                        joint_idx += 1
                
                abs_scad_path = os.path.abspath(scad_path)
                
                # If part_name is specified, use 'use' statement to avoid executing top-level geometry,
                # and call the part's module inside the intersection.
                # If part_name is None, fall back to 'include' inside the intersection.
                if part_name:
                    instantiation = f"{part_name}();"
                    import_statement = f"use <{abs_scad_path}>"
                else:
                    instantiation = f"include <{abs_scad_path}>"
                    import_statement = ""
                
                # Expand bounding box slightly (0.1mm) to prevent boundary overlaps
                intersection_scad = f"""intersection() {{
    {instantiation}
    translate([{x_min - 0.1:.4f}, {y_min - 0.1:.4f}, {z_min - 0.1:.4f}])
        cube([{x_max - x_min + 0.2:.4f}, {y_max - y_min + 0.2:.4f}, {z_max - z_min + 0.2:.4f}]);
}}"""
                
                body_scad = intersection_scad
                for call in reversed(chain_calls):
                    body_scad = f"{call} {body_scad}"
                    
                prefix = import_statement + "\n\n" if import_statement else ""
                temp_scad_content = prefix + "\n\n".join(module_defs) + "\n\n" + body_scad + "\n"
                
                temp_scad_path = os.path.join(output_dir, f"_temp_seg_{uuid.uuid4().hex}.scad")
                with open(temp_scad_path, "w") as f:
                    f.write(temp_scad_content)
                    
                try:
                    cmd_args = []
                    if part_name:
                        cmd_args.extend(["-D", f'part="{part_name}"'])
                    cmd_args.extend(["-o", stl_path, temp_scad_path])
                    run_openscad(cmd_args)
                    
                    from stl_utils import compute_stl_volume
                    if not os.path.exists(stl_path) or compute_stl_volume(stl_path) <= 0.0:
                        raise RuntimeError(f"Generated STL for segment {seg_name} is empty or non-manifold.")
                        
                finally:
                    if os.path.exists(temp_scad_path):
                        os.remove(temp_scad_path)
                        
                segments.append({
                    "name": seg_name,
                    "stl_path": stl_path,
                    "dimensions_mm": {
                        "x": round(x_max - x_min, 2),
                        "y": round(y_max - y_min, 2),
                        "z": round(z_max - z_min, 2)
                    },
                    "fits_bed": True,
                    "joint_type": applied_joint_type if applied_joint_type else "none",
                    "joint_face": applied_joint_face if applied_joint_face else "none"
                })
                idx += 1
                
    return segments
