import os
import tempfile
import shutil
from scad_utils import validate_scad_path, run_openscad
from stl_utils import compute_stl_volume, extract_bounding_box

def generate_intersection_scad(part_a_stl_path: str, part_b_stl_path: str) -> str:
    """Generates wrapper SCAD code to calculate intersection of two STL files."""
    esc_a = part_a_stl_path.replace("\\", "\\\\")
    esc_b = part_b_stl_path.replace("\\", "\\\\")
    return f"""intersection() {{
    import("{esc_a}");
    import("{esc_b}");
}}
"""

def check_pair(scad_path: str, part_a: str, part_b: str) -> dict | None:
    """Calculates intersection between part_a and part_b.
    
    Returns:
        dict: containing part_a, part_b, intersection_volume_mm3, bounding_box if volume > 0.001
        None: if no collision detected
    """
    validate_scad_path(scad_path)
    
    base_temp_dir = os.path.expanduser("~/.openscad_temp")
    os.makedirs(base_temp_dir, exist_ok=True)
    temp_dir = tempfile.mkdtemp(dir=base_temp_dir, prefix="interference_")
    
    try:
        part_a_stl = os.path.join(temp_dir, f"{part_a}.stl")
        part_b_stl = os.path.join(temp_dir, f"{part_b}.stl")
        wrapper_scad_path = os.path.join(temp_dir, "intersection.scad")
        wrapper_stl_path = os.path.join(temp_dir, "intersection.stl")
        
        # 1. Export part_a to STL
        try:
            run_openscad(["-D", f'part="{part_a}"', "-o", part_a_stl, scad_path])
            part_a_exists = True
        except RuntimeError as e:
            if "Current top level object is empty" in str(e):
                part_a_exists = False
            else:
                raise
                
        # 2. Export part_b to STL
        try:
            run_openscad(["-D", f'part="{part_b}"', "-o", part_b_stl, scad_path])
            part_b_exists = True
        except RuntimeError as e:
            if "Current top level object is empty" in str(e):
                part_b_exists = False
            else:
                raise
                
        # If either part is empty, there is no collision
        if not part_a_exists or not part_b_exists:
            return None
        
        # 3. Generate wrapper SCAD
        scad_code = generate_intersection_scad(part_a_stl, part_b_stl)
        with open(wrapper_scad_path, "w") as f:
            f.write(scad_code)
            
        # 4. Compile to STL
        try:
            run_openscad(["-o", wrapper_stl_path, wrapper_scad_path])
        except RuntimeError as e:
            if "Current top level object is empty" in str(e):
                return None
            raise
        
        # 5. Read volume
        volume = compute_stl_volume(wrapper_stl_path)
        
        # Tolerance threshold to filter float precision noise
        if volume > 0.001:
            bbox = extract_bounding_box(wrapper_stl_path)
            return {
                "part_a": part_a,
                "part_b": part_b,
                "intersection_volume_mm3": round(volume, 4),
                "bounding_box": bbox
            }
        return None
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def run_pairwise_check(scad_path: str, parts: list[str], fail_fast: bool = False) -> list[dict]:
    """Runs interference checks for all unique pairs of parts.
    
    Args:
        scad_path: Path to the .scad source file
        parts: List of part names to check
        fail_fast: If True, stops checking after first collision is found
        
    Returns:
        list[dict]: List of detected collisions
    """
    validate_scad_path(scad_path)
    collisions = []
    
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            part_a = parts[i]
            part_b = parts[j]
            
            res = check_pair(scad_path, part_a, part_b)
            if res is not None:
                collisions.append(res)
                if fail_fast:
                    return collisions
                    
    return collisions
