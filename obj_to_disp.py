# To be replaced by tools in snake-biscuits/QtPyHammer & BlendHammer
import itertools
import vector

# remember default .obj orientation is +Y-UP -Z-FORWARD
# orientation is not specified in the file
# assuming +Z-UP +Y-FOWARD for now
def obj_indexed_vertices(filepath):
    """positions only"""
    file = open(filepath)
    v  = []
    vertex_count = 0
    vertices = []
    indices = []
    for line in file.readlines():
        line = line.rstrip('\n')
        if line.startswith('v'):
            v.append([float(f) for f in line.split(' ')[1:]])
        elif line.startswith('f'):
            line = line.split(' ')[1:]
            if len(line) == 4: #QUADS ONLY! for neighbour map
                for point in line:
                    vertex = v[int(point.split('/')[0]) - 1]
                    vertex = vector.vec3(*vertex)
                    if vertex not in vertices:
                        vertices.append(vertex)
                        indices.append(vertex_count)
                        vertex_count += 1
                    else:
                        indices.append(vertices.index(vertex))
    file.close()
    return vertices, indices

def obj_grouped_objects(filepath):
    """positions & groupings only"""
    file = open(filepath)
    g = ['group0'] # (name, object_name1, ...)
    groups = []
    o = ['object0', 0, 0] # (name, start, end)
    objects = {} #{name: (start, end)}
    v = []
    vertices = []
    indices = []
    for line in file.readlines():
        line = line[:-1]
        if line.startswith('g'):
            groups.append(g)
            g = [' '.join(line.split()[1:])]
        elif line.startwith('o'):
            objects[o[0]] = o[1:]
            o = [' '.join(line.split()[1:]), o[2] + 1, 0]
            g.append(o[0])
        elif line.startswith('v'):
            v.append([float(f) for f in line.split(' ')[1:]])
        elif line.startswith('f'):
            line = line.split(' ')[1:]
            if len(line) == 4: #QUADS ONLY! for neighbour map
                for point in line:
                    vertex = v[int(point.split('/')[0]) - 1]
                    vertex = vector.vec3(*vertex)
                    if vertex not in vertices:
                        vertices.append(vertex)
                        indices.append(vertex_count)
                        vertex_count += 1
                    else:
                        indices.append(vertices.index(vertex))
                    o[2] += 1
    return vertices, indices, objects, groups


def get_street(start, neighbourhood, n_filter=lambda x: True): # for edges
        """a street is a sequence of neighbours\nneighbourhood map must index points"""
        out = start # expecting the first two neighbours of the street
        good_neighbour = lambda x: x not in out and n_filter(x)
        while True:
            neighbours = neighbourhood[out[-1]]
            next_neighbour = [*filter(good_neighbour, neighbours)]
            if len(next_neighbour) == 1:
                out += next_neighbour
            else:
                break
        return out


def get_paralell_street(start, adjacent_street, neighbourhood): # no user filter
    """a street is a sequence of neighbours\nneighbourhood map must index points"""
    out = start
    for other_neighbour in adjacent_street[1:]:
        good_neighbour = lambda x: x in neighbourhood[other_neighbour] and x not in adjacent_street
        neighbours = neighbourhood[out[-1]]
        next_neighbour = [*filter(good_neighbour, neighbours)]
        out.append(next_neighbour[0])
    return out


def quads_to_rows(vertices, indices):
    neighbourhood = {i: set() for i, x in enumerate(vertices)} #a map that tells you who your neighbours are
    for i, index in enumerate(indices[::4]):
        i *= 4
        quad = [index, indices[i + 1], indices[i + 2], indices[i + 3]]
        for i, point in enumerate(quad):
            neighbourhood[point].add(quad[i - 1])
            neighbourhood[point].add(quad[i + 1 if i != 3 else 0])
    corners = [*filter(lambda i: len(neighbourhood[i]) == 2, neighbourhood)]
    edges = [*filter(lambda i: len(neighbourhood[i]) == 3, neighbourhood)]

    is_edge = lambda point: point in edges
    end_corner = lambda street: [*filter(lambda neighbour: neighbour in corners, neighbourhood[street[-1]])][0]

    A = corners[0]
    A_edge_neighbours = [*filter(is_edge, neighbourhood[A])]
    AB = get_street([A, A_edge_neighbours[0]], neighbourhood, n_filter=is_edge)
    B = end_corner(AB)
    AB.append(B)

    AD = get_street([A, A_edge_neighbours[1]], neighbourhood, n_filter=is_edge)
    D = end_corner(AD)
    AD.append(D)

    rows = [AB]
    for start in AD[1:]:
        # good neighbour is neighbour of rows[-1][i + 1]
        row = get_paralell_street([start], rows[-1], neighbourhood)
        rows.append(row)
    return rows


def change_direction(rows):
    out = [[]] * len(rows)
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            out[j][i] = value
    return out

def rotate(rows, times):
    """rotates rows 90 degrees CW * times"""
    times = times % 4
    # 90
    # A[0][0] = [0][-1]
    # B[0][-1] = [-1][-1]
    # C[-1][-1] = [-1][0]
    # D[-1][0] = [0][0]
    # 180
    # rows = reversed(rows) # flip y
    # for i, row in enumerate(rows):
    #   rows[i] = row(reversed) # flip x

def generate_solid(rows):
    """create a sensibly placed solid and inject displacement"""
    # remember .obj faces are rotated CCW
    A = rows[0][0]
    B = rows[0][-1]
    C = rows[-1][-1]
    D = rows[-1][0]

    ABC = ((A - B) * (C - B)).normalise()
    CDB = ((C - D) * (B - D)).normalise()
    N = ABC + CDB / 2

    dominant_axis = [1 if x abs(x) == max(abs(y) for y in N) else 0 for x in N]
    if N.index([i for i, x in enumerate(dominant_axis) if i == 1]) < 0:
        dominant_axis = -dominant_axis

    solid = {"id": "0", "sides": [], "editor": {
                 "color": "255 0 255", "visgroupshown": "1",
                 "visgroupautoshown": "1"}}

    # other_side = {"material": "TOOLS/TOOLSNODRAW"}

    side_id = 1
    disp_side = {"material": "DEV/DEV_BLENDMEASURE"}
    #disp_side["dispinfo"] = str(side_id)
    #side_id += 1
    #disp_side["dispinfo"] = {"flags": "0", "subdiv": "0", "elevation": "0"}
    #disp_side["dispinfo"]["power"] = 2 or 3
    #disp_side["dispinfo"]["startposition"] = "[X.XX Y.YY Z.ZZ]" # A on Grid
    # calc x, y, z from dominant axis
    # get bounds of A, B, C & D
    # snap A, B & C to GRID (2^x integers)
    # consider UVs (AB & AC to texvecs)
    #disp_side["plane"] = "(X Y Z) (X Y Z) (X Y Z)"
    #solid["sides"].append(disp_side)
    # extrude other 5 faces back from disp by grid_size units
    # final face is reversed disp A B & C
    # ENSURE DISPLACEMENT IS ALWAYS SIDE 0
    

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '../')
    import vmf_tool
    ### INJECTS DISPLACEMENT DATA INTO A DISPLACEMENT MADE IN HAMMER ###
    vertices, indices = obj_indexed_vertices("power2_disp_quads.obj")
    rows = quads_to_rows(vertices, indices)
    # make rows relative to barymetric coords
    # indices > vertices > vectors
    A = vector.vec3(*vertices[rows[0][0]])
    B = vector.vec3(*vertices[rows[0][-1]])
    C = vector.vec3(*vertices[rows[-1][-1]])
    D = vector.vec3(*vertices[rows[-1][0]])
    AD = D - A
    BC = C - B
    vector_rows = []
    # rows are nice and easy to split!
    # use vector.lerp for boundaries between disps of different powers
    for x, row in enumerate(rows): 
        x = x / 4 # assuming power 2
        vector_rows.append([])
        for y, index in enumerate(row):
            y = y / 4 # assuming power 2
            bary_point = vector.lerp(A + (AD * x), B + (BC * x), y)
            point = vertices[index] - bary_point
            vector_rows[-1].append(point)

    with open("../mapsrc/test_disp.vmf") as target_file:
        base_vmf = vmf_tool.parse_lines(target_file.readlines())
    scope = vmf_tool.scope(["world", "solid", "sides", 0, "dispinfo"])
    # ^ solid 0, side 0
    scope.add("startposition")
    dispinfo.set_in(base_vmf, f"[{A.x} {A.y} {A.z}]")
    scope.retreat()
    for i, row in enumerate(vector_rows):
        row_distances = [v.magnitude() for v in row] # 1 per vert
        row_normals = [v / w if w != 0 else vector.vec3() for v, w in zip(row, row_distances)] # 3 per vert
        row_normals = [*map(lambda v: f"{v}", row_normals)]
        row_distances = [*map(str, row_distances)]
        scope.add("distances")
        scope.add(f"row{i}")
        dispinfo.set_in(base_vmf, " ".join(row_distances))
        scope.retreat()
        scope.retreat()
        scope.add("normals")
        scope.add(f"row{i}")
        scope.set_in(base_vmf, " ".join(row_normals))
        scope.retreat()
        scope.retreat()

    with open("objs/power2_obj.vmf", "w") as out_file:
        vmf_tool.export(base_vmf, out_file)
