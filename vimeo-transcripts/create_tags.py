import anthropic
import os
import openpyxl
import difflib
from dotenv import load_dotenv


def load_all_tags(csv_path):
    """Load all tags from CSV and return normalized + original versions"""
    with open(csv_path, 'r', encoding='utf-8') as f:
        tags = [line.strip() for line in f if line.strip()]

    # Create lookup: normalized -> original
    tag_lookup = {tag.lower().strip(): tag for tag in tags}
    return tag_lookup


def validate_and_match_tags(response_tags, tag_lookup):
    """Validate tags and find closest matches using fuzzy matching"""
    matched_tags = []
    logs = []

    for tag in response_tags:
        tag_normalized = tag.strip().lower()

        # Try exact match first
        if tag_normalized in tag_lookup:
            matched_tags.append(tag_lookup[tag_normalized])
            # logs.append(f"✓ Exact match: '{tag}' -> '{tag_lookup[tag_normalized]}'")
        else:
            # Fuzzy match
            all_tags = list(tag_lookup.keys())
            matches = difflib.get_close_matches(tag_normalized, all_tags, n=1, cutoff=0.95)

            if matches:
                matched_tag = tag_lookup[matches[0]]
                matched_tags.append(matched_tag)
                logs.append(f"⚠ Fuzzy match: '{tag}' -> '{matched_tag}' (similarity check)")
            else:
                logs.append(f"✗ No match found for: '{tag}' (skipped)")

    return matched_tags, logs


def read_csv_file(csv_path):
    """Read CSV file and return all tags as a formatted string"""
    with open(csv_path, 'r', encoding='utf-8') as f:
        tags = [line.strip() for line in f if line.strip()]

    csv_content = f"CSV File: {csv_path}\n"
    csv_content += f"Total available tags: {len(tags)}\n\n"
    csv_content += "Complete tag list (choose ONLY from these):\n"
    csv_content += ", ".join(tags)

    return csv_content

def query_claude_with_video_and_csv(
    query,
    csv_path,
    video_info,
    api_key=None
):
    """
    Send a query to Claude with CSV data and video information
    
    Args:
        query (str): The question/prompt to ask Claude
        csv_path (str): Path to the CSV file
        video_info (dict): Dictionary containing video metadata
        api_key (str): Anthropic API key (optional, will use env var if not provided)
    
    Returns:
        str: Claude's response
    """
    # Initialize the client
    if api_key is None:
        api_key = os.getenv('ANTHROPIC_API_KEY')
    
    client = anthropic.Anthropic(api_key=api_key)
    
    # Read CSV content
    csv_content = read_csv_file(csv_path)
    
    # Format video information
    video_content = "Video Information:\n"
    for key, value in video_info.items():
        video_content += f"- {key}: {value}\n"
    
    # Construct the full message
    full_message = f"""
{query}

{csv_content}

{video_content}
"""
    
    # Make the API request
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": full_message
            }
        ]
    )
    
    return message.content[0].text

# Example usage
if __name__ == "__main__":
    load_dotenv()


    excel_file = 'assets/Caravan English Videos List (1-7-2026) - Copy.xlsx'
    print("\nLoading Excel file...")
    wb = openpyxl.load_workbook(excel_file, read_only=False)

    # Find the English Video List sheet (case-insensitive)
    english_sheet = None
    for sheet_name in wb.sheetnames:
        if 'english video list' in sheet_name.lower():
            english_sheet = wb[sheet_name]
            print(f"Found sheet: '{sheet_name}'")
            break


    if not english_sheet:
        print("ERROR: Could not find 'English Video List' sheet in Excel file")
        exit(1)


    category_col_idx = 3
    video_name_col_idx = 4
    video_length_col_idx = 5
    teacher_col_idx = 5
    description_col_idx = 9
    transcript_col_idx = 21 # Column U is index 21
    first_tag_col_idx = 22 # Column V is index 22
    row_counter = 2

    MAX_ROWS = 2000  # Set to None to process all rows

    # Initialize counters
    successful = 0
    failed = 0
    skipped = 0

    # CSV file path
    csv_path = "assets/Tags.csv"

    # Load tag lookup once before the loop
    tag_lookup = load_all_tags(csv_path)
    print(f"Loaded {len(tag_lookup)} tags from CSV\n")

    while True:
        status = 0
        status_info = "default"

        if MAX_ROWS and row_counter >= MAX_ROWS:
            print(f"Reached {MAX_ROWS} rows limit (testing mode)")
            break

        category = english_sheet.cell(row=row_counter, column=category_col_idx).value
        video_name = english_sheet.cell(row=row_counter, column=video_name_col_idx).value
        video_length = english_sheet.cell(row=row_counter, column=video_length_col_idx).value
        teacher = english_sheet.cell(row=row_counter, column=teacher_col_idx).value
        description = english_sheet.cell(row=row_counter, column=description_col_idx).value
        transcripts = english_sheet.cell(row=row_counter, column=transcript_col_idx).value
        tag = english_sheet.cell(row=row_counter, column=first_tag_col_idx).value



        if not transcripts:
            print(f"\nSkipping row {row_counter}: no transcript available")
            skipped += 1
            row_counter += 1
            continue
        elif tag:
            print(f"\nSkipping row {row_counter}: tags already exist")
            skipped += 1
            row_counter += 1
            continue
        else:
            # Video information
            video_info = {
                "category": category,
                "video_name": video_name,
                "description": description,
                "transcripts": transcripts
            }
            
            # Query
            query = (
                "Analyze the video transcript and description to identify its PRIMARY themes and main focus areas. "
                "Pick the 10 most relevant unique tags from the CSV that represent CENTRAL themes of the video. "
                "You may provide less than 10 tags if the next most relevant tag is too unrelated to the content of the video. "
                "\n"
                "CRITICAL TAG SELECTION CRITERIA:\n"
                "1. Each tag must represent a MAIN focus or substantial theme in the video, not just a passing mention\n"
                "2. If a concept is only mentioned briefly or in passing (1-2 times), do NOT select it as a tag\n"
                "3. The video should spend meaningful time discussing or demonstrating the tagged concept\n"
                "4. Ask yourself: 'Is this tag a primary reason someone would watch this video?' If no, don't use it\n"
                "5. Prioritize tags that match the video's category and intended learning outcomes\n"
                "\n"
                "FORMATTING REQUIREMENTS:\n"
                "- Tags MUST be exclusively chosen from and EXACTLY as written in the provided CSV tag list\n"
                "- Copy each tag character-for-character from the CSV - do not create, modify, or paraphrase any tags\n"
                "- Double-check that every tag you select appears in the CSV list above\n"
                "- Tags should be unique and should not include any duplicates\n"
                "- Format: Provide tags separated by commas without spaces after commas (tag1,tag2,tag3)\n"
                "- Provide ONLY the tags in your response, no other text or formatting"
            ) \
            
            # Make the request
            try:
                response = query_claude_with_video_and_csv(
                    query=query,
                    csv_path=csv_path,
                    video_info=video_info
                )
                print(f"\n{row_counter}: {video_name}")
                print(f"Raw response: {response}")

                # Validate and match tags
                response_tags = response.strip().split(',')
                matched_tags, validation_logs = validate_and_match_tags(response_tags, tag_lookup)

                # Print validation logs
                for log in validation_logs:
                    print(log)

                # Write matched tags to Excel
                for index, tag in enumerate(matched_tags):
                    tag_cell = english_sheet.cell(row=row_counter, column=first_tag_col_idx + index)
                    tag_cell.value = tag

                print(f"✓ Wrote {len(matched_tags)} tags to Excel")
                wb.save(excel_file)
                successful += 1




            except Exception as e:
                print(f"Error: {e}")
                failed += 1

        row_counter += 1