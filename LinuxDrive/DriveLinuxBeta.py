#!/usr/bin/env python2
import FileManagement
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)
baseLocation = '/OneDrive'
baseFolder = 'OneDrive'
baseLocated = False

folder_metadata = {
    'title': baseFolder,
    # The mimetype defines this new file as a folder, so don't change this.
    'mimeType': 'application/vnd.google-apps.folder'
}
folder = drive.CreateFile(folder_metadata)

home = os.path.expanduser('~')

# If the base file is not located, the base file is created. Regardless,
# the baseID is assigned to the base folder
for file_list in drive.ListFile({'q': 'trashed=false', 'maxResults': 1000}):
    for folders in file_list:
        if folders['title'] == baseFolder:
            print('Found LinuxDrive id, it is:', folders['id'])
            baseLocated = True
            folder_title = folders['title']
            folder_id = folders['id']
            break
if not baseLocated:
    folder.Upload()
    folder_title = folder['title']
    folder_id = folder['id']
    print('title: %s, id: %s' % (folder_title, folder_id))

baseID = folder_id

# Walking through all subdirectories in specified folder
FileManagement.walkDir(baseID, home+baseLocation, baseFolder, drive)





