import os
from os import walk
import datetime
from apiclient import http
import magic

from locater import Locater

files = []
dirs = []


class Update:
    def __init__(self, base_id, drive, base_path):
        self.drive = drive
        self.base_id = base_id
        self.locater = Locater(base_id=base_id, drive=drive, base_path=base_path)
        self.folder_id = None

    def update(self, full_path, file_names):
        print("Trying to update")
        self.folder_id = self.locater.find(full_path=full_path, previous_folder=self.folder_id)

        file_located = False
        page_token = None

        print(file_names)
        for filename in file_names:
            print("Searching for " + filename)
            response = self.drive.service.files().list(q="mimeType!='application/vnd.google-apps.folder'"
                                                         and "'%s' in parents" % self.folder_id
                                                         and "name='%s'" % filename,
                                                       spaces='drive',
                                                       fields='nextPageToken, files(id, name, parents, modifiedTime)',
                                                       pageToken=page_token).execute()

            for file in response.get('files', []):
                if file.get('name') == filename and self.folder_id in file.get('parents'):
                    print("File located")

                    # Getting time of modification of all files in path
                    modified_date = os.path.getmtime(full_path + '/' + filename)

                    # Converting Google's weird datetime zulu syntax into UTC syntax
                    datetime_existing = datetime.datetime.strptime(file.get('modifiedTime').replace("T", " ")[:19],
                                                                   '%Y-%m-%d %H:%M:%S')

                    if datetime.datetime.utcfromtimestamp(modified_date) > datetime_existing:
                        self.drive.service.files().delete(fileId=(file.get('id'))).execute()
                        print("More recent version of file found. File removed.")
                        break

                    else:
                        print("Found file in folder already id, it is: ", file.get('id'))
                        file_located = True
                        break

            if not file_located:
                if os.path.isfile(full_path + "/" + filename):
                    file_metadata = {
                        'parents': [self.folder_id],
                        'name': filename,
                    }

                    mime_type = magic.from_file(full_path + "/" + filename, mime=True)

                    media = http.MediaFileUpload(full_path + "/" + filename, mimetype=mime_type)

                    self.drive.service.files().create(body=file_metadata,
                                                      media_body=media,
                                                      fields='id').execute()

                    print("Did not find file, creating it")
                else:
                    print("Is not a real file")

    def update_folder(self, full_path):
        self.locater.find(full_path=full_path, previous_folder=self.folder_id)

    def rename_file(self, temp_name, filename, watch_path, notify):
        if os.path.isdir(watch_path + "/" + filename):
            notify.add_watch(bytes(watch_path + "/" + filename, encoding="utf-8"))

        self.folder_id = self.locater.find(full_path=watch_path, previous_folder=self.folder_id)
        page_token = None
        response = self.drive.service.files().list(q="'%s' in parents" % self.folder_id
                                                     and "name='%s'" % temp_name,
                                                   spaces='drive',
                                                   fields='nextPageToken, files(id, name, parents)',
                                                   pageToken=page_token).execute()

        for file in response.get('files', []):
            if file.get('name') == temp_name and self.folder_id in file.get('parents'):
                print("Older folder found")

                file_metadata = {'name': filename}

                self.drive.service.files().update(fileId=file.get('id'), body=file_metadata,
                                                  fields='id').execute()

    def multi_add(self, watch_path, notify):
        for (dir_path, dir_names, file_names) in walk(watch_path):
            for directory in dir_names:
                Update.update_folder(self, dir_path + "/" + directory)
                notify.add_watch(bytes(dir_path + "/" + directory, encoding="utf-8"))

            else:
                Update.update(self, full_path=dir_path, file_names=file_names)

    def move(self, temp_path, watch_path, filename):
        self.folder_id = self.locater.find(full_path=temp_path, previous_folder=self.folder_id)
        new_parent = self.locater.find(watch_path, self.folder_id)
        print(new_parent)
        page_token = None
        response = self.drive.service.files().list(q="'%s' in parents" % self.folder_id
                                                     and "name='%s'" % filename,
                                                   spaces='drive',
                                                   fields='nextPageToken, files(id, name, parents)',
                                                   pageToken=page_token).execute()
        for file in response.get('files', []):
            if file.get('name') == filename and self.folder_id in file.get('parents'):
                previous_parents = ",".join(file.get('parents'))
                # Move the file to the new folder
                self.drive.service.files().update(fileId=file.get('id'),
                                                  addParents=new_parent,
                                                  removeParents=previous_parents,
                                                  fields='id, parents').execute()

                print("Successfully moved remote file")
