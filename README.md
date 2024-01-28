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
