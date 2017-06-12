import os
import datetime
import Locater
from apiclient import http
import magic

files = []
dirs = []


def update(base_id, full_path, filename, drive):
    print("Trying to update")
    folder_id = Locater.find(base_id, full_path, drive)

    file_located = False
    page_token = None
    response = drive.service.files().list(q="mimeType!='application/vnd.google-apps.folder'"
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
        print(mime_type)

        media = http.MediaFileUpload(full_path + "/" + filename, mimetype=mime_type)

        drive.service.files().create(body=file_metadata,
                                     media_body=media,
                                     fields='id').execute()

        print("Did not find file, creating it")


def update_folder(base_id, full_path, drive):
    Locater.find(base_id, full_path, drive)


def rename_file(base_id, temp_name, filename, watch_path, drive):
    print("Renaming folder")
    folder_id = Locater.find(base_id, watch_path, drive)

    page_token = None
    response = drive.service.files().list(q="'%s' in parents" % folder_id
                                            and "name='%s'" % temp_name,
                                          spaces='drive',
                                          fields='nextPageToken, files(id, name, parents)',
                                          pageToken=page_token).execute()

    for file in response.get('files', []):
        if file.get('name') == temp_name and folder_id in file.get('parents'):
            print("Older folder found")

            file_metadata = {'name': filename}

            drive.service.files().update(fileId=file.get('id'), body=file_metadata,
                                         fields='id').execute()
