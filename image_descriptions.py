import os
import csv
import re
from time import sleep
from PIL import Image

import google.generativeai as genai

from config import GOOGLE_API_KEY, GEMINI_MODEL, GEMINI_SLEEP, ARCHIVE_VERSION
from fetch_metadata import load_titles, draw_header


def create_description_csv():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    titles = load_titles(os.path.join(script_dir, "metadata.csv"))
    metadata_days = {int(k): v["title"] for k, v in titles.items()}
    describe_png_images_to_csv(metadata_days, script_dir)


def create_reduced_images(block_size=2, output_format="png"):
    """
    Original images have square blocks many pixels tall. Shrink them using the top-left pixel.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_dir = os.path.join(script_dir, "images")
    image_files = sorted([f for f in os.listdir(image_dir) if f.endswith('.jpg')])
    reduced_dir = os.path.join(script_dir, "reduced_images")
    os.makedirs(reduced_dir, exist_ok=True)  # Create pdf directory if needed

    for image_file in image_files:  # Process each image
        image_name = image_file.split(".")[0]
        output_img = os.path.join(reduced_dir, f"{image_name}.{output_format}")
        if int(image_name) % 10 == 0:
            print(f"Reducing image: {image_file}. Will skip those already present.")
        if os.path.exists(output_img):
            continue

        try:
            img = Image.open(os.path.join(image_dir, image_file))
            width, height = img.size
            new_width = width // block_size
            new_height = height // block_size  # square images could use width instead
            reduced_image = Image.new("RGB", (new_width, new_height))
            reduced_pixels = reduced_image.load()
            original_pixels = img.load()

            # Take the color of the top-left pixels of the original blocks
            for y_new in range(new_height):
                for x_new in range(new_width):
                    x_original = x_new * block_size
                    y_original = y_new * block_size
                    color = original_pixels[x_original, y_original]
                    reduced_pixels[x_new, y_new] = color
            reduced_image.save(output_img)

        except Exception as e:
            print(f"An error occurred processing {image_name}: {e}")


def analyze_image_with_metadata(model, image_path, title_text):
    prompt_text = f"Analyze in detail all the elements of this pixel art image from basepaint.xyz project.{title_text} Take into account the color palette and resolution limitations. Identify all notable elements with emphasis on Internet memes, but mind tv, anime, games, comic, culture and other references too."
    prompt_text += " Sort the elements according to their relevance. The bigger ones should be more prominent. In case of a tie, sort them by position (the ones on top and left should be first)."
    prompt_text += " Output format should be one line for each element as follows: `(X,Y) <element>: <description>`, considering that images are square and 0,0 represents top left corner and 100,100 bottom right corner. (X,Y) represents the central pixel coordinate where the element is located. Also do not include any output that doesn't comply with this format."
    res = ""
    try:
        img = Image.open(image_path)
        response = model.generate_content([prompt_text, img])
        res = response.candidates[0].content.parts[0].text
    except Exception as e:
        print(f"Error during analysis of image {image_path}: {e}")
    finally:
        return res


def describe_png_images_to_csv(metadata_days, script_dir):
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    reduced_dir = os.path.join(script_dir, "reduced_images")
    description_csv = os.path.join(script_dir, "description.csv")

    existing_ids = set()
    if os.path.exists(description_csv):
        with open(description_csv, "r", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            try:
                existing_ids = {int(row["filename"]) for row in reader}
            except Exception as e:
                print(f"Error reading description csv: {e}")

    with open(description_csv, "a", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        if not existing_ids:
            csv_writer.writerow(["filename", "analysis"])

        for filename in sorted(os.listdir(reduced_dir)):
            if filename.endswith(".png"):
                image_id = int(os.path.splitext(filename)[0])
                if image_id in existing_ids:
                    continue
                title_text = metadata_days.get(image_id, "")
                description = analyze_image_with_metadata(model, os.path.join(reduced_dir, filename), title_text)
                if description:
                    for d in description.split("\n"):
                        csv_writer.writerow([image_id, d.strip().lstrip('*').strip()])
                if image_id % GEMINI_SLEEP[0] == 0:
                    print(f"Analyzed image with metadata: {filename} . Sleeping {GEMINI_SLEEP[1]} secs to avoid rate limits.")
                    sleep(GEMINI_SLEEP[1])
    print("Finished creating description csv.")


def create_description_page(canvas, script_dir,page_width, page_height, x_pos, day_num, descriptions, titles, include_description_image, include_description_image_grid):
    current_description = descriptions.get(int(day_num))
    if not current_description:
        print(f"No description found for day {day_num}")
        return
    draw_header(canvas, int(day_num), {"title": "", "palette": ""}, x_pos, page_height, page_width)
    canvas.setFont("OpenSans-Regular", 14)
    description_label = f"Description version {ARCHIVE_VERSION}"
    canvas.drawString(x_pos + 100, page_height - 54, description_label)
    canvas.setFont("OpenSans-Italic", 14)
    canvas.drawString(x_pos + 100 + canvas.stringWidth(description_label) + 20, page_height - 54, f"({GEMINI_MODEL})")
    render_description_text(canvas, page_height, x_pos, day_num, current_description, titles.get(day_num, {"title": ""})["title"])
    if include_description_image:    
        draw_description_grid(canvas, script_dir, page_width, page_height, x_pos, day_num, current_description, include_description_image_grid)
    canvas.showPage()


def render_description_text(canvas, page_height, x_pos, day_num, descriptions, title):
    canvas.setFont("OpenSans-Bold", 12)
    canvas.drawString(x_pos, page_height - 85 + 12, f"(X, Y): {title}")
    title_width = canvas.stringWidth(f"(X, Y): {title}", "OpenSans-Bold", 12)
    canvas.setFont("OpenSans-Italic", 10)
    canvas.drawString(x_pos + title_width + 2, page_height - 85 + 13, "(more info at https://github.com/isaacbernat/basepaint)")

    canvas.setFont("OpenSans-Regular", 10)
    coord_regex = r"\((\d+)\.*\d*,\s*(\d+)\.*\d*\)"  # LLMs sometimes use decimals -_-
    max_value = 0
    for line_num, l in enumerate(descriptions):
        try:
            x, y = [int(m) for m in re.search(coord_regex, l).groups()]
        except Exception as e:
            print(f"DEBUG: {day_num=} doesn't match regex {l=}")
            continue  # LLMs don't always follow explicit instructions on format...

        max_value = max(max_value, x, y)
        canvas.drawString(x_pos, page_height - 85 - line_num * 12, f"({x},{y})")
        try:
            label, value = l.split(")", 1)[1].strip().split(":", 1)
        except:  # LLMs don't always follow the required format -_-
            value = l.split(")", 1)[1].strip()
            label = ""

        canvas.setFont("OpenSans-Bold", 10)
        canvas.drawString(x_pos + 35, page_height - 85 - line_num * 12, f"{label.strip()}: ")
        canvas.setFont("OpenSans-Regular", 10)
        label_width = canvas.stringWidth(f"{label.strip()}: ", "OpenSans-Bold", 10)
        canvas.drawString(x_pos + 35 + label_width, page_height - 85 - line_num * 12, value.strip())
    if max_value > 100:
        print(f"DEBUG: {day_num=}, {max_value=}")  # LLMs don't always follow restrictions -_-


def draw_description_grid(canvas, script_dir, page_width, page_height, x_pos, day_num, descriptions, include_description_image_grid):
    filled_page = 85 + ((len(descriptions) + 1) * 12)
    square_size = min(page_height - filled_page, page_width - (x_pos * 2))
    small_square_size = square_size / 10
    square_x_pos = (page_width - square_size) / 2

    output_img = os.path.join(script_dir, "reduced_images", f"{day_num:04d}.png")
    canvas.drawImage(
        output_img,
        square_x_pos,
        12,
        width=square_size,
        height=square_size)

    canvas.setFont("OpenSans-Regular", 8)
    canvas.drawString(
        square_x_pos - 9,
        square_size + 2  + 12,  # position above grid
        "X="
    )
    canvas.drawString(
        square_x_pos + square_size - 2,
        square_size + 2  + 12,  # position above grid
        "Y=0"
    )
    for i in range(10):
        for j in range(10):
            if include_description_image_grid:
                canvas.rect(  # Draw grid lines
                    square_x_pos + (j * small_square_size),  # x position
                    i * small_square_size + 12,  # y position
                    small_square_size,  # width
                    small_square_size,  # height
                    fill=0  # draw outline
                )
            if i == 0:  # Draw X coordinate number at top
                canvas.drawString(
                    square_x_pos + (j * small_square_size),  # center horizontally
                    square_size + 2  + 12,  # position above grid
                    str(j * 10)
            )
            if j == 0:  # Draw Y coordinate number at right
                canvas.drawString(
                    square_x_pos + square_size + 2,  # position to the right of grid
                    i * small_square_size  + 12,  # center vertically
                    str(100 - i * 10)
                )
