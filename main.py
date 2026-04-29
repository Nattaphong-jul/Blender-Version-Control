bl_info = {
    "name": "Version Control",
    "blender": (3, 0, 0),
    "category": "System",
}

import bpy

class BVC_OT_SaveVersion(bpy.types.Operator):
    bl_idname = "bvc.save_version"
    bl_label  = "Save Version"

    def execute(self, context):
        print("Save Version clicked!")
        return {"FINISHED"}

class BVC_PT_Panel(bpy.types.Panel):
    bl_label       = "Version Control"
    bl_idname      = "BVC_PT_panel"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "Versions"

    def draw(self, context):
        layout = self.layout
        layout.operator("bvc.save_version", text="Save Version")

def register():
    bpy.utils.register_class(BVC_OT_SaveVersion)
    bpy.utils.register_class(BVC_PT_Panel)

def unregister():
    bpy.utils.unregister_class(BVC_OT_SaveVersion)
    bpy.utils.unregister_class(BVC_PT_Panel)
    
if __name__ == "__main__":
    register()