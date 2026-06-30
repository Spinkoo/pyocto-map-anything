import numpy as np
from model_handler import DepthModel

# Available depth estimation models
AVAILABLE_MODELS = {
    # Depth Anything v3 models (require depth_anything_3 package)
    "da3-giant-large": "depth-anything/DA3NESTED-GIANT-LARGE-1.1",
    "da3-large": "depth-anything/DA3-LARGE-1.1",
    "da3-base": "depth-anything/DA3-BASE",
    "da3-small": "depth-anything/DA3-SMALL",
    # HuggingFace transformers models
    "zoe": "Intel/zoedepth-nyu-kitti",
    "dpt-large": "Intel/dpt-large",
    "dpt-hybrid": "Intel/dpt-hybrid-midas",
    "depth-anything": "depth-anything/Depth-Anything-V2-Small-hf",
    "midas-small": "Intel/dpt-beit-large-512",
}

class DepthProcessor:
    def __init__(self, model_name="dpt-hybrid"):
        # Store original name to detect model type
        self.original_name = model_name

        if model_name in AVAILABLE_MODELS:
            model_name = AVAILABLE_MODELS[model_name]

        # Check if this is a DA3 model
        self.is_da3 = ("depth-anything/DA3" in model_name or "DA3" in model_name or
                       self.original_name.startswith("da3-"))

        self.model = DepthModel(model_name, is_da3=self.is_da3)

    def get_depth(self, img_rgb, return_intrinsics=False):
        depths, intrinsics_list = self.model.infer_batch([img_rgb])
        depth_raw = depths[0]
        intrinsics = intrinsics_list[0] if intrinsics_list else None

        if hasattr(depth_raw, 'getdata'):
            depth_map = np.array(depth_raw)
        else:
            depth_map = np.array(depth_raw)

        # DA3 models already return depth in meters, HF models need scaling
        if self.is_da3:
            # DA3 depth is already in meters
            depth_clipped = np.clip(depth_map, 0.1, 5.0)
        else:
            # HF models return relative depth, apply scaling
            depth_clipped = np.clip(depth_map * 0.02, 0.1, 5.0)

        if return_intrinsics:
            return depth_clipped, intrinsics
        return depth_clipped