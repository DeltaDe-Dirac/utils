# utils

A collection of utility scripts for common tasks.

---

## ☁️ `gdrive` - Google Drive Uploader

Upload a local file to a Google Drive folder by name or folder ID. The script authenticates with OAuth2, checks that Drive has enough space, and optionally overwrites an existing file or deletes the local source after a successful upload.

### ✨ Features

- **OAuth2 login** - Browser consent on first run; tokens saved in `token.json` for later runs
- **Folder by name or ID** - Destination can be a Drive folder name or a folder ID
- **Quota check** - Refuses to upload when Drive does not have enough free space
- **Resumable upload** - Uses the Drive API resumable media upload
- **Overwrite control** - Existing same-name files are rejected unless `--override` is set
- **Optional source cleanup** - `--delete-source` removes the local file only after a successful upload

### 🚀 Quick Start

#### 1. Install dependencies

```bash
cd gdrive
pip install -r requirements.txt
```

#### 2. Add Google Cloud credentials

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the **Google Drive API**.
3. Create an **OAuth 2.0 Client ID** (Desktop app).
4. Download the client secret file and save it as `gdrive/credentials.json`.

Do not commit `credentials.json` or `token.json`. They are secrets.

#### 3. Generate `token.json` (needs a browser)

Run this **on a machine with a browser**, from `gdrive/`:

```bash
cd gdrive
python generate_token.py
```

This opens Google sign-in (`run_local_server`), writes `token.json`, and lists 10 Drive files as a smoke test.

- **Keep `token.json`.** That is the reusable login (refresh). Copy it to the runtime `gdrive/` if you authorized on another machine.
- **`credentials.json` is only needed to mint or replace `token.json`** (first run, or after `invalid_grant`). You can omit it on later uploads once `token.json` refreshes cleanly.
- Scope is **full Drive** (`https://www.googleapis.com/auth/drive`), same as `upload.py`. A metadata-readonly token cannot upload. If you change scopes, delete `token.json` and run `generate_token.py` again.

#### 4. Upload a file

**By folder name:**
```bash
python gdrive/upload.py /path/to/file.jpg MyFolder
```

**By folder ID:**
```bash
python gdrive/upload.py /path/to/file.jpg 1aBcDeFgHiJkLmNoPqRsTuVwXyZ
```

**Overwrite if the same name already exists:**
```bash
python gdrive/upload.py /path/to/file.jpg MyFolder --override
```

**Delete the local file after a successful upload:**
```bash
python gdrive/upload.py /path/to/file.jpg MyFolder --delete-source
```

If `token.json` is missing or cannot refresh, run `python generate_token.py` instead of hoping `upload.py` can complete a headless browser flow.

### 📖 Usage

```
usage: upload.py [-h] [--override] [--delete-source] source destination

Upload files to Google Drive

positional arguments:
  source           Path to the local source file
  destination      Google Drive folder name or ID

optional arguments:
  -h, --help       Show this help message and exit
  --override       Overwrite if a file with the same name exists in destination
  --delete-source  Delete the source file after a successful upload
```

### 📁 Output

- Prints the new or updated Drive **file ID** on success
- Does **not** delete the local source if the upload fails
- `--override` updates the existing Drive file; it does not create a second copy

### ⚠️ Important Notes

- **File only** - The source path must be an existing file, not a directory
- **Folder lookup** - Names are searched across Drive; if several folders share a name, the first match is used. Prefer a folder ID when names collide
- **ID heuristic** - If no folder name matches and the destination is longer than 20 characters, it is treated as a folder ID
- **OAuth scope** - Requests full Drive access (`https://www.googleapis.com/auth/drive`). Delete `token.json` after changing scopes
- **Working directory** - `credentials.json` and `token.json` are resolved relative to the current working directory, not the script path. Run from `gdrive/` or pass paths after `cd gdrive`
- **Unlimited quota** - A Drive quota limit of `0` is treated as unlimited (typical for some Workspace accounts)

---

## 🛠 Development

### Project Structure

```
utils/
├── gdrive/
│   ├── generate_token.py  # Browser OAuth; writes token.json
│   ├── oauth.py           # Shared scopes + credential load/refresh
│   ├── upload.py          # Upload CLI
│   ├── requirements.txt   # Google API client libraries
│   ├── credentials.json   # OAuth client secret (local only)
│   └── token.json         # User tokens (local only)
└── README.md              # This file
```

### Dependencies

```
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
```

---

## 📄 License

Apache License 2.0 - See [LICENSE](../LICENSE) for details.

---

## 🙏 Credits

- **Google Drive API v3** - Upload, quota, and folder lookup
- **google-auth-oauthlib** - Installed-app OAuth flow
