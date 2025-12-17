import json
import requests
from pathlib import Path
import time
import re
from dotenv import load_dotenv
import os

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def parse_vtt_to_text(vtt_content):
    """
    Parse VTT content and extract plain text transcript.

    Args:
        vtt_content: String content of VTT file

    Returns:
        String of clean transcript text
    """
    lines = vtt_content.split('\n')
    transcript_lines = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip WEBVTT header
        if line.startswith('WEBVTT'):
            i += 1
            continue

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Skip cue numbers (just digits)
        if line.isdigit():
            i += 1
            continue

        # Skip timestamp lines (contains -->)
        if '-->' in line:
            i += 1
            continue

        # This should be actual caption text
        # Clean up any VTT formatting tags like <v Name>
        text = re.sub(r'<[^>]+>', '', line)
        text = text.strip()

        if text:
            transcript_lines.append(text)

        i += 1

    # Join all lines with spaces
    return ' '.join(transcript_lines)

def convert_vtt_to_transcript(vtt_path, output_path):
    """
    Convert a VTT file to a clean transcript text file.

    Args:
        vtt_path: Path to VTT file
        output_path: Path for output transcript text file

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(vtt_path, 'r', encoding='utf-8') as f:
            vtt_content = f.read()

        transcript_text = parse_vtt_to_text(vtt_content)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transcript_text)

        return True
    except Exception as e:
        print(f"  Error converting VTT to transcript: {e}")
        return False

def convert_all_vtts_to_transcripts(transcripts_folder):
    """
    Convert all VTT files in the transcripts folder to .txt transcript files.

    Args:
        transcripts_folder: Path to folder containing VTT files

    Returns:
        Tuple of (successful_count, failed_count)
    """
    transcripts_folder = Path(transcripts_folder)

    if not transcripts_folder.exists():
        print(f"Error: Transcripts folder not found: {transcripts_folder}")
        return (0, 0)

    vtt_files = list(transcripts_folder.glob('*.vtt'))

    if not vtt_files:
        print("No VTT files found in transcripts folder")
        return (0, 0)

    print(f"Found {len(vtt_files)} VTT files to convert\n")

    successful = 0
    failed = 0

    for vtt_file in vtt_files:
        output_path = vtt_file.with_suffix('.txt')

        # Skip if transcript already exists
        if output_path.exists():
            print(f"Skipping {vtt_file.name} - transcript already exists")
            continue

        print(f"Converting: {vtt_file.name}")

        if convert_vtt_to_transcript(vtt_file, output_path):
            print(f"  Saved to: {output_path.name}")
            successful += 1
        else:
            failed += 1

    print(f"\n{'='*50}")
    print(f"Conversion complete!")
    print(f"Successfully converted: {successful}")
    print(f"Failed: {failed}")

    return (successful, failed)

def get_video_id_from_uri(uri):
    """Extract video ID from URI like '/videos/1071167545'"""
    return uri.split('/')[-1]

def fetch_texttracks(video_id):
    load_dotenv()

    # Get API key from environment variable
    api_key = os.getenv('VIMEO_API_KEY')
    bearer_token = os.getenv('BEARER_TOKEN')
    """Fetch texttracks for a video from Vimeo API"""

    url = f"https://api.vimeo.com/videos/{video_id}/texttracks"

    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Accept': 'application/vnd.vimeo.*+json;version=3.4',
        'X-API-Key': api_key
    }

    all_texttracks = []
    page = 1

    while True:
        params = {"page": page, "per_page": 100}
        response = requests.get(url, headers=headers, params=params)
        time.sleep(5)
        
        if response.status_code != 200:
            print(f"  Error fetching texttracks: {response.status_code}")
            return None

        data = response.json()
        all_texttracks.extend(data.get("data", []))

        # Check if there are more pages
        paging = data.get("paging", {})
        if not paging.get("next"):
            break

        page += 1

    return all_texttracks

def select_texttrack(texttracks):
    """
    Select the appropriate texttrack based on priority:
    1. language='en' and active=True
    2. language='en-x-autogen' (fallback)
    """
    if not texttracks:
        return None

    # First priority: active English texttracks
    for track in texttracks:
        if track.get("language") == "en" and track.get("active") == True:
            return '', track

    # Fallback: auto-generated English
    for track in texttracks:
        if track.get("language") == "en-x-autogen":
            return "(autogenerated)", track

    return None

def download_vtt(link, output_path):
    """Download VTT file from the given link"""
    response = requests.get(link)


    if response.status_code != 200:
        print(f"  Error downloading VTT: {response.status_code}")
        return False

    with open(output_path, 'wb') as f:
        f.write(response.content)


    return True

def main():
    # Load videos.json
    videos_json_path = Path('videos.json')

    if not videos_json_path.exists():
        print("Error: videos.json not found")
        return

    with open(videos_json_path, 'r', encoding='utf-8') as f:
        videos_data = json.load(f)

    videos = videos_data.get("data", [])

    if not videos:
        print("No videos found in videos.json")
        return

    # Create transcripts folder
    texttracks_folder = Path('texttracks')
    texttracks_folder.mkdir(exist_ok=True)
    transcripts_folder = Path('transcripts')
    transcripts_folder.mkdir(exist_ok=True)


    print(f"Found {len(videos)} videos to process\n")

    successful = 0
    failed = 0
    skipped = 0

    for i, video in enumerate(videos, 1):

        # if i >= 4:
        #     continue

        video_uri = video.get("uri")
        video_name = video.get("name", "Unknown")

        if not video_uri:
            print(f"[{i}/{len(videos)}] Skipping video without URI")
            skipped += 1
            continue

        video_id = get_video_id_from_uri(video_uri)
        print(f"[{i}/{len(videos)}] Processing: {video_name} (ID: {video_id})")

    

        # Fetch texttracks
        texttracks = fetch_texttracks(video_id)

        if texttracks is None:
            print(f"  Failed to fetch texttracks")
            failed += 1
            continue

        if not texttracks:
            print(f"  No texttracks available")
            failed += 1
            continue

        # Select appropriate texttrack
        autogen, selected_track = select_texttrack(texttracks)

        # Check if transcript already exists
        safe_name = sanitize_filename(video_name)
        output_path = texttracks_folder / f"{safe_name}{autogen}.vtt"

        if output_path.exists():
            print(f"  Transcript already exists, skipping")
            skipped += 1
            continue

        if not selected_track:
            print(f"  No suitable texttrack found")
            failed += 1
            continue

        # Download the VTT file
        link = selected_track.get("link")
        language = selected_track.get("language")

        if not link:
            print(f"  No download link available")
            failed += 1
            continue


        print(f"  Downloading texttrack (language: {language})")

        if download_vtt(link, output_path):
            print(f"  Saved VTT to: {output_path.name}")

            # Automatically convert to text transcript
            txt_output_path = transcripts_folder / f"{safe_name}.txt"
            if convert_vtt_to_transcript(output_path, txt_output_path):
                print(f"  Converted to text: {txt_output_path.name}")

            successful += 1
        else:
            print(f"  Failed to download")
            failed += 1

        # Rate limiting - be nice to the API
        

    print(f"\n{'='*50}")
    print(f"Processing complete!")
    print(f"Successfully downloaded: {successful}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print(f"Transcripts saved to: {transcripts_folder.absolute()}")

if __name__ == "__main__":
    main()
