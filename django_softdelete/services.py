from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.db import transaction

EXCLUDE_DELETE_RELATIONS = ['transactions_sent', 'transactions_received']

def soft_delete_user(user):
    """
    Soft delete a user but keep exclude relation for tracking purposes.
    :param user: User to be deleted
    :return:
    """
    # Important user data

    # user.phone_number = ""
    # user.email = ""
    # user.first_name = ""
    # user.last_name = ""
    # user.username = ""
    # user.birth_date = ""

    user.is_deleted = True
    user.deleted_at = timezone.now()

    with transaction.atomic():

        for field in user._meta.get_fields():
            if field.is_relation:
                if field.name in EXCLUDE_DELETE_RELATIONS:
                    continue

                try:
                    related_object = getattr(user, field.name)
                except ObjectDoesNotExist:
                    continue
                except AttributeError:
                    continue

                if field.many_to_many:
                    related_object.clear()
                elif field.one_to_many:
                    for obj in related_object.all():
                        obj.delete()

                elif field.one_to_one:
                    if related_object:
                        related_object.delete()

        user.save()
