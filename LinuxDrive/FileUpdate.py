import os
import re
import datetime

files = []
dirs = []


def update(baseID, fullPath, filename, drive):
    folder_id = baseID

    # Trying to translate the dirpath into the path of Google Drive...
    pathDelimited = re.split('/', fullPath)
    # Determining where is the list of subfolders the basefolder is located, only happens once

    for i in range(len(pathDelimited)):
        if pathDelimited[i] == "OneDrive":
            pathLocation = i
            break

        # If there are additional folders in the path, they are iterated through
        # Because the current folder_ID is the base folder, we start by searching folder that have this as parent
    for i in range(pathLocation + 1, len(pathDelimited)):
        baseLocated = False
        print("Searching for folder named", pathDelimited[i], "with parent folder", folder_id)

        for file_list in drive.ListFile({'q': "'" + folder_id + "'" + " in parents", 'maxResults': 1000}):
            for folders in file_list:
                print("Found folder named", folders['title'])
                if folders['title'] == pathDelimited[i]:
                    # print('Found base id, it is:', folders['id'])
                    baseLocated = True
                    folder_id = folders['id']
                    break

            if not baseLocated:
                print("Did not find folder, creating it")
                folder_metadata = {
                    'title': pathDelimited[i],
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [{"kind": "drive#fileLink", "id": folder_id}]
                }
                print('Parent should be' + folder_id)
                folder = drive.CreateFile(folder_metadata)
                folder.Upload()
                folder_title = folder['title']
                folder_id = folder['id']
                print('title: %s, id: %s' % (folder_title, folder_id))


    fileLocated = False
    for file_list in drive.ListFile({'q': "'" + folder_id + "'" + " in parents", 'maxResults': 1000}):
        for filesContained in file_list:
            if filesContained['title'] == filename:
                # Getting time of modification of all files in path
                modifiedDate = os.path.getmtime(fullPath + '/' + filename)

                # Converting googles weird datetime zulu syntax into UTC syntax
                datetime_Existing = datetime.datetime.strptime(filesContained['modifiedDate'].replace("T", " ")[:19],
                                                               '%Y-%m-%d %H:%M:%S')

                if datetime.datetime.utcfromtimestamp(modifiedDate) > datetime_Existing:
                    fileToRemove = drive.CreateFile({'id': filesContained['id']})
                    fileToRemove.Delete()
                    print("More recent version of file found. File removed.")
                    break

                else:
                    print("Found file in folder already id, it is: ", filesContained['id'])
                    fileLocated = True
                    break



    if not fileLocated:
        print(filename)
        print("Did not find file, creating it")
        print([{"kind": "drive#fileLink", "id": folder_id}])

        f = drive.CreateFile({"title": filename, "parents": [{"kind": "drive#fileLink", "id": folder_id}]})
        f.SetContentFile(os.path.join(fullPath, filename))
        f.Upload()

def update_folder(baseID, fullPath, drive):
    print("Updating folder")

    folder_id = baseID

    # Trying to translate the dirpath into the path of Google Drive...
    pathDelimited = re.split('/', fullPath)
    # Determining where is the list of subfolders the basefolder is located, only happens once

    for i in range(len(pathDelimited)):
        if pathDelimited[i] == "OneDrive":
            pathLocation = i
            break

            # If there are additional folders in the path, they are iterated through
            # Because the current folder_ID is the base folder, we start by searching folder that have this as parent
    for i in range(pathLocation + 1, len(pathDelimited)):
        baseLocated = False
        print("Searching for folder named", pathDelimited[i], "with parent folder", folder_id)

        for file_list in drive.ListFile({'q': "'" + folder_id + "'" + " in parents", 'maxResults': 1000}):
            for folders in file_list:
                print("Found folder named", folders['title'])
                if folders['title'] == pathDelimited[i]:
                    # print('Found base id, it is:', folders['id'])
                    baseLocated = True
                    folder_id = folders['id']
                    break

            if not baseLocated:
                print("Did not find folder, creating it")
                folder_metadata = {
                    'title': pathDelimited[i],
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [{"kind": "drive#fileLink", "id": folder_id}]
                }
                print('Parent should be' + folder_id)
                folder = drive.CreateFile(folder_metadata)
                folder.Upload()
                folder_title = folder['title']
                folder_id = folder['id']
                print('title: %s, id: %s' % (folder_title, folder_id))