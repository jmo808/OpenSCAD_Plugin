import os
import subprocess
import tempfile
import shutil
import json
import re
from mcp.server.fastmcp import FastMCP, Image

# Initialize the FastMCP server
mcp = FastMCP("openscad-mcp")

# Environment configurations
OPENSCAD_BINARY_PATH = os.getenv("OPENSCAD_BINARY_PATH", "/home/jules/.local/bin/openscad")
OPENSCAD_DEFAULT_TOLERANCE = float(os.getenv("OPENSCAD_DEFAULT_TOLERANCE", "0.05"))

def get_openscad_binary() -> str:
    """Detects and returns the path to the OpenSCAD executable."""
    binary = os.getenv("OPENSCAD_BINARY_PATH", OPENSCAD_BINARY_PATH)
    if os.path.exists(binary) and os.access(binary, os.X_OK):
        return binary
    
    # Try finding in system PATH
    system_bin = shutil.which("openscad") or shutil.which("openscad-nightly")
    if system_bin:
        return system_bin
        
    raise FileNotFoundError(
        f"OpenSCAD binary not found at '{binary}' and was not found in system PATH. "
        "Please install OpenSCAD or configure the OPENSCAD_BINARY_PATH environment variable."
    )

def validate_scad_path(path: str) -> str:
    """Validates that the file path exists and returns its absolute path."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"OpenSCAD file not found at: '{path}'")
    return os.path.abspath(path)

def run_openscad(args: list) -> subprocess.CompletedProcess:
    """Executes the OpenSCAD binary with the given arguments."""
    openscad_bin = get_openscad_binary()
    cmd = [openscad_bin] + args
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

@mcp.tool()
def generate_scad(scad_code: str, output_path: str, parameters: dict = None) -> str:
    """Writes or modifies an OpenSCAD (.scad) source code file, incorporating mechanical parameters.

    Args:
        scad_code: The complete OpenSCAD source code body.
        output_path: Local path where the .scad file should be written.
        parameters: Optional dictionary of key-value design parameters (e.g. tolerances, dimensions)
                    to be prepended as variable definitions in the OpenSCAD file.

    Returns:
        A success message indicating the write location and injected parameters.
    """
    # Validate that we are not writing empty code or code with obvious placeholders
    if not scad_code.strip():
        raise ValueError("Cannot write empty OpenSCAD code.")
    
    # Prepend parameters if provided
    prepended_lines = []
    if parameters:
        for key, val in parameters.items():
            # Basic sanitization of keys
            safe_key = "".join(c for c in key if c.isalnum() or c == "_")
            if not safe_key:
                continue
            
            # Format value correctly for OpenSCAD
            if isinstance(val, str):
                prepended_lines.append(f'{safe_key} = "{val}";')
            elif isinstance(val, bool):
                prepended_lines.append(f'{safe_key} = {"true" if val else "false"};')
            elif isinstance(val, (int, float)):
                prepended_lines.append(f'{safe_key} = {val};')
            elif isinstance(val, list):
                # Ensure the list converts to OpenSCAD syntax
                prepended_lines.append(f'{safe_key} = {json.dumps(val)};')
            else:
                # Fallback to string representation
                prepended_lines.append(f'{safe_key} = "{val}";')
                
    if prepended_lines:
        scad_code = "\n".join(prepended_lines) + "\n\n" + scad_code

    # Ensure parent directories exist
    parent_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(parent_dir, exist_ok=True)

    with open(output_path, "w") as f:
        f.write(scad_code)

    injected = ", ".join(parameters.keys()) if parameters else "None"
    return f"Successfully generated OpenSCAD file at '{output_path}'. Injected parameters: {injected}."

@mcp.tool()
def compile_and_preview(
    scad_path: str,
    output_dir: str = None,
    img_size: int = 512,
    projection: str = "ortho",
    colorscheme: str = "Sunset",
    views: list = None
) -> list:
    """Compiles an OpenSCAD model and renders orthogonal or perspective views to preview PNGs.
    The rendered images are returned directly in the response payload.

    Args:
        scad_path: Absolute or relative path to the source .scad file.
        output_dir: Directory where the preview PNG files will be written. Defaults to /tmp/openscad_previews.
        img_size: Resolution (width and height) of the rendered square PNG preview. Defaults to 512.
        projection: Camera projection type: 'ortho' (default) or 'perspective'.
        colorscheme: Color palette to apply to the render. Defaults to 'Sunset'.
        views: List of view angles to render. Defaults to ['isometric', 'top', 'front'].
               Allowed views: 'isometric', 'top', 'front', 'right', 'bottom', 'back'.

    Returns:
        A list containing a text explanation and the base64-encoded Image content parts.
    """
    validate_scad_path(scad_path)

    if not output_dir:
        output_dir = os.path.expanduser("~/.openscad_previews")
        
    os.makedirs(output_dir, exist_ok=True)

    if not views:
        views = ["isometric", "top", "front"]

    # Map standardized view names to --camera parameter:
    # Format: translate_x,y,z,rot_x,y,z,dist (dist=0 with viewall & autocenter fits the viewport)
    camera_presets = {
        "isometric": "0,0,0,55,0,45,0",
        "top": "0,0,0,0,0,0,0",
        "front": "0,0,0,90,0,0,0",
        "right": "0,0,0,90,0,90,0",
        "bottom": "0,0,0,180,0,0,0",
        "back": "0,0,0,90,0,180,0"
    }

    projection_flag = "o" if projection.lower().startswith("o") else "p"
    scad_basename = os.path.splitext(os.path.basename(scad_path))[0]
    
    results = []
    rendered_info = []

    for view in views:
        view_lower = view.lower().strip()
        if view_lower not in camera_presets:
            continue
            
        camera_args = camera_presets[view_lower]
        preview_filename = f"{scad_basename}_{view_lower}.png"
        preview_path = os.path.join(output_dir, preview_filename)
        
        # Build command args (excluding binary path since run_openscad prepends it)
        cmd_args = [
            "-o", preview_path,
            "--imgsize", f"{img_size},{img_size}",
            "--projection", projection_flag,
            "--colorscheme", colorscheme,
            "--autocenter",
            "--viewall",
            f"--camera={camera_args}",
            scad_path
        ]
        
        try:
            process = run_openscad(cmd_args)
            if os.path.exists(preview_path):
                with open(preview_path, "rb") as f:
                    img_bytes = f.read()
                
                # Create Image wrapper and convert to MCP image content representation
                img_content = Image(data=img_bytes, format="png").to_image_content()
                results.append(img_content)
                rendered_info.append(f"{view_lower} (saved to {preview_path})")
            else:
                rendered_info.append(f"{view_lower} (failed to generate file)")
        except subprocess.CalledProcessError as e:
            rendered_info.append(f"{view_lower} (error: {e.stderr.strip()})")

    summary_text = f"Compiled '{scad_path}' and generated {len(results)} views: {', '.join(rendered_info)}."
    text_content = {"type": "text", "text": summary_text}
    
    # Prepend the text description followed by the image payloads
    return [text_content] + results

@mcp.tool()
def export_stl(scad_path: str, output_path: str) -> str:
    """Compiles the final OpenSCAD geometry and exports it into a 3D-printable STL file.

    Args:
        scad_path: Path to the validated .scad source file.
        output_path: Path where the output .stl file should be saved.

    Returns:
        A success message with the file location and size details.
    """
    validate_scad_path(scad_path)

    # Ensure parent directory of the output file exists
    parent_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(parent_dir, exist_ok=True)

    cmd_args = [
        "-o", output_path,
        scad_path
    ]

    try:
        process = run_openscad(cmd_args)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"OpenSCAD export failed:\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")

    if not os.path.exists(output_path):
        raise RuntimeError(f"Export finished but the output STL file '{output_path}' was not found.")

    size_bytes = os.path.getsize(output_path)
    size_kb = size_bytes / 1024.0
    
    return f"Successfully exported 3D geometry to STL at '{output_path}' ({size_kb:.2f} KB)."

def discover_parts(scad_path: str) -> list[str]:
    """Parses the SCAD file to find all part selector names."""
    with open(scad_path, "r") as f:
        content = f.read()
    # Match patterns like: part == "side_panel" or part=="back_panel"
    matches = re.findall(r'part\s*==\s*["\']([^"\']+)["\']', content)
    parts = []
    for m in matches:
        if m != "all" and m not in parts:
            parts.append(m)
    return parts

def get_dxf_bbox(dxf_path: str) -> tuple[float, float]:
    """Computes the width and height of a 2D DXF file by parsing vertex coordinates."""
    if not os.path.exists(dxf_path):
        return 0.0, 0.0
    with open(dxf_path, 'r') as f:
        lines = f.read().splitlines()
    xs = []
    ys = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == '10' and i + 1 < len(lines):
            try:
                xs.append(float(lines[i+1].strip()))
            except ValueError:
                pass
        elif stripped == '20' and i + 1 < len(lines):
            try:
                ys.append(float(lines[i+1].strip()))
            except ValueError:
                pass
    if xs and ys:
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        return round(width, 2), round(height, 2)
    return 0.0, 0.0

def get_svg_bbox(svg_path: str) -> tuple[float, float]:
    """Computes the width and height of an SVG file by parsing width/height attributes."""
    if not os.path.exists(svg_path):
        return 0.0, 0.0
    with open(svg_path, 'r') as f:
        content = f.read()
    svg_match = re.search(r'<svg[^>]+>', content)
    if svg_match:
        tag = svg_match.group(0)
        width_m = re.search(r'width="([^"]+)"', tag)
        height_m = re.search(r'height="([^"]+)"', tag)
        if width_m and height_m:
            w_str = re.sub(r'[a-zA-Z]+', '', width_m.group(1))
            h_str = re.sub(r'[a-zA-Z]+', '', height_m.group(1))
            try:
                return round(float(w_str), 2), round(float(h_str), 2)
            except ValueError:
                pass
    return 0.0, 0.0

@mcp.tool()
def export_2d_templates(
    scad_path: str,
    output_dir: str,
    part_name: str = None,
    format: str = "both"
) -> list:
    """Extracts individual panels from a 3D OpenSCAD assembly and exports them as flat 2D DXF/SVG vector files.

    Args:
        scad_path: Path to the source .scad file.
        output_dir: Directory where DXF/SVG files will be written.
        part_name: Optional name of a specific part/module to export. If omitted, exports all discovered parts.
        format: Output format — 'dxf', 'svg', or 'both'.

    Returns:
        A list containing a text explanation and a JSON string of the exported files and metadata.
    """
    validate_scad_path(scad_path)
    os.makedirs(output_dir, exist_ok=True)

    # Determine parts to export
    if part_name:
        parts_to_export = [part_name]
    else:
        parts_to_export = discover_parts(scad_path)

    if not parts_to_export:
        return [
            {"type": "text", "text": "No parts discovered or specified for export."},
            {"type": "text", "text": "[]"}
        ]

    # Resolve formats
    fmt = format.lower().strip()
    formats_to_export = []
    if fmt == "both":
        formats_to_export = ["dxf", "svg"]
    elif fmt in ["dxf", "svg"]:
        formats_to_export = [fmt]
    else:
        raise ValueError(f"Invalid format '{format}'. Supported formats: 'dxf', 'svg', 'both'.")

    exported_files = []
    rendered_info = []

    for part in parts_to_export:
        for ext in formats_to_export:
            filename = f"{part}.{ext}"
            file_path = os.path.abspath(os.path.join(output_dir, filename))
            
            cmd_args = [
                "-D", f'part="{part}"',
                "-o", file_path,
                scad_path
            ]
            
            try:
                run_openscad(cmd_args)
                
                # Extract dimensions
                if ext == "dxf":
                    width, height = get_dxf_bbox(file_path)
                else:
                    width, height = get_svg_bbox(file_path)
                    
                exported_files.append({
                    "part_name": part,
                    "format": ext,
                    "file_path": file_path,
                    "width_mm": width,
                    "height_mm": height
                })
                rendered_info.append(f"{part}.{ext} ({width}x{height} mm)")
            except Exception as e:
                rendered_info.append(f"{part}.{ext} (failed: {str(e)})")

    summary_text = f"Exported 2D templates to '{output_dir}': {', '.join(rendered_info)}."
    text_content = {"type": "text", "text": summary_text}
    json_content = {"type": "text", "text": json.dumps(exported_files, indent=2)}
    
    return [text_content, json_content]

if __name__ == "__main__":
    mcp.run()
