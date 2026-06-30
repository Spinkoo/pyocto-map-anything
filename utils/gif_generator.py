"""
Generate rotating GIF animations from 3D OctoMap reconstructions
"""
import math
import open3d as o3d
import numpy as np
from PIL import Image
import os
import tempfile
import shutil


def _aabb_corners(points):
    """Return the 8 corners of the axis-aligned bounding box."""
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    return np.array([
        [mins[0], mins[1], mins[2]],
        [mins[0], mins[1], maxs[2]],
        [mins[0], maxs[1], mins[2]],
        [mins[0], maxs[1], maxs[2]],
        [maxs[0], mins[1], mins[2]],
        [maxs[0], mins[1], maxs[2]],
        [maxs[0], maxs[1], mins[2]],
        [maxs[0], maxs[1], maxs[2]],
    ])


def _rotation_matrix(angle, rotation_axis='y'):
    """Rotation matrix for spinning geometry around the scene center."""
    c, s = np.cos(angle), np.sin(angle)
    if rotation_axis == 'y':
        return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])
    if rotation_axis == 'x':
        return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def _rotate_points(points, center, angle, rotation_axis='y'):
    """Rotate points around center by angle (radians)."""
    R = _rotation_matrix(angle, rotation_axis)
    return (points - center) @ R.T + center


# Fixed camera: looks at the scene from +Z toward the origin (Open3D uses -front)
CAMERA_FRONT = np.array([0.0, 0.0, 1.0])


def _camera_axes(front, up):
    """Build an orthonormal camera basis (right, image-up) from view direction."""
    front = front / np.linalg.norm(front)
    up = np.asarray(up, dtype=float)
    up = up / np.linalg.norm(up)
    right = np.cross(up, front)
    right_norm = np.linalg.norm(right)
    if right_norm < 1e-8:
        up = np.array([0.0, 0.0, 1.0])
        right = np.cross(up, front)
        right_norm = np.linalg.norm(right)
    right /= right_norm
    img_up = np.cross(front, right)
    img_up /= np.linalg.norm(img_up)
    return right, img_up


def _projected_extents(corners, center, front, up):
    """Half-width and half-height of the AABB projected onto the view plane."""
    right, img_up = _camera_axes(front, up)
    offsets = corners - center
    max_x = float(np.max(np.abs(offsets @ right)))
    max_y = float(np.max(np.abs(offsets @ img_up)))
    return max_x, max_y


def _max_projected_radius(corners, center, num_frames, rotation_axis, up, aspect,
                          camera_front=CAMERA_FRONT):
    """Largest half-span on screen as geometry rotates in front of a fixed camera."""
    max_radius = 0.0
    for i in range(num_frames):
        angle = 2 * np.pi * i / num_frames
        rotated = _rotate_points(corners, center, angle, rotation_axis)
        extent_x, extent_y = _projected_extents(rotated, center, camera_front, up)
        max_radius = max(max_radius, extent_x / aspect, extent_y)
    return max_radius


def _fit_camera_to_scene(ctr, vis, corners, center, num_frames, rotation_axis,
                         up, width, height, padding=1.05, zoom=None,
                         camera_front=CAMERA_FRONT):
    """
    Lock the camera and frame the scene tightly by fitting vertical FOV to the
    worst-case projection as geometry rotates. Falls back to fixed zoom when set.
    """
    aspect = width / height
    up = np.asarray(up, dtype=float)
    camera_front = np.asarray(camera_front, dtype=float)

    ctr.set_lookat(center)
    ctr.set_front(camera_front)
    ctr.set_up(up)
    for _ in range(15):
        vis.poll_events()
        vis.update_renderer()

    vis.reset_view_point(True)
    for _ in range(15):
        vis.poll_events()
        vis.update_renderer()

    if zoom is not None:
        ctr.set_zoom(zoom)
    else:
        max_radius = _max_projected_radius(
            corners, center, num_frames, rotation_axis, up, aspect, camera_front
        )
        extent_x, extent_y = _projected_extents(corners, center, camera_front, up)
        visible_radius = max(extent_x / aspect, extent_y)

        if max_radius >= 1e-9 and visible_radius >= 1e-9:
            fov_deg = ctr.get_field_of_view()
            half_tan = math.tan(math.radians(fov_deg) / 2.0)
            target_half_tan = half_tan * max_radius * padding / visible_radius
            target_fov_deg = math.degrees(2.0 * math.atan(target_half_tan))
            ctr.change_field_of_view(target_fov_deg - fov_deg)
        else:
            ctr.set_zoom(0.7)

    # reset_view_point moves the camera; lock it back before animating geometry
    ctr.set_lookat(center)
    ctr.set_front(camera_front)
    ctr.set_up(up)
    for _ in range(10):
        vis.poll_events()
        vis.update_renderer()


def create_rotating_gif(points, colors, output_path, resolution=0.05, num_frames=60,
                        rotation_axis='y', fps=10, width=1024, height=768,
                        zoom=None, padding=1.05):
    """
    Create a rotating GIF animation of a 3D scene.
    
    Args:
        points: (N, 3) numpy array of 3D points
        colors: (N, 3) numpy array of RGB colors (0-1 range)
        output_path: Path to save the GIF file
        resolution: Voxel resolution for display
        num_frames: Number of frames in the animation (default: 60 for full rotation)
        rotation_axis: Axis to rotate around ('y' for horizontal, 'x' for vertical)
        fps: Frames per second for the GIF
        width: Image width in pixels
        height: Image height in pixels
        zoom: Fixed camera zoom (None = auto-fit from projected bounds)
        padding: Margin around the scene when auto-fitting (1.05 = 5% border)
    """
    if len(points) == 0:
        print("No points to visualize")
        return

    orig_points = np.asarray(points, dtype=float)
    orig_colors = np.asarray(colors, dtype=float)
    
    # Create temporary directory for frames
    temp_dir = tempfile.mkdtemp()
    frame_paths = []
    
    try:
        # Create point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        pcd.colors = o3d.utility.Vector3dVector(colors)
        
        # For very fine resolutions (< 0.005), use point cloud directly
        # For coarser resolutions, create a voxel grid for better visualization
        use_point_cloud = resolution < 0.005
        display_resolution = None
        
        if use_point_cloud:
            print(f"Using point cloud directly (resolution {resolution:.6f} is very fine)")
            voxel_grid = None
        else:
            # Create voxel grid for better visualization
            # For fine resolutions, use the actual resolution or a small multiplier
            # For coarser resolutions, use a larger multiplier
            if resolution < 0.01:
                # Fine resolution: use actual resolution or very small multiplier
                display_resolution = resolution * 1.1
            else:
                # Coarser resolution: use larger multiplier for better visualization
                display_resolution = resolution * 1.5
            
            print(f"Using voxel grid with display resolution: {display_resolution:.6f} (OctoMap resolution: {resolution:.6f})")
            
            voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(
                pcd, voxel_size=display_resolution
            )
            
            # Check if voxel grid has any voxels
            if len(voxel_grid.get_voxels()) == 0:
                print("Warning: Voxel grid is empty, falling back to point cloud")
                use_point_cloud = True
                voxel_grid = None
        
        # Use AABB center so framing matches the projected bounds
        mins = points.min(axis=0)
        maxs = points.max(axis=0)
        center = (mins + maxs) / 2.0
        corners = _aabb_corners(points)
        up = np.array([0.0, 1.0, 0.0])
        
        # Create visualizer - use invisible window to avoid blocking main window
        vis = o3d.visualization.Visualizer()
        vis.create_window(width=width, height=height, visible=False)
        
        # Add geometry based on whether we're using voxel grid or point cloud
        if use_point_cloud:
            vis.add_geometry(pcd)
        else:
            vis.add_geometry(voxel_grid)
        
        # Get view control
        ctr = vis.get_view_control()
        if ctr is None:
            vis.destroy_window()
            raise RuntimeError(
                "Open3D failed to initialize the render window (get_view_control returned None). "
                "On WSL, try: export XDG_SESSION_TYPE=x11"
            )

        _fit_camera_to_scene(
            ctr, vis, corners, center, num_frames, rotation_axis,
            up, width, height, padding=padding, zoom=zoom,
        )

        def _update_geometry(angle):
            nonlocal voxel_grid
            rotated_points = _rotate_points(orig_points, center, angle, rotation_axis)
            if use_point_cloud:
                pcd.points = o3d.utility.Vector3dVector(rotated_points)
                pcd.colors = o3d.utility.Vector3dVector(orig_colors)
                vis.update_geometry(pcd)
            else:
                vis.remove_geometry(voxel_grid, reset_bounding_box=False)
                rotated_pcd = o3d.geometry.PointCloud()
                rotated_pcd.points = o3d.utility.Vector3dVector(rotated_points)
                rotated_pcd.colors = o3d.utility.Vector3dVector(orig_colors)
                voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(
                    rotated_pcd, voxel_size=display_resolution
                )
                vis.add_geometry(voxel_grid, reset_bounding_box=False)
        
        # Generate frames — fixed camera, rotating geometry
        print(f"Generating {num_frames} frames for rotation...")
        for i in range(num_frames):
            angle = 2 * np.pi * i / num_frames
            _update_geometry(angle)
            
            # Update renderer multiple times to ensure proper rendering
            # More passes for invisible window to ensure proper rendering
            for _ in range(30):
                vis.poll_events()
                vis.update_renderer()
            
            # Capture frame using float buffer (more reliable than capture_screen_image)
            frame_path = os.path.join(temp_dir, f"frame_{i:04d}.png")
            try:
                # Use float buffer method which is more reliable
                img_buffer = vis.capture_screen_float_buffer(do_render=True)
                if img_buffer is not None:
                    # Convert to numpy array
                    img_array = np.asarray(img_buffer)
                    # Convert from [0,1] float to [0,255] uint8
                    img_array = (np.clip(img_array, 0, 1) * 255).astype(np.uint8)
                    # Open3D returns images in correct orientation, no need to flip
                    # Convert to PIL Image and save
                    img = Image.fromarray(img_array)
                    img.save(frame_path)
                    frame_paths.append(frame_path)
                else:
                    # Fallback: try capture_screen_image
                    success = vis.capture_screen_image(frame_path, do_render=True)
                    if success and os.path.exists(frame_path):
                        frame_paths.append(frame_path)
                    else:
                        print(f"Warning: Failed to capture frame {i}")
            except Exception as e:
                print(f"Warning: Error capturing frame {i}: {e}")
            
            if (i + 1) % 10 == 0:
                print(f"  Captured {i + 1}/{num_frames} frames...")
        
        vis.destroy_window()
        
        # Load frames and create GIF
        print("Creating GIF from frames...")
        images = []
        for frame_path in frame_paths:
            if os.path.exists(frame_path):
                img = Image.open(frame_path)
                # Convert RGBA to RGB if needed
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                # Check if image is not all black
                img_array = np.array(img)
                if np.any(img_array > 0):  # Has non-black pixels
                    images.append(img)
                else:
                    print(f"Warning: Frame {os.path.basename(frame_path)} is all black, skipping")
        
        # Save as GIF
        if len(images) > 0:
            images[0].save(
                output_path,
                save_all=True,
                append_images=images[1:],
                duration=int(1000 / fps),  # Duration in milliseconds
                loop=0  # Infinite loop
            )
            print(f"GIF saved to {output_path} ({len(images)} frames)")
        else:
            print("Error: No valid frames captured (all frames were black)")
            print(f"Captured {len(frame_paths)} frame files, but none contain visible content")
            
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def generate_gif_from_octomap(octomap_handler, output_path, resolution=0.05, **kwargs):
    """
    Generate a rotating GIF from an OctoMap handler.
    
    This is a convenience wrapper that extracts the structure from the OctoMap
    and generates the GIF in one call.
    
    Args:
        octomap_handler: OctomapHandler instance with the map data
        output_path: Path to save the GIF file (will add .gif if missing)
        resolution: Voxel resolution for display
        **kwargs: Additional arguments passed to create_rotating_gif
                  (num_frames, rotation_axis, fps, width, height, zoom, padding)
    
    Returns:
        True if GIF was generated successfully, False otherwise
    """
    # Extract structure from OctoMap
    points, colors = octomap_handler.get_structure()
    
    if len(points) == 0:
        print("No voxels to display in GIF")
        return False
    
    # Ensure output path has .gif extension
    if not output_path.endswith('.gif'):
        output_path = f"{output_path}.gif"
    
    print("Generating rotating GIF (this may take a moment)...")
    create_rotating_gif(points, colors, output_path, resolution=resolution, **kwargs)
    return True

