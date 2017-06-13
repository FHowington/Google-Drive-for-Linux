from drive import Drive
import os
from notify import NotifyMonitor

gDrive = Drive()

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

baseFolder = 'OneDrivePractice'

os.chdir('/')

# If the base file is not located, the base file is created. Regardless,
# the baseID is assigned to the base folder

page_token = None
folder_id = None
baseLocated = False
while not baseLocated:
    response = gDrive.service.files().list(q="mimeType='application/vnd.google-apps.folder'"
                                             and "name='%s'" % baseFolder,
                                           spaces='drive',
                                           fields='nextPageToken, files(id, name)',
                                           pageToken=page_token).execute()

    for folder in response.get('files', []):
        if folder.get('name') == baseFolder:
            folder_id = folder['id']
            baseLocated = True
            break

    page_token = response.get('nextPageToken', None)
    if page_token is None:
        break

if not baseLocated:
    folder_metadata = {
        'name': baseFolder,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    print("Not located")

    folder = gDrive.service.files().create(body=folder_metadata,
                                           fields='id').execute()
    folder_id = folder.get('id')

print("Started Monitor")

notify = NotifyMonitor()
notify.monitor(folder_id, gDrive)
