import os
import subprocess
import tempfile
import shutil
import json
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

if __name__ == "__main__":
    mcp.run()
