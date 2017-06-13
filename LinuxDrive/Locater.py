import re


def find(base_id, full_path, gDrive, notify):
    folder_id = base_id

    # Trying to translate the dirpath into the path of Google Drive...
    pathDelimited = re.split('/', full_path)
    # Determining where is the list of subfolders the basefolder is located, only happens once

    for i in range(len(pathDelimited)):
        if pathDelimited[i] == "OneDrive":
            path_location = i
            break

    # If there are additional folders in the path, they are iterated through
    # Because the current folder_ID is the base folder, we start by searching folder that have this as parent
    for i in range(path_location + 1, len(pathDelimited)):
        folder_located = False
        print("Searching for folder named", pathDelimited[i], "with parent folder", folder_id)

        page_token = None

        response = gDrive.service.files().list(q="mimeType='application/vnd.google-apps.folder'"
                                                 and "'%s' in parents" % folder_id
                                                 and "name='%s'" % pathDelimited[i],
                                               spaces='drive',
                                               fields='nextPageToken, files(id, name,parents)',
                                               pageToken=page_token).execute()

        for folder in response.get('files', []):

            print(folder.get('name'))
            if folder.get('name') == pathDelimited[i] and folder_id in folder.get('parents'):
                folder_id = folder.get('id')
                folder_located = True
                print("Folder located")
                break

        if not folder_located:
            print("Did not find folder, creating it")
            print(folder_id)
            folder_metadata = {
                'parents': [folder_id],
                'name': pathDelimited[i],
                'mimeType': 'application/vnd.google-apps.folder'
            }

            notify.add_watch(bytes(full_path, encoding="utf-8"))

            print('Parent should be' + folder_id)
            folder = gDrive.service.files().create(body=folder_metadata,
                                                   fields='name, id,parents').execute()
            folder_id = folder.get('id')
    return folder_id
