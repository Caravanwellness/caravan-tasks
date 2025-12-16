import csv
import re

# First, let's create a language mapping dictionary from the languages.txt file
lang_mapping = {}
with open('files/languages.txt', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and '(' in line and ')' in line:
            # Extract language name and code
            match = re.match(r'(.+?)\s*\(([^)]+)\)$', line)
            if match:
                lang_name = match.group(1).strip()
                lang_code = match.group(2).strip()
                lang_mapping[lang_code] = lang_name

# print(lang_mapping)

print(f"Loaded {len(lang_mapping)} language mappings")
print("Sample mappings:", list(lang_mapping.items())[:5])

# Now process the CSV
rows = []
with open('files/Subtitle.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    rows.append(header)
    
    for i, row in enumerate(reader, start=2):  # start=2 because we skipped header (line 1)
        if i <= 149:
            # Keep rows 1-149 as they are
            rows.append(row)
        else:
            # Process rows after 149
            video_id = row[0]
            language = row[1]
            link = row[2]
            
            # Extract video_id and language code from the filename
            if not video_id and not language and link:
                # Parse filename like "1129940028_bn.vtt" or "1129940028_bn.srt"
                filename = link
                match = re.match(r'(\d+)_([^.]+)\.(vtt|srt)', filename)
                if match:
                    extracted_video_id = match.group(1)
                    lang_code = match.group(2)
                    file_ext = match.group(3)

                    # Map language code to full language name
                    language_name = lang_mapping.get(lang_code, lang_code)

                    # Create new link with URL prefix
                    new_link = f"https://articles.caravanwellness.com/content/subtitles/{extracted_video_id}_{lang_code}.{file_ext}"
                    
                    rows.append([extracted_video_id, language_name, new_link])
                else:
                    # If pattern doesn't match, keep as is
                    rows.append(row)
            else:
                # If already has data, keep as is
                rows.append(row)

print(f"Processed {len(rows)} total rows")

# Write to output file
with open('files/Subtitle_updated.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(rows)

print("CSV file updated successfully!")

# Show a sample of the updated rows
print("\nSample of updated rows (rows 148-155):")
for i in range(148, min(155, len(rows))):
    print(f"Row {i}: {rows[i]}")