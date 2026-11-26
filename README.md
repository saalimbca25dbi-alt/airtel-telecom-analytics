# Airtel Telecom Analytics

A data analysis project, Semester 3 OJT: Airtel subscriber data.

## The question

We are losing nearly one subscriber in four. Which of the things we could do
about it actually works?

## Data

The full `airtel.db` is about 123 MB and is intentionally not stored in Git.
The small `data/airtel.db` file is only a practice database.

## Streamlit Cloud database setup

The app reads `data/raw/airtel.db` locally. In Streamlit Cloud, it can download
the ZIP from a **restricted** Google Drive file and read `airtel.db` from it.
The Drive file must be shared with a read-only Google service account; do not
set it to â€œAnyone with the link.â€

1. In Google Cloud Console, create or select a project, enable the Google Drive
   API, then create a service account and download its JSON key.
2. Copy the service account's `client_email` from that JSON. In Google Drive,
   share `airtel_database.zip` with that email as **Viewer**. Keep General
   access set to **Restricted**.
3. In Streamlit Community Cloud, open **Manage app â†’ Settings â†’ Secrets** and
   add the file ID and the complete service account JSON. Paste the JSON between
   triple single quotes, preserving it exactly:

   ```toml
   [database]
   google_drive_file_id = "1EBviAsS6ebKOwJaMCoAWkzGN1CY5YBJN"
   google_service_account_json = '''PASTE THE COMPLETE SERVICE ACCOUNT JSON HERE'''
   ```

   Keep the JSON key only in Streamlit Secrets; never commit or send it in chat.
4. Click **Save**, then **Reboot app**. The app downloads the private ZIP to
   temporary storage, validates the database tables, and opens the database in
   read-only mode. The small practice database is rejected.

The app also supports private S3 credentials as an alternate source. Never
commit credentials or the full database to the repository.

## Progress

- Step 0: environment, repository and data receipt

