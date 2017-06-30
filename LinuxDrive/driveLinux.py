import os
import json
import sys
from drive import Drive
from notify import NotifyMonitor

parameters_file = "parameters.json"


def main():
    os.chdir(os.path.dirname(__file__))

    if __name__ == '__main__':
        if len(sys.argv) > 1:
            if sys.argv[1] == '--s':
                create_parameters()

    try:
        with open(parameters_file) as f_obj:
            parameters = json.load(f_obj)

    except FileNotFoundError:
        print(os.getcwd())
        create_parameters()
        with open(parameters_file) as f_obj:
            parameters = json.load(f_obj)

    drive = Drive()

    os.chdir('/')

    base_folder = parameters['drive_folder_name']
    base_path = parameters['path_to_folder']

    # If the base file is not located, the base file is created. Regardless,
    # the baseID is assigned to the base folder

    page_token = None
    folder_id = None
    base_located = False
    while not base_located:
        response = drive.service.files().list(q="mimeType='application/vnd.google-apps.folder'"
                                                and "name='%s'" % base_folder,
                                              spaces='drive',
                                              fields='nextPageToken, files(id, name)',
                                              pageToken=page_token).execute()

        for folder in response.get('files', []):
            if folder.get('name') == base_folder:
                folder_id = folder['id']
                base_located = True
                break

        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

    if not base_located:
        folder_metadata = {
            'name': base_folder,
            'mimeType': 'application/vnd.google-apps.folder'}

        print("Base folder not located, creating base folder " + base_folder + " on Google Drive")
        folder = drive.service.files().create(body=folder_metadata,
                                              fields='id').execute()
        folder_id = folder.get('id')

    print("Started Monitor")
    notify = NotifyMonitor(base_folder=base_folder, base_path=base_path, base_id=folder_id, drive=drive)
    notify.monitor(parameters['update_on_start'])


def create_parameters():
    parameters = {}
    parameters['drive_folder_name'] = input("What is the name of the remote folder (On the Google Drive)? ")
    parameters['path_to_folder'] = input(
        "What is the absolute path to the local folder to monitor? (ex: /home/forbes/gDrive)? ")
    update_on_start = input(
        "Do you want to perform a full scan of the directory, uploading any changes, \n when the program start? Note "
        "that this is an intensive process (y/n)")
    if update_on_start == 'y':
        parameters['update_on_start'] = True
    else:
        parameters['update_on_start'] = False
    with open(parameters_file, 'w') as f_obj:
        json.dump(parameters, f_obj)


if __name__ == '__main__':
    main()
