import csv
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_thumbnails_folder():
    """Create thumbnails folder if it doesn't exist"""
    if not os.path.exists('images/thumbnails'):
        os.makedirs('images/thumbnails')
        print("Created 'thumbnails' folder")

def create_videos_folder():
    """Create videos folder if it doesn't exist"""
    if not os.path.exists('videos'):
        os.makedirs('videos')
        print("Created 'videos' folder")

def get_thumbnail_url_from_vimeo(page_url):
    """Extract thumbnail URL from Vimeo API using video ID from vimeo.com URLs"""
    try:
        import re

        # Extract video ID from Vimeo URL
        # Pattern matches URLs like https://vimeo.com/1040132809 or https://vimeo.com/1040132809?share=copy
        match = re.search(r'vimeo\.com/(\d+)', page_url)

        if not match:
            print(f"  Could not extract video ID from URL: {page_url}")
            return None

        video_id = match.group(1)
        print(f"  Extracted video ID: {video_id}")


        # Call Vimeo API

        load_dotenv()

        # Get API key from environment variable
        api_key = os.getenv('VIMEO_API_KEY')
        bearer_token = os.getenv('BEARER_TOKEN')
        """Fetch texttracks for a video from Vimeo API"""

        url = f"https://api.vimeo.com/videos/{video_id}"

        headers = {
            'Authorization': 'Bearer ' + bearer_token,
            'Accept': 'application/vnd.vimeo.*+json;version=3.4',
            'X-API-Key': api_key
        }

        # Retry logic for rate limiting
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                time.sleep(15)
                break  # Success, exit retry loop
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429 and attempt < max_retries - 1:
                    print(f"  Rate limit hit (429), waiting 30 seconds before retry...")
                    time.sleep(30)
                    continue
                else:
                    raise  # Re-raise the exception if it's not 429 or we're out of retries

        # Parse JSON response
        video_data = response.json()
        # print(video_data)

        # Extract base_link from pictures
        if 'pictures' in video_data and video_data['pictures']:
            base_link = video_data['pictures'].get('base_link')

            if base_link:
                print(f"  Found thumbnail via Vimeo API")

                return base_link
            else:
                print(f"  No base_link found in pictures data")
                return None
        else:
            print(f"  No pictures data found in API response")
            return None

    except requests.exceptions.RequestException as e:
        print(f"  Error calling Vimeo API: {e}")
        return None
    except Exception as e:
        print(f"  Error processing Vimeo thumbnail: {e}")
        return None

def get_thumbnail_url(page_url):
    """Extract thumbnail URL from og:image meta tag"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(page_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        og_image = soup.find('meta', property='og:image')

        if og_image and og_image.get('content'):
            return og_image['content']
        else:
            print(f"  No og:image found for {page_url}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching page {page_url}: {e}")
        return None

def get_video_url(page_url):
    """Extract video download URL from page by finding VIDEO_ID"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(page_url, headers=headers, timeout=10)
        response.raise_for_status()

        # Search for VIDEO_ID in the HTML
        # Pattern: "VIDEO_ID":2454995
        import re
        match = re.search(r'"VIDEO_ID":(\d+)', response.text)

        if match:
            video_id = match.group(1)
            api_url = f"https://api.vhx.tv/videos/{video_id}/files"
            print(f"  Found VIDEO_ID: {video_id}")
            return api_url

        print(f"  No VIDEO_ID found for {page_url}")
        return None

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching page {page_url}: {e}")
        return None

def download_thumbnail(thumbnail_url, video_name, row_number):
    """Download thumbnail image to thumbnails folder"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(thumbnail_url, headers=headers, timeout=10)
        response.raise_for_status()

        # Get file extension from URL
        parsed_url = urlparse(thumbnail_url)
        path = unquote(parsed_url.path)
        ext = os.path.splitext(path)[1] or '.png'

        # Create safe filename from video name
        safe_name = "".join(c for c in video_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        filename = f"{(row_number + 1):03d}_{safe_name}{ext}"

        filepath = os.path.join('images','thumbnails', filename)

        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"   Downloaded: {filename}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"  Error downloading thumbnail {thumbnail_url}: {e}")
        return False

def download_video(api_url, video_name, row_number):
    """Download video file to videos folder using VHX API"""
    try:
        # Get API key from environment
        api_key = os.getenv('VIMEO_API_KEY')
        if not api_key:
            print(f"\n  Error: VIMEO_API_KEY not found in .env file")
            return False

        # Make API request to get video file info using Basic Auth
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        print(f"  Fetching video file info from API...")
        # Basic auth with api_key as username, empty password
        from requests.auth import HTTPBasicAuth
        api_response = requests.get(api_url, headers=headers, auth=HTTPBasicAuth(api_key, ''), timeout=30)
        api_response.raise_for_status()

        # Parse JSON response - it's a list of file objects
        files_data = api_response.json()

        # Extract the download URL from the source href
        # Find the highest quality MP4 file (1080p, 720p, etc.)
        download_url = None
        quality_order = ['1080p', '720p', '540p', '360p', '240p']

        # Filter for MP4 files only
        mp4_files = [f for f in files_data if f.get('format') == 'mp4' and f.get('method') == 'progressive']

        if mp4_files:
            # Sort by quality preference
            for quality in quality_order:
                for file in mp4_files:
                    if file.get('quality') == quality:
                        if '_links' in file and 'source' in file['_links']:
                            download_url = file['_links']['source']['href']
                            print(f"  Selected quality: {quality} ({file.get('size', {}).get('formatted', 'unknown size')})")
                            break
                if download_url:
                    break

        if not download_url:
            print(f"\n  Error: No MP4 download URL found in API response")
            return False

        print(f"  Found download URL")

        # Download the video file
        download_response = requests.get(download_url, headers=headers, auth=HTTPBasicAuth(api_key, ''), timeout=60, stream=True)
        download_response.raise_for_status()

        # Get file extension from URL or default to .mp4
        parsed_url = urlparse(download_url)
        path = unquote(parsed_url.path)
        ext = os.path.splitext(path)[1] or '.mp4'

        # Create safe filename from video name
        safe_name = "".join(c for c in video_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        filename = f"{safe_name}{ext}"

        filepath = os.path.join('videos', filename)

        # Download with progress indication
        total_size = int(download_response.headers.get('content-length', 0))
        downloaded = 0

        with open(filepath, 'wb') as f:
            for chunk in download_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r   Downloading: {percent:.1f}%", end='', flush=True)

        print(f"\r   Downloaded: {filename}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"\n  Error downloading video: {e}")
        return False
    except Exception as e:
        print(f"\n  Error processing video download: {e}")
        return False

def main():
    csv_path = os.path.join('sheets', 'Passport.csv')

    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return

    create_thumbnails_folder()
    create_videos_folder()

    print(f"\nReading URLs from: {csv_path}\n")

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        success_count = 0
        fail_count = 0
        

        for i, row in enumerate(reader, start=1):
            if i <= 5:
                continue

            video_name = row.get('Video Title', '').strip()
            url = row.get('URL', '').strip()
            # content_format = row.get('Content Format', '').strip()

            # if not video_name == "Meditation for Mental Focus Truike":
            #     continue

            if not url:
                print(f"{i}. Skipping row - no URL")
                continue

            # if content_format.lower() != 'video' and content_format.lower() != 'audio':
            #     print(f"{i}. Skipping {video_name} - Content Format is '{content_format}'")
            #     continue

            print(f"{i}. Processing: {video_name}")
            print(f"  URL: {url}")

            # Get thumbnail URL from page
            # Check if URL is a vimeo.com URL
            if 'vimeo.com' in url:
                print(f"  Detected Vimeo URL, using microdata extraction")
                thumbnail_url = get_thumbnail_url_from_vimeo(url)
            else:
                thumbnail_url = get_thumbnail_url(url)

            video_api_url = get_video_url(url)

            # Download thumbnail
            # if thumbnail_url:
            #     print(f"  Found thumbnail: {thumbnail_url}")
            #     if download_thumbnail(thumbnail_url, video_name, i):
            #         success_count += 1
            #     else:
            #         fail_count += 1
            # else:
            #     fail_count += 1

            # Download video
            if video_api_url:
                print(f"  Video API URL: {video_api_url}")
                if download_video(video_api_url, video_name, i):
                    success_count += 1
                else:
                    fail_count += 1
            else:
                fail_count += 1

            # Be polite and don't hammer the server
            time.sleep(1)
            print()

    print(f"\n{'='*60}")
    print(f"Download complete!")
    print(f"Successfully downloaded: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
