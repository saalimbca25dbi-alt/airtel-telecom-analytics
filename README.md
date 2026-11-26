# Airtel Telecom Analytics

A data analysis project, Semester 3 OJT: Airtel subscriber data.

## The question

We are losing nearly one subscriber in four. Which of the things we could do
about it actually works?

## Data

The full `airtel.db` is about 123 MB and is intentionally not stored in Git.
The small `data/airtel.db` file is only a practice database.

## Streamlit Cloud database setup

The app reads `data/raw/airtel.db` for local use. In Streamlit Cloud, it can
download the database at startup from a private Amazon S3 object.

1. In AWS, create a private S3 bucket with **Block Public Access** enabled and
   upload the full database as `airtel/airtel.db` (or choose another object
   key). Keep the object private; do not enable public access or public links.
2. Create an AWS identity whose policy allows only `s3:GetObject` for this
   database object (and no write or public-access permissions). Keep the
   access key and secret key private.
3. In Streamlit Community Cloud, open **My apps â†’ this app â†’ â‹® â†’ Settings â†’
   Secrets**. Paste the TOML below, replacing the bucket and credentials. These
   values belong only in the app's Secrets settings, never in GitHub or source
   files:

   ```toml
   [database]
   s3_bucket = "your-private-bucket"
   s3_key = "airtel/airtel.db"
   aws_region = "ap-south-1"
   aws_access_key_id = "YOUR_READ_ONLY_ACCESS_KEY"
   aws_secret_access_key = "YOUR_READ_ONLY_SECRET_KEY"
   ```

4. Click **Save**, then **Reboot app** from the app menu. Streamlit Cloud will
   download the private S3 copy into its temporary app storage and validate its
   required tables. Locally, the app continues to use `data/raw/airtel.db`.
   The small practice database is rejected because it lacks the required
   analysis tables.

Never commit AWS credentials or the full database to the repository. If the
credentials are rotated, update app Secrets and reboot it.

## Progress

- Step 0: environment, repository and data receipt

