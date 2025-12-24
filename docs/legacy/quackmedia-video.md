# QuackMedia Video Processing

A clean, streaming-first video processing library built on FFmpeg.

## Prerequisites

- **FFmpeg** and **ffprobe** must be installed and available on PATH
- Python 3.8+
- Dependencies: `ffmpeg-python`, `numpy`, `pydantic`

### Installing FFmpeg

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html or use chocolatey:
```bash
choco install ffmpeg
```

## Quick Start

```python
from pathlib import Path
from quackmedia.video import probe, slice_video, extract_frames, extract_audio

# Probe video metadata
info = probe(Path("input.mp4"))
print(f"Duration: {info.duration}s, Resolution: {info.width}x{info.height}")

# Extract a 10-second clip
clip = slice_video(
    Path("input.mp4"), 
    Path("output/clip.mp4"), 
    start=5.0, 
    end=15.0, 
    overwrite=True
)

# Extract frames at 2 fps
frames = extract_frames(
    Path("input.mp4"), 
    Path("output/frames"), 
    fps=2.0
)
print(f"Extracted {frames.total} frames to {frames.output_dir}")

# Extract audio track
audio = extract_audio(
    Path("input.mp4"), 
    Path("output/audio.flac")
)
print(f"Extracted audio: {audio.duration}s")
```

## Streaming Frame Processing

All frame operations return iterators for memory efficiency:

```python
from quackmedia.video import read_frames, keyframes, scene_changes

# Process frames one at a time (no lists in memory)
for frame in read_frames(Path("video.mp4"), fps=10.0):
    # frame is numpy array (height, width, 3) uint8
    processed = process_frame(frame)
    # ... do something with frame

# Extract keyframes
for timestamp, frame in keyframes(Path("video.mp4")):
    print(f"Keyframe at {timestamp:.2f}s")
    save_frame(frame, f"keyframe_{timestamp:.2f}.png")

# Detect scene changes
for timestamp, frame in scene_changes(Path("video.mp4"), threshold=0.3):
    print(f"Scene change at {timestamp:.2f}s")
```

## Writing Videos

```python
import numpy as np
from quackmedia.video import write_video

# Create frames programmatically
frames = []
for i in range(90):  # 3 seconds at 30fps
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    frames.append(frame)

# Write to video file
result = write_video(
    frames, 
    Path("output.mp4"), 
    fps=30.0,
    codec="libx264",
    crf=23  # Quality (lower = better)
)
print(f"Wrote {result.frame_count} frames, duration: {result.duration}s")
```

## Generating Test Videos

Use synthetic generators for testing:

```python
from quackmedia.video.synthetic.video import VideoGenerator, VideoConfig

# Generate a small test video
config = VideoConfig(
    duration=5.0,
    fps=24,
    width=640,
    height=480,
    pattern="color_bars"  # or "gradient", "checkerboard", etc.
)

generator = VideoGenerator(config)
test_video = generator.generate(Path("test_video.mp4"))
```

## API Reference

### Core Functions

- `probe(input_path)` → `VideoProbeResult` - Get video metadata
- `read_frames(input_path, **kwargs)` → `Iterator[np.ndarray]` - Stream video frames
- `extract_frame_at(input_path, timestamp)` → `np.ndarray` - Get single frame
- `write_video(frames, output_path, **kwargs)` → `WriteResult` - Write frames to video

### Operations

- `slice_video(input_path, output_path, start, end, **kwargs)` → `SliceResult`
- `extract_frames(input_path, output_dir, **kwargs)` → `ExtractFramesResult`
- `extract_audio(input_path, output_path, **kwargs)` → `AudioExtractResult`
- `transcode(input_path, output_path, **kwargs)` → `MediaOpResult`

### Detection

- `keyframes(input_path)` → `Iterator[Tuple[float, np.ndarray]]`
- `scene_changes(input_path, threshold=0.3)` → `Iterator[Tuple[float, np.ndarray]]`

### Error Handling

All functions raise subclasses of `QuackMediaError`:

- `ToolNotFound` - FFmpeg/ffprobe not found
- `InvalidInput` - Bad parameters or missing files  
- `OperationFailed` - FFmpeg operation failed

```python
from quackmedia.errors import ToolNotFound, InvalidInput, OperationFailed

try:
    result = probe(Path("video.mp4"))
except ToolNotFound:
    print("Please install FFmpeg")
except InvalidInput as e:
    print(f"Invalid input: {e}")
except OperationFailed as e:
    print(f"Operation failed: {e}")
    if e.ffmpeg_error:
        print(f"FFmpeg said: {e.ffmpeg_error}")
```

## Design Principles

- **Streaming first**: No large lists of frames in memory
- **Path objects**: All file paths are `pathlib.Path`
- **Consistent results**: All operations return Pydantic models
- **Clean errors**: Unified error hierarchy
- **No side effects**: Functions don't print or show progress bars

## Performance Tips

- Use lower `fps` for frame extraction when possible
- Use `reencode=False` for slicing when you don't need re-encoding
- Set appropriate `crf` values (18-28 range) for quality vs speed
- Use `preset="fast"` or `preset="ultrafast"` for speed over compression