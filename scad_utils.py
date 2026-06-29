import os
import re
import shutil
import subprocess

OPENSCAD_BINARY_PATH = os.getenv("OPENSCAD_BINARY_PATH", "/home/jules/.local/bin/openscad")

def get_openscad_binary() -> str:
    """Detects and returns the path to the OpenSCAD executable."""
    binary = os.getenv("OPENSCAD_BINARY_PATH", OPENSCAD_BINARY_PATH)
    if os.path.exists(binary) and os.access(binary, os.X_OK):
        return binary
    # Try system path
    sys_bin = shutil.which("openscad")
    if sys_bin:
        return sys_bin
    raise FileNotFoundError(
        f"OpenSCAD binary not found at '{binary}' and not available in PATH. "
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
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"OpenSCAD execution failed for command {cmd}:\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")

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

def get_dxf_bounds(dxf_path: str) -> tuple[float, float, float, float]:
    """Parses a DXF file to return (x_min, x_max, y_min, y_max)."""
    if not os.path.exists(dxf_path):
        return 0.0, 0.0, 0.0, 0.0
    with open(dxf_path, 'r') as f:
        lines = f.read().splitlines()
    xs = []
    ys = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # DXF group codes are on even-indexed lines in the splitlines list
        if i % 2 == 0:
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
        return min(xs), max(xs), min(ys), max(ys)
    return 0.0, 0.0, 0.0, 0.0

def get_dxf_bbox(dxf_path: str) -> tuple[float, float]:
    """Computes the width and height of a 2D DXF file by parsing vertex coordinates."""
    x_min, x_max, y_min, y_max = get_dxf_bounds(dxf_path)
    return round(x_max - x_min, 2), round(y_max - y_min, 2)

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

