import traceback
import bpy
from bpy.types import Operator
from bpy.types import Panel
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.props import EnumProperty
from bpy.props import CollectionProperty
from bpy.props import BoolProperty
import os

from bpy.props import PointerProperty
from bpy.types import PropertyGroup, Panel

from mrBoxman.boxman.boxmanriglogic import auto_rig
from .boxmancommon import check_for_object_mode, check_file_name_extension, insert_boxman, apply_parenting_array, \
    check_selected_object, replace_boxman, add_mesh, check_selected_objects_array, add_property_to_object, \
    force_parent_reset, ObjectIsNotRootException
from .boxmanclasses import BoxmanFileTypes, deserialize_library, show_message_box, standard_except_operation, \
    BoxmanTemplateLibrary, IStaticDictionaryListable, ValueDescription, BoxmanJointTypes, BoxmanExtremityTypes, \
    load_boxman_mesh_from_object, load_boxman_from_object


#
# import sys
# sys.modules["boxmanclasses"] = bpy.data.texts["boxmanclasses.py"].as_module()
# sys.modules["boxmancommon"] = bpy.data.texts["boxmancommon.py"].as_module()
# sys.modules["boxmanriglogic"] = bpy.data.texts["boxmanriglogic.py"].as_module()
# from boxmanclasses import *
# from boxmancommon import *
# from boxmanriglogic import *


class BoxmanRigPanelVariables(IStaticDictionaryListable):
    """
    Module variables
    """
    BOXMAN_JOINT_TYPES: ValueDescription = ValueDescription("BOXMAN_joint_types",
                                                            "BOXMAN_joint_types")

    BOXMAN_JOINT_GROUPS: ValueDescription = ValueDescription("BOXMAN_joint_groups",
                                                             "BOXMAN_joint_groups")


def joint_types_assign(self, context):
    """
    Sets the value of the selector based on the sub types
    """
    value = self.BOXMAN_joint_groups
    total_joints = BoxmanJointTypes.list_attribute_values()  # type: list[JointType]

    any_list = [("NONE", "NONE", "NONE")]
    if value == BoxmanExtremityTypes.ANY.value:
        any_list = [(joint_type.value, joint_type.value, joint_type.description)
                    for joint_type in total_joints]
    else:
        any_list = [(joint_type.value, joint_type.value, joint_type.description)
                    for joint_type in total_joints if joint_type.sub_class == value]
    return any_list


class BoxmanRigPanelVariablesSettings(PropertyGroup):
    """
    Property group of the selectors
    """
    BOXMAN_joint_types: bpy.props.EnumProperty(
        items=joint_types_assign,
        name="Joint type",
        description="MrBoxman joint type",
        default=None,
    )

    BOXMAN_joint_groups: bpy.props.EnumProperty(
        items=[(group_type.value, group_type.value, group_type.description) for group_type in
               BoxmanExtremityTypes.list_attribute_values()],
        name="Joint group",
        description="MrBoxman joint type group",
        default=None,
    )


def set_joint_type_value(context, selected_type: str) -> None:
    """
    Sets the joint type of a boxman converted mesh
    """
    try:
        print("Setting joint type...")
        check_for_object_mode(context)
        selected_objects = check_selected_objects_array(context)
        for selected_object in selected_objects:
            print("Operating over: " + selected_object.name)
            to_modify = load_boxman_mesh_from_object(selected_object)
            props = to_modify.properties
            if selected_type and selected_type in BoxmanJointTypes.list_attribute_names():
                props.joint_type = selected_type
            else:
                raise ValueError()
            add_property_to_object(selected_object, props)

        show_message_box("Joint type changed!")
    except Exception as ex:
        standard_except_operation(ex)


def autorig_boxman(context) -> None:
    """
    Resets the parenting transformations, loads a boxman and creates the complete rig automatically.
    """
    try:
        print("Auto rigging...")
        print("Resetting transformations...")

        check_for_object_mode(context)
        selected_object = check_selected_object(context)
        print("Operating over: " + selected_object.name)
        force_parent_reset(context, selected_object)

        to_rig = load_boxman_from_object(selected_object)
        if not to_rig.q_is_root():
            raise ObjectIsNotRootException()

        print("Rigging boxman...")
        auto_rig(context, to_rig)

        show_message_box("Auto rig complete!")
    except Exception as ex:
        standard_except_operation(ex)


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_OT_SetJointType(Operator):
    # noinspection SpellCheckingInspection
    bl_idname = "mrboxman.set_joint_type"
    bl_label = "Set joint type"
    bl_description = "Sets the correct type of joint to the selected boxman meshes."
    bl_options = {'UNDO'}  # THIS IS TERRIBLY IMPORTANT!!!!!! O_O

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        settings = context.scene.rigpanelsettings
        layout = self.layout
        layout.prop(settings, BoxmanRigPanelVariables.BOXMAN_JOINT_GROUPS.value)
        layout.prop(settings, BoxmanRigPanelVariables.BOXMAN_JOINT_TYPES.value)

    def execute(self, context):
        scn = context.scene
        arg = scn.rigpanelsettings.BOXMAN_joint_types
        set_joint_type_value(context, arg)
        return {'FINISHED'}


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_OT_AutoRigOperator(Operator):
    # noinspection SpellCheckingInspection
    bl_idname = "mrboxman.auto_rig_boxman"
    bl_label = "Auto rig MrBoxman"
    bl_description = "Applies the autorig transformation to the selected Boxman object." \
                     "Applies parent transformations (for simplicity) and generates the rig controls." \
                     "You need to select the Boxman object from the root mesh."
    bl_options = {'UNDO'}  # THIS IS TERRIBLY IMPORTANT!!!!!! O_O

    def execute(self, context):
        autorig_boxman(context)
        return {'FINISHED'}


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_PT_RigPanelPanel(Panel):
    # noinspection SpellCheckingInspection
    bl_idname = "MRBOXMAN_PT_mrboxman_rig_panel"
    bl_label = "MrBoxman Rig Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MrBoxman"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="MrBoxman AutoRig", icon="POSE_HLT")
        row = layout.row()
        row.operator(MRBOXMAN_OT_AutoRigOperator.bl_idname)
        row = layout.row()
        row.operator(MRBOXMAN_OT_SetJointType.bl_idname)


classes = [MRBOXMAN_OT_AutoRigOperator,
           MRBOXMAN_OT_SetJointType,
           MRBOXMAN_PT_RigPanelPanel,
           BoxmanRigPanelVariablesSettings
           ]


# noinspection PyMissingOrEmptyDocstring
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # noinspection SpellCheckingInspection
    bpy.types.Scene.rigpanelsettings = PointerProperty(type=BoxmanRigPanelVariablesSettings)


# noinspection PyMissingOrEmptyDocstring
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.rigpanelsettings


if __name__ == "__main__":
    print("\033[H\033[J")
    register()


