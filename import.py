import bpy
import bmesh
import struct
import math


model_header_size = 24
class model_header:
    unk1 = 0                # 0x00, 4bytes
    signature = ""          # 0x04, 8bytes
    unk2 = 0                # 0x0C, 2bytes
    unk3 = 0                # 0x0E, 2bytes
    something = 0           # 0x10, 4bytes
    vert_byte_length = 0    # 0x14, 4bytes

model_vertex_size = 24
class model_vertex:
    x = 0.0     # 0x00, float
    y = 0.0     # 0x04, float
    z = 0.0     # 0x08, float
    n_x = 0.0   # 0x0C, uint
    n_y = 0.0   # 0x10, uint
    uv_x = 0.0  # 0x14, float16
    uv_y = 0.0  # 0x16, float16


class model_mesh_unk:
    unk1 = 0 # uint
    unk2 = 0 # uint
    unk3 = 0 # uint
    unk4 = 0 # uint, larger number? flags?

class model_mesh_part:
    label = ""
    first_vert_index = 0
    last_vert_index = 0 
    indices_offset = 0 
    triangles_count = 0
    coord_stuff = []
    _first_vert_index = 0
    _indices_offset = 0
    vert_count = 0
class model_mesh:
    name = "" # 0x00, 66bytes
    unk_count = 0
    unkers = []
    part_count = 0
    parts = []

def read_model_mesh(f):
    f.read(4) # this int is unknown for now
    meshes_count = read_uint(f)
    meshes = []
    for i in range(0, meshes_count):
        mesh = model_mesh()
        mesh.name = read_string(f)
        mesh.unk_count = read_uint(f)
        for js in range(0, mesh.unk_count):
            unker = model_mesh_unk()
            unker.unk1 = read_uint(f)
            unker.unk2 = read_uint(f)
            unker.unk3 = read_uint(f)
            unker.unk4 = read_uint(f)
            mesh.unkers.append(unker)

        mesh.part_count = read_uint(f)
        for js in range(0, mesh.part_count):
            part = model_mesh_part()
            part.label = read_string(f)
            part.first_vert_index = read_uint(f)
            part.last_vert_index = read_uint(f)
            part.indices_offset = read_uint(f)
            part.triangles_count = read_uint(f)
            part.coord_stuff = f.read(64)
            part._first_vert_index = read_uint(f)
            part._indices_offset = read_uint(f)
            part.vert_count = read_uint(f)
            mesh.parts.append(part)

        meshes.append(mesh)
    return meshes


# shorthand functions
def read(f, len): 
    result = bytearray(f.read(len))
    result.reverse()
    #print(result)
    #print(f.read(len))
    #print(type(f.read(len)))
    return result

def read_uint(f):   return struct.unpack('I', read(f, 4))[0]
def read_int(f):    return struct.unpack('i', read(f, 4))[0]
def read_ushort(f): return struct.unpack('H', read(f, 2))[0]
def read_short(f):  return struct.unpack('h', read(f, 2))[0]
def read_ubyte(f):  return struct.unpack('B', read(f, 1))[0]
def read_byte(f):   return struct.unpack('b', read(f, 1))[0]

def read_float(f): return struct.unpack('f', read(f, 4))[0]
def read_float16(f): return struct.unpack('e', read(f, 2))[0]

def read_norm(f): 
    read_value = read_uint(f)

    #thing = (read_value / 4294967295.0)  * (360)
    thing = (((read_value / 4294967295.0) * 2.0) - 1.0) * (math.pi*2)
    #if (thing > math.pi*1) and (thing < math.pi*3):
    #    thing = 0.0 # (math.pi*2) - thing

    return thing
    return (((read_uint(f) / 4294967295) * 2.0) - 1.0) * (math.pi*2)
    #return (read_int(f) / 2147483647.5) * (math.pi*2)

def read_string(f): 
    result = bytearray()
    curr_byte = f.read(1)
    while curr_byte != b'\x00':
        result += curr_byte
        curr_byte = f.read(1)
    return result.decode('utf-8')

def read_fixed_string(f, length):
    return f.read(length).decode('utf-8')


def read_model_header(f):
    header = model_header()
    header.unk1 = read_int(f)
    header.signature = read_string(f)
    header.unk2 = read_short(f)
    header.unk3 = read_short(f)
    return header


def read_model_indices(f):
    # read indices
    indicies_byte_length = read_uint(f)
    indicies_width = read_uint(f)
    indicies_byte_length //= indicies_width
    indices = []
    if indicies_width == 4: # 4 byte width indices
        for i in range(0, indicies_byte_length):
            indices.append(read_uint(f))
    elif indicies_width == 2: # 2 byte wide indices
        for i in range(0, indicies_byte_length):
            indices.append(read_ushort(f))
    else: raise Exception("bad vert indices byte width")
    return indices

def read_some_data(context, filepath, use_some_setting):
    print("running read_some_data...")
    f = open(filepath, mode="rb")
    header = read_model_header(f)

    vert_something = read_int(f)
    vert_byte_length = read_int(f)
    # read verts
    vert_count = vert_byte_length // model_vertex_size
    verts = []
    for i in range(0, vert_count):
        vert = model_vertex()
        vert.x = read_float(f)
        vert.y = read_float(f)
        vert.z = read_float(f)

        vert.n_x = read_norm(f)
        vert.n_y = read_norm(f)

        vert.uv_x = read_float16(f)
        vert.uv_y = read_float16(f)
        verts.append(vert)
    
    # read indices
    indices = read_model_indices(f)
    # read objects
    meshes = read_model_mesh(f)

    # now we can load all this into blender
    for mesh in meshes:
        bpy_mesh = bpy.data.meshes.new("myMesh")
        obj = bpy.data.objects.new(mesh.name, bpy_mesh)
        bpy.context.collection.objects.link(obj)

        # gather local verts
        blender_verts = []
        blender_UVs = []
        blender_normals = []
        for i in range(mesh.first_vert_index, mesh.last_vert_index+1):
            vert = verts[i]
            blender_verts.append((vert.x, vert.y, vert.z))
            blender_UVs.append((vert.uv_x, vert.uv_y))

            yaw = vert.n_y
            pitch = vert.n_x
            x = math.cos(yaw)*math.cos(pitch)
            y = math.sin(yaw)*math.cos(pitch)
            z = math.sin(pitch)
            blender_normals.append((x, y, z)) 

        # gather all the indices together
        blender_indices = []
        for i in range(0, mesh.triangles_count):
            index = (i*3)+mesh.indices_offset
            blender_indices.append((indices[index]-mesh.first_vert_index, indices[index+1]-mesh.first_vert_index, indices[index+2]-mesh.first_vert_index))

        bpy_mesh.from_pydata(blender_verts, [], blender_indices)
        
        # no idea what this does, bing gave me this
        uv_layer = bpy_mesh.uv_layers.new()
        bpy_mesh.uv_layers.active = uv_layer
        for face in bpy_mesh.polygons:
            for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                uv_layer.data[loop_idx].uv = blender_UVs[vert_idx]
        
        # no idea if this actually works, bing also gave me this
        normals2 = []
        for l in bpy_mesh.loops:
            normals2.append(blender_normals[l.vertex_index])
        # Set the custom split normals for the mesh
        bpy_mesh.normals_split_custom_set(normals2)
        bpy_mesh.use_auto_smooth = True


    return {'FINISHED'}

class bone_data:
    unk_uint = 0
    float_unk1 = 0
    float_unk2 = 0
    float_unk3 = 0
    float_unk4 = 0 # typically 1.0
    float_unk5 = 0 # typically 1.0
    float_unk6 = 0 # typically 1.0
    float_unk7 = 0 # typically 1.0
    uint_flags = 0
    pos_x = 0
    pos_y = 0
    pos_z = 0


model_vertex_size = 32
class bone_vertex:
    x = 0.0     # 0x00, float
    y = 0.0     # 0x04, float
    z = 0.0     # 0x08, float
    n_x = 0.0   # 0x0C, uint
    n_y = 0.0   # 0x10, uint
    uv_x = 0.0  # 0x14, float16
    uv_y = 0.0  # 0x16, float16
    bone_weights = 0 # 0x18, uint
    bone_indices = 0 # 0x1C, uint


def read_some_rigged_data(context, filepath, use_some_setting):
    print("running read_some_data...")
    f = open(filepath, mode="rb")
    header = read_model_header(f)

    bone_count = read_uint(f)
    bone_names = []
    for i in range(0, bone_count):
        curr_bone = read_fixed_string(f, 32)
        bone_names.append(curr_bone)
    
    bone_parents = []
    for i in range(0, bone_count):
        bone_parents.append(read_int(f)) # first will be -1 for the base bone
    
    bone_unknown_index1 = read_uint(f)
    bone_unknown_index2 = read_uint(f)
    bone_unknown_index3 = read_uint(f) 

    # then read the bone orientation things
    bone_orientations = []
    for i in range(0, bone_count):
        orientation = bone_data()
        orientation.unk_uint = read_uint(f)
        orientation.float_unk1 = read_float(f)
        orientation.float_unk2 = read_float(f)
        orientation.float_unk3 = read_float(f)
        orientation.float_unk4 = read_float(f)
        orientation.float_unk5 = read_float(f)
        orientation.float_unk6 = read_float(f)
        orientation.float_unk7 = read_float(f)
        orientation.uint_flags = read_uint(f)
        orientation.pos_x = read_float(f)
        orientation.pos_y = read_float(f)
        orientation.pos_z = read_float(f)
        bone_orientations.append(orientation)
    
    # then theres a buncha random junk here (5 position floats)
    unk_pos1 = read_float(f)
    unk_pos2 = read_float(f)
    unk_pos3 = read_float(f)
    unk_pos4 = read_float(f)
    unk_pos5 = read_float(f)

    # then read the vertices
    vert_something = read_int(f)
    vert_byte_length = read_int(f)
    # read verts
    vert_count = vert_byte_length // model_vertex_size
    verts = []
    for i in range(0, vert_count):
        vert = bone_vertex()
        vert.x = read_float(f)
        vert.y = read_float(f)
        vert.z = read_float(f)
        vert.n_x = read_norm(f)
        vert.n_y = read_norm(f)
        vert.uv_x = read_float16(f)
        vert.uv_y = read_float16(f)
        vert.bone_weights = read_uint(f)
        vert.bone_indices = read_uint(f)
        verts.append(vert)

    # read indices
    indices = read_model_indices(f)
    # read objects
    meshes = read_model_mesh(f)

    print(len(verts))
    print(len(indices))
    print(len(meshes))
    print(len(meshes[0].parts))

    # now we can load all this into blender
    for mesh in meshes:

        for part in mesh.parts:
            #part_mat = bpy.data.materials.new(name=part.label)
            #obj.data.materials.append(part_mat)
            bpy_mesh = bpy.data.meshes.new("myMesh")
            obj = bpy.data.objects.new(mesh.name + "_" + part.label, bpy_mesh)
            bpy.context.collection.objects.link(obj)

            # gather local verts
            blender_verts = []
            blender_UVs = []
            blender_normals = []
            for i in range(part.first_vert_index, part.last_vert_index+1):
                vert = verts[i]
                blender_verts.append((vert.x, vert.y, vert.z))
                blender_UVs.append((vert.uv_x, vert.uv_y))
                blender_normals.append((math.cos(vert.n_y)*math.cos(vert.n_x), math.sin(vert.n_y)*math.cos(vert.n_x), math.sin(vert.n_x))) 

            # gather all the indices together
            blender_indices = []
            for i in range(0, part.triangles_count):
                index = (i*3)+part.indices_offset
                blender_indices.append((indices[index]-part.first_vert_index, indices[index+1]-part.first_vert_index, indices[index+2]-part.first_vert_index))

            bpy_mesh.from_pydata(blender_verts, [], blender_indices)
            
            print("exporting mesh")

            #########  EXTRA JUNK ########
            # no idea what this does, bing gave me this
            uv_layer = bpy_mesh.uv_layers.new()
            bpy_mesh.uv_layers.active = uv_layer
            for face in bpy_mesh.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    uv_layer.data[loop_idx].uv = blender_UVs[vert_idx]
            # no idea if this actually works, bing also gave me this
            normals2 = []
            for l in bpy_mesh.loops:
                normals2.append(blender_normals[l.vertex_index])
            # Set the custom split normals for the mesh
            bpy_mesh.normals_split_custom_set(normals2)
            bpy_mesh.use_auto_smooth = True

    
    return {'FINISHED'}





# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ImportSomeData(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_test.some_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Some Data"

    # ImportHelper mix-in class uses this.
    filename_ext = ".txt"

    filter_glob: StringProperty(
        default="*.dat",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting: BoolProperty(
        name="Example Boolean",
        description="Example Tooltip",
        default=True,
    )

    type: EnumProperty(
        name="Example Enum",
        description="Choose between two items",
        items=(
            ('OPT_A', "First Option", "Description one"),
            ('OPT_B', "Second Option", "Description two"),
        ),
        default='OPT_A',
    )

    def execute(self, context):
        return read_some_rigged_data(context, self.filepath, self.use_setting)


# Only needed if you want to add into a dynamic menu.
def menu_func_import(self, context):
    self.layout.operator(ImportSomeData.bl_idname, text="Text Import Operator")


# Register and add to the "file selector" menu (required to use F3 search "Text Import Operator" for quick access).
def register():
    bpy.utils.register_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_test.some_data('INVOKE_DEFAULT')
