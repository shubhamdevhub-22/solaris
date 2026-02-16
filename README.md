# Solaris CRM - Unity Wholesale

A comprehensive Customer Relationship Management (CRM) system built with Django, designed for wholesale operations including order management, product management, vendor management, and financial tracking.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Deployment](#deployment)
- [API Modules](#api-modules)
- [Database Models](#database-models)
- [Contributing](#contributing)

## 🎯 Project Overview

Solaris CRM is a full-featured CRM platform tailored for wholesale businesses. It provides tools for managing customers, orders, products, vendors, credit memos, expense management, and generating comprehensive reports.

## ✨ Features

- **Customer Management**: Complete customer lifecycle management with contact information and validation
- **Order Management**: Create, track, and manage customer orders with status workflows
- **Product Management**: Manage product catalog, pricing, and inventory
- **Purchase Orders**: Handle vendor purchase orders and procurement
- **Credit Memos**: Process credit transactions and adjustments
- **Vendor Management**: Maintain vendor relationships and information
- **Expense Management**: Track and manage business expenses
- **Reports & Analytics**: Generate sales reports, financial summaries, and business insights
- **User Management**: Role-based access control and user administration
- **Email Service Integration**: SendGrid integration for transactional emails
- **Celery Background Tasks**: Asynchronous task processing for long-running operations
- **Data Import/Export**: Support for CSV and Excel file handling
- **Responsive UI**: Bootstrap-based responsive design

## 🛠️ Tech Stack

### Backend
- **Framework**: Django 4.1.7
- **Database**: PostgreSQL (psycopg2)
- **Task Queue**: Celery 5.3.4 with Redis
- **Cache**: Redis
- **Task Scheduler**: Django-Celery-Beat

### Frontend
- **Template Engine**: Django Templates
- **CSS Framework**: Bootstrap 4
- **Data Tables**: Django-DataTables-Too
- **Form Styling**: Crispy Forms (Bootstrap 4)

### Key Libraries
- **Authentication**: Django-AllAuth
- **Phone Numbers**: Django-PhoneNumber-Field
- **Geolocation**: GeoPy
- **File Processing**: Pillow, openpyxl, xlrd, xhtml2pdf
- **Reporting**: ReportLab, xhtml2pdf
- **Barcodes**: python-barcode
- **Data Analysis**: Pandas, NumPy
- **Google Maps**: googlemaps
- **CORS**: Django-CORS-Headers
- **Email**: Django-Anymail (SendGrid)

## 📁 Project Structure

```
solaris-crm/
├── app_modules/                    # Main application modules
│   ├── base/                       # Base models, middleware, permissions
│   │   ├── middleware.py
│   │   ├── mixins.py
│   │   ├── models.py
│   │   └── permissions.py
│   ├── company/                    # Company management
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── tasks.py
│   │   └── urls.py
│   ├── customers/                  # Customer management
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── validators.py
│   │   ├── signals.py
│   │   ├── tasks.py
│   │   └── urls.py
│   ├── product/                    # Product catalog management
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── signals.py
│   │   ├── tasks.py
│   │   └── urls.py
│   ├── order/                      # Order management
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── signals.py
│   │   ├── utils.py
│   │   ├── context_processors.py
│   │   └── templatetags/
│   ├── purchase_order/             # Purchase order management
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── urls.py
│   ├── credit_memo/                # Credit memo processing
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── urls.py
│   ├── expanse_management/         # Expense tracking
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── urls.py
│   ├── vendors/                    # Vendor management
│   │   ├── models.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── reports/                    # Reporting and analytics
│   │   ├── models.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── users/                      # User authentication & management
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── urls.py
│   └── utils/                      # Utility functions
│       └── helpers.py
├── unity_wholesale/                # Project configuration
│   ├── settings/
│   │   ├── base.py                # Base settings
│   │   ├── local.py               # Local development settings
│   │   └── production.py           # Production settings
│   ├── celery.py                  # Celery configuration
│   ├── urls.py                    # URL routing
│   ├── wsgi.py                    # WSGI configuration
│   └── asgi.py                    # ASGI configuration
├── templates/                      # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── company/
│   ├── customer/
│   ├── order/
│   ├── product/
│   ├── purchase_order/
│   ├── credit_memo/
│   ├── expanse_management/
│   ├── vendors/
│   ├── reports/
│   ├── users/
│   └── ...
├── static/                         # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   ├── images/
│   ├── assets/
│   └── ...
├── media/                          # User-uploaded media
│   ├── company-logo/
│   ├── product-images/
│   ├── sales-bills/
│   └── csv/
├── services/                       # External services
│   └── email_service.py           # Email service integration
├── requirements/                   # Dependency specifications
│   ├── base.txt                   # Base requirements
│   ├── local.txt                  # Local development requirements
│   └── production.txt             # Production requirements
├── manage.py                       # Django management script
├── deploy.sh                       # Deployment script
└── venv2/                          # Python virtual environment
```

## 📦 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 10+
- Redis
- Git

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd solaris-crm
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements/base.txt
# For local development:
pip install -r requirements/local.txt
# For production:
pip install -r requirements/production.txt
```

### Step 4: Create Environment Variables
Create a `.env` file in the project root:
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgres://user:password@localhost:5432/solaris_crm
REDIS_URL=redis://localhost:6379/0
SENDGRID_API_KEY=your-sendgrid-key
GOOGLE_MAPS_API_KEY=your-google-maps-key
```

### Step 5: Database Setup
```bash
python manage.py seed
python manage.py createsuperuser
```

### Step 6: Collect Static Files
```bash
python manage.py collectstatic
```

## ⚙️ Configuration

### Settings Files
- **base.py**: Core Django settings shared across environments
- **local.py**: Development-specific settings (extends base.py)
- **production.py**: Production-specific settings (extends base.py)

### Celery Configuration
The project uses Celery for asynchronous task processing. Configure in `unity_wholesale/celery.py`:
- Task queue: Redis
- Task result backend: Redis/Database
- Periodic tasks: Managed via Django-Celery-Beat

### Email Service
Configured with SendGrid via Django-Anymail. Set `SENDGRID_API_KEY` in environment variables.

## 🚀 Usage

### Running Development Server
```bash
python manage.py runserver
```
Access the application at `http://localhost:8000`

### Running Celery Worker
```bash
celery -A unity_wholesale worker -l info
```

### Running Celery Beat (Scheduler)
```bash
celery -A unity_wholesale beat -l info
```

### Creating a Superuser
```bash
python manage.py createsuperuser
```

### Loading Test Data
```bash
python manage.py seed
```

### Running Tests
```bash
python manage.py test
```

## 🔧 Development

### Code Structure Guidelines
- Each app is self-contained with its own models, views, forms, and URLs
- Use Django's class-based views for consistency
- Implement custom mixins in `app_modules/base/mixins.py` for shared functionality
- Follow Django best practices and PEP 8 standards

### Creating Migrations
```bash
python manage.py makemigrations app_name
python manage.py migrate
```

### Running Management Commands
```bash
python manage.py <command>
```

## 🚢 Deployment

### Using the Deployment Script
```bash
chmod +x deploy.sh
./deploy.sh
```

### Manual Deployment Steps
1. Activate virtual environment
2. Collect static files: `python manage.py collectstatic`
3. Run migrations: `python manage.py migrate`
4. Seed database: `python manage.py seed`
5. Start services:
   - Nginx web server
   - Gunicorn application server
   - Celery worker
   - Celery beat scheduler

### Production Checklist
- [ ] Set DEBUG=False
- [ ] Configure SECRET_KEY securely
- [ ] Set ALLOWED_HOSTS
- [ ] Configure PostgreSQL database
- [ ] Set up Redis for caching and tasks
- [ ] Configure email service (SendGrid)
- [ ] Set up SSL/HTTPS certificates
- [ ] Configure static and media file serving
- [ ] Set up proper logging
- [ ] Enable CSRF protection

## 📊 API Modules

### Company Module (`app_modules/company/`)
Manages company information and settings.
- Models: Company configuration and details
- Views: CRUD operations for company data
- Tasks: Background jobs for company operations

### Customers Module (`app_modules/customers/`)
Complete customer lifecycle management.
- Features: Customer profiles, contact info, validation
- Signals: Automatic actions on customer creation/update
- Tasks: Automated customer-related tasks

### Product Module (`app_modules/product/`)
Product catalog and inventory management.
- Features: Product listing, pricing, images
- Signals: Auto-update product stats
- Tasks: Bulk product operations

### Order Module (`app_modules/order/`)
Order creation, processing, and tracking.
- Features: Order workflows, item management, status tracking
- Utils: Order processing utilities
- Context Processors: Shared order context
- Template Tags: Custom template filters

### Purchase Order Module (`app_modules/purchase_order/`)
Vendor purchase order management.
- Features: PO creation, tracking, receipt management
- Integrations: Vendor tracking and updates

### Credit Memo Module (`app_modules/credit_memo/`)
Credit transaction processing.
- Features: Credit creation, approval, application

### Expense Management Module (`app_modules/expanse_management/`)
Business expense tracking and management.
- Features: Expense categorization, reporting

### Vendors Module (`app_modules/vendors/`)
Vendor information and relationship management.
- Features: Vendor profiles, contact details, ratings

### Reports Module (`app_modules/reports/`)
Business analytics and reporting.
- Features: Sales reports, financial summaries, custom exports

### Users Module (`app_modules/users/`)
User authentication and authorization.
- Features: User profiles, roles, permissions
- Integrations: Django-AllAuth for social authentication

## 🗄️ Database Models

The application uses Django ORM with PostgreSQL. Key model relationships:
- **Customers**: Central to orders and credit memos
- **Orders**: Contain line items linking to products
- **Products**: Catalog with pricing and inventory
- **Vendors**: Source for purchase orders and products
- **Users**: Role-based access control

## 📝 Contributing

1. Create a feature branch: `git checkout -b feature/feature-name`
2. Make your changes and commit: `git commit -m 'Add feature'`
3. Push to branch: `git push origin feature/feature-name`
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**MIT License Summary:**
- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Private use allowed
- ⚠️ Liability and warranty disclaimers apply

## 📧 Support

For support and questions, please contact: shubham.devhub@gmail.com

---

**Last Updated**: February 2026
**Version**: 1.0.0
