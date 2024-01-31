import bpy
import bmesh
import struct
import math
# stolen
def quaternion_to_euler_angle(w, x, y, z):
    ysqr = y * y

    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + ysqr)
    X = math.degrees(math.atan2(t0, t1))

    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    Y = math.degrees(math.asin(t2))

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (ysqr + z * z)
    Z = math.degrees(math.atan2(t3, t4))

    return X, Y, Z


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
    n_x = 0.0   # 0x0C, ushort?
    n_y = 0.0   # 0x0E, ushort?
    n_z = 0.0   # 0x10, ushort?
    n_w = 0.0   # 0x12, ushort?
    uv_x = 0.0  # 0x14, float16
    uv_y = 0.0  # 0x16, float16


class model_mesh:
    name = "" # 0x00, 66bytes
    unk4byters = [] # 0x04, 72 bytes
    # unk1 = 0 # 0x42, 4bytes
    # unk2 = 0 # 0x46, 4bytes
    # unk3 = 0 # 0x4A, 4bytes
    # unk4 = 0 # 0x4E, 4bytes
    # unk5 = 0 # 0x52, 4bytes
    # unk6 = 0 # 0x56, 4bytes
    # unk8 = 0 # 0x5A, 4bytes
    # unk9 = 0 # 0x5E, 4bytes
    # unk10 = 0 # 0x62, 4bytes
    # unk11 = 0 # 0x66, 4bytes
    # unk12 = 0 # 0x6A, 4bytes
    # unk13 = 0 # 0x6E, 4bytes
    # unk14 = 0 # 0x72, 4bytes
    # unk15 = 0 # 0x76, 4bytes
    # unk16 = 0 # 0x7A, 4bytes
    # unk17 = 0 # 0x7E, 4bytes
    # unk18 = 0 # 0x82, 4bytes
    # unk19 = 0 # 0x86, 4bytes
    label = "" # 0x8A, 10bytes
    indices_offset = 0 # 0x94, 4bytes
    last_indices_offset = 0 # 0x98, 4bytes
    unk_offset = 0 # 0x9C, 4bytes
    unk_count = 0 # 0xA0, 4bytes
    coord_stuff = [] # 0xA4, 64bytes
    _indices_offset = 0 # 0xE4, 4bytes
    _unk_offset = 0 # 0xE8, 4bytes
    indices_count = 0 # 0xEC, 4bytes


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

def read_float_ushort(f): return ((read_ushort(f) / 65535.0) * 2.0) - 1.0

def read_string(f): 
    result = bytearray()
    curr_byte = f.read(1)
    while curr_byte != b'\x00':
        result += curr_byte
        curr_byte = f.read(1)
    return result.decode('utf-8')

def read_some_data(context, filepath, use_some_setting):
    print("running read_some_data...")
    f = open(filepath, mode="rb")
    #f.close()

    # read model header
    header = model_header()
    header.unk1 = read_int(f)
    header.signature = read_string(f)
    header.unk2 = read_short(f)
    header.unk3 = read_short(f)
    header.something = read_int(f)
    header.vert_byte_length = read_int(f)
    # read verts
    vert_count = header.vert_byte_length // model_vertex_size
    verts = []
    for i in range(0, vert_count):
        vert = model_vertex()
        vert.x = read_float(f)
        vert.y = read_float(f)
        vert.z = read_float(f)
        vert.n_x = read_float_ushort(f)
        vert.n_y = read_float_ushort(f)
        vert.n_z = read_float_ushort(f)
        vert.n_w = read_float_ushort(f)
        vert.uv_x = read_float16(f)
        vert.uv_y = read_float16(f)
        verts.append(vert)
    
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
    
    # read into objects
    f.read(4) # this int is unknown for now
    meshes_count = read_uint(f)
    meshes = []


    # debug
    print(meshes_count)
    print(len(verts))
    print(len(indices))

    for i in range(0, meshes_count):
        mesh = model_mesh()
        mesh.name = read_string(f)
        mesh.unk4byters = f.read(72)
        mesh.label = read_string(f)
        mesh.indices_offset = read_uint(f)
        mesh.last_indices_offset = read_uint(f)
        mesh.unk_offset = read_uint(f)
        mesh.unk_count = read_uint(f)
        mesh.coord_stuff = f.read(64)
        mesh._indices_offset = read_uint(f)
        mesh._unk_offset = read_uint(f)
        mesh.indices_count = read_uint(f)
        meshes.append(mesh)

    # generate the verts into a compatible format
    blender_verts = []
    blender_UVs = []
    blender_normals = []
    for vert in verts:
        blender_verts.append((vert.x, vert.y, vert.z))
        blender_UVs.append((vert.uv_x, vert.uv_y))
        blender_normals.append((quaternion_to_euler_angle(vert.n_w, vert.n_x, vert.n_y, vert.n_z)))

    # # testing whole thing
    # bpy_mesh = bpy.data.meshes.new("myMesh")
    # obj = bpy.data.objects.new(mesh.name, bpy_mesh)
    # bpy.context.collection.objects.link(obj)

    # blender_indices = []
    # for i in range(0, (len(indices)) //3):
    #     index = i*3
    #     blender_indices.append((indices[index], indices[index+1], indices[index+2]))
    
    # bpy_mesh.from_pydata(blender_verts, [], blender_indices)
    
    # uv_layer = bpy_mesh.uv_layers.new()
    # bpy_mesh.uv_layers.active = uv_layer
    # for face in bpy_mesh.polygons:
    #     for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
    #         uv_layer.data[loop_idx].uv = blender_UVs[vert_idx]

    # return {'FINISHED'}

    # now we can load all this into blender
    for mesh in meshes:
        bpy_mesh = bpy.data.meshes.new("myMesh")
        obj = bpy.data.objects.new(mesh.name, bpy_mesh)
        bpy.context.collection.objects.link(obj)
        # gather all the indices together
        blender_indices = []
        try:
            for i in range(0, mesh.unk_count):
                index = (i*3)+mesh.unk_offset
                blender_indices.append((indices[index], indices[index+1], indices[index+2]))
        except:
            print("mc error")
            print(i)
            print(index)
            print(len(indices))
            
            # label = "" # 0x8A, 10bytes
            # indices_offset = 0 # 0x94, 4bytes
            # last_indices_offset = 0 # 0x98, 4bytes
            # unk_offset = 0 # 0x9C, 4bytes
            # coord_stuff = [] # 0xA0, 68bytes
            # _indices_offset = 0 # 0xE4, 4bytes
            # _unk_offset = 0 # 0xE8, 4bytes
            # indices_count = 0 # 0xEC, 4bytes
            print(mesh.name)
            print(mesh.label)
            print(mesh.indices_offset)
            print(mesh.last_indices_offset)
            print(mesh._indices_offset)
            print(mesh._unk_offset)
            print(mesh.indices_count)
            raise

        bpy_mesh.from_pydata(blender_verts, [], blender_indices)
        
        uv_layer = bpy_mesh.uv_layers.new()
        bpy_mesh.uv_layers.active = uv_layer
        for face in bpy_mesh.polygons:
            for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                uv_layer.data[loop_idx].uv = blender_UVs[vert_idx]


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
        return read_some_data(context, self.filepath, self.use_setting)


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
