import bpy
import bmesh
import struct
import math
import os
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty

model_header_size = 24
class model_header_signature:
    signature = ""
    unk = 0
class model_header:
    sig_count = 0             
    signatures = []

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
    coord_stuff = [] # 32 bytes

class model_mesh:
    name = "" # 0x00, 66bytes
    unk_count = 0
    unkers = []
    part_count = 0
    parts = []
    coord_stuff = [] # 32 bnytes
    first_vert_index = 0
    indices_offset = 0
    vert_count = 0 

def read_model_mesh(f):
    f.read(4) # this int is unknown for now
    meshes_count = read_uint(f)
    meshes = []
    for i in range(0, meshes_count):
        mesh = model_mesh()
        mesh.name = read_string(f)
        mesh.unk_count = read_uint(f)
        mesh.unkers = []
        for js in range(0, mesh.unk_count):
            unker = model_mesh_unk()
            unker.unk1 = read_uint(f)
            unker.unk2 = read_uint(f)
            unker.unk3 = read_uint(f)
            unker.unk4 = read_uint(f)
            mesh.unkers.append(unker)

        mesh.part_count = read_uint(f)
        mesh.parts = []
        for js in range(0, mesh.part_count):
            part = model_mesh_part()
            part.label = read_string(f)
            part.first_vert_index = read_uint(f)
            part.last_vert_index = read_uint(f)
            part.indices_offset = read_uint(f)
            part.triangles_count = read_uint(f)
            part.coord_stuff = f.read(32)
            mesh.parts.append(part)

        mesh.coord_stuff = f.read(32)
        mesh.first_vert_index = read_uint(f)
        mesh.indices_offset = read_uint(f)
        mesh.vert_count = read_uint(f)
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
    header.sig_count = read_int(f)
    header.signatures = []
    for i in range(0, header.sig_count):
        sig = model_header_signature()
        sig.signature = read_string(f)
        sig.unk = read_uint(f)
        header.signatures.append(sig)
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


def construct_meshes(meshes, verts, indices, bone_count = -1, bone_names = [], bone_orientations = [], bone_parents = []):
    for mesh in meshes:
        for part in mesh.parts:
            #part_mat = bpy.data.materials.new(name=part.label)
            #obj.data.materials.append(part_mat)
            bpy_mesh = bpy.data.meshes.new("myMesh")
            obj = bpy.data.objects.new(mesh.name + "_" + part.label, bpy_mesh)
            bpy.context.collection.objects.link(obj)

            # create and assign material
            mat = bpy.data.materials.get(part.label)
            if mat is None: mat = bpy.data.materials.new(part.label)
            obj.data.materials.append(mat)

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

            ####### BONE JUNK #########
            if bone_count != -1:
                # setup bones
                arm = bpy.data.armatures.new('MyArmature')
                arm_obj = bpy.data.objects.new('MyArmature', arm)
                bpy.context.collection.objects.link(arm_obj)
                mod = obj.modifiers.new('Armature', type='ARMATURE')
                mod.object = arm_obj
                
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = arm_obj
                bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                ebs = arm.edit_bones

                # Create the bones
                bones = []
                for i in range(0, bone_count):
                    name = bone_names[i]
                    pos_data = bone_orientations[i]
                    bone = ebs.new(name)
                    bone.head = (pos_data.pos_x, pos_data.pos_y, pos_data.pos_z)
                    bone.tail = (pos_data.pos_x, pos_data.pos_y, pos_data.pos_z+1.0)
                    bones.append(bone)
                # setup parenting
                for i in range(0, bone_count):
                    parent = bone_parents[i]
                    if parent == -1: continue
                    ebs.active = bones[parent]
                    bones[i].select = True
                    bpy.ops.armature.parent_set (type='OFFSET')
                    bones[i].select = False


                # apply vertex weights
                bpy.ops.object.mode_set (mode='OBJECT')
                groups = obj.vertex_groups
                
                groups_array = []
                for i in range(0, bone_count):
                    group = groups.new(name=bone_names[i])
                    groups_array.append(group)

                for i in range(part.first_vert_index, part.last_vert_index+1):
                    vert = verts[i]
                    # bone1
                    bone1 = vert.bone_indices & 0xff
                    weight1 = (vert.bone_weights & 0x3ff) / 1023.0
                    groups_array[bone1].add([i], weight1, 'ADD')
                    # bone2
                    bone2 = (vert.bone_indices >> 8) & 0xff
                    if bone2 != bone1:
                        weight2 = ((vert.bone_weights >> 10) & 0x3ff) / 1023.0
                        groups_array[bone2].add([i], weight2, 'ADD')
                    # bone3
                    bone3 = (vert.bone_indices >> 16) & 0xff
                    if bone3 != bone2:
                        weight3 = (vert.bone_weights >> 20 & 0x1F) / 31.0
                        groups_array[bone3].add([i], weight3, 'ADD')
                    # bone4
                    bone4 = (vert.bone_indices >> 24) & 0xff
                    if bone4 != bone3:
                        weight4 = (vert.bone_weights >> 26 & 0x1F) / 31.0
                        groups_array[bone4].add([i], weight4, 'ADD')


def read_static_model(context, filepath):
    print("running read_some_data...")
    f = open(filepath, mode="rb")
    header = read_model_header(f)

    vert_stride = read_int(f)
    vert_byte_length = read_int(f)
    # error checking
    vert_padding = vert_stride - model_vertex_size
    if vert_padding < 0: raise Exception("vertex stride is smaller than regular size (we'll lose vertex data)")
    # read verts
    vert_count = vert_byte_length // vert_stride
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
        # skip padding
        if vert_padding != 0: f.read(vert_padding)
    
    # read indices
    indices = read_model_indices(f)
    # read objects
    meshes = read_model_mesh(f)
    # construct
    construct_meshes(meshes, verts, indices)

    f.close()
    return {'FINISHED'}

class bone_data:
    pos_x = 0
    pos_y = 0
    pos_z = 0
    unk_uint = 0
    float_unk1 = 0
    float_unk2 = 0
    float_unk3 = 0
    float_unk4 = 0 # typically 1.0
    float_unk5 = 0 # typically 1.0
    float_unk6 = 0 # typically 1.0
    float_unk7 = 0 # typically 1.0
    uint_flags = 0
skinned_model_vertex_size = 32
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
def read_rigged_model(context, filepath):
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
    

    # then read the bone orientation things
    bone_orientations = []
    for i in range(0, bone_count):
        orientation = bone_data()
        orientation.pos_x = read_float(f)
        orientation.pos_y = read_float(f)
        orientation.pos_z = read_float(f)
        orientation.unk_uint = read_uint(f)
        orientation.float_unk1 = read_float(f)
        orientation.float_unk2 = read_float(f)
        orientation.float_unk3 = read_float(f)
        orientation.float_unk4 = read_float(f)
        orientation.float_unk5 = read_float(f)
        orientation.float_unk6 = read_float(f)
        orientation.float_unk7 = read_float(f)
        orientation.uint_flags = read_uint(f)
        bone_orientations.append(orientation)
    
    # then theres a buncha random junk here (8 position floats)
    unk_pos1 = read_float(f)
    unk_pos2 = read_float(f)
    unk_pos3 = read_float(f) 
    unk_pos4 = read_float(f)
    unk_pos5 = read_float(f)
    unk_pos6 = read_float(f)
    unk_pos7 = read_float(f)
    unk_pos8 = read_float(f)

    vert_stride = read_int(f)
    vert_byte_length = read_int(f)
    # error checking
    vert_padding = vert_stride - skinned_model_vertex_size
    if vert_padding < 0: raise Exception("vertex stride is smaller than regular size (we'll lose vertex data)")
    # read verts
    vert_count = vert_byte_length // vert_stride
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
        # skip padding
        if vert_padding != 0: f.read(vert_padding)

    # read indices
    indices = read_model_indices(f)
    # read objects
    meshes = read_model_mesh(f)
    # now we can load all this into blender
    construct_meshes(meshes, verts, indices, bone_count, bone_names, bone_orientations, bone_parents)
    f.close()
    return {'FINISHED'}





# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ImportSomeData(Operator, ImportHelper):
    """Import model files from Hydro Thunder Hurricane"""
    bl_idname = "import_test.some_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Hydro Thunder models"
    # ImportHelper mix-in class uses this.
    #filename_ext = ".txt"
    filter_glob: StringProperty(
        default="*.dat",
        options={'HIDDEN'},
        maxlen=255,)  # Max internal buffer length, longer would be clamped.

    type: EnumProperty(
        name="Import type",
        description="Choose type of model to import",
        items=(
            ('OPT_A', "Static model", "Import a static model"),
            ('OPT_B', "Skinned model", "Import a skinned model"),
        ),
        default='OPT_A',)
    
    # Enable multiple file selection
    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},)
    # Store the folder path
    directory: StringProperty(
        subtype='DIR_PATH',)


    def execute(self, context):
        for file in self.files:
            filepath = os.path.join(self.directory, file.name)
            print(filepath)
            if self.type == 'OPT_A':
                read_static_model(context, filepath)
            elif self.type == "OPT_B":
                read_rigged_model(context, filepath)
        return {'FINISHED'}


# Only needed if you want to add into a dynamic menu.
def menu_func_import(self, context):
    self.layout.operator(ImportSomeData.bl_idname, text="Hydro Thunder Import")


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
