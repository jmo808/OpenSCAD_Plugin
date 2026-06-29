import os
import struct
import pytest
import tempfile
import shutil

# We will import from stl_utils, which we will implement next.
# During RED phase, this import will fail or the functions won't exist.
from stl_utils import compute_stl_volume, extract_bounding_box

# Vertices for a 10x10x10 cube
CUBE_VERTICES = [
    # Bottom (Z=0)
    ((0.0, 0.0, 0.0), (10.0, 10.0, 0.0), (10.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
    ((0.0, 0.0, 0.0), (0.0, 10.0, 0.0), (10.0, 10.0, 0.0), (0.0, 0.0, -1.0)),
    # Top (Z=10)
    ((0.0, 0.0, 10.0), (10.0, 0.0, 10.0), (10.0, 10.0, 10.0), (0.0, 0.0, 1.0)),
    ((0.0, 0.0, 10.0), (10.0, 10.0, 10.0), (0.0, 10.0, 10.0), (0.0, 0.0, 1.0)),
    # Front (Y=0)
    ((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (10.0, 0.0, 10.0), (0.0, -1.0, 0.0)),
    ((0.0, 0.0, 0.0), (10.0, 0.0, 10.0), (0.0, 0.0, 10.0), (0.0, -1.0, 0.0)),
    # Right (X=10)
    ((10.0, 0.0, 0.0), (10.0, 10.0, 0.0), (10.0, 10.0, 10.0), (1.0, 0.0, 0.0)),
    ((10.0, 0.0, 0.0), (10.0, 10.0, 10.0), (10.0, 0.0, 10.0), (1.0, 0.0, 0.0)),
    # Back (Y=10)
    ((10.0, 10.0, 0.0), (0.0, 10.0, 0.0), (0.0, 10.0, 10.0), (0.0, 1.0, 0.0)),
    ((10.0, 10.0, 0.0), (0.0, 10.0, 10.0), (10.0, 10.0, 10.0), (0.0, 1.0, 0.0)),
    # Left (X=0)
    ((0.0, 10.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 10.0), (-1.0, 0.0, 0.0)),
    ((0.0, 10.0, 0.0), (0.0, 0.0, 10.0), (0.0, 10.0, 10.0), (-1.0, 0.0, 0.0))
]

def write_binary_stl(path, triangles):
    header = b'\x00' * 80
    num_triangles = len(triangles)
    with open(path, 'wb') as f:
        f.write(header)
        f.write(struct.pack('<I', num_triangles))
        for v1, v2, v3, normal in triangles:
            # write normal (3 floats)
            f.write(struct.pack('<fff', *normal))
            # write vertices (3 floats each)
            f.write(struct.pack('<fff', *v1))
            f.write(struct.pack('<fff', *v2))
            f.write(struct.pack('<fff', *v3))
            # attribute byte count (uint16)
            f.write(struct.pack('<H', 0))

def write_ascii_stl(path, triangles):
    with open(path, 'w') as f:
        f.write("solid test_cube\n")
        for v1, v2, v3, normal in triangles:
            f.write(f"  facet normal {normal[0]} {normal[1]} {normal[2]}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {v1[0]} {v1[1]} {v1[2]}\n")
            f.write(f"      vertex {v2[0]} {v2[1]} {v2[2]}\n")
            f.write(f"      vertex {v3[0]} {v3[1]} {v3[2]}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write("endsolid test_cube\n")

@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    if os.path.exists(d):
        shutil.rmtree(d)

def test_imports():
    assert compute_stl_volume is not None
    assert extract_bounding_box is not None

def test_binary_cube_volume(temp_dir):
    stl_path = os.path.join(temp_dir, "cube_bin.stl")
    write_binary_stl(stl_path, CUBE_VERTICES)
    
    vol = compute_stl_volume(stl_path)
    # Expected volume of 10x10x10 cube is 1000.0
    assert abs(vol - 1000.0) < 1e-3

def test_ascii_cube_volume(temp_dir):
    stl_path = os.path.join(temp_dir, "cube_ascii.stl")
    write_ascii_stl(stl_path, CUBE_VERTICES)
    
    vol = compute_stl_volume(stl_path)
    assert abs(vol - 1000.0) < 1e-3

def test_empty_degenerate_stl(temp_dir):
    stl_path = os.path.join(temp_dir, "empty.stl")
    # Write a valid binary STL with 0 triangles
    write_binary_stl(stl_path, [])
    
    vol = compute_stl_volume(stl_path)
    assert vol == 0.0
    
    bbox = extract_bounding_box(stl_path)
    assert bbox == {
        "x_min": 0.0, "x_max": 0.0,
        "y_min": 0.0, "y_max": 0.0,
        "z_min": 0.0, "z_max": 0.0
    }

def test_bounding_box(temp_dir):
    stl_path = os.path.join(temp_dir, "cube.stl")
    write_binary_stl(stl_path, CUBE_VERTICES)
    
    bbox = extract_bounding_box(stl_path)
    assert bbox == {
        "x_min": 0.0, "x_max": 10.0,
        "y_min": 0.0, "y_max": 10.0,
        "z_min": 0.0, "z_max": 10.0
    }

def test_invalid_stl(temp_dir):
    stl_path = os.path.join(temp_dir, "corrupt.stl")
    with open(stl_path, "wb") as f:
        f.write(b"this is not a valid stl file at all")
        
    with pytest.raises((ValueError, RuntimeError, struct.error)):
        compute_stl_volume(stl_path)
