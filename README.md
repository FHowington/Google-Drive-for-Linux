# Google-Drive-for-Linux
This is a python 3 based project that utilizes pyDrive and iNotify to maintain synchronization between a local directory
and a folder on the user's google drive.

Goals for upcoming updates:
May eventually remove usage of pyDrive. There are issues with the "resumable" uploading that might be mitigated.
Need to make a command line and potentially GUI interface for setting up new users.

Streamline updloading of content. This should include use of iNotify to keep track of recently modified files
Also would like to use something other then cron job to repeatedly execute script. May also do this through iNotify
