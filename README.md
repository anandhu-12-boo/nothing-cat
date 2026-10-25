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
cd gravity_pwa_catalogue
py -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_catalogue
$env:NOTHING_ADMIN_PASSWORD = "your-secure-password"
python manage.py setup_admin
python manage.py runserver
```

Open http://127.0.0.1:8000/. Admin dashboard login is at http://127.0.0.1:8000/dashboard/login/.

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
