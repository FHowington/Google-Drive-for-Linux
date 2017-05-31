import logging
from os import walk
import os
import inotify.adapters
import FileUpdate

_DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
_LOGGER = logging.getLogger(__name__)


def _configure_logging():

    _LOGGER.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter(_DEFAULT_LOG_FORMAT)
    ch.setFormatter(formatter)
    _LOGGER.addHandler(ch)


def monitor(base_id, drive):

    # Originally I used os.walk to add all subdirectories, but this prevents need for incorporating updates to watch
    # list in the event new folders are added to watched directory.
    base_path = '/home/forbes/OneDrive'

    i = inotify.adapters.InotifyTree(bytes(base_path, encoding="utf-8"))
    try:
        for event in i.event_gen():
            if event is not None:
                (header, type_names, watch_path, filename) = event
                #print("Watch path: " + watch_path.decode("utf-8").replace("//", "/"))
                #print("Filename: " + filename.decode("utf-8"))
                #print(header)
                #print(type_names)
                if "IN_CLOSE_WRITE" in type_names:

                    # This indicates that the file was saved. Initial creation of a file may generate
                    # this as well as an IN_CREATE, but the uploader should be able to prevent multiple copies

                    if os.path.getsize(watch_path.decode("utf-8") + "/" + filename.decode("utf-8")) > 0:
                        FileUpdate.update(base_id, watch_path.decode("utf-8"), filename.decode("utf-8"), drive)
                    else:
                        print("File is 0 bytes, will not attempt upload")

                elif "IN_CREATE" in type_names:
                    print("Something created")

                    # This indicates that whatever was just created was a folder. This must be handled differently
                    # than a newly created file would be
                    if os.path.isdir(watch_path.decode("utf-8") + "/" + filename.decode("utf-8")):
                        print("New folder detected")
                        FileUpdate.update_folder(base_id,watch_path.decode("utf-8") + "/" +
                                                 filename.decode("utf-8"), drive)
                    else:
                        FileUpdate.update(base_id, watch_path.decode("utf-8"), filename.decode("utf-8"), drive)

                        


                # Creating new folder
                # if type_names[0] == "IN_ISDIR":
                # print("Added" + (watch_path.decode("utf-8") + filename.decode("utf-8")).replace("//", "/"))


    finally:
        for (dir_path, dir_names, file_names) in walk(base_path):
            i.remove_watch(bytes(dir_path, encoding='utf-8'))

if __name__ == '__main__':
    _configure_logging()
    monitor(0)