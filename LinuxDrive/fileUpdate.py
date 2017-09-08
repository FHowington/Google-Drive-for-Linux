import os
import logging
from os import walk
import datetime
from apiclient import http
import magic
import json

from locater import Locater

files = []
dirs = []
save_file_name = "files.json"


class Update:
    def __init__(self, base_id, drive, base_path, save_file=None):
        self.drive = drive
        self.base_id = base_id
        self.locater = Locater(base_id=base_id, drive=drive, base_path=base_path)
        self.folder_id = None
        self.logger = logging.getLogger('Drive_Linux')
        self.save_file = save_file

    def update(self, full_path, file_names):
        if self.save_file is not None:
            self.save_file.seek(0)
            saved_files = json.load(self.save_file)

        self.folder_id = self.locater.find(full_path=full_path)

        file_located = False
        page_token = None

        for filename in file_names:
            if self.save_file is not None:
                if full_path + '/' + filename in saved_files:
                    if len(saved_files[full_path + '/' + filename]) > 20:
                        datetime_existing = datetime.datetime.strptime(saved_files[full_path + '/' + filename],
                                                                       '%Y-%m-%d %H:%M:%S.%f')
                    else:
                        datetime_existing = datetime.datetime.strptime(saved_files[full_path + '/' + filename],
                                                                       '%Y-%m-%d %H:%M:%S')

                    modified_date = os.path.getmtime(full_path + '/' + filename)
                    if datetime.datetime.utcfromtimestamp(modified_date) <= datetime_existing:
                        file_located = True

            if not file_located:
                response = self.drive.service.files().list(q="mimeType!='application/vnd.google-apps.folder'"
                                                             and "'%s' in parents" % self.folder_id
                                                             and "name='%s'" % filename,
                                                           spaces='drive',
                                                           fields='nextPageToken, files(id, name, parents,'
                                                                  ' modifiedTime)',
                                                           pageToken=page_token).execute()

                for file in response.get('files', []):
                    if file.get('name') == filename and self.folder_id in file.get('parents'):

                        # Getting time of modification of all files in path
                        modified_date = os.path.getmtime(full_path + '/' + filename)

                        # Converting Google's weird datetime zulu syntax into UTC syntax

                        datetime_existing = datetime.datetime.strptime(file.get('modifiedTime').replace("T", " ")[:19],
                                                                       '%Y-%m-%d %H:%M:%S')

                        if datetime.datetime.utcfromtimestamp(modified_date) > datetime_existing:
                            self.drive.service.files().delete(fileId=(file.get('id'))).execute()
                            self.logger.info(
                                "More recent version of " + filename + " found. File removed from Google Drive.")
                            if self.save_file is not None:
                                saved_files[full_path + '/' + filename] = datetime.datetime.utcfromtimestamp(
                                    modified_date).__str__()

                            break

                        else:
                            file_located = True
                            if self.save_file is not None:
                                saved_files[full_path + '/' + filename] = datetime.datetime.utcfromtimestamp(
                                    modified_date).__str__()
                            break

            if not file_located:
                if os.path.isfile(full_path + "/" + filename):
                    file_metadata = {
                        'parents': [self.folder_id],
                        'name': filename,
                    }

                    mime_type = magic.from_file(full_path + "/" + filename, mime=True)
                    if os.path.getsize(full_path + "/" + filename) > 0:
                        media = http.MediaFileUpload(full_path + "/" + filename, resumable=True, mimetype=mime_type)
                    else:
                        media = http.MediaFileUpload(full_path + "/" + filename, resumable=False, mimetype=mime_type)
                        self.logger.debug(
                            "File " + full_path + "/" + filename + " is zero bytes. Non-resumable upload used.")

                    self.drive.service.files().create(body=file_metadata,
                                                      media_body=media,
                                                      fields='id').execute()
                    self.logger.info("Creating file " + full_path + "/" + filename)

                    if self.save_file is not None:
                        saved_files[full_path + '/' + filename] = datetime.datetime.utcfromtimestamp(
                            modified_date).__str__()

        if self.save_file is not None:
            self.save_file.seek(0)
            json.dump(saved_files, self.save_file)

    def update_folder(self, full_path):
        self.folder_id = self.locater.find(full_path=full_path)

    def rename_file(self, temp_name, filename, watch_path, notify):
        if os.path.isdir(watch_path + "/" + filename):
            notify.add_watch(bytes(watch_path + "/" + filename, encoding="utf-8"))

        self.folder_id = self.locater.find(full_path=watch_path)

        page_token = None
        response = self.drive.service.files().list(q="'%s' in parents" % self.folder_id
                                                     and "name='%s'" % temp_name,
                                                   spaces='drive',
                                                   fields='nextPageToken, files(id, name, parents)',
                                                   pageToken=page_token).execute()

        for file in response.get('files', []):
            if file.get('name') == temp_name and self.folder_id in file.get('parents'):
                file_metadata = {'name': filename}

                self.drive.service.files().update(fileId=file.get('id'), body=file_metadata,
                                                  fields='id').execute()
                self.logger.info("Renamed " + watch_path + "/" + temp_name + " to " + watch_path + "/" + filename)

    def multi_add(self, watch_path, notify=None):
        for (dir_path, dir_names, file_names) in walk(watch_path):
            for directory in dir_names:
                Update.update_folder(self, dir_path + "/" + directory)
                if notify is not None:
                    notify.add_watch(bytes(dir_path + "/" + directory, encoding="utf-8"))
            Update.update(self, full_path=dir_path, file_names=file_names)

    def move(self, temp_path, watch_path, filename):
        # Does it make sense for previous path to be updated here?
        self.folder_id = self.locater.find(full_path=temp_path)
        new_parent = self.locater.find(full_path=watch_path)
        self.folder_id = new_parent
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
                self.logger.info(
                    "Moved remote file " + temp_path + "/" + filename + " to " + watch_path + "/" + filename)
