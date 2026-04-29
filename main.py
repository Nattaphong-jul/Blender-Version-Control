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

    def execute(self, context):
        blend_path = bpy.data.filepath
        if not blend_path:
            self.report({"ERROR"}, "Please save your file first!")
            return {"CANCELLED"}
    
        destination_folder = os.path.join(os.path.dirname(blend_path), ".bvc", "versions")
        copy_file(blend_path, destination_folder)

        self.report({"INFO"}, "Version saved!")
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