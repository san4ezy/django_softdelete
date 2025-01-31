from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.db.models.signals import pre_delete, post_delete
from django.utils import timezone

from django_softdelete.exceptions import SoftDeleteException
from django_softdelete.managers import DeletedManager
from django_softdelete.managers import GlobalManager
from django_softdelete.managers import SoftDeleteManager
from django_softdelete.signals import post_hard_delete, post_soft_delete, post_restore
import uuid


class SoftDeleteModel(models.Model):
    """
    A Django model which has been enhanced with soft deletion characteristics.

    Attributes:
        deleted_at (models.DateTimeField): Date and time when an instance was soft-deleted.
            If this field is not None, it means the instance has been soft-deleted.
        restored_at (models.DateTimeField): Date and time when an instance was
            restored.
        transaction_id (models.UUIDField): UUID field that is used to label all
            entites that were soft-deleted inside same transaction. Later it is
            used to restore objects. This will prevent situations where related
            objects that were deleted before soft-deletion, are restored.
        objects (SoftDeleteManager): a custom manager that excludes soft deleted objects.
        deleted_objects (DeletedManager): a custom manager that handles only soft deleted objects.
        global_objects (GlobalManager): a custom manager that handles all objects regardless of deletion status.

    Note:
        This model is abstract, to use it, it should be subclassed.

    Methods:
        is_deleted: Check if the object is deleted.
        hard_delete: Hard delete the object, removing it permanently.
        delete: Soft deletes the object by setting the `deleted_at` attribute to the current time and date.
        restore: Restores a soft deleted object by setting its `deleted_at` attribute to None.
    """
    deleted_at = models.DateTimeField(blank=True, null=True)
    restored_at = models.DateTimeField(blank=True, null=True)
    transaction_id = models.UUIDField(blank=True, null=True)

    objects = SoftDeleteManager()
    deleted_objects = DeletedManager()
    global_objects = GlobalManager()

    class Meta:
        abstract = True

    # PUBLIC SECTION

    @property
    def is_deleted(self):
        """
        Check if the object has been deleted.

        :return: True if the object has been deleted, False otherwise
        """
        return self.deleted_at is not None

    @property
    def is_restored(self):
        """
        Checks if the object has been restored.

        :return: True if the object has been restored, False otherwise
        """
        return self.restored_at is not None

    def hard_delete(self, *args, **kwargs):
        """
        Deletes the object from the database permanently.

        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: None
        """
        super().delete(*args, **kwargs)
        post_hard_delete.send(sender=self.__class__, instance=self)

    def delete(
            self,
            strict: bool = False,
            transaction_id: str = None,
            using=None,
            *args, **kwargs,
    ):
        """
        Delete the object and all related objects.

        :param strict: Whether to enforce strict deletion by checking if related models
                       are subclasses of SoftDeleteModel.
        :param transaction_id: A UUID used to identify all objects that were deleted inside same transaction
        :param using: (str, optional) The database alias to use for the deletion.
                      If not specified, the default database connection will be used.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: None
        """
        pre_delete.send(
            sender=self.__class__, instance=self, using=using,
        )

        now = timezone.now()
        transaction_id = uuid.uuid4() if not transaction_id else transaction_id
        with transaction.atomic():
            for field in self._meta.get_fields():

                # Skip generic relations
                if isinstance(field, GenericRelation):
                    continue

                RelatedModel = field.related_model

                if not RelatedModel:
                    continue

                if strict and not issubclass(RelatedModel, SoftDeleteModel):
                    raise SoftDeleteException(
                        f"{RelatedModel.__name__} is not a subclass of SoftDeleteModel."
                    )

                if field.one_to_one:
                    self.__delete_related_one_to_one(
                        field, strict, transaction_id, *args, **kwargs
                    )

                # elif field.many_to_many:
                #     # M2M forward must not be deleted
                #     print("M2M forward", field.name)
                #
                # elif field.many_to_one:
                #     # Maybe M2M reverse
                #     print("M2M reverse", field.name, field.remote_field)  # field.remote_field?

                elif field.one_to_many:
                    self.__delete_related_one_to_many(field, strict, transaction_id, *args, **kwargs)

                else:
                    continue

            self.deleted_at = now
            self.restored_at = None
            self.transaction_id = transaction_id
            self.save(
                update_fields=['deleted_at', 'restored_at', 'transaction_id', ]
            )

            post_soft_delete.send(
                sender=self.__class__, instance=self, using=using,
            )

    def restore(self, strict: bool = True, transaction_id: str = None, *args, **kwargs):
        """Restores a deleted object by setting the deleted_at field to None.

        :param strict: A boolean indicating whether to perform strict restoration.
            If True, the related objects must be subclasses of SoftDeleteModel.
            If False, the related objects are restored regardless.
        :param transaction_id: A UUID used to identify all objects that were deleted inside same transaction
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: None
        """

        now = timezone.now()
        self.deleted_at = None
        self.restored_at = now
        transaction_id = self.transaction_id if not transaction_id else transaction_id
        with transaction.atomic():
            for field in self._meta.get_fields():

                # Skip generic relations
                if isinstance(field, GenericRelation):
                    continue

                RelatedModel = field.related_model
                if not RelatedModel:
                    continue

                if strict and not issubclass(RelatedModel, SoftDeleteModel):
                    raise SoftDeleteException(
                        f"{RelatedModel.__name__} is not a subclass of SoftDeleteModel."
                    )

                if field.one_to_one:
                    self.__restore_related_one_to_one(field, strict, transaction_id, *args, **kwargs)

                # elif field.many_to_many:
                #     # M2M must not be restored
                #     self.__restore_related_many_to_many(field, strict, *args, **kwargs)

                elif field.one_to_many:
                    try:
                        self.__restore_related_one_to_many(
                            field, strict, transaction_id, *args, **kwargs
                        )
                    except ValueError as e:
                        continue

                else:
                    continue
            self.transaction_id = None
            self.save(
                update_fields=['deleted_at', 'restored_at', 'transaction_id', ]
            )
            post_restore.send(sender=self.__class__, instance=self)

    # PRIVATE SECTION

    def __delete_related_object(self, field, related_object, strict, transaction_id, *args, **kwargs):
        """
        :param field: The field that defines the relationship between the current object and the related object.
        :param related_object: The related object that needs to be deleted.
        :param strict: A boolean value indicating whether to perform strict deletion or not.
        :param transaction_id: A UUID used to identify all objects that were deleted inside same transaction
        :param args: Additional positional arguments to be passed to the delete method of the related object.
        :param kwargs: Additional keyword arguments to be passed to the delete method of the related object.
        :return: None

        This method is used to delete a related object based on the given field and related object. The method performs different actions based on the value of the `on_delete` attribute of the
        * field.

        The method first checks if the field itself has an `on_delete` attribute. If so, it assigns the value of `field.on_delete` to `on_delete`. If not, it checks if the field has a `remote
        *_field` attribute and if it does, checks if `field.remote_field` has an `on_delete` attribute. If the `on_delete` attribute is found, it assigns the value to `on_delete`.

        After determining the `on_delete` value, the method executes a series of `match` statements to determine the action to be taken. The available `on_delete` options are:

        - `models.CASCADE`: Deletes the related object with the option to perform strict deletion.
        - `models.SET_NULL`: Sets the value of the related field to `None` and saves the related object.
        - `models.PROTECT`: Raises a `ProtectedError` if the related object is not `None`, indicating that deletion is restricted.
        - `models.SET_DEFAULT`: Sets the value of the related field to the default value defined in the field and saves the related object.
        - `models.SET`: If a callable `on_delete_set_function` is defined in the field's `remote_field`, calls the function to get the desired value and sets the related field accordingly.
        - `models.DO_NOTHING`: Performs no action.
        - `models.RESTRICT`: Raises a `ProtectedError` if the related object is not `None`, indicating that deletion is restricted.
        - Any other value: Deletes the related object with the option to perform strict deletion.

        After the `match` statement, the method checks if the related object has a primary key (`pk`). If it does, it saves the related object. If an `AttributeError` is raised during this process
        *, it is caught and ignored.

        Example usage:
            obj._delete_related_object(field, related_object, strict=True)
        """
        if hasattr(field, 'on_delete'):
            on_delete = field.on_delete
        elif hasattr(field, 'remote_field') and hasattr(field.remote_field, 'on_delete'):
            on_delete = field.remote_field.on_delete
        else:
            return

        if on_delete == models.CASCADE:
            if strict:
                kwargs['strict'] = strict
            if isinstance(related_object, SoftDeleteModel):
                related_object.delete(transaction_id=transaction_id, *args, **kwargs)
            else:
                related_object.delete(*args, **kwargs)
        elif on_delete == models.SET_NULL:
            setattr(related_object, field.remote_field.name, None)
            related_object.save()

        elif on_delete == models.PROTECT:
            related_query_name = (field.remote_field.related_query_name or
                                    field.remote_field.related_name or
                                    field.opts.model_name)

            if callable(related_query_name):
                related_query_name = related_query_name()

            if related_object:
                related_manager_name = related_query_name if hasattr(self,
                                                                        related_query_name) else f"{related_query_name}_set"
                protected_objects = list(getattr(self, related_manager_name).all())
                raise ProtectedError(
                    f"Cannot delete {self} because {related_object} is related with PROTECT",
                    protected_objects=protected_objects
                )

        elif on_delete == models.SET_DEFAULT:
            default_value = field.get_default()
            setattr(related_object, field.remote_field.name, default_value)
            related_object.save()

        elif on_delete == models.SET:
            if callable(field.remote_field.on_delete_set_function):
                value = field.remote_field.on_delete_set_function(self)
                setattr(related_object, field.remote_field.name, value)
                related_object.save()

        elif on_delete == models.DO_NOTHING:
            pass  # Explicitly do nothing

        elif on_delete == models.RESTRICT:
            if related_object:
                raise ProtectedError(
                    f"Cannot delete {self} because {related_object} "
                    f"is related with RESTRICT",
                    [related_object]
                )

        else:  # M2M
            related_object.delete(strict=strict, *args, **kwargs)

        try:
            if related_object.pk is not None:
                related_object.save()
        except AttributeError:
            pass

    def __restore_related_object(self, field, related_object, strict, transaction_id, *args, **kwargs):
        """
        Restores a related object and saves it if it has a valid primary key.

        :param field: The related field.
        :type field: Any
        :param related_object: The related object to restore.
        :type related_object: Any
        :param strict: Flag to determine if restore should be strict or not.
        :type strict: bool
        :param transaction_id: A UUID used to identify all objects that were deleted inside same transaction
        :type transaction_id: str
        :param args: Additional positional arguments for the related object's restore method.
        :type args: Any
        :param kwargs: Additional keyword arguments for the related object's restore method.
        :type kwargs: Any
        :return: None
        :rtype: None
        """
        if related_object.is_deleted:
            related_object.restore(strict=strict, transaction_id=transaction_id, *args, **kwargs)
            try:
                if related_object.pk is not None:
                    related_object.save()
            except AttributeError:
                pass

    def __delete_related_one_to_one(self, field, strict, transaction_id, *args, **kwargs):
        """
        Delete related one-to-one object.

        :param field: The field representing the one-to-one relationship.
        :param strict: If True, raise an exception if the related object does not exist. If False, do nothing if the related object does not exist.
        :param transaction_id: A UUID used to identify all objects that were deleted inside same transaction
        :param args: Additional positional arguments passed to __delete_related_object method.
        :param kwargs: Additional keyword arguments passed to __delete_related_object method.
        :return: None
        """
        related_object = getattr(self, field.name, None)
        if related_object:
            remote_model = field.remote_field.model
            related_query_name = (
                    field.remote_field.related_query_name
                    or field.remote_field.related_name
                    or field.opts.model_name
            )
            if callable(related_query_name):
                related_query_name = related_query_name()
            if hasattr(remote_model, related_query_name):
                if kwargs.get('o2o_model') != transaction_id:
                    kwargs['o2o_remote'] = transaction_id
                    self.__delete_related_object(
                        field, related_object, strict, transaction_id, *args, **kwargs
                    )
            elif hasattr(self, related_query_name):
                if kwargs.get('o2o_remote') != transaction_id:
                    kwargs['o2o_model'] = transaction_id
                    self.__delete_related_object(
                        field, related_object, strict, transaction_id, *args, **kwargs
                    )

    def __delete_related_one_to_many(self, field, strict, *args, **kwargs):
        """
        Delete all related objects in a one-to-many relationship.

        :param field: the field that represents the one-to-many relationship
        :type field: django.db.models.fields.related.ForeignObjectRel
        :param strict: whether to raise an exception if any related object cannot be deleted
        :type strict: bool
        :param args: additional positional arguments to be passed to __delete_related_object()
        :param kwargs: additional keyword arguments to be passed to __delete_related_object()
        :return: None
        """
        related_objects = getattr(self, field.get_accessor_name()).all()
        for related_object in related_objects:
            self.__delete_related_object(
                field, related_object, strict, *args, **kwargs
            )

    # def __delete_related_many_to_many(self, field, strict, *args, **kwargs):
    #     """
    #     This method deletes related objects in a many-to-many relationship.
    #
    #     :param field: The field representing the many-to-many relationship.
    #     :param strict: A boolean indicating whether to raise an error if no related objects are found.
    #     :param args: Additional positional arguments.
    #     :param kwargs: Additional keyword arguments.
    #     :return: None
    #     """
    #     related_objects = getattr(self, field.name, None)
    #     if not related_objects:
    #         raise ValueError('No related objects found')
    #     for related_object in related_objects.filter(
    #         deleted_at__isnull=True
    #     ):
    #         self._delete_related_object(
    #             field, related_object, strict, *args, **kwargs
    #         )

    def __restore_related_one_to_one(self, field, strict, transaction_id, *args, **kwargs):
        """
        :param field: Field object representing the one-to-one relationship.
        :param strict: Flag indicating whether to raise an exception if the related object is not found.
        :param transaction_id: A UUID used to identify all objects that were deleted inside same transaction
        :param args: Additional positional arguments to be passed to the __restore_related_object method.
        :param kwargs: Additional keyword arguments to be passed to the __restore_related_object method.
        :return: None
        """
        related_object = getattr(self, field.name, None)
        if related_object and related_object.transaction_id == transaction_id:
            self.__restore_related_object(
                field, related_object, strict, transaction_id, *args, **kwargs
            )

    def __restore_related_one_to_many(self, field, strict, transaction_id, *args, **kwargs):
        """
        This method is used to restore related objects in a one-to-many relationship.

        :param field: A Django field representing the relationship between two models
        :param strict: A flag indicating whether to restore related objects even if they are not marked as deleted
        :param transaction_id: A UUID used to identify all objects that were deleted inside same transaction
        :param args: Additional positional arguments to be passed to the __restore_related_object method
        :param kwargs: Additional keyword arguments to be passed to the __restore_related_object method
        :return: None
        """
        remote_field = field.remote_field
        remote_model = field.remote_field.model
        if not issubclass(remote_model, SoftDeleteModel):
            raise ValueError('No related objects found')
        # TODO: it would be better to save object manager names in the variables
        for related_object in remote_model.deleted_objects.filter(
            **{remote_field.name: self, "transaction_id": transaction_id}
        ):
            self.__restore_related_object(
                field, related_object, strict, transaction_id, *args, **kwargs
            )

    # def __restore_related_many_to_many(self, field, strict, *args, **kwargs):
    #     """
    #     Restore related many-to-many objects.
    #
    #     :param field: The field representing the many-to-many relationship.
    #     :param strict: Whether to restore related objects strictly, i.e., only if their deletion is also restored.
    #     :param args: Additional positional arguments.
    #     :param kwargs: Additional keyword arguments.
    #     :return: None
    #     """
    #     remote_model = field.remote_field.model
    #     for related_object in remote_model.deleted_objects.filter(
    #             deleted_at__isnull=False
    #     ):
    #         self._restore_related_object(
    #             field, related_object, strict, *args, **kwargs
    #         )
