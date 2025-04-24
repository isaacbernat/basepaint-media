import cv2
import os


def extract_images_from_video(video_path, number_of_intervals=12):
    output_dir = 'video_images'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    video_capture = cv2.VideoCapture(video_path)
    total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    if fps > 0:
        duration = total_frames / fps
        interval = duration / number_of_intervals
        timestamps = [(i * interval) for i in range(number_of_intervals + 1)][1:]

        # Extract images at specified timestamps
        for timestamp in timestamps:
            index = timestamps.index(timestamp)
            filename = os.path.join(output_dir, f'{os.path.basename(video_path).split(".")[0]}_{index:03d}.jpg')
            if os.path.exists(filename):
                print(f"Skipping {filename} at this time point, since it already exists.")
                break
            video_capture.set(cv2.CAP_PROP_POS_MSEC, (timestamp - 0.1) * 1000)
            success, frame = video_capture.read()
            if success:
                cv2.imwrite(filename, frame)
            else:
                print(f"error extracting image at timestamp {timestamp}")
    else:
        print(f"Error: FPS is 0 for {video_path}")
    video_capture.release()
