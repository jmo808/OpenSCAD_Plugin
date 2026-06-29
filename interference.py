import os
import tempfile
import shutil
import base64
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
            if "Current top level object is empty" in str(e) or "Current top level object is not a 3D object" in str(e):
                part_a_exists = False
            else:
                raise
                
        # 2. Export part_b to STL
        try:
            run_openscad(["-D", f'part="{part_b}"', "-o", part_b_stl, scad_path])
            part_b_exists = True
        except RuntimeError as e:
            if "Current top level object is empty" in str(e) or "Current top level object is not a 3D object" in str(e):
                part_b_exists = False
            else:
                raise
                
        # If either part is empty or 2D, there is no 3D collision volume
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
            if "Current top level object is empty" in str(e) or "Current top level object is not a 3D object" in str(e):
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

def generate_highlight_scad(scad_path: str, collisions: list[dict], temp_dir: str) -> str:
    """Generates the wrapper SCAD code for visual collision highlight."""
    assembly_stl = os.path.join(temp_dir, "assembly.stl")
    assembly_stl_esc = assembly_stl.replace("\\", "\\\\")
    
    scad_lines = [
        "// Collision highlight render wrapper",
        "color([0.7, 0.7, 0.7, 0.25]) {",
        f'    import("{assembly_stl_esc}");',
        "}",
        "color(\"red\") {"
    ]
    
    for c in collisions:
        part_a = c["part_a"]
        part_b = c["part_b"]
        col_stl = os.path.join(temp_dir, f"{part_a}_{part_b}_intersection.stl")
        col_stl_esc = col_stl.replace("\\", "\\\\")
        scad_lines.append(f'    import("{col_stl_esc}");')
        
    scad_lines.append("}")
    return "\n".join(scad_lines)

def render_collision_highlight(
    scad_path: str,
    collisions: list[dict],
    output_path: str,
    img_size: int = 512,
    colorscheme: str = "Sunset"
) -> str:
    """Renders a PNG preview of the assembly with colliding parts highlighted in red."""
    validate_scad_path(scad_path)
    
    if not collisions:
        return ""
        
    base_temp_dir = os.path.expanduser("~/.openscad_temp")
    os.makedirs(base_temp_dir, exist_ok=True)
    temp_dir = tempfile.mkdtemp(dir=base_temp_dir, prefix="highlight_")
    
    try:
        # 1. Export full assembly
        assembly_stl = os.path.join(temp_dir, "assembly.stl")
        try:
            run_openscad(["-D", 'part="all"', "-o", assembly_stl, scad_path])
        except RuntimeError as e:
            if "Current top level object is empty" in str(e) or "Current top level object is not a 3D object" in str(e):
                with open(assembly_stl, "wb") as f:
                    f.write(b"\x00" * 84)
            else:
                raise
        
        # 2. Export each collision's intersection STL
        for c in collisions:
            part_a = c["part_a"]
            part_b = c["part_b"]
            col_stl = os.path.join(temp_dir, f"{part_a}_{part_b}_intersection.stl")
            
            part_a_stl = os.path.join(temp_dir, f"{part_a}.stl")
            part_b_stl = os.path.join(temp_dir, f"{part_b}.stl")
            
            run_openscad(["-D", f'part="{part_a}"', "-o", part_a_stl, scad_path])
            run_openscad(["-D", f'part="{part_b}"', "-o", part_b_stl, scad_path])
            
            # Generate wrapper to intersect them
            wrapper_scad = os.path.join(temp_dir, f"{part_a}_{part_b}_intersection.scad")
            scad_code = generate_intersection_scad(part_a_stl, part_b_stl)
            with open(wrapper_scad, "w") as f:
                f.write(scad_code)
                
            run_openscad(["-o", col_stl, wrapper_scad])
            
        # 3. Generate highlight wrapper SCAD
        highlight_scad_path = os.path.join(temp_dir, "highlight.scad")
        scad_code = generate_highlight_scad(scad_path, collisions, temp_dir)
        with open(highlight_scad_path, "w") as f:
            f.write(scad_code)
            
        # 4. Render to PNG using OpenSCAD CLI
        camera_args = "0,0,0,55,0,45,0" # isometric
        
        cmd_args = [
            "-o", output_path,
            "--imgsize", f"{img_size},{img_size}",
            "--projection", "o",  # orthogonal
            "--colorscheme", colorscheme,
            "--autocenter",
            "--viewall",
            f"--camera={camera_args}",
            highlight_scad_path
        ]
        
        run_openscad(cmd_args)
        
        if not os.path.exists(output_path):
            raise RuntimeError(f"Failed to render collision highlight PNG at: '{output_path}'")
            
        # Read and encode to base64
        with open(output_path, "rb") as f:
            img_bytes = f.read()
        return base64.b64encode(img_bytes).decode("utf-8")
        
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
