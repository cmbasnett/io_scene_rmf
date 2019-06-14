bl_info = {
    'name': 'Rich Map Format',
    'description': 'Import Rich Map Format (rmf) files used in Valve Hammer Editor',
    'author': 'Colin Basnett',
    'version': (1, 0, 0),
    'blender': (2, 79, 0),
    'location': 'File > Import-Export',
    'warning': 'This add-on is under development.',
    'wiki_url': 'https://github.com/cmbasnett/io_scene_rmf/wiki',
    'tracker_url': 'https://github.com/cmbasnett/io_scene_rmf/issues',
    'support': 'COMMUNITY',
    'category': 'Import-Export'
}

if 'bpy' in locals():
    import importlib
    if 'rmf'       in locals():  importlib.reload(rmf)
    if 'reader'     in locals(): importlib.reload(reader)
    if 'importer'   in locals(): importlib.reload(importer)

import bpy
from . import rmf
from . import reader
from . import importer

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(importer.ImportOperator.menu_func_import)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(importer.ImportOperator.menu_func_import)

