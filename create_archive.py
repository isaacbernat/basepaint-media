from argparse import ArgumentParser

from fetch_files import fetch_files
from fetch_metadata import create_metadata_csv
from enrich_metadata import enrich_metadata_csv
from image_to_pdf import create_pdf
from image_descriptions import create_reduced_images, create_description_csv
from config import LATEST, BATCH_SIZE, CREATE_COVER, INCLUDE_VIDEO, INCLUDE_DESCRIPTION, EXCLUDE_IMAGES, INCLUDE_DESCRIPTION_IMAGE, INCLUDE_DESCRIPTION_IMAGE_GRID


if __name__ == '__main__':
    parser = ArgumentParser(description='Create a Basepaint archive')
    parser.add_argument('-c', '--create-cover', action='store_true', default=CREATE_COVER, help='Create cover PDF')
    parser.add_argument('-v', '--include-video', action='store_true', default=INCLUDE_VIDEO, help='Include video frames in PDF')
    parser.add_argument('-d', '--include-description', action='store_true', default=INCLUDE_DESCRIPTION, help='Include image descriptions')
    parser.add_argument('-di', '--include-description-image', action='store_true', default=INCLUDE_DESCRIPTION_IMAGE, help='Include thumbnail under the image descriptions')
    parser.add_argument('-dig', '--include-description-image-grid', action='store_true', default=INCLUDE_DESCRIPTION_IMAGE_GRID, help='Include grid on top of image descriptions')
    parser.add_argument('-e', '--exclude-images', action='store_true', default=EXCLUDE_IMAGES, help='Exclude pages with images and metadata')
    args = parser.parse_args()

    print(f"Creating archive for up to day {LATEST}.")
    fetch_files(LATEST, "images")
    create_metadata_csv(LATEST)
    enrich_metadata_csv()
    if args.include_video:
        fetch_files(LATEST, "videos")
    if args.include_description:
        create_reduced_images()
        create_description_csv()
    create_pdf(BATCH_SIZE, args.create_cover, args.include_video, args.include_description, args.exclude_images, args.include_description_image, args.include_description_image_grid)
