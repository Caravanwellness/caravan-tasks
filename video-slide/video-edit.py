from pathlib import Path
from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip
import re

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def find_matching_slide(video_name, slides_folder):
    """Find the corresponding slide image for a video"""
    # Remove extension from video name
    video_base = Path(video_name).stem

    # Common image extensions to check
    image_extensions = ['.jpeg', '.jpg', '.png', '.JPEG', '.JPG', '.PNG']

    for ext in image_extensions:
        slide_path = slides_folder / f"{video_base}{ext}"
        if slide_path.exists():
            return slide_path

    return None

def replace_first_5_seconds(video_path, slide_path, output_path, duration=5):
    """Replace the first 5 seconds of a video with a static image"""

    print(f"Processing: {video_path.name}")

    # Load the video
    video = VideoFileClip(str(video_path))

    # Load the slide image
    slide = ImageClip(str(slide_path))

    # Set the slide duration to 5 seconds and match video size
    slide = slide.set_duration(duration)
    slide = slide.resize(video.size)

    # If video has audio, extract audio for the slide portion
    if video.audio is not None:
        slide_audio = video.audio.subclip(0, min(duration, video.duration))
        slide = slide.set_audio(slide_audio)

    # If video is longer than 5 seconds, get the rest of the video
    if video.duration > duration:
        remaining_video = video.subclip(duration)
        # Concatenate slide and remaining video
        final_video = concatenate_videoclips([slide, remaining_video])
    else:
        # If video is 5 seconds or less, just use the slide
        final_video = slide

    # Write the output
    final_video.write_videofile(
        str(output_path),
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        fps=video.fps
    )

    # Close clips to free resources
    video.close()
    slide.close()
    final_video.close()

    print(f"Completed: {output_path.name}\n")

def main():
    # Define folders
    videos_folder = Path('assets/videos')
    slides_folder = Path('assets/slides')
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
        # Find matching slide
        slide_path = find_matching_slide(video_file.name, slides_folder)

        if slide_path is None:
            print(f"Warning: No matching slide found for '{video_file.name}' - skipping")
            skipped += 1
            continue

        # Create output path
        output_path = output_folder / video_file.name

        try:
            replace_first_5_seconds(video_file, slide_path, output_path)
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
