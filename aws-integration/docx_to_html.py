"""
Convert DOCX and PDF files to WCAG-compliant HTML.
Maintains headers, paragraphs, lists, and links with proper accessibility.
"""

from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
import html
import fitz  # PyMuPDF
import re


def get_link_aria_label(link_text):
    """Generate aria-label for links in 'Visit the X website' format."""
    if not link_text:
        return ""
    return f' aria-label="Visit the {html.escape(link_text)} website"'


def process_paragraph(paragraph):
    """Convert a paragraph to HTML, preserving links."""
    style_name = paragraph.style.name if paragraph.style else ""
    # print(f"Processing paragraph with style: '{style_name}'")

    # Determine tag based on style
    if style_name.startswith('Heading 1'):
        tag = 'h1'
    elif style_name.startswith('Heading 2'):
        tag = 'h1'
    elif style_name.startswith('Heading 3'):
        tag = 'h2'
    elif style_name.startswith('Heading 4'):
        tag = 'h3'
    elif style_name.startswith('Heading 5'):
        tag = 'h4'
    elif style_name.startswith('Heading 6'):
        tag = 'h5'
    else:
        tag = 'p'

    content_parts = []

    for child in paragraph._p:
        if child.tag == qn('w:hyperlink'):
            rel_id = child.get(qn('r:id'))
            url = None
            if rel_id and rel_id in paragraph.part.rels:
                url = paragraph.part.rels[rel_id].target_ref

            link_text = ''
            for run in child.findall(qn('w:r')):
                for text_elem in run.findall(qn('w:t')):
                    if text_elem.text:
                        link_text += text_elem.text

            if url and link_text:
                aria_label = get_link_aria_label(link_text)
                content_parts.append(f'<a href="{html.escape(url)}"{aria_label}>{html.escape(link_text)}</a>')
            elif link_text:
                content_parts.append(html.escape(link_text))

        elif child.tag == qn('w:r'):
            is_bold = False
            is_italic = False

            rpr = child.find(qn('w:rPr'))
            if rpr is not None:
                if rpr.find(qn('w:b')) is not None:
                    is_bold = True
                if rpr.find(qn('w:i')) is not None:
                    is_italic = True

            for text_elem in child.findall(qn('w:t')):
                if text_elem.text:
                    text = html.escape(text_elem.text)
                    if is_bold and is_italic:
                        text = f'<em>{text}</em>'
                    elif is_bold:
                        text = f'{text}'
                    elif is_italic:
                        text = f'<em>{text}</em>'
                    content_parts.append(text)

    content = ''.join(content_parts)

    if not content.strip():
        return '', tag

    return f'            <{tag}>{content}</{tag}>', tag


def get_paragraph_content(para):
    """Extract content from a paragraph for list items."""
    content_parts = []
    for child in para._p:
        if child.tag == qn('w:hyperlink'):
            rel_id = child.get(qn('r:id'))
            url = None
            if rel_id and rel_id in para.part.rels:
                url = para.part.rels[rel_id].target_ref

            link_text = ''
            for run in child.findall(qn('w:r')):
                for text_elem in run.findall(qn('w:t')):
                    if text_elem.text:
                        link_text += text_elem.text

            if url and link_text:
                aria_label = get_link_aria_label(link_text)
                content_parts.append(f'<a href="{html.escape(url)}"{aria_label}>{html.escape(link_text)}</a>')
            elif link_text:
                content_parts.append(html.escape(link_text))

        elif child.tag == qn('w:r'):
            is_bold = False
            is_italic = False

            rpr = child.find(qn('w:rPr'))
            if rpr is not None:
                if rpr.find(qn('w:b')) is not None:
                    is_bold = True
                if rpr.find(qn('w:i')) is not None:
                    is_italic = True

            for text_elem in child.findall(qn('w:t')):
                if text_elem.text:
                    text = html.escape(text_elem.text)
                    if is_bold and is_italic:
                        text = f'<em>{text}</em>'
                    elif is_bold:
                        text = f'{text}'
                    elif is_italic:
                        text = f'<em>{text}</em>'
                    content_parts.append(text)

    return ''.join(content_parts)


def is_list_paragraph(para):
    """Check if a paragraph is a list item."""
    style_name = para.style.name if para.style else ""

    pPr = para._p.find(qn('w:pPr'))
    if pPr is not None:
        numPr = pPr.find(qn('w:numPr'))
        if numPr is not None:
            return True

    if 'List' in style_name or 'Bullet' in style_name:
        return True

    return False


def process_list_items(paragraphs, start_idx):
    """Process consecutive list items starting from start_idx."""
    items = []
    idx = start_idx

    while idx < len(paragraphs):
        para = paragraphs[idx]

        if not is_list_paragraph(para):
            break

        content = get_paragraph_content(para)
        if content.strip():
            items.append(f'                <li>{content}</li>')

        idx += 1

    if not items:
        return '', start_idx

    list_html = '            <ul>\n' + '\n'.join(items) + '\n            </ul>'
    return list_html, idx


def is_disclaimer_text(text):
    """Check if text appears to be a disclaimer/footer."""
    disclaimer_phrases = [
        'this content is intended for general information',
        'not a substitute for professional',
        'not intended to be relied upon',
        'consult your doctor',
        'seek professional advice'
    ]
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in disclaimer_phrases)


def convert_docx_to_html(docx_path):
    """Convert a DOCX file to WCAG-compliant HTML."""
    doc = Document(docx_path)
    html_parts = []
    title = docx_path.stem  # Use filename as title
    in_references = False
    references_content = []
    footer_content = []

    paragraphs = list(doc.paragraphs)
    idx = 0

    while idx < len(paragraphs):
        para = paragraphs[idx]

        # Check if this is a list item
        if is_list_paragraph(para):
            list_html, idx = process_list_items(paragraphs, idx)
            if list_html:
                if in_references:
                    references_content.append(list_html)
                else:
                    html_parts.append(list_html)
        else:
            para_html, tag = process_paragraph(para)
            if para_html:
                # Check for References section
                if tag in ('h2', 'h3') and 'reference' in para_html.lower():
                    in_references = True
                    references_content.append(para_html)
                    idx += 1
                    continue

                # Check for disclaimer/footer content
                if is_disclaimer_text(para_html):
                    footer_content.append(para_html)
                    idx += 1
                    continue

                if in_references:
                    references_content.append(para_html)
                else:
                    html_parts.append(para_html)
            idx += 1

    # Build the final HTML document
    body_content = '\n'.join(html_parts)

    # Build references section if exists
    references_html = ''
    if references_content:
        ref_content = '\n'.join(references_content).replace('<h2>', '<h2 id="references-heading">').replace('<h3>', '<h3 id="references-heading">')
        references_html = f'''
            <section aria-labelledby="references-heading">
{ref_content}
            </section>'''

    # Build footer if exists
    footer_html = ''
    if footer_content:
        footer_items = '\n'.join(fc.replace('<p>', '<p><small><em>').replace('</p>', '</em></small></p>') for fc in footer_content)
        footer_html = f'''
            <footer>
{footer_items}
            </footer>'''

    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            font-family: 'Inter', sans-serif;
        }}
        body {{
            font-size: 16px;
            color: #10151A;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        main {{
            max-width: 8.5in;
            margin: 0 auto;
            padding: 1in;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            min-height: 100vh;
            box-sizing: border-box;
        }}
        h1 {{
            color: #0058BE;
            text-align: center;
        }}
        h2, h3, h4, h5, h6 {{
            color: #0058BE;
        }}
        a {{
            color: #0058BE;
        }}
        section[aria-labelledby="references-heading"] a {{
            color: #10151A;
        }}
        .skip-link {{
            position: absolute;
            top: -40px;
            left: 0;
            background: #0058BE;
            color: white;
            padding: 8px;
            z-index: 100;
        }}
        .skip-link:focus {{
            top: 0;
        }}
    </style>
</head>
<body>
    <a href="#main-content" class="skip-link">Skip to main content</a>

    <main id="main-content">
        <article>
{body_content}
{references_html}
{footer_html}
        </article>
    </main>
</body>
</html>'''

    return full_html

def main():
    assets_dir = Path(__file__).parent / 'assets' / 'pager_assets'
    output_dir = assets_dir / 'html_output'
    output_dir.mkdir(exist_ok=True)

    docx_files = list(assets_dir.glob('*.docx'))


    if len(docx_files) == 0:
        print("No DOCX files found in assets folder.")
        return

    print(f"Found {len(docx_files)} DOCX file(s) to convert.")

    # Process DOCX files
    for docx_path in docx_files:
        print(f"Converting DOCX: {docx_path.name}")

        try:
            html_content = convert_docx_to_html(docx_path)

            output_path = output_dir / f"{docx_path.stem}.html"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"  -> Saved to: {output_path.name}")

        except Exception as e:
            print(f"  -> Error: {e}")

    print("\nConversion complete!")


if __name__ == '__main__':
    main()
