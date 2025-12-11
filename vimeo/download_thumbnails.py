import csv
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
import time

def create_thumbnails_folder():
    """Create thumbnails folder if it doesn't exist"""
    if not os.path.exists('images/thumbnails'):
        os.makedirs('images/thumbnails')
        print("Created 'thumbnails' folder")

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

def main():
    csv_path = os.path.join('sheets', 'Sterling.csv')

    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return

    create_thumbnails_folder()

    print(f"\nReading URLs from: {csv_path}\n")

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        success_count = 0
        fail_count = 0

        for i, row in enumerate(reader, start=1):
            video_name = row.get('Topic', '').strip()
            url = row.get('URL', '').strip()
            content_format = row.get('Content Format', '').strip()

            if not url:
                print(f"{i}. Skipping row - no URL")
                continue

            if content_format.lower() != 'video' and content_format.lower() != 'audio':
                print(f"{i}. Skipping {video_name} - Content Format is '{content_format}'")
                continue

            print(f"{i}. Processing: {video_name}")
            print(f"  URL: {url}")

            # Get thumbnail URL from page
            thumbnail_url = get_thumbnail_url(url)

            if thumbnail_url:
                print(f"  Found thumbnail: {thumbnail_url}")
                if download_thumbnail(thumbnail_url, video_name, i):
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
