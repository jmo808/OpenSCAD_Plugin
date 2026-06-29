import os
import pytest
from server import generate_scad, compile_and_preview, export_stl, get_openscad_binary

def test_get_openscad_binary():
    try:
        binary = get_openscad_binary()
        assert os.path.exists(binary)
    except FileNotFoundError:
        pass

def test_generate_scad(local_tmp_path):
    output_path = os.path.join(local_tmp_path, "output.scad")
    code = "cube([10, 20, 30]);"
    params = {"thickness": 6.35, "material": "wood"}
    
    res = generate_scad(code, output_path, params)
    assert "output.scad" in res
    assert os.path.exists(output_path)
    
    with open(output_path, "r") as f:
        content = f.read()
    assert 'thickness = 6.35;' in content
    assert 'material = "wood";' in content
    assert code in content

def test_generate_scad_empty():
    with pytest.raises(ValueError):
        generate_scad("", "path.scad")

def test_compile_and_preview(sample_scad_file, local_tmp_path):
    output_dir = os.path.join(local_tmp_path, "previews")
    try:
        res = compile_and_preview(sample_scad_file, output_dir=output_dir, img_size=100, views=["isometric"])
        assert len(res) > 0
        assert "isometric" in res[0]["text"]
        assert len(res) > 1
        assert res[1].type == "image"
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")

def test_compile_and_preview_missing_file():
    with pytest.raises(FileNotFoundError):
        compile_and_preview("nonexistent_file.scad")

def test_export_stl(sample_scad_file, local_tmp_path):
    output_path = os.path.join(local_tmp_path, "output.stl")
    try:
        res = export_stl(sample_scad_file, output_path)
        assert "output.stl" in res
        assert os.path.exists(output_path)
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")

def test_export_stl_missing_file():
    with pytest.raises(FileNotFoundError):
        export_stl("nonexistent_file.scad", "output.stl")

def test_validate_scad_path(sample_scad_file):
    from server import validate_scad_path
    path = validate_scad_path(sample_scad_file)
    assert path == sample_scad_file
    
    with pytest.raises(FileNotFoundError):
        validate_scad_path("nonexistent.scad")

def test_run_openscad(sample_scad_file, local_tmp_path):
    from server import run_openscad
    import subprocess
    output_path = os.path.join(local_tmp_path, "output.stl")
    
    try:
        proc = run_openscad(["-o", output_path, sample_scad_file])
        assert isinstance(proc, subprocess.CompletedProcess)
        assert proc.returncode == 0
        assert os.path.exists(output_path)
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")

    # test failing command
    try:
        with pytest.raises(subprocess.CalledProcessError):
            run_openscad(["-o", output_path, "nonexistent.scad"])
    except FileNotFoundError:
        pass

