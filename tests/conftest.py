import pytest
import os
import shutil

@pytest.fixture(scope="session", autouse=True)
def test_temp_dir():
    # Create a local test_temp directory inside the project root
    # since Flatpak OpenSCAD can't access /tmp
    temp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test_temp"))
    os.makedirs(temp_dir, exist_ok=True)
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

@pytest.fixture
def local_tmp_path(test_temp_dir):
    # Unique subdirectory per test
    import uuid
    path = os.path.join(test_temp_dir, str(uuid.uuid4()))
    os.makedirs(path, exist_ok=True)
    yield path
    if os.path.exists(path):
        shutil.rmtree(path)

@pytest.fixture
def sample_scad_content():
    return """
// Simple test SCAD file
part = "all";

module side_panel() {
    cube([10, 50, 100]);
}

module back_panel() {
    cube([200, 10, 100]);
}

if (part == "side_panel") {
    projection() side_panel();
} else if (part == "back_panel") {
    // Project and rotate back panel flat to XY plane
    projection() rotate([90, 0, 0]) back_panel();
} else {
    side_panel();
    translate([0, 60, 0]) back_panel();
}
"""

@pytest.fixture
def sample_scad_file(local_tmp_path, sample_scad_content):
    scad_file = os.path.join(local_tmp_path, "test_model.scad")
    with open(scad_file, "w") as f:
        f.write(sample_scad_content)
    return scad_file
