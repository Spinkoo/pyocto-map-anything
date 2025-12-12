# Example Gallery

This folder contains example 3D reconstructions generated from single RGB images using AI depth estimation and OctoMap.

## Reconstructions with Animations

### Castle
<div align="center">
  <table>
    <tr>
      <td align="center">
        <b>Input Image</b><br/>
        <img src="../data/images/castle.jpg" width="400" alt="Castle input image"/>
      </td>
      <td align="center">
        <b>3D Voxel Reconstruction</b><br/>
        <img src="castle.gif" width="400" alt="Castle 3D reconstruction animation"/>
      </td>
    </tr>
  </table>
</div>

### Room 1
<div align="center">
  <table>
    <tr>
      <td align="center">
        <b>Input Image</b><br/>
        <img src="../data/images/room1.jpg" width="400" alt="Room 1 input image"/>
      </td>
      <td align="center">
        <b>3D Voxel Reconstruction</b><br/>
        <img src="room1.gif" width="400" alt="Room 1 3D reconstruction animation"/>
      </td>
    </tr>
  </table>
</div>

### Room 2
<div align="center">
  <table>
    <tr>
      <td align="center">
        <b>Input Image</b><br/>
        <img src="../data/images/room2.jpg" width="400" alt="Room 2 input image"/>
      </td>
      <td align="center">
        <b>3D Voxel Reconstruction</b><br/>
        <img src="room2.gif" width="400" alt="Room 2 3D reconstruction animation"/>
      </td>
    </tr>
  </table>
</div>

### Room 3
<div align="center">
  <table>
    <tr>
      <td align="center">
        <b>Input Image</b><br/>
        <img src="../data/images/room3.jpg" width="400" alt="Room 3 input image"/>
      </td>
      <td align="center">
        <b>3D Voxel Reconstruction</b><br/>
        <img src="room3.gif" width="400" alt="Room 3 3D reconstruction animation"/>
      </td>
    </tr>
  </table>
</div>

### White House
<div align="center">
  <table>
    <tr>
      <td align="center">
        <b>Input Image</b><br/>
        <img src="../data/images/white_house.jpg" width="400" alt="White house input image"/>
      </td>
      <td align="center">
        <b>3D Voxel Reconstruction</b><br/>
        <img src="white_house.gif" width="400" alt="White house 3D reconstruction animation"/>
      </td>
    </tr>
  </table>
</div>

### Windows
<div align="center">
  <table>
    <tr>
      <td align="center">
        <b>Input Image</b><br/>
        <img src="../data/images/windows.jpg" width="400" alt="Windows input image"/>
      </td>
      <td align="center">
        <b>3D Voxel Reconstruction</b><br/>
        <img src="windows.gif" width="400" alt="Windows 3D reconstruction animation"/>
      </td>
    </tr>
  </table>
</div>

### Bedroom
<div align="center">
  <table>
    <tr>
      <td align="center">
        <b>Input Image</b><br/>
        <img src="../data/images/bedroom.jpg" width="400" alt="Bedroom input image"/>
      </td>
      <td align="center">
        <b>3D Voxel Reconstruction</b><br/>
        <img src="bedroom.gif" width="400" alt="Bedroom 3D reconstruction animation"/>
      </td>
    </tr>
  </table>
</div>

## Additional Sample Images

All sample images now have corresponding 3D reconstructions above.

To generate your own 3D reconstructions and GIFs, use:

```bash
python demo_pyoctomap.py --input data/images/<image_name>.jpg --visualize --gif examples/<output_name>.gif --resolution 0.005
```

## How to Generate New Examples

1. Place your input image in `data/images/`
2. Run the reconstruction with GIF generation:
   ```bash
   python demo_pyoctomap.py --input data/images/your_image.jpg --gif examples/your_output.gif --resolution 0.005
   ```
3. The GIF will be saved in the `examples/` folder

For best results, use high-resolution images with good lighting and clear depth cues.
