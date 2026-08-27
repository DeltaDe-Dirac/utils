#!/usr/bin/env python3
"""Mint or refresh gdrive/token.json using credentials.json.

Run this on a machine with a browser (run_local_server). After a valid
token.json exists, upload.py can refresh it without credentials.json.

If token.json is invalid (invalid_grant), delete it and run this again.
"""
from googleapiclient.errors import HttpError

from oauth import drive_service


def main():
    try:
        service = drive_service()
        results = service.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)"
        ).execute()
        items = results.get("files", [])
        if not items:
            print("No files found.")
            return
        print("Files found:")
        for item in items:
            print(f"{item['name']} ({item['id']})")
    except HttpError as exc:
        print(f"An error occurred: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
