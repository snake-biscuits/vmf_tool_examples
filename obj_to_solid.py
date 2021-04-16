nodraw = "TOOLS/TOOLSNODRAW"
skip = "TOOLS/TOOLSSKIP"
wire = "EDITOR/WIREFRAME"


def obj_solids(filepath, material=nodraw):
    """turns .obj mesh objects into .vmf solids"""
    file = open(filepath)
    v = []
    _id = 1
    brush = {"sides": [], "editor": {"color": "255 0 255", "visgroupshown": "1",
                                     "visgroupautoshown": "1"}}
    current_brush = brush.copy()
    current_brush["id"] = str(_id)
    _id += 1
    solids = []
    for line in file.readlines():
        line = line.rstrip("\n")
        if line.startswith("o"):  # new object, new brush
            if current_brush != brush.copy():
                solids.append(current_brush)
            current_brush = brush.copy()
            current_brush["id"] = str(_id)
            _id += 1
            current_brush["sides"] = []
        elif line.startswith("v"):  # vertex
            v.append([float(f) for f in line.split(" ")[1:]])
        elif line.startswith("f"):  # face (side)
            line = line.replace("\\", "/").split(" ")[1:]
            plane = []
            for point in line[:3]:
                vertex = v[int(point.split("/")[0]) - 1]
                plane.append(" ".join([str(x) for x in vertex]))
            plane = reversed(plane)
            _id += 1
            current_brush["sides"].append({
                "id": str(_id),
                "plane": f"({') ('.join(plane)})",
                "material": material,
                "uaxis": "[0 -1 0 0] 0.25",
                "vaxis": "[0 0 -1 0] 0.25",
                "rotation": "0",
                "lightmapscale": "16",
                "smoothing_groups": "0"})
    solids.append(current_brush)
    file.close()
    return solids


if __name__ == "__main__":
    import sys
    import vmf_tool  # did you run install_vmf_tool.bat?

    base = vmf_tool.Vmf("mapsrc/blank.vmf")

    for filepath in sys.argv[1:]:
        base.raw_namespace.world.solids = obj_solids(filepath)
        base.save_to_file(f"{filepath}.vmf")

    input("Success! Press Enter to Exit")
