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
    "name": "Cessen's Misc Blender Tools",
    "version": (0, 1, 0),
    "author": "Nathan Vegdahl",
    "blender": (3, 0, 0),
    "description": "Misc tools for Cessen's personal workflows.",
    "location": "",
    # "doc_url": "",
    "category": "Cessen",
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


class ToggleAddSubWeightPaintBrush(bpy.types.Operator):
    """Quick op for toggling between my most common weight painting brushes"""
    bl_idname = "paint.weight_toggle_add_sub"
    bl_label = "Toggle Add/Sub Brush"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and \
               context.mode == 'PAINT_WEIGHT'

    def execute(self, context):
        if "Add" not in bpy.data.brushes:
            b = bpy.data.brushes.new("Add", mode='WEIGHT_PAINT')
            b.blend = 'ADD'
        if "Subtract" not in bpy.data.brushes:
            b = bpy.data.brushes.new("Subtract", mode='WEIGHT_PAINT')
            b.blend = 'SUB'

        if context.tool_settings.weight_paint.brush == bpy.data.brushes["Add"]:
            context.tool_settings.weight_paint.brush = bpy.data.brushes["Subtract"]
        else:
            context.tool_settings.weight_paint.brush = bpy.data.brushes["Add"]

        return {'FINISHED'}


class NormalizeUnlockedDeformWeights(bpy.types.Operator):
    """Normalizes unlocked deform weights such that when combined with the locked weights it all adds up to 1.0"""
    bl_idname = "paint.normalize_unlocked_deform_weights"
    bl_label = "Normalize Unlocked Deform Weights"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and \
               context.mode == 'PAINT_WEIGHT'

    def execute(self, context):
        obj = context.active_object

        # Get the armature (if any) that deforms this object.
        armature = None
        for mod in obj.modifiers:
            if mod.type == 'ARMATURE' and mod.object != None:
                armature = mod.object
                break
        if armature is None:
            return {'CANCELLED'}

        # Get a list of deform bones from the deforming armature.
        deform_bones = set()
        for bone in armature.data.bones:
            if bone.use_deform:
                deform_bones.add(bone.name)

        # Build a list of vertex group indices for locked and unlocked deform groups.
        locked = []
        unlocked = []
        for group in obj.vertex_groups:
            if group.name in deform_bones:
                if group.lock_weight:
                    locked += [group.index]
                else:
                    unlocked += [group.index]

        # Loop through the vertices and normalize the unlocked deform groups.
        for vert in obj.data.vertices:
            # Get the total locked and unlocked weights.
            locked_sum = 0.0
            unlocked_sum = 0.0
            for group in vert.groups:
                if group.group in locked:
                    locked_sum += group.weight
                elif group.group in unlocked:
                    unlocked_sum += group.weight
            if unlocked_sum <= 0.0:
                continue

            # Normalize.
            if locked_sum >= 1.0:
                for group in vert.groups:
                    if group.group in unlocked:
                        group.weight = 0.0
            else:
                room = 1.0 - locked_sum
                norm_factor = room / unlocked_sum
                for group in vert.groups:
                    if group.group in unlocked:
                        group.weight *= norm_factor

        return {'FINISHED'}


class NormalizeUnlockedUnselectedDeformWeights(bpy.types.Operator):
    """Normalizes unlocked deform weights in a way that prioritizes the selected weight groups remaining unchanged."""
    bl_idname = "paint.normalize_unlocked_unselected_deform_weights"
    bl_label = "Normalize Unlocked Unselected Deform Weights"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and \
               context.mode == 'PAINT_WEIGHT'

    def execute(self, context):
        obj = context.active_object

        # Get the armature (if any) that deforms this object.
        armature = None
        for mod in obj.modifiers:
            if mod.type == 'ARMATURE' and mod.object != None:
                armature = mod.object
                break
        if armature is None:
            return {'CANCELLED'}

        # Get a list of deform bones from the deforming armature.
        deform_bones = set()
        deform_bones_selected = set()
        for bone in armature.data.bones:
            if bone.use_deform:
                deform_bones.add(bone.name)
                if bone.select:
                    deform_bones_selected.add(bone.name)

        # Build a list of vertex group indices for locked and unlocked deform groups,
        # the latter being split into selected and unselected.
        locked = []
        unlocked_selected = []
        unlocked_unselected = []
        for group in obj.vertex_groups:
            if group.name in deform_bones:
                if group.lock_weight:
                    locked += [group.index]
                elif group.name in deform_bones_selected:
                    unlocked_selected += [group.index]
                else:
                    unlocked_unselected += [group.index]

        # Loop through the vertices and normalize the unlocked deform groups.
        for vert in obj.data.vertices:
            # Get the total locked and unlocked weights.
            locked_sum = 0.0
            unlocked_selected_sum = 0.0
            unlocked_unselected_sum = 0.0
            for group in vert.groups:
                if group.group in locked:
                    locked_sum += group.weight
                elif group.group in unlocked_selected:
                    unlocked_selected_sum += group.weight
                elif group.group in unlocked_unselected:
                    unlocked_unselected_sum += group.weight
            if unlocked_selected_sum <= 0.0 and unlocked_unselected_sum <= 0.0:
                continue

            # Normalize.
            if locked_sum >= 1.0:
                for group in vert.groups:
                    if group.group not in locked:
                        group.weight = 0.0
            else:
                room = 1.0 - locked_sum
                unselected_room = room - unlocked_selected_sum
                norm_selected = 1.0
                norm_unselected = 1.0
                if unselected_room <= 0.0 or unlocked_unselected_sum <= 0.0:
                    norm_selected = room / unlocked_selected_sum
                    norm_unselected = 0.0
                else:
                    norm_selected = 1.0
                    norm_unselected = unselected_room / unlocked_unselected_sum

                for group in vert.groups:
                    if group.group in unlocked_selected:
                        group.weight *= norm_selected
                    if group.group in unlocked_unselected:
                        group.weight *= norm_unselected

        return {'FINISHED'}


#========================================================


def register():
    bpy.utils.register_class(NormalizeQuaternions)
    bpy.utils.register_class(ToggleAddSubWeightPaintBrush)
    bpy.utils.register_class(NormalizeUnlockedDeformWeights)
    bpy.utils.register_class(NormalizeUnlockedUnselectedDeformWeights)



def unregister():
    bpy.utils.unregister_class(NormalizeQuaternions)
    bpy.utils.unregister_class(ToggleAddSubWeightPaintBrush)
    bpy.utils.unregister_class(NormalizeUnlockedDeformWeights)
    bpy.utils.unregister_class(NormalizeUnlockedUnselectedDeformWeights)


if __name__ == "__main__":
    register()
