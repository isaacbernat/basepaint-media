from argparse import ArgumentParser

from fetch_files import fetch_files
from fetch_metadata import create_metadata_csv
from enrich_metadata import enrich_metadata_csv
from image_to_pdf import create_pdf
from config import LATEST, BATCH_SIZE, CREATE_COVER, INCLUDE_VIDEO


if __name__ == '__main__':
    parser = ArgumentParser(description='Create a Basepaint archive')
    parser.add_argument('-c', '--create-cover', action='store_true', default=CREATE_COVER, help='Create cover PDF')
    parser.add_argument('-v', '--include-video', action='store_true', default=INCLUDE_VIDEO, help='Include video frames in PDF')
    args = parser.parse_args()

    print(f"Creating archive for up to day {LATEST}.")
    fetch_files(LATEST, "images")
    create_metadata_csv(LATEST)
    enrich_metadata_csv()
    fetch_files(LATEST, "videos")
    create_pdf(BATCH_SIZE, args.create_cover, args.include_video)
