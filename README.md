# Nothing Product Catalogue

Django product catalogue with public product browsing, search and details, a
staff-only product dashboard, image/document uploads, and Excel export.

## Local development (Windows)

```powershell
cd "C:\Users\boo\Desktop\nthoing catloge\nothing-product-catalogue"
py -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The local default database is `db.sqlite3`. To create the dashboard admin for
the first time, run `python manage.py setup_admin` and enter a password when
prompted. The dashboard email is `heimglobal@gmail.com`.

Open the catalogue at http://127.0.0.1:8000/ and the dashboard at
http://127.0.0.1:8000/dashboard/login/.

## Deploy on Render

The root `render.yaml` is a Blueprint for this project. It configures the
verified WSGI application (`config.wsgi:application`), a Render PostgreSQL
database, static collection, migrations and S3-compatible storage for media.
The Blueprint selects paid Render plans for the web service and database.
Review current Render pricing and the storage provider's pricing before
provisioning resources.

### Deploy steps

1. Push this project to the GitHub repository you want Render to deploy. In
   Render, choose **New + → Blueprint** and connect that repository.
2. Select the repository root as the Blueprint root directory. Render reads
   `render.yaml` and creates the web service and database. Its `sync: false`
   media settings must be entered in the service's Environment page before the
   application can start.
3. Create a bucket in an S3-compatible object-storage service (for example,
   Amazon S3 or Cloudflare R2). Configure it to serve the catalogue's uploaded
   images and public product documents. Do not put private files in this
   public-media bucket.
4. Set the storage environment variables in Render. For Cloudflare R2,
   use the S3 API endpoint, region `auto`, an R2 access key/secret, and the
   bucket's public custom domain. For AWS S3, use the bucket's region and a
   public domain/CloudFront URL as appropriate.
5. Review and approve the Blueprint. Render provisions PostgreSQL and the web
   service; the build installs packages, collects static files and applies
   migrations. The first web-service start will fail until the media variables
   are set. After setting them, manually redeploy. The start command is
   `gunicorn config.wsgi:application`.
6. After the first successful deploy, open the Render Shell for the web
   service and create the administrator as described below.
7. Add any custom domain to `DJANGO_ALLOWED_HOSTS` as a comma-separated host
   and to `DJANGO_CSRF_TRUSTED_ORIGINS` as a full `https://` origin. The
   default Render hostname is detected automatically.

Equivalent service commands, if configuring Render manually:

```text
Build: pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
Start: gunicorn config.wsgi:application
```

Use the PostgreSQL **internal** connection URL from the same Render region for
`DATABASE_URL`. Do not copy database credentials into source files.

### Environment variables

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Render PostgreSQL connection URL. The Blueprint connects it automatically. |
| `DJANGO_SECRET_KEY` | Django signing secret. Render generates a value in the Blueprint. Keep it stable and private. |
| `DJANGO_DEBUG` | Set to `false` in production. |
| `DJANGO_ALLOWED_HOSTS` | Optional comma-separated hostnames for custom domains. Render's service hostname is added automatically. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Optional comma-separated full origins, e.g. `https://catalogue.example.com`, for custom domains. |
| `AWS_STORAGE_BUCKET_NAME` | Required bucket for uploaded product images and documents in hosted deployments. |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Private credentials for the media bucket. Store only in Render environment settings. |
| `AWS_S3_ENDPOINT_URL` | S3 API endpoint; required by providers such as R2. |
| `AWS_S3_REGION_NAME` | Bucket region; use `auto` for R2. |
| `AWS_S3_CUSTOM_DOMAIN` | Optional public hostname for media URLs, without `https://`. |
| `MEDIA_ROOT` | Local filesystem upload directory. Only relevant when using local filesystem storage. |

The app defaults to SQLite and local media storage outside Render/Vercel. On
Render, startup intentionally fails if the persistent database, secret, or
media bucket is missing rather than silently using ephemeral storage.

### Static files and uploaded media

WhiteNoise serves collected static assets (CSS, JavaScript and icons). The
Render build runs `collectstatic`; uploaded product images and brand documents
are Django media files and are stored in the configured S3-compatible bucket.
Keep the bucket available and public-read only for files intended to appear in
the catalogue. Back up the bucket independently. Do not use the web service's
ephemeral filesystem for uploads.

## Administrator account

The Blueprint does not create or reset an administrator automatically. In the
Render Shell, run:

```text
python manage.py setup_admin
```

For a new admin, the command securely prompts for a password. Re-running it
does not change an existing password. To explicitly reset the password, run
`python manage.py setup_admin --reset-password`; the command prompts unless
`NOTHING_ADMIN_PASSWORD` is set in the shell environment. Never save an admin
password in the Blueprint or commit it to Git.

## Existing SQLite data

The local `db.sqlite3` and uploaded files are ignored by Git and are not copied
to Render. A fresh PostgreSQL database is populated with the schema by
`migrate`, not with local product rows.

Before transferring data, make a separate backup of the SQLite database and
media directory. A Django fixture can be exported locally with:

```powershell
python manage.py dumpdata catalogue --indent 2 --output catalogue-data.json
```

Do not commit that fixture: it contains catalogue data and media paths. This
project's data migration creates default categories, so review the fixture and
the target database before importing; a blind `loaddata` may conflict with
those rows. For a populated catalogue, migrate categories by slug and import
related brands, models, variants and documents with their foreign keys mapped
to the target records. Test the import on a separate empty PostgreSQL database
first; do not import over live production records. Upload/copy the referenced
media files to the configured bucket separately, preserving their relative
paths.

## Checks

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py collectstatic --noinput
python manage.py test
```

## Troubleshooting

- **Build fails installing dependencies:** check the Render build log and
  confirm it is using the repository root, Python 3.12.14 and
  `requirements.txt`.
- **Database connection or migration failure:** verify `DATABASE_URL` is
  linked to the Render PostgreSQL resource, that both resources are in the
  same region, and that the database is available.
- **Static files return 404:** confirm the build completed `collectstatic`,
  WhiteNoise is enabled, and the request uses `/static/`.
- **Uploaded images/documents return 404:** check the bucket name, S3 endpoint,
  credentials, public media domain and bucket read policy. Media is not served
  from Django's static-file handler.
- **`DisallowedHost`:** add the requested hostname to `DJANGO_ALLOWED_HOSTS`
  without a scheme.
- **CSRF verification failure:** add the exact HTTPS origin, including scheme,
  to `DJANGO_CSRF_TRUSTED_ORIGINS`.
- **HTTP 500:** inspect Render application logs. Confirm `DJANGO_SECRET_KEY`,
  `DATABASE_URL`, and all required media-bucket variables are configured, then
  check that migrations completed.

## Git

Check `git status` before committing deployment files. Commit only the source
and configuration changes; do not commit `.env` files, SQLite databases,
fixtures, uploads or credentials. Push to the branch connected to the intended
Render service.
