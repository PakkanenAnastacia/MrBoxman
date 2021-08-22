"""
add custom properties to selected
"""
import bpy
import numpy as np
import math
from bpy.types import Operator
from bpy.types import Panel
from mathutils import Euler

from .boxmanclasses import BoxmanPrefixes, BoxmanProperties, BoxmanOrientations, BoxmanDTO, BoxmanJointTypes, \
     NotABoxmanException, standard_except_operation, load_boxman_from_object, show_message_box
from .boxmancommon import BoxmanNamingException, add_mesh, add_property_to_object, apply_parenting_array, \
     check_for_object_mode, check_selected_object, force_parent_reset, ObjectIsNotRootException

# import sys
# sys.modules["boxmanclasses"] = bpy.data.texts["boxmanclasses.py"].as_module()
# sys.modules["boxmancommon"] = bpy.data.texts["boxmancommon.py"].as_module()
# from boxmanclasses import *
# from boxmancommon import *


def find_root_mesh(context, target_object):
    """
    Checks the parenting chain and returns the absolute root of the target object
    """
    if target_object.parent is None:
        return target_object
    else:
        return find_root_mesh(context, target_object.parent)


def mirror_from_center(context, target_object):
    """
    Mirrors the selected mesh, Center oriented not extends to the children, unless the children are also
    center oriented.
    """
    obj_parent = target_object
    obj_parent.select_set(True)
    context.view_layer.objects.active = obj_parent
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.symmetrize(direction="POSITIVE_Y")
    bpy.ops.object.mode_set(mode="OBJECT")
    obj_parent.select_set(False)
    context.view_layer.objects.active = None

    # Mirrors the centered chains
    if len(obj_parent.children) > 0:
        for child in obj_parent.children:
            if child[BoxmanProperties.PROP_ORIENTATION] == BoxmanOrientations.C:
                mirror_from_center(context, child)


def mirror_on_axis(context, parenting_chain, target: BoxmanDTO):
    """
    Mirrors a boxman chain by recursive duplication.
    """
    mirror_vertex = []
    for vert in target.vertex_list:
        mirror_vertex.append((vert[0], -vert[1], vert[2]))
    for polygon in target.polygon_list:
        polygon.reverse()  # This is needed for the polygon orientations

    ret = add_mesh(context, target.get_object_name(), mirror_vertex, target.polygon_list)
    ret.location.x = target.location[0]
    ret.location.y = -target.location[1]
    ret.location.z = target.location[2]

    for child in target.children:
        cc = mirror_on_axis(context, parenting_chain, child)
        parenting_chain.append([ret, cc])

    ret.rotation_euler = Euler((target.rotations[0][0],
                                target.rotations[0][1],
                                target.rotations[0][2]),
                               target.rotations[1])
    ret.scale = target.scale
    ret.rotation_euler.x = -ret.rotation_euler.x
    ret.rotation_euler.z = -ret.rotation_euler.z

    add_property_to_object(ret, target.properties)
    return ret


def mirror_boxman(context, selected_object, target: BoxmanDTO):
    """
    Branches the mirror function depending the orientation of the object.
    """
    if target.properties.orientation == BoxmanOrientations.C:
        mirror_from_center(context, selected_object)
    else:
        parenting_array = []
        target.chain_reverse_orientation()
        mirror_on_axis(context, parenting_array, target)
        apply_parenting_array(context, parenting_array)


def object_name_to_property(target_object) -> BoxmanProperties:
    """
    Uses the object name to get the boxman properties used in the conversion.
    If the object has a description, it keeps it, otherwise it replaces it.
    """
    naming = target_object.name.split(".")
    if naming[0] != BoxmanPrefixes.BOXMAN.value:
        raise BoxmanNamingException(target_object.name)

    if naming[1] not in BoxmanOrientations.list_attribute_names():
        raise BoxmanNamingException(target_object.name)

    ret = BoxmanProperties()
    ret.name = ".".join(naming[2:])
    ret.orientation = naming[1]

    if BoxmanProperties.PROP_BOXMAN_DESCRIPTION in target_object.keys():
        ret.description = target_object[BoxmanProperties.PROP_BOXMAN_DESCRIPTION]
    else:
        ret.description = ret.name

    if BoxmanProperties.PROP_JOINT_TYPE in target_object.keys(): # If it has a type, it leaves it
        ret.joint_type = target_object[BoxmanProperties.PROP_JOINT_TYPE]

    return ret


def convert_object_to_boxman(context, target_object, is_joint_root=True) -> None:
    """
    Adds boxman compatible properties to an object.
    """
    if target_object.type == "MESH":
        props = object_name_to_property(target_object)
        if is_joint_root: # overrides the joint type for the root
            props.joint_type = BoxmanJointTypes.OBJECT_ROOT.value

        add_property_to_object(target_object, props)
        for child in target_object.children:
            convert_object_to_boxman(context, child, False)
    else:
        raise NotABoxmanException()


def fill_children_array(selected_object, children_array):
    """
    Used to flatten the tree of objects
    """
    for child in selected_object.children:
        fill_children_array(child, children_array)
        children_array.append(child)


def select_all_for(context) -> None:
    """
    Selects all the linked elements to a boxman mesh.
    """
    try:
        print("Selecting all connected...")

        check_for_object_mode(context)
        selected_object = check_selected_object(context)
        ret = find_root_mesh(context, selected_object)
        bpy.ops.object.select_all(action='DESELECT')
        ret.select_set(True)
        context.view_layer.objects.active = ret

        # now, the root is selected!
        selected_root = check_selected_object(context)
        children_array = [selected_root]
        fill_children_array(selected_root, children_array)
        bpy.ops.object.select_all(action='DESELECT')
        for child in children_array:
            child.select_set(True)

        show_message_box("All selected!!")
        print("Selected!")
    except Exception as ex:
        standard_except_operation(ex)


def select_root_for(context) -> None:
    """
    Selects the root boxman mesh.
    """
    try:
        print("Selecting root connected...")

        check_for_object_mode(context)
        selected_object = check_selected_object(context)
        ret = find_root_mesh(context, selected_object)
        bpy.ops.object.select_all(action='DESELECT')
        ret.select_set(True)
        context.view_layer.objects.active = ret
        show_message_box("Root selected!!")
        print("Selected!")
    except Exception as ex:
        standard_except_operation(ex)


def chain_delete_selected(context) -> None:
    """
    Resets the parenting transformations, loads a boxman, mirrors it, and then inserts it.
    """
    try:
        print("Deleting chain...")
        check_for_object_mode(context)
        selected_object = check_selected_object(context)
        children_array = [selected_object]
        fill_children_array(selected_object, children_array)
        bpy.ops.object.select_all(action='DESELECT')
        for child in children_array:
            child.select_set(True)

        bpy.ops.object.delete(use_global=False, confirm=True)

        print("Chain deleted!")
    except Exception as ex:
        standard_except_operation(ex)


def mirror_boxman_operation(context) -> None:
    """
    Resets the parenting transformations, loads a boxman, mirrors it, and then inserts it.
    """
    try:
        print("Resetting transformations...")
        check_for_object_mode(context)
        selected_object = check_selected_object(context)
        print("Operating over: " + selected_object.name)
        force_parent_reset(context, selected_object)
        print("Loading boxman...")
        to_mirror = load_boxman_from_object(selected_object)
        print("Mirroring boxman...")
        mirror_boxman(context, selected_object, to_mirror)

        show_message_box("Mirrored boxman!")
    except Exception as ex:
        standard_except_operation(ex)


def force_reset_transforms(context) -> None:
    """
    Converts the selected mesh chain to have the boxman properties it needs to operate
    """
    try:
        print("Resetting transformations...")
        check_for_object_mode(context)
        selected_object = check_selected_object(context)
        print("Operating over: " + selected_object.name)
        force_parent_reset(context, selected_object)
        show_message_box("Transformations resetted!")
        print("Converted!")
    except Exception as ex:
        standard_except_operation(ex)


def convert_selected_to_boxman(context) -> None:
    """
    Converts the selected mesh chain to have the boxman properties it needs to operate
    """
    try:
        print("Converting to boxman...")
        check_for_object_mode(context)
        selected_object = check_selected_object(context)
        print("Operating over: " + selected_object.name)
        convert_object_to_boxman(context, selected_object)
        show_message_box("Converted to boxman object!")
        print("Converted!")
    except Exception as ex:
        standard_except_operation(ex)


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_OT_MirrorBoxman(Operator):
    # noinspection SpellCheckingInspection
    bl_idname = "mrboxman.mirror_boxman"
    bl_label = "Mirror Boxman"
    bl_description = "Mirrors the selected MrBoxman object in the X|Y plane. Resets the parenting assignations."
    bl_options = {'UNDO'}  # THIS IS TERRIBLY IMPORTANT!!!!!! O_O

    def execute(self, context):
        mirror_boxman_operation(context)
        return {'FINISHED'}


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_OT_ForceParentReboot(Operator):
    # noinspection SpellCheckingInspection
    bl_idname = "mrboxman.force_parent_reboot"
    bl_label = "Force chain parent transform"
    bl_description = "Applies parent transformations to all objects in a chain and reapplies the object " \
                     "parent relation, applying scale transforms. " \
                     "The selected object looses parenting, by mind full of that."
    bl_options = {'UNDO'}  # THIS IS TERRIBLY IMPORTANT!!!!!! O_O

    def execute(self, context):
        force_reset_transforms(context)
        return {'FINISHED'}


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_OT_ChainDeleteOperator(Operator):
    """
    This deletes a chain of objects!
    Click here to confirm.
    """
    # noinspection SpellCheckingInspection
    bl_idname = "mrboxman.chain_delete"
    bl_label = "Chain delete objects"
    bl_description = "Deletes a chain of parented objects."
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}  # THIS IS TERRIBLY IMPORTANT!!!!!! O_O

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        chain_delete_selected(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_OT_SelectRoot(Operator):
    # noinspection SpellCheckingInspection
    bl_idname = "mrboxman.select_root"
    bl_label = "Boxman select root"
    bl_description = "Selects the root of the currently selected boxman mesh."
    bl_options = {'UNDO'}  # THIS IS TERRIBLY IMPORTANT!!!!!! O_O

    def execute(self, context):
        select_root_for(context)
        return {'FINISHED'}


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_OT_SelectAll(Operator):
    # noinspection SpellCheckingInspection
    bl_idname = "mrboxman.select_all"
    bl_label = "Boxman select all"
    bl_description = "Selects all the meshes related to the boxman object"
    bl_options = {'UNDO'}  # THIS IS TERRIBLY IMPORTANT!!!!!! O_O

    def execute(self, context):
        select_all_for(context)
        return {'FINISHED'}


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_OT_ConvertOperator(Operator):
    # noinspection SpellCheckingInspection
    bl_idname = "mrboxman.convert_to_boxman"
    bl_label = "Boxman Convert selected"
    bl_description = "Converts the currently selected chain of mesh objects into boxman " \
                     "compatible objects adding the properties needed for operations." \
                     "It will also check that the naming convention is correct."
    bl_options = {'UNDO'}  # THIS IS TERRIBLY IMPORTANT!!!!!! O_O

    def execute(self, context):
        convert_selected_to_boxman(context)
        return {'FINISHED'}


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_PT_UtilsPanel(Panel):
    # noinspection SpellCheckingInspection
    bl_idname = "MRBOXMAN_PT_mrboxman_utils_panel"
    bl_label = "MrBoxman Meta Utilities"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MrBoxman"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="MrBoxman Utilities", icon="SETTINGS")
        row = layout.row()
        row.operator(MRBOXMAN_OT_ConvertOperator.bl_idname)
        row = layout.row()
        row.operator(MRBOXMAN_OT_MirrorBoxman.bl_idname)
        row = layout.row()
        row.label(text="Parenting functions", icon="SETTINGS")
        row = layout.row()
        row.operator(MRBOXMAN_OT_ForceParentReboot.bl_idname)
        row = layout.row()
        row.operator(MRBOXMAN_OT_SelectRoot.bl_idname)
        row.operator(MRBOXMAN_OT_SelectAll.bl_idname)
        row = layout.row()
        row.operator(MRBOXMAN_OT_ChainDeleteOperator.bl_idname)


classes = [MRBOXMAN_OT_ChainDeleteOperator,
           MRBOXMAN_OT_MirrorBoxman,
           MRBOXMAN_OT_SelectRoot,
           MRBOXMAN_OT_SelectAll,
           MRBOXMAN_OT_ForceParentReboot,
           MRBOXMAN_OT_ConvertOperator,
           MRBOXMAN_PT_UtilsPanel
           ]


# noinspection PyMissingOrEmptyDocstring
def register():
    for cls in classes:
        bpy.utils.register_class(cls)


# noinspection PyMissingOrEmptyDocstring
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    print("\033[H\033[J")
    register()
