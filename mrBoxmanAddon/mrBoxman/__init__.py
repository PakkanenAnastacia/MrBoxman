bl_info = {
    "name": "MrBoxman",
    "description": "Collection of tools for creating, editing importing and exporting "
                   "parented base meshes as libraries.",
    "author": "Alejandro Tevez",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "VIEW_3D > UI > MrBoxman",
    "warning": "In experimental state use at your own risk :D",
    "support": "COMMUNITY",
    "category": "ADDON_X",
}

from .boxman import boxmanimportexport as bxm_io, boxmanlibrary as bxm_lb, boxmanconverter as bxm_cv, \
    boxmanrig as bxm_rg

def register():
    bxm_cv.register()
    bxm_lb.register()
    bxm_io.register()
    bxm_rg.register()

def unregister():
    bxm_cv.unregister()
    bxm_lb.unregister()
    bxm_io.unregister()
    bxm_rg.unregister()

