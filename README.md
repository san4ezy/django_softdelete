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

## Quick example

```python
a1 = Article.objects.create(title='django')
a2 = Article.objects.create(title='python')
a3 = Article.objects.create(title='django_softdelete')
Article.objects.count()  # 3

a1.delete()  # soft deletion of object
Article.objects.count()  # 2

deleted_a1 = Article.deleted_objects.first()  # <Article: 'django'>
deleted_a1.restore()  # restores deleted object
Article.objects.count()  # 3
Article.deleted_objects.count()  # 0

a1.hard_delete()  # deletes the object at all.

```

## Batch deletion

```python
Article.objects.filter(some_value=True).delete()  # soft delete for all filtered objects
Article.deleted_objects.filter(some_value=True).restore()  # restore for all filtered objects
```

## Custom manager

If you need a soft delete functionality for model with your own object manager,
you want to extend it with the `SoftDeleteManager`.

```python
from django_softdelete.models import SoftDeleteManager

class YourOwnManager(SoftDeleteManager):
    pass
```

The same class exists for the `deleted_objects` manager too -- `DeletedManager`.

## Custom QuerySet

If you need to use soft delete functionality for your custom `QuerySet`, use the 
`SoftDeleteQuerySet` as a parent class or extending existing one.

```python
from django_softdelete.models import SoftDeleteQuerySet

class YourOwnQuerySet(SoftDeleteQuerySet):
    pass
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

