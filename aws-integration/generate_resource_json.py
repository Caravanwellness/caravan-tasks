from pathlib import Path
import csv
import json
import uuid
import os
import re
import shutil
import unicodedata
from datetime import datetime, timezone



def generate_uuid():
    """Generate a 32-character UUID (without hyphens)."""
    return uuid.uuid4().hex


def map_format_to_media_type(format_value):
    """Map CSV format to media_type."""
    format_lower = format_value.lower().strip()
    if format_lower == "article":
        return "article"
    elif format_lower == "infographic":
        return "infographic"
    else:
        return format_lower


def parse_tags(tags_string):
    """Parse comma-separated tags into a list."""
    if not tags_string:
        return []
    return [tag.strip() for tag in tags_string.split(",") if tag.strip()]


def create_resource_json(row, resource_id, thumbnail_folder):
    """Create the JSON structure for a single resource."""
    media_type = map_format_to_media_type(row.get("Format", ""))

    # Determine content URL based on media type
    if media_type == "article":
        content_url = f"https://articles.caravanwellness.com/content/articles/{resource_id}.html"
    elif media_type == "infographic":
        content_url = f"https://articles.caravanwellness.com/content/infographics/{resource_id}.pdf"
    else:
        content_url = f"https://articles.caravanwellness.com/content/{media_type}s/{resource_id}"

    # Generate thumbnail URL from topic name
    topic = row.get("Topic", "").strip()
    found_thumbnail_name = find_matching_resource(topic, thumbnail_folder) 

    print(f"\nThumbnail found for topic '{topic}': {found_thumbnail_name}")

    thumbnail_name = found_thumbnail_name.name if found_thumbnail_name else topic.replace(" ", "-") + ".png"
    thumbnail_url = f"https://articles.caravanwellness.com/content/assets/{thumbnail_name}"


    resource_data = {
        "data": [
            {
                "id": resource_id,
                "name": topic,
                "description": row.get("Decription", ""),  # Note: CSV has typo "Decription"
                "language": "en",
                "media_type": media_type,
                "thumbnail": thumbnail_url,
                "translations": [],
                "content": content_url,
                "category": row.get("Category", "").lower(),
                "tags": parse_tags(row.get("Tags", "")),
                "audience": {
                    "age": row.get("Age", "18-65"),
                    "gender": row.get("Gender", "all").lower(),
                    "region": row.get("Region", "worldwide").lower()
                },
                "length": row.get("Length (Reading Time)", ""),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        ],
        # "status": 200
    }

    return resource_data


def find_matching_resource(topic, resources_folder):
    """Find a resource file matching the topic name."""
    resources_path = Path(resources_folder)
    topic_normalized = normalize_name(topic)

    # Common resource extensions
    resource_extensions = ['.pdf', '.html', '.PDF', '.HTML', '.png', '.PNG', '.jpg', '.jpeg', '.JPG', '.JPEG']

    # First try exact match with topic name
    # topic_filename = topic.replace(" ", "-")
    # for ext in resource_extensions:
    #     resource_path = resources_path / f"{topic_filename}{ext}"
    #     if resource_path.exists():
    #         return resource_path

    # # Try exact match without replacing spaces
    # for ext in resource_extensions:
    #     resource_path = resources_path / f"{topic}{ext}"
    #     if resource_path.exists():
    #         return resource_path

    # If no exact match, try fuzzy matching
    for resource_file in resources_path.iterdir():
        if resource_file.is_file() and resource_file.suffix in resource_extensions:
            resource_normalized = normalize_name(resource_file.stem)
            if resource_normalized == topic_normalized:
                return resource_file

    return None


def process_csv(csv_path, output_folder, resources_folder, thumbnail_folder):
    """Process CSV file and generate individual JSON files."""
    json_output = Path(output_folder) / "json"
    resources_output = Path(output_folder) / "resources"
    os.makedirs(json_output, exist_ok=True)
    os.makedirs(resources_output, exist_ok=True)

    all_resources = []  # Collect all resource data for index.json

    with open(csv_path, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        created_files = []
        for row in reader:
            # Skip empty rows
            if not row.get("Topic"):
                continue

            resource_id = generate_uuid()
            resource_json = create_resource_json(row, resource_id, thumbnail_folder)
            resource_json["status"] = 200

            # Write to individual JSON file
            json_path = json_output / f"{resource_id}.json"
            with open(json_path, "w", encoding="utf-8") as jsonfile:
                json.dump(resource_json, jsonfile, indent=2, ensure_ascii=False)

            # Add to all_resources list (just the data object, not the wrapper)
            all_resources.append(resource_json["data"][0])

            # Find and copy the matching resource file
            topic = row.get("Topic", "").strip()
            source_resource = find_matching_resource(topic, resources_folder)

            if source_resource:
                # Copy with new UUID name, preserving extension
                new_resource_path = resources_output / f"{resource_id}{source_resource.suffix}"
                shutil.copy2(source_resource, new_resource_path)
                print(f"Created: {json_path.name} + {new_resource_path.name} - {topic}")
            else:
                print(f"Created: {json_path.name} (no resource found) - {topic}")

            created_files.append((json_path, topic))

    # Write index.json with all resources
    index_path = json_output / "index.json"
    index_json = {
        "data": all_resources,
        "status": 200
    }
    with open(index_path, "w", encoding="utf-8") as jsonfile:
        json.dump(index_json, jsonfile, indent=2, ensure_ascii=False)
    print(f"\nCreated: {index_path.name} (index with {len(all_resources)} resources)")

    return created_files

def normalize_name(name):
    """Normalize a name by keeping only alphanumeric characters and converting to lowercase"""
    name = unicodedata.normalize('NFC', name)
    return ''.join(c for c in name if c.isalnum()).casefold()



def main():
    client = "pager"
    csv_path = f"assets/{client}/info.csv"
    resources_folder = f"assets/{client}/pre-json/"
    output_folder = f"assets/{client}/output/"
    thumbnail_folder = f"assets/{client}/thumbnails/"

    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        return 1

    if not os.path.exists(resources_folder):
        print(f"Error: Resources folder not found: {resources_folder}")
        return 1

    created_files = process_csv(csv_path, output_folder, resources_folder, thumbnail_folder)
    print(f"\nCreated {len(created_files)} JSON files in {output_folder}")

    return 0


if __name__ == "__main__":
    exit(main())
