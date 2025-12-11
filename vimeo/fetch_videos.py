import os
import json
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
import re

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    # Remove invalid characters for Windows filenames
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def download_thumbnail(video):
    """Download thumbnail for a video"""
    video_id = video.get('id')
    video_title = video.get('title', 'untitled')
    thumbnail_url = video.get('thumbnail', {}).get('source')

    if not thumbnail_url or 'default-medium.png' in thumbnail_url:
        print(f"  Skipping {video_title} (ID: {video_id}) - no custom thumbnail")
        return False

    # Create filename: "video_title - video_id.jpg"
    safe_title = sanitize_filename(video_title)
    filename = f"{safe_title} - {video_id}.jpg"
    filepath = thumbnails_folder / filename

    try:
        # Download the thumbnail
        img_response = requests.get(thumbnail_url, timeout=10)
        img_response.raise_for_status()

        # Save to file
        with open(filepath, 'wb') as f:
            f.write(img_response.content)

        print(f"  ✓ Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to download {video_title} (ID: {video_id}): {e}")
        return False


# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
api_key = os.getenv('VIMEO_API_KEY')

if not api_key:
    raise ValueError("VIMEO_API_KEY not found in .env file")

# Fetch all videos with pagination
def fetch_all_videos(api_key):
    """Fetch all videos from the API with pagination"""
    all_videos = []
    url = "https://api.vhx.tv/videos"
    page = 1
    per_page = 150

    while True:
        print(f"\nFetching page {page}...")
        query_params = {
            'per_page': per_page,
            'page': page
        }

        response = requests.get(url, auth=(api_key, ''), params=query_params)

        print(f"Status Code: {response.status_code}")

        # Check for errors
        if response.status_code != 200:
            print(f"Error: {response.text}")
            break

        data = response.json()

        # Get videos from this page
        if '_embedded' in data and 'videos' in data['_embedded']:
            videos = data['_embedded']['videos']
            all_videos.extend(videos)
            print(f"Retrieved {len(videos)} videos (Total so far: {len(all_videos)})")

            # Check if there are more pages
            next_link = data.get('_links', {}).get('next', {}).get('href')
            if not next_link:
                print(f"\nCompleted! No more pages.")
                break

            page += 1
            # break
        else:
            break

    return all_videos, data.get('total', 0)

# Fetch all videos
print("Starting to fetch all videos...")
all_videos, total_videos = fetch_all_videos(api_key)



# Filter for only videos with status "complete" and exclude (Highlight) videos
if '_embedded' in data and 'videos' in data['_embedded']:
    complete_videos = [
        video for video in data['_embedded']['videos']
        if video.get('status') == 'complete' 
            and video.get('description') is not None and video.get('description') != "" 
            and '(Highlight' not in video.get('title', '') and '9x16' not in video.get('title', '') 
            
    ]

    # Update the data with filtered videos
    data['_embedded']['videos'] = complete_videos
    data['count'] = len(complete_videos)

    print(f"\nTotal videos fetched: {data.get('total', 0)}")
    print(f"Complete videos filtered: {len(complete_videos)}")

    # Download thumbnails for complete videos
    # if complete_videos:
    #     print(f"\nDownloading thumbnails...")
    #     downloaded = 0
    #     for video in complete_videos:
    #         if download_thumbnail(video):
    #             downloaded += 1
    #     print(f"\nThumbnails downloaded: {downloaded}/{len(complete_videos)}")

# Write to CSV file
csv_filename = 'sheets/videos.csv'
if '_embedded' in data and 'videos' in data['_embedded']:
    with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        csv_writer = csv.writer(csvfile)

        # Write header
        csv_writer.writerow(['Title', 'Description', 'Video Link', 'Video Page Link'])

        # Write video data
        for video in data['_embedded']['videos']:
            title = video.get('title', '')
            video_link = video.get('_links', {}).get('self', {}).get('href', '')
            video_page_link = video.get('_links', {}).get('video_page', {}).get('href', '')
            description = video.get('description', '') or ''  # Use empty string if None

            csv_writer.writerow([title, description, video_link, video_page_link])

    print(f"\nCSV file saved: {csv_filename}")

# Write to JSON file
with open('sheets/videos.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"JSON file saved: videos.json")
