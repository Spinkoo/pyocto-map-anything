# pyocto-map-anything

Bring your images to life in 3D: Instantly transform a single photo into a vibrant voxel scene with the power of **AI depth estimation** and **OctoMap**.

This demo showcases **[pyoctomap](https://github.com/Spinkoo/pyoctomap)** - Python bindings for OctoMap that enable direct integration of AI depth predictions into C++ `ColorOcTree` structures, all from Python. The pipeline seamlessly combines state-of-the-art depth estimation models with OctoMap's efficient voxel-based 3D mapping.

## Purpose

This repository demonstrates how to:

- **Reconstruct 3D environments** from single RGB images using AI depth estimation
- **Integrate depth predictions** directly into OctoMap's voxel-based representation
- **Support multiple depth models** through a unified API (Depth Anything v3 and HuggingFace models)
- **Automatically estimate camera intrinsics** when using Depth Anything v3 models
- **Visualize and save** 3D reconstructions as OctoMap files

Built on **[pyoctomap](https://github.com/Spinkoo/pyoctomap)**, this demo highlights the power of Python-native OctoMap bindings for robotics, SLAM, and 3D reconstruction applications.

## Model Versatility & OctoMap Integration

The pipeline supports two families of depth estimation models with seamless integration:

### Depth Anything v3 (DA3) Models

| Model | Accuracy | Speed | Intrinsics | Use Case |
|-------|----------|-------|------------|----------|
| `depth-anything/DA3NESTED-GIANT-LARGE` | Highest | Slowest | ✅ Automatic | Maximum accuracy needed |
| `depth-anything/DA3NESTED-LARGE` | High | Medium | ✅ Automatic | Best balance (recommended) |
| `depth-anything/DA3NESTED-BASE` | Good | Fast | ✅ Automatic | Faster inference |
| `depth-anything/DA3NESTED-SMALL` | Moderate | Fastest | ✅ Automatic | Real-time applications |

**Key Features:**
- **Automatic camera intrinsics estimation** - No need to provide fx, fy, cx, cy
- **High accuracy** depth predictions in meters
- **State-of-the-art** performance on diverse scenes

### HuggingFace Models

| Model | Accuracy | Speed | Intrinsics | Use Case |
|-------|----------|-------|------------|----------|
| `isl-org/ZoeDepth` | Excellent | Medium | ❌ FOV-based | High accuracy, general scenes |
| `Intel/dpt-large` | Very High | Slow | ❌ FOV-based | Maximum accuracy (HF models) |
| `Intel/dpt-hybrid-midas` (default) | Good | Medium | ❌ FOV-based | Balanced performance |
| `LiheYoung/depth-anything-v2-small-hf` | Good | Fast | ❌ FOV-based | Fast general purpose |
| `Intel/dpt-beit-large-512` | Moderate | Fastest | ❌ FOV-based | Quick processing |

**Key Features:**
- **Easy installation** - Works with standard `transformers` library
- **No special setup** required
- **Wide model selection** from HuggingFace Hub

### Unified Integration

All models work through the same API - simply change the `--model` argument. The pipeline automatically:
- Handles model-specific depth scaling
- Extracts camera intrinsics (DA3 models)
- Projects depth maps to 3D point clouds
- Fuses points into OctoMap's `ColorOcTree` structure

The **pyoctomap** library provides the bridge between Python and OctoMap's C++ implementation, enabling efficient voxel-based mapping directly from Python code.

## Installation

### Standard Dependencies

Install the core dependencies:

```bash
pip install -r requirements.txt
```

This installs:
- `pyoctomap` - Python bindings for OctoMap
- `transformers` - For HuggingFace depth models
- `torch` - PyTorch for model inference
- `opencv-python` - Image processing
- `open3d` - 3D visualization
- `numpy` - Numerical operations

### Depth Anything v3 Installation

To use Depth Anything v3 models, you need to install the `depth_anything_3` package separately:

#### Option 1: Quick Install (Recommended)

```bash
# Install PyTorch dependencies
pip install xformers torch>=2 torchvision

# Install depth-anything-v3
pip install depth-anything-v3
```

#### Option 2: From Source

For the latest features or if you encounter issues:

```bash
# Install PyTorch dependencies
pip install xformers torch>=2 torchvision

# Clone the repository
git clone https://github.com/LiheYoung/Depth-Anything-V3.git
cd Depth-Anything-V3

# Install the package
pip install -e .
```

**Note:** CUDA is recommended for faster inference. The models will work on CPU but will be significantly slower.

**Reference:** For detailed installation instructions and troubleshooting, see the [Depth Anything V3 repository](https://github.com/LiheYoung/Depth-Anything-V3).

## Usage

### Basic Example

Process a single image with the default model:

```bash
python demo_pyoctomap.py --input data/images/room2.jpg --visualize --resolution 0.005
```

### Using Depth Anything v3 Models

Depth Anything v3 models provide automatic camera intrinsics estimation:

```bash
# Using DA3-LARGE model
python demo_pyoctomap.py --input data/images/room1.jpg --visualize --model "depth-anything/DA3-LARGE" --resolution 0.005

# Using DA3-GIANT-LARGE for highest accuracy
python demo_pyoctomap.py --input data/images/room2.jpg --visualize --model "depth-anything/DA3NESTED-GIANT-LARGE" --resolution 0.005
```

When using DA3 models, you'll see output like:
```
Using DA3 estimated intrinsics: fx=381.6, fy=381.1, cx=252.0, cy=168.0
```

### Using HuggingFace Models

HuggingFace models use FOV-based intrinsics (default 65°):

```bash
# Using ZoeDepth (high accuracy)
python demo_pyoctomap.py --input data/images/room2.jpg --visualize --model "Intel/zoedepth-nyu-kitti" --resolution 0.005

# Using default dpt-hybrid model
python demo_pyoctomap.py --input data/images/room3.jpg --visualize --resolution 0.005
```

### Saving OctoMap Files

Save the reconstruction to a file:

```bash
python demo_pyoctomap.py --input data/images/room3.jpg --model "depth-anything/DA3-LARGE" --output my_reconstruction.ot
```

### High-Resolution Mapping

For detailed reconstructions, use smaller resolution values:

```bash
python demo_pyoctomap.py --input data/images/white_house.jpg --visualize --model "depth-anything/DA3-LARGE" --resolution 0.005
```

## Command Reference

### Arguments

- `--input` (required): Path to input image file
- `--model`: Depth estimation model name (default: `dpt-hybrid`)
  - DA3 models: `depth-anything/DA3NESTED-GIANT-LARGE`, `depth-anything/DA3NESTED-LARGE`, `depth-anything/DA3NESTED-BASE`, `depth-anything/DA3NESTED-SMALL`
  - HF models: `Intel/zoedepth-nyu-kitti`, `Intel/dpt-large`, `Intel/dpt-hybrid`, `LiheYoung/depth-anything-v2-small-hf`, `Intel/dpt-beit-large-512`
- `--resolution`: OctoMap voxel resolution in meters (default: `0.05`)
  - Smaller values = higher detail but more memory
  - Recommended: `0.005` for detailed scenes, `0.05` for general use
- `--fov`: Camera field of view in degrees (default: `65.0`)
  - Only used for HuggingFace models (DA3 models estimate intrinsics automatically)
- `--visualize`: Open interactive 3D viewer
- `--output`: Output file path for OctoMap (.ot format)

### Model Selection Guide

**Choose DA3 models when:**
- You need automatic camera intrinsics estimation
- You want highest accuracy depth predictions
- You have CUDA available for faster inference

**Choose HuggingFace models when:**
- You want quick setup without additional dependencies
- You prefer models from the HuggingFace ecosystem
- You're working on CPU or have limited GPU memory

### Resolution Recommendations

- **0.005m (5mm)**: High detail, suitable for indoor scenes, furniture, objects
- **0.01m (1cm)**: Good balance for most indoor/outdoor scenes
- **0.05m (5cm)**: General purpose, faster processing, less memory

## Project Structure

```
pyocto-map-anything/
│
├── demo_pyoctomap.py      # Main demo script
├── depth_processor.py     # Depth model loading and inference
├── model_handler.py       # Model-specific handling (DA3 vs HF)
├── data_handler.py        # 3D point cloud projection
├── visualizer.py          # Open3D visualization
├── requirements.txt       # Python dependencies
└── data/
    └── images/           # Sample images for testing
```

## About pyoctomap

This demo is built on **[pyoctomap](https://github.com/Spinkoo/pyoctomap)**, a Python binding library for OctoMap that provides:

- Direct access to OctoMap's `ColorOcTree` from Python
- Efficient voxel-based 3D mapping
- Color integration for visual mapping
- Binary file I/O for map persistence

Visit the [pyoctomap repository](https://github.com/Spinkoo/pyoctomap) to learn more about the library and explore additional features.

## Notes

- Illustrations and visual examples will be added in a future update
- For issues or questions about Depth Anything v3, refer to the [official repository](https://github.com/LiheYoung/Depth-Anything-V3)
- For pyoctomap-related questions, visit the [pyoctomap repository](https://github.com/Spinkoo/pyoctomap)
