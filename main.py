bl_info = {
    "name": "Version Control",
    "blender": (3, 0, 0),
    "category": "System",
}

import bpy
import os
import shutil
import datetime
import json

def copy_file(source_path, destination_folder, description=""):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") # Format: YYYYMMDD_HHMMSS
    file_name = os.path.basename(source_path)
    manifest_path = os.path.join(destination_folder, "manifest.json")

    os.makedirs(os.path.join(destination_folder, timestamp), exist_ok=True)

    entries = load_manifest(manifest_path)
    entries.append({
                "version_id": timestamp,
                "timestamp": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), # Format: DD-MM-YYYY HH:MM:SS
                "description": description,
                "file_name": file_name
            })
    write_manifest(manifest_path, entries)

    shutil.copy(source_path, os.path.join(destination_folder, timestamp))

def load_manifest(manifest_path) -> list:
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as manifest_file:
            return json.load(manifest_file)
    return []

def write_manifest(manifest_path, entries):
    with open(manifest_path, "w") as manifest_file:
        json.dump(entries, manifest_file, indent=2)

def reload_version_list(context):
    blend_path = bpy.data.filepath
    if not blend_path:
        return

    wm = context.window_manager
    wm.bvc_versions.clear()

    destination_folder = os.path.join(os.path.dirname(blend_path), ".bvc", "versions")
    manifest_path = os.path.join(destination_folder, "manifest.json")
    entries = load_manifest(manifest_path)
    for entry in reversed(entries):
        item = wm.bvc_versions.add()
        item.version_id  = entry["version_id"]
        item.timestamp   = entry["timestamp"]
        item.description = entry["description"]

@bpy.app.handlers.persistent
def load_version_list(dummy):
    reload_version_list(bpy.context)

def roll_back(target_file, destination_folder, selected_id):
    manifest_path = os.path.join(destination_folder, "manifest.json")
    entries = load_manifest(manifest_path)

    for entry in entries:
        if entry["version_id"] == selected_id:
            version_folder = os.path.join(destination_folder, entry["version_id"])
            source_file = os.path.join(version_folder, entry["file_name"])
            
            if os.path.exists(source_file):
                # Copy latest version before rolling back
                copy_file(target_file, destination_folder, description=f"Roll Back")

                # Roll Back
                shutil.copy(source_file, target_file)
                print(f"Successfully rolled back to version: {selected_id}")
            else:
                print(f"Error: Version file not found at {source_file}")
            break


class BVC_OT_SaveVersion(bpy.types.Operator):
    bl_idname = "bvc.save_version"
    bl_label  = "Save Version"

    description: bpy.props.StringProperty(
        name="Description",
        default=""
    )

    def invoke(self, context, event):
        if not bpy.data.filepath:
            self.report({"ERROR"}, "Please save your file first!")
            return {"CANCELLED"}
        return context.window_manager.invoke_props_dialog(self, width=200)

    def draw(self, context):
        self.layout.prop(self, "description", text="Note")

    def execute(self, context):
        blend_path = bpy.data.filepath
        if not blend_path:
            self.report({"ERROR"}, "Please save your file first!")
            return {"CANCELLED"}
    
        destination_folder = os.path.join(os.path.dirname(blend_path), ".bvc", "versions")

        # Save current blend file before copying
        bpy.ops.wm.save_mainfile()

        # Copy file to version folder
        copy_file(blend_path, destination_folder, description=self.description)

        reload_version_list(bpy.context)

        self.report({"INFO"}, "Version saved!")
        return {"FINISHED"}

# Roll Back
class BVC_OT_RollBack(bpy.types.Operator):
    bl_idname = "bvc.roll_back"
    bl_label  = "Roll Back"

    def execute(self, context):
        blend_path = bpy.data.filepath
        wm = context.window_manager

        # Get selected version from the list
        index = wm.bvc_active_index
        selected = wm.bvc_versions[index]

        destination_folder = os.path.join(os.path.dirname(blend_path), ".bvc", "versions")
        roll_back(blend_path, destination_folder, selected.version_id)

        reload_version_list(bpy.context)

        self.report({"INFO"}, f"Rolled back to {selected.timestamp}")
        bpy.ops.wm.revert_mainfile()
        return {"FINISHED"}

# Main Windows
class BVC_PT_Panel(bpy.types.Panel):
    bl_label       = "Version Control"
    bl_idname      = "BVC_PT_panel"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "Versions"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        layout.operator("bvc.save_version", text="Save Version")

        layout.template_list(
            "BVC_UL_VersionList", "",
            wm, "bvc_versions",
            wm, "bvc_active_index",
            rows=3,
        )

        layout.operator("bvc.roll_back", text="Roll Back to Selected")
        layout.operator("bvc.refresh", text="Refresh")
        layout.operator("bvc.delete_version", text="Delete Selected")

# Version history list [Column]
class BVC_VersionItem(bpy.types.PropertyGroup):
    version_id: bpy.props.StringProperty()
    timestamp: bpy.props.StringProperty()
    description: bpy.props.StringProperty()

class BVC_UL_VersionList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if item.description:
            layout.label(text=f"{item.timestamp}  —  {item.description}")
        else:
            layout.label(text=item.timestamp)

# Refresh Button
class BVC_OT_Refresh(bpy.types.Operator):
    bl_idname = "bvc.refresh"
    bl_label  = "Refresh"

    def execute(self, context):
        reload_version_list(context)
        self.report({"INFO"}, "Refreshed!")
        return {"FINISHED"}

# Delete Version
class BVC_OT_DeleteVersion(bpy.types.Operator):
    bl_idname = "bvc.delete_version"
    bl_label  = "Delete Version"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        blend_path = bpy.data.filepath
        wm = context.window_manager

        index = wm.bvc_active_index
        selected = wm.bvc_versions[index]

        destination_folder = os.path.join(os.path.dirname(blend_path), ".bvc", "versions")
        manifest_path = os.path.join(destination_folder, "manifest.json")
        entries = load_manifest(manifest_path)

        entry = next((e for e in entries if e["version_id"] == selected.version_id), None)
        if entry:
            version_folder = os.path.join(destination_folder, selected.version_id)
            if os.path.exists(version_folder):
                shutil.rmtree(version_folder)
            entries.remove(entry)
            write_manifest(manifest_path, entries)

        reload_version_list(context)
        self.report({"INFO"}, "Version deleted.")
        return {"FINISHED"}


def register():
    bpy.utils.register_class(BVC_OT_SaveVersion)
    bpy.utils.register_class(BVC_PT_Panel)
    bpy.utils.register_class(BVC_VersionItem)
    bpy.utils.register_class(BVC_UL_VersionList)
    bpy.utils.register_class(BVC_OT_RollBack)
    bpy.utils.register_class(BVC_OT_Refresh)
    bpy.utils.register_class(BVC_OT_DeleteVersion)

    bpy.types.WindowManager.bvc_versions = bpy.props.CollectionProperty(type=BVC_VersionItem)
    bpy.types.WindowManager.bvc_active_index = bpy.props.IntProperty(default=0)
    bpy.app.handlers.load_post.append(load_version_list)
    

def unregister():
    bpy.utils.unregister_class(BVC_OT_SaveVersion)
    bpy.utils.unregister_class(BVC_PT_Panel)
    bpy.utils.unregister_class(BVC_VersionItem)
    bpy.utils.unregister_class(BVC_UL_VersionList)
    bpy.utils.unregister_class(BVC_OT_RollBack)
    bpy.utils.unregister_class(BVC_OT_Refresh)
    bpy.utils.unregister_class(BVC_OT_DeleteVersion)
    bpy.app.handlers.load_post.remove(load_version_list)

    del bpy.types.WindowManager.bvc_versions
    del bpy.types.WindowManager.bvc_active_index
    
if __name__ == "__main__":
    register()