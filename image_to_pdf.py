import os
import csv
from collections import defaultdict
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image


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


def count_pixels(image_path, palette):
    image = Image.open(image_path).convert("RGB")  # Ensure image is in RGB mode
    pixel_count = [0] * len(palette)
    color_dict = {tuple(color): index for index, color in enumerate(palette)}
    errors = 0
    for pixel in image.getdata():
        try:
            pixel_count[color_dict[pixel]] += 1
        except Exception as e:  # image 547 fails
            errors += 1
    if errors:
        print(f"count_pixels errors for {image_path}: {errors} pixels not matching palette colors")

    return [(count / (image.width * image.height)) * 100 for count in pixel_count]  # percentage_count


def draw_text(canvas, text_italic, text_normal, x, y, italic_offset, x_offset, page_width):
    canvas.setFont("OpenSans-Italic", 12)  # Italic for descriptive part
    canvas.drawString(x + x_offset, y, text_italic)
    canvas.setFont("OpenSans-Regular", 12)  # Regular font for the rest
    if italic_offset:
        total_italic_offset = x + x_offset + italic_offset
    else:
        total_italic_offset = page_width - canvas.stringWidth(text_normal) - x
    canvas.drawString(total_italic_offset, y, text_normal)


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


def draw_footer_line(c, footer_y, page_width, prefix_text, url_text):
    prefix_width = c.stringWidth(prefix_text, "OpenSans-Regular", 10)
    total_width = prefix_width + c.stringWidth(url_text, "FiraMono-Regular", 10)
    start_x = (page_width - total_width) / 2

    c.setFont("OpenSans-Regular", 10)
    c.drawString(start_x, footer_y, prefix_text)
    c.setFont("FiraMono-Regular", 10)
    c.drawString(start_x + prefix_width, footer_y, url_text)


def draw_pixel_info(c, sorted_palette, x_pos, first_line_y, palette_text_padding, max_lines=99, text_formula=lambda count: f" {count:.2f}% "):
    line_offset = 40
    init_text_padding = palette_text_padding
    COLOURS_PER_LINE = 7
    for i, (count, color) in enumerate(sorted_palette):
        if i == COLOURS_PER_LINE * max_lines:
            break
        if i % COLOURS_PER_LINE == 0:
            line_offset -= 40
            palette_text_padding= init_text_padding
        x_offset = x_pos + ((i % COLOURS_PER_LINE) * 20)

        c.setFont("OpenSans-Regular", 12)
        c.drawString(x_offset + palette_text_padding, first_line_y - 60 + line_offset, text_formula(count))
            
        c.setFont("FiraMono-Regular", 12)
        c.drawString(x_offset + palette_text_padding + 4, first_line_y - 80 + line_offset, f" #{color[0]:02x}{color[1]:02x}{color[2]:02x}")
        palette_text_padding += 50

        c.setFillColorRGB(color[0] / 255, color[1] / 255, color[2] / 255)
        c.rect(x_offset + palette_text_padding, first_line_y - 60 + line_offset, 10, 10, fill=1, stroke=1)  # stroke=1 to draw the border
        c.setFillColorRGB(0, 0, 0)  # Reset fill color to black for subsequent text


def draw_description(c, titles, day_num, pixel_counts, x_pos, page_width, first_line_y):
    formatted_mint_date = datetime.fromtimestamp(int(titles.get(day_num, {}).get('MINT_DATE', ''))).strftime('%Y-%m-%d')
    left_column_italic_offset = c.stringWidth("Mint date: ", "OpenSans-Italic", 12)
    left_column = [("Mint date:", f" {formatted_mint_date}"),
                   ("Theme:", f" {titles.get(day_num, {}).get('title', '')}"),
                   ("Proposer:", f" {titles.get(day_num, {}).get('proposer', '')}"),
                   ("Palette:", ""),
    ]
    right_column = [("Day:", f" {day_num}"),
                    ("Minted:", f" {titles.get(day_num, {}).get('minted', 0)}"),
                    ("Artists:", f" {titles.get(day_num, {}).get('artists', 0)}"),
                    ("", ""),
    ]
    for i, (left_text, right_text) in enumerate(zip(left_column, right_column)):
        draw_text(c, left_text[0], left_text[1], x_pos, first_line_y - (i * 20), italic_offset=left_column_italic_offset, x_offset=0, page_width=page_width)
        draw_text(c, right_text[0], right_text[1], x_pos, first_line_y - (i * 20), italic_offset=0, x_offset=page_width * 0.75, page_width=page_width)
    
    sorted_palette = sorted(zip(pixel_counts, titles.get(day_num, {}).get('palette', [])), key=lambda x: x[0], reverse=True)
    draw_pixel_info(c, sorted_palette, x_pos, first_line_y, left_column_italic_offset)


def draw_mosaic(c, x_pos, page_height, image_files, input_directory):
    c.setFont("OpenSans-Regular", 12)
    c.drawString(x_pos + 10, page_height - 180, "Top 100 colors (by pixel count):")
    c.drawString(381, page_height - 180, f"Archive version: 0.1.0")

    color_dict = defaultdict(int)
    for i, image_file in enumerate(image_files, 1):  # Process each image
        if i % 10 == 0:
            print(f"Collecting front-page pixels stats {i}/{len(image_files)}")
        image_path = os.path.join(input_directory, image_file)
        image = Image.open(image_path).convert("RGB")  # Ensure image is in RGB mode
        for pixel in image.getdata():
            color_dict[pixel] += 1

    draw_pixel_info(
        c,
        sorted({value: key for key, value in color_dict.items()}.items(), reverse=True),
        x_pos,
        first_line_y=page_height - 140,
        palette_text_padding=10,
        max_lines=15,
        text_formula=lambda count: f" {count/1000000:.2f}M "
    )


def load_fonts():
    pdfmetrics.registerFont(TTFont('FiraMono-Regular', './fonts/Fira_Mono/FiraMono-Regular.ttf'))
    pdfmetrics.registerFont(TTFont('OpenSans-Regular', './fonts/Open_Sans/static/OpenSans-Regular.ttf'))
    pdfmetrics.registerFont(TTFont('OpenSans-Italic', './fonts/Open_Sans/static/OpenSans-Italic.ttf'))
    pdfmetrics.registerFont(TTFont('OpenSans-Bold', './fonts/Open_Sans/static/OpenSans-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('MekSans-Regular', './fonts/MEK/meksans-regular-webfont.ttf'))
    pdfmetrics.registerFont(TTFont('MekMono', './fonts/MEK/mek-mono-webfont.ttf'))


def create_canvas(output_pdf, size=A4):
    c = canvas.Canvas(output_pdf, pagesize=size)
    c.setStrokeColorRGB(0, 0, 0)  # Set border color to black
    page_width, _ = size
    img_size = 2560 * 72 / 96  # Convert pixels to points (96 DPI to 72 DPI)
    scale_factor = (page_width * 0.9) / img_size  # 90% of page width
    scaled_width = img_size * scale_factor
    x_pos = (page_width - scaled_width) / 2

    return c, x_pos, scaled_width


def create_pdf_from_images(input_directory, pdf_dir, titles, image_files, size=A4, batch=100):
    page_width, page_height = size
    for page_num, image_file in enumerate(image_files, 1):  # Process each image
        if page_num % batch == 1:
            output_pdf = os.path.join(pdf_dir, f"basepaint_archive_{page_num}_to_{page_num+99}.pdf")
            c, x_pos, scaled_width = create_canvas(output_pdf)

        day_num = int(image_file.split('.')[0])  # Extract day number (assuming XXXX.jpg)
        if page_num % 10 == 0:
            print(f"Processing image {day_num}/{len(image_files)}")

        draw_header(c, day_num, titles, x_pos, page_height, page_width)
        image_path = os.path.join(input_directory, image_file)
        c.drawImage(image_path,
                   x_pos,  # center horizontally
                   page_height - scaled_width - 70,  # position below header
                   width=scaled_width, 
                   height=scaled_width)
        try:
            pixel_counts = count_pixels(image_path, titles.get(day_num, {}).get('palette', []))
            draw_description(c, titles, day_num, pixel_counts, x_pos, page_width, first_line_y=(page_height - scaled_width - 90))
        except Exception as e:
            print(f"Error processing image {day_num}: {e}")
        draw_footer_line(c, 40, page_width, "Artwork generated collaboratively at  ", f"https://basepaint.xyz/canvas/{day_num}")
        draw_footer_line(c, 40 - 15, page_width, "Archive available at  ", "https://github.com/isaacbernat/basepaint")
        c.showPage()
        if page_num % 100 == 0:
            c.save()
            print(f"saved {output_pdf}")


def create_cover(input_directory, pdf_dir, size, image_files):
    print("Creating PDF cover...")
    output_pdf = os.path.join(pdf_dir, "basepaint_archive_000_cover.pdf")
    page_width, page_height = size
    c, x_pos, _ = create_canvas(output_pdf)

    title = f"Basepaint Archive"
    c.setFont("MekSans-Regular", 64)
    c.drawString(x_pos + 7, page_height - 81, title)

    subtitle = f"Art Lives in Every Pixel"
    c.setFont("MekMono", 24)
    c.drawString(x_pos + 10, page_height - 105, subtitle)
    c.drawString(349, page_height - 105, f"From day #1 to #{len(image_files)}")

    draw_mosaic(c, x_pos, page_height, image_files, input_directory)
    draw_footer_line(c, 40, page_width, "Artwork generated collaboratively at  ", f"https://basepaint.xyz")
    draw_footer_line(c, 40 - 15, page_width, "Archive available at  ", "https://github.com/isaacbernat/basepaint")

    c.showPage()
    c.save()


def create_pdf(batch_size=100, add_cover=True):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    img_dir = os.path.join(script_dir, "images")
    pdf_dir = os.path.join(script_dir, "pdf")
    os.makedirs(pdf_dir, exist_ok=True)  # Create pdf directory if needed
    titles = load_titles('metadata.csv')
    image_files = sorted([f for f in os.listdir(img_dir) if f.endswith('.jpg')])
    size=A4
    load_fonts()
    create_pdf_from_images(img_dir, pdf_dir, titles, image_files, size=size, batch=batch_size)
    if add_cover:
        create_cover(
            input_directory=img_dir,
            pdf_dir=pdf_dir,
            size=size,
            image_files=image_files,
        )
    print("Finish creating PDF.")

if __name__ == "__main__":
    create_pdf()  # Call the function to execute it immediately
