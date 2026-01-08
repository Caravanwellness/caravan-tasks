import csv
import pandas as pd
from download_texttracks import get_video_id_from_uri, fetch_texttracks, select_texttrack, sanitize_filename, get_vtt, parse_vtt_to_text 

def main():
    df = pd.read_csv('assets/Caravan English Videos List (1-7-2026).csv')

    for index, row in df.iterrows():
        # 'row' is a Pandas Series object
        print(f'Name: {row["name"]}, Age: {row["age"]}')

    with open('assets/Caravan English Videos List (1-7-2026).csv', mode='rw', newline='', encoding='utf-8') as file:
        csv_reader = csv.reader(file, delimiter=',')
        # Optional: Skip the header row if present
        # next(csv_reader, None) 
        for i, row in csv_reader:
            if i > 5:
                continue

            # Each 'row' is a list, e.g., ['1', 'Alice', '20', '62', '120.6']
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

            # Download the VTT file
            link = selected_track.get("link")
            language = selected_track.get("language")

            if not link:
                print(f"  No download link available")
                failed += 1
                continue


            print(f"  Downloading texttrack (language: {language})")

            transcript = parse_vtt_to_text(get_vtt(link))

            print(row)
            # Access individual columns by index (e.g., row[1] for 'name')
            # name = row[1] 