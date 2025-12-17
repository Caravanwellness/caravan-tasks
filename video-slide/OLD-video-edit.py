from pathlib import Path
from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip
import re
import numpy as np
import random

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def find_static_image_end(video_path, threshold=0.01, sample_rate=0.1):
    """
    Find the timestamp where a video stops being a static image.

    Args:
        video_path: Path to the video file
        threshold: Difference threshold (0-1, lower = more sensitive)
        sample_rate: How often to sample frames in seconds

    Returns:
        Float timestamp in seconds, or None if no change detected
    """
    try:
        video = VideoFileClip(str(video_path), audio=False)
    except Exception as e:
        print(f"  Error loading video in find_static_image_end: {e}")
        raise

    prev_frame = None
    current_time = 0

    while current_time < video.duration:
        frame = video.get_frame(current_time)

        if prev_frame is not None:
            # Calculate mean absolute difference between frames
            diff = np.mean(np.abs(frame.astype(float) - prev_frame.astype(float))) / 255.0

            if diff > threshold:
                save_transition_snapshots(True, prev_frame, frame, sanitize_filename(Path(video_path).stem))
                video.close()
                return current_time

        prev_frame = frame
        current_time += sample_rate

    print("  No change detected in video frames.")

    video.close()
    return 5  # Entire video is static

def find_static_image_start(video_path, threshold=0.01, sample_rate=0.1):
    """
    Find the timestamp where a static image begins at the end of a video.
    Scans backwards from the end to find when motion stops.

    Args:
        video_path: Path to the video file
        threshold: Difference threshold (0-1, lower = more sensitive)
        sample_rate: How often to sample frames in seconds

    Returns:
        Float timestamp in seconds where static image starts, or video duration if no static found
    """
    try:
        video = VideoFileClip(str(video_path), audio=False)
    except Exception as e:
        print(f"  Error loading video in find_static_image_start: {e}")
        raise

    # Start from the end and work backwards
    current_time = video.duration - sample_rate
    prev_frame = None
    static_start = video.duration

    while current_time > 0:
        frame = video.get_frame(current_time)

        if prev_frame is not None:
            # Calculate mean absolute difference between frames
            diff = np.mean(np.abs(frame.astype(float) - prev_frame.astype(float))) / 255.0

            if diff > threshold:
                static_start -= 0.1
                # Found motion - static image starts after this point
                save_transition_snapshots(False, frame, prev_frame, sanitize_filename(Path(video_path).stem))
                video.close()
                print(f"  Static image starts at: {video.duration - static_start:.2f}s before end")
                return static_start

        # Still in static region, update static_start
        static_start = current_time
        prev_frame = frame
        current_time -= sample_rate

    print("  Entire video appears to be static from beginning.")

    video.close()
    return 0  # Entire video is static

def save_transition_snapshots(start, before_frame, frame_end, video_name):
    """
    Find the transition point from motion to static image and save both frames.
    Saves the static image and a frame right before the transition.

    Args:
        video_path: Path to the video file
        output_folder: Path to folder where snapshots will be saved
        threshold: Difference threshold (0-1, lower = more sensitive)
        sample_rate: How often to sample frames in seconds

    Returns:
        Tuple of (static_image_path, before_transition_path, transition_timestamp)
    """

    # Create output folder if it doesn't exist
    output_folder = Path('assets/static_snapshots')
    output_folder.mkdir(exist_ok=True, parents=True)

    # Convert frame to PIL Image and save
    from PIL import Image
    if start:
        frame_start_static_path = output_folder / f"{video_name}_1.png"
        frame_start_static_img = Image.fromarray(before_frame)
        frame_start_static_img.save(str(frame_start_static_path))

        # Save the frame right before transition
        after_frame_static_path = output_folder / f"{video_name}_2.png"
        after_frame_static_img = Image.fromarray(frame_end)
        after_frame_static_img.save(str(after_frame_static_path))
    else:
        before_frame_static_path = output_folder / f"{video_name}_3.png"
        before_frame_static_img = Image.fromarray(before_frame)
        before_frame_static_img.save(str(before_frame_static_path))

        # Save the frame right before transition
        frame_end_static_path = output_folder / f"{video_name}_4.png"
        frame_end_static_img = Image.fromarray(frame_end)
        frame_end_static_img.save(str(frame_end_static_path))

def normalize_name(name):
    """Normalize a name by keeping only alphanumeric characters and converting to lowercase"""
    return re.sub(r'[^a-zA-Z0-9]', '', name).lower()

def find_matching_slide(video_name, slides_folder):
    """Find the corresponding slide image for a video, matching alphanumeric characters only"""
    # Remove extension from video name
    video_base = Path(video_name).stem
    video_normalized = normalize_name(video_base)

    # Common image extensions to check
    image_extensions = ['.jpeg', '.jpg', '.png', '.JPEG', '.JPG', '.PNG']

    # First try exact match
    for ext in image_extensions:
        slide_path = slides_folder / f"{video_base}{ext}"
        if slide_path.exists():
            return slide_path

    # If no exact match, try fuzzy matching
    for slide_file in slides_folder.iterdir():
        if slide_file.is_file() and slide_file.suffix in image_extensions:
            slide_normalized = normalize_name(slide_file.stem)
            if slide_normalized == video_normalized:
                return slide_file

    return None

def get_random_mantra(mantras_folder):
    """Get a random mantra image from the mantras folder"""
    if not mantras_folder.exists():
        return None

    # Common image extensions to check
    image_extensions = ['.jpeg', '.jpg', '.png', '.JPEG', '.JPG', '.PNG']

    # Get all image files in the mantras folder
    mantra_images = [f for f in mantras_folder.iterdir()
                     if f.is_file() and f.suffix in image_extensions]

    if not mantra_images:
        return None

    return random.choice(mantra_images)

def replace_intro_and_outro(video_path, slide_path, mantra_path, output_path, intro_duration, outro_timestamp):
    """Replace the first portion with a slide and last 5 seconds with a mantra image

    Args:
        video_path: Path to the input video
        slide_path: Path to the slide image
        mantra_path: Path to the mantra image for outro
        output_path: Path for the output video
        intro_duration: Duration of intro slide in seconds
        outro_duration: Duration of outro mantra in seconds (default 5)
    """


    print(f"Processing: {video_path.name}")

    # Load the video
    try:
        video = VideoFileClip(str(video_path))
    except Exception as e:
        print(f"  Error loading video: {e}")
        raise

    outro_duration = video.duration - outro_timestamp

    # Load the slide image for intro
    intro_slide = ImageClip(str(slide_path))
    intro_slide = intro_slide.set_duration(intro_duration)
    intro_slide = intro_slide.resize(video.size)

    # If video has audio, extract audio for the intro slide portion
    if video.audio is not None:
        intro_audio = video.audio.subclip(0, min(intro_duration, video.duration))
        intro_slide = intro_slide.set_audio(intro_audio)

    # Calculate the middle section
    if video.duration > intro_duration + outro_duration:
        # Get middle video section (between intro and outro)
        middle_video = video.subclip(intro_duration, video.duration - outro_duration)

        # Load the mantra image for outro
        outro_slide = ImageClip(str(mantra_path))
        outro_slide = outro_slide.set_duration(outro_duration)
        outro_slide = outro_slide.resize(video.size)

        # Extract audio for the outro portion
        if video.audio is not None:
            outro_audio = video.audio.subclip(video.duration - outro_duration, video.duration)
            outro_slide = outro_slide.set_audio(outro_audio)

        # Concatenate all three parts
        final_video = concatenate_videoclips([intro_slide, middle_video, outro_slide])
    elif video.duration > intro_duration:
        # Video is too short for outro, just replace intro
        remaining_video = video.subclip(intro_duration)
        final_video = concatenate_videoclips([intro_slide, remaining_video])
    else:
        # Video is very short, just use the intro slide
        final_video = intro_slide

    # Write the output with optimized settings
    final_video.write_videofile(
        str(output_path),
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        fps=video.fps,
        preset='ultrafast',  # Much faster encoding (ultrafast, superfast, veryfast, faster, fast, medium)
        threads=6,           # Use 6 out of 8 CPU cores (leaves 2 for system)
        # logger=None          # Disable verbose logging for cleaner output
    )

    # Close clips to free resources
    video.close()
    intro_slide.close()
    final_video.close()

    print(f"Completed: {output_path.name}\n")

def main():
    # Define folders
    videos_folder = Path('assets/videos')
    slides_folder = Path('assets/slides')
    mantras_folder = Path('assets/mantras')
    output_folder = Path('assets/output')

    # Create output folder if it doesn't exist
    output_folder.mkdir(exist_ok=True)

    # Check if required folders exist
    if not videos_folder.exists():
        print(f"Error: 'videos' folder not found")
        return

    if not slides_folder.exists():
        print(f"Error: 'slides' folder not found")
        return

    if not mantras_folder.exists():
        print(f"Warning: 'mantras' folder not found - outro will not be added")

    # Get all video files
    video_extensions = ['.mp4', '.mov', '.avi', '.MP4', '.MOV', '.AVI']
    video_files = [f for f in videos_folder.iterdir()
                   if f.is_file() and f.suffix in video_extensions]

    if not video_files:
        print("No video files found in 'videos' folder")
        return

    print(f"Found {len(video_files)} video(s) to process\n")

    # Process each video
    processed = 0
    skipped = 0

    for video_file in video_files:
        if processed >= 65:
            # print(f"{video_file.name} - skipping")
            skipped += 1
            continue
        # if video_file.name != "Meditation_for_Mental_Focus_Truike.mp4":
        #     # print(f"{video_file.name} - skipping")
        #     skipped += 1
        #     continue
        # Find matching slide
        slide_path = find_matching_slide(video_file.name, slides_folder)
        print(f"{video_file.name} - slide: {slide_path.name if slide_path else 'None'}")

        if slide_path is None:
            print(f"Warning: No matching slide found for '{video_file.name}' - skipping")
            skipped += 1
            continue

        # Get a random mantra image
        mantra_path = get_random_mantra(mantras_folder)

        if mantra_path is None:
            print(f"Warning: No mantra images found for '{video_file.name}' - skipping")
            skipped += 1
            continue

        # Create output path
        output_path = output_folder / video_file.name

        try:
            duration = find_static_image_end(video_file, threshold=0.01, sample_rate=0.1)
            end_duration = find_static_image_start(video_file, threshold=0.01, sample_rate=0.1)
            print(f"  Detected static image duration for {video_file.name}: {duration:.2f}s, end at {end_duration:.2f}s")

            print(f"  Using mantra: {mantra_path.name}")
            # replace_intro_and_outro(video_file, slide_path, mantra_path, output_path, duration, end_duration)
            processed += 1
        except Exception as e:
            print(f"Error processing {video_file.name}: {str(e)}\n")
            skipped += 1

    print(f"\n{'='*50}")
    print(f"Processing complete!")
    print(f"Successfully processed: {processed}")
    print(f"Skipped: {skipped}")
    print(f"Output saved to: {output_folder.absolute()}")

if __name__ == "__main__":
    main()
