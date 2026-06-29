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
