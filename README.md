# Gravity Catalogue PWA

Mobile-first, desktop-compatible Django PWA with HTMX filtering and Tailwind styling.

## Features

- Installable PWA with manifest and service worker
- Responsive compact product list
- HTMX search and brand filtering without full-page reloads
- Separate Brand and Product database models
- Dynamic brand counts
- Excel price-list download
- Tap any model to open its dedicated specification and price page
- WhatsApp sharing includes model, variant, prices, colours and specifications
- Django Admin for products, prices and stock
- 12 verified Nothing variants and 5 supplied HEIM televisions

## Run on Windows

```powershell
cd "C:\Users\boo\Desktop\nthoing catloge\nothing-product-catalogue"
py -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
$env:NOTHING_ADMIN_PASSWORD = "your-secure-password"
python manage.py setup_admin
python manage.py runserver
```

Open http://127.0.0.1:8000/. Admin dashboard login is at http://127.0.0.1:8000/dashboard/login/.

## Deploy on Vercel

Vercel's function filesystem is not a persistent, writable database. Do not use
SQLite for a Vercel deployment. Create a hosted PostgreSQL database and add its
connection URL to the Vercel project as `DATABASE_URL` (or `POSTGRES_URL`).
Also configure:

- `DJANGO_SECRET_KEY`: a long, random secret used only by Django.
- `DJANGO_ALLOWED_HOSTS`: comma-separated hostnames, including the
  `.vercel.app` suffix and any custom domain.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: comma-separated origins including `https://`
  and any custom domain, if using one.

The app defaults to `DEBUG=False`; only set `DJANGO_DEBUG=true` for local
development. Run `python manage.py migrate` against the hosted database before
serving traffic. Local development continues to use `db.sqlite3`.

## Dashboard login

- Email: heimglobal@gmail.com
- Password: set via the NOTHING_ADMIN_PASSWORD environment variable before running `python manage.py setup_admin`
- The dashboard is protected behind Django authentication and staff-only access.

## Test on a phone

Connect the phone and computer to the same Wi-Fi. Run:

```powershell
python manage.py runserver 0.0.0.0:8000
```

Find the computer's IPv4 address with `ipconfig`, then open `http://YOUR-IP:8000/` on the phone. PWA installation requires HTTPS in production (localhost is exempt during development).
# nothing-cat
