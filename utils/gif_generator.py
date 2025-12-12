"""
Generate rotating GIF animations from 3D OctoMap reconstructions
"""
import open3d as o3d
import numpy as np
from PIL import Image
import os
import tempfile
import shutil
import time


def create_rotating_gif(points, colors, output_path, resolution=0.05, num_frames=60, 
                        rotation_axis='y', fps=10, width=1024, height=768):
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
    """
    if len(points) == 0:
        print("No points to visualize")
        return
    
    # Create temporary directory for frames
    temp_dir = tempfile.mkdtemp()
    frame_paths = []
    
    try:
        # Create point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        pcd.colors = o3d.utility.Vector3dVector(colors)
        
        # Create voxel grid for better visualization
        display_resolution = resolution * 1.5
        voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(
            pcd, voxel_size=display_resolution
        )
        
        # Calculate center and bounds of the scene
        center = points.mean(axis=0)
        bounds = points.max(axis=0) - points.min(axis=0)
        max_dim = np.max(bounds)
        
        # Create visualizer - use invisible window to avoid blocking main window
        vis = o3d.visualization.Visualizer()
        vis.create_window(width=width, height=height, visible=False)
        
        vis.add_geometry(voxel_grid)
        
        # Get view control
        ctr = vis.get_view_control()
        
        # Set initial camera position
        ctr.set_lookat(center)
        ctr.set_up([0, 1, 0])
        ctr.set_front([0, 0, -1])
        ctr.set_zoom(0.7)
        
        # Force initial render with multiple passes
        # Don't use sleep here as it blocks - just render multiple times
        for _ in range(30):
            vis.poll_events()
            vis.update_renderer()
        
        # Generate frames
        print(f"Generating {num_frames} frames for rotation...")
        for i in range(num_frames):
            # Calculate rotation angle (full 360 degrees)
            angle = 2 * np.pi * i / num_frames
            
            if rotation_axis == 'y':
                # Rotate around Y axis (horizontal rotation)
                front_x = np.sin(angle)
                front_z = np.cos(angle)
                front = np.array([front_x, 0, front_z])
            elif rotation_axis == 'x':
                # Rotate around X axis (vertical rotation)
                front_y = np.sin(angle)
                front_z = np.cos(angle)
                front = np.array([0, front_y, front_z])
            else:
                # Default to Y axis
                front_x = np.sin(angle)
                front_z = np.cos(angle)
                front = np.array([front_x, 0, front_z])
            
            # Normalize front vector
            front = front / np.linalg.norm(front)
            
            # Set camera view
            ctr.set_front(front)
            ctr.set_lookat(center)
            ctr.set_up([0, 1, 0])
            
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
                  (num_frames, rotation_axis, fps, width, height)
    
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

