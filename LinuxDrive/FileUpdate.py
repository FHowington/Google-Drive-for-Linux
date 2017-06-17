import os
from os import walk
import datetime
import Locater
from apiclient import http
import magic

files = []
dirs = []


class Update:
    def __init__(self, base_id, drive):
        self.drive = drive
        self.base_id = base_id

    def update(self, full_path, filename):
        print("Trying to update")
        folder_id = Locater.find(self.base_id, full_path, self.drive)

        file_located = False
        page_token = None
        response = self.drive.service.files().list(q="mimeType!='application/vnd.google-apps.folder'"
                                                     and "'%s' in parents" % folder_id
                                                     and "name='%s'" % filename,
                                                   spaces='drive',
                                                   fields='nextPageToken, files(id, name, parents, modifiedTime)',
                                                   pageToken=page_token).execute()

        for file in response.get('files', []):
            if file.get('name') == filename and folder_id in file.get('parents'):
                print("File located")

                # Getting time of modification of all files in path
                modified_date = os.path.getmtime(full_path + '/' + filename)

                # Converting Google's weird datetime zulu syntax into UTC syntax
                datetime_existing = datetime.datetime.strptime(file.get('modifiedTime').replace("T", " ")[:19],
                                                               '%Y-%m-%d %H:%M:%S')

                if datetime.datetime.utcfromtimestamp(modified_date) > datetime_existing:
                    # fileToRemove = drive.CreateFile({'id': filesContained['id']})
                    # fileToRemove.Delete()
                    print("More recent version of file found. File removed.")
                    break

                else:
                    print("Found file in folder already id, it is: ", file.get('id'))
                    file_located = True
                    break

        if not file_located:
            file_metadata = {
                'parents': [folder_id],
                'name': filename,
            }

            mime_type = magic.from_file(full_path + "/" + filename, mime=True)

            media = http.MediaFileUpload(full_path + "/" + filename, mimetype=mime_type)

            self.drive.service.files().create(body=file_metadata,
                                              media_body=media,
                                              fields='id').execute()

            print("Did not find file, creating it")

    def update_folder(self, full_path):
        Locater.find(self.base_id, full_path, self.drive)

    def rename_file(self, temp_name, filename, watch_path, notify):
        if os.path.isdir(watch_path + "/" + filename):
            notify.add_watch(bytes(watch_path + "/" + filename, encoding="utf-8"))

        folder_id = Locater.find(self.base_id, watch_path, self.drive)
        page_token = None
        response = self.drive.service.files().list(q="'%s' in parents" % folder_id
                                                     and "name='%s'" % temp_name,
                                                   spaces='drive',
                                                   fields='nextPageToken, files(id, name, parents)',
                                                   pageToken=page_token).execute()

        for file in response.get('files', []):
            if file.get('name') == temp_name and folder_id in file.get('parents'):
                print("Older folder found")

                file_metadata = {'name': filename}

                self.drive.service.files().update(fileId=file.get('id'), body=file_metadata,
                                                  fields='id').execute()

    def multi_add(self, watch_path, notify):
        for (dir_path, dir_names, file_names) in walk(watch_path):
            for file in file_names:
                if os.path.isdir(dir_path + "/" + file):
                    notify.add_watch(bytes(dir_path + "/" + file, encoding="utf-8"))
                else:
                    Update.update(self, self.base_id, dir_path)
