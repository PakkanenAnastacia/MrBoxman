"""
Contains the basic boxman DTO contracts and serialization
"""
import traceback
from typing import List

import bpy
from enum import Enum
import json
from json import JSONEncoder
import zlib
import inspect
from abc import ABC
from dataclasses import dataclass


# region DataClasses
# TODO: This region goes in another file

# noinspection PyClassHasNoInit
@dataclass
class ValueDescription:
    """
    Data contract to simplify syntax
    """
    value: str
    description: str


# noinspection PyClassHasNoInit
@dataclass
class JointType(ValueDescription):
    """
    Data contract to simplify syntax
    """
    sub_class: str


class IStaticDictionaryListable(ABC):
    """
    This interface allows to enumerate the fields in a class which are not methods. Be careful, if the
    field  starts with an '_' (like a protected field), the field wont be recovered.
    Useful for static classes that hold constant values
    """

    @classmethod
    def list_attribute_names(cls) -> list:
        """
        Lists the names of the fields
        """
        attributes = inspect.getmembers(cls,
                                        lambda a: (not (inspect.ismethod(a)) and not (inspect.isroutine(a))))
        elements = [a[0] for a in attributes if not a[0].startswith("_")]
        return elements

    @classmethod
    def list_attribute_values(cls) -> list:
        """
        Lists the values of the fields
        """
        attributes = inspect.getmembers(cls,
                                        lambda a: (not (inspect.ismethod(a)) and not (inspect.isroutine(a))))
        elements = [a[1] for a in attributes if not a[0].startswith("_")]
        return elements

    @classmethod
    def first_or_default(cls, property_value: str, default: ValueDescription) -> ValueDescription:
        """
        Gets an instance of a ValueDescription on the current class, searching the list with the value property
        on the argument.
        :param property_value:
        Key to search.
        :param default:
        Default value returned if the value is not found.
        :return:
        A ValueDescription item that matches the value argument if its found in the fields of the class or the
        default values otherwise.
        """
        attributes = cls.list_attribute_values()
        return next((a for a in attributes if a.value == property_value), default)


# endregion


# region Encoder
class BoxmanEncoder(JSONEncoder):
    """
    Tells the json serializer how to handle the boxman classes
    """
    def default(self, o):
        return o.__dict__

# endregion

# region Super Basic Exceptions
# TODO: This region goes in another file


class NotABoxmanException(Exception):
    """
    Raised when trying to operate over a mesh that can be used.
    """
    def __init__(self):
        super(NotABoxmanException).__init__("Object is not MrBoxman compatible!")


class NotInLibraryException(Exception):
    """
    When trying to use a key for an object that is not in the loaded dictionary.
    """
    def __init__(self, key: str):
        super(NotInLibraryException, self).__init__(f"The key: '{key}' is not "
                                                    f"present in the MrBoxman library!")


# endregion


# region Enums
# TODO: This region goes in another file

class BoxmanFileTypes(IStaticDictionaryListable):
    """
    Lists the constants and prefixes used in the whole addon
    """
    BOXMAN_OBJECT_TYPE: ValueDescription = ValueDescription("bxmo", "Boxman Object file type")
    BOXMAN_LIBRARY_TYPE: ValueDescription = ValueDescription("bxml", "Boxman Library file type")


class BoxmanPrefixes(IStaticDictionaryListable):
    """
    Lists the constants and prefixes used in the whole addon
    """
    BOXMAN: ValueDescription = ValueDescription("bxm", "Boxman")
    BOXMAN_GENERIC_DESC: ValueDescription = ValueDescription("bxm_obj", "BoxmanObject")


class BoxmanExtremityTypes(IStaticDictionaryListable):
    """
    Allows for grouping of the joint types in the display.
    The idea is to keep them similar to the ones in the =riggify= addon.
    """
    ANY: ValueDescription = ValueDescription("ANY",
                                             "Brings all types at once.")

    DEFAULT: ValueDescription = ValueDescription("DEFAULT",
                                                 "Default Types")

    SPINE: ValueDescription = ValueDescription("SPINE",
                                               "Controls for the spinal cord of the characters.")

    HEAD: ValueDescription = ValueDescription("HEAD",
                                              "Controls for the neck and head of the character")

    LEG: ValueDescription = ValueDescription("LEG",
                                             "Controls for the legs of the characters.")

    ARM: ValueDescription = ValueDescription("ARM",
                                             "Controls for the arms of the characters.")

    HAND: ValueDescription = ValueDescription("HAND",
                                              "Controls for the hands of the characters.")

    FEET: ValueDescription = ValueDescription("FEET",
                                              "Controls for the feet of the characters.")

    CHAIN: ValueDescription = ValueDescription("CHAIN",
                                               "Controls for chain-like extremities.")


class BoxmanJointTypes(IStaticDictionaryListable):
    """
    Types of joints to be used in the boxman rig
    """
    # region DEFAULT

    DEFAULT: JointType = JointType("DEFAULT",
                                   "Default joint, creates a round trackball bounding box controller",
                                   BoxmanExtremityTypes.DEFAULT.value)

    # endregion

    # region ROOT

    OBJECT_ROOT: JointType = JointType("OBJECT_ROOT",
                                       "Object Root joint. Origin of global transformations."
                                       "Creates a unit ring controller.",
                                       BoxmanExtremityTypes.DEFAULT.value)

    # endregion

    # region SPINE

    SPINE_ROOT: JointType = JointType("SPINE_ROOT",
                                      "Generally used for the Hips of a boxman character. Creates a "
                                      "bounding box controller. Defines a new local root.",
                                      BoxmanExtremityTypes.SPINE.value)

    SPINE_SECTION: JointType = JointType("SPINE_SECTION",
                                         "Generally used for vertebra or any middle section of the "
                                         "character. Creates a ring controller. Defines a new local root.",
                                         BoxmanExtremityTypes.SPINE.value)
    # endregion

    # region HEAD

    NECK_ROOT: JointType = JointType("NECK_ROOT",
                                     "Generally used for the base of the neck a boxman character. Creates a "
                                     "bounding box controller.",
                                     BoxmanExtremityTypes.HEAD.value)

    NECK_SECTION: JointType = JointType("NECK_SECTION",
                                        "Generally used for vertebra or any middle section of the "
                                        "character. Creates a ring controller.",
                                        BoxmanExtremityTypes.HEAD.value)

    HEAD: JointType = JointType("HEAD",
                                "Creates a proxy control with a bonding box that copies rotations.",
                                BoxmanExtremityTypes.HEAD.value)

    # endregion

    # region HAND

    FINGER_ROOT: JointType = JointType("FINGER_ROOT",
                                       "Used for the first knuckle of a finger. Creates a bounding ring "
                                       "controller.",
                                       BoxmanExtremityTypes.HAND.value)

    FINGER_SECTION: JointType = JointType("FINGER_SECTION",
                                          "Used for the second and third knuckles of a finger. Creates a bounding ring "
                                          "controller.",
                                          BoxmanExtremityTypes.HAND.value)

    HAND_ROOT: JointType = JointType("HAND_ROOT",
                                     "Used for the wrists of hand boxman. Creates a controller"
                                     "for the whole hand and marks the location of an IK handle if the joint is in the "
                                     "scan of arm chain.",
                                     BoxmanExtremityTypes.HAND.value)

    # endregion

    # region IGNORE

    ACCESSORY: JointType = JointType("ACCESSORY",
                                     "Ignored in the creation of controllers, is subjected to the control of the "
                                     "nearest non ignored parent.",
                                     BoxmanExtremityTypes.DEFAULT.value)

    # endregion

    # region ARM

    SHOULDER_ROOT: JointType = JointType("SHOULDER_ROOT",
                                         "Creates a trackball proxy controller for rotations. It NEEDS an ARM_HUMERUS "
                                         "child in order to operate.",
                                         BoxmanExtremityTypes.ARM.value)

    ARM_HUMERUS: JointType = JointType("ARM_HUMERUS",
                                       "Locate at the end of the shoulder, cover the humerus, "
                                       "its origin will be used for IK transformation."
                                       "Display is ignored.",
                                       BoxmanExtremityTypes.ARM.value)

    ARM_RADIUS: JointType = JointType("ARM_RADIUS",
                                      "Locate at the end of the humerus, "
                                      "The next bone in the chain will, will be the one with "
                                      "IK target constraints if the type matches the root of a hand of a default "
                                      "IK target effector.",
                                      BoxmanExtremityTypes.ARM.value)

    ARM_ELBOW: JointType = JointType("ARM_ELBOW",
                                     "At its location, there will be created a pole target for the arm IK if "
                                     "placed correctly at the chain, it is expected that its child of "
                                     "the radius.",
                                     BoxmanExtremityTypes.ARM.value)

    # endregion

    # region LEG

    LEG_THIGH: JointType = JointType("LEG_THIGH",
                                     "Locate at the root of the femur, its origin is used in IK calculations.",
                                     BoxmanExtremityTypes.LEG.value)

    LEG_SHIN: JointType = JointType("LEG_SHIN",
                                    "Locate at the end of the humerus, over the shin."
                                    "The next bone in the chain will, will be the one with "
                                    "IK target constraints if the type matches the root of a feet of a default "
                                    "IK target effector.",
                                    BoxmanExtremityTypes.LEG.value)

    LEG_KNEE: JointType = JointType("LEG_KNEE",
                                    "At its location, there will be created a pole target for the arm IK if "
                                    "placed correctly at the chain, it is expected that its child of "
                                    "the shin.",
                                    BoxmanExtremityTypes.LEG.value)

    # endregion

    # region FEET

    FOOT_ROOT: JointType = JointType("FOOT_ROOT",
                                     "Used for the ankles of hand boxman. Creates a controller"
                                     "for the whole hand and marks the location of an IK handle if the joint is in the "
                                     "scan of arm chain.",
                                     BoxmanExtremityTypes.FEET.value)

    TOE_ROOT: JointType = JointType("TOE_ROOT",
                                    "Used for the first knuckle of a finger. Creates a bounding ring "
                                    "controller.",
                                    BoxmanExtremityTypes.FEET.value)

    TOE_SECTION: JointType = JointType("TOE_SECTION",
                                       "Used for the second and third knuckles of a finger. Creates a bounding ring "
                                       "controller.",
                                       BoxmanExtremityTypes.FEET.value)

    # endregion

    # region CHAIN

    CHAIN_ROOT = JointType("CHAIN_ROOT",
                           "Used as origin of a chain/cable. It creates the origin of an IK controller,"
                           "the length of the IK chain is determined by the chain"
                           "of tentacle objects. To nest tentacles an intermediate object is required."
                           "It NEEDS at least one CHAIN_SEGMENT child to operate.",
                           BoxmanExtremityTypes.CHAIN.value)

    CHAIN_SEGMENT = JointType("CHAIN_SEGMENT",
                              "Segment of a chain. It inherits the chain length of the current IK"
                              "of the tentacle root. Only one tentacle segment child is allowed per segment,"
                              "if its the end of the chain of tentacle objects it creates the IK control at the "
                              "tip of the mesh. A new Root Chain can be nested to branch other chains.",
                              BoxmanExtremityTypes.CHAIN.value)

    # endregion


class BoxmanOrientations(IStaticDictionaryListable):
    """
    Lists the orientation constants used in the whole addon
    """
    L: ValueDescription = ValueDescription("L", "Left")
    R: ValueDescription = ValueDescription("R", "Right")
    C: ValueDescription = ValueDescription("C", "Center")


# endregion


class BoxmanProperties:
    """
    Properties of a boxman object
    """
    PROP_IS_BOXMAN: str = "is_boxman"
    PROP_ORIENTATION: str = "boxman_orientation"
    PROP_BOXMAN_NAME: str = "boxman_name"
    PROP_JOINT_TYPE: str = "boxman_jointType"
    PROP_BOXMAN_DESCRIPTION: str = "boxman_description"

    def __init__(self):
        self.name: str = BoxmanPrefixes.BOXMAN.value
        self.orientation: str = BoxmanOrientations.C.value
        self.joint_type: str = BoxmanJointTypes.DEFAULT.value
        self.description: str = BoxmanPrefixes.BOXMAN.value


class BoxmanMeshDTO:
    """
    Basic mesh contract form
    """
    def __init__(self):
        self.location = []
        self.scale = []
        self.rotations = []
        self.vertex_list = []
        self.polygon_list = []
        self.properties: BoxmanProperties = BoxmanProperties()

    def q_is_root(self) -> bool:
        """
        Tells if the boxman object can be used to root some transformations
        """
        return True

    def get_object_name(self) -> str:
        """
        Gets the name of the blander object that is linked to the boxman dto instance
        """
        return f"{BoxmanPrefixes.BOXMAN.value}.{self.properties.orientation}.{self.properties.name}"

    @staticmethod
    def get_object_name_from_object(cls, obj):
        """
        Uses operates over a boxman compatible object to get its correct name
        """
        if obj.get(BoxmanProperties.PROP_IS_BOXMAN) is None:
            raise NotABoxmanException()

        orientation = obj.get(BoxmanProperties.PROP_ORIENTATION)
        name = obj.get(BoxmanProperties.PROP_BOXMAN_NAME)
        return f"{BoxmanPrefixes.BOXMAN.value}.{orientation}.{name}"

    def serialize(self, minify: bool = True):
        """
        Gets a string representation of the boxman object, used for exporting.
        The Minify parameter tels if the serialization is indented or not (for readability)
        """
        if not minify:
            return json.dumps(self, indent=4, cls=BoxmanEncoder)
        else:
            return self.__str__()

    def __str__(self):
        return BoxmanEncoder().encode(self)


class BoxmanDTO(BoxmanMeshDTO):
    """
    Main DTO of the addon
    """

    def __init__(self, mesh_data: BoxmanMeshDTO = None):
        super().__init__()
        self.children: List = []
        if not mesh_data is None:
            self.location = mesh_data.location
            self.scale = mesh_data.scale
            self.rotations = mesh_data.rotations
            self.vertex_list = mesh_data.vertex_list
            self.polygon_list = mesh_data.polygon_list
            self.properties = mesh_data.properties

    def q_is_root(self) -> bool:
        """
        Tells of the current boxman object is the root of the system
        """
        root = self.properties.joint_type
        return root == BoxmanJointTypes.OBJECT_ROOT.value

    def chain_reverse_orientation(self) -> None:
        """
        Reverses the orientation property of the current instance and all its children
        """
        # take the target, get the reverse name, check if exist
        options = {
            BoxmanOrientations.L.value: BoxmanOrientations.R.value,
            BoxmanOrientations.R.value: BoxmanOrientations.L.value,
            BoxmanOrientations.C.value: BoxmanOrientations.C.value
        }

        self.properties.orientation = options[self.properties.orientation]
        for child in self.children:
            child.chain_reverse_orientation()


def load_boxman_mesh_from_object(obj) -> BoxmanMeshDTO:
    """
    Creates a boxman mesh object from a context object object.
    """
    if obj.get(BoxmanProperties.PROP_IS_BOXMAN) is None:
        raise NotABoxmanException()

    ret = BoxmanMeshDTO()
    ret.properties.name = obj[BoxmanProperties.PROP_BOXMAN_NAME]
    ret.properties.orientation = obj[BoxmanProperties.PROP_ORIENTATION]
    ret.properties.joint_type = obj[BoxmanProperties.PROP_JOINT_TYPE]
    ret.properties.description = obj[BoxmanProperties.PROP_BOXMAN_DESCRIPTION]

    # temps
    obj_location = obj.location
    obj_rotation = obj.rotation_euler
    obj_scale = obj.scale
    obj_data_vertices = obj.data.vertices
    obj_data_polygons = obj.data.polygons

    ret.location = [obj_location[0], obj_location[1], obj_location[2]]
    ret.scale = [obj_scale[0], obj_scale[1], obj_scale[2]]
    ret.rotations = [[obj_rotation.x, obj_rotation.y, obj_rotation.z], obj_rotation.order]
    ret.vertex_list = []
    ret.polygon_list = []
    for vert in obj_data_vertices:
        ret.vertex_list.append([vert.co[0], vert.co[1], vert.co[2]])
    for poly in obj_data_polygons:
        polygon = []
        for index in poly.vertices:
            polygon.append(index)
        ret.polygon_list.append(polygon)

    return ret


def load_boxman_from_object(obj) -> BoxmanDTO:
    """
    Creates a boxman dto from a context object object.
    """
    loader = load_boxman_mesh_from_object(obj)
    ret = BoxmanDTO(loader)
    if len(obj.children) > 0:
        for child in obj.children:
            ret.children.append(load_boxman_from_object(child))
    return ret


def construct_boxman_from_json(json_object: dict) -> BoxmanDTO:
    """
    Creates a boxman dto from a dictionary
    """
    ret = BoxmanDTO()
    ret.location = json_object["location"]
    ret.scale = json_object["scale"]
    ret.rotations = json_object["rotations"]
    ret.vertex_list = json_object["vertex_list"]
    ret.polygon_list = json_object["polygon_list"]
    ret.properties.name = json_object["properties"]["name"]
    ret.properties.orientation = json_object["properties"]["orientation"]
    ret.properties.joint_type = json_object["properties"]["joint_type"]
    ret.properties.description = json_object["properties"]["description"]

    kids = json_object["children"]
    ret.children = []
    for cc in kids:
        ret.children.append(construct_boxman_from_json(cc))
    return ret


def show_message_box(message="", title="MrBoxman", icon='INFO'):
    """
    Uses the bpy interface to show a popup message
    """
    def draw(self, context):
        """
        Prints the message box on the screen at cursor location
        """
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


class StringCompressor:
    """
    This class compresses strings in different formats
    """
    @staticmethod
    def compress(element: str) -> str:
        """Compresses a string encoding it as UTF-8"""
        a = element.encode("UTF-8")
        return zlib.compress(a).hex()

    @staticmethod
    def decompress(element: bytes) -> str:
        """Decompresses a UTF-8 string"""
        return zlib.decompress(element).decode("UTF-8")


class BoxmanTemplateLibrary:
    """
    This contains dictionaries of templated names and the compressed string serializations
    """
    def __init__(self):
        self.library_name = "template_library"
        self.template_objects: dict = {}
        self.object_descriptions = {}

    def get_boxman_object(self, key: str) -> BoxmanDTO:
        """
        Gets a boxman dto from the dictionary
        """
        if key not in self.template_objects:
            raise NotInLibraryException(key)

        raw_text = self.template_objects[key]
        json_text = StringCompressor.decompress(bytes.fromhex(raw_text))
        dd = json.loads(json_text)
        return construct_boxman_from_json(dd)

    def serialize(self, minify: bool = True):
        """
        Gets a string representation if the dictionary
        """
        if not minify:
            return json.dumps(self, indent=4, cls=BoxmanEncoder)
        else:
            return self.__str__()

    def __str__(self):
        return BoxmanEncoder().encode(self)


def deserialize_library(serialized: str) -> BoxmanTemplateLibrary:
    """
    Gets an instance of the library from a serialized dictionary
    """
    json_object = json.loads(serialized)
    ret = BoxmanTemplateLibrary()
    ret.library_name = json_object["library_name"]
    ret.template_objects = json_object["template_objects"]
    ret.object_descriptions = json_object["object_descriptions"]
    return ret


def standard_except_operation(ex: Exception):
    """
    Used to show the error message on cached exceptions.
    """
    print("Execution failed!")
    traceback.print_exc()
    print(ex)
    show_message_box(ex.__str__(), "Cached exception", "ERROR")
    raise ex
