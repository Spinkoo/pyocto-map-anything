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
        self.vis.add_geometry(self.pcd)
        self.voxel_grid = None
        self._first_update = True

    def update(self, points, colors):
        if self.is_closed or len(points) == 0:
            return

        self.pcd.points = o3d.utility.Vector3dVector(points)
        self.pcd.colors = o3d.utility.Vector3dVector(colors)

        if self.voxel_grid:
            self.vis.remove_geometry(self.voxel_grid, reset_bounding_box=False)

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
