import re
import requests
import os

def get_vimeo_url(page_url):
    """Check if URL is a Vimeo URL"""
    match = re.search(r'vimeo\.com/(\d+)', page_url)

    if not match:
        print(f"  Could not extract video ID from URL: {page_url}")
        return None

    video_id = match.group(1)
    print(f"  Extracted video ID: {video_id}")

def get_video_url_ott(page_url):
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
            api_url = f"https://api.vhx.tv/videos/{video_id}"
            print(f"  Found VIDEO_ID: {video_id}")
            return api_url

        print(f"  No VIDEO_ID found for {page_url}")
        return None

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching page {page_url}: {e}")
        return None


def request_vimeo_ott_api(api_url):
    """Request Vimeo OTT API to get video details including download links"""
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

        return api_response.json()


    except requests.exceptions.RequestException as e:
        print(f"\n  Error calling Vimeo OTT API: {e}")
        return None