# NqoPerfumes

A Django-based digital perfume catalogue built from a real family business problem.

## Why I Built This

Before building this project, my mother ran a small perfume side business using printed catalogues. She would receive or share a catalogue, show customers the available perfumes, and use that catalogue to take orders.

When I started learning web development, I realised I could solve a practical problem for her: instead of repeatedly sharing a physical catalogue or individual product pictures, she could share a single link to an online catalogue.

Customers can open the catalogue, browse the available perfumes, view product information and images, and use the website as a central reference when deciding what they want to order.

This project is therefore more than a practice e-commerce application. It started from a real problem in my own environment and became one of the projects through which I learned how a web application can be connected to cloud infrastructure.

## What the Application Does

- Displays a catalogue of perfumes.
- Stores product names, descriptions, prices and stock quantities.
- Allows product images to be uploaded through the Django admin.
- Provides an administrative interface for managing catalogue products.
- Provides stock-aware product information.
- Uses Supabase PostgreSQL for persistent product data.
- Uses Supabase Storage for persistent product images.
- Uses Django's authentication and administrative tooling.
- Includes two-factor authentication support for the admin area.
- Serves the application with Gunicorn and static assets with WhiteNoise.

## Architecture

```text
                         Customer
                            |
                            v
                  +-------------------+
                  |  Django Web App   |
                  |   Python / HTML   |
                  +---------+---------+
                            |
              +-------------+-------------+
              |                           |
              v                           v
       Supabase PostgreSQL         Supabase Storage
       Product metadata            Product images
       - name                      - products/...
       - description
       - price
       - stock
       - timestamps
```

The application separates **structured product data** from **product media**:

- Supabase PostgreSQL stores product records such as names, descriptions, prices, stock and timestamps.
- Supabase Storage stores uploaded product images.
- Django's `Product.image` field uses a custom storage backend that talks to Supabase Storage through its S3-compatible API.
- Public product images are served from the Supabase Storage public URL.

Supabase Storage supports the S3 protocol, so the project can use Django's existing `django-storages` and `boto3` integration without using Amazon S3 itself.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application programming language |
| Django 6.1 | Web framework and backend |
| PostgreSQL | Persistent application database |
| Supabase | Managed PostgreSQL and object storage platform |
| Supabase Storage | Cloud storage for product images |
| django-storages | Django storage abstraction |
| boto3 | S3-compatible storage client |
| Pillow | Image processing |
| Gunicorn | WSGI application server |
| WhiteNoise | Static-file serving |
| Django Admin | Product and inventory management |
| Django OTP / Admin 2FA | Additional admin authentication security |
| HTML/CSS | Frontend presentation |

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

## Running Locally

Clone the repository and enter the Django project:

```bash
git clone https://github.com/Olwethu-Tshabalala16/NqoPerfumes.git
cd NqoPerfumes/nqoperfumes/myshop
```

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r ../../../requirements.txt
```

Configure the Supabase environment variables, then run migrations:

```bash
python manage.py migrate
```

Create an administrator:

```bash
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

The catalogue will then be available through the local Django server, with product management available through Django Admin.

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
