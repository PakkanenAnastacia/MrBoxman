import traceback
import bpy
from bpy.types import Operator
from bpy.types import Panel
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.props import EnumProperty
from bpy.props import BoolProperty
import os


from .boxmancommon import check_for_object_mode, check_file_name_extension, insert_boxman, apply_parenting_array, \
    check_selected_object, replace_boxman, add_mesh
from .boxmanclasses import BoxmanFileTypes, deserialize_library, show_message_box, standard_except_operation, \
    BoxmanTemplateLibrary, IStaticDictionaryListable, ValueDescription


# import sys
# sys.modules["boxmanclasses"] = bpy.data.texts["boxmanclasses.py"].as_module()
# sys.modules["boxmancommon"] = bpy.data.texts["boxmancommon.py"].as_module()
# from boxmanclasses import *
# from boxmancommon import *


class BoxmanLibraryPanelVariables(IStaticDictionaryListable):
    """
    Module variables
    """
    BOXMAN_TEMPLATE_OBJECTS: ValueDescription = ValueDescription("BOXMAN_template_objects", "BOXMAN_template_objects")
    BOXMAN_LIBRARY_NAME: ValueDescription = ValueDescription("BOXMAN_library_name", "BOXMAN_library_name")


def initialize_combo_boxes(templates=None, library_name=None):
    """
    Initializes the combo box that shows the available meshes and templates.
    """
    template_objects = templates
    if templates is None:
        template_objects = [("NONE", "NONE", "NONE")]

    bpy.types.Scene.BOXMAN_template_objects = bpy.props.EnumProperty(
        items=template_objects,
        name="Template Objects",
        description="Boxman template meshes",
        default=None,
    )

    if library_name is None:
        bpy.types.Scene.BOXMAN_library_name = bpy.props.StringProperty(
            name="Loaded library name",
            description="MrBoxman library name",
            default="NONE",
        )
    else:
        bpy.context.scene[BoxmanLibraryPanelVariables.BOXMAN_LIBRARY_NAME.value] = library_name


def load_boxman_gizmo(context) -> None:
    """
    Loads the boxman gizmo
    """
    try:
        # I know that i can make a cleaner implementation, but it works for now
        print("Inserting gizmo...")
        vertex_list = [[-0.03996354341506958, -0.03996354341506958, -0.03996354341506958],
                       [-0.03996354341506958, -0.03996354341506958, 0.03996354341506958],
                       [-0.03996354341506958, 0.03996354341506958, -0.03996354341506958],
                       [-0.03996354341506958, 0.03996354341506958, 0.03996354341506958],
                       [0.03996354341506958, -0.03996354341506958, -0.03996354341506958],
                       [0.03996354341506958, -0.03996354341506958, 0.03996354341506958],
                       [0.03996354341506958, 0.03996354341506958, -0.03996354341506958],
                       [0.03996354341506958, 0.03996354341506958, 0.03996354341506958],
                       [-0.03996354341506958, 0.4261080026626587, -0.03996354341506958],
                       [-0.03996354341506958, 0.4261080026626587, 0.03996354341506958],
                       [0.03996354341506958, 0.4261080026626587, 0.03996354341506958],
                       [0.03996354341506958, 0.4261080026626587, -0.03996354341506958],
                       [0.4261080026626587, 0.03996354341506958, -0.03996354341506958],
                       [0.4261080026626587, 0.03996354341506958, 0.03996354341506958],
                       [0.4261080026626587, -0.03996354341506958, 0.03996354341506958],
                       [0.4261080026626587, -0.03996354341506958, -0.03996354341506958],
                       [0.03996354341506958, 0.03996354341506958, 0.4261080026626587],
                       [-0.03996354341506958, 0.03996354341506958, 0.4261080026626587],
                       [-0.03996354341506958, -0.03996354341506958, 0.4261080026626587],
                       [0.03996354341506958, -0.03996354341506958, 0.4261080026626587],
                       [0.0, 0.499206006526947, 0.0], [0.499206006526947, 0.0, 0.0],
                       [0.0, 0.0, 0.499206006526947]]
        face_list = [[0, 1, 3, 2], [10, 20, 9], [9, 20, 8], [4, 5, 1, 0], [2, 6, 4, 0], [3, 9, 8, 2],
                     [7, 10, 9, 3], [6, 11, 10, 7], [2, 8, 11, 6], [7, 13, 12, 6], [5, 14, 13, 7],
                     [4, 15, 14, 5], [6, 12, 15, 4], [3, 17, 16, 7], [1, 18, 17, 3], [5, 19, 18, 1],
                     [7, 16, 19, 5], [11, 20, 10], [8, 20, 11], [13, 21, 12], [14, 21, 13], [15, 21, 14],
                     [12, 21, 15], [17, 22, 16], [18, 22, 17], [19, 22, 18], [16, 22, 19]]
        add_mesh(context, "Gizmo", vertex_list, face_list)
        show_message_box("Gizmo inserted!!")
        print("Inserted!")
    except Exception as ex:
        standard_except_operation(ex)


def import_boxman_library(self, context, filepath: str) -> None:
    """
    Imports the selected boxman object as a template.
    """
    try:
        print("Importing library...")
        check_for_object_mode(context)
        check_file_name_extension(filepath, BoxmanFileTypes.BOXMAN_LIBRARY_TYPE.value)

        file = open(filepath, 'r')
        raw_text = file.read()
        file.close()
        lib = deserialize_library(raw_text)
        self.__class__.boxman_library = lib

        template_objects = []
        for key in lib.template_objects.keys():
            template_objects.append((key, key, f"Adds template object"
                                               f" with description '{lib.object_descriptions[key]}'"))

        initialize_combo_boxes(template_objects, lib.library_name)
        show_message_box("Library imported!!")
        print("Library imported!")
    except Exception as ex:
        standard_except_operation(ex)


def import_boxman_from_library(context, library: BoxmanTemplateLibrary, library_key: str) -> None:
    """
    Imports the selected boxman object as a template
    """
    try:
        print("Importing boxman...")
        check_for_object_mode(context)

        cursor_location = context.scene.cursor.location
        boxman_to_generate = library.get_boxman_object(library_key)
        parenting_chain = []
        ret = insert_boxman(context, parenting_chain, boxman_to_generate)
        apply_parenting_array(context, parenting_chain)
        ret.location = cursor_location

        show_message_box(f"Boxman {boxman_to_generate.properties.name} imported from the library!!")
        print("Boxman imported!")
    except Exception as ex:
        standard_except_operation(ex)


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_OT_LoadGizmo(Operator):
    # noinspection SpellCheckingInspection
    bl_idname = "mrboxman.load_gizmo"
    bl_label = "Gizmo"
    bl_description = "Loads a gizmo with the orientations for mirroring operations. Front/Left/Up"
    bl_options = {'UNDO'}  # THIS IS TERRIBLY IMPORTANT!!!!!! O_O

    def execute(self, context):
        load_boxman_gizmo(context)
        return {'FINISHED'}


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_OT_LoadTemplateLibraryOperator(Operator, ImportHelper):
    # noinspection SpellCheckingInspection
    bl_idname = "mrboxman.import_library"
    bl_label = "Import MrBoxman library"
    bl_description = "Import a MrBoxman object library from a .bxml"
    bl_options = {'UNDO'}  # THIS IS TERRIBLY IMPORTANT!!!!!! O_O

    filter_glob: StringProperty(
        default='*.bxml',
        options={'HIDDEN'}
    )
    boxman_library = None

    def execute(self, context):
        filepath = self.filepath
        import_boxman_library(self, context, filepath)
        return {'FINISHED'}


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_OT_LibraryInsertOperator(Operator):
    # noinspection SpellCheckingInspection
    bl_idname = "mrboxman.boxman_library_insert"
    bl_label = "Template insert"
    bl_description = "Inserts a MrBoxman object using one from the template library"
    bl_options = {'UNDO'}  # THIS IS TERRIBLY IMPORTANT!!!!!! O_O

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        scn = context.scene
        layout = self.layout
        layout.prop(scn, "BOXMAN_template_objects")

    def execute(self, context):
        scn = context.scene
        lib = MRBOXMAN_OT_LoadTemplateLibraryOperator.boxman_library
        if lib is None:
            show_message_box("Library is not loaded!", "Cached exception", "ERROR")
            return {'FINISHED'}
        import_boxman_from_library(context, lib, scn.BOXMAN_template_objects)
        return {'FINISHED'}


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_PT_TemplateLibraryPanel(Panel):
    # noinspection SpellCheckingInspection
    bl_idname = "MRBOXMAN_PT_TemplateLibraryPanel"
    bl_label = "MrBoxman Libraries"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MrBoxman"

    def draw(self, context):
        scn = context.scene
        layout = self.layout
        row = layout.row()
        row.label(text="MrBoxman Library", icon="NODE")
        row.operator(MRBOXMAN_OT_LoadGizmo.bl_idname)
        row = layout.row()
        row.prop(scn, BoxmanLibraryPanelVariables.BOXMAN_LIBRARY_NAME.value)
        row = layout.row()
        row.operator(MRBOXMAN_OT_LoadTemplateLibraryOperator.bl_idname)
        row = layout.row()
        row.label(text="Template operators")
        row = layout.row()
        row.operator(MRBOXMAN_OT_LibraryInsertOperator.bl_idname)


classes = [MRBOXMAN_OT_LibraryInsertOperator,
           MRBOXMAN_OT_LoadGizmo,
           MRBOXMAN_OT_LoadTemplateLibraryOperator,
           MRBOXMAN_PT_TemplateLibraryPanel
           ]


# noinspection PyMissingOrEmptyDocstring
def register():
    print("Registering...")
    initialize_combo_boxes()
    for cls in classes:
        bpy.utils.register_class(cls)


# noinspection PyMissingOrEmptyDocstring
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.BOXMAN_template_objects
    del bpy.types.Scene.BOXMAN_library_name


if __name__ == "__main__":
    print("\033[H\033[J")
    register()
