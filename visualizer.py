import open3d as o3d
import numpy as np

class Visualizer:
    def __init__(self, resolution=0.05):
        self.resolution = resolution
        self.is_closed = False

        self.vis = o3d.visualization.VisualizerWithKeyCallback()
        self.vis.create_window(width=1024, height=768)
        self.vis.register_key_callback(ord("Q"), self._on_key_q)

        self.pcd = o3d.geometry.PointCloud()
        self.voxel_grid = None
        self._geometry_added = False
        self._first_update = True

    def update(self, points, colors):
        if self.is_closed or len(points) == 0:
            return

        self.pcd.points = o3d.utility.Vector3dVector(points)
        self.pcd.colors = o3d.utility.Vector3dVector(colors)

        # Remove existing geometry
        if self.voxel_grid:
            self.vis.remove_geometry(self.voxel_grid, reset_bounding_box=False)
            self.voxel_grid = None
        
        if self._geometry_added and self.resolution >= 0.005:
            # Remove point cloud if we were using it before and now switching to voxel grid
            self.vis.remove_geometry(self.pcd, reset_bounding_box=False)
            self._geometry_added = False
        
        # For very fine resolutions (< 0.005), use point cloud directly
        # For coarser resolutions, create a voxel grid for better visualization
        if self.resolution < 0.005:
            # Use point cloud directly for very fine resolutions
            if not self._geometry_added:
                self.vis.add_geometry(self.pcd, reset_bounding_box=self._first_update)
                self._geometry_added = True
            else:
                self.vis.update_geometry(self.pcd)
        else:
            # Create voxel grid for better visualization
            if self.resolution < 0.01:
                # Fine resolution: use actual resolution or very small multiplier
                display_resolution = self.resolution * 1.1
            else:
                # Coarser resolution: use larger multiplier for better visualization
                display_resolution = self.resolution * 1.5
            
            self.voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(
                self.pcd, voxel_size=display_resolution
            )
            self.vis.add_geometry(self.voxel_grid, reset_bounding_box=self._first_update)
        
        self._first_update = False

        self.vis.poll_events()
        self.vis.update_renderer()

    def _on_key_q(self, _vis):
        self.is_closed = True
        return False

    def close(self):
        if not self.is_closed:
            self.is_closed = True
            self.vis.destroy_window()
