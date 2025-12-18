import numpy as np

class DataHandler:
    def __init__(self, width, height, fov_degrees=65.0, fx=None, fy=None, cx=None, cy=None):
        self.w = width
        self.h = height

        # Calculate focal length from field of view
        fov_rad = np.radians(fov_degrees)
        self.fx = fx if fx is not None else width / (2.0 * np.tan(fov_rad / 2.0))
        self.fy = fy if fy is not None else self.fx
        self.cx = cx if cx is not None else width / 2.0
        self.cy = cy if cy is not None else height / 2.0
        print(f"fx: {self.fx}, fy: {self.fy}, cx: {self.cx}, cy: {self.cy} instead of {width / (2.0 * np.tan(fov_rad / 2.0))}, {width / (2.0 * np.tan(fov_rad / 2.0))}, {width / 2.0}, {height / 2.0}")
        # Pre-compute pixel grid
        self.u, self.v = np.meshgrid(np.arange(width), np.arange(height))

    def project_to_3d(self, depth_map, img_rgb, center_around_origin=True):
        # Mask valid pixels
        mask = (depth_map > 0.1) & (depth_map < 4.5)

        # Extract valid data
        z = depth_map[mask]
        u_valid = self.u[mask]
        v_valid = self.v[mask]
        colors = img_rgb[v_valid, u_valid]

        # Pinhole projection
        x = (u_valid - self.cx) * z / self.fx
        y = -(v_valid - self.cy) * z / self.fy  # Flip Y

        points = np.stack([x, y, z], axis=1)

        if center_around_origin:
            center = points.mean(axis=0, keepdims=True)
            points = points - center
            points[:, 2] = -points[:, 2]  # Flip Z
            points[:, 2] += 1.0  # Shift forward
        colors = colors / 255.0
        return points, colors