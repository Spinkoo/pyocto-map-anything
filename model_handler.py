import warnings
import os
from PIL import Image
import numpy as np

# Disable torch dynamo/inductor to prevent nvrtc JIT compilation errors
# (e.g. "invalid value for --gpu-architecture")
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")

import torch
if hasattr(torch, '_dynamo'):
    torch._dynamo.config.suppress_errors = True

# Suppress transformers warnings
warnings.filterwarnings("ignore", message=".*were not initialized from the model checkpoint.*")

class DepthModel:
    def __init__(self, model_name, is_da3=False):
        self.is_da3 = is_da3

        if self.is_da3:
            try:
                from depth_anything_3.api import DepthAnything3
            except ImportError:
                raise ImportError("depth_anything_3 package not found. Install it with: pip install depth-anything-v3")

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model = DepthAnything3.from_pretrained(model_name).to(device)
        else:
            from transformers import pipeline
            device_arg = 0 if torch.cuda.is_available() else -1
            self.pipe = pipeline(task="depth-estimation", model=model_name, device=device_arg)

    def infer_batch(self, rgb_list):
        if self.is_da3:
            # DA3 expects numpy arrays directly
            prediction = self.model.inference(rgb_list)
            depths = [prediction.depth[i] for i in range(prediction.depth.shape[0])]

            # Extract intrinsics from DA3 if available
            intrinsics_list = []
            if prediction.intrinsics is not None:
                for i in range(prediction.depth.shape[0]):
                    K = prediction.intrinsics[i]  # 3x3 camera matrix
                    intrinsics_dict = {
                        'fx': float(K[0, 0]),
                        'fy': float(K[1, 1]),
                        'cx': float(K[0, 2]),
                        'cy': float(K[1, 2])
                    }
                    intrinsics_list.append(intrinsics_dict)
            else:
                intrinsics_list = [None] * len(depths)
        else:
            # HF models expect PIL Images
            pil_images = [Image.fromarray(img) if isinstance(img, np.ndarray) else img for img in rgb_list]
            import torch
            with torch.inference_mode():
                outs = self.pipe(pil_images)
            depths = [out["depth"] for out in outs]
            intrinsics_list = [None] * len(depths)  # HF models don't provide intrinsics

        return depths, intrinsics_list

