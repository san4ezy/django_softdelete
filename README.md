# Django Soft Delete

This is a set of small classes to make soft deletion of objects.  
Use the abstract model `SoftDeleteModel` for adding two new fields:
- `is_deleted` - is a boolean field, shows weather of a deletion state of object
- `deleted_at` - is a DateTimeField, serves a timestamp of deletion.

Also, you can use `SoftDeleteManager` and `DeletedManager` object managers for getting
alive and deleted objects accordingly.

By default, the `SoftDeleteModel` has `objects` attribute as `SoftDeleteManager` and
`deleted_objects` attribute as `DeletedManager`.

## How to use

```
pip install django-soft-delete
```

Add the `SoftDeleteModel` as a parent for your model:

```python
# For regular model
from django.db import models
from django_softdelete.models import SoftDeleteModel

class Article(SoftDeleteModel):
    title = models.CharField(max_length=100)
    
    # Following fields will be added automatically
    # is_deleted
    # deleted_at
    
    # Following managers will be added automatically
    # objects = SoftDeleteManager()
    # deleted_objects = DeletedManager()
    # global_objects = GlobalManager()


# For inherited model
from django_softdelete.models import SoftDeleteModel

class Post(SoftDeleteModel, SomeParentModelClass):
    title = models.CharField(max_length=100)
```

Make and apply the migrations:
```
./manage.py makemigrations
./manage.py migrate
```

## Relations

You can also use soft deletion for models that are related to others. This library does not interfere with standard Django functionality. This means that you can also use cascading delete, but remember that soft delete only works with the `SoftDeleteModel` classes. If you delete an instance of the parent model and use cascading delete, then the instances of the child model will be hard-deleted. To prevent hard deletion in this case, you should use `SoftDeleteModel` for child models in the same way as for parent model. 

## Quick Start Guide

Let's walk through setting up a new project and using the core features of `django-soft-delete`.

### 1. Project Setup

First, set up your Django project. We'll use `uv` here, but you can use `venv` and `pip` as well.

```bash
# Initialize a virtual environment
uv init

# Add django and django-soft-delete
uv add django django-soft-delete

# Create a new Django project and an app
uv run django-admin startproject myproject
cd myproject
uv run python manage.py startapp core
```

### 2. Define Your Model

Now, edit `core/models.py` and make your model inherit from `SoftDeleteModel`.

```python
from django.db import models
from django_softdelete.models import SoftDeleteModel

class Article(SoftDeleteModel):
    title = models.CharField(max_length=100)

    # The following are automatically added by SoftDeleteModel:
    #
    # FIELDS
    # is_deleted: BooleanField
    # deleted_at: DateTimeField
    #
    # MANAGERS
    # objects: SoftDeleteManager (default, sees only "alive" objects)
    # deleted_objects: DeletedManager (sees only "deleted" objects)
    # global_objects: GlobalManager (sees all objects, alive or deleted)

    def __str__(self):
        return self.title
```

### 3. Configure Your Project

Add your new `core` app to the `INSTALLED_APPS` list in `myproject/settings.py`.

```python
# myproject/settings.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Add your app here
    'core',
]
```

### 4. Run Migrations

Create and apply the database migrations. `SoftDeleteModel` will add the `is_deleted` and `deleted_at` fields to your `Article` table.

```bash
uv run manage.py makemigrations core
uv run manage.py migrate
```

### 5. Basic Usage in the Shell

Let's see it in action! Start the Django shell:

```bash
uv run manage.py shell
```

Now, run these instructions one by one to see how soft deletion works.

```python
from core.models import Article

# Create a few articles
a1 = Article.objects.create(title='Intro to Django Soft Delete')
a2 = Article.objects.create(title='Advanced Python')
a3 = Article.objects.create(title='Using django-soft-delete')

# The default manager only sees "alive" objects
print(f"Initial count: {Article.objects.count()}")
# >>> Initial count: 3

# --- Soft-delete an article ---
# This doesn't remove it from the DB, just marks it as deleted
a1.delete()

# The default manager now shows one less object
print(f"Count after soft delete: {Article.objects.count()}")
# >>> Count after soft delete: 2
print(Article.objects.all())
# >>> <QuerySet [<Article: Advanced Python>, <Article: Using django-soft-delete>]>

# --- Finding and Restoring Deleted Objects ---
# Use `deleted_objects` to find deleted items
print(f"Deleted objects count: {Article.deleted_objects.count()}")
# >>> Deleted objects count: 1

deleted_a1 = Article.deleted_objects.first()
print(f"Found deleted article: {deleted_a1}")
# >>> Found deleted article: Intro to Django Soft Delete

# Restore the deleted article
deleted_a1.restore()
print(f"Count after restore: {Article.objects.count()}")
# >>> Count after restore: 3
print(f"Deleted count after restore: {Article.deleted_objects.count()}")
# >>> Deleted count after restore: 0

# --- Permanent Deletion ---
# To permanently delete an object, use `hard_delete()`
a3.hard_delete()
print(f"Count after hard delete: {Article.objects.count()}")
# >>> Count after hard delete: 2

# --- Viewing All Objects ---
# You can query all objects, alive or deleted, with `global_objects`
print(f"Global count (alive + deleted): {Article.global_objects.count()}")
# >>> Global count (alive + deleted): 2
```

## Working with Relationships

`django-soft-delete` intelligently handles relationships between models.

### Cascading Soft Deletes

If a related model also inherits from `SoftDeleteModel`, deleting the parent will soft-delete the children.

Let's add these models to `core/models.py` and run migrations again.

```python
class Product(SoftDeleteModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Option(SoftDeleteModel): # Also a SoftDeleteModel
    # Using models.CASCADE will trigger a soft-delete on the Option
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)

    def __str__(self):
        return f"{self.product.name} - {self.name}"
```

Now, test the cascading behavior in the shell:

```python
from core.models import Product, Option

p = Product.objects.create(name='Laptop')
Option.objects.create(product=p, name='16GB RAM')

print(f"Initial option count: {Option.objects.count()}")
# >>> Initial option count: 1

# Soft-deleting the Product...
p.delete()

# ...also soft-deletes the related Option because it's a SoftDeleteModel
print(f"Option count after parent delete: {Option.objects.count()}")
# >>> Option count after parent delete: 0
print(f"Deleted option count: {Option.deleted_objects.count()}")
# >>> Deleted option count: 1
```

### Protecting Relationships

You can use Django's standard `on_delete=models.PROTECT` to prevent a model from being deleted if it has active children, and this works perfectly with soft deletion.

## Batch Operations

You can perform soft-delete and restore operations on entire querysets, making bulk updates easy.

```python
# Create some data
Article.objects.create(title='Django Best Practices')
Article.objects.create(title='Advanced Django')

# Soft-delete all articles with 'Django' in the title
Article.objects.filter(title__icontains='Django').delete()
print(f"Alive articles count: {Article.objects.count()}")
# >>> Alive articles count: 1 (Only 'Advanced Python' remains)

# Restore all deleted articles
Article.deleted_objects.all().restore()
print(f"Alive articles count after restore: {Article.objects.count()}")
# >>> Alive articles count after restore: 4
```

## Advanced Usage: Custom Managers and QuerySets

A common requirement is to add custom methods to your model's manager (e.g., `Sale.objects.by_product(...)`). To do this without losing the soft-delete logic, you must inherit from `SoftDeleteQuerySet` and `SoftDeleteManager`.

Here is a complete example.

### 1. Define a Custom QuerySet

Create a new file `core/querysets.py`. Your custom `QuerySet` will contain the filtering logic.

```python
# Note that django_softdelete.querysets doesn't contain SoftDeleteQuerySet class so you must import it from django_softdelete.managers 
from django_softdelete.managers import SoftDeleteQuerySet

class SaleQuerySet(SoftDeleteQuerySet):
    def by_product(self, product_id):
        return self.filter(product_id=product_id)

    def by_price(self, price):
        return self.filter(sale_price__gt=price)

    def with_related_data(self):
        return self.select_related('product')
```

### 2. Define a Custom Manager

Create a new file `core/managers.py`. The manager will use your custom `QuerySet`.

```python
from django_softdelete.managers import SoftDeleteManager
from .querysets import SaleQuerySet

class SaleManager(SoftDeleteManager):
    def get_queryset(self):
        # Ensure the base queryset is used so core soft-delete features work
        base_qs = super().get_queryset()
        # Use our custom queryset for all manager calls
        return SaleQuerySet(model=self.model, query=base_qs.query, using=self._db)

    def by_product(self, product_id):
        """A manager method that uses a custom queryset method."""
        return self.get_queryset().by_product(product_id).with_related_data()

    def by_price(self, price):
        """Another manager method that uses a custom queryset method."""
        return self.get_queryset().by_price(price).with_related_data()
```

### 3. Update the Model

Finally, update `core/models.py` to use the new manager.

```python
# ... (imports and other models) ...
from .managers import SaleManager

class Sale(SoftDeleteModel):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    name = models.CharField(max_length=32)
    sale_price = models.DecimalField(max_digits=5, decimal_places=2)

    # Assign your custom manager
    objects = SaleManager()

    def __str__(self):
        return f"{self.name} - {self.product.name} (${self.sale_price})"
```

After adding these files and updating the model, run `makemigrations` and `migrate`.

### 4. Test the Custom Manager

This script instructions demonstrates how could custom methods work perfectly alongside the soft-delete functionality and Django's `on_delete=PROTECT`.

```python
# --- SETUP ---
from django.db.models import ProtectedError
from core.models import Product, Sale

# --- 1. CREATE SOME DATA ---
product_a = Product.objects.create(name="Laptop Pro")
product_b = Product.objects.create(name="Wireless Mouse")

Sale.objects.create(name="Summer Sale", product=product_a, sale_price=99.99)
Sale.objects.create(name="Clearance", product=product_a, sale_price=75.50)
Sale.objects.create(name="Flash Sale", product=product_b, sale_price=25.00)
Sale.objects.create(name="Black Friday", product=product_b, sale_price=19.99)

print(f"Total sales created: {Sale.objects.count()}")
# Total sales created: 4

# --- 2. TEST THE CUSTOM MANAGER METHODS ---
print("\n--- Testing by_product() ---")
laptop_sales = Sale.objects.by_product(product_id=product_a.id)
print(f"Found {laptop_sales.count()} sales for {product_a.name}:")
for sale in laptop_sales:
    print(f"- {sale}")

# Found 2 sales for Laptop Pro:
# - Summer Sale - Laptop Pro ($99.99)
# - Clearance - Laptop Pro ($75.50)

print("\n--- Testing by_price() ---")
expensive_sales = Sale.objects.by_price(price=50.00)
print(f"Found {expensive_sales.count()} sales with price > $50.00:")
for sale in expensive_sales:
    print(f"- {sale}")

# Found 2 sales with price > $50.00:
# - Summer Sale - Laptop Pro ($99.99)
# - Clearance - Laptop Pro ($75.50)

# --- 3. VERIFY SOFT-DELETE STILL WORKS ---
print("\n--- Testing Soft Delete ---")
sale_to_delete = Sale.objects.get(name="Flash Sale")
print(f"Soft-deleting '{sale_to_delete.name}'...")
sale_to_delete.delete()

print(f"Total alive sales now: {Sale.objects.count()}")
# Total alive sales now: 3

# Check that our custom filter still works and respects the soft delete
mouse_sales = Sale.objects.by_product(product_id=product_b.id)
print(f"Found {mouse_sales.count()} alive sales for {product_b.name}:")
for sale in mouse_sales:
    print(f"- {sale}")

# Found 1 alive sales for Wireless Mouse:
# - Black Friday - Wireless Mouse ($19.99)

# Find and restore the deleted sale
deleted_sale = Sale.deleted_objects.get(name="Flash Sale")
print(f"Restoring '{deleted_sale.name}'...")
deleted_sale.restore()
print(f"Total alive sales after restore: {Sale.objects.count()}")
# Total alive sales after restore: 4

# --- 4. TEST 'on_delete=PROTECT' ---
print("\n--- Testing on_delete=PROTECT ---")
print(f"Attempting to delete product '{product_a.name}', which has active sales...")
try:
    product_a.delete()
except ProtectedError as e:
    print("SUCCESS: Django raised ProtectedError, as expected!")
    # The exact error message may vary slightly between Django versions
    print("Error message contains protected foreign key references.")

# SUCCESS: Django raised ProtectedError, as expected!
# Error message contains protected foreign key references.
```

## Development

This project uses [Hatch](https://hatch.pypa.io/) for environment management, testing, and building. Hatch provides a more comprehensive alternative to traditional requirements.txt files and virtualenv management.

### Installing Hatch

```bash
pip install hatch
```

### Creating Development Environments

```bash
# Create the default development environment
hatch env create

# Create the test environment with all test dependencies
hatch env create test
```

### Setting Up the Database

The test project uses SQLite by default. You don't need to manually create the database file as Django will create it automatically when needed.

```bash
# Activate the test environment
hatch shell test

# Create and apply migrations
python manage.py makemigrations
python manage.py migrate
```

This will create the SQLite database file at the location specified in settings.py (`./db.sqlite3`) and set up all necessary tables.

### Activating Environments

```bash
# Activate the default environment
hatch shell

# Activate the test environment
hatch shell test
```

### Running Tests

```bash
# Run tests with all configured options (coverage, etc.)
hatch run test:pytest
```

### Important: Setting Up the Test Database

Before running tests, you must create and apply migrations for the test app:

```bash
# Activate the test environment
hatch shell test

# Create migrations for the test app models (required before first test run)
python manage.py makemigrations test_app

# Apply all migrations
python manage.py migrate
```

If you encounter "no such table" errors during testing, this usually means you need to run the migration steps above.

## Support me with a cup of coffee

USDT (ERC20): `0x308dad9B7014AdeD217e817B6274EeeD971200F9`

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/H2H015I0T4)

