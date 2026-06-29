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

def pack_ffd(panels: list[dict], sheet_w: float, sheet_h: float, kerf: float) -> list[dict]:
    """Packs panels onto sheets using an optimized First-Fit Decreasing (FFD) algorithm with 90° rotation.
    
    Sorts panels by area descending. For each panel, finds the first available 
    corner position on any existing sheet (or creates a new sheet) where it fits, 
    trying both original and rotated orientations.
    """
    if not panels:
        return []
        
    # Sort panels by area descending
    sorted_panels = sorted(panels, key=lambda p: p["width_mm"] * p["height_mm"], reverse=True)
    
    sheets = []
    
    for panel in sorted_panels:
        w = panel["width_mm"]
        h = panel["height_mm"]
        name = panel["part_name"]
        
        # Check if panel can fit at all (original or rotated)
        can_fit_orig = (w + 2 * kerf <= sheet_w) and (h + 2 * kerf <= sheet_h)
        can_fit_rot = (h + 2 * kerf <= sheet_w) and (w + 2 * kerf <= sheet_h)
        if not (can_fit_orig or can_fit_rot):
            raise ValueError(f"Panel '{name}' ({w}x{h}) is too large for sheet ({sheet_w}x{sheet_h}) with kerf {kerf}")
            
        placed = False
        
        # Try to place on existing sheets
        for sheet in sheets:
            # Sort candidates by y then x
            sheet["candidates"] = sorted(sheet["candidates"], key=lambda pt: (pt[1], pt[0]))
            
            placement_found = None
            for cx, cy in sheet["candidates"]:
                # Try original then rotated orientation
                orientations = [(w, h, False)]
                if w != h:
                    orientations.append((h, w, True))
                    
                for pw, ph, rotated in orientations:
                    if cx + pw + kerf <= sheet_w and cy + ph + kerf <= sheet_h:
                        # Check overlap
                        overlaps = False
                        for p in sheet["panels"]:
                            px, py = p["x"], p["y"]
                            pw_p, ph_p = p["width"], p["height"]
                            if not (cx + pw + kerf <= px or cx >= px + pw_p + kerf or
                                    cy + ph + kerf <= py or cy >= py + ph_p + kerf):
                                overlaps = True
                                break
                        if not overlaps:
                            placement_found = (cx, cy, pw, ph, rotated)
                            break
                if placement_found:
                    break
                    
            if placement_found:
                cx, cy, pw, ph, rotated = placement_found
                # Place the panel
                sheet["panels"].append({
                    "part_name": name,
                    "x": round(cx, 2),
                    "y": round(cy, 2),
                    "width": pw,
                    "height": ph,
                    "rotated": rotated
                })
                # Update candidates
                sheet["candidates"].remove((cx, cy))
                sheet["candidates"].append((cx + pw + kerf, cy))
                sheet["candidates"].append((cx, cy + ph + kerf))
                
                # Filter candidates: remove duplicates, out-of-bounds, and covered ones
                filtered_candidates = []
                for tx, ty in sheet["candidates"]:
                    if tx + kerf > sheet_w or ty + kerf > sheet_h:
                        continue
                    # Check if inside any placed panel
                    covered = False
                    for p in sheet["panels"]:
                        px, py = p["x"], p["y"]
                        pw_p, ph_p = p["width"], p["height"]
                        if px <= tx < px + pw_p + kerf - 1e-5 and py <= ty < py + ph_p + kerf - 1e-5:
                            covered = True
                            break
                    if not covered:
                        filtered_candidates.append((tx, ty))
                # Unique
                sheet["candidates"] = list(dict.fromkeys(filtered_candidates))
                placed = True
                break
                
        if not placed:
            # Create a new sheet
            new_sheet_number = len(sheets) + 1
            
            # Try original first, fallback to rotated if it doesn't fit originally
            pw, ph, rotated = w, h, False
            if w + 2 * kerf > sheet_w or h + 2 * kerf > sheet_h:
                pw, ph, rotated = h, w, True
                
            new_sheet_panels = [{
                "part_name": name,
                "x": round(kerf, 2),
                "y": round(kerf, 2),
                "width": pw,
                "height": ph,
                "rotated": rotated
            }]
            
            # Initial candidates
            new_candidates = [
                (kerf + pw + kerf, kerf),
                (kerf, kerf + ph + kerf)
            ]
            # Filter candidates
            filtered_candidates = []
            for tx, ty in new_candidates:
                if tx + kerf <= sheet_w and ty + kerf <= sheet_h:
                    filtered_candidates.append((tx, ty))
                    
            sheets.append({
                "sheet_number": new_sheet_number,
                "sheet_width_mm": sheet_w,
                "sheet_height_mm": sheet_h,
                "panels": new_sheet_panels,
                "candidates": list(dict.fromkeys(filtered_candidates)),
                "utilization_percent": 0.0,
                "waste_area_mm2": 0.0
            })
            
    # Calculate final utilization and waste for all sheets
    sheet_area = sheet_w * sheet_h
    for sheet in sheets:
        placed_area = sum(p["width"] * p["height"] for p in sheet["panels"])
        sheet["utilization_percent"] = round((placed_area / sheet_area) * 100.0, 2)
        sheet["waste_area_mm2"] = round(sheet_area - placed_area, 2)
        # Remove candidate tracking info before returning to user
        if "candidates" in sheet:
            del sheet["candidates"]
            
    return sheets

