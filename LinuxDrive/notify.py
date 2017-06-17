import logging
import os
import inotify.adapters

from FileUpdate import Update
from os import walk

_DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
_LOGGER = logging.getLogger(__name__)


class NotifyMonitor:
    def __init__(self, base_folder, base_path, base_id, drive):
        self.base_folder = base_folder
        self.base_path = base_path
        self.base_id = base_id
        self.drive = drive
        self.update = Update(base_id, drive)
        _LOGGER.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        formatter = logging.Formatter(_DEFAULT_LOG_FORMAT)
        ch.setFormatter(formatter)
        _LOGGER.addHandler(ch)

    def monitor(self):
        temp_name = None
        temp_cookie = None
        temp_path = None
        """ Formerly used notify tree, however there seems to be issues regarding watching newly created folders.
        May revert to tree if I can figure out how to ensure addition of all subfolders and files in new folder
        """

        i = inotify.adapters.Inotify()
        for (dirpath, dirnames, filenames) in walk(self.base_path):
            i.add_watch(bytes(dirpath, encoding="utf-8"))

        try:
            for event in i.event_gen():
                if event is not None:
                    (header, type_names, watch_path, filename) = event
                    if "IN_CLOSE_WRITE" in type_names:
                        """ This indicates that the file was saved. Initial creation of a file may generate
                        this as well as an IN_CREATE, but the uploader should be able to prevent multiple copies 
                        """

                        if os.path.getsize(watch_path.decode("utf-8") + "/" + filename.decode("utf-8")) > 0:
                            if not os.path.isdir(watch_path.decode("utf-8") + "/" + filename.decode("utf-8")):
                                print("Something written to")
                                self.update.update(watch_path.decode("utf-8"), filename.decode("utf-8"))
                        else:
                            print("File is 0 bytes, will not attempt upload")

                    elif "IN_CREATE" in type_names:
                        print("Something created")

                        """ This indicates that whatever was just created was a folder. This must be handled differently
                        than a newly created file would be
                        """
                        if os.path.isdir(watch_path.decode("utf-8") + "/" + filename.decode("utf-8")):
                            print("New folder detected")
                            self.update.update_folder(watch_path.decode("utf-8") + "/" +
                                                      filename.decode("utf-8"))
                            i.add_watch(
                                bytes((watch_path.decode("utf-8") + "/" + filename.decode("utf-8")),
                                      encoding="utf-8"))
                            """Because pasting a folder does not raise iNotify events for the files within the folder
                            we need to manually query the folder for it's contents"""
                            print("Recursively adding folder")
                            self.update.multi_add(watch_path.decode("utf-8") + "/" +
                                                  filename.decode("utf-8"), i)

                        else:
                            print("Not a folder")
                            self.update.update(watch_path.decode("utf-8"), filename.decode("utf-8"))

                    elif "IN_MOVED_FROM" in type_names:
                        temp_cookie = header.cookie
                        temp_path = watch_path
                        temp_name = filename

                    elif "IN_MOVED_TO" in type_names:
                        if header.cookie == temp_cookie:
                            print("A move or rename has been performed")

                            # Determining if this was a rename
                            if temp_path == watch_path:
                                if os.path.isdir(watch_path.decode("utf-8") + "/" + filename.decode("utf-8")):
                                    i.add_watch(bytes(
                                        (watch_path.decode("utf-8") + "/" + filename.decode("utf-8")),
                                        encoding="utf-8"))

                                print("This was a rename")
                                self.update.rename_file(temp_name.decode("utf-8"),
                                                        filename.decode("utf-8"),
                                                        watch_path.decode("utf-8"), i)
                            else:
                                print("This was a move")

        finally:
            print("Shutting down")
