import bpy
import bmesh
import struct
import math
import os
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty
import mathutils
from mathutils import Matrix

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
    color = None


class model_mesh_unk:
    unk1 = 0 # uint
    unk2 = 0 # uint
    unk3 = 0 # uint
    unk4 = 0 # uint, larger number? flags?

class object_bounds:
    min_x = 0.0
    min_y = 0.0
    min_z = 0.0
    yaw = 0.0
    max_x = 0.0
    max_y = 0.0
    max_z = 0.0
    pitch = 0.0

class model_mesh_part:
    label = ""
    first_vert_index = 0
    last_vert_index = 0 
    indices_offset = 0 
    triangles_count = 0
    bounds = object_bounds()

class model_mesh:
    name = "" # 0x00, 66bytes
    unk_count = 0
    unkers = []
    part_count = 0
    parts = []
    bounds = object_bounds()
    first_vert_index = 0
    indices_offset = 0
    vert_count = 0 

class model_coord_data:
    name = ""
    unk = 0
    label = ""
    matrix_1 = 0.0
    matrix_2 = 0.0
    matrix_3 = 0.0
    matrix_4 = 0.0
    matrix_5 = 0.0
    matrix_6 = 0.0
    matrix_7 = 0.0
    matrix_8 = 0.0
    matrix_9 = 0.0
    matrix_10 = 0.0
    matrix_11 = 0.0
    matrix_12 = 0.0
    matrix_13 = 0.0
    matrix_14 = 0.0
    matrix_15 = 0.0
    matrix_16 = 0.0
    bounds = object_bounds()


def read_bounds(f):
    result = object_bounds()
    result.min_x = read_float(f)
    result.min_y = read_float(f)
    result.min_z = read_float(f)
    result.yaw   = read_float(f)
    result.max_x = read_float(f)
    result.max_y = read_float(f)
    result.max_z = read_float(f)
    result.pitch = read_float(f)
    return result

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
            part.bounds = read_bounds(f)
            mesh.parts.append(part)

        mesh.bounds = read_bounds(f)
        mesh.first_vert_index = read_uint(f)
        mesh.indices_offset = read_uint(f)
        mesh.vert_count = read_uint(f)
        meshes.append(mesh)
    return meshes

def read_model_coords(f):
    result = model_coord_data()
    #result.label     = read_string(f) # theres no way for us to read this
    result.matrix_1  = read_float(f)
    result.matrix_2  = read_float(f)
    result.matrix_3  = read_float(f)
    result.matrix_4  = read_float(f)
    result.matrix_5  = read_float(f)
    result.matrix_6  = read_float(f)
    result.matrix_7  = read_float(f)
    result.matrix_8  = read_float(f)
    result.matrix_9  = read_float(f)
    result.matrix_10 = read_float(f)
    result.matrix_11 = read_float(f)
    result.matrix_12 = read_float(f)
    result.matrix_13 = read_float(f)
    result.matrix_14 = read_float(f)
    result.matrix_15 = read_float(f)
    result.matrix_16 = read_float(f)
    result.bounds    = read_bounds(f)
    #result.unk       = read_ubyte(f) # no point in reading this data 
    #result.name      = read_string(f)
    return result # theres also seemingly a single byte that goes before this data?


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
    indices = []
    if indicies_width == 3: # 4 byte width indices
        indicies_byte_length //= 4
        for i in range(0, indicies_byte_length):
            indices.append(read_uint(f))
    elif indicies_width == 2: # 2 byte wide indices
        indicies_byte_length //= 2
        for i in range(0, indicies_byte_length):
            indices.append(read_ushort(f))
    elif indicies_width == 1: # 1 byte wide indices # UNCONFIRMED!!!!
        indicies_byte_length //= 1
        for i in range(0, indicies_byte_length):
            indices.append(read_ubyte(f))
    else: raise Exception("bad vert indices byte width")
    return indices


########## DEBUG ###########
def set_origin(obj, global_coord):
    # Get the local coordinate of the global point
    local_coord = obj.matrix_world.inverted() @ global_coord
    # Transform the mesh by the negative of the local point
    obj.data.transform(mathutils.Matrix.Translation(-local_coord))
    # Move the object by the difference of the global point and the object's location
    obj.matrix_world.translation += (global_coord - obj.matrix_world.translation)

def add_object(name,x,y,z):
    bpy_mesh = bpy.data.meshes.new("myMesh")
    obj = bpy.data.objects.new(name, bpy_mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = obj.location + mathutils.Vector((x,y,z))

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1)
    bm.to_mesh(bpy_mesh)
    bm.free()

    obj.select_set(False)



def construct_meshes(meshes, verts, indices, f, bone_count = -1, bone_names = [], bone_orientations = [], bone_parents = []):
    has_vert_color = verts[0].color != None
    bytes_offset = f.tell()
    excess_bytes = f.read() 
    
    mesh_index = 0
    for mesh in meshes:
        mesh_index += 1
        # get alternate component mesh component (cant just read there because theres too much junk in the way)
        offset = excess_bytes.find(mesh.name.encode('utf-8'))
        if offset < 0: raise Exception("failed to find position data for " + mesh.name)

        f.seek(bytes_offset + offset - 97)
        # then read that junk
        coord_data = read_model_coords(f)
        object_pos_matrix = Matrix((
            (coord_data.matrix_1,  coord_data.matrix_2,  coord_data.matrix_3,  coord_data.matrix_4 ),
            (coord_data.matrix_5,  coord_data.matrix_6,  coord_data.matrix_7,  coord_data.matrix_8 ),
            (coord_data.matrix_9,  coord_data.matrix_10, coord_data.matrix_11, coord_data.matrix_12),
            (coord_data.matrix_13, coord_data.matrix_14, coord_data.matrix_15, coord_data.matrix_16)))
        #coord_data_origin = ((coord_data.bounds.min_x+coord_data.bounds.max_x)/2, (coord_data.bounds.min_y+coord_data.bounds.max_y)/2, (coord_data.bounds.min_z+coord_data.bounds.max_z)/2)
        coord_data_origin = (coord_data.bounds.min_x, coord_data.bounds.min_y, coord_data.bounds.min_z)
        #coord_data_origin = (coord_data.bounds.max_x, coord_data.bounds.max_y, coord_data.bounds.max_z)


        add_object(str(mesh_index) +"_b_min", mesh.bounds.min_x, mesh.bounds.min_y, mesh.bounds.min_z )
        add_object(str(mesh_index) +"_b_max", mesh.bounds.max_x, mesh.bounds.max_y, mesh.bounds.max_z )
        add_object(str(mesh_index) +"_m_min", coord_data.bounds.min_x, coord_data.bounds.min_y, coord_data.bounds.min_z )
        add_object(str(mesh_index) +"_m_max", coord_data.bounds.max_x, coord_data.bounds.max_y, coord_data.bounds.max_z )

        part_index = 0
        for part in mesh.parts:
            part_index += 1
            add_object(str(mesh_index) +"_"+str(part_index)+"_min", part.bounds.min_x, part.bounds.min_y, part.bounds.min_z )
            add_object(str(mesh_index) +"_"+str(part_index)+"_max", part.bounds.max_x, part.bounds.max_y, part.bounds.max_z )

            #part_mat = bpy.data.materials.new(name=part.label)
            #obj.data.materials.append(part_mat)
            bpy_mesh = bpy.data.meshes.new("myMesh")
            obj = bpy.data.objects.new(str(mesh_index) +"_"+ str(part_index) +"_"+ mesh.name +"_"+ part.label, bpy_mesh)
            #print(mesh.name + "_" + part.label)
            bpy.context.collection.objects.link(obj)
            # set orientation (we need to set the origin point first !!!!)
            #origin = ((mesh.bounds.min_x+mesh.bounds.max_x)/2, (mesh.bounds.min_y+mesh.bounds.max_y)/2, (mesh.bounds.min_z+mesh.bounds.max_z)/2)
            origin = (mesh.bounds.min_x, mesh.bounds.min_y, mesh.bounds.min_z)
            #origin = (mesh.bounds.max_x, mesh.bounds.max_y, mesh.bounds.max_z)
            obj.matrix_world = object_pos_matrix # set world pos first, as cursor overrides this??
            #print(object_pos_matrix.to_translation())
            #print(coord_data_origin)
            #obj.location = obj.location + mathutils.Vector(origin)
            obj.location = obj.location + mathutils.Vector(coord_data_origin)
            # bpy.ops.object.mode_set(mode='OBJECT')
            # obj.select_set(True)
            # bpy.context.scene.cursor.location = mathutils.Vector(origin)
            # bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            # obj.select_set(False)
            #print(obj.location)
            #obj.matrix_world = object_pos_matrix
            #print(obj.location)
            #set_origin(obj, mathutils.Vector(((part.bounds.min_x+part.bounds.max_x)/2, (part.bounds.min_y+part.bounds.max_y)/2, (part.bounds.min_z+part.bounds.max_z)/2)))
            #bpy.context.scene.cursor.location = mathutils.Vector((part.bounds.min_x, part.bounds.min_y, part.bounds.min_z))
            #bpy.ops.object.origin_set({"object": obj}, type="ORIGIN_CURSOR")
            #obj.location = (part.bounds.min_x-part.bounds.max_x, part.bounds.min_y-part.bounds.max_y, part.bounds.min_z-part.bounds.max_z)
            #aobj.location = ((part.bounds.min_x+part.bounds.max_x)/2, (part.bounds.min_y+part.bounds.max_y)/2, (part.bounds.min_z+part.bounds.max_z)/2)
            #obj.location = (part.bounds.min_x, part.bounds.min_y, part.bounds.min_z)
            #obj.rotation_euler = (math.radians(part.bounds.pitch), math.radians(part.bounds.yaw), 0)

            # create and assign material
            mat = bpy.data.materials.get(part.label)
            if mat is None: mat = bpy.data.materials.new(part.label)
            obj.data.materials.append(mat)

            # gather local verts
            blender_verts = []
            blender_UVs = []
            blender_normals = []
            blender_vert_colors = []
            for i in range(part.first_vert_index, part.last_vert_index+1):
                vert = verts[i]
                blender_verts.append((vert.x-origin[0], vert.y-origin[1], vert.z-origin[2]))
                #blender_verts.append((vert.x-coord_data_origin[0], vert.y-coord_data_origin[1], vert.z-coord_data_origin[2]))
                #blender_verts.append((vert.x, vert.y, vert.z))
                blender_UVs.append((vert.uv_x, vert.uv_y))
                blender_normals.append((math.cos(vert.n_y)*math.cos(vert.n_x), math.sin(vert.n_y)*math.cos(vert.n_x), math.sin(vert.n_x))) 
                if has_vert_color == True: blender_vert_colors.append( ((vert.color&255)/255, ((vert.color>>8)&255)/255.0, ((vert.color>>16)&255)/255.0, (vert.color>>24)/255.0 ) )


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
            
            ####### VERT COLOR JUNK ####
            if has_vert_color == True:
                # Get the vertex color layer
                color_layer = bpy_mesh.vertex_colors.new(name="vert_colors")
                # Set the color of each vertex
                for face in bpy_mesh.polygons:
                    for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                        color_layer.data[loop_idx].color = blender_vert_colors[vert_idx]
                        #print(idx)

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

    # output debug information
    # mesh_index = 0
    # for mesh in meshes:
    #     mesh_index += 1

    #     part_index = 0
    #     for part in mesh.parts:
    #         part_index += 1





def read_static_model(context, filepath, import_as_single = False):
    print("running read_some_data...")
    f = open(filepath, mode="rb")
    header = read_model_header(f)

    vert_stride = read_int(f)
    vert_byte_length = read_int(f)
    # error checking
    has_vert_color = False
    vert_padding = vert_stride - model_vertex_size
    if vert_padding < 0: raise Exception("vertex stride is smaller than regular size (we'll lose vertex data)")
    if vert_stride >= model_vertex_size+4:
        has_vert_color = True
        vert_padding -= 4
        print("vertex colors!!!!")
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
        # if possible, do vertex colors
        if has_vert_color == True:
            vert.color = read_uint(f)

        verts.append(vert)
        # skip padding
        if vert_padding != 0: f.read(vert_padding)
    
    # read indices
    indices = read_model_indices(f)
    # read objects
    meshes = read_model_mesh(f)
    # construct
    if import_as_single:
        blender_verts = []
        blender_indices = []
        for vert in verts: blender_verts.append((vert.x, vert.y, vert.z))
        for i in range(0, len(indices)//3): blender_indices.append((indices[(i*3)], indices[(i*3)+1], indices[(i*3)+2]))
        bpy_mesh = bpy.data.meshes.new("myMesh")
        obj = bpy.data.objects.new("whole_mesh", bpy_mesh)
        bpy.context.collection.objects.link(obj)
        bpy_mesh.from_pydata(blender_verts, [], blender_indices)
    
    else:
        construct_meshes(meshes, verts, indices, f)

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
    construct_meshes(meshes, verts, indices, f, bone_count, bone_names, bone_orientations, bone_parents)
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
            ('OPT_C', "Static model (single mesh)", "Import a static model"),
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
                read_static_model(context, filepath, False)
            elif self.type == 'OPT_C':
                read_static_model(context, filepath, True)
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
