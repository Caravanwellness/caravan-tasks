import os
import requests
from urllib.parse import urlparse, unquote
import re
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv


load_dotenv()

def get_thumbnail_url_from_vimeo(page_url):
    """Extract thumbnail URL from Vimeo API using video ID from vimeo.com URLs"""
    try:

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


def download_thumbnail(folder_path, thumbnail_url, video_name, row_number):
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

        filepath = os.path.join(folder_path, filename)

        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"   Downloaded: {filename}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"  Error downloading thumbnail {thumbnail_url}: {e}")
        return False
    
