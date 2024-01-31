import bpy
import struct


model_header_size = 0x18
class model_header:
    unk1 = 0                # 0x00, 4bytes
    signature = []          # 0x04, 8bytes
    unk2 = 0                # 0x0C, 2bytes
    unk3 = 0                # 0x0E, 2bytes
    something = 0           # 0x10, 4bytes
    vert_byte_length = 0    # 0x14, 4bytes

model_vertex_size = 0x18
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

# shorthand functions
def read_uint(reader): return struct.unpack('I', reader.read(4).reverse())
def read_int(reader): return struct.unpack('i', reader.read(4).reverse())
def read_ushort(reader): return struct.unpack('H', reader.read(2).reverse())
def read_short(reader): return struct.unpack('h', reader.read(2).reverse())
def read_ubyte(reader): return struct.unpack('B', reader.read(1).reverse())
def read_byte(reader): return struct.unpack('b', reader.read(1).reverse())

def read_float(reader): return struct.unpack('f', reader.read(4).reverse())
def read_float16(reader): return struct.unpack('e', reader.read(4).reverse())

def read_float_ushort(reader): return ((65535.0 / read_ushort(reader)) * 2.0) - 1.0

def read_some_data(context, filepath, use_some_setting):
    print("running read_some_data...")
    f = open(filepath, 'r', encoding='utf-8')
    #data = f.read()
    #f.close()

    # read model header
    header = model_header()
    header.unk1 = read_int(f)
    header.signature = f.read(8)
    header.unk2 = read_short(f)
    header.unk3 = read_short(f)
    header.something = read_int(f)
    header.vert_byte_length = read_int(f)
    
    # read verts
    vert_count = header.vert_byte_length / model_vertex_size
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
        vert.uv_x = read_float16(f)
        verts.append(vert)
    
    # read indices
    f.read(4) # this int is unknown for now
    indicies_byte_length = read_int(f)
    indices = []
    if header.unk1 == 3: # 4 byte width indices
        for i in range(0, indicies_byte_length):
            indices.append(read_uint(f))
    else: # 2 byte wide indices
        for i in range(0, indicies_byte_length):
            indices.append(read_ushort(f))
    
    # read into objects
    

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
        default="*.txt",
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
