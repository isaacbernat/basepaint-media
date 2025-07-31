import requests
import csv
import os
from typing import Dict, List, Any


def fetch_day_data(day: int) -> Dict[str, Any]:
    url = f'https://basepaint.xyz/api/art/{day}'
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def extract_metadata(data: Dict[str, Any], fieldnames: List[str]) -> Dict[str, Any]:
    metadata = {f: None for f in fieldnames}
    for attr in data.get('attributes', []):  # Extract attributes
        if attr['trait_type'] == 'Day':
            metadata['NUM'] = int(attr['value'])
        elif attr['trait_type'] == 'Theme':
            metadata['TITLE'] = attr['value']
        elif attr['trait_type'] == 'Contributor Count':
            metadata['ARTISTS'] = attr['value']
        elif attr['trait_type'] == 'Proposer':
            metadata['PROPOSER'] = attr['value']
        elif attr['trait_type'] == 'Mint Date':
            metadata['MINT_DATE'] = attr['value']
        elif attr['trait_type'].startswith('Color #'):
            if metadata['PALETTE'] is None:
                metadata['PALETTE'] = []
            hex_color = attr['value'].lstrip('#')  # Convert hex to RGB
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            metadata['PALETTE'].append(f"{rgb[0]}, {rgb[1]}, {rgb[2]}")
    
    if metadata['PALETTE']:
        metadata['PALETTE'] = ';'.join(metadata['PALETTE'])
    
    return metadata


def create_metadata_csv(max_day: int):
    skipped_days = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "metadata.csv")
    fieldnames = ['NUM', 'TITLE', 'PALETTE', 'MINTED', 'ARTISTS', 'PROPOSER', 'MINT_DATE']
    
    existing_days = set()
    if os.path.exists(csv_path):  # Read existing days from CSV if it exists
        with open(csv_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            existing_days = {int(row['NUM']) for row in reader}
    
    mode = 'a' if existing_days else 'w'  # Open in append mode if file exists, write mode if it doesn't
    with open(csv_path, mode, newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if mode == 'w':
            writer.writeheader()
        
        print("Fetching metadata...")
        for day in range(1, max_day + 1):
            if day in existing_days:
                skipped_days.append(day)
                continue
            try:
                data = fetch_day_data(day)
                metadata = extract_metadata(data, fieldnames)
                metadata['MINTED'] = "N/A"  # Set MINTED to 0 since it's not available in the API
                writer.writerow(metadata)
                if day % 10 == 0:
                    print(f"Processed Day {day}: {metadata['TITLE']}")
            except Exception as e:
                print(f"Error processing Day {day}: {str(e)}")
    print(f"Skipped days (already in CSV): {skipped_days}")
    print("Finished creating metadata csv.")


def load_titles(csv_path):
    titles = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            titles[int(row['NUM'])] = {
                'title': row['TITLE'],
                'palette': [tuple(map(int, color.strip().split(','))) for color in row['PALETTE'].split(';')],
                'minted': row.get('MINTED', 0),
                'artists': row.get('ARTISTS', 0),
                'proposer': row.get('PROPOSER', ''),
                'MINT_DATE': row.get('MINT_DATE', ''),
            }
    return titles


def draw_header(canvas, day_num, titles, x_pos, page_height, page_width):
    title_data = titles.get(day_num, {'title': '', 'palette': []})
    title = f"Day {day_num}: {title_data['title']}"
    canvas.setFont("MekSans-Regular", 24)
    canvas.drawString(x_pos, page_height - 55, title)
    
    square_size = canvas.stringWidth("o", "MekSans-Regular", 24)
    square_spacing = square_size * 1.2  # Add some spacing between squares
    palette = title_data['palette']
    total_palette_width = len(palette) * square_spacing
    start_x = page_width - x_pos - total_palette_width
    
    for i, color in enumerate(palette):
        canvas.setFillColorRGB(color[0]/255, color[1]/255, color[2]/255)
        canvas.rect(start_x + (i * square_spacing), page_height - 50 - square_size/2, 10, 10, fill=1, stroke=1)  # stroke=1 to draw the border
    canvas.setFillColorRGB(0, 0, 0)  # Reset fill color to black for subsequent text
