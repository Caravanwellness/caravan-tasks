import json

def save_progress(progress_file, row_number, completed_rows):
    """Save progress to JSON file"""
    progress = {
        "last_processed_row": row_number,
        "completed_rows": completed_rows,
        "last_update": datetime.now().isoformat()
    }
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)


def save_progress(progress_file, row_number, completed_rows):
    """Save progress to JSON file"""
    video_data = {
        "data" : {
            "id": "a4c91d7ef20342b89e351e7c9dbb5a1c",
            "name": "How To Incorporate Short Walks Into Your Day",
            "description": "Short, frequent walks can boost energy, improve circulation, support mental health, and help maintain mobility",
            "language": "en",
            "media_type": "infographic",
            "thumbnail": "https://articles.caravanwellness.com/content/assets/How-To-Incorporate-Short-Walks.png",
            "content": "https://articles.caravanwellness.com/content/infographics/a4c91d7ef20342b89e351e7c9dbb5a1c.pdf",
            "category": "physical health",
            "tags": [
                "walking",
                "physical activity",
                "movement",
                "walking",
                "energy boost",
                "heart health",
                "exercise tips",
                "workplace wellness",
                "mobility support",
                "healthy habits"
            ],
            "audience": {
                "age": "18-65",
                "gender": "all",
                "region": "worldwide"
            },
            "length": "1-min read"
        },
        "status": 200
    }
    with open(progress_file, 'w') as f:
        json.dump(video_data, f, indent=2)