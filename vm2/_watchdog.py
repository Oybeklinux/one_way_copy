import os
import time
from datetime import datetime, timedelta

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from settings import save_file_name
from vm1.constants import DIRECTORY


def copy_file(src, dst, buffer_size=1024 * 1024):
    with open(src, 'rb') as src_file, open(dst, 'wb') as dst_file:
        while True:
            buf = src_file.read(buffer_size)
            if not buf:
                break
            dst_file.write(buf)
    _, file = os.path.split(dst)
    save_file_name(file)


def rename_file(src_path):
    """
    rename file to YYYY-MM-DD-HH-mm-ss.[ext]
    :param src_path:
    :return: new_path
    """

    path, file = os.path.split(src_path)
    ext = file.split(".")
    ext = f".{ext[1]}" if len(ext) == 2 else ""
    dt = datetime.utcnow()
    new_name = os.path.join(path, dt.strftime("%Y-%m-%d-%H-%M-%S") + ext)

    # increment to 1 second if file exists
    while os.path.exists(new_name):
        dt += timedelta(seconds=1)
        new_name = os.path.join(path, dt.strftime("%Y-%m-%d-%H-%M-%S") + ext)
    return new_name


class MyHandler(FileSystemEventHandler):
    def __init__(self, src_dir, dst_dir):
        self.src_dir = src_dir
        self.dst_dir = dst_dir

    def process(self, event):
        """
        Process the event to copy files from src_dir to dst_dir.
        """
        if not event.is_directory:
            # src_path = event.src_path
            # If the event is a move event, the destination path is event.dest_path
            dst_path = os.path.join(self.dst_dir, os.path.relpath(event.src_path, self.src_dir))
            dst_path = rename_file(dst_path)

            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)

            if os.path.exists(event.src_path):
                copy_file(event.src_path, dst_path)
                print(f'Copied: {event.src_path} to {dst_path}')

    def on_created(self, event):
        self.process(event)

    def on_moved(self, event):
        # For moved events, we should copy from the event.dest_path
        if not event.is_directory:
            src_path = rename_file(event.dest_path)
            dst_path = os.path.join(self.dst_dir, os.path.relpath(event.dest_path, self.src_dir))

            os.makedirs(os.path.dirname(dst_path), exist_ok=True)

            if os.path.exists(src_path):
                copy_file(src_path, dst_path)
                print(f'Moved: {src_path} to {dst_path}')


def watch_files():
    src_dir = "uploads"  # Replace with the source directory path
    dst_dir = DIRECTORY  # Replace with the destination directory path

    event_handler = MyHandler(src_dir, dst_dir)
    observer = Observer()
    observer.schedule(event_handler, src_dir, recursive=True)
    observer.start()

    try:
        while True:
            print("+++watch_files+++++")
            time.sleep(2)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()



