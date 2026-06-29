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
        with pytest.raises(RuntimeError):
            run_openscad(["-o", output_path, "nonexistent.scad"])
    except FileNotFoundError:
        pass

def test_export_2d_templates_single(sample_scad_file, local_tmp_path):
    from server import export_2d_templates
    import json
    
    output_dir = os.path.join(local_tmp_path, "export_single")
    try:
        res = export_2d_templates(sample_scad_file, part_name="side_panel", output_dir=output_dir, format="both")
        assert len(res) == 2
        assert "side_panel" in res[0]["text"]
        
        data = json.loads(res[1]["text"])
        assert len(data) == 2  # one DXF, one SVG
        assert data[0]["part_name"] == "side_panel"
        assert data[0]["format"] in ["dxf", "svg"]
        assert os.path.exists(data[0]["file_path"])
        # Dimensions for side_panel: cube([10, 50, 100]); => 2D projection width=10, height=50 or 50, 100 depending on view,
        # but projection() flat XY of cube([10, 50, 100]) is 10 x 50.
        assert data[0]["width_mm"] > 0
        assert data[0]["height_mm"] > 0
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")

def test_export_2d_templates_all(sample_scad_file, local_tmp_path):
    from server import export_2d_templates
    import json
    
    output_dir = os.path.join(local_tmp_path, "export_all")
    try:
        res = export_2d_templates(sample_scad_file, output_dir=output_dir, format="dxf")
        assert len(res) == 2
        
        data = json.loads(res[1]["text"])
        # side_panel and back_panel should be discovered and exported
        parts = [d["part_name"] for d in data]
        assert "side_panel" in parts
        assert "back_panel" in parts
        assert all(d["format"] == "dxf" for d in data)
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")

def test_export_2d_templates_missing_file():
    from server import export_2d_templates
    with pytest.raises(FileNotFoundError):
        export_2d_templates("nonexistent.scad", output_dir="out")

def test_add_dimensions(sample_scad_file, local_tmp_path):
    from server import add_dimensions, get_dxf_bbox, get_svg_bbox
    import json
    
    output_dxf = os.path.join(local_tmp_path, "dim_output.dxf")
    output_svg = os.path.join(local_tmp_path, "dim_output.svg")
    
    try:
        # 1. Export in DXF
        res_dxf = add_dimensions(sample_scad_file, part_name="side_panel", output_path=output_dxf, units="mm", offset=15.0)
        assert "dim_output.dxf" in res_dxf
        assert os.path.exists(output_dxf)
        
        # Verify the dimensions of the output dxf
        # Original side_panel is 10 x 50. With 15mm offset in X and Y, the new bbox width/height should be larger
        w_dxf, h_dxf = get_dxf_bbox(output_dxf)
        assert w_dxf > 10 + 10  # original 10 + offset margin
        assert h_dxf > 50 + 10  # original 50 + offset margin
        
        # 2. Export in SVG
        res_svg = add_dimensions(sample_scad_file, part_name="side_panel", output_path=output_svg, units="inches", offset=10.0)
        assert "dim_output.svg" in res_svg
        assert os.path.exists(output_svg)
        
        w_svg, h_svg = get_svg_bbox(output_svg)
        assert w_svg > 10 + 5
        assert h_svg > 50 + 5
        
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")

def test_add_dimensions_missing_file():
    from server import add_dimensions
    with pytest.raises(FileNotFoundError):
        add_dimensions("nonexistent.scad", "side_panel", "out.dxf")

def test_generate_multiview(sample_scad_file, local_tmp_path):
    from server import generate_multiview
    from PIL import Image as PILImage
    
    output_png = os.path.join(local_tmp_path, "multiview.png")
    try:
        res = generate_multiview(sample_scad_file, output_path=output_png, img_size=200)
        assert len(res) == 2
        assert "multiview" in res[0]["text"]
        assert res[1].type == "image"
        
        assert os.path.exists(output_png)
        with PILImage.open(output_png) as img:
            assert img.size == (200, 200)
            
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")

def test_generate_multiview_missing_file():
    from server import generate_multiview
    with pytest.raises(FileNotFoundError):
        generate_multiview("nonexistent.scad", "out.png")




