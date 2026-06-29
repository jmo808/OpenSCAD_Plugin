import os
import struct

def is_binary_stl(stl_path: str) -> bool:
    """Heuristic to determine if an STL file is binary or ASCII."""
    if not os.path.exists(stl_path):
        raise FileNotFoundError(f"STL file not found at: '{stl_path}'")
        
    file_size = os.path.getsize(stl_path)
    if file_size < 84:
        # A valid binary STL must be at least 84 bytes.
        return False
        
    with open(stl_path, 'rb') as f:
        header = f.read(80)
        num_triangles_bytes = f.read(4)
        if len(num_triangles_bytes) < 4:
            return False
        num_triangles = struct.unpack('<I', num_triangles_bytes)[0]
        
    # Standard check: does the file size match the declared number of triangles?
    if file_size == 84 + num_triangles * 50:
        return True
        
    # Fallback check: check for null bytes in the first 1024 bytes
    with open(stl_path, 'rb') as f:
        chunk = f.read(1024)
    return b'\x00' in chunk

def parse_stl(stl_path: str) -> tuple[float, dict]:
    """Parses STL file and returns (volume, bounding_box)."""
    if not os.path.exists(stl_path):
        raise FileNotFoundError(f"STL file not found at: '{stl_path}'")
        
    is_bin = is_binary_stl(stl_path)
    
    volume = 0.0
    x_coords = []
    y_coords = []
    z_coords = []
    
    if is_bin:
        with open(stl_path, 'rb') as f:
            f.seek(80)
            num_triangles_bytes = f.read(4)
            if len(num_triangles_bytes) < 4:
                raise ValueError("Corrupt binary STL: unable to read triangle count")
            num_triangles = struct.unpack('<I', num_triangles_bytes)[0]
            
            # Verify file size matches expected triangles size
            file_size = os.path.getsize(stl_path)
            if file_size < 84 + num_triangles * 50:
                raise ValueError("Corrupt binary STL: file is too small for the declared triangle count")
                
            for _ in range(num_triangles):
                data = f.read(50)
                if len(data) < 50:
                    raise ValueError("Corrupt binary STL: unexpected end of file")
                unpacked = struct.unpack('<12fH', data)
                v1 = unpacked[3:6]
                v2 = unpacked[6:9]
                v3 = unpacked[9:12]
                
                # Signed volume of tetrahedron
                v_tet = (-v3[0]*v2[1]*v1[2] + v2[0]*v3[1]*v1[2] + v3[0]*v1[1]*v2[2] - v1[0]*v3[1]*v2[2] - v2[0]*v1[1]*v3[2] + v1[0]*v2[1]*v3[2]) / 6.0
                volume += v_tet
                
                x_coords.extend([v1[0], v2[0], v3[0]])
                y_coords.extend([v1[1], v2[1], v3[1]])
                z_coords.extend([v1[2], v2[2], v3[2]])
    else:
        with open(stl_path, 'r', errors='ignore') as f:
            current_triangle = []
            has_solid = False
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                parts = stripped.split()
                if parts[0] == 'solid':
                    has_solid = True
                elif parts[0] == 'vertex':
                    if len(parts) < 4:
                        raise ValueError("Corrupt ASCII STL: malformed vertex line")
                    try:
                        v = (float(parts[1]), float(parts[2]), float(parts[3]))
                        current_triangle.append(v)
                    except ValueError:
                        raise ValueError("Corrupt ASCII STL: invalid float in vertex")
                        
                    if len(current_triangle) == 3:
                        v1, v2, v3 = current_triangle
                        v_tet = (-v3[0]*v2[1]*v1[2] + v2[0]*v3[1]*v1[2] + v3[0]*v1[1]*v2[2] - v1[0]*v3[1]*v2[2] - v2[0]*v1[1]*v3[2] + v1[0]*v2[1]*v3[2]) / 6.0
                        volume += v_tet
                        
                        x_coords.extend([v1[0], v2[0], v3[0]])
                        y_coords.extend([v1[1], v2[1], v3[1]])
                        z_coords.extend([v1[2], v2[2], v3[2]])
                        current_triangle = []
            if not has_solid and not x_coords:
                raise ValueError("Corrupt or invalid STL file format")

    if x_coords and y_coords and z_coords:
        bbox = {
            "x_min": min(x_coords), "x_max": max(x_coords),
            "y_min": min(y_coords), "y_max": max(y_coords),
            "z_min": min(z_coords), "z_max": max(z_coords)
        }
    else:
        bbox = {
            "x_min": 0.0, "x_max": 0.0,
            "y_min": 0.0, "y_max": 0.0,
            "z_min": 0.0, "z_max": 0.0
        }
        
    return abs(volume), bbox

def compute_stl_volume(stl_path: str) -> float:
    """Computes the volume of the STL mesh."""
    vol, _ = parse_stl(stl_path)
    return vol

def extract_bounding_box(stl_path: str) -> dict:
    """Extracts the bounding box of the STL mesh."""
    _, bbox = parse_stl(stl_path)
    return bbox
