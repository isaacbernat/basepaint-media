import requests
import os


def download_file(url, filename, datatype):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
    else:
        print(f"Failed to download {datatype} from {url}")


def fetch_files(latest, datatype="images"):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(script_dir, datatype)
    os.makedirs(images_dir, exist_ok=True)  # Create files directory if needed

    skipped_days = []
    print(f"Fetching {datatype}...")
    extension = "jpg" if datatype == "images" else "mp4"
    for day in range(1, latest):
        path = os.path.join(images_dir, f"{day:04d}.{extension}")
        if os.path.exists(path):
            skipped_days.append(day)  
            continue
        if datatype == "images":
            file_url = f"https://basepaint.xyz/api/art/image?day={day}"  # jpg image 2560x2560
            # available in png at lower res too at https://basepaint.net/v3/{day:04d}.png
        elif datatype == "videos":
            file_url = f"https://basepaint.net/animations/{day:04d}.{extension}"
        download_file(file_url, path, datatype)
        if day % 10 == 0:
            print(f"Downloading {datatype} {day}")
    print(f"Skipped days (already downloaded): {skipped_days}")
    print(f"Finished downloading {datatype}.")
