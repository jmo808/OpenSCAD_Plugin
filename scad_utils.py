import re

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
