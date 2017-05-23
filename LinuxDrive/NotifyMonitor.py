import logging
from os import walk
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

def monitor(baseID, drive):
    i = inotify.adapters.Inotify()
    basePath = "/home/forbes/OneDrive"
    for (dirpath, dirnames, filenames) in walk(basePath):
        i.add_watch(bytes(dirpath, encoding="utf-8"))

    try:
        for event in i.event_gen():
            if event is not None:
                (header, type_names, watch_path, filename) = event
                #print(type_names[0])
                #print(watch_path.decode("utf-8"))
                #print(filename.decode("utf-8"))
                #print(baseID)
                if(type_names[0] == "IN_CLOSE_WRITE"):
                    print("TRYING")
                    FileUpdate.update(baseID,watch_path.decode("utf-8"),filename.decode("utf-8"),drive)


    finally:
        for (dirpath, dirnames, filenames) in walk(basePath):
            i.remove_watch(bytes(dirpath, encoding='utf-8'))

if __name__ == '__main__':
    _configure_logging()
    monitor(0)