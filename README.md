## Version Control for Blender

A Git-inspired version control plugin for Blender, designed for 3D artists —
no Git knowledge required.

> Originally developed as a Final Project for ITCS373 Creative Programming,  
> Faculty of ICT, Mahidol University.

### Features
- Save a version of your `.blend` file with a description and timestamp
- Browse full version history with timestamps, descriptions, and file sizes
- Roll back to any previous version (with an automatic safety snapshot)
- Delete old versions to free up disk space
- Version history stored in a `.bvc/versions/` folder next to your `.blend` file

<table>
  <tr>
    <td><img width="400" alt="Usage 1" src="https://github.com/user-attachments/assets/0ddec608-1def-4fff-9f53-acb80cd43b1c" /></td>
    <td><img width="400" alt="Usage 2" src="https://github.com/user-attachments/assets/ebd0d8fe-ecf4-4fbc-a31a-cd87f70d2481" /></td>
  </tr>
</table>

### Requirements
- Blender 3.0 or later

### Installation
1. Download `main.py`
2. In Blender: **Edit → Preferences → Add-ons → Install**
3. Select the downloaded file and enable **"Version Control"**
4. Open the **Versions** tab in the 3D Viewport sidebar (press **N**)

### What's Next
- (v0.2.0) Per-file version history — multiple `.blend` files in the same folder
  each keep their own separate history
- (v0.3.0) Ability to save versions with packed textures