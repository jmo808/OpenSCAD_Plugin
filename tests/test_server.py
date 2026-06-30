import os
import pytest
import json
import subprocess
import asyncio
from PIL import Image as PILImage

from server import (
    generate_scad, compile_and_preview, export_stl, get_openscad_binary,
    validate_scad_path, run_openscad, export_2d_templates, add_dimensions,
    generate_multiview, get_dxf_bbox, get_svg_bbox, mcp
)
import install


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
    path = validate_scad_path(sample_scad_file)
    assert path == sample_scad_file
    
    with pytest.raises(FileNotFoundError):
        validate_scad_path("nonexistent.scad")

def test_run_openscad(sample_scad_file, local_tmp_path):
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
    with pytest.raises(FileNotFoundError):
        export_2d_templates("nonexistent.scad", output_dir="out")

def test_add_dimensions(sample_scad_file, local_tmp_path):
    
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
    with pytest.raises(FileNotFoundError):
        add_dimensions("nonexistent.scad", "side_panel", "out.dxf")

def test_generate_multiview(sample_scad_file, local_tmp_path):
    
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
    with pytest.raises(FileNotFoundError):
        generate_multiview("nonexistent.scad", "out.png")

def test_mcp_registration():
    
    tools = asyncio.run(mcp.list_tools())
    tool_names = [t.name for t in tools]
    
    expected_tools = [
        "generate_scad",
        "compile_and_preview",
        "export_stl",
        "export_2d_templates",
        "add_dimensions",
        "generate_multiview",
        "check_interference",
        "extract_bom",
        "split_for_printing"
    ]
    for t in expected_tools:
        assert t in tool_names

def test_documentation_references():
    with open("instructions.md", "r") as f:
        content = f.read()
        
    expected_tools = [
        "generate_scad",
        "compile_and_preview",
        "export_stl",
        "export_2d_templates",
        "add_dimensions",
        "generate_multiview",
        "check_interference",
        "extract_bom"
    ]
    for t in expected_tools:
        assert t in content

def test_skill_references():
    with open("skills/openscad-mcp/SKILL.md", "r") as f:
        content = f.read()
        
    expected_tools = [
        "generate_scad",
        "compile_and_preview",
        "export_stl",
        "export_2d_templates",
        "add_dimensions",
        "generate_multiview",
        "check_interference",
        "extract_bom"
    ]
    for t in expected_tools:
        assert t in content

def test_installer(local_tmp_path, monkeypatch):
    
    mock_schema_dir = os.path.join(local_tmp_path, "schema")
    mock_plugin_dir = os.path.join(local_tmp_path, "plugin")
    
    monkeypatch.setattr(install, "SCHEMA_DIRS", [mock_schema_dir])
    monkeypatch.setattr(install, "PLUGIN_DIR", mock_plugin_dir)
    
    install.run_install()
    
    assert os.path.exists(os.path.join(mock_schema_dir, "generate_scad.json"))
    assert os.path.exists(os.path.join(mock_schema_dir, "export_2d_templates.json"))
    assert os.path.exists(os.path.join(mock_schema_dir, "check_interference.json"))
    assert os.path.exists(os.path.join(mock_schema_dir, "extract_bom.json"))
    assert os.path.exists(os.path.join(mock_plugin_dir, "plugin.json"))

def test_check_interference_tool(overlapping_scad_file, local_tmp_path):
    from server import check_interference
    
    output_png = os.path.join(local_tmp_path, "col_highlight.png")
    try:
        res = check_interference(overlapping_scad_file, fail_fast=False, output_path=output_png, img_size=200)
        assert len(res) == 3
        
        # Check text summary
        assert "collision(s) detected" in res[0]["text"]
        assert "cube_a" in res[0]["text"]
        
        # Check image base64
        assert res[1].type == "image"
        
        # Check JSON structured data
        json_data = json.loads(res[2]["text"])
        assert len(json_data) == 1
        assert json_data[0]["part_a"] == "cube_a"
        assert json_data[0]["part_b"] == "cube_b"
        assert json_data[0]["intersection_volume_mm3"] > 0
        
        assert os.path.exists(output_png)
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")

def test_check_interference_tool_clean(sample_scad_file, local_tmp_path):
    from server import check_interference
    
    output_png = os.path.join(local_tmp_path, "col_highlight_clean.png")
    try:
        res = check_interference(sample_scad_file, fail_fast=False, output_path=output_png, img_size=200)
        assert len(res) == 2  # No image rendered since no collisions
        assert "no collisions detected" in res[0]["text"]
        assert res[1]["text"] == "[]" # JSON empty list
        
        assert not os.path.exists(output_png)
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")

def test_extract_bom_tool(local_tmp_path):
    from server import extract_bom
    scad_content = """
    // BOM: M3x12 screw, qty=4, category=fastener
    /* BOM:
     *   name: M3 Nut
     *   qty: 2
     *   category: fastener
     */
    """
    scad_path = os.path.join(local_tmp_path, "annotated.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)
        
    out_dir = os.path.join(local_tmp_path, "bom_out")
    res = extract_bom(scad_path, output_dir=out_dir)
    assert len(res) == 2
    
    summary = res[0]["text"]
    assert "Found 2 hardware items" in summary or "found 2 hardware items" in summary.lower()
    assert "bom.json" in summary
    assert "bom.md" in summary
    assert "bom.csv" in summary
    
    json_data = json.loads(res[1]["text"])
    assert json_data["summary"]["total_unique_items"] == 2
    assert json_data["summary"]["total_quantity"] == 6

def test_extract_bom_tool_clean(local_tmp_path):
    from server import extract_bom
    scad_content = """
    module no_bom() { cube([10, 10, 10]); }
    """
    scad_path = os.path.join(local_tmp_path, "clean.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)
        
    out_dir = os.path.join(local_tmp_path, "bom_out_clean")
    res = extract_bom(scad_path, output_dir=out_dir)
    assert len(res) == 2
    assert "No BOM annotations found" in res[0]["text"]
    assert json.loads(res[1]["text"]) == {}

def test_extract_bom_tool_malformed(local_tmp_path):
    from server import extract_bom
    scad_content = """
    // BOM: qty=4, category=fastener
    // BOM: M3 Nut, qty=2, category=fastener
    """
    scad_path = os.path.join(local_tmp_path, "malformed.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)
        
    out_dir = os.path.join(local_tmp_path, "bom_out_malformed")
    res = extract_bom(scad_path, output_dir=out_dir)
    assert len(res) == 2
    assert "Found 1 hardware items" in res[0]["text"] or "found 1 hardware items" in res[0]["text"].lower()
    assert "warning" in res[0]["text"].lower()

def test_nest_panels_tool_optimized(sample_scad_file, local_tmp_path):
    from server import nest_panels
    output_dir = os.path.join(local_tmp_path, "nest_out")
    
    try:
        res = nest_panels(
            scad_path=sample_scad_file,
            sheet_preset="2x4",
            kerf=2.0,
            strategy="optimized",
            output_dir=output_dir
        )
        assert len(res) >= 2
        assert "Successfully nested" in res[0]["text"]
        files = os.listdir(output_dir)
        pngs = [f for f in files if f.endswith(".png")]
        assert len(pngs) >= 1
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")

def test_nest_panels_tool_simple(sample_scad_file, local_tmp_path):
    from server import nest_panels
    output_dir = os.path.join(local_tmp_path, "nest_out_simple")
    
    try:
        res = nest_panels(
            scad_path=sample_scad_file,
            sheet_width=300.0,
            sheet_height=300.0,
            kerf=1.0,
            strategy="simple",
            output_dir=output_dir
        )
        assert len(res) >= 2
        assert "Successfully nested" in res[0]["text"]
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")

def test_split_for_printing_tool_auto(local_tmp_path):
    from server import split_for_printing
    scad_content = "module large_part() { cube([150, 150, 400]); }\nlarge_part();"
    scad_path = os.path.join(local_tmp_path, "large_part.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)
        
    try:
        res = split_for_printing(
            scad_path=scad_path,
            part_name="large_part",
            bed_width=220.0,
            bed_depth=220.0,
            bed_height=250.0,
            safety_margin=10.0,
            split_axis="auto",
            joint_type="auto",
            output_dir=local_tmp_path
        )
        assert len(res) >= 2
        assert "Successfully split" in res[0]["text"]
        import json
        data = json.loads(res[1]["text"])
        assert "segments" in data
        assert len(data["segments"]) == 2
        assert data["segments"][0]["joint_type"] == "flange"
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")

def test_split_for_printing_tool_manual(local_tmp_path):
    from server import split_for_printing
    scad_content = "module large_part() { cube([150, 150, 400]); }\nlarge_part();"
    scad_path = os.path.join(local_tmp_path, "large_part.scad")
    with open(scad_path, "w") as f:
        f.write(scad_content)
        
    try:
        res = split_for_printing(
            scad_path=scad_path,
            part_name="large_part",
            split_axis="z",
            manual_coordinate=200.0,
            joint_type="dovetail",
            output_dir=local_tmp_path
        )
        assert len(res) >= 2
        import json
        data = json.loads(res[1]["text"])
        assert len(data["segments"]) == 2
        assert data["segments"][0]["joint_type"] == "dovetail"
    except FileNotFoundError:
        pytest.skip("OpenSCAD binary not found/available")








