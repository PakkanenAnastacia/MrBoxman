import bpy
import numpy as np
import sys
from typing import Callable
from typing import List
from typing import TypedDict
import pprint
import inspect
from mathutils import Euler, Vector
from math import sqrt, atan2, asin, acos, radians
from bpy.types import Operator
from bpy.types import Panel

from .boxmanclasses import BoxmanExtremityTypes, BoxmanOrientations, BoxmanJointTypes
from .boxmancommon import check_selected_object, ObjectIsNotRootException
from .mrBoxman.boxman.boxmanclasses import BoxmanDTO
from .mrBoxman.boxman.boxmancommon import add_mesh, ValueCantBeZeroException

# sys.modules["boxmanclasses"] = bpy.data.texts["boxmanclasses.py"].as_module()
# sys.modules["boxmancommon"] = bpy.data.texts["boxmancommon.py"].as_module()
# from boxmanclasses import *
# from boxmancommon import *

prettyPrinter = pprint.PrettyPrinter(indent=4)


# region Generated Controls
# TODO: This goes in another file

class BoxmanRigControl:
    """
    Contract for the rig controls and bound boxes that will be used to create meta-rig meshes.
    """
    # region Control naming constants
    DEFAULT_CONTROL_SUFFIX: str = "CTRL"
    DEFAULT_CONTROL_NAME: str = "DEFAULT"
    ROOT_CONTROL_SUFFIX: str = "ROOT"
    IK_CONTROL_SUFFIX: str = "IK"
    POLE_TARGET_SUFFIX: str = "POLE"
    SPINE_CONTROL_SUFFIX: str = "SPINE"
    NECK_CONTROL_SUFFIX: str = "NECK"
    # endregion

    def __init__(self):
        self.vertex_list = []
        self.edges_list = []
        self.name = "BoxmanRigControl"

    def add_as_mesh(self, context):
        """
        Adds a mesh to act as a rig control using the vertex and edge data of the
        current stored object, it returns a reference to the object itself
        """
        # noinspection PyArgumentEqualDefault
        return add_mesh(context, self.name, self.vertex_list, None, self.edges_list)

    def scale_to_boxman(self, boxman_vertex_list: List[List[float]]) -> None:
        """
        Creates a bounding box with the shape of the proportions of the boxman argument.
        It need the argument to be in 3D, not 2d like a ring or it will explode.
        """
        box_vectors = np.array(self.vertex_list)
        print(box_vectors.size)

        x_box = box_vectors[:, 0]
        y_box = box_vectors[:, 1]
        z_box = box_vectors[:, 2]

        x_min_box = np.amin(x_box)
        x_max_box = np.amax(x_box)
        y_min_box = np.amin(y_box)
        y_max_box = np.amax(y_box)
        z_min_box = np.amin(z_box)
        z_max_box = np.amax(z_box)

        data_vectors = np.array(boxman_vertex_list)
        x_data = data_vectors[:, 0]
        y_data = data_vectors[:, 1]
        z_data = data_vectors[:, 2]

        x_min = np.amin(x_data)
        x_max = np.amax(x_data)
        y_min = np.amin(y_data)
        y_max = np.amax(y_data)
        z_min = np.amin(z_data)
        z_max = np.amax(z_data)

        new_vector = []
        for i in range(0, box_vectors.shape[0]):
            x_box_scaled = x_min + (x_box[i] - x_min_box) * (x_max - x_min) / (x_max_box - x_min_box)
            y_box_scaled = y_min + (y_box[i] - y_min_box) * (y_max - y_min) / (y_max_box - y_min_box)
            z_box_scaled = z_min + (z_box[i] - z_min_box) * (z_max - z_min) / (z_max_box - z_min_box)
            new_vector.append([x_box_scaled, y_box_scaled, z_box_scaled])

        self.vertex_list = new_vector


class BoxmanRigControlFactory:
    """
    Static class that brings boxman controls.
    """

    def __init__(self):
        pass

    @staticmethod
    def get_unit_cube(name: str) -> BoxmanRigControl:
        """
        Get a unit cube ready to be scaled to a bounding box.
        """
        control = BoxmanRigControl()
        control.vertex_list = [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0],
            [0.0, 1.0, 1.0],
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
            [1.0, 1.0, 1.0]
        ]
        control.edges_list = [[0, 2], [0, 1], [1, 3], [2, 3], [2, 6], [3, 7],
                              [6, 7], [4, 6], [5, 7], [4, 5], [0, 4], [1, 5]]
        control.name = name
        return control

    @staticmethod
    def get_unit_cross_regular_polygon(name: str, sides: int = 6, radius: float = 1.0) -> BoxmanRigControl:
        """
        Creates a cross with two regular polygons
        """
        if sides <= 0:
            raise ValueCantBeZeroException()
        n = sides
        fraction = 2 * np.pi / n
        control = BoxmanRigControl()
        for i in range(0, n+1):
            element = [radius * np.cos(fraction * i),
                       radius * np.sin(fraction * i),
                       0.0]
            control.vertex_list.append(element)
            control.edges_list.append([i, i + 1])
            
        control.edges_list[-1][1] = 0

        # then create the perpendicular ring
        for i in range(0, n+1):
            element = [0,
                       radius * np.cos(fraction * i),
                       radius * np.sin(fraction * i)]
            control.vertex_list.append(element)
            control.edges_list.append([i+n+1, i + n + 2])
            
        control.edges_list[-1][1]= n+1
        # on the last, it connects to the first
        control.name = name
        return control

    @staticmethod
    def get_unit_regular_polygon(name: str, sides: int = 6, radius: float = 1.0) -> BoxmanRigControl:
        """
        Creates a regular polygon oriented in Z
        """
        if sides <= 0:
            raise ValueCantBeZeroException()
        n = sides
        fraction = 2 * np.pi / n
        control = BoxmanRigControl()
        for i in range(0, n + 1):
            element = [radius * np.cos(fraction * i),
                       radius * np.sin(fraction * i),
                       0.0]
            control.vertex_list.append(element)
            control.edges_list.append([i, i + 1])

        control.edges_list[-1][1] = 0
        # on the last, it connects to the first
        control.name = name
        return control

# endregion


# region BaseRiggers

class RiggerException(Exception):
    """
    General use of exceptions for the riggers
    """

    def __init__(self, target_rigger, message) -> None:
        super().__init__(f"Rigger {type(target_rigger).__name__} gave an exception with message {message}.")


class RiggerBase:
    """
    Rigger of default type bones, it acts almost as an abstract class
    """

    # region Layer Indexes
    DEFAULT_LAYER_INDEX = 0 # Default view
    CONTROL_LAYER_INDEX = 1 # Only shows control bones, iks and pole targets
    MAYORS_LAYER_INDEX = 2 # Shows controls and roots of chains
    MINORS_LAYER_INDEX = 3 # Fingers and sections of chains
    ARM_LAYER_INDEX = 4 # For Arms
    HAND_LAYER_INDEX = 5 # For the Hands
    LEG_LAYER_INDEX = 6 # For the Legs
    FEET_LAYER_INDEX = 7 # For the Feet ONLY
    SPINE_LAYER_INDEX = 8 # For the spine
    HEAD_LAYER_INDEX = 9 # For the Head
    CHAIN_LAYER_INDEX = 10 # For Chains
    GLOBAL_LAYER_INDEX = 31 # ALL
    # endregion

    # region Collection constants
    COLLECTION_SUFFIX = "COLL"
    # noinspection SpellCheckingInspection
    COLLECTION_CONTROL_MESH_SUFFIX = "MESHCTRL"
    COLLECTION_MESH_SUFFIX = "MESH"
    # endregion

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        self.linked_object: BoxmanDTO = linked_object
        self.parent_rigger = parent_rigger
        self.armature_object_name = ""
        self.rigger_factory = None
        self.current_edit_bone = None  # This is the reference to the editable entity, not the bone in the data context
        self.control_bone = None # this is going to be used sometimes

        # this is the absolute root of all riggers, used to parent all the IK controls
        self.absolute_root_rigger = None

        # this is used to parent locally without loosing sight of the absolute, used fo hands and such
        self.local_control_root = None

        self.stored_parenting_fixture = []  # type: List[Callable]
        self.stored_mesh_creation_fixture = []  # type: List[Callable]
        self.stored_control_creation_fixture = []  # type: List[Callable]
        self.stored_collection_assignments= [] # type: List[Callable]

        if parent_rigger is not None:
            # name of the armature
            self.armature_object_name = parent_rigger.armature_object_name

            # find the absolute
            self.absolute_root_rigger = parent_rigger.absolute_root_rigger

            # find the absolute
            self.local_control_root = parent_rigger.local_control_root

            # The fixture is composed of calls to static methods with arguments precalculated before
            # going to object mode
            self.stored_parenting_fixture = parent_rigger.stored_parenting_fixture

            # The fixture is composed of calls to static methods with arguments precalculated before
            # going to pose mode
            self.stored_mesh_creation_fixture = parent_rigger.stored_mesh_creation_fixture

            # The fixture is composed of calls to static methods with arguments precalculated before
            # going back to object mode, this are the constraints and bone replacements
            self.stored_control_creation_fixture = parent_rigger.stored_control_creation_fixture

            # The fixture is composed of calls to static methods with arguments precalculated before
            # going back to object mode, this are the constraints and bone replacements
            self.stored_collection_assignments = parent_rigger.stored_collection_assignments
        else:
            # set the armature name
            self.armature_object_name = "Armature_"+linked_object.properties.name
            self.absolute_root_rigger = self
            self.local_control_root = self

    def rig(self, context) -> None:
        """
        Void method that executes the rig.
        It creates the bones and fills the fixtures that execute at changing modes.
        stored_parenting_fixture -> Parents the meshes to the bones
        stored_mesh_creation_fixture -> Creates meshes if needed
        stored_control_creation_fixture -> Assigns the meshes to the controllers and creates the constraints
        """
        # This is the one in the base class there is no need
        raise NotImplementedError()

    # region Mesh Functions

    def get_typical_size(self) -> float:
        """
        Gets a pseudo norm as typical size of the object
        """
        vertex_list = np.array(self.linked_object.vertex_list)
        vertex_list = np.abs(vertex_list)  # gets absolute value
        norm_x = np.amax(vertex_list[:, 0])
        norm_y = np.amax(vertex_list[:, 1])
        norm_z = np.amax(vertex_list[:, 2])
        return np.linalg.norm(np.array([norm_x, norm_y, norm_z]))

    def get_mesh_mean_point(self) -> List:
        """
        Gets the mean point of the currently linked boxman object.
        as the tail of a bone.
        """
        print(f"Calculating mean point of mesh {self.linked_object.properties.name}...")
        # need to add these 2
        vertex_list = np.array(self.linked_object.vertex_list)
        mean = np.mean(vertex_list, axis=0)

        # this needs to apply euler rotations with the vector
        mean_vector = Vector((mean[0], mean[1], mean[2]))
        euler = Euler((self.linked_object.rotations[0][0],
                       self.linked_object.rotations[0][1],
                       self.linked_object.rotations[0][2]),
                      self.linked_object.rotations[1]
                      )
        mean_vector.rotate(euler)
        return [mean_vector[0] + self.linked_object.location[0],
                mean_vector[1] + self.linked_object.location[1],
                mean_vector[2] + self.linked_object.location[2]
                ]

    # endregion

    # region Naming functions

    def get_main_collection_name(self) -> str:
        """
        Gets the name of the collection
        """
        return f"{self.armature_object_name}_{self.COLLECTION_SUFFIX}"

    def get_control_mesh_collection_name(self) -> str:
        """
        Gets the name of the collection
        """
        return f"{self.armature_object_name}_{self.COLLECTION_SUFFIX}_{self.COLLECTION_CONTROL_MESH_SUFFIX}"

    def get_mesh_object_collection_name(self) -> str:
        """
        Gets the name of the collection
        """
        return f"{self.armature_object_name}_{self.COLLECTION_SUFFIX}_{self.COLLECTION_MESH_SUFFIX}"

    # endregion

    # region Mesh queues

    def queue_parent_object_to_rig(self) -> None:
        """
        This method queues the addition of the parenting relation between the bone and the mesh associated with
        the boxman.
        """
        current_bone_name = self.current_edit_bone.name  # this turns the reference into a constant
        linked_object_name = self.linked_object.get_object_name()
        armature_name = self.armature_object_name
        self.stored_parenting_fixture.append(
            lambda context: self.parent_object_to_rig(context, current_bone_name, linked_object_name, armature_name)
        )

    @staticmethod
    def parent_object_to_rig(context, current_bone_name, linked_object_name, armature_name) -> None:
        """
        Parents a mesh to a bone of the rig
        """
        obj = check_selected_object(context, "ARMATURE")
        if current_bone_name not in obj.pose.bones.keys():
            raise NameError()

        bpy.data.objects[linked_object_name].parent = bpy.data.objects[armature_name]
        bpy.data.objects[linked_object_name].parent_bone = current_bone_name
        bpy.data.objects[linked_object_name].parent_type = 'BONE'
        context.object.data.bones[current_bone_name].use_relative_parent = True
        print(f"Linking {linked_object_name}...")

    def queue_link_mesh_to_collection(self, collection_name=None, mesh_name=None) -> None:
        """
        Queues the addition of a mesh to a collection,
        If collection is None it operates over the scene collection
        If mesh_name is None it operates over the current linked object
        """
        mesh_object_name = None
        if mesh_name is None:
            mesh_object_name = self.linked_object.get_object_name()
        else:
            mesh_object_name = mesh_name

        self.stored_collection_assignments.append(
            lambda context: self.link_mesh_to_collection(context, collection_name, mesh_object_name)
        )

    @staticmethod
    def link_mesh_to_collection(context, collection_name, mesh_object_name) -> None:
        """
        Adds a mesh to a collection
        """
        mesh_object = bpy.data.objects[mesh_object_name]
        collection = None
        if collection_name is None:
            collection = bpy.context.scene.collection
        else:
            collection = bpy.data.collections[collection_name]

        print(f"Linking {mesh_object_name} to collection {collection_name}...")
        if not any([x for x in collection.keys() if x == mesh_object_name]):
            collection.objects.link(mesh_object)
        else:
            print(f"Object {mesh_object_name} already linked to collection {collection_name}...")

    def queue_unlink_mesh_from_collection(self, collection_name=None, mesh_name=None) -> None:
        """
        Queues the removal of a mesh from a collection
        If collection is None it operates over the scene collection
        If mesh_name is None it operates over the current linked object
        """
        mesh_object_name = None
        if mesh_name is None:
            mesh_object_name = self.linked_object.get_object_name()
        else:
            mesh_object_name = mesh_name

        self.stored_collection_assignments.append(
            lambda context: self.unlink_mesh_to_collection(context, collection_name, mesh_object_name)
        )

    @staticmethod
    def unlink_mesh_to_collection(context, collection_name, mesh_object_name) -> None:
        """
        Removes a mesh to a collection
        """
        mesh_object = bpy.data.objects[mesh_object_name]
        collection = None
        if collection_name is None:
            collection = bpy.context.scene.collection
        else:
            collection = bpy.data.collections[collection_name]
        collection.objects.unlink(mesh_object)
        print(f"Unlinking {mesh_object_name} to collection {collection_name}...")

    # endregion

    # region Bone queues

    def queue_add_bone_to_group(self, group_name, bone_name):
        """
        Adds a bone to a group assuming its been created
        """
        armature_name = self.armature_object_name
        self.stored_control_creation_fixture.append(
            lambda context: self.add_bone_to_group(context, group_name, bone_name, armature_name)
        )

    @staticmethod
    def add_bone_to_group(context, group_name, bone_name, armature_name) -> None:
        """
        Creates bone groups to color the controls
        """
        print(f"Adding {bone_name} to group {group_name}...")
        target_bone = bpy.data.objects[armature_name].pose.bones[bone_name]
        bone_group = bpy.data.objects[armature_name].pose.bone_groups[group_name]
        if bone_group is None:
            raise ValueError(f"Value of bone_group can not be None!")
        target_bone.bone_group = bone_group

    def queue_add_bone_to_layers(self, layer_index: List[int], bone_name) -> None:
        """
        Queues the addition of a bone to a layer
        """
        armature_name = self.armature_object_name
        self.stored_control_creation_fixture.append(
            lambda context: self.add_bone_to_layers(context, layer_index, bone_name, armature_name)
        )

    @staticmethod
    def add_bone_to_layers(context, layer_index: List[int], bone_name, armature_name) -> None:
        """
        Adds a bone to the layers of an array
        """
        if any(index > 31 for index in layer_index):
            raise ValueError("Layer index is over the limit!")

        for index in layer_index:
            print(f"Adding {bone_name} to layer {str(index)}...")
            target_bone = bpy.data.objects[armature_name].pose.bones[bone_name]
            target_bone.bone.layers[index] = True

    # endregion


class RiggerFactoryBase:
    """
    Contract used in the riggers
    """

    def __init__(self):
        pass

    def create_rigger(self, selected_object: BoxmanDTO, parent_rigger: RiggerBase) -> RiggerBase:
        """
        Creates a rigger for the selected boxman object
        """
        pass


# endregion

# region ClassRiggers

# region BasicRiggers
# TODO: Move this to another file

class RootRigger(RiggerBase):
    """
    Only works for root objects.
    It creates a ring control of size 1, and parents all the bones in the boxman.
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        if not self.linked_object.q_is_root():
            raise ObjectIsNotRootException()

    def rig(self, context) -> None:
        """
        Creates the root bone, queues the creating of the control templates, and sets in motion the creation of the
        rest of the rig.
        Created control meshes are hidden after the creation.
        """
        print(f"Generating Root rig for {self.linked_object.properties.name}.")
        # creates the armature
        self.queue_add_control_mesh_templates()
        bpy.ops.object.armature_add(enter_editmode=True, align='WORLD',
                                    location=(0, 0, 0),
                                    scale=(1, 1, 1))
        # sets the current bone as the root and sets its tail to the location of the gizmo
        bpy.ops.armature.select_linked()
        self.current_edit_bone = bpy.context.selected_bones[0]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        # Oriented forward
        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]

        self.current_edit_bone.tail.x = self.current_edit_bone.head.x + 1.0
        self.current_edit_bone.tail.y = self.current_edit_bone.head.y
        self.current_edit_bone.tail.z = self.current_edit_bone.head.z

        # this needs to be done before creating anything
        self.queue_create_bone_groups()
        self.queue_create_collections()

        # cat it to account for refactors
        factory: RiggerFactoryBase = self.rigger_factory
        for cc in self.linked_object.children:
            child_rigger: RiggerBase = factory.create_rigger(cc, self)
            child_rigger.rig(context)
            child_bone = child_rigger.current_edit_bone
            child_bone.parent = self.current_edit_bone
            child_bone.use_connect = False  # this is only valid for the root bone

        self.queue_parent_object_to_rig()
        self.queue_attach_root_shape()
        self.queue_hide_template_meshes()
        self.queue_add_bone_to_group(BoxmanExtremityTypes.DEFAULT.value, self.current_edit_bone.name)

        self.queue_add_bone_to_layers([RiggerBase.MAYORS_LAYER_INDEX,
                                       RiggerBase.CONTROL_LAYER_INDEX,
                                       RiggerBase.GLOBAL_LAYER_INDEX],
                                      self.current_edit_bone.name)

        self.queue_unlink_mesh_from_collection()
        self.queue_link_mesh_to_collection(self.get_control_mesh_collection_name())

        self.queue_link_controls_to_collection()
        self.queue_unlink_control_meshes_to_collection()

        print(f"Generated Root rig for {self.linked_object.properties.name}!")

    # region Naming functions
    @staticmethod
    def get_root_control_name(armature_name):
        """
        Gets the name of the root controller mesh
        """
        return f"{armature_name}_{BoxmanRigControl.ROOT_CONTROL_SUFFIX}_{BoxmanRigControl.DEFAULT_CONTROL_SUFFIX}"

    @staticmethod
    def get_default_control_name(armature_name):
        """
        Gets the name os the default control mesh
        """
        return f"{armature_name}_{BoxmanRigControl.DEFAULT_CONTROL_NAME}_{BoxmanRigControl.DEFAULT_CONTROL_SUFFIX}"

    @staticmethod
    def get_pole_target_control_name(armature_name):
        """
        Gets the name of the pole target control mesh
        """
        return f"{armature_name}_{BoxmanRigControl.POLE_TARGET_SUFFIX}_{BoxmanRigControl.DEFAULT_CONTROL_SUFFIX}"

    @staticmethod
    def get_default_ik_control_name(armature_name):
        """
        Gets the name of the default ik control mesh
        """
        return f"{armature_name}_{BoxmanRigControl.IK_CONTROL_SUFFIX}_{BoxmanRigControl.DEFAULT_CONTROL_SUFFIX}"

    # endregion

    # region Template meshes queues

    def queue_add_control_mesh_templates(self) -> None:
        """
        Queues the creation of the controls used to replace the bone displays
        """
        location = self.linked_object.location
        armature_name = self.armature_object_name

        self.stored_mesh_creation_fixture.append(
            lambda context: self.add_control_mesh_templates(context, location, armature_name)
        )

    @staticmethod
    def add_control_mesh_templates(context, location, armature_name) -> None:
        """
        Adds a control for each type of required render.
        """
        # adds the root ring
        print(f"Adding {BoxmanRigControl.ROOT_CONTROL_SUFFIX} control shape...")
        name = RootRigger.get_root_control_name(armature_name)
        ring_data = BoxmanRigControlFactory.get_unit_regular_polygon(name, 8)
        ring_object = ring_data.add_as_mesh(context)
        ring_object.location.x = location[0]
        ring_object.location.y = location[1]
        ring_object.location.z = location[2]

        # adds the default ring
        print(f"Adding {BoxmanRigControl.DEFAULT_CONTROL_NAME} control shape...")
        name = RootRigger.get_default_control_name(armature_name)
        ring_data = BoxmanRigControlFactory.get_unit_cross_regular_polygon(name, 8)
        ring_object = ring_data.add_as_mesh(context)
        ring_object.location.x = location[0] + 1.0 # offset by 1.0
        ring_object.location.y = location[1]
        ring_object.location.z = location[2]

        # adds the default pole target
        print(f"Adding {BoxmanRigControl.POLE_TARGET_SUFFIX} control shape...")
        name = RootRigger.get_pole_target_control_name(armature_name)
        ring_data = BoxmanRigControlFactory.get_unit_cross_regular_polygon(name, 4)
        ring_object = ring_data.add_as_mesh(context)
        ring_object.location.x = location[0] + 2.0 # offset by 1.0
        ring_object.location.y = location[1]
        ring_object.location.z = location[2]

        # adds the default ik control
        print(f"Adding {BoxmanRigControl.IK_CONTROL_SUFFIX} control shape...")
        name = RootRigger.get_default_ik_control_name(armature_name)
        ring_data = BoxmanRigControlFactory.get_unit_cross_regular_polygon(name, 3)
        ring_object = ring_data.add_as_mesh(context)
        ring_object.location.x = location[0] + 3.0 # offset by 1.0
        ring_object.location.y = location[1]
        ring_object.location.z = location[2]

    def queue_hide_template_meshes(self) -> None:
        """
        Queues the action of hide all meshes once created
        """
        armature_name = self.armature_object_name
        self.stored_mesh_creation_fixture.append(
            lambda context: self.hide_template_meshes(context, armature_name)
        )

    @staticmethod
    def hide_template_meshes(context, armature_name) -> None:
        """
        Hides all created control meshes
        """
        print(f"Hiding {BoxmanRigControl.ROOT_CONTROL_SUFFIX} control shape...")
        root_name = RootRigger.get_root_control_name(armature_name)
        bpy.data.objects[root_name].hide_viewport = True
        bpy.data.objects[root_name].hide_render = True

        print(f"Hiding {BoxmanRigControl.DEFAULT_CONTROL_NAME} control shape...")
        ring_name = RootRigger.get_default_control_name(armature_name)
        bpy.data.objects[ring_name].hide_viewport = True
        bpy.data.objects[ring_name].hide_render = True

        print(f"Hiding {BoxmanRigControl.POLE_TARGET_SUFFIX} control shape...")
        pole_name = RootRigger.get_pole_target_control_name(armature_name)
        bpy.data.objects[pole_name].hide_viewport = True
        bpy.data.objects[pole_name].hide_render = True

        print(f"Hiding {BoxmanRigControl.IK_CONTROL_SUFFIX} control shape...")
        ik_name = RootRigger.get_default_ik_control_name(armature_name)
        bpy.data.objects[ik_name].hide_viewport = True
        bpy.data.objects[ik_name].hide_render = True

    def queue_create_collections(self) -> None:
        """
        queues the creation of the main collections
        """
        main_collection_name = self.get_main_collection_name()
        control_collection_name = self.get_control_mesh_collection_name()
        mesh_object_collection_name = self.get_mesh_object_collection_name()
        self.stored_control_creation_fixture.append(
            lambda context: self.create_collections(context, main_collection_name,
                                                    control_collection_name,
                                                    mesh_object_collection_name)
        )

    @staticmethod
    def create_collections(context, main_collection_name, control_collection_name, mesh_object_collection_name) -> None:
        """
        Creates bone groups to color the controls
        """
        # the main collection is linked to the scene
        main_collection = bpy.data.collections.new(main_collection_name)
        bpy.context.scene.collection.children.link(main_collection)

        control_collection = bpy.data.collections.new(control_collection_name)
        main_collection.children.link(control_collection)

        mesh_collection = bpy.data.collections.new(mesh_object_collection_name)
        main_collection.children.link(mesh_collection)

    def queue_link_controls_to_collection(self) -> None:
        """
        Links the control template meshes to the control collection
        """
        control_collection_name = self.get_control_mesh_collection_name()
        armature_name = self.armature_object_name
        root_name = RootRigger.get_root_control_name(armature_name)
        ring_name = RootRigger.get_default_control_name(armature_name)
        pole_name = RootRigger.get_pole_target_control_name(armature_name)
        ik_name = RootRigger.get_default_ik_control_name(armature_name)
        self.queue_link_mesh_to_collection(control_collection_name, root_name)
        self.queue_link_mesh_to_collection(control_collection_name, ring_name)
        self.queue_link_mesh_to_collection(control_collection_name, pole_name)
        self.queue_link_mesh_to_collection(control_collection_name, ik_name)

    def queue_unlink_control_meshes_to_collection(self) -> None:
        """
        Unlinks the control meshes from the main scene collection
        """
        armature_name = self.armature_object_name
        root_name = RootRigger.get_root_control_name(armature_name)
        ring_name = RootRigger.get_default_control_name(armature_name)
        pole_name = RootRigger.get_pole_target_control_name(armature_name)
        ik_name = RootRigger.get_default_ik_control_name(armature_name)
        self.queue_unlink_mesh_from_collection(mesh_name=root_name)
        self.queue_unlink_mesh_from_collection(mesh_name=ring_name)
        self.queue_unlink_mesh_from_collection(mesh_name=pole_name)
        self.queue_unlink_mesh_from_collection(mesh_name=ik_name)

    # endregion

    # region Bone queues

    def queue_attach_root_shape(self) -> None:
        """
        Queues the change of shape of the main root bone
        """
        current_bone_name = self.current_edit_bone.name  # this turns the reference into a constant
        armature_name = self.armature_object_name
        self.stored_control_creation_fixture.append(
            lambda context: self.attach_root_shape(context, current_bone_name, armature_name)
        )

    @staticmethod
    def attach_root_shape(context, current_bone_name, armature_name) -> None:
        """
        Creates a roll control of half a typical size
        """
        print(f"Attaching default ring control to {current_bone_name}...")
        name = RootRigger.get_root_control_name(armature_name)
        bpy.data.objects[armature_name].pose.bones[current_bone_name].custom_shape = bpy.data.objects[name]
        bpy.data.objects[armature_name].pose.bones[current_bone_name].custom_shape_scale = 0.5

    def queue_create_bone_groups(self) -> None:
        """
        Queues the creation of bone groups
        """
        armature_name = self.armature_object_name
        self.stored_control_creation_fixture.append(
            lambda context: self.create_bone_groups(context, armature_name)
        )

    @staticmethod
    def create_bone_groups(context, armature_name) -> None:
        """
        Creates bone groups to color the controls
        """
        # DEFAULT places ROOT and Defaults
        group = bpy.data.objects[armature_name].pose.bone_groups.new()
        group.name = BoxmanExtremityTypes.DEFAULT.value
        group.color_set = "THEME01"

        # SPINE is for... the spine
        group = bpy.data.objects[armature_name].pose.bone_groups.new()
        group.name = BoxmanExtremityTypes.SPINE.value
        group.color_set = "THEME02"

        # HEAD is for the neck and head controls
        group = bpy.data.objects[armature_name].pose.bone_groups.new()
        group.name = BoxmanExtremityTypes.HEAD.value
        group.color_set = "THEME03"

        # HAND is for the hand and fingers
        group = bpy.data.objects[armature_name].pose.bone_groups.new()
        group.name = BoxmanExtremityTypes.HAND.value
        group.color_set = "THEME04"

        # ARM is for the arm and its controls
        group = bpy.data.objects[armature_name].pose.bone_groups.new()
        group.name = BoxmanExtremityTypes.ARM.value
        group.color_set = "THEME05"

        # LEG is for the Leg and its controls
        group = bpy.data.objects[armature_name].pose.bone_groups.new()
        group.name = BoxmanExtremityTypes.LEG.value
        group.color_set = "THEME06"

        # FEET is for the Foot and its controls
        group = bpy.data.objects[armature_name].pose.bone_groups.new()
        group.name = BoxmanExtremityTypes.FEET.value
        group.color_set = "THEME07"

        # CHAIN is for the chain like controls and its ik controls
        group = bpy.data.objects[armature_name].pose.bone_groups.new()
        group.name = BoxmanExtremityTypes.CHAIN.value
        group.color_set = "THEME08"

    def queue_link_armature_to_main_collection(self) -> None:
        """
        queues the creation of the main collections
        """
        main_collection_name = self.get_main_collection_name()
        armature_name = self.armature_object_name
        self.stored_control_creation_fixture.append(
            lambda context: self.link_armature_to_main_collection(context, main_collection_name, armature_name)
        )

    @staticmethod
    def link_armature_to_main_collection(context, main_collection_name, armature_name) -> None:
        """
        Creates bone groups to color the controls
        """
        # the main collection is linked to the scene
        armature_object = bpy.data.objects[armature_name]
        collection = bpy.data.collections[main_collection_name]
        collection.objects.link(armature_object)

    # endregion


class AccessoryRigger(RiggerBase):
    """
    This rigger is a dead end for all other riggers.
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)

    def rig(self, context) -> None:
        """
        It scans for non accessory objects, accessory objects are that, are not rigged
        """
        print(f"Accessory rigger at {self.linked_object.properties.name}, all children ignored...")

        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()
        for child_object in self.linked_object.children:
            accessory_rigger = AccessoryRigger(child_object, self)
            accessory_rigger.rig(context)


class DefaultRigger(RiggerBase):
    """
    The default rigger is the one that you should choose if you don't know what you are doing,
    This chains the bone creation of any structure and replaces the bones with the default ring track ball.
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)

    def rig(self, context) -> None:
        """
        It creates a bone with the default shape and parents it to the current boxman object.
        In the default class, it handles all types of children, is the most generic of them all.
        """
        print(f"Generating default rig for {self.linked_object.properties.name}.")

        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]

        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        # there ere 3 possibilities
        # if: it's end of a chain
        if len(self.linked_object.children) == 0:
            # if its the end of a chain, it places the tail in the mean
            typical_offset = self.get_typical_size()
            self.current_edit_bone.tail.x = self.current_edit_bone.head.x + typical_offset
            self.current_edit_bone.tail.y = self.current_edit_bone.head.y
            self.current_edit_bone.tail.z = self.current_edit_bone.head.z

            self.queue()
            return  # its end of a link

        # if: has only one child
        if len(self.linked_object.children) == 1:
            # If the child is only one, the target of the tail is the position of the next member of the chain
            # and the child bone is linked to the
            child_object: BoxmanDTO = self.linked_object.children[0]

            factory: RiggerFactoryBase = self.rigger_factory
            child_rigger: RiggerBase = factory.create_rigger(child_object, self)
            child_rigger.rig(context)
            child_bone = child_rigger.current_edit_bone
            if child_bone is not None:  # there might be boneless riggers
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = True  # this is only valid for the root bone
                self.current_edit_bone.tail.x = child_object.location[0]
                self.current_edit_bone.tail.y = child_object.location[1]
                self.current_edit_bone.tail.z = child_object.location[2]
            else:
                typical_offset = self.get_typical_size()
                self.current_edit_bone.tail.x = self.current_edit_bone.head.x + typical_offset
                self.current_edit_bone.tail.y = self.current_edit_bone.head.y
                self.current_edit_bone.tail.z = self.current_edit_bone.head.z

            self.queue()
            return

        # if: has multiple children
        # The rail is irrelevant more than the size of the object,
        # It places the tail at a displacement of typical size,
        # creates the children rigs and
        # it parents the results without connecting the bones

        typical_offset = self.get_typical_size()
        self.current_edit_bone.tail.x = self.current_edit_bone.head.x + typical_offset
        self.current_edit_bone.tail.y = self.current_edit_bone.head.y
        self.current_edit_bone.tail.z = self.current_edit_bone.head.z

        for linked_child in self.linked_object.children:
            child_object: BoxmanDTO = linked_child

            factory: RiggerFactoryBase = self.rigger_factory
            child_rigger: RiggerBase = factory.create_rigger(child_object, self)
            child_rigger.rig(context)
            child_bone = child_rigger.current_edit_bone
            if child_bone is not None:  # there might be boneless riggers
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = False  # this is only valid for the root bone

        self.queue()
        print(f"Generated default rig for {self.linked_object.properties.name}!")

    def queue(self) -> None:
        """
        Actions to queue after the fact
        """
        self.queue_parent_object_to_rig()
        self.queue_attach_default_shape()
        self.queue_add_bone_to_group(BoxmanExtremityTypes.DEFAULT.value, self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX, RiggerBase.MINORS_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()

    def queue_attach_default_shape(self) -> None:
        """
        Queues the assignment of the default ring to the current bone.
        """
        current_bone_name = self.current_edit_bone.name  # this turns the reference into a constant
        armature_name = self.armature_object_name
        self.stored_control_creation_fixture.append(
            lambda context: self.attach_ring_shape(context, current_bone_name, armature_name)
        )

    @staticmethod
    def attach_ring_shape(context, current_bone_name, armature_name) -> None:
        """
        Creates a roll control of half a typical size
        """
        print(f"Attaching default ring control to {current_bone_name}...")
        name = f"{armature_name}_{BoxmanRigControl.DEFAULT_CONTROL_NAME}_{BoxmanRigControl.DEFAULT_CONTROL_SUFFIX}"
        bpy.data.objects[armature_name].pose.bones[current_bone_name].custom_shape = bpy.data.objects[name]
        bpy.data.objects[armature_name].pose.bones[current_bone_name].custom_shape_scale = 0.5

    def queue_hide_current_bone(self) -> None:
        """
        Queues the action of hide the current bone, used in child classes, it is displayed in the global layer thou
        """
        current_bone_name = self.current_edit_bone.name  # this turns the reference into a constant
        armature_name = self.armature_object_name

        self.stored_control_creation_fixture.append(
            lambda context: self.hide_current_bone(context, current_bone_name, armature_name)
        )

    @staticmethod
    def hide_current_bone(context, current_bone_name, armature_name) -> None:
        """
        Hides the current bone
        """
        print(f"Hiding bone {current_bone_name}...")

        target_bone = bpy.data.objects[armature_name].pose.bones[current_bone_name]
        target_bone.bone.layers[RiggerBase.GLOBAL_LAYER_INDEX] = True
        target_bone.bone.layers[RiggerBase.DEFAULT_LAYER_INDEX] = False


class PoleTargetRigger(DefaultRigger):
    """
    The pole target rigger is a base implementation, abstract.
    It can generate pole target controls and attach their shapes.
    """
    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        self.offset_sign = 1

    def rig(self, context) -> None:
        """
        In this class it uses the same method as the one in the default rigger
        """
        raise NotImplementedError()

    def create_control_bone(self) -> None:
        """
        Creates a control bone placed with an offset relative to the typical size of the boxman object.
        The control is parented to the absolute Root.
        """
        print(f"Generating pole target control bone for {self.linked_object.properties.name}...")
        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.control_bone = newly_created[0]

        x_offset = self.get_typical_size()
        x_size_offset = self.parent_rigger.get_typical_size() # places the control distanced with the parent
        self.control_bone.head.x = self.current_edit_bone.head.x + x_size_offset * self.offset_sign
        self.control_bone.head.y = self.current_edit_bone.head.y
        self.control_bone.head.z = self.current_edit_bone.head.z
        self.control_bone.name = f"{self.current_edit_bone.name}_" \
                                 f"{BoxmanRigControl.POLE_TARGET_SUFFIX}_{BoxmanRigControl.DEFAULT_CONTROL_SUFFIX}"

        self.control_bone.tail.x = self.current_edit_bone.head.x + (x_size_offset + x_offset) * self.offset_sign
        self.control_bone.tail.y = self.current_edit_bone.head.y
        self.control_bone.tail.z = self.current_edit_bone.head.z

    def queue_attach_default_shape(self) -> None:
        """
        Queues the assignment of the pole target mesh to the control bone
        """
        control_bone_name = self.control_bone.name
        armature_name = self.armature_object_name
        self.stored_control_creation_fixture.append(
            lambda context: self.attach_pole_target_shape(context, control_bone_name, armature_name)
        )

    @staticmethod
    def attach_pole_target_shape(context, control_bone_name, armature_name) -> None:
        """
        Attaches the pole target mesh to the control bone
        """
        print(f"Attaching pole control shape to {control_bone_name}...")
        name = RootRigger.get_pole_target_control_name(armature_name)
        bpy.data.objects[armature_name].pose.bones[control_bone_name].custom_shape = bpy.data.objects[name]
        bpy.data.objects[armature_name].pose.bones[control_bone_name].custom_shape_scale = 2.0


class IkControlRigger(DefaultRigger):
    """
    This rigger is super important, it can handle the creation of IK controls.
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        self.pole_target_bone = None
        self.pole_target_offset = 1
        # this tells if the control bone is placed on the head or the tail of the current bone
        self.place_on_head = True
        self.affect_parent = True
        self.angle_orient = False

    def rig(self, context) -> None:
        """
        Direct inheritance
        """
        super().rig(context)

    def create_control_bone(self, absolute: bool = True) -> None:
        """
        It creates a control bone placed with an x offset relative to the typical size.
        The control is parented to the absolute Root if the absolute argument is true
        """
        print(f"Generating IK control bone for {self.linked_object.properties.name}...")
        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.control_bone = newly_created[0]

        x_offset = self.get_typical_size()
        if self.place_on_head:
            self.control_bone.head.x = self.current_edit_bone.head.x
            self.control_bone.head.y = self.current_edit_bone.head.y
            self.control_bone.head.z = self.current_edit_bone.head.z
            self.control_bone.tail.x = self.current_edit_bone.head.x + x_offset
            self.control_bone.tail.y = self.current_edit_bone.head.y
            self.control_bone.tail.z = self.current_edit_bone.head.z
        else:
            self.control_bone.head.x = self.current_edit_bone.tail.x
            self.control_bone.head.y = self.current_edit_bone.tail.y
            self.control_bone.head.z = self.current_edit_bone.tail.z
            self.control_bone.tail.x = self.current_edit_bone.tail.x + x_offset
            self.control_bone.tail.y = self.current_edit_bone.tail.y
            self.control_bone.tail.z = self.current_edit_bone.tail.z

        self.control_bone.name = f"{self.current_edit_bone.name}_" \
                                 f"{BoxmanRigControl.IK_CONTROL_SUFFIX}_{BoxmanRigControl.DEFAULT_CONTROL_SUFFIX}"

        # tells if the control is local or global with the parenting
        if absolute:
            self.control_bone.parent = self.absolute_root_rigger.current_edit_bone
        else:
            self.control_bone.parent = self.local_control_root.current_edit_bone

        self.control_bone.use_connect = False

    def queue_create_ik_constraint(self, angle=180.0, chain_length=2) -> None:
        """
        Queue the creation of an IK constraint.
        """
        armature_name = self.armature_object_name
        current_bone_control_name = self.control_bone.name  # this turns the reference into a constant
        ik_affected_bone_name = ""
        if self.affect_parent:
            ik_affected_bone_name = self.parent_rigger.current_edit_bone.name
        else:
            ik_affected_bone_name = self.current_edit_bone.name

        pole_target_angle = angle
        if self.angle_orient:
            pole_target_angle = self.get_angle_orient()

        pole_target_bone = None
        if self.pole_target_bone is not None:
            pole_target_bone = self.pole_target_bone.name

        self.stored_control_creation_fixture.append(
            lambda context: self.create_ik_constraint(context, ik_affected_bone_name,
                                                      current_bone_control_name, armature_name, pole_target_bone,
                                                      pole_target_angle, chain_length)
        )

    def get_angle_orient(self) -> float:
        """
        If the angle orient property is true, it uses the offset sign and the orientation of the L/R/C bone
        to calculate the correct canonical angle for the pole target, if any
        :return:
        The angle used for the pole target
        """
        angle = 0.0
        if self.pole_target_offset == 1:
            # if the orientation is negative
            if self.linked_object.properties.orientation == BoxmanOrientations.L.value:
                angle = 0.0
            elif self.linked_object.properties.orientation == BoxmanOrientations.R.value:
                angle = -105.0
            else:
                angle = 0.0
        elif self.pole_target_offset == -1:
            print(f"ORIENTATION AT {self.linked_object.properties.orientation}")
            # if the orientation is negative
            if self.linked_object.properties.orientation == BoxmanOrientations.L.value:
                angle = 180.0
            elif self.linked_object.properties.orientation == BoxmanOrientations.R.value:
                angle = 75.0
            else:
                angle = 180.0
        else:
            raise ValueError()

        return angle

    @staticmethod
    def create_ik_constraint(context, ik_affected_bone_name, current_bone_control_name,
                             armature_name, pole_target_bone_name=None, angle=180.0, chain_length=2) -> None:
        """
        Creates an IK constraint over the parent bone, the IK is of chain count 2 and the pole target is assigned
        if the control is declared before calling the queue.
        The Ik control exists this method with its shape assigned.
        """
        print(f"Generating IK constraint for {ik_affected_bone_name}...")
        armature = bpy.data.objects[armature_name]
        ik_target_bone = bpy.data.objects[armature_name].pose.bones[ik_affected_bone_name]
        constraint = ik_target_bone.constraints.new("IK")
        constraint.target = armature
        constraint.subtarget = current_bone_control_name
        constraint.chain_count = chain_length
        if pole_target_bone_name is not None:
            print("Adding pole target...")
            constraint.pole_target = armature
            constraint.pole_subtarget = pole_target_bone_name
            constraint.pole_angle = radians(angle)

        name = f"{armature_name}_{BoxmanRigControl.IK_CONTROL_SUFFIX}_{BoxmanRigControl.DEFAULT_CONTROL_SUFFIX}"
        bpy.data.objects[armature_name].pose.bones[current_bone_control_name].custom_shape = bpy.data.objects[name]
        bpy.data.objects[armature_name].pose.bones[current_bone_control_name].custom_shape_scale = 1

# endregion


# region Arm
# TODO: MOVE THIS TO ANOTHER FILE

class ShoulderRigger(DefaultRigger):
    """
    This class creates a rig that places a control outside the mesh at typical distance unit on X
    and applies a same rotation constraint.
    """
    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        self.mandatory = []
        self.non_mandatory = []

    def verify_chain(self) -> None:
        """
        Checks the mandatory children
        """
        if len(self.linked_object.children) == 0:
            raise RiggerException(self, f"This rigger requires a child to operate.")

        self.mandatory = [x for x in self.linked_object.children
                          if x.properties.joint_type == BoxmanJointTypes.ARM_HUMERUS.value]

        self.non_mandatory = [x for x in self.linked_object.children
                              if x.properties.joint_type != BoxmanJointTypes.ARM_HUMERUS.value]

        if len(self.mandatory) != 1:
            raise RiggerException(self, f"This rigger requires ONE a "
                                        f"child of type {BoxmanJointTypes.ARM_HUMERUS.value}.")

    def rig(self, context) -> None:
        """
        This rig creates a hidden bone with a proxy control for rotations.
        The rotation control is parented to the same object as the original bone.
        """
        print(f"Generating shoulder rig for {self.linked_object.properties.name}...")
        self.verify_chain()

        # We create the bone as in the default scenario
        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]
        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        # If the child is only one, the target of the tail is the position of the next member of the chain
        child_object: BoxmanDTO = self.mandatory[0]
        factory: RiggerFactoryBase = self.rigger_factory
        child_rigger: RiggerBase = factory.create_rigger(child_object, self)
        child_rigger.rig(context)
        # After all happened
        child_bone = child_rigger.current_edit_bone
        child_bone.parent = self.current_edit_bone
        child_bone.use_connect = True  # this is only valid for the root bone

        self.current_edit_bone.tail.x = child_object.location[0]
        self.current_edit_bone.tail.y = child_object.location[1]
        self.current_edit_bone.tail.z = child_object.location[2]

        # then we handle the non mandatory children
        for child in self.non_mandatory:
            child_rigger: RiggerBase = factory.create_rigger(child, self)
            child_rigger.rig(context)
            # After all happened
            if child_rigger.current_edit_bone is not None:
                child_bone = child_rigger.current_edit_bone
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = False

        # then, we use the typical size to create a new bone at relative distance of the original
        # the coordinate and the order of the displacement can be other parameters of the joint type assign,
        # but it works for now
        x_offset = self.get_typical_size()
        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.control_bone = newly_created[0]
        self.control_bone.head.x = self.current_edit_bone.head.x + x_offset
        self.control_bone.head.y = self.current_edit_bone.head.y
        self.control_bone.head.z = self.current_edit_bone.head.z
        self.control_bone.name = f"{self.current_edit_bone.name}_{BoxmanRigControl.DEFAULT_CONTROL_SUFFIX}"

        # If the child is only one, the target of the tail is the position of the next member of the chain
        self.control_bone.tail.x = self.current_edit_bone.tail.x + x_offset
        self.control_bone.tail.y = self.current_edit_bone.tail.y
        self.control_bone.tail.z = self.current_edit_bone.tail.z

        # the control is parented to the parent
        self.control_bone.parent = self.parent_rigger.current_edit_bone
        self.control_bone.use_connect = False

        self.queue()
        print(f"Generated shoulder rig for {self.linked_object.properties.name}!")

    def queue(self) -> None:
        """
        Creates the action queue
        """
        self.queue_parent_object_to_rig() # this is the same
        self.queue_create_shoulder_constraint() # this changes
        self.queue_hide_current_bone() # hides the bone overtaken by the control
        self.queue_add_bone_to_group(BoxmanExtremityTypes.ARM.value, self.control_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.ARM_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.MAYORS_LAYER_INDEX,
                                       RiggerBase.CONTROL_LAYER_INDEX,
                                       RiggerBase.ARM_LAYER_INDEX],
                                      self.control_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()

    def queue_create_shoulder_constraint(self) -> None:
        """
        Queues the creation of the same rotation constraint
        """
        current_bone_name = self.current_edit_bone.name  # this turns the reference into a constant
        current_bone_control_name = self.control_bone.name  # this turns the reference into a constant
        armature_name = self.armature_object_name

        self.stored_control_creation_fixture.append(
            lambda context: self.create_shoulder_constraint(context, current_bone_name,
                                                            current_bone_control_name, armature_name)
        )

    @staticmethod
    def create_shoulder_constraint(context, current_bone_name, current_bone_control_name, armature_name) -> None:
        """
        Creates a constraint of same rotation over the control
        """
        print(f"Attaching shoulder ring control to {current_bone_name}...")
        name = RootRigger.get_default_control_name(armature_name)
        armature = bpy.data.objects[armature_name]
        current_bone = bpy.data.objects[armature_name].pose.bones[current_bone_name]
        constraint = current_bone.constraints.new("COPY_ROTATION")
        constraint.target = armature
        constraint.subtarget = current_bone_control_name
        bpy.data.objects[armature_name].pose.bones[current_bone_control_name].custom_shape = bpy.data.objects[name]
        bpy.data.objects[armature_name].pose.bones[current_bone_control_name].custom_shape_scale = 0.5


class HumerusRigger(DefaultRigger):
    """
    The humerus rigger only holds the humerus bone, that will be un-hidden.
    Its purpose is only to be a bridge between the radius bone and
    whatever its in between. Its also used to type check the parent of the radius rigger
    so it can set the Iks controls
    """
    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        self.mandatory = []
        self.non_mandatory = []

    def verify_chain(self) -> None:
        """
        Checks for mandatory children
        """
        if len(self.linked_object.children) == 0:
            raise RiggerException(self, f"This rigger requires a child to operate.")

        self.mandatory = [x for x in self.linked_object.children
                          if x.properties.joint_type == BoxmanJointTypes.ARM_RADIUS.value]

        self.non_mandatory = [x for x in self.linked_object.children
                              if x.properties.joint_type != BoxmanJointTypes.ARM_RADIUS.value]

        if len(self.mandatory) != 1:
            raise RiggerException(self, f"This rigger requires ONE a "
                                        f"child of type {BoxmanJointTypes.ARM_RADIUS.value}.")

    def rig(self, context) -> None:
        """
        Similar to the default rig, only difference is that it expects at least one child of radius type.
        The idea is that it guaranties that the radius has at least two bones for the IK.
        """
        print(f"Generating humerus rig for {self.linked_object.properties.name}...")

        self.verify_chain()
        # We create the bone as in the default scenario
        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]
        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        child_object: BoxmanDTO = self.mandatory[0]
        factory: RiggerFactoryBase = self.rigger_factory
        child_rigger: RiggerBase = factory.create_rigger(child_object, self)
        child_rigger.rig(context)
        # After all happened
        child_bone = child_rigger.current_edit_bone
        child_bone.parent = self.current_edit_bone
        child_bone.use_connect = True  # this is only valid for the root bone
        self.current_edit_bone.tail.x = child_object.location[0]
        self.current_edit_bone.tail.y = child_object.location[1]
        self.current_edit_bone.tail.z = child_object.location[2]

        # then we handle the non mandatory children
        for child in self.non_mandatory:
            child_non_mandatory_rigger: RiggerBase = factory.create_rigger(child, self)
            child_non_mandatory_rigger.rig(context)
            # After all happened
            if child_non_mandatory_rigger.current_edit_bone is not None:
                child_bone = child_non_mandatory_rigger.current_edit_bone
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = False

        self.queue_parent_object_to_rig()  # this is the same
        self.queue_add_bone_to_group(BoxmanExtremityTypes.ARM.value, self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.MAYORS_LAYER_INDEX,
                                       RiggerBase.ARM_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()
        print(f"Generated humerus rig for {self.linked_object.properties.name}!")


class ElbowRigger(PoleTargetRigger):
    """
    The elbow rigger is a dead end with a hidden bone that places a pole target.
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        if len(self.linked_object.children) > 0:
            print("The elbow rigger is a dead end! potential data loss detected!!!!")
        self.offset_sign = -1

    def rig(self, context) -> None:
        """
        Creates a hidden bone and creates a pole target control
        """
        print(f"Generating elbow rig for {self.linked_object.properties.name}...")
        # this works as the default rigger of a disconnected parent
        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]

        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        mean = self.get_mesh_mean_point()
        self.current_edit_bone.tail.x = mean[0]
        self.current_edit_bone.tail.y = mean[1]
        self.current_edit_bone.tail.z = mean[2]

        self.create_control_bone()
        self.control_bone.parent = self.local_control_root.current_edit_bone
        self.control_bone.use_connect = False

        self.queue_hide_current_bone()
        self.queue_attach_default_shape()
        self.queue_add_bone_to_group(BoxmanExtremityTypes.ARM.value, self.current_edit_bone.name)
        self.queue_add_bone_to_group(BoxmanExtremityTypes.ARM.value, self.control_bone.name)

        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.ARM_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.CONTROL_LAYER_INDEX,
                                       RiggerBase.MAYORS_LAYER_INDEX,
                                       RiggerBase.ARM_LAYER_INDEX],
                                      self.control_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()
        print(f"Generated elbow rig for {self.linked_object.properties.name}!")


class HandRootRigger(IkControlRigger):
    """
    This rigger creates a rig for the hand, no mandatory bones, but it creates an IK control for the
    two previous bones in the chain.
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        self.angle_orient = True

    def rig(self, context) -> None:
        """
        Performs a default rig but attaches an IK control constraint to the last two bones on the chain.
        """
        # does the same as the default
        super().rig(context)

    def queue(self) -> None:
        """
        Actions to queue after the fact
        """
        self.queue_parent_object_to_rig()
        self.queue_attach_default_shape()
        self.create_control_bone(False)
        self.queue_create_ik_constraint()
        self.queue_add_rotation_constraint()
        self.queue_add_bone_to_group(BoxmanExtremityTypes.HAND.value, self.current_edit_bone.name)
        self.queue_add_bone_to_group(BoxmanExtremityTypes.ARM.value, self.control_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.HAND_LAYER_INDEX,
                                       RiggerBase.ARM_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.CONTROL_LAYER_INDEX,
                                       RiggerBase.MAYORS_LAYER_INDEX,
                                       RiggerBase.ARM_LAYER_INDEX],
                                      self.control_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()

    def queue_add_rotation_constraint(self):
        """
        Queues the addition of a constraint that adds the rotation of the IK controller to the main bone
        """
        armature_name = self.armature_object_name
        current_edit_bone_name = self.current_edit_bone.name  # this turns the reference into a constant
        ik_control_bone_name = self.control_bone.name  # this turns the reference into a constant

        self.stored_control_creation_fixture.append(
            lambda context: self.add_rotation_constraint(context, ik_control_bone_name,
                                                         current_edit_bone_name, armature_name)
        )

    @staticmethod
    def add_rotation_constraint(context, ik_control_bone_name, current_edit_bone_name, armature_name) -> None:
        """
        Creates a copy location constraint to the parent bone
        """
        print(f"Adding rotation constraints to {current_edit_bone_name}...")
        armature = bpy.data.objects[armature_name]
        current_bone = bpy.data.objects[armature_name].pose.bones[current_edit_bone_name]
        constraint = current_bone.constraints.new("COPY_ROTATION")
        constraint.target = armature
        constraint.subtarget = ik_control_bone_name
        constraint.mix_mode = "ADD"
        constraint.owner_space = "LOCAL"
        constraint.target_space = "LOCAL"


class RadiusRigger(DefaultRigger):
    """
    The radius creates a default rig expecting one hand root child, to use for IK constraints.
    If it has an elbow child, it uses it as pole target.
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        self.mandatory = []
        self.non_mandatory = []

    def verify_chain(self) -> None:
        """
        Checks for mandatory bones
        """
        if len(self.linked_object.children) == 0:
            raise RiggerException(self, f"This rigger requires a child to operate.")

        self.mandatory = [x for x in self.linked_object.children
                          if x.properties.joint_type == BoxmanJointTypes.HAND_ROOT.value]

        self.non_mandatory = [x for x in self.linked_object.children
                              if x.properties.joint_type != BoxmanJointTypes.HAND_ROOT.value]

        if len(self.mandatory) != 1:
            raise RiggerException(self, f"This rigger requires ONE a "
                                        f"child of type {BoxmanJointTypes.HAND_ROOT.value}.")

    def rig(self, context) -> None:
        """
        Acts like de default rigger, expecting a hand root to link and use as IK control.
        The pole target is optional, and the bone is not invisible so that the pole target can be adjusted if needed.
        """

        print(f"Generating radius rig for {self.linked_object.properties.name}...")
        self.verify_chain()
        # We create the bone as in the default scenario
        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]
        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        # we handle the non mandatory first to have the name of the pole target, if any
        pole_target_bone = None
        pole_target_offset = 0
        # handle the non mandatory children
        factory: RiggerFactoryBase = self.rigger_factory
        for child in self.non_mandatory:
            child_non_mandatory_rigger: RiggerBase = factory.create_rigger(child, self)
            child_non_mandatory_rigger.rig(context)
            # After all happened
            if child_non_mandatory_rigger.current_edit_bone is not None:
                child_bone = child_non_mandatory_rigger.current_edit_bone
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = False # the connect is going to the mandatory
            if isinstance(child_non_mandatory_rigger, ElbowRigger):
                pole_target_bone = child_non_mandatory_rigger.control_bone
                pole_target_offset = child_non_mandatory_rigger.offset_sign

        child_object: BoxmanDTO = self.mandatory[0]
        factory: RiggerFactoryBase = self.rigger_factory
        # noinspection PyTypeChecker
        child_rigger = factory.create_rigger(child_object, self) # type: HandRootRigger
        child_rigger.pole_target_bone = pole_target_bone
        child_rigger.pole_target_offset = pole_target_offset

        # if there is only one, there is no need for a pole target
        child_rigger.rig(context)
        child_bone = child_rigger.current_edit_bone
        child_bone.parent = self.current_edit_bone
        child_bone.use_connect = True  # this is only valid for the root bone

        self.current_edit_bone.tail.x = child_object.location[0]
        self.current_edit_bone.tail.y = child_object.location[1]
        self.current_edit_bone.tail.z = child_object.location[2]
        self.queue_parent_object_to_rig()
        self.queue_add_bone_to_group(BoxmanExtremityTypes.ARM.value, self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.ARM_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()
        print(f"Generated radius rig for {self.linked_object.properties.name}!")


class FingerRiggerBase(DefaultRigger):
    """
    Base class of the finger riggers
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        self.control_bone = None

    def rig(self, context) -> None:
        """
        Direct inheritance
        """
        raise NotImplementedError()


class FingerSectionRigger(FingerRiggerBase):
    """
    The finger rigger acts as a default rigger that doesnt hide the bone.
    It can accept and pass a rotation control to children of the same type.
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)

    def rig(self, context) -> None:
        """
        Handles the creation of children bones the same way a default rigger do,
        except that the bones arent hidden
        """
        print(f"Generating finger rig for {self.linked_object.properties.name}.")

        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]

        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        # there ere 3 possibilities
        mean = self.get_mesh_mean_point()
        # if: it's end of a chain
        if len(self.linked_object.children) == 0:
            self.current_edit_bone.tail.x = mean[0]
            self.current_edit_bone.tail.y = mean[1]
            self.current_edit_bone.tail.z = mean[2]

            self.queue()
            return  # its end of a link

        # if: has only one child
        if len(self.linked_object.children) == 1:
            # If the child is only one, the target of the tail is the position of the next member of the chain
            # and the child bone is linked to the
            child_object: BoxmanDTO = self.linked_object.children[0]
            factory: RiggerFactoryBase = self.rigger_factory
            child_rigger = factory.create_rigger(child_object, self)
            # It chains the control to the other fingers
            if isinstance(child_rigger, FingerRiggerBase):
                child_rigger.control_bone = self.control_bone

            child_rigger.rig(context)
            child_bone = child_rigger.current_edit_bone
            if child_bone is not None:  # there might be boneless riggers
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = True  # this is only valid for the root bone
                self.current_edit_bone.tail.x = child_object.location[0]
                self.current_edit_bone.tail.y = child_object.location[1]
                self.current_edit_bone.tail.z = child_object.location[2]
            else:
                self.current_edit_bone.tail.x = mean[0]
                self.current_edit_bone.tail.y = mean[1]
                self.current_edit_bone.tail.z = mean[2]

            self.queue()
            return

        # if: has multiple children
        # It creates the tail at the mean point, creates the children rigs and
        # it parents the results without connecting the bones
        self.current_edit_bone.tail.x = mean[0]
        self.current_edit_bone.tail.y = mean[1]
        self.current_edit_bone.tail.z = mean[2]

        same_type_children = []
        for linked_child in self.linked_object.children:
            child_object: BoxmanDTO = linked_child

            factory: RiggerFactoryBase = self.rigger_factory
            child_rigger = factory.create_rigger(child_object, self)
            if isinstance(child_rigger, FingerRiggerBase):
                child_rigger.control_bone = self.control_bone
                same_type_children.append(child_rigger)

            child_rigger.rig(context)
            child_bone = child_rigger.current_edit_bone
            if child_bone is not None:  # there might be boneless riggers
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = False

        # If it has only ONE child of type finger, it uses the connect
        if len(same_type_children) == 1:
            child_rigger = same_type_children[0]
            child_rigger.current_edit_bone.use_connect = True
            self.current_edit_bone.tail.x = child_rigger.linked_object.location[0]
            self.current_edit_bone.tail.y = child_rigger.linked_object.location[1]
            self.current_edit_bone.tail.z = child_rigger.linked_object.location[2]

        self.queue()
        print(f"Generated finger rig for {self.linked_object.properties.name}!")

    def queue(self) -> None:
        """
        Queue action after the fact
        """
        self.queue_parent_object_to_rig()
        self.queue_create_rotation_constraint()
        self.queue_add_bone_to_group(BoxmanExtremityTypes.HAND.value, self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.ARM_LAYER_INDEX,
                                       RiggerBase.HAND_LAYER_INDEX,
                                       RiggerBase.MINORS_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()

    def queue_create_rotation_constraint(self) -> None:
        """
        Queues the creation of the same rotation constraint
        """
        if self.control_bone is not None:
            current_bone_name = self.current_edit_bone.name  # this turns the reference into a constant
            current_bone_control_name = self.control_bone.name  # this turns the reference into a constant
            armature_name = self.armature_object_name

            self.stored_control_creation_fixture.append(
                lambda context: self.create_rotation_constraint(context, current_bone_name,
                                                                current_bone_control_name, armature_name)
            )

    @staticmethod
    def create_rotation_constraint(context, current_bone_name, current_bone_control_name, armature_name) -> None:
        """
        Creates a constraint of same rotation over the control and hides the
        """
        print(f"Attaching chain rotation control to {current_bone_name}...")
        armature = bpy.data.objects[armature_name]
        current_bone = bpy.data.objects[armature_name].pose.bones[current_bone_name]
        constraint = current_bone.constraints.new("COPY_ROTATION")
        constraint.target = armature
        constraint.subtarget = current_bone_control_name
        constraint.mix_mode = "ADD"
        constraint.owner_space = "LOCAL"
        constraint.target_space = "LOCAL"


class FingerRootRigger(FingerSectionRigger):
    """
    This rigger creates a proxy control that controls the rotations of all the other controls
    of type finger that encounters in his children
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)

    def rig(self, context) -> None:
        """
        Handles the creation of children bones the same way a finger rigger do,
        except that the bones arent hidden and the control is always created.
        """
        print(f"Generating root finger rig for {self.linked_object.properties.name}.")

        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]

        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.control_bone = newly_created[0]

        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        self.control_bone.head.x = self.current_edit_bone.head.x
        self.control_bone.head.y = self.current_edit_bone.head.y
        self.control_bone.head.z = self.current_edit_bone.head.z
        self.control_bone.name = f"{self.current_edit_bone.name}_{BoxmanRigControl.DEFAULT_CONTROL_SUFFIX}"
        self.control_bone.parent = self.parent_rigger.current_edit_bone # forced
        self.control_bone.use_connect = False

        # there ere 3 possibilities
        mean = self.get_mesh_mean_point()
        # if: it's end of a chain
        if len(self.linked_object.children) == 0:
            self.current_edit_bone.tail.x = mean[0]
            self.current_edit_bone.tail.y = mean[1]
            self.current_edit_bone.tail.z = mean[2]

            self.control_bone.tail.x = self.current_edit_bone.tail.x
            self.control_bone.tail.y = self.current_edit_bone.tail.y
            self.control_bone.tail.z = self.current_edit_bone.tail.z

            self.queue()
            return  # its end of a link

        # if: has only one child
        if len(self.linked_object.children) == 1:
            # If the child is only one, the target of the tail is the position of the next member of the chain
            # and the child bone is linked to the
            child_object: BoxmanDTO = self.linked_object.children[0]
            factory: RiggerFactoryBase = self.rigger_factory
            child_rigger = factory.create_rigger(child_object, self)
            # It chains the control to the other fingers
            if isinstance(child_rigger, FingerRiggerBase):
                child_rigger.control_bone = self.control_bone

            child_rigger.rig(context)
            child_bone = child_rigger.current_edit_bone
            if child_bone is not None:  # there might be boneless riggers
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = True  # this is only valid for the root bone
                self.current_edit_bone.tail.x = child_object.location[0]
                self.current_edit_bone.tail.y = child_object.location[1]
                self.current_edit_bone.tail.z = child_object.location[2]

                self.control_bone.tail.x = self.current_edit_bone.tail.x
                self.control_bone.tail.y = self.current_edit_bone.tail.y
                self.control_bone.tail.z = self.current_edit_bone.tail.z
            else:
                self.current_edit_bone.tail.x = mean[0]
                self.current_edit_bone.tail.y = mean[1]
                self.current_edit_bone.tail.z = mean[2]

                self.control_bone.tail.x = self.current_edit_bone.tail.x
                self.control_bone.tail.y = self.current_edit_bone.tail.y
                self.control_bone.tail.z = self.current_edit_bone.tail.z

            self.queue()
            return

        # if: has multiple children
        # It creates the tail at the mean point, creates the children rigs and
        # it parents the results without connecting the bones
        self.current_edit_bone.tail.x = mean[0]
        self.current_edit_bone.tail.y = mean[1]
        self.current_edit_bone.tail.z = mean[2]

        same_type_children = []
        for linked_child in self.linked_object.children:
            child_object: BoxmanDTO = linked_child

            factory: RiggerFactoryBase = self.rigger_factory
            child_rigger = factory.create_rigger(child_object, self)
            if isinstance(child_rigger, FingerRiggerBase):
                child_rigger.control_bone = self.control_bone
                same_type_children.append(child_rigger)

            child_rigger.rig(context)
            child_bone = child_rigger.current_edit_bone
            if child_bone is not None:  # there might be boneless riggers
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = False

        # If it has only ONE child of type finger, it uses the connect
        if len(same_type_children) == 1:
            child_rigger = same_type_children[0]
            child_rigger.current_edit_bone.use_connect = True
            self.current_edit_bone.tail.x = child_rigger.linked_object.location[0]
            self.current_edit_bone.tail.y = child_rigger.linked_object.location[1]
            self.current_edit_bone.tail.z = child_rigger.linked_object.location[2]

        self.queue()
        print(f"Generated root finger rig for {self.linked_object.properties.name}!")

    def queue(self) -> None:
        """
        Queue action after the fact
        """
        self.queue_parent_object_to_rig()
        self.queue_attach_shape_to_control()
        self.queue_create_rotation_constraint()
        self.queue_add_bone_to_group(BoxmanExtremityTypes.HAND.value, self.control_bone.name)
        self.queue_add_bone_to_group(BoxmanExtremityTypes.HAND.value, self.current_edit_bone.name)

        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.ARM_LAYER_INDEX,
                                       RiggerBase.HAND_LAYER_INDEX,
                                       RiggerBase.MINORS_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.ARM_LAYER_INDEX,
                                       RiggerBase.HAND_LAYER_INDEX,
                                       RiggerBase.MINORS_LAYER_INDEX,
                                       RiggerBase.CONTROL_LAYER_INDEX],
                                      self.control_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()

    def queue_attach_shape_to_control(self) -> None:
        """
        Queues the assignment of the default ring to the current bone.
        """
        control_bone_name = self.control_bone.name  # this turns the reference into a constant
        armature_name = self.armature_object_name
        self.stored_control_creation_fixture.append(
            lambda context: self.attach_shape_to_control(context, control_bone_name, armature_name)
        )

    @staticmethod
    def attach_shape_to_control(context, control_bone_name, armature_name) -> None:
        """
        Creates a roll control of half a typical size
        """
        print(f"Attaching default ring control to {control_bone_name}...")
        name = RootRigger.get_default_control_name(armature_name)
        bpy.data.objects[armature_name].pose.bones[control_bone_name].custom_shape = bpy.data.objects[name]
        bpy.data.objects[armature_name].pose.bones[control_bone_name].custom_shape_scale = 0.5

# endregion

# region Leg
# TODO: MOVE THIS TO ANOTHER FILE

class ThighRigger(DefaultRigger):
    """
    The Thigh rigger only holds the femur bone, that will be un-hidden.
    Its purpose is only to be a bridge between the radius bone and
    whatever its in between. Its also used to type check the parent of the radius shin
    so it can set the Iks controls
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        self.mandatory = []
        self.non_mandatory = []

    def verify_chain(self) -> None:
        """
        Checks for mandatory children
        """
        if len(self.linked_object.children) == 0:
            raise RiggerException(self, f"This rigger requires a child to operate.")

        self.mandatory = [x for x in self.linked_object.children
                          if x.properties.joint_type == BoxmanJointTypes.LEG_SHIN.value]

        self.non_mandatory = [x for x in self.linked_object.children
                              if x.properties.joint_type != BoxmanJointTypes.LEG_SHIN.value]

        if len(self.mandatory) != 1:
            raise RiggerException(self, f"This rigger requires ONE a "
                                        f"child of type {BoxmanJointTypes.LEG_SHIN.value}.")

    def rig(self, context) -> None:
        """
        Similar to the default rig, only difference is that it expects at least one child of radius type.
        The idea is that it guaranties that the radius has at least two bones for the IK.
        """
        print(f"Generating femur rig for {self.linked_object.properties.name}...")

        self.verify_chain()
        # We create the bone as in the default scenario
        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]
        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        child_object: BoxmanDTO = self.mandatory[0]
        factory: RiggerFactoryBase = self.rigger_factory
        child_rigger: RiggerBase = factory.create_rigger(child_object, self)
        child_rigger.rig(context)
        # After all happened
        child_bone = child_rigger.current_edit_bone
        child_bone.parent = self.current_edit_bone
        child_bone.use_connect = True  # this is only valid for the root bone
        self.current_edit_bone.tail.x = child_object.location[0]
        self.current_edit_bone.tail.y = child_object.location[1]
        self.current_edit_bone.tail.z = child_object.location[2]

        # then we handle the non mandatory children
        for child in self.non_mandatory:
            child_non_mandatory_rigger: RiggerBase = factory.create_rigger(child, self)
            child_non_mandatory_rigger.rig(context)
            # After all happened
            if child_non_mandatory_rigger.current_edit_bone is not None:
                child_bone = child_non_mandatory_rigger.current_edit_bone
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = False

        self.queue_parent_object_to_rig()  # this is the same
        self.queue_add_bone_to_group(BoxmanExtremityTypes.LEG.value, self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.MAYORS_LAYER_INDEX,
                                       RiggerBase.LEG_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()
        print(f"Generated femur rig for {self.linked_object.properties.name}!")


class KneeRigger(PoleTargetRigger):
    """
    The knee rigger is a dead end with a hidden bone that places a pole target.
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        if len(self.linked_object.children) > 0:
            print("The knee rigger is a dead end! potential data loss detected!!!!")

    def rig(self, context) -> None:
        """
        Creates a hidden bone and creates a pole target control
        """
        print(f"Generating knee rig for {self.linked_object.properties.name}...")
        # this works as the default rigger of a disconnected parent
        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]

        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        mean = self.get_mesh_mean_point()
        self.current_edit_bone.tail.x = mean[0]
        self.current_edit_bone.tail.y = mean[1]
        self.current_edit_bone.tail.z = mean[2]

        self.create_control_bone()
        self.control_bone.parent = self.absolute_root_rigger.current_edit_bone
        self.control_bone.use_connect = False

        self.queue_hide_current_bone()
        self.queue_attach_default_shape()
        self.queue_add_bone_to_group(BoxmanExtremityTypes.LEG.value, self.current_edit_bone.name)
        self.queue_add_bone_to_group(BoxmanExtremityTypes.LEG.value, self.control_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.LEG_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.MAYORS_LAYER_INDEX,
                                       RiggerBase.CONTROL_LAYER_INDEX,
                                       RiggerBase.LEG_LAYER_INDEX],
                                      self.control_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()
        print(f"Generated knee rig for {self.linked_object.properties.name}...")


class FeetRigger(IkControlRigger):
    """
    Target of IK for the leg. It detaches the foot results.
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)

    def rig(self, context) -> None:
        """
        Creates the IK target control and
        """
        super().rig(context)

    def queue(self) -> None:
        """
        Actions to queue after the fact
        """
        self.queue_parent_object_to_rig()
        self.queue_attach_default_shape()
        self.create_control_bone()
        self.control_bone.parent = self.absolute_root_rigger.current_edit_bone
        self.control_bone.use_connect = False  # this is only valid for the root bone
        self.queue_create_ik_constraint(angle=0.0)
        self.queue_create_copy_location_constraint()
        self.queue_add_rotation_constraint()
        self.queue_add_bone_to_group(BoxmanExtremityTypes.FEET.value, self.current_edit_bone.name)
        self.queue_add_bone_to_group(BoxmanExtremityTypes.LEG.value, self.control_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.LEG_LAYER_INDEX,
                                       RiggerBase.FEET_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.MAYORS_LAYER_INDEX,
                                       RiggerBase.LEG_LAYER_INDEX,
                                       RiggerBase.CONTROL_LAYER_INDEX],
                                      self.control_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()

    def queue_create_copy_location_constraint(self) -> None:
        """
        Queue the creation of an IK constraint.
        """
        armature_name = self.armature_object_name
        current_edit_bone_name = self.current_edit_bone.name  # this turns the reference into a constant
        parent_bone_name = self.parent_rigger.current_edit_bone.name  # this turns the reference into a constant

        self.stored_control_creation_fixture.append(
            lambda context: self.create_copy_location_constraint(context, parent_bone_name,
                                                                 current_edit_bone_name, armature_name)
        )

    @staticmethod
    def create_copy_location_constraint(context, parent_bone_name, current_edit_bone_name, armature_name) -> None:
        """
        Creates a copy location constraint to the parent bone
        """
        armature = bpy.data.objects[armature_name]
        target_bone = bpy.data.objects[armature_name].pose.bones[current_edit_bone_name]
        constraint = target_bone.constraints.new("COPY_LOCATION")
        constraint.head_tail = 1.0
        constraint.target = armature
        constraint.subtarget = parent_bone_name

    def queue_add_rotation_constraint(self):
        """
        Queues the addition of a constraint that adds the rotation of the IK controller to the main bone
        """
        armature_name = self.armature_object_name
        current_edit_bone_name = self.current_edit_bone.name  # this turns the reference into a constant
        ik_control_bone_name = self.control_bone.name  # this turns the reference into a constant

        self.stored_control_creation_fixture.append(
            lambda context: self.add_rotation_constraint(context, ik_control_bone_name,
                                                         current_edit_bone_name, armature_name)
        )

    @staticmethod
    def add_rotation_constraint(context, ik_control_bone_name, current_edit_bone_name, armature_name) -> None:
        """
        Creates a copy location constraint to the parent bone
        """
        print(f"Adding rotation constraints to {current_edit_bone_name}...")
        armature = bpy.data.objects[armature_name]
        current_bone = bpy.data.objects[armature_name].pose.bones[current_edit_bone_name]
        constraint = current_bone.constraints.new("COPY_ROTATION")
        constraint.target = armature
        constraint.subtarget = ik_control_bone_name
        constraint.mix_mode = "ADD"
        constraint.owner_space = "LOCAL"
        constraint.target_space = "LOCAL"


class ShinRigger(DefaultRigger):
    """
    The radius creates a default rig expecting one hand root child, to use for IK constraints.
    If it has an elbow child, it uses it as pole target.
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        self.mandatory = []
        self.non_mandatory = []

    def verify_chain(self) -> None:
        """
        Checks for mandatory bones
        """
        if len(self.linked_object.children) == 0:
            raise RiggerException(self, f"This rigger requires a child to operate.")

        self.mandatory = [x for x in self.linked_object.children
                          if x.properties.joint_type == BoxmanJointTypes.FOOT_ROOT.value]

        self.non_mandatory = [x for x in self.linked_object.children
                              if x.properties.joint_type != BoxmanJointTypes.FOOT_ROOT.value]

        if len(self.mandatory) != 1:
            raise RiggerException(self, f"This rigger requires ONE a "
                                        f"child of type {BoxmanJointTypes.FOOT_ROOT.value}.")

    def rig(self, context) -> None:
        """
        Acts like de default rigger, expecting a hand root to link and use as IK control.
        The pole target is optional, and the bone is not invisible so that the pole target can be adjusted if needed.
        """
        print(f"Generating shin rig for {self.linked_object.properties.name}...")
        self.verify_chain()
        # We create the bone as in the default scenario
        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]
        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        # we handle the non mandatory first to have the name of the pole target, if any
        pole_target_bone = None
        pole_target_offset = 0
        # handle the non mandatory children
        factory: RiggerFactoryBase = self.rigger_factory
        for child in self.non_mandatory:
            child_non_mandatory_rigger: RiggerBase = factory.create_rigger(child, self)
            child_non_mandatory_rigger.rig(context)
            # After all happened
            if child_non_mandatory_rigger.current_edit_bone is not None:
                child_bone = child_non_mandatory_rigger.current_edit_bone
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = False  # the connect is going to the mandatory
            if isinstance(child_non_mandatory_rigger, KneeRigger):
                pole_target_bone = child_non_mandatory_rigger.control_bone
                pole_target_offset = child_non_mandatory_rigger.offset_sign

        child_object: BoxmanDTO = self.mandatory[0]
        factory: RiggerFactoryBase = self.rigger_factory
        child_rigger = factory.create_rigger(child_object, self)
        child_rigger.pole_target_bone = pole_target_bone
        child_rigger.pole_target_offset = pole_target_offset
        # if there is only one, there is no need for a pole target
        child_rigger.rig(context)
        child_bone = child_rigger.current_edit_bone
        child_bone.parent = self.absolute_root_rigger.current_edit_bone
        child_bone.use_connect = False  # this is only valid for the root bone

        self.current_edit_bone.tail.x = child_object.location[0]
        self.current_edit_bone.tail.y = child_object.location[1]
        self.current_edit_bone.tail.z = child_object.location[2]
        self.queue_parent_object_to_rig()
        self.queue_add_bone_to_group(BoxmanExtremityTypes.LEG.value, self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.LEG_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()
        print(f"Generated shin rig for {self.linked_object.properties.name}!")


class ToeRiggerBase(FingerRiggerBase):
    """
    Base class of the finger riggers
    """
    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        self.control_bone = None

    def rig(self, context) -> None:
        """
        Direct inheritance
        """
        raise NotImplementedError()


class ToeSectionRigger(FingerSectionRigger):
    """
    The finger rigger acts as a default rigger that doesnt hide the bone.
    It can accept and pass a rotation control to children of the same type.
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)

    def rig(self, context) -> None:
        """
        Direct inheritance
        """
        super().rig(context)
        # override

    def queue(self) -> None:
        """
        Queue action after the fact
        """
        self.queue_parent_object_to_rig()
        self.queue_create_rotation_constraint()
        self.queue_add_bone_to_group(BoxmanExtremityTypes.FEET.value, self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.LEG_LAYER_INDEX,
                                       RiggerBase.FEET_LAYER_INDEX,
                                       RiggerBase.MINORS_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()


class ToeRootRigger(FingerRootRigger):
    """
    This rigger creates a proxy control that controls the rotations of all the other controls
    of type finger that encounters in his children
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)

    def rig(self, context) -> None:
        """
        Direct inheritance
        """
        super().rig(context)

    def queue(self) -> None:
        """
        Queue action after the fact
        """
        self.queue_parent_object_to_rig()
        self.queue_attach_shape_to_control()
        self.queue_create_rotation_constraint()
        self.queue_add_bone_to_group(BoxmanExtremityTypes.FEET.value, self.control_bone.name)
        self.queue_add_bone_to_group(BoxmanExtremityTypes.FEET.value, self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.LEG_LAYER_INDEX,
                                       RiggerBase.FEET_LAYER_INDEX,
                                       RiggerBase.MINORS_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.LEG_LAYER_INDEX,
                                       RiggerBase.FEET_LAYER_INDEX,
                                       RiggerBase.MINORS_LAYER_INDEX,
                                       RiggerBase.CONTROL_LAYER_INDEX],
                                      self.control_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()

# endregion


# region Torso

class SpineRiggerBase(DefaultRigger):
    """
    Base rigger for the spine elements
    """
    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        self.control_bone = None
        self.local_control_root = self

    def rig(self, context) -> None:
        """
        Used the default rigger
        """
        raise NotImplementedError()

    def queue_create_rotation_constraint(self, influence_factor: float = 1.0) -> None:
        """
        Queues the creation of the same rotation constraint
        """
        if self.control_bone is not None:
            current_bone_name = self.current_edit_bone.name  # this turns the reference into a constant
            current_bone_control_name = self.control_bone.name  # this turns the reference into a constant
            armature_name = self.armature_object_name
            influence_factor_const = influence_factor

            self.stored_control_creation_fixture.append(
                lambda context: self.create_rotation_constraint(context, current_bone_name,
                                                                current_bone_control_name, armature_name,
                                                                influence_factor_const)
            )

    @staticmethod
    def create_rotation_constraint(context, current_bone_name,
                                   current_bone_control_name, armature_name, influence_factor) -> None:
        """
        Creates a constraint of same rotation over the control and hides the
        """
        print(f"Attaching chain rotation control to {current_bone_name}...")
        armature = bpy.data.objects[armature_name]
        current_bone = bpy.data.objects[armature_name].pose.bones[current_bone_name]
        constraint = current_bone.constraints.new("COPY_ROTATION")
        constraint.target = armature
        constraint.subtarget = current_bone_control_name
        constraint.mix_mode = "ADD"
        constraint.owner_space = "WORLD"
        constraint.target_space = "LOCAL"
        constraint.influence = influence_factor


class SpineSectionRigger(SpineRiggerBase):
    """
    It creates a control chain with half additive rotations on a control if inherited.
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)

    def rig(self, context) -> None:
        """
        Handles the creation of children bones the same way a default rigger do,
        except that the bones arent hidden
        """
        print(f"Generating spine rig for {self.linked_object.properties.name}.")

        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]

        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        # there ere 3 possibilities
        mean = self.get_mesh_mean_point()
        # if: it's end of a chain
        if len(self.linked_object.children) == 0:
            self.current_edit_bone.tail.x = mean[0]
            self.current_edit_bone.tail.y = mean[1]
            self.current_edit_bone.tail.z = mean[2]

            self.queue()
            return  # its end of a link

        # if: has only one child
        if len(self.linked_object.children) == 1:
            # If the child is only one, the target of the tail is the position of the next member of the chain
            # and the child bone is linked to the
            child_object: BoxmanDTO = self.linked_object.children[0]
            factory: RiggerFactoryBase = self.rigger_factory
            child_rigger = factory.create_rigger(child_object, self)
            # It chains the control to the other fingers
            if isinstance(child_rigger, SpineRiggerBase):
                child_rigger.control_bone = self.control_bone

            child_rigger.rig(context)
            child_bone = child_rigger.current_edit_bone
            if child_bone is not None:  # there might be boneless riggers
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = True  # this is only valid for the root bone
                self.current_edit_bone.tail.x = child_object.location[0]
                self.current_edit_bone.tail.y = child_object.location[1]
                self.current_edit_bone.tail.z = child_object.location[2]
            else:
                self.current_edit_bone.tail.x = mean[0]
                self.current_edit_bone.tail.y = mean[1]
                self.current_edit_bone.tail.z = mean[2]

            self.queue()
            return

        # if: has multiple children
        # It creates the tail at the mean point, creates the children rigs and
        # it parents the results without connecting the bones
        self.current_edit_bone.tail.x = mean[0]
        self.current_edit_bone.tail.y = mean[1]
        self.current_edit_bone.tail.z = mean[2]

        same_type_children = []
        for linked_child in self.linked_object.children:
            child_object: BoxmanDTO = linked_child

            factory: RiggerFactoryBase = self.rigger_factory
            child_rigger = factory.create_rigger(child_object, self)
            if isinstance(child_rigger, SpineRiggerBase):
                child_rigger.control_bone = self.control_bone
                same_type_children.append(child_rigger)

            child_rigger.rig(context)
            child_bone = child_rigger.current_edit_bone
            if child_bone is not None:  # there might be boneless riggers
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = False

        # If it has only ONE child of type finger, it uses the connect
        if len(same_type_children) == 1:
            child_rigger = same_type_children[0]
            child_rigger.current_edit_bone.use_connect = True
            self.current_edit_bone.tail.x = child_rigger.linked_object.location[0]
            self.current_edit_bone.tail.y = child_rigger.linked_object.location[1]
            self.current_edit_bone.tail.z = child_rigger.linked_object.location[2]

        self.queue()
        print(f"Generated finger rig for {self.linked_object.properties.name}!")

    def queue(self) -> None:
        """
        Queue action after the fact
        """
        self.queue_parent_object_to_rig()
        self.queue_attach_default_shape()
        self.queue_create_rotation_constraint(0.5)
        self.queue_add_bone_to_group(BoxmanExtremityTypes.SPINE.value, self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.MAYORS_LAYER_INDEX,
                                       RiggerBase.SPINE_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()


class SpineRootRigger(SpineSectionRigger):
    """
    The spine root creates an invisible bone and a control box related with the typical size.
    It the bone is connected to the control that manipulates the rotations of the resulting elements
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)

    def rig(self, context) -> None:
        """
        Creates a rig similar to the default, but attaching a control bone that will apply a copy rotations and
        transpose located at the root
        """
        print(f"Generating root spine rig for {self.linked_object.properties.name}.")
        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]

        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.control_bone = newly_created[0]

        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        typical = self.get_typical_size()
        self.control_bone.head.x = self.current_edit_bone.head.x
        self.control_bone.head.y = self.current_edit_bone.head.y
        self.control_bone.head.z = self.current_edit_bone.head.z
        # positioned with
        self.control_bone.tail.x = self.control_bone.head.x
        self.control_bone.tail.y = self.control_bone.head.y + 1.0 # use absolute units?
        self.control_bone.tail.z = self.control_bone.head.z
        # parented to the absolute root
        self.control_bone.name = f"{self.current_edit_bone.name}_{BoxmanRigControl.DEFAULT_CONTROL_SUFFIX}"
        self.control_bone.parent = self.absolute_root_rigger.current_edit_bone # forced
        self.control_bone.use_connect = False

        # there ere 3 possibilities
        mean = self.get_mesh_mean_point()
        # if: it's end of a chain
        if len(self.linked_object.children) == 0:
            self.current_edit_bone.tail.x = mean[0]
            self.current_edit_bone.tail.y = mean[1]
            self.current_edit_bone.tail.z = mean[2]

            self.queue()
            return  # its end of a link

        # if: has only one child
        if len(self.linked_object.children) == 1:
            # If the child is only one, the target of the tail is the position of the next member of the chain
            # and the child bone is linked to the
            child_object: BoxmanDTO = self.linked_object.children[0]
            factory: RiggerFactoryBase = self.rigger_factory
            child_rigger = factory.create_rigger(child_object, self)
            # It chains the control to the other fingers
            if isinstance(child_rigger, SpineRiggerBase):
                child_rigger.control_bone = self.control_bone

            child_rigger.rig(context)
            child_bone = child_rigger.current_edit_bone
            if child_bone is not None:  # there might be boneless riggers
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = True  # this is only valid for the root bone
                self.current_edit_bone.tail.x = child_object.location[0]
                self.current_edit_bone.tail.y = child_object.location[1]
                self.current_edit_bone.tail.z = child_object.location[2]
            else:
                self.current_edit_bone.tail.x = mean[0]
                self.current_edit_bone.tail.y = mean[1]
                self.current_edit_bone.tail.z = mean[2]

            self.queue()
            return

        # if: has multiple children
        # It creates the tail at the mean point, creates the children rigs and
        # it parents the results without connecting the bones
        self.current_edit_bone.tail.x = mean[0]
        self.current_edit_bone.tail.y = mean[1]
        self.current_edit_bone.tail.z = mean[2]

        same_type_children = []
        for linked_child in self.linked_object.children:
            child_object: BoxmanDTO = linked_child

            factory: RiggerFactoryBase = self.rigger_factory
            child_rigger = factory.create_rigger(child_object, self)
            if isinstance(child_rigger, SpineRiggerBase):
                child_rigger.control_bone = self.control_bone
                same_type_children.append(child_rigger)

            child_rigger.rig(context)
            child_bone = child_rigger.current_edit_bone
            if child_bone is not None:  # there might be boneless riggers
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = False

        # If it has only ONE child of type finger, it uses the connect
        if len(same_type_children) == 1:
            child_rigger = same_type_children[0]
            child_rigger.current_edit_bone.use_connect = True
            self.current_edit_bone.tail.x = child_rigger.linked_object.location[0]
            self.current_edit_bone.tail.y = child_rigger.linked_object.location[1]
            self.current_edit_bone.tail.z = child_rigger.linked_object.location[2]

        self.queue()
        print(f"Generated root spine rig for {self.linked_object.properties.name}!")

    def queue(self) -> None:
        """
        Actions to queue after the creation of the bones and controls
        """
        self.queue_create_proportion_control_shape()
        self.queue_hide_template_mesh()
        self.queue_attach_shape_to_control()
        self.queue_parent_object_to_rig()
        self.queue_hide_current_bone()
        self.queue_create_rotation_constraint()
        self.queue_create_location_constraint()
        self.queue_add_bone_to_group(BoxmanExtremityTypes.SPINE.value, self.current_edit_bone.name)
        self.queue_add_bone_to_group(BoxmanExtremityTypes.SPINE.value, self.control_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.SPINE_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.MAYORS_LAYER_INDEX,
                                       RiggerBase.CONTROL_LAYER_INDEX,
                                       RiggerBase.SPINE_LAYER_INDEX],
                                      self.control_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()

    @staticmethod
    def get_control_shape_name(armature_name, linked_name) -> str:
        """
        Gets the name of the hidden control shape
        """
        return f"{armature_name}_{linked_name}_{BoxmanRigControl.SPINE_CONTROL_SUFFIX}" \
               f"_{BoxmanRigControl.DEFAULT_CONTROL_SUFFIX}"

    def queue_create_proportion_control_shape(self) -> None:
        """
        Creates a proportion bounding box for the current hip control, it creates a mesh, so it goes in the object
        mode fixture.
        It Also groups the control to the collection
        """
        linked_name = self.linked_object.get_object_name()
        linked_location = self.linked_object.location
        linked_vertex_array = self.linked_object.vertex_list
        armature_name = self.armature_object_name
        self.stored_mesh_creation_fixture.append(
            lambda context: self.create_proportion_control_shape(context,
                                                                 linked_name,
                                                                 linked_location,
                                                                 linked_vertex_array,
                                                                 armature_name)
        )
        control_name = self.get_control_shape_name(armature_name, linked_name)
        self.queue_link_mesh_to_collection(self.get_control_mesh_collection_name(), control_name)
        self.queue_unlink_mesh_from_collection(mesh_name=control_name)

    @staticmethod
    def create_proportion_control_shape(context,
                                        linked_name,
                                        linked_location,
                                        linked_vertex_array,
                                        armature_name) -> None:
        """
        Adds a control for each type of required render.
        """
        # adds the proportional cube
        print(f"Adding {BoxmanRigControl.SPINE_CONTROL_SUFFIX} control shape...")
        control_name = SpineRootRigger.get_control_shape_name(armature_name, linked_name)
        ring_data = BoxmanRigControlFactory.get_unit_cube(control_name)
        ring_data.scale_to_boxman(linked_vertex_array)
        ring_object = ring_data.add_as_mesh(context)
        ring_object.location.x = linked_location[0] + 1.0
        ring_object.location.y = linked_location[1]
        ring_object.location.z = linked_location[2]

    def queue_hide_template_mesh(self) -> None:
        """
        Queues the action of hide all meshes once created
        """
        armature_name = self.armature_object_name
        linked_name = self.linked_object.get_object_name()
        self.stored_mesh_creation_fixture.append(
            lambda context: self.hide_template_mesh(context, armature_name, linked_name)
        )

    @staticmethod
    def hide_template_mesh(context, armature_name, linked_name) -> None:
        """
        Hides all created control meshes
        """
        # TODO: Add the other control shapes and make it into a factory class, this is terrible!
        print(f"Hiding {BoxmanRigControl.SPINE_CONTROL_SUFFIX} control shape...")
        spine_name = SpineRootRigger.get_control_shape_name(armature_name, linked_name)
        bpy.data.objects[spine_name].hide_viewport = True
        bpy.data.objects[spine_name].hide_render = True

    def queue_attach_shape_to_control(self) -> None:
        """
        Queues the assignment of the default ring to the current bone.
        """
        control_bone_name = self.control_bone.name  # this turns the reference into a constant
        armature_name = self.armature_object_name
        linked_name = self.linked_object.get_object_name()
        self.stored_control_creation_fixture.append(
            lambda context: self.attach_shape_to_control(context, control_bone_name, armature_name, linked_name)
        )

    @staticmethod
    def attach_shape_to_control(context, control_bone_name, armature_name, linked_name) -> None:
        """
        Creates a roll control of half a typical size
        """
        print(f"Attaching default ring control to {control_bone_name}...")
        spine_name = SpineRootRigger.get_control_shape_name(armature_name, linked_name)
        bpy.data.objects[armature_name].pose.bones[control_bone_name].custom_shape = bpy.data.objects[spine_name]
        bpy.data.objects[armature_name].pose.bones[control_bone_name].custom_shape_scale = 1.0

    def queue_create_location_constraint(self) -> None:
        """
        Queues the creation of the same rotation constraint
        """
        current_bone_name = self.current_edit_bone.name  # this turns the reference into a constant
        current_bone_control_name = self.control_bone.name  # this turns the reference into a constant
        armature_name = self.armature_object_name

        self.stored_control_creation_fixture.append(
            lambda context: self.create_location_constraint(context, current_bone_name,
                                                            current_bone_control_name, armature_name)
            )

    @staticmethod
    def create_location_constraint(context, current_bone_name,
                                   current_bone_control_name, armature_name) -> None:
        """
        Creates a constraint that make the original bone follow the control
        """
        print(f"Attaching chain rotation control to {current_bone_name}...")
        armature = bpy.data.objects[armature_name]
        current_bone = bpy.data.objects[armature_name].pose.bones[current_bone_name]
        constraint = current_bone.constraints.new("COPY_LOCATION")
        constraint.target = armature
        constraint.subtarget = current_bone_control_name

# endregion


# region Head
# TODO: THIS IS BOILERPLATE! I need to find a cleaner implementation

class NeckRiggerBase(DefaultRigger):
    """
    Base rigger for the spine elements
    """
    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        self.control_bone = None

    def rig(self, context) -> None:
        """
        Used the default rigger
        """
        raise NotImplementedError()

    def queue_create_rotation_constraint(self, influence_factor: float = 1.0) -> None:
        """
        Queues the creation of the same rotation constraint
        """
        if self.control_bone is not None:
            current_bone_name = self.current_edit_bone.name  # this turns the reference into a constant
            current_bone_control_name = self.control_bone.name  # this turns the reference into a constant
            armature_name = self.armature_object_name
            influence_factor_const = influence_factor

            self.stored_control_creation_fixture.append(
                lambda context: self.create_rotation_constraint(context, current_bone_name,
                                                                current_bone_control_name, armature_name,
                                                                influence_factor_const)
            )

    @staticmethod
    def create_rotation_constraint(context, current_bone_name,
                                   current_bone_control_name, armature_name, influence_factor) -> None:
        """
        Creates a constraint of same rotation over the control and hides the
        """
        print(f"Attaching chain rotation control to {current_bone_name}...")
        armature = bpy.data.objects[armature_name]
        current_bone = bpy.data.objects[armature_name].pose.bones[current_bone_name]
        constraint = current_bone.constraints.new("COPY_ROTATION")
        constraint.target = armature
        constraint.subtarget = current_bone_control_name
        constraint.mix_mode = "ADD"
        constraint.owner_space = "WORLD"
        constraint.target_space = "LOCAL"
        constraint.influence = influence_factor


class NeckSectionRigger(NeckRiggerBase):
    """
    It creates a control chain with half additive rotations on a control if inherited.
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)

    def rig(self, context) -> None:
        """
        Handles the creation of children bones the same way a default rigger do,
        except that the bones arent hidden
        """
        print(f"Generating neck rig for {self.linked_object.properties.name}.")

        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]

        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        # there ere 3 possibilities
        mean = self.get_mesh_mean_point()
        # if: it's end of a chain
        if len(self.linked_object.children) == 0:
            self.current_edit_bone.tail.x = mean[0]
            self.current_edit_bone.tail.y = mean[1]
            self.current_edit_bone.tail.z = mean[2]

            self.queue()
            return  # its end of a link

        # if: has only one child
        if len(self.linked_object.children) == 1:
            # If the child is only one, the target of the tail is the position of the next member of the chain
            # and the child bone is linked to the
            child_object: BoxmanDTO = self.linked_object.children[0]
            factory: RiggerFactoryBase = self.rigger_factory
            child_rigger = factory.create_rigger(child_object, self)
            # It chains the control to the other fingers
            if isinstance(child_rigger, NeckRiggerBase):
                child_rigger.control_bone = self.control_bone

            child_rigger.rig(context)
            child_bone = child_rigger.current_edit_bone
            if child_bone is not None:  # there might be boneless riggers
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = True  # this is only valid for the root bone
                self.current_edit_bone.tail.x = child_object.location[0]
                self.current_edit_bone.tail.y = child_object.location[1]
                self.current_edit_bone.tail.z = child_object.location[2]
            else:
                self.current_edit_bone.tail.x = mean[0]
                self.current_edit_bone.tail.y = mean[1]
                self.current_edit_bone.tail.z = mean[2]

            self.queue()
            return

        # if: has multiple children
        # It creates the tail at the mean point, creates the children rigs and
        # it parents the results without connecting the bones
        self.current_edit_bone.tail.x = mean[0]
        self.current_edit_bone.tail.y = mean[1]
        self.current_edit_bone.tail.z = mean[2]

        same_type_children = []
        for linked_child in self.linked_object.children:
            child_object: BoxmanDTO = linked_child

            factory: RiggerFactoryBase = self.rigger_factory
            child_rigger = factory.create_rigger(child_object, self)
            if isinstance(child_rigger, NeckRiggerBase):
                child_rigger.control_bone = self.control_bone
                same_type_children.append(child_rigger)

            child_rigger.rig(context)
            child_bone = child_rigger.current_edit_bone
            if child_bone is not None:  # there might be boneless riggers
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = False

        # If it has only ONE child of type finger, it uses the connect
        if len(same_type_children) == 1:
            child_rigger = same_type_children[0]
            child_rigger.current_edit_bone.use_connect = True
            self.current_edit_bone.tail.x = child_rigger.linked_object.location[0]
            self.current_edit_bone.tail.y = child_rigger.linked_object.location[1]
            self.current_edit_bone.tail.z = child_rigger.linked_object.location[2]

        self.queue()
        print(f"Generated neck rig for {self.linked_object.properties.name}!")

    def queue(self) -> None:
        """
        Queue action after the fact
        """
        self.queue_parent_object_to_rig()
        self.queue_attach_default_shape()
        self.queue_create_rotation_constraint()
        self.queue_add_bone_to_group(BoxmanExtremityTypes.HEAD.value, self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.HEAD_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()


class NeckRootRigger(NeckSectionRigger):
    """
    The spine root creates an invisible bone and a control box related with the typical size.
    It the bone is connected to the control that manipulates the rotations of the resulting elements
    """
    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)

    def rig(self, context) -> None:
        """
        Creates a rig similar to the default, but attaching a control bone that will apply a copy rotations and
        transpose located at the root
        """
        print(f"Generating root neck rig for {self.linked_object.properties.name}.")

        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]

        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.control_bone = newly_created[0]

        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        typical = self.get_typical_size()
        self.control_bone.head.x = self.current_edit_bone.head.x
        self.control_bone.head.y = self.current_edit_bone.head.y
        self.control_bone.head.z = self.current_edit_bone.head.z
        # positioned with
        self.control_bone.tail.x = self.control_bone.head.x
        self.control_bone.tail.y = self.control_bone.head.y + 1.0 # use absolute units?
        self.control_bone.tail.z = self.control_bone.head.z
        # parented to the absolute root
        self.control_bone.name = f"{self.current_edit_bone.name}_{BoxmanRigControl.DEFAULT_CONTROL_SUFFIX}"
        self.control_bone.parent = self.parent_rigger.current_edit_bone
        self.control_bone.use_connect = False

        # there ere 3 possibilities
        mean = self.get_mesh_mean_point()
        # if: it's end of a chain
        if len(self.linked_object.children) == 0:
            self.current_edit_bone.tail.x = mean[0]
            self.current_edit_bone.tail.y = mean[1]
            self.current_edit_bone.tail.z = mean[2]

            self.queue()
            return  # its end of a link

        # if: has only one child
        if len(self.linked_object.children) == 1:
            # If the child is only one, the target of the tail is the position of the next member of the chain
            # and the child bone is linked to the
            child_object: BoxmanDTO = self.linked_object.children[0]
            factory: RiggerFactoryBase = self.rigger_factory
            child_rigger = factory.create_rigger(child_object, self)
            # It chains the control to the other fingers
            if isinstance(child_rigger, NeckRiggerBase):
                child_rigger.control_bone = self.control_bone

            child_rigger.rig(context)
            child_bone = child_rigger.current_edit_bone
            if child_bone is not None:  # there might be boneless riggers
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = True  # this is only valid for the root bone
                self.current_edit_bone.tail.x = child_object.location[0]
                self.current_edit_bone.tail.y = child_object.location[1]
                self.current_edit_bone.tail.z = child_object.location[2]
            else:
                self.current_edit_bone.tail.x = mean[0]
                self.current_edit_bone.tail.y = mean[1]
                self.current_edit_bone.tail.z = mean[2]

            self.queue()
            return

        # if: has multiple children
        # It creates the tail at the mean point, creates the children rigs and
        # it parents the results without connecting the bones
        self.current_edit_bone.tail.x = mean[0]
        self.current_edit_bone.tail.y = mean[1]
        self.current_edit_bone.tail.z = mean[2]

        same_type_children = []
        for linked_child in self.linked_object.children:
            child_object: BoxmanDTO = linked_child

            factory: RiggerFactoryBase = self.rigger_factory
            child_rigger = factory.create_rigger(child_object, self)
            if isinstance(child_rigger, NeckRiggerBase):
                child_rigger.control_bone = self.control_bone
                same_type_children.append(child_rigger)

            child_rigger.rig(context)
            child_bone = child_rigger.current_edit_bone
            if child_bone is not None:  # there might be boneless riggers
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = False

        # If it has only ONE child of type finger, it uses the connect
        if len(same_type_children) == 1:
            child_rigger = same_type_children[0]
            child_rigger.current_edit_bone.use_connect = True
            self.current_edit_bone.tail.x = child_rigger.linked_object.location[0]
            self.current_edit_bone.tail.y = child_rigger.linked_object.location[1]
            self.current_edit_bone.tail.z = child_rigger.linked_object.location[2]

        self.queue()
        print(f"Generated root neck rig for {self.linked_object.properties.name}!")

    def queue(self) -> None:
        """
        Actions to queue after the creation of the bones and controls
        """
        self.queue_create_proportion_control_shape()
        self.queue_hide_template_mesh()
        self.queue_attach_shape_to_control()
        self.queue_parent_object_to_rig()
        self.queue_hide_current_bone()
        self.queue_create_rotation_constraint()
        self.queue_create_location_constraint()
        self.queue_add_bone_to_group(BoxmanExtremityTypes.HEAD.value, self.current_edit_bone.name)
        self.queue_add_bone_to_group(BoxmanExtremityTypes.HEAD.value, self.control_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.HEAD_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.HEAD_LAYER_INDEX,
                                       RiggerBase.MAYORS_LAYER_INDEX,
                                       RiggerBase.CONTROL_LAYER_INDEX],
                                      self.control_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()

    @staticmethod
    def get_control_shape_name(armature_name, linked_name) -> str:
        """
        Gets the name of the hidden control shape
        """
        return f"{armature_name}_{linked_name}_{BoxmanRigControl.NECK_CONTROL_SUFFIX}" \
               f"_{BoxmanRigControl.DEFAULT_CONTROL_SUFFIX}"

    def queue_create_proportion_control_shape(self) -> None:
        """
        Creates a proportion bounding box for the current hip control, it creates a mesh, so it goes in the object
        mode fixture
        """
        linked_name = self.linked_object.properties.name
        linked_location = self.linked_object.location
        linked_vertex_array = self.linked_object.vertex_list
        armature_name = self.armature_object_name
        self.stored_mesh_creation_fixture.append(
            lambda context: self.create_proportion_control_shape(context,
                                                                 linked_name,
                                                                 linked_location,
                                                                 linked_vertex_array,
                                                                 armature_name)
        )
        control_name = self.get_control_shape_name(armature_name, linked_name)
        self.queue_link_mesh_to_collection(self.get_control_mesh_collection_name(), control_name)
        self.queue_unlink_mesh_from_collection(mesh_name=control_name)

    @staticmethod
    def create_proportion_control_shape(context,
                                        linked_name,
                                        linked_location,
                                        linked_vertex_array,
                                        armature_name) -> None:
        """
        Adds a control for each type of required render.
        """
        # adds the proportional cube
        print(f"Adding {BoxmanRigControl.NECK_CONTROL_SUFFIX} control shape...")
        name = NeckRootRigger.get_control_shape_name(armature_name, linked_name)
        ring_data = BoxmanRigControlFactory.get_unit_cube(name)
        ring_data.scale_to_boxman(linked_vertex_array)
        ring_object = ring_data.add_as_mesh(context)
        ring_object.location.x = linked_location[0] + 1.0
        ring_object.location.y = linked_location[1]
        ring_object.location.z = linked_location[2]

    def queue_hide_template_mesh(self) -> None:
        """
        Queues the action of hide all meshes once created
        """
        armature_name = self.armature_object_name
        linked_name = self.linked_object.properties.name
        self.stored_mesh_creation_fixture.append(
            lambda context: self.hide_template_mesh(context, armature_name, linked_name)
        )

    @staticmethod
    def hide_template_mesh(context, armature_name, linked_name) -> None:
        """
        Hides all created control meshes
        """
        # TODO: Add the other control shapes and make it into a factory class, this is terrible!
        print(f"Hiding {BoxmanRigControl.SPINE_CONTROL_SUFFIX} control shape...")
        spine_name = NeckRootRigger.get_control_shape_name(armature_name, linked_name)
        bpy.data.objects[spine_name].hide_viewport = True
        bpy.data.objects[spine_name].hide_render = True

    def queue_attach_shape_to_control(self) -> None:
        """
        Queues the assignment of the default ring to the current bone.
        """
        control_bone_name = self.control_bone.name  # this turns the reference into a constant
        armature_name = self.armature_object_name
        linked_name = self.linked_object.properties.name
        self.stored_control_creation_fixture.append(
            lambda context: self.attach_shape_to_control(context, control_bone_name, armature_name, linked_name)
        )

    @staticmethod
    def attach_shape_to_control(context, control_bone_name, armature_name, linked_name) -> None:
        """
        Creates a roll control of half a typical size
        """
        print(f"Attaching default ring control to {control_bone_name}...")
        name = NeckRootRigger.get_control_shape_name(armature_name, linked_name)
        bpy.data.objects[armature_name].pose.bones[control_bone_name].custom_shape = bpy.data.objects[name]
        bpy.data.objects[armature_name].pose.bones[control_bone_name].custom_shape_scale = 1.0

    def queue_create_location_constraint(self) -> None:
        """
        Queues the creation of the same rotation constraint
        """
        current_bone_name = self.current_edit_bone.name  # this turns the reference into a constant
        current_bone_control_name = self.control_bone.name  # this turns the reference into a constant
        armature_name = self.armature_object_name

        self.stored_control_creation_fixture.append(
            lambda context: self.create_location_constraint(context, current_bone_name,
                                                            current_bone_control_name, armature_name)
            )

    @staticmethod
    def create_location_constraint(context, current_bone_name,
                                   current_bone_control_name, armature_name) -> None:
        """
        Creates a constraint the makes the control bone follow the original bone
        """
        print(f"Attaching chain rotation control to {current_bone_name}...")
        armature = bpy.data.objects[armature_name]
        current_bone = bpy.data.objects[armature_name].pose.bones[current_bone_name]
        constraint = current_bone.constraints.new("COPY_LOCATION")
        constraint.target = armature
        constraint.subtarget = current_bone_control_name


class HeadRigger(NeckRootRigger):
    """
    This uses some of the methods of the spine to create a hidden control that uses a bounding box, the original bone is
    centered to the mesh regardless of children
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)

    def rig(self, context) -> None:
        """
        Creates a conventional rig, tail always centered, with an additional control to tell the
        """

        print(f"Generating root spine rig for {self.linked_object.properties.name}.")

        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]

        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.control_bone = newly_created[0]

        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        typical = self.get_typical_size()
        self.control_bone.head.x = self.current_edit_bone.head.x
        self.control_bone.head.y = self.current_edit_bone.head.y
        self.control_bone.head.z = self.current_edit_bone.head.z
        # positioned with
        self.control_bone.tail.x = self.control_bone.head.x
        self.control_bone.tail.y = self.control_bone.head.y + 1.0 # use absolute units?
        self.control_bone.tail.z = self.control_bone.head.z
        # parented to the absolute root
        self.control_bone.name = f"{self.current_edit_bone.name}_{BoxmanRigControl.DEFAULT_CONTROL_SUFFIX}"
        self.control_bone.parent = self.parent_rigger.current_edit_bone
        self.control_bone.use_connect = False

        mean = self.get_mesh_mean_point()

        self.current_edit_bone.tail.x = mean[0]
        self.current_edit_bone.tail.y = mean[1]
        self.current_edit_bone.tail.z = mean[2]

        for linked_child in self.linked_object.children:
            child_object: BoxmanDTO = linked_child

            factory: RiggerFactoryBase = self.rigger_factory
            child_rigger = factory.create_rigger(child_object, self)
            child_rigger.rig(context)
            child_bone = child_rigger.current_edit_bone
            if child_bone is not None:  # there might be boneless riggers
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = False

        self.queue() # same bone layers
        print(f"Generated root spine rig for {self.linked_object.properties.name}!")

# endregion


# region Chain

class ChainRiggerBase(DefaultRigger):
    """
    Base rigger for tentacles
    """
    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        self.chain_length = 0
        self.mandatory = []
        self.non_mandatory = []

    def rig(self, context) -> None:
        """
        Direct inheritance
        """
        super().rig(context)


class ChainSegmentRigger(IkControlRigger, ChainRiggerBase):
    """
    This rigger creates a segment of the chain rigger or stops to create the ik control
    """
    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        self.affect_parent = False
        self.place_on_head = False

    def verify_chain(self):
        """
        Checks the mandatory children
        """
        # if the chain continues this is bigger than 1
        self.mandatory = [x for x in self.linked_object.children
                          if x.properties.joint_type == BoxmanJointTypes.CHAIN_SEGMENT.value]

        self.non_mandatory = [x for x in self.linked_object.children
                              if x.properties.joint_type != BoxmanJointTypes.CHAIN_SEGMENT.value]

        if len(self.mandatory) > 1: # it does not need to be equal to one, only none more tha one
            raise RiggerException(self, f"This rigger only supports ONE "
                                        f"child of type {BoxmanJointTypes.CHAIN_SEGMENT.value}.")

    def rig(self, context) -> None:
        """
        This class riggs similar to the default, but the chain is determined by its only possible children.
        """
        print(f"Generating chain segment rig for {self.linked_object.properties.name}...")
        self.verify_chain()

        # We create the bone as in the default scenario
        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]
        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        # there are many options
        factory: RiggerFactoryBase = self.rigger_factory
        # if there IS a mandatory control
        if len(self.mandatory) == 1:
            # If the child is only one, the target of the tail is the position of the next member of the chain
            child_object: BoxmanDTO = self.mandatory[0]
            # for the ONLY mandatory, it'll output a tentacle rigger always
            child_rigger = factory.create_rigger(child_object, self)
            child_rigger.chain_length = self.chain_length + 1 # adds to the chain length
            child_rigger.rig(context)
            # After all happened
            child_bone = child_rigger.current_edit_bone
            child_bone.parent = self.current_edit_bone
            child_bone.use_connect = True  # it connects to the children

            self.current_edit_bone.tail.x = child_object.location[0]
            self.current_edit_bone.tail.y = child_object.location[1]
            self.current_edit_bone.tail.z = child_object.location[2]
        else:
            # If the chain ends here for the tentacles, I need to create a control at the center, of the mesh
            # and create the IK constraint
            mean = self.get_mesh_mean_point()
            self.current_edit_bone.tail.x = mean[0]
            self.current_edit_bone.tail.y = mean[1]
            self.current_edit_bone.tail.z = mean[2]
            self.create_control_bone(False)
            self.queue_create_ik_constraint(chain_length=self.chain_length)

        # then we handle the non mandatory children
        for child in self.non_mandatory:
            child_rigger: RiggerBase = factory.create_rigger(child, self)
            child_rigger.rig(context)
            # After all happened
            if child_rigger.current_edit_bone is not None:
                child_bone = child_rigger.current_edit_bone
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = False

        self.queue_parent_object_to_rig()  # this is the same
        self.queue_add_bone_to_group(BoxmanExtremityTypes.CHAIN.value, self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.MINORS_LAYER_INDEX,
                                       RiggerBase.CHAIN_LAYER_INDEX],
                                      self.current_edit_bone.name)
        if self.control_bone is not None:
            self.queue_add_bone_to_group(BoxmanExtremityTypes.CHAIN.value, self.control_bone.name)
            self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                           RiggerBase.MAYORS_LAYER_INDEX,
                                           RiggerBase.CONTROL_LAYER_INDEX,
                                           RiggerBase.CHAIN_LAYER_INDEX],
                                          self.control_bone.name)

        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()
        print(f"Generated chain segment rig for {self.linked_object.properties.name}!")


class ChainRootRigger(ChainRiggerBase):
    """
    This control starts a chain of riggers that end with an IK control at every root.
    It needs at least ONE
    """

    def __init__(self, linked_object: BoxmanDTO, parent_rigger=None):
        super().__init__(linked_object, parent_rigger)
        self.chain_length = 2 # to start the chain

    def verify_chain(self):
        """
        Checks the mandatory children
        """
        if len(self.linked_object.children) == 0:
            raise RiggerException(self, f"This rigger requires a child to operate.")

        self.mandatory = [x for x in self.linked_object.children
                          if x.properties.joint_type == BoxmanJointTypes.CHAIN_SEGMENT.value]

        self.non_mandatory = [x for x in self.linked_object.children
                              if x.properties.joint_type != BoxmanJointTypes.CHAIN_SEGMENT.value]

        if len(self.mandatory) != 1:
            raise RiggerException(self, f"This rigger requires ONE a "
                                        f"child of type {BoxmanJointTypes.CHAIN_SEGMENT.value}.")

    def rig(self, context) -> None:
        """
        This class riggs similar to the default, but the chain is determined by its only possible children.
        """
        print(f"Generating root chain rig for {self.linked_object.properties.name}...")
        self.verify_chain()

        # We create the bone as in the default scenario
        bpy.ops.armature.bone_primitive_add()
        bpy.ops.armature.select_linked()
        newly_created = bpy.context.selected_bones
        self.current_edit_bone = newly_created[0]
        self.current_edit_bone.head.x = self.linked_object.location[0]
        self.current_edit_bone.head.y = self.linked_object.location[1]
        self.current_edit_bone.head.z = self.linked_object.location[2]
        self.current_edit_bone.name = self.linked_object.get_object_name()

        # If the child is only one, the target of the tail is the position of the next member of the chain
        child_object: BoxmanDTO = self.mandatory[0]
        factory: RiggerFactoryBase = self.rigger_factory
        # for the ONLY mandatory, it'll output a tentacle rigger always
        child_rigger = factory.create_rigger(child_object, self)
        child_rigger.chain_length = self.chain_length
        child_rigger.rig(context)
        # After all happened
        child_bone = child_rigger.current_edit_bone
        child_bone.parent = self.current_edit_bone
        child_bone.use_connect = True  # it connects to the children

        self.current_edit_bone.tail.x = child_object.location[0]
        self.current_edit_bone.tail.y = child_object.location[1]
        self.current_edit_bone.tail.z = child_object.location[2]

        # then we handle the non mandatory children
        for child in self.non_mandatory:
            child_rigger: RiggerBase = factory.create_rigger(child, self)
            child_rigger.rig(context)
            # After all happened
            if child_rigger.current_edit_bone is not None:
                child_bone = child_rigger.current_edit_bone
                child_bone.parent = self.current_edit_bone
                child_bone.use_connect = False

        self.queue_parent_object_to_rig()  # this is the same
        self.queue_add_bone_to_group(BoxmanExtremityTypes.CHAIN.value, self.current_edit_bone.name)
        self.queue_add_bone_to_layers([RiggerBase.GLOBAL_LAYER_INDEX,
                                       RiggerBase.MAYORS_LAYER_INDEX,
                                       RiggerBase.CHAIN_LAYER_INDEX],
                                      self.current_edit_bone.name)
        self.queue_link_mesh_to_collection(self.get_mesh_object_collection_name())
        self.queue_unlink_mesh_from_collection()
        print(f"Generated root chain rig for {self.linked_object.properties.name}!")

# endregion

# endregion


class RiggerFactoryDictionary(TypedDict):
    """
    Used to create the Riggers in the factory
    """
    key: str
    func: Callable[[BoxmanDTO, RiggerBase], RiggerBase]


class RiggerForbiddenTypesDictionary(TypedDict):
    """
    Used to tell the if I can create the rigger from the current source
    """
    key: str
    values: List[str]


class RigTypeFactory(RiggerFactoryBase):
    """
    Creates the rigger types from the joint types of the Boxman linked objects, it contains the libraries of what
    joint type creates what rigger
    """

    def __init__(self):
        super().__init__()
        # Based on the type of the joints in the boxman, it creates instances of the riggers.
        # If the type is not found in the list, the method explodes.
        self.type_dictionary: RiggerFactoryDictionary = {
            # region defaults
            BoxmanJointTypes.OBJECT_ROOT.value: lambda x, y: RootRigger(x, y),
            BoxmanJointTypes.DEFAULT.value: lambda x, y: DefaultRigger(x, y),
            BoxmanJointTypes.ACCESSORY.value: lambda x, y: AccessoryRigger(x, y),
            # endregion
            # region Arms
            BoxmanJointTypes.SHOULDER_ROOT.value: lambda x, y: ShoulderRigger(x, y),
            BoxmanJointTypes.ARM_HUMERUS.value: lambda x, y: HumerusRigger(x, y),
            BoxmanJointTypes.ARM_RADIUS.value: lambda x, y: RadiusRigger(x, y),
            BoxmanJointTypes.ARM_ELBOW.value: lambda x, y: ElbowRigger(x, y),
            # region Arms
            # region Hands
            BoxmanJointTypes.HAND_ROOT.value: lambda x, y: HandRootRigger(x, y),
            BoxmanJointTypes.FINGER_ROOT.value: lambda x, y: FingerRootRigger(x, y),
            BoxmanJointTypes.FINGER_SECTION.value: lambda x, y: FingerSectionRigger(x, y),
            # endregion
            # region Legs
            BoxmanJointTypes.LEG_THIGH.value: lambda x, y: ThighRigger(x, y),
            BoxmanJointTypes.LEG_KNEE.value: lambda x, y: KneeRigger(x, y),
            BoxmanJointTypes.LEG_SHIN.value: lambda x, y: ShinRigger(x, y),
            # endregion
            # region Spine
            BoxmanJointTypes.SPINE_ROOT.value: lambda x, y: SpineRootRigger(x, y),
            BoxmanJointTypes.SPINE_SECTION.value: lambda x, y: SpineSectionRigger(x, y),
            # endregion
            # region Head
            BoxmanJointTypes.NECK_ROOT.value: lambda x, y: NeckRootRigger(x, y),
            BoxmanJointTypes.NECK_SECTION.value: lambda x, y: NeckSectionRigger(x, y),
            BoxmanJointTypes.HEAD.value: lambda x, y: HeadRigger(x, y),
            # endregion
            # region Feet
            BoxmanJointTypes.FOOT_ROOT.value: lambda x, y: FeetRigger(x, y),
            BoxmanJointTypes.TOE_ROOT.value: lambda x, y: ToeRootRigger(x, y),
            BoxmanJointTypes.TOE_SECTION.value: lambda x, y: ToeSectionRigger(x, y),
            # endregion
            # region Chain
            BoxmanJointTypes.CHAIN_ROOT.value: lambda x, y: ChainRootRigger(x, y),
            BoxmanJointTypes.CHAIN_SEGMENT.value: lambda x, y: ChainSegmentRigger(x, y),
            # endregion
        }

        # internal use
        root_key: List[str] = [BoxmanJointTypes.OBJECT_ROOT.value]
        ik_direct_keys: List[str] = [
            BoxmanJointTypes.FOOT_ROOT.value,
            BoxmanJointTypes.HAND_ROOT.value,
            BoxmanJointTypes.CHAIN_SEGMENT.value
        ]

        # this is the list of riggers that CAN NOT be created from a specific source
        self.forbidden_matrix: RiggerForbiddenTypesDictionary = {
            # region defaults
            # root cant create other roots nor direct iks
            BoxmanJointTypes.OBJECT_ROOT.value: root_key + ik_direct_keys,
            # defaults are the same
            BoxmanJointTypes.DEFAULT.value: root_key + ik_direct_keys,
            # this doesnt matter since it doesnt rig
            BoxmanJointTypes.ACCESSORY.value: [],
            # endregion
            # region Arms
            # shoulders are just a default with a proxy
            BoxmanJointTypes.SHOULDER_ROOT.value: root_key + ik_direct_keys,
            # humerus are the same but shin makes no sense here
            BoxmanJointTypes.ARM_HUMERUS.value: root_key + ik_direct_keys + [BoxmanJointTypes.LEG_SHIN.value],
            # radius can take hands, but not other iks
            BoxmanJointTypes.ARM_RADIUS.value: root_key + [BoxmanJointTypes.FOOT_ROOT.value,
                                                           BoxmanJointTypes.CHAIN_SEGMENT.value],
            # same as the default, but it generates a pole
            BoxmanJointTypes.ARM_ELBOW.value: root_key + ik_direct_keys,
            # region Arms
            # region Hands
            # direct keys
            BoxmanJointTypes.HAND_ROOT.value: root_key + ik_direct_keys,
            # direct keys
            BoxmanJointTypes.FINGER_ROOT.value: root_key + ik_direct_keys,
            # direct keys
            BoxmanJointTypes.FINGER_SECTION.value: root_key + ik_direct_keys,
            # endregion
            # region Legs
            # Thighs are like the resp but radius make no sense
            BoxmanJointTypes.LEG_THIGH.value: root_key + ik_direct_keys + [BoxmanJointTypes.ARM_RADIUS.value],
            # Knees are the same
            BoxmanJointTypes.LEG_KNEE.value: root_key + ik_direct_keys,
            # Shins can take feet, but not other iks
            BoxmanJointTypes.LEG_SHIN.value: root_key + [BoxmanJointTypes.HAND_ROOT.value,
                                                         BoxmanJointTypes.CHAIN_SEGMENT.value],
            # endregion
            # region Spine
            # Spines can take anything
            BoxmanJointTypes.SPINE_ROOT.value: root_key + ik_direct_keys,
            # Spines can take anything
            BoxmanJointTypes.SPINE_SECTION.value: root_key + ik_direct_keys,
            # endregion
            # region Head
            # Spines can take anything
            BoxmanJointTypes.NECK_ROOT.value: root_key + ik_direct_keys,
            # Spines can take anything
            BoxmanJointTypes.NECK_SECTION.value: root_key + ik_direct_keys,
            # Spines can take anything
            BoxmanJointTypes.HEAD.value: root_key + ik_direct_keys,
            # endregion
            # region Feet
            # direct keys
            BoxmanJointTypes.FOOT_ROOT.value: root_key + ik_direct_keys,
            # direct keys
            BoxmanJointTypes.TOE_ROOT.value: root_key + ik_direct_keys,
            # direct keys
            BoxmanJointTypes.TOE_SECTION.value: root_key + ik_direct_keys,
            # endregion
            # region Chain
            # direct keys except the other iks
            BoxmanJointTypes.CHAIN_ROOT.value: root_key + [BoxmanJointTypes.HAND_ROOT.value,
                                                           BoxmanJointTypes.FOOT_ROOT.value],
            # direct keys except the other iks
            BoxmanJointTypes.CHAIN_SEGMENT.value: root_key + [BoxmanJointTypes.HAND_ROOT.value,
                                                              BoxmanJointTypes.FOOT_ROOT.value],
        }

    def create_rigger(self,
                      selected_object: BoxmanDTO,
                      parent_rigger=None
                      ) -> RiggerBase:
        """
        Creates a rigger from the dictionary, checking first for forbidden link attempts
        """

        # If not in the list, its a default
        element: RiggerBase
        if selected_object.properties.joint_type not in self.type_dictionary.keys():
            raise NotImplementedError()

        if parent_rigger is not None:
            forbidden_types = self.forbidden_matrix.__getitem__(parent_rigger.linked_object.properties.joint_type)
            if selected_object.properties.joint_type in forbidden_types:
                raise RiggerException(parent_rigger,
                                      f"Cant create a rigger for type {selected_object.properties.joint_type} "
                                      f"from the current type...")

        element = self.type_dictionary.__getitem__(selected_object.properties.joint_type)(selected_object,
                                                                                          parent_rigger)
        element.rigger_factory = self

        return element


def auto_rig(context, selected_object: BoxmanDTO) -> None:
    """
    Calls the whole rig presses, executing the fixtures after changing modes several times.
    """
    rig_factory = RigTypeFactory()

    # first create the bones and set the fixture
    print("Autorig started...")
    print("Creating bones...")
    root_rigger = rig_factory.create_rigger(selected_object)  # dummy argument
    root_rigger.rig(context)

    # changing to object mode creates the pose bones
    print("Changing to OBJECT mode...")
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.object.name = root_rigger.armature_object_name
    bpy.context.object.show_in_front = True

    # Then I make the parenting chain of the meshes to the pose bones
    print("Bones created!")
    print("Executing fixtures...")
    print("Parenting bones...")
    for item in root_rigger.stored_parenting_fixture:
        item(context)
    print("Bones parented!")

    # Then I create the controls that will replace the meshes in pose mode
    print("Creating controls...")
    print("Switching to object mode...")
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    for item in root_rigger.stored_mesh_creation_fixture:
        item(context)
    print("Control meshes created!")

    # then i set active the current armature
    bpy.ops.object.select_all(action='DESELECT')
    print("Changing to POSE mode...")
    armature_object = bpy.data.objects[root_rigger.armature_object_name]
    armature_object.data.display_type = "STICK"
    armature_object.select_set(True)
    bpy.context.view_layer.objects.active = armature_object
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='DESELECT')
    print("Creating controls and constraints...")
    for item in root_rigger.stored_control_creation_fixture:
        item(context)

    print("Constraints created!")
    bpy.ops.object.mode_set(mode='OBJECT')
    print("Grouping objects...")
    for item in root_rigger.stored_collection_assignments:
        item(context)

    print(f"Linking Armature to main collection...")
    armature_object = bpy.data.objects[root_rigger.armature_object_name]
    collection = bpy.data.collections[root_rigger.get_main_collection_name()]
    collection.objects.link(armature_object)
    scene_collection = bpy.context.scene.collection
    scene_collection.objects.unlink(armature_object)

    print("Objects grouped!")








