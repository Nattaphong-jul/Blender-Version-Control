# Nattaphong Jullayakiat
# Faculty of ICT Mahidol University
# Student ID: 6688155

bl_info = {
    "name": "Version Control",
    "author": "Nattaphong Jullayakiat",
    "version": (0, 1, 3),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Versions",
    "description": "Save and restore versions of your Blender project",
    "category": "System",
}

import bpy
import os
import shutil
import datetime
import json


def format_size(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def copy_file(source_path, destination_folder, description=""):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")  # Format: YYYYMMDD_HHMMSS
    file_name = os.path.basename(source_path)
    manifest_path = os.path.join(destination_folder, "manifest.json")

    os.makedirs(os.path.join(destination_folder, timestamp), exist_ok=True)

    entries = load_manifest(manifest_path)
    entries.append({
        "version_id": timestamp,
        "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "description": description,
        "file_name": file_name,
        "size_label": format_size(os.path.getsize(source_path))
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
        item.size_label  = entry.get("size_label", "")


@bpy.app.handlers.persistent
def load_version_list(dummy):
    reload_version_list(bpy.context)


def roll_back(target_file, destination_folder, selected_id, selected_description):
    manifest_path = os.path.join(destination_folder, "manifest.json")
    entries = load_manifest(manifest_path)

    for entry in entries:
        if entry["version_id"] == selected_id:
            version_folder = os.path.join(destination_folder, entry["version_id"])
            source_file = os.path.join(version_folder, entry["file_name"])

            if os.path.exists(source_file):
                # Label shows where we rolled back to
                snapshot_description = f"Roll Back \u2192 {selected_description}" if selected_description else f"Roll Back \u2192 {entry['timestamp']}"
                copy_file(target_file, destination_folder, description=snapshot_description)

                # Roll back
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

    _block_unsaved = False

    @classmethod
    def poll(cls, context):
        return bpy.data.filepath != ""

    def invoke(self, context, event):
        if bpy.data.is_dirty:
            self._block_unsaved = True
            return context.window_manager.invoke_props_dialog(self, width=280)

        self._block_unsaved = False
        return context.window_manager.invoke_props_dialog(self, width=200)

    def draw(self, context):
        if self._block_unsaved:
            col = self.layout.column(align=True)
            col.label(text="You have unsaved changes.", icon="ERROR")
            col.label(text="Please save first (Ctrl+S) before backing up.")
        else:
            self.layout.prop(self, "description", text="Note")

    def execute(self, context):
        if self._block_unsaved:
            return {"CANCELLED"}

        blend_path = bpy.data.filepath
        destination_folder = os.path.join(os.path.dirname(blend_path), ".bvc", "versions")

        bpy.ops.wm.save_mainfile()
        copy_file(blend_path, destination_folder, description=self.description)
        reload_version_list(bpy.context)

        self.report({"INFO"}, "Version saved!")
        return {"FINISHED"}


class BVC_OT_RollBack(bpy.types.Operator):
    bl_idname = "bvc.roll_back"
    bl_label  = "Roll Back"

    _block_unsaved = False

    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        if not hasattr(wm, "bvc_versions"):
            return False
        return bpy.data.filepath != "" and len(wm.bvc_versions) > 0

    def invoke(self, context, event):
        if bpy.data.is_dirty:
            self._block_unsaved = True
            return context.window_manager.invoke_props_dialog(self, width=280)

        self._block_unsaved = False
        return context.window_manager.invoke_confirm(self, event)

    def draw(self, context):
        if self._block_unsaved:
            col = self.layout.column(align=True)
            col.label(text="You have unsaved changes.", icon="ERROR")
            col.label(text="Please save first (Ctrl+S) before rolling back.")

    def execute(self, context):
        if self._block_unsaved:
            return {"CANCELLED"}

        blend_path = bpy.data.filepath
        wm = context.window_manager

        bpy.ops.wm.save_mainfile()

        index = wm.bvc_active_index
        selected = wm.bvc_versions[index]

        destination_folder = os.path.join(os.path.dirname(blend_path), ".bvc", "versions")
        roll_back(blend_path, destination_folder, selected.version_id, selected.description)

        reload_version_list(bpy.context)

        self.report({"INFO"}, f"Rolled back to {selected.timestamp}")
        bpy.ops.wm.revert_mainfile()
        return {"FINISHED"}


class BVC_OT_DeleteVersion(bpy.types.Operator):
    bl_idname = "bvc.delete_version"
    bl_label  = "Delete Version"

    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        if not hasattr(wm, "bvc_versions"):
            return False
        return len(wm.bvc_versions) > 0

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


class BVC_OT_Refresh(bpy.types.Operator):
    bl_idname = "bvc.refresh"
    bl_label  = "Refresh"

    def execute(self, context):
        reload_version_list(context)
        self.report({"INFO"}, "Refreshed!")
        return {"FINISHED"}


class BVC_VersionItem(bpy.types.PropertyGroup):
    version_id  : bpy.props.StringProperty()
    timestamp   : bpy.props.StringProperty()
    description : bpy.props.StringProperty()
    size_label  : bpy.props.StringProperty()


class BVC_UL_VersionList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if item.description:
            layout.label(text=f"{item.timestamp}  —  {item.description}")
        else:
            layout.label(text=item.timestamp)


class BVC_PT_Panel(bpy.types.Panel):
    bl_label       = "Version Control"
    bl_idname      = "BVC_PT_panel"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "Versions"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        # Safety check — properties not registered yet
        if not hasattr(wm, "bvc_versions"):
            layout.label(text="Loading...", icon="INFO")
            return

        # File name header
        blend_path = bpy.data.filepath
        if not blend_path:
            layout.label(text="Save your file first!", icon="ERROR")
            return

        blend_name = os.path.basename(blend_path)
        layout.label(text=blend_name, icon="FILE_BLEND")
        layout.separator()

        # Save Version button
        row = layout.row()
        row.scale_y = 1.5
        row.operator("bvc.save_version", text="Save a Version", icon="PLUS")

        layout.separator()

        # Version count label
        count = len(wm.bvc_versions)
        layout.label(text=f"Version History ({count})", icon="RECOVER_LAST")

        if count == 0:
            box = layout.box()
            box.label(text="No versions saved yet.", icon="INFO")
        else:
            layout.template_list(
                "BVC_UL_VersionList", "",
                wm, "bvc_versions",
                wm, "bvc_active_index",
                rows=5,
            )

            # Detail box — only shows when a version is selected
            idx = wm.bvc_active_index
            if 0 <= idx < count:
                sel = wm.bvc_versions[idx]
                box = layout.box()
                col = box.column(align=True)
                col.label(text=sel.timestamp, icon="TIME")
                if sel.description:
                    col.label(text=sel.description, icon="EDITMODE_HLT")
                col.label(text=sel.size_label, icon="DISK_DRIVE")

                col.separator()
                # Rollback + Delete inside the detail box
                row = col.row(align=True)
                row.operator("bvc.roll_back", text="Go Back to This", icon="LOOP_BACK")
                row.operator("bvc.delete_version", text="", icon="TRASH")

        layout.separator()
        layout.operator("bvc.refresh", text="Refresh List", icon="FILE_REFRESH")


classes = (
    BVC_VersionItem,
    BVC_UL_VersionList,
    BVC_OT_SaveVersion,
    BVC_OT_RollBack,
    BVC_OT_DeleteVersion,
    BVC_OT_Refresh,
    BVC_PT_Panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.bvc_versions = bpy.props.CollectionProperty(type=BVC_VersionItem)
    bpy.types.WindowManager.bvc_active_index = bpy.props.IntProperty(default=0)
    bpy.app.handlers.load_post.append(load_version_list)

def unregister():
    bpy.app.handlers.load_post.remove(load_version_list)

    del bpy.types.WindowManager.bvc_versions
    del bpy.types.WindowManager.bvc_active_index

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()