import os
import time
from datetime import datetime, timedelta

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from sync_server.settings import save_file_name
from sync_server.constants import DIRECTORY
from sync_server.log import get_logger

logger = get_logger(__name__)


def copy_file(src, dst, buffer_size=1024 * 1024):
    dst_file = open(dst, 'wb')
    with open(src, 'rb') as src_file:
        while True:
            buf = src_file.read(buffer_size)
            if not buf:
                break
            dst_file.write(buf)

    # save to state.json
    _, file = os.path.split(dst)
    save_file_name(file)


def rename_file(src_path):
    """
    rename file to YYYY-MM-DD-HH-mm-ss.[ext]
    :param src_path:
    :return: new_path
    """

    path, file = os.path.split(src_path)
    ext = os.path.splitext(src_path)[1]
    dt = datetime.utcnow()

    # increment to 1 second if file exists
    while dt.strftime("%Y-%m-%d-%H-%M-%S") in get_cur_dir_file_names():
        dt += timedelta(seconds=1)

    return os.path.join(path, dt.strftime("%Y-%m-%d-%H-%M-%S")+ext)


def get_cur_dir_file_names():
    filenames = []
    for filename in os.listdir(DIRECTORY):
        if os.path.isfile(os.path.join(DIRECTORY, filename)):
            name, _ = os.path.splitext(filename)
            filenames.append(name)
    return filenames


class MyHandler(FileSystemEventHandler):
    def __init__(self, src_dir, dst_dir):
        self.src_dir = src_dir
        self.dst_dir = dst_dir
        self.check_interval = 0.3
        self.check_duration = 5

    def on_created(self, event):
        if not event.is_directory:
            self.handle_new_file(event.src_path)

    def handle_new_file(self, file_path):
        # Check if file is fully uploaded
        if self.is_file_fully_uploaded(file_path):
            print(f"File fully uploaded: {file_path}")
            # Process the file
            self.process_file(file_path)
        else:
            print(f"File still uploading: {file_path}")

    def is_file_fully_uploaded(self, file_path):
        previous_size = -1
        for _ in range(self.check_duration):
            current_size = os.path.getsize(file_path)
            if current_size == previous_size:
                return True
            previous_size = current_size
            time.sleep(self.check_interval)
        return False

    def process_file(self, file_path):
        """
        Process the event to copy files from src_dir to dst_dir.
        """

        dst_path = os.path.join(self.dst_dir, os.path.relpath(file_path, self.src_dir))
        dst_path = rename_file(dst_path)

        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)

        if os.path.exists(file_path):
            copy_file(file_path, dst_path)

            logger.info(f'Copied: {file_path} to {dst_path}')

    # def on_moved(self, event):
    #     # For moved events, we should copy from the event.dest_path
    #     if not event.is_directory:
    #         src_path = rename_file(event.dest_path)
    #         dst_path = os.path.join(self.dst_dir, os.path.relpath(event.dest_path, self.src_dir))
    #
    #         os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    #
    #         if os.path.exists(src_path):
    #             copy_file(src_path, dst_path)
    #             logger.info(f'Moved: {src_path} to {dst_path}')


def watch_files():
    src_dir = "uploads"  # Replace with the source directory path
    dst_dir = DIRECTORY  # Replace with the destination directory path

    event_handler = MyHandler(src_dir, dst_dir)
    observer = Observer()
    observer.schedule(event_handler, src_dir, recursive=False)
    print(os.path.curdir, src_dir, dst_dir)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    watch_files()
