"""
These are the methods an utilities that appear in the whole addon
"""
import bpy
import os
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from mathutils import Euler

from .boxmanclasses import BoxmanProperties, BoxmanMeshDTO, BoxmanDTO, NotABoxmanException

# import sys
# sys.modules["boxmanclasses"] = bpy.data.texts["boxmanclasses.py"].as_module()
# from boxmanclasses import *


# region mesh functions
def add_mesh(context, name: str, vertices, faces=None, edges=None):
    """
    Adds a mesh to the context using the vertex and polygon information available in a BoxmanMeshDTO.
    """
    target_faces = faces
    target_edges = edges
    if faces is None:
        target_faces = []

    if edges is None:
        target_edges = []

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, target_edges, target_faces)
    return object_data_add(context, mesh)


def add_property_to_object(target_object, properties: BoxmanProperties) -> None:
    """
    Adds the boxman markers to a mesh object.
    """
    target_object[BoxmanProperties.PROP_IS_BOXMAN] = True
    target_object[BoxmanProperties.PROP_ORIENTATION] = properties.orientation
    target_object[BoxmanProperties.PROP_BOXMAN_NAME] = properties.name
    target_object[BoxmanProperties.PROP_JOINT_TYPE] = properties.joint_type
    target_object[BoxmanProperties.PROP_BOXMAN_DESCRIPTION] = properties.description


def replace_boxman(target_object, boxman: BoxmanMeshDTO):
    """
    replaces a mesh with the data ob a boxman mesh.
    """
    if target_object.get(BoxmanProperties.PROP_IS_BOXMAN) is None:
        raise NotABoxmanException()

    if boxman.properties.orientation != target_object.get(BoxmanProperties.PROP_ORIENTATION):
        raise OrientationNotMatchException()

    mesh = bpy.data.meshes.new(boxman.get_object_name())
    mesh.from_pydata(boxman.vertex_list, [], boxman.polygon_list)
    target_object.data = mesh
    return target_object


def apply_parenting_array(context, parenting_array: list):
    """
    Applies an object parenting to an array of parent/child object pointers.
    """
    for element in parenting_array:
        parent_object = element[0]
        child_object = element[1]
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = None
        context.view_layer.objects.active = parent_object
        child_object.select_set(True)
        parent_object.select_set(True)
        bpy.ops.object.parent_set(type='OBJECT')
        context.view_layer.objects.active = None
        child_object.select_set(False)
        parent_object.select_set(False)


def force_parent_reset(context, selected_object) -> None:
    """
    Takes an abject, clears the parent transformations to apply them and then reapplies parenting relations.
    """
    parenting_array = []  # this holds the parent/child pairs that I will need
    clear_parenting(context, selected_object, parenting_array)
    apply_parenting_array(context, parenting_array)


def clear_parenting(context, target_object, parenting_array) -> None:
    """
    Clears the parent relation of an object chain and applies the keep transform.
    The resulting objects are kept in a parenting array.
    """
    if target_object.parent is not None:
        # If its not a root I need to de-parent and keep.
        bpy.ops.object.select_all(action='DESELECT')
        target_object.select_set(True)
        context.view_layer.objects.active = target_object
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        target_object.select_set(False)
        context.view_layer.objects.active = None

    for child in target_object.children:
        clear_parenting(context, child, parenting_array)
        parenting_array.append([target_object, child])


def insert_boxman(context, parenting_array, boxman: BoxmanMeshDTO):
    """
    Insert a selected boxman object.
    """
    print(f"Inserting {boxman.properties.name}")
    ret = add_mesh(context, boxman.get_object_name(), vertices=boxman.vertex_list, faces=boxman.polygon_list)
    add_property_to_object(ret, boxman.properties)

    ret.location.x = boxman.location[0]
    ret.location.y = boxman.location[1]
    ret.location.z = boxman.location[2]

    if isinstance(boxman, BoxmanDTO):
        for child in boxman.children:
            child_object = insert_boxman(context, parenting_array, child)
            parenting_array.append([ret, child_object])

    ret.rotation_euler = Euler((boxman.rotations[0][0],
                                boxman.rotations[0][1],
                                boxman.rotations[0][2]),
                               boxman.rotations[1])
    ret.scale = boxman.scale
    return ret
# endregion

# region Exceptions
# TODO: This region goes in another file


class OrientationNotMatchException(Exception):
    """
    When trying to operate over a loaded boxman in witch the objects name differs its properties.
    """
    def __init__(self):
        super(OrientationNotMatchException, self).__init__(f"The orientations don't match!")


class NotATypeException(Exception):
    """
    When you select something that is not a mesh.
    """
    def __init__(self, obj_type: str):
        super(NotATypeException, self).__init__(f"This operation only makes sense in objects of type {obj_type}!")


class NotInObjectModeException(Exception):
    """
    Then the context is not in object mode.
    """
    def __init__(self):
        super(NotInObjectModeException, self).__init__("Context must be set to object mode!")


class BoxmanNamingException(Exception):
    """
    When the object does not have the nomenclature of a boxman
    """
    def __init__(self, name: str):
        super(BoxmanNamingException, self).__init__(f"Not compatible with MrBoxman naming "
                                                    f"convention! Object name '{name}'.")


class WrongFileNameException(Exception):
    """
    When trying to open a file with the wrong format.
    """
    def __init__(self):
        super(WrongFileNameException, self).__init__("Wrong file name extension!")


class NeedsObjectSelectedException(Exception):
    """
    When trying to use an operator without anything selected.
    """
    def __init__(self):
        super(NeedsObjectSelectedException, self).__init__("Needs to have something selected!")


class ObjectIsNotRootException(Exception):
    """
    When trying to call an operator over a non root
    """
    def __init__(self):
        super(ObjectIsNotRootException, self).__init__("The object must be a joint type ROOT!")


class NeedsMoreThanOneSelectionException(Exception):
    """
    When trying to call an operator that needs more than one selected mesh
    """
    def __init__(self):
        super(NeedsMoreThanOneSelectionException, self).__init__("Needs more than one selected object!")


class NameCantBeEmptyException(Exception):
    """
    When trying to use an string that cant be empty.
    """
    def __init__(self, parameter: str):
        super(NameCantBeEmptyException, self).__init__(f"String can not be empty! Parameter name '{parameter}'.")


class ValueCantBeZeroException(Exception):
    """
    When the value of something cant be null or negative
    """
    def __init__(self):
        super(ValueCantBeZeroException, self).__init__("Value canot be negative nor zero.")


# endregion

# region Standard Checks
def check_file_name_extension(file_path: str, desired: str) -> str:
    """
    Checks if the file extension matches a desired form and returns the flat filename.
    """
    head, tail = os.path.split(file_path)
    if tail.split(".")[-1] != desired:
        raise WrongFileNameException()

    return tail


def check_for_object_mode(context) -> None:
    """
    If an object is selected, it checks that the operation mode is object mode.
    """
    if not context.active_object is None:
        current_mode = bpy.context.active_object.mode
        if current_mode != "OBJECT":
            raise NotInObjectModeException()


def check_selected_object(context, obj_type="MESH"):
    """
    Checks if there is any mesh selected and outputs the last object on the selection chain
    """
    selection_obj = context.selected_objects
    if len(selection_obj) == 0:
        raise NeedsObjectSelectedException()

    if selection_obj[0].type != obj_type:
        raise NotATypeException(obj_type)

    return selection_obj[0]


def check_selected_objects_array(context, obj_type="MESH") -> list:
    """
    Checks if there is any mesh selected and outputs the last object on the selection chain
    """
    selection_obj = context.selected_objects
    if len(selection_obj) == 0:
        raise NeedsObjectSelectedException()

    for element in selection_obj:
        if element.type != obj_type:
            raise NotATypeException(obj_type)

    return selection_obj
# endregion
