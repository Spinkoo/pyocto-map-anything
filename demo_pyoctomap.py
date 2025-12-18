"""
3D Reconstruction Demo using Depth Estimation and OctoMap
"""
import argparse
import numpy as np
import cv2
import pyoctomap

from depth_processor import DepthProcessor
from data_handler import DataHandler


class OctomapHandler:
    def __init__(self, resolution=0.05):
        self.tree = pyoctomap.ColorOcTree(resolution)
        self.tree.setProbHit(0.9)
        self.tree.setProbMiss(0.4)
        self.tree.setClampingThresMin(0.12)
        self.tree.setClampingThresMax(0.97)

    def insert_cloud(self, points, colors, origin=None):
        if len(points) == 0:
            return

        points_double = points.astype(np.float64)
        if origin is None:
            origin = np.array([0., 0., 0.], dtype=np.float64)
        else:
            origin = np.array(origin, dtype=np.float64)
        self.tree.insertPointCloudWithColor(points_double, colors, origin, lazy_eval=True)


    def get_structure(self):
        # Extract occupied voxels and their colors
        occupied_nodes = []
        node_colors = []
        for it in self.tree.begin_leafs(maxDepth=0):
            if self.tree.isNodeOccupied(it):
                c = it.getCoordinate()
                color = it.getColor()
                occupied_nodes.append([c[0], c[1], c[2]])
                node_colors.append([color[0], color[1], color[2]])

        return np.array(occupied_nodes), np.array(node_colors).astype(float) / 255.0

    def save(self, filename):
        self.tree.updateInnerOccupancy()
        self.tree.writeBinary(filename)



# --- MAIN PIPELINE ---
def load_image(args):
    frame = cv2.imread(args.input)
    if frame is None:
        raise ValueError(f"Could not open image: {args.input}")
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w = frame.shape[:2]  
    return frame, h, w

def run_pipeline(args):
    # Load image
    img_rgb, h, w = load_image(args)

    # Initialize components
    depth_proc = DepthProcessor(model_name=args.model)
    octomap_handler = OctomapHandler(resolution=args.resolution)
    data_handler = DataHandler(w, h, fov_degrees=args.fov)

    # Process depth
    depth, intrinsics = depth_proc.get_depth(img_rgb, return_intrinsics=True)

    # Handle dimension mismatch (DA3 may resize images)
    depth_h, depth_w = depth.shape[:2]
    if (depth_h, depth_w) != (h, w):
        print(f"Depth map size {depth_w}x{depth_h} differs from input {w}x{h}, updating DataHandler")
        img_rgb = cv2.resize(img_rgb, (depth_w, depth_h), interpolation=cv2.INTER_LINEAR)
        h, w = depth_h, depth_w

    # Use DA3 intrinsics if available, otherwise use FOV
    if intrinsics is not None:
        print(f"Using DA3 estimated intrinsics: fx={intrinsics['fx']:.1f}, fy={intrinsics['fy']:.1f}, cx={intrinsics['cx']:.1f}, cy={intrinsics['cy']:.1f}")
        data_handler = DataHandler(w, h, fx=intrinsics['fx'], fy=intrinsics['fy'],
                                   cx=intrinsics['cx'], cy=intrinsics['cy'])
    else:
        data_handler = DataHandler(w, h, fov_degrees=args.fov)

    # Project to 3D
    raw_points, colors = data_handler.project_to_3d(depth, img_rgb, center_around_origin=True)
    print(f"Generated {len(raw_points):,} 3D points")

    # Build OctoMap
    octomap_handler.insert_cloud(raw_points, colors)
    print(f"Map contains {octomap_handler.tree.size()} voxels")

    # Save results
    if args.output:
        octomap_handler.save(args.output)
        print(f"Saved to {args.output}")

    # Generate GIF if requested (do this BEFORE visualization to avoid window conflicts)
    if args.gif:
        from utils.gif_generator import generate_gif_from_octomap
        generate_gif_from_octomap(octomap_handler, args.gif, resolution=args.resolution)

    # Visualize (after GIF generation to avoid window conflicts)
    if args.visualize:
        from visualizer import Visualizer
        vis = Visualizer(resolution=args.resolution)

        points, colors = octomap_handler.get_structure()
        if len(points) > 0:
            vis.update(points, colors)
            print("Press 'q' to exit")

            while not vis.is_closed:
                vis.vis.poll_events()
                vis.vis.update_renderer()
                import time
                time.sleep(0.01)
        else:
            print("No voxels to display")

        vis.close()


if __name__ == "__main__":
    # Available models for help text
    model_options = [
        "DA3 models (provide intrinsics, require depth_anything_3): depth-anything/DA3NESTED-GIANT-LARGE, depth-anything/DA3NESTED-LARGE, depth-anything/DA3NESTED-BASE, depth-anything/DA3NESTED-SMALL",
        "HF models: Intel/zoedepth-nyu-kitti, Intel/dpt-large, Intel/dpt-hybrid (default), LiheYoung/depth-anything-v2-small-hf, Intel/dpt-beit-large-512"
    ]

    parser = argparse.ArgumentParser(
        description="3D Reconstruction from Images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Available models:\n" + "\n".join(f"  {opt}" for opt in model_options)
    )
    parser.add_argument("--input", required=True, help="Path to input image file")
    parser.add_argument("--model", default="dpt-hybrid",
                       help="Depth estimation model (see available models below)")
    parser.add_argument("--resolution", type=float, default=0.05, help="OctoMap resolution in meters")
    parser.add_argument("--fov", type=float, default=65.0, help="Camera field of view in degrees")
    parser.add_argument("--visualize", action="store_true", help="Show 3D visualization")
    parser.add_argument("--output", help="Output file path for OctoMap (.ot)")
    parser.add_argument("--gif", help="Generate rotating GIF animation (specify output path)")

    args = parser.parse_args()
    run_pipeline(args)