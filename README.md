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
- Uses AWS S3 for product media storage.
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
       Product Database              AWS S3
       Product metadata             Product media
       - name                       - images
       - description
       - price
       - stock
       - timestamps
```

The application separates **product metadata** from **product media**:

- The Django database stores structured product information such as names, descriptions, prices and stock.
- **Amazon S3** stores uploaded product images and provides cloud-based object storage for the application's media.
- Django connects the product record to its uploaded image through the ImageField.

This separation is important because object storage and relational application data solve different problems.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application programming language |
| Django 6.1 | Web framework and backend |
| SQLite | Development database |
| AWS S3 | Cloud object storage for product images |
| django-storages | Django integration with S3 |
| boto3 | AWS SDK used by the S3 storage integration |
| Pillow | Image processing |
| Gunicorn | WSGI application server |
| WhiteNoise | Static-file serving |
| Django Admin | Product and inventory management |
| Django OTP / Admin 2FA | Additional admin authentication security |
| HTML/CSS | Frontend presentation |

## AWS S3

One of the important changes in this project was moving product media storage into AWS S3.

The application does not hard-code AWS credentials. Instead, the S3 bucket, region and credentials are supplied through environment variables:

```env
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

The application uses Django's storage abstraction, so the Product.image field can remain an ordinary Django ImageField while the underlying media is stored remotely in S3.

## Security and Configuration

Sensitive configuration belongs in environment variables rather than source code.

Required configuration includes:

```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://your-domain.example
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
ADMIN_2FA_EMAIL_SENDER=admin@example.com
```

Do not commit real AWS credentials or production secrets to Git.

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

Set the required environment variables, then run migrations:

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

The core application currently uses a Product model containing:

- name
- description
- price
- stock
- image
- created_at
- updated_at

The model also exposes an is_in_stock() method so the application can determine whether a product currently has available stock.

## What I Learned

This project helped me understand the relationship between application development and cloud infrastructure.

I learned that building a web application is not only about writing frontend and backend code. The application also needs somewhere to persist structured data, somewhere appropriate to store files, and a way to connect those services reliably.

Using **AWS S3** was particularly important to me because I am aspiring to become a **data engineer**. Cloud platforms and cloud storage are fundamental parts of modern data systems. Understanding object storage, cloud resources, application configuration and how software interacts with cloud infrastructure gives me a stronger foundation for working with data platforms later.

This project therefore became an early practical step toward combining software engineering with my longer-term interest in data engineering and cloud technologies.

## Project Direction

The project began as a simple solution to help my mother's perfume business move away from a physical catalogue and toward a shareable digital catalogue.

As I continue developing it, the project can evolve beyond a basic product listing into a more complete commerce system, including stronger inventory management, order workflows, customer interactions and cloud-native infrastructure.

The main lesson remains simple: **software should solve a real problem first, and the technology should support that problem.**