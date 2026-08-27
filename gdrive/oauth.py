"""Shared Google Drive OAuth for gdrive scripts.

Keep SCOPES identical for generate_token.py and upload.py. A token minted
with a narrower scope cannot upload. If you change SCOPES, delete token.json
and run generate_token.py again.
"""
from __future__ import annotations

import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Full Drive access — required by upload.py. Not metadata-readonly.
SCOPES = ["https://www.googleapis.com/auth/drive"]

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


def get_credentials():
    """Load token.json, refresh if needed, or run the local-browser OAuth flow."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(
                    f"Error: '{CREDENTIALS_FILE}' not found. "
                    "Download an OAuth 2.0 Desktop client secret from Google Cloud Console."
                )
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        print(f"Wrote {TOKEN_FILE}")

    return creds


def drive_service():
    return build("drive", "v3", credentials=get_credentials())
