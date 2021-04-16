import os

import vmf_tool

import obj_to_solid


def test_obj_to_vmf():
    base = vmf_tool.Vmf("mapsrc/blank.vmf")
    base.raw_namespace.world.solids = obj_to_solid.obj_solids("objs/hemisphere.obj")
    base.save_to_file("tests/hemisphere.vmf")

    with open("objs/hemisphere.obj") as file:
        obj_faces = [L for L in file.readlines() if L.split()[0] == "f"]

    assert os.path.exists("tests/hemisphere.vmf")
    hemisphere_vmf = vmf_tool.Vmf("tests/hemisphere.vmf")
    assert len(hemisphere_vmf.brushes[1].faces) == len(obj_faces)
    os.remove("tests/hemisphere.vmf")
