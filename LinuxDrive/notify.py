import logging
import os
import inotify.adapters
import FileUpdate
from os import walk

_DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
_LOGGER = logging.getLogger(__name__)


class NotifyMonitor:
    def __init__(self):
        _LOGGER.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        formatter = logging.Formatter(_DEFAULT_LOG_FORMAT)
        ch.setFormatter(formatter)
        _LOGGER.addHandler(ch)

    def monitor(self, base_id, drive):
        temp_name = None
        temp_cookie = None
        temp_path = None
        """ Formerly used notify tree, however there seems to be issues regarding watching newly created folders.
        May revert to tree if I can figure out how to ensure addition of all subfolders and files in new folder
        """
        # i = inotify.adapters.InotifyTree(bytes(base_path, encoding="utf-8"))

        base_path = '/home/forbes/OneDrivePractice'
        i = inotify.adapters.Inotify()
        for (dirpath, dirnames, filenames) in walk(base_path):
            i.add_watch(bytes(dirpath, encoding="utf-8"))

        try:
            for event in i.event_gen():
                if event is not None:
                    (header, type_names, watch_path, filename) = event
                    print(filename)
                    print(type_names)
                    print(watch_path)
                    print(header)
                    if "IN_CLOSE_WRITE" in type_names:
                        """ This indicates that the file was saved. Initial creation of a file may generate
                        this as well as an IN_CREATE, but the uploader should be able to prevent multiple copies 
                        """

                        if os.path.getsize(watch_path.decode("utf-8") + "/" + filename.decode("utf-8")) > 0:
                            if not os.path.isdir(watch_path.decode("utf-8") + "/" + filename.decode("utf-8")):
                                print("Something written to")
                                FileUpdate.update(base_id, watch_path.decode("utf-8"), filename.decode("utf-8"), drive,
                                                  i)
                        else:
                            print("File is 0 bytes, will not attempt upload")

                    elif "IN_CREATE" in type_names:
                        print("Something created")

                        """ This indicates that whatever was just created was a folder. This must be handled differently
                        than a newly created file would be
                        """
                        if os.path.isdir(watch_path.decode("utf-8") + "/" + filename.decode("utf-8")):
                            print("New folder detected")
                            FileUpdate.update_folder(base_id, watch_path.decode("utf-8") + "/" +
                                                     filename.decode("utf-8"), drive, i)
                            i.add_watch(
                                bytes((watch_path.decode("utf-8") + "/" + filename.decode("utf-8")),
                                      encoding="utf-8"))
                            """Because pasting a folder does not raise iNotify events for the files within the folder
                            we need to manually query the folder for it's contents"""

                        else:
                            FileUpdate.update(base_id, watch_path.decode("utf-8"), filename.decode("utf-8"), drive, i)

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
                                FileUpdate.rename_file(base_id, temp_name.decode("utf-8"), filename.decode("utf-8"),
                                                       watch_path.decode("utf-8"), drive, i)
                            else:
                                print("This was a move")

        finally:
            print("Shutting down")
