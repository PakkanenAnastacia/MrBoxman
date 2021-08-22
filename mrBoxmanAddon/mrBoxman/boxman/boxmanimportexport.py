"""
This exports a boxman object
"""
import json

import bpy
from bpy.types import Operator
from bpy.types import Panel
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.props import StringProperty
import os

from .boxmanclasses import BoxmanFileTypes, load_boxman_from_object, StringCompressor, BoxmanTemplateLibrary, \
    deserialize_library, show_message_box, standard_except_operation, load_boxman_mesh_from_object, BoxmanPrefixes, \
    IStaticDictionaryListable, construct_boxman_from_json
from .boxmancommon import check_for_object_mode, check_selected_object, force_parent_reset, ObjectIsNotRootException, \
    check_file_name_extension, NameCantBeEmptyException, insert_boxman, apply_parenting_array


# import sys
# sys.modules["boxmanclasses"] = bpy.data.texts["boxmanclasses.py"].as_module()
# sys.modules["boxmancommon"] = bpy.data.texts["boxmancommon.py"].as_module()
# from boxmanclasses import *
# from boxmancommon import *


class BoxmanExportPanelVariables(IStaticDictionaryListable):
    """
    Module variables
    """
    BOXMAN_EXPORT_NAME: str = "BOXMAN_export_name"


def initialize_description_input() -> None:
    """
    Initializes the description of the mesh or object that is going to be exported
    """
    bpy.types.Scene.BOXMAN_export_name = bpy.props.StringProperty(
        name="Export name",
        description="Name that is displayed in de library selector",
        default=BoxmanPrefixes.BOXMAN_GENERIC_DESC.value,
    )
    return


def export_selected_boxman(context, filepath: str, export_to_library: bool = False) -> None:
    """
    Exports the selected boxman object as a template.
    """
    try:
        print("Exporting...")
        check_for_object_mode(context)
        selected_object = check_selected_object(context)
        print("Operating over : " + selected_object.name)
        print("Forcing parent reset...")
        force_parent_reset(context, selected_object)
        to_export = load_boxman_from_object(selected_object)
        export_name = context.scene[BoxmanExportPanelVariables.BOXMAN_EXPORT_NAME]
        if not bool(export_name.strip()):
            NameCantBeEmptyException(BoxmanExportPanelVariables.BOXMAN_EXPORT_NAME)

        to_export.properties.description = export_name

        # the export roots are all at 0 location
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = None

        if not export_to_library:
            print("Exporting to file!")
            tail = check_file_name_extension(filepath, BoxmanFileTypes.BOXMAN_OBJECT_TYPE.value)
            file = open(filepath, 'w', encoding='utf-8')
            to_compress = to_export.serialize()
            comp = StringCompressor.compress(to_compress)
            file.write(comp)
            file.close()
        else:
            library = BoxmanTemplateLibrary()
            print("Exporting to library!")
            tail = check_file_name_extension(filepath, BoxmanFileTypes.BOXMAN_LIBRARY_TYPE.value)
            if os.path.isfile(filepath):
                file = open(filepath, 'r', encoding='utf-8')
                serial_to_add = file.read()
                file.close()
                library = deserialize_library(serial_to_add)
            else:
                print("Creating new library!")
                library = BoxmanTemplateLibrary()
                library.library_name = tail

            to_compress = to_export.serialize()
            comp = StringCompressor.compress(to_compress)
            library.template_objects[to_export.properties.name] = comp
            library.object_descriptions[to_export.properties.name] = export_name
            file = open(filepath, "w", encoding='utf-8')
            file.write(library.serialize(False))
            file.close()

        show_message_box("Object exported!!")
        print("Object exported!!")
    except Exception as ex:
        standard_except_operation(ex)


def import_boxman_from_file(context, filepath: str) -> None:
    """
    Imports the selected boxman object as a template.
    """
    try:
        print("Importing...")
        check_for_object_mode(context)
        check_file_name_extension(filepath, BoxmanFileTypes.BOXMAN_OBJECT_TYPE.value)

        cursor_location = context.scene.cursor.location
        file = open(filepath, 'r')
        raw_text = file.read()
        file.close()
        json_text = StringCompressor.decompress(bytes.fromhex(raw_text))
        dd = json.loads(json_text)
        boxman_to_generate = construct_boxman_from_json(dd)

        parenting_chain = []
        ret = insert_boxman(context, parenting_chain, boxman_to_generate)
        apply_parenting_array(context, parenting_chain)

        ret.location = cursor_location
        show_message_box(f"Boxman {boxman_to_generate.properties.name} imported!!")
        print("Imported!")
    except Exception as ex:
        standard_except_operation(ex)


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_OT_ExportBoxmanToLibraryOperator(Operator, ExportHelper):
    # noinspection SpellCheckingInspection
    bl_idname = "mrboxman.export_object_library"
    bl_label = "Export selected MrBoxman to library"
    bl_description = "Add selected MrBoxman object to a library file. Doing so resets the transformations and " \
                     "parenting on the current object."

    filename_ext = ".bxml"  # boxmanMesh

    filter_glob: StringProperty(
        default='*.bxml',
        options={'HIDDEN'}
    )

    def execute(self, context):
        filepath = self.filepath
        export_selected_boxman(context, filepath, True)
        return {'FINISHED'}


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_OT_ExportBoxmanObjectOperator(Operator, ExportHelper):
    # noinspection SpellCheckingInspection
    bl_idname = "mrboxman.export_object"
    bl_label = "Export selected MrBoxman Object"
    bl_description = "Export selected MrBoxman Object as .bxmo. Doing so resets the transformations and " \
                     "parenting on the current object."
    filename_ext = ".bxmo"  # boxmanMesh

    filter_glob: StringProperty(
        default='*.bxmo',
        options={'HIDDEN'}
    )

    def execute(self, context):
        filepath = self.filepath
        export_selected_boxman(context, filepath)
        return {'FINISHED'}


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_OT_TemplateImportOperator(Operator, ImportHelper):
    # noinspection SpellCheckingInspection
    bl_idname = "mrboxman.import_boxman_file"
    bl_label = "Import MrBoxman from file"
    bl_description = "Imports a MrBoxman object to the scene from a file"
    bl_options = {'UNDO'}  # THIS IS TERRIBLY IMPORTANT!!!!!! O_O

    filter_glob: StringProperty(
        default='*.bxmo',
        options={'HIDDEN'}
    )

    def execute(self, context):
        filepath = self.filepath
        import_boxman_from_file(context, filepath)
        return {'FINISHED'}


# noinspection PyPep8Naming,PyMissingOrEmptyDocstring,PyMethodMayBeStatic
class MRBOXMAN_PT_ExportPanel(Panel):
    # noinspection SpellCheckingInspection
    bl_idname = "MRBOXMAN_PT_mrboxman_export_panel"
    bl_label = "MrBoxman Exports"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MrBoxman"

    def draw(self, context):
        scn = context.scene
        layout = self.layout
        row = layout.row()
        row.label(text="Import/Export boxman objects and meshes to files", icon="FILE")
        row = layout.row()
        row.operator(MRBOXMAN_OT_ExportBoxmanObjectOperator.bl_idname)
        row.operator(MRBOXMAN_OT_TemplateImportOperator.bl_idname)
        row = layout.row()
        row.label(text="Export boxman objects to libraries", icon="NODE")
        row = layout.row()
        row.prop(scn, BoxmanExportPanelVariables.BOXMAN_EXPORT_NAME)
        row = layout.row()
        row.operator(MRBOXMAN_OT_ExportBoxmanToLibraryOperator.bl_idname)


classes = [MRBOXMAN_OT_ExportBoxmanToLibraryOperator,
           MRBOXMAN_OT_ExportBoxmanObjectOperator,
           MRBOXMAN_OT_TemplateImportOperator,
           MRBOXMAN_PT_ExportPanel
           ]


# noinspection PyMissingOrEmptyDocstring
def register():
    print("Registering...")
    initialize_description_input()
    for cls in classes:
        bpy.utils.register_class(cls)


# noinspection PyMissingOrEmptyDocstring
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.BOXMAN_export_name


if __name__ == "__main__":
    print("\033[H\033[J")
    register()
