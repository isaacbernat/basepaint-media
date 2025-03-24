from bs4 import BeautifulSoup
import os
import csv
import re


# prerreq, download https://basepaint.xyz/gallery as gallery.html first
def enrich_metadata_csv():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_file = os.path.join(script_dir, "gallery.html")
    csv_file = os.path.join(script_dir, "metadata.csv")

    print("Enriching existing metadata csv...")
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Find all div elements and store them in a list for sorting
            title_divs = soup.find_all('div', class_='sm:flex-1 text-white text-md')
            entries = []

            for div in title_divs:
                text = div.text.strip()
                match = re.match(r'Day #(\d+): (.*)', text)
                if match:
                    num, title = match.groups()
                    
                    # Find stats div for minted and artists counts
                    stats_div = div.find_next('div', class_='block text-sm text-gray-500')
                    minted_count = 0
                    artists_count = 0
                    if stats_div:
                        stats_text = stats_div.text.strip()
                        minted_match = re.search(r'(\d+) minted', stats_text)
                        artists_match = re.search(r'(\d+) artists', stats_text)
                        if minted_match:
                            minted_count = int(minted_match.group(1))
                        if artists_match:
                            artists_count = int(artists_match.group(1))
                    
                    # Find the color palette div that follows this title
                    palette_div = div.find_next('div', class_='inline-flex flex-row gap-0.5 pt-0.5 items-start')
                    colors = []
                    if palette_div:
                        color_divs = palette_div.find_all('div', class_='w-4 h-4 sm:block hidden border border-1 border-gray-700 rounded-sm')
                        for color_div in color_divs:
                            style = color_div.get('style', '')
                            color_match = re.search(r'background-color: rgb\((.*?)\)', style)
                            if color_match:
                                colors.append(color_match.group(1))
                    
                    # Join colors with semicolon for CSV storage
                    palette = ';'.join(colors) if colors else ''
                    entries.append((int(num), title.strip(), palette, minted_count, artists_count))  # Add new stats
        
        # Sort entries by number
        entries.sort(key=lambda x: x[0])
        
        # Read existing entries from the CSV file
        existing_entries = {}
        if os.path.exists(csv_file):
            with open(csv_file, 'r', newline='', encoding='utf-8') as csvf:
                reader = csv.reader(csvf)
                header = next(reader)  # Skip header
                for row in reader:
                    existing_entries[row[0]] = row  # Store existing rows by NUM

        # Update or append entries
        for entry in entries:
            num = str(entry[0])
            if num in existing_entries:
                existing_entries[num][3] = entry[3]  # Update MINTED column

        # Write updated entries to CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvf:
            writer = csv.writer(csvf)
            writer.writerow(header)
            writer.writerows(existing_entries.values())
    except Exception as e:
        print(f"An error occurred: {e}")
    print("Finished enriching metadata csv.")
