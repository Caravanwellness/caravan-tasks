"""
Standalone script to convert VTT texttrack files to plain text transcripts.
"""

from pathlib import Path
import re

def parse_vtt_to_text(vtt_content):
    """
    Parse VTT content and extract plain text transcript.

    Args:
        vtt_content: String content of VTT file

    Returns:
        String of clean transcript text
    """
    lines = vtt_content.split('\n')
    transcript_lines = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip WEBVTT header
        if line.startswith('WEBVTT'):
            i += 1
            continue

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Skip cue numbers (just digits)
        if line.isdigit():
            i += 1
            continue

        # Skip timestamp lines (contains -->)
        if '-->' in line:
            i += 1
            continue

        # This should be actual caption text
        # Clean up any VTT formatting tags like <v Name>
        text = re.sub(r'<[^>]+>', '', line)
        text = text.strip()

        if text:
            transcript_lines.append(text)

        i += 1

    # Join all lines with spaces
    return ' '.join(transcript_lines)

def convert_vtt_to_transcript(vtt_path, output_path):
    """
    Convert a VTT file to a clean transcript text file.

    Args:
        vtt_path: Path to VTT file
        output_path: Path for output transcript text file

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(vtt_path, 'r', encoding='utf-8') as f:
            vtt_content = f.read()

        transcript_text = parse_vtt_to_text(vtt_content)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transcript_text)

        return True
    except Exception as e:
        print(f"  Error converting VTT to transcript: {e}")
        return False

def main():
    """Convert all VTT files in the transcripts folder to .txt files."""
    transcripts_folder = Path('transcripts')

    if not transcripts_folder.exists():
        print(f"Error: Transcripts folder not found: {transcripts_folder}")
        return

    vtt_files = list(transcripts_folder.glob('*.vtt'))

    if not vtt_files:
        print("No VTT files found in transcripts folder")
        return

    print(f"Found {len(vtt_files)} VTT files to convert\n")

    successful = 0
    failed = 0
    skipped = 0

    for vtt_file in vtt_files:
        output_path = vtt_file.with_suffix('.txt')

        # Skip if transcript already exists
        if output_path.exists():
            print(f"Skipping {vtt_file.name} - transcript already exists")
            skipped += 1
            continue

        print(f"Converting: {vtt_file.name}")

        if convert_vtt_to_transcript(vtt_file, output_path):
            print(f"  Saved to: {output_path.name}")
            successful += 1
        else:
            failed += 1

    print(f"\n{'='*50}")
    print(f"Conversion complete!")
    print(f"Successfully converted: {successful}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print(f"Transcripts saved to: {transcripts_folder.absolute()}")

if __name__ == "__main__":
    main()
