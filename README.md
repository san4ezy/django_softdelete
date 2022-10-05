# Django Soft Delete

This is a set of small classes to make soft deletion of objects.  
Use the abstract model `SoftDeleteModel` for adding two new fields:
- `is_deleted` - is a boolean field, shows weather of a deletion state of object
- `deleted_at` - is a DateTimeField, serves a timestamp of deletion.

Also, you can use `SoftDeleteManager` and `DeletedManager` object managers for getting
alive and deleted objects accordingly.

By default, the `SoftDeleteModel` has `objects` attribute as `SoftDeleteManager` and
`deleted_objects` attribute as `DeletedManager`.

## Installation

```
pip install django-soft-delete
```


Add the `SoftDeleteModel` as a parent for your model:
```python
# For regular model
class Article(SoftDeleteModel):
    title = models.CharField(max_length=100)
    
    # Following fields will be added automatically
    # is_deleted
    # deleted_at
    
    # Following managers will be added automatically
    # objects = SoftDeleteManager()
    # deleted_objects = DeletedManager()


# For inherited model
class Post(SoftDeleteModel, SomeParentModelClass):
    title = models.CharField(max_length=100)
```

Make and apply the migrations:
```
./manage.py makemigrations
./manage.py migrate
```

## Quick example

```python
a1 = Article.objects.create(title='Django')
a2 = Article.objects.create(title='Django')
a3 = Article.objects.create(title='Django')
Article.objects.count()  # 3

a1.delete()  # soft deletion of object
Article.objects.count()  # 2

deleted_a1 = Article.deleted_objects.first()  # <Article: 'Django'>
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
class YourOwnManager(SoftDeleteManager):
    pass
```

The same class exists for the `deleted_objects` manager too -- `DeletedManager`.

## Custom QuerySet

If you need to use soft delete functionality for your custom `QuerySet`, use the 
`SoftDeleteQuerySet` as a parent class or extending existing one.

```python
class YourOwnQuerySet(SoftDeleteQuerySet):
    pass
```
