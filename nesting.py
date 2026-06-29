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

def pack_shelf(panels: list[dict], sheet_w: float, sheet_h: float, kerf: float) -> list[dict]:
    """Packs panels onto sheets using a simple shelf packing algorithm.
    
    Places panels left-to-right on horizontal shelves. Starts a new shelf when 
    the current shelf is full. Starts a new sheet when the current sheet is full.
    """
    if not panels:
        return []
        
    sheets = []
    
    current_sheet_number = 1
    current_sheet_panels = []
    
    x = kerf
    y = kerf
    shelf_height = 0.0
    
    for panel in panels:
        w = panel["width_mm"]
        h = panel["height_mm"]
        name = panel["part_name"]
        
        # A single panel must fit inside the sheet accounting for kerf margins on all sides
        if w + 2 * kerf > sheet_w or h + 2 * kerf > sheet_h:
            raise ValueError(f"Panel '{name}' ({w}x{h}) is too large for sheet ({sheet_w}x{sheet_h}) with kerf {kerf}")
            
        # Try to place on the current shelf
        if x + w + kerf <= sheet_w and y + h + kerf <= sheet_h:
            current_sheet_panels.append({
                "part_name": name,
                "x": round(x, 2),
                "y": round(y, 2),
                "width": w,
                "height": h,
                "rotated": False
            })
            x += w + kerf
            if h > shelf_height:
                shelf_height = h
        else:
            # Try to start a new shelf on the current sheet
            new_x = kerf
            new_y = y + shelf_height + kerf
            
            if new_x + w + kerf <= sheet_w and new_y + h + kerf <= sheet_h:
                x = new_x
                y = new_y
                shelf_height = h
                current_sheet_panels.append({
                    "part_name": name,
                    "x": round(x, 2),
                    "y": round(y, 2),
                    "width": w,
                    "height": h,
                    "rotated": False
                })
                x += w + kerf
            else:
                # Start a new sheet
                sheet_area = sheet_w * sheet_h
                placed_area = sum(p["width"] * p["height"] for p in current_sheet_panels)
                util = round((placed_area / sheet_area) * 100.0, 2)
                waste = round(sheet_area - placed_area, 2)
                
                sheets.append({
                    "sheet_number": current_sheet_number,
                    "sheet_width_mm": sheet_w,
                    "sheet_height_mm": sheet_h,
                    "panels": current_sheet_panels,
                    "utilization_percent": util,
                    "waste_area_mm2": waste
                })
                
                current_sheet_number += 1
                current_sheet_panels = []
                x = kerf
                y = kerf
                shelf_height = h
                
                current_sheet_panels.append({
                    "part_name": name,
                    "x": round(x, 2),
                    "y": round(y, 2),
                    "width": w,
                    "height": h,
                    "rotated": False
                })
                x += w + kerf
                
    if current_sheet_panels:
        sheet_area = sheet_w * sheet_h
        placed_area = sum(p["width"] * p["height"] for p in current_sheet_panels)
        util = round((placed_area / sheet_area) * 100.0, 2)
        waste = round(sheet_area - placed_area, 2)
        
        sheets.append({
            "sheet_number": current_sheet_number,
            "sheet_width_mm": sheet_w,
            "sheet_height_mm": sheet_h,
            "panels": current_sheet_panels,
            "utilization_percent": util,
            "waste_area_mm2": waste
        })
        
    return sheets

