from moviepy.editor import VideoFileClip
from pathlib import Path
import sys

video_path = Path('assets/videos/Building Resilience.mp4')

print(f"Testing video file: {video_path}")
print(f"File exists: {video_path.exists()}")
print(f"File size: {video_path.stat().st_size / (1024*1024):.2f} MB")

# Test 1: Try loading with default settings
print("\nTest 1: Loading with default settings...")
try:
    video = VideoFileClip(str(video_path))
    print(f"  SUCCESS - Duration: {video.duration:.2f}s, FPS: {video.fps}, Size: {video.size}")
    video.close()
except Exception as e:
    print(f"  FAILED: {e}")

# Test 2: Try loading without audio
print("\nTest 2: Loading without audio...")
try:
    video = VideoFileClip(str(video_path), audio=False)
    print(f"  SUCCESS - Duration: {video.duration:.2f}s, FPS: {video.fps}, Size: {video.size}")
    video.close()
except Exception as e:
    print(f"  FAILED: {e}")

# Test 3: Try loading with target_resolution
print("\nTest 3: Loading with target_resolution...")
try:
    video = VideoFileClip(str(video_path), target_resolution=(1080, 1920))
    print(f"  SUCCESS - Duration: {video.duration:.2f}s, FPS: {video.fps}, Size: {video.size}")
    video.close()
except Exception as e:
    print(f"  FAILED: {e}")

# Test 4: Try getting a single frame
print("\nTest 4: Trying to get first frame...")
try:
    video = VideoFileClip(str(video_path), audio=False)
    frame = video.get_frame(0)
    print(f"  SUCCESS - Frame shape: {frame.shape}")
    video.close()
except Exception as e:
    print(f"  FAILED: {e}")

# Test 5: Try with fps parameter
print("\nTest 5: Loading with explicit fps...")
try:
    video = VideoFileClip(str(video_path), fps_source='fps')
    print(f"  SUCCESS - Duration: {video.duration:.2f}s, FPS: {video.fps}, Size: {video.size}")
    video.close()
except Exception as e:
    print(f"  FAILED: {e}")
