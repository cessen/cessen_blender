#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#======================= END GPL LICENSE BLOCK ========================

bl_info = {
    "name": "Cessen's Misc Animation Tools",
    "version": (0, 1, 0),
    "author": "Nathan Vegdahl",
    "blender": (2, 93, 0),
    "description": "Misc tools to make some animation tasks a little easier",
    "location": "",
    # "doc_url": "",
    "category": "Animation",
}


import bpy

class NormalizeQuaternions(bpy.types.Operator):
    """Normalizes the quaternion rotation coordinates of selected objects and bones"""
    bl_idname = "object.normalize_quaternions"
    bl_label = "Normalize Quaternions"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'ARMATURE' and obj.mode == 'POSE':
                for bone in obj.pose.bones:
                    if bone.bone.select and bone.rotation_mode == 'QUATERNION':
                        bone.rotation_quaternion.normalize()
            else:
                if obj.rotation_mode == 'QUATERNION':
                    obj.rotation_quaternion.normalize()
                
        return {'FINISHED'}

#========================================================


def register():
    bpy.utils.register_class(NormalizeQuaternions)


def unregister():
    bpy.utils.unregister_class(NormalizeQuaternions)


if __name__ == "__main__":
    register()
