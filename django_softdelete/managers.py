from django.db import models


class SoftDeleteQuerySet(models.query.QuerySet):
    """
    A custom QuerySet class for soft deletion of objects.

    Methods:
    - delete(): Soft deletes all objects in the QuerySet.
    - hard_delete(): Hard deletes all objects in the QuerySet.

    """
    def delete(self, strict: bool = False):
        """
        Override delete method to perform soft deletion on the queryset.
        """
        for obj in self.all():
            obj.delete(strict=strict)
        return

    def hard_delete(self):
        """
        Hard delete the objects permanently.
        """
        return super().delete()


class DeletedQuerySet(models.query.QuerySet):
    """
    A subclass of `models.query.QuerySet` that adds a `restore` method for restoring deleted objects.

    restore(*args, **kwargs) - Restore deleted objects based on the given filter arguments.
    """
    def restore(self, strict: bool = True, *args, **kwargs):
        """
        Restore items from the trash.

        :param args: Additional arguments for filtering the items to be restored.
        :param kwargs: Additional keyword arguments for filtering the items to be restored.
        :return: None.
        """
        qs = self.filter(*args, **kwargs)
        for obj in qs:
            obj.restore(strict=strict)
        return

    def hard_delete(self):
        """
        Hard delete the objects permanently.
        """
        return super().delete()


class SoftDeleteManager(models.Manager):
    """
    Get the queryset of the SoftDeleteManager.

    The queryset only includes objects that have not been deleted (deleted_at is null).

    :return: The queryset.
    :rtype: django.db.models.query.QuerySet
    """
    def get_queryset(self):
        """
        Get the queryset for the model.

        :return: A queryset that filters out objects with a non-null `deleted_at` field.
        :rtype: SoftDeleteQuerySet
        """
        return SoftDeleteQuerySet(self.model, using=self._db).filter(
            deleted_at__isnull=True
        )


class DeletedManager(models.Manager):
    """
        DeletedManager: A class that manages deleted objects in a database table.

        This class is a custom manager for a Django model that selectively retrieves only the deleted objects from the database table.

        :param models.Manager: The base class for Django model managers.
        :returns: An instance of DeletedManager.
        :rtype: DeletedManager
        :raises: None

        :Example:

        deleted_manager = DeletedManager()
        deleted_queryset = deleted_manager.get_queryset()
    """
    def get_queryset(self):
        """
        Returns the query set containing the deleted records.

        :return: A query set containing the deleted records.
        :rtype: DeletedQuerySet
        """
        return DeletedQuerySet(self.model, using=self._db).filter(
            deleted_at__isnull=False
        )


class GlobalManager(models.Manager):
    """
    It's a standard Django objects manager, which works with all objects regardless
    of soft deletion logic.
    """
    pass
