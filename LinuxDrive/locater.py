import re


class Locater:
    def __init__(self, base_id, drive, base_path):
        self.drive = drive
        self.base_id = base_id
        self.base_name = re.split('/', base_path)[-1]

    def find(self, full_path, folder_id):
        folder_id = self.base_id
        path_location = 0

        # Trying to translate the dirpath into the path of Google Drive...
        path_delimited = re.split('/', full_path)
        # Determining where is the list of subfolders the basefolder is located, only happens once

        for i in range(len(path_delimited)):
            if path_delimited[i] == self.base_name:
                path_location = i
                break

        """If there are additional folders in the path, they are iterated through
        Because the current folder_ID is the base folder, we start by searching folder that have this as parent
        """

        for i in range(path_location + 1, len(path_delimited)):
            folder_located = False
            print("Searching for folder named", path_delimited[i], "with parent folder", folder_id)

            page_token = None

            response = self.drive.service.files().list(q="mimeType='application/vnd.google-apps.folder'"
                                                         and "'%s' in parents" % folder_id
                                                         and "name='%s'" % path_delimited[i],
                                                       spaces='drive',
                                                       fields='nextPageToken, files(id, name,parents)',
                                                       pageToken=page_token).execute()

            for folder in response.get('files', []):

                print(folder.get('name'))
                if folder.get('name') == path_delimited[i] and folder_id in folder.get('parents'):
                    folder_id = folder.get('id')
                    folder_located = True
                    print("Folder located")
                    break

            if not folder_located:
                print("Did not find folder, creating it")
                print(folder_id)
                folder_metadata = {
                    'parents': [folder_id],
                    'name': path_delimited[i],
                    'mimeType': 'application/vnd.google-apps.folder'
                }

                print('Parent should be' + folder_id)
                folder = self.drive.service.files().create(body=folder_metadata,
                                                           fields='name, id,parents').execute()
                folder_id = folder.get('id')
        return folder_id
