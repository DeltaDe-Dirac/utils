import os
import argparse
import sys
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate():
    """Authenticates the user using OAuth2."""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("Error: 'credentials.json' file not found. Please download it from Google Cloud Console.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def get_file_size(local_path):
    """Returns the size of the local file in bytes."""
    try:
        return os.path.getsize(local_path)
    except OSError as e:
        print(f"Error checking local file size: {e}")
        sys.exit(1)

def check_drive_space(service, required_bytes):
    """Checks if Google Drive has enough space for the file."""
    try:
        # Drive API v3 returns quota data under the nested storageQuota object.
        about = service.about().get(
            fields='storageQuota(limit,usage)'
        ).execute()
        quota = about.get('storageQuota', {})

        limit = int(quota.get('limit', 0))
        usage = int(quota.get('usage', 0))

        # If limit is 0, it implies unlimited storage (typical for Enterprise/Edu)
        if limit == 0:
            return True, "Unlimited storage available."

        available = limit - usage

        if available >= required_bytes:
            return True, f"Space available: {available} bytes."
        else:
            return False, f"Insufficient space. Required: {required_bytes} bytes. Available: {available} bytes."

    except HttpError as error:
        print(f"Error checking Drive quota: {error}")
        sys.exit(1)

def find_folder_id(service, folder_identifier):
    """
    Finds the Folder ID.
    If the identifier looks like an ID (long alphanumeric), returns it directly.
    Otherwise, searches for the folder name in the root directory.
    """
    # Heuristic: If it contains no '/' and is long, assume it's an ID.
    # Note: This is a simplification. Real IDs are specific lengths.

    # Check if it's likely a name
    query = f"name='{folder_identifier}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = response.get('files', [])

    if not files:
        # Assume it might be an ID passed by user
        # We can try to get file metadata to verify
        try:
            # If folder_identifier is actually an ID, this works
            # If it's a name that didn't return results, we treat it as ID if user insisted
            # For this script, we will strictly search by name. If not found, we return error.
            # However, to support IDs:
            if len(folder_identifier) > 20: # Rough heuristic for IDs
                return folder_identifier
            print(f"Error: Folder '{folder_identifier}' not found.")
            sys.exit(1)
        except:
            print(f"Error: Folder '{folder_identifier}' not found.")
            sys.exit(1)

    # If multiple folders have same name, we pick the first one
    return files[0]['id']

def file_exists_in_drive(service, file_name, folder_id):
    """Checks if a file with the same name exists in the destination folder."""
    query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
    response = service.files().list(q=query, spaces='drive', fields='files(id)').execute()
    files = response.get('files', [])
    return len(files) > 0, files[0]['id'] if files else None

def upload_file(service, local_path, folder_id, override_flag):
    """Uploads the file to Google Drive."""
    file_name = os.path.basename(local_path)
    file_metadata = {'name': file_name, 'parents': [folder_id]}

    media = MediaFileUpload(local_path, resumable=True)

    try:
        # Check existence
        exists, existing_file_id = file_exists_in_drive(service, file_name, folder_id)

        if exists:
            if override_flag:
                print(f"File '{file_name}' exists. Overriding...")
                # Update existing file
                file = service.files().update(
                    fileId=existing_file_id,
                    media_body=media
                ).execute()
                return file.get('id')
            else:
                print(f"Error: File '{file_name}' already exists in destination. Use --override to overwrite.")
                sys.exit(1)
        else:
            print(f"Uploading '{file_name}'...")
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            return file.get('id')

    except HttpError as error:
        print(f"An error occurred during upload: {error}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Upload files to Google Drive")
    parser.add_argument("source", help="Path to the local source file")
    parser.add_argument("destination", help="Google Drive Folder Name or ID")
    parser.add_argument("--override", action="store_true", help="Overwrite if file exists in destination")
    parser.add_argument("--delete-source", action="store_true", help="Delete source file after successful upload")

    args = parser.parse_args()

    # 1. Validate Local Input
    if not os.path.exists(args.source):
        print(f"Error: Source path '{args.source}' does not exist.")
        sys.exit(1)

    if not os.path.isfile(args.source):
        print(f"Error: Source path '{args.source}' is not a file.")
        sys.exit(1)

    # 2. Authenticate
    print("Authenticating...")
    service = authenticate()

    # 3. Check Space
    file_size = get_file_size(args.source)
    space_ok, msg = check_drive_space(service, file_size)
    if not space_ok:
        print(f"Error: {msg}")
        sys.exit(1)
    print(f"Storage Check: {msg}")

    # 4. Resolve Destination
    folder_id = find_folder_id(service, args.destination)

    # 5. Upload
    file_id = upload_file(service, args.source, folder_id, args.override)

    # 6. Handle Success and Cleanup
    if file_id:
        print(f"Upload successful. File ID: {file_id}")
        if args.delete_source:
            try:
                os.remove(args.source)
                print(f"Source file '{args.source}' deleted as requested.")
            except OSError as e:
                print(f"Warning: Upload succeeded, but failed to delete source file: {e}")
    else:
        print("Error: Upload failed. Source file was NOT deleted.")
        sys.exit(1)

if __name__ == '__main__':
    main()
