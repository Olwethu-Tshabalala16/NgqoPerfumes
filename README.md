# NqoPerfumes

A Django-based digital perfume catalogue built from a real family business problem.

## Why I Built This

Before building this project, my mother ran a small perfume side business using printed catalogues. She would receive or share a catalogue, show customers the available perfumes, and use that catalogue to take orders.

When I started learning web development, I realised I could solve a practical problem for her: instead of repeatedly sharing a physical catalogue or individual product pictures, she could share a single link to an online catalogue.

Customers can open the catalogue, browse the available perfumes, view product information and images, and use the website as a central reference when deciding what they want to order.

This project is therefore more than a practice e-commerce application. It started from a real problem in my own environment and became one of the projects through which I learned how a web application can be connected to cloud infrastructure.

## What the Application Does

- Displays a searchable fragrance catalogue in a standalone frontend.
- Exposes product names, descriptions, prices, stock quantities and image URLs through a JSON API.
- Allows product records and images to be managed through Django Admin.
- Uses Supabase PostgreSQL for persistent product data.
- Uses Supabase Storage's S3-compatible API for persistent product images.
- Includes two-factor authentication support for the admin area.
- Serves the backend with Gunicorn and backend static assets with WhiteNoise.
## Architecture

The customer-facing frontend and Django backend are separate applications. The frontend uses plain HTML, CSS and JavaScript and communicates with the backend over HTTP using JSON.

```text
frontend/ (HTML, CSS, JavaScript)
          |
          | GET /api/products/ (JSON)
          v
Django backend (Python)
  |                   |
  v                   v
Supabase           Supabase Storage
PostgreSQL         Product images
```

- `frontend/` contains the customer-facing catalogue and does not contain database or storage credentials.
- `nqoperfumes/myshop/` contains Django settings, the product model, API endpoints and Django Admin.
- `GET /api/products/` returns the public catalogue as JSON.
- `GET /api/health/` provides a lightweight health check.
- Supabase PostgreSQL stores structured product records.
- Supabase Storage stores product images through `django-storages` and `boto3`.
- CORS is restricted to origins explicitly configured with `CORS_ALLOWED_ORIGINS`.
## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| Django 6.1 | Backend framework, ORM and administration |
| Django JSON views | Lightweight read-only catalogue API |
| HTML, CSS and JavaScript | Independent customer-facing frontend |
| PostgreSQL | Persistent application database |
| Supabase | Managed PostgreSQL and object storage platform |
| django-storages / boto3 | S3-compatible product image storage |
| django-cors-headers | Configurable cross-origin access for the frontend |
| python-dotenv | Load local environment variables from `.env` |
| Pillow | Image processing |
| Gunicorn | WSGI application server |
| WhiteNoise | Backend static-file serving |
| Django Admin / Admin 2FA | Product management and additional authentication security |
## Supabase PostgreSQL

The application uses the `DATABASE_URL` environment variable to connect Django's ORM to the Supabase PostgreSQL database.

For a serverless deployment such as Vercel, use the Supabase **transaction pooler** connection string. Supabase documents transaction pooling for serverless functions and shared session pooling for IPv4-compatible persistent connections.

The database password must remain in environment variables and must never be committed to Git.

## Supabase Storage

Create a public file bucket named:

```text
product-images
```

The application uses Supabase Storage's S3-compatible endpoint.

Required environment variables:

```env
SUPABASE_URL=https://PROJECT_REF.supabase.co
SUPABASE_STORAGE_BUCKET=product-images
SUPABASE_STORAGE_ENDPOINT=https://PROJECT_REF.storage.supabase.co/storage/v1/s3
SUPABASE_STORAGE_REGION=PROJECT_REGION
SUPABASE_STORAGE_ACCESS_KEY_ID=your-storage-s3-access-key
SUPABASE_STORAGE_SECRET_ACCESS_KEY=your-storage-s3-secret
```

The S3 access key and secret are **server-side credentials**. They must only be configured in local environment variables or the deployment platform's secret/environment-variable settings.

The application generates public image URLs in the following form:

```text
https://PROJECT_REF.supabase.co/storage/v1/object/public/product-images/products/...
```

## Environment Configuration

Copy `.env.example` to a local `.env` file and replace the placeholders with your actual Supabase and Django configuration.

Required configuration includes:

```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_URL=your-supabase-postgresql-connection-string

SUPABASE_URL=https://PROJECT_REF.supabase.co
SUPABASE_STORAGE_BUCKET=product-images
SUPABASE_STORAGE_ENDPOINT=https://PROJECT_REF.storage.supabase.co/storage/v1/s3
SUPABASE_STORAGE_REGION=your-project-region
SUPABASE_STORAGE_ACCESS_KEY_ID=your-storage-access-key
SUPABASE_STORAGE_SECRET_ACCESS_KEY=your-storage-secret

ADMIN_2FA_EMAIL_SENDER=admin@example.com
```

Never commit `.env`.

## Configure NqoPerfumes With Your Own Supabase Project

Follow this section when setting up your own copy of NqoPerfumes. You need to configure **two separate Supabase services**: PostgreSQL for product data and Storage for product images. Creating a Supabase project alone does not configure the Django application automatically.

### 1. Create a Supabase project

1. Sign in at [Supabase](https://supabase.com/) and create a new project.
2. Choose a project name and region.
3. Set a strong database password and store it securely.
4. Wait until the project has finished provisioning.

Keep the database password available for the database connection setup. Do not put it in source code or commit it to Git.

### 2. Get the PostgreSQL connection string

1. Open your Supabase project and select **Connect** (or the database connection settings).
2. Copy a PostgreSQL connection string suitable for your hosting environment.
3. For a serverless deployment, use the **transaction pooler** connection details recommended by Supabase. For a persistent local connection, use a connection option supported by your network and hosting environment.
4. Replace the placeholders in `DATABASE_URL` with the actual connection details.

The example in `.env.example` uses this general format:

```env
DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@POOLER_HOST:5432/postgres
```

This is a template, not a working connection string. Use the exact host, port, username, and database name provided by Supabase. URL-encode special characters in the password if required by the connection-string format.

### 3. Create the product image bucket

1. In your Supabase project, open **Storage**.
2. Create a bucket named `product-images`.
3. Configure it as a **public bucket** if you want product images to load using the public URLs generated by this project.
4. In the Supabase Storage S3 connection settings, obtain an S3 access key and secret for server-side use.

The application stores product images under the `products/` path within this bucket. The bucket name must match `SUPABASE_STORAGE_BUCKET` in your environment.

The bucket being public allows visitors to download product images; it does **not** mean that S3 secret credentials should be public. Keep upload credentials on the Django server only. Do not put them in frontend JavaScript or commit them to GitHub.

### 4. Configure your local environment

From the repository root, copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` and replace the example values with values from your own Supabase project. The important variables are:

| Variable | Where to get it / what it controls |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string from Supabase's **Connect** or database connection settings. |
| `SUPABASE_URL` | Project URL shown in the Supabase project settings; it normally has the form `https://PROJECT_REF.supabase.co`. |
| `SUPABASE_STORAGE_BUCKET` | The Storage bucket name; use `product-images` unless you also change the application configuration. |
| `SUPABASE_STORAGE_ENDPOINT` | The S3-compatible Storage endpoint for your project, normally `https://PROJECT_REF.storage.supabase.co/storage/v1/s3`. Use the endpoint shown by Supabase if it differs. |
| `SUPABASE_STORAGE_REGION` | The region value required by the S3-compatible Storage configuration for your project. |
| `SUPABASE_STORAGE_ACCESS_KEY_ID` | The S3 access key generated in Supabase Storage settings. |
| `SUPABASE_STORAGE_SECRET_ACCESS_KEY` | The secret paired with that S3 access key. Treat it as a password. |
| `DJANGO_SECRET_KEY` | A new, unique Django secret key for your environment. Do not reuse a public example value in production. |
| `DJANGO_DEBUG` | Use `True` for local development only; set it to `False` in production. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames allowed to serve the application. Set these to your actual local or deployment hosts. |
| `CSRF_TRUSTED_ORIGINS` | Include the full trusted origins required by your deployment, including the scheme such as `https://`, if applicable. |
| `ADMIN_2FA_EMAIL_SENDER` | The sender address used by the admin two-factor-authentication configuration. Configure any required email settings for your deployment as well. |

The `.env.example` file documents the variable names expected by this repository. Keep your real credentials in `.env` or in your hosting provider's environment-variable settings.

**Never commit `.env` or paste real database passwords and S3 secrets into issues, pull requests, logs, screenshots, or frontend code.** If a secret is accidentally published, revoke or rotate it in Supabase.

### 5. Install dependencies and apply migrations

From the Django project directory shown in [Running Locally](#running-locally), install the dependencies and make sure the environment variables are available to Django. Then run:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Migrations create the database schema in your configured Supabase PostgreSQL database. They do **not** copy products or images from another Supabase project. The superuser command creates an administrator for your own installation.

### 6. Test database and image storage

Start the application locally:

```bash
python manage.py runserver
```

Use Django Admin to create a test product and upload an image. Confirm that:

- The product record is saved and remains available after restarting the server.
- The uploaded image appears in the `product-images` bucket under `products/`.
- The image loads on the public catalogue.
- No credentials appear in the browser, page source, or Git-tracked files.

If database access works but image uploads fail, check the Storage endpoint, region, bucket name, and S3 access credentials. If uploads work but images do not display, verify that the bucket is public and that the generated public URL points to your own project and bucket.

### 7. Moving from another Supabase project

Changing the environment variables connects NqoPerfumes to a different backend; it does **not** migrate existing data. If you are moving an existing catalogue, export and import the database records and separately copy the image files to the new bucket. Check image paths and URLs after migration.

## Running Locally

### 1. Install and configure the backend

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your own Django secret, Supabase PostgreSQL connection string, and Supabase Storage credentials. Do not commit the real `.env` file.

Start the Django backend:

```bash
cd nqoperfumes/myshop
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The backend API is available at:

- `http://127.0.0.1:8000/api/products/` — product catalogue JSON.
- `http://127.0.0.1:8000/api/health/` — health check.
- `http://127.0.0.1:8000/admin/` — product administration.

For local development, the default `.env.example` CORS origins allow a frontend served on port 5500.

### 2. Run the separate frontend

Open a second terminal from the repository root:

```bash
cd frontend
python -m http.server 5500
```

Open `http://127.0.0.1:5500` in your browser. The frontend's `config.js` points to the local Django API by default. When deploying, change `API_BASE_URL` to the public backend origin, or use an empty string when frontend and backend share the same origin. Add the deployed frontend origin to `CORS_ALLOWED_ORIGINS` on the backend.

### 3. Run the backend tests

From `nqoperfumes/myshop` with the virtual environment activated:

```bash
python manage.py check
python manage.py test
```

The GitHub Actions workflow runs Django checks, automated backend tests and frontend JavaScript syntax checks on pushes and pull requests.
## Data Model

The core application uses a Product model containing:

- `name`
- `description`
- `price`
- `stock`
- `image`
- `created_at`
- `updated_at`

The `image` field remains a normal Django ImageField. Django's storage abstraction determines where the file is physically stored, so application code does not need to manually upload files to Supabase.

The model also exposes an `is_in_stock()` method so the application can determine whether a product currently has available stock.

## Security and Configuration

Sensitive configuration belongs in environment variables rather than source code.

The Supabase Storage S3 credentials provide server-side access and must never be exposed to browser-side JavaScript or committed to Git.

The public product image bucket is intentionally public for catalogue delivery. Public access applies to downloads; administrative uploads and changes remain server-side operations authenticated by the storage credentials.

## What I Learned

This project helped me understand the relationship between application development and cloud infrastructure.

I learned that building a web application is not only about writing frontend and backend code. The application also needs somewhere appropriate to persist structured data, somewhere appropriate to store files, and a reliable way to connect those services.

Using Supabase gives this project a managed PostgreSQL database and persistent object storage while keeping the Django application independent from a local filesystem.

The project also demonstrates an important software-engineering principle: Django's storage abstraction allows the application model to remain stable while the underlying storage provider changes.

## Project Direction

The project began as a simple solution to help my mother's perfume business move away from a physical catalogue and toward a shareable digital catalogue.

As I continue developing it, the project can evolve beyond a basic product listing into a more complete commerce system, including stronger inventory management, order workflows, customer interactions and cloud-native infrastructure.

The main lesson remains simple: **software should solve a real problem first, and the technology should support that problem.**
