import os
import requests
from urllib.parse import urlparse, unquote
from requests.auth import HTTPBasicAuth
from request import request_vimeo_ott_api

def download_video(folder_path, api_url, video_name, row_number):
    """Download video file to videos folder using VHX API"""
    try:
        # Get API key from environment
        api_key = os.getenv('VIMEO_API_KEY')
        # if not api_key:
        #     print(f"\n  Error: VIMEO_API_KEY not found in .env file")
        #     return False

        # # Make API request to get video file info using Basic Auth
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # print(f"  Fetching video file info from API...")
        # # Basic auth with api_key as username, empty password
        # from requests.auth import HTTPBasicAuth
        # api_response = requests.get(api_url, headers=headers, auth=HTTPBasicAuth(api_key, ''), timeout=30)
        # api_response.raise_for_status()

        # Parse JSON response - it's a list of file objects
        files_data = request_vimeo_ott_api(api_url + "/files")

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

        filepath = os.path.join(folder_path, filename)

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
