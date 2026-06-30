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
