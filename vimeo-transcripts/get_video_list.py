import os
import json
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
import re
import operator

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    # Remove invalid characters for Windows filenames
    return re.sub(r'[<>:"/\\|?*]', '', filename)



# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
api_key = os.getenv('VIMEO_API_KEY')
bearer_token = os.getenv('BEARER_TOKEN')

if not api_key:
    raise ValueError("VIMEO_API_KEY not found in .env file")

# Fetch all videos with pagination
def fetch_all_videos(api_key):

    """Fetch all videos from the API with pagination"""
    all_videos = []

    url = 'https://api.vimeo.com/users/90373291/folders/27705491/videos'

    headers = {
        'Authorization': 'Bearer ' + bearer_token,
        'Accept': 'application/vnd.vimeo.*+json;version=3.4',
        'X-API-Key': api_key
    }

    page = 1
    while url:
        print(f"Fetching page {page}...")
        response = requests.get(url, headers=headers)

        print(f"Status Code: {response.status_code}")

        # Check for errors
        if response.status_code != 200:
            print(f"Error: {response.text}")
            break

        data = response.json()

        # Get videos from this page
        videos = data.get('data', [])
        all_videos.extend(videos)
        print(f"Retrieved {len(videos)} videos from page {page} (Total: {len(all_videos)})")


        # Check for next page
        paging = data.get('paging', {})
        if not paging.get('next'):
            print(f"\nCompleted! No more pages.")
            break
        url = 'https://api.vimeo.com/' + paging.get('next')
        page += 1

    # Save all videos to JSON file
    with open('humana_videos.json', 'w', encoding='utf-8') as f:
        json.dump({'data': all_videos, 'total': len(all_videos)}, f, indent=2, ensure_ascii=False)

    print(f"\nCompleted! Total videos fetched: {len(all_videos)}")
    return all_videos

# Fetch all videos
print("Starting to fetch all videos...")
if os.path.exists('humana_videos.json'):
    with open('humana_videos.json', 'r', encoding='utf-8') as f:
        all_videos = json.load(f)['data']
else:
    all_videos = fetch_all_videos(api_key)

# for video in all_videos:
#     print(f"{video['name']}: {video['embed']['html']}")


# Create a data structure similar to single-page response
# data = {
#     '_embedded': {'videos': all_videos},
#     # 'total': total_videos,
#     'count': len(all_videos)
# }

# # Create thumbnails folder if it doesn't exist
# thumbnails_folder = Path('thumbnails')
# thumbnails_folder.mkdir(exist_ok=True)

# # Filter for only videos with status "complete" and exclude (Highlight) videos
# if '_embedded' in data and 'videos' in data['_embedded']:
#     complete_videos = [
#         video for video in data['_embedded']['videos']
#         if video.get('status') == 'complete' 
#             and video.get('description') is not None and video.get('description') != "" 
#             and '(Highlight' not in video.get('title', '') and '9x16' not in video.get('title', '') 
            
#     ]

#     # Update the data with filtered videos
#     data['_embedded']['videos'] = complete_videos
#     data['count'] = len(complete_videos)

#     print(f"\nTotal videos fetched: {data.get('total', 0)}")
#     print(f"Complete videos filtered: {len(complete_videos)}")

    # Download thumbnails for complete videos
    # if complete_videos:
    #     print(f"\nDownloading thumbnails...")
    #     downloaded = 0
    #     for video in complete_videos:
    #         if download_thumbnail(video):
    #             downloaded += 1
    #     print(f"\nThumbnails downloaded: {downloaded}/{len(complete_videos)}")

# Write to CSV file
csv_filename = 'humana_embed_videos.csv'
with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
    csv_writer = csv.writer(csvfile)

    # Write header
    csv_writer.writerow(['Title', 'Embed'])

    # Write video data
    for video in all_videos:
        print(f"{video['name']}: {video['embed']['html']}")
        title = video['name']
        embed = video['embed']['html']
        # video_link = video.get('_links', {}).get('self', {}).get('href', '')
        # video_page_link = video.get('_links', {}).get('video_page', {}).get('href', '')
        # description = video.get('description', '') or ''  # Use empty string if None

        csv_writer.writerow([title, embed])

    print(f"\nCSV file saved: {csv_filename}")

with open(csv_filename, 'r', newline='', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    header = next(reader) # Read and store the header row
    data = sorted(reader, key=operator.itemgetter(1)) # Sort data by the specified column index

# Write the sorted data to a new file
with open(csv_filename, 'w', newline='', encoding='utf-8') as outfile:
    writer = csv.writer(outfile)
    writer.writerow(header) # Write the header row
    writer.writerows(data) # Write the sorted data rows

# Write to JSON file
# with open('sante_videos.json', 'w', encoding='utf-8') as f:
#     json.dump(data, f, indent=2, ensure_ascii=False)

print(f"JSON file saved: humana_videos.json")
