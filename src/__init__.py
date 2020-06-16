bl_info = {
    'name': 'Rich Map Format',
    'description': 'Import Rich Map Format (rmf) files used in Valve Hammer Editor',
    'author': 'Colin Basnett',
    'version': (1, 0, 0),
    'blender': (2, 80, 0),
    'location': 'File > Import-Export',
    'warning': 'This add-on is under development.',
    'wiki_url': 'https://github.com/cmbasnett/io_scene_rmf/wiki',
    'tracker_url': 'https://github.com/cmbasnett/io_scene_rmf/issues',
    'support': 'COMMUNITY',
    'category': 'Import-Export'
}

if 'bpy' in locals():
    import importlib
    if 'utils'      in locals(): importlib.reload(utils)
    if 'rmf'       in locals():  importlib.reload(rmf)
    if 'reader'     in locals(): importlib.reload(reader)
    if 'importer'   in locals(): importlib.reload(importer)

import bpy
from . import utils
from . import rmf
from . import reader
from . import importer

classes = (
    importer.RMF_OT_ImportOperator,
)


def menu_func_import(self, context):
    self.layout.operator(importer.RMF_OT_ImportOperator.bl_idname, text='Rich Map Format (.rmf)')


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    for cls in classes:
        bpy.utils.unregister_class(cls)
