import bpy
import bpy_extras
import bmesh
import os
from mathutils import Vector, Matrix, Quaternion
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty, CollectionProperty
from .writer import RmfWriter
from .builder import RmfBuilder
from .rmf import *


class RMF_OT_ExportOperator(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = 'io_scene_rmf.rmf_export'  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = 'Export Rich Map Format'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    # ImportHelper mixin class uses this
    filename_ext = '.rmf'

    filter_glob : StringProperty(
        default="*.rmf",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be hilighted.
    )

    def execute(self, context):
        rmf = RmfBuilder().from_context(context)
        RmfWriter().to_file(rmf, self.filepath)
        return {'FINISHED'}
