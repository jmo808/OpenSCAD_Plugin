import os
import tempfile
import shutil
from scad_utils import (
    discover_parts,
    validate_scad_path,
    run_openscad,
    get_dxf_bbox
)

def extract_panel_dimensions(scad_path: str, parts: list[str] = None) -> list[dict]:
    """Extracts panel dimensions (width_mm, height_mm) from the OpenSCAD assembly file.
    
    Using the part selector pattern, each discovered/specified part is exported 
    to a temporary DXF projection, and its bounding box is parsed.
    """
    # 1. Validate SCAD path
    validate_scad_path(scad_path)
    
    # 2. Discover parts
    discovered = discover_parts(scad_path)
    if not discovered:
        return []
        
    # 3. Filter if parts list is provided
    if parts is not None:
        parts_to_process = [p for p in discovered if p in parts]
    else:
        parts_to_process = discovered
        
    results = []
    
    # Create a local temp directory inside the SCAD file's directory
    # since sandboxed/Flatpak OpenSCAD cannot access system /tmp
    scad_dir = os.path.dirname(os.path.abspath(scad_path))
    import uuid
    tmpdir = os.path.join(scad_dir, f".tmp_nesting_{uuid.uuid4().hex}")
    os.makedirs(tmpdir, exist_ok=True)
    
    try:
        for part in parts_to_process:
            temp_dxf = os.path.join(tmpdir, f"{part}.dxf")
            
            # Export part to DXF using OpenSCAD CLI
            cmd_args = [
                "-D", f'part="{part}"',
                "-o", temp_dxf,
                scad_path
            ]
            
            try:
                run_openscad(cmd_args)
                width, height = get_dxf_bbox(temp_dxf)
                results.append({
                    "part_name": part,
                    "width_mm": width,
                    "height_mm": height
                })
            except Exception as e:
                raise RuntimeError(f"Failed to compile part '{part}': {str(e)}")
    finally:
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
                
    return results
