from unittest.mock import patch

import pytest
from django.db.models.deletion import ProtectedError
from django.db.models.signals import pre_delete
from django.db.models.signals import post_delete

from django_softdelete.exceptions import SoftDeleteException
from django_softdelete.signals import post_soft_delete
from django_softdelete.signals import post_hard_delete
from django_softdelete.signals import post_restore

from django.utils import timezone
from test_app.models import *


@pytest.mark.django_db
class TestSoftDeleteModel:
    """

    The TestSoftDeleteModel class contains test methods for testing the functionality
    of soft deletion and restoration of objects.

    """
    def assert_objects_count(self, model, a: int, d: int, g: int = None):
        """
        Assert Objects Count Method

        This method is used to assert the count of objects, deleted objects, and global objects in a given model.

        :param model: The model for which the counts are to be asserted.
        :type model: Any valid Django model.
        :param a: The expected count of objects in the model.
        :type a: int
        :param d: The expected count of deleted objects in the model.
        :type d: int
        :param g: The expected count of global objects in the model. Default is None, which will be calculated as the sum of `a` and `d`.
        :type g: int, optional
        :return: A boolean value indicating whether the counts match the expected values. Returns True if all counts match, False otherwise.
        :rtype: bool

        Example usage:
            >>> assert_objects_count(MyModel, 10, 5)
            True
            >>> assert_objects_count(MyModel, 10, 5, 15)
            True
            >>> assert_objects_count(MyModel, 10, 5, 14)
            False
        """
        if g is None:
            g = a + d
        return all([
            model.objects.count() == a,
            model.deleted_objects.count() == d,
            model.global_objects.count() == g,
        ])

    def assert_object_in(self, obj, a: bool, d: bool, g: bool = None):
        """
        Asserts that the given object exists in the specified model or models.

        :param obj: The object to assert existence for.
        :param a: A boolean indicating whether the object should exist in the model's regular objects.
        :param d: A boolean indicating whether the object should exist in the model's deleted_objects.
        :param g: A boolean indicating whether the object should exist in the model's global_objects (optional).
        :return: True if the object exists in all specified models, False otherwise.
        """
        model = obj.__class__
        s = [
            model.objects.filter(id=obj.id).exists() is a,
            model.deleted_objects.filter(id=obj.id).exists() is d,
        ]
        if g is not None:
            s.append(model.global_objects.filter(id=obj.id).exists() is g)
        return all(s)

    def test_is_deleted(self, product):
        """
        Check if the 'is_deleted' attribute of a product is set correctly.
        """
        now = timezone.now()
        assert not product.is_deleted
        assert product.deleted_at is None
        product.deleted_at = now
        product.save()
        assert product.is_deleted

    def test_is_restored(self, product):
        """
        Check if the 'is_deleted' attribute of a product is set correctly.
        """
        now = timezone.now()
        assert not product.is_restored
        assert product.restored_at is None
        product.restored_at = now
        product.save()
        assert product.is_restored

    def test_soft_delete(self, product):
        """
        Test the soft delete functionality of a product.
        """
        assert not product.is_deleted
        assert self.assert_objects_count(Product, 1, 0 ,1)

        product.delete()
        product.refresh_from_db()
        assert product.is_deleted
        assert self.assert_objects_count(Product, 0, 1, 1)

    # def test_soft_deleted_objects_keep_relations(
    #         self, product_factory, option, product_landing, product,
    # ):
    #     # product = product_factory(option=option, landing=product_landing)
    #     shop = product.shop
    #     print(shop.product_set.all())
    #     product.delete()
    #
    #     # assert Option.deleted_objects.filter(product__pk=product.pk).exists()
    #     # assert ProductLanding.deleted_objects.filter(product__pk=product.pk).exists()
    #     # assert Shop.deleted_objects.filter(pk=product.shop.pk).exists()
    #     # shop.refresh_from_db()
    #     print(product.pk)
    #     print(shop.product_set.all())
    #     print(shop.product_set.filter(pk=product.pk))
    #     assert shop.product_set.filter(pk=product.pk).exists()

    def test_hard_delete(self, product):
        """
        Delete the product permanently from the database.
        """
        obj_id = product.id
        product.hard_delete()

        with pytest.raises(Product.DoesNotExist):
            Product.objects.get(id=obj_id)

        assert self.assert_objects_count(Product, 0, 0, 0)

    def test_restore(self, product):
        """
        Restores a deleted product in the database.
        """
        product.delete()
        obj_id = product.id

        product.restore()
        product.refresh_from_db()
        assert not product.is_deleted
        assert product.id == obj_id
        assert product.is_restored

        assert self.assert_objects_count(Product, 1, 0, 1)

    def test_queryset_soft_delete(self, product_factory):
        """
        Test soft deleting queryset.
        """
        obj1 = product_factory()
        obj2 = product_factory()
        obj3 = product_factory()

        Product.objects.filter(id=obj1.id).delete()
        assert self.assert_objects_count(Product, 2, 1, 3)
        assert self.assert_object_in(obj1, False, True, True)

        obj1.refresh_from_db()
        assert obj1.is_deleted

    def test_queryset_soft_delete_multiple(self, product_factory):
        """
        Test the soft deletion of multiple objects in the queryset.
        """
        obj1 = product_factory()
        obj2 = product_factory()
        obj3 = product_factory()

        ids = [obj1.id, obj2.id, ]
        Product.objects.filter(id__in=ids).delete()
        assert self.assert_objects_count(Product, 1, 2, 3)
        assert self.assert_object_in(obj1, False, True, True)
        assert self.assert_object_in(obj2, False, True, True)
        assert self.assert_object_in(obj3, True, False, True)

        obj1.refresh_from_db()
        assert obj1.is_deleted
        obj2.refresh_from_db()
        assert obj2.is_deleted
        obj3.refresh_from_db()
        assert not obj3.is_deleted

    def test_queryset_hard_delete(self, product_factory):
        """
        Test the hard delete functionality of the queryset.
        """
        obj1 = product_factory()
        obj2 = product_factory()
        obj3 = product_factory()

        ids = [obj1.id, obj2.id, ]
        Product.objects.filter(id__in=ids).hard_delete()
        assert self.assert_objects_count(Product, 1, 0, 1)
        assert self.assert_object_in(obj1, False, False, False)
        assert self.assert_object_in(obj2, False, False, False)
        assert self.assert_object_in(obj3, True, False, True)

        with pytest.raises(Product.DoesNotExist):
            Product.objects.get(id=obj1.id)
        with pytest.raises(Product.DoesNotExist):
            Product.objects.get(id=obj2.id)
        assert Product.objects.filter(id=obj3.id).exists()

    def test_queryset_restore(self, product_factory):
        """
        Test the restoration of deleted objects in the queryset.
        """
        obj1 = product_factory()
        obj2 = product_factory()
        obj3 = product_factory()
        ids = [obj1.id, obj2.id, ]

        Product.objects.all().delete()
        Product.deleted_objects.filter(id__in=ids).restore()
        assert self.assert_objects_count(Product, 2, 1, 3)
        assert self.assert_object_in(obj1, True, False, True)
        assert self.assert_object_in(obj2, True, False, True)
        assert self.assert_object_in(obj3, False, True, True)

        obj1.refresh_from_db()
        assert not obj1.is_deleted
        assert obj1.is_restored
        obj2.refresh_from_db()
        assert not obj2.is_deleted
        assert obj2.is_restored
        obj3.refresh_from_db()
        assert obj3.is_deleted
        assert not obj3.is_restored

    def test_delete_cascade(self, product_factory, option, product_landing, shop):
        """
        The test_delete_cascade method is responsible for testing the cascade
        delete functionality of a product.
        """
        product = product_factory(option=option, landing=product_landing)
        product.delete()

        option.refresh_from_db()
        product_landing.refresh_from_db()
        shop.refresh_from_db()
        assert self.assert_object_in(option, False, True, True)
        assert option.is_deleted
        assert self.assert_object_in(product_landing, False, True, True)
        assert product_landing.is_deleted

        # The model the product related to is still alive
        assert self.assert_object_in(shop, True, False, True)
        assert not shop.is_deleted

    def test_restore_cascade(self, option, product_image):
        """
        The test is responsible for testing the cascade
        restoring functionality of a product.
        """
        product = option.product
        product.images.add(product_image)
        product.delete()

        # Test restore
        product.restore()

        # product = Product.global_objects.get(pk=product.pk)
        # option = Option.global_objects.get(pk=option.pk)
        # product_image = ProductImage.global_objects.get(pk=product_image.pk)

        product.refresh_from_db()
        option.refresh_from_db()
        product_image.refresh_from_db()
        assert self.assert_object_in(product, True, False, True)
        assert self.assert_object_in(option, True, False, True)
        assert self.assert_object_in(product_image, True, False, True)
        assert not product.is_deleted
        assert not option.is_deleted
        assert not product_image.is_deleted
        assert product.is_restored
        assert option.is_restored
        # assert product_image.is_restored  # TODO: fix this

    def test_hard_delete_cascade(self, option):
        """
        Test the hard delete cascade functionality.
        """
        product = option.product
        product.hard_delete()
        assert not Product.deleted_objects.filter(id=product.id)
        assert not Option.objects.filter(id=option.id).exists()

    def test_delete_reverse_cascade(self, product_factory, category):
        product = product_factory()
        category.delete()
        product.refresh_from_db()
        assert product.is_deleted

    def test_atomic(self, product):
        """
        This test checks if deletion and restore methods of the SoftDeleteModel
        are atomic and can roll back in case of an error.
        """
        with patch('test_app.models.Product.save') as mock_save:
            mock_save.side_effect = ValueError("Artificial error")
            with pytest.raises(ValueError) as e:
                product.delete()
            assert str(e.value) == "Artificial error"
        assert self.assert_object_in(product, True, False, True)

    def test_signal_calls_on_soft_delete(self, product, signal_mock):
        with (
            signal_mock(pre_delete, Product) as pre_delete_mock,
            signal_mock(post_delete, Product) as post_delete_mock,
            signal_mock(post_soft_delete, Product) as post_soft_delete_mock,
        ):
            product.delete()
            assert pre_delete_mock.call_count == 1
            assert post_delete_mock.call_count == 1
            assert post_soft_delete_mock.call_count == 1

    def test_signal_calls_on_hard_delete(self, product, signal_mock):
        with (
            signal_mock(pre_delete, Product) as pre_delete_mock,
            signal_mock(post_delete, Product) as post_delete_mock,
            signal_mock(post_hard_delete, Product) as post_hard_delete_mock,
        ):
            product.hard_delete()
            assert pre_delete_mock.call_count == 1
            assert post_delete_mock.call_count == 1
            assert post_hard_delete_mock.call_count == 1

    def test_signal_calls_on_restore(self, product, signal_mock):
        with signal_mock(post_restore, Product) as post_restore_mock:
            product.restore()
            assert post_restore_mock.call_count == 1

    def test_delete_with_restricted_relation(
            self, product_restricted_category, category
    ):
        p = product_restricted_category
        with pytest.raises(ProtectedError) as e:
            category.delete()
            err_msg = str(e.value)
            assert f"Cannot delete Category object ({category.pk})" in err_msg
            assert f"ProductRestrictedCategory object ({p.pk})" in err_msg
            assert f"related with RESTRICT" in err_msg

        p.refresh_from_db()
        assert not p.is_deleted
        assert not category.is_deleted

    # def test_delete_with_not_soft_delete_model_relation(
    #         self, not_soft_related_model, product_not_soft_relation,
    # ):
    #     with pytest.raises(SoftDeleteException) as e:
    #         product_not_soft_relation.delete()
    #     assert str(e.value) == "NotSoftRelatedModel is not a subclass of SoftDeleteModel."

    def test_delete_with_not_soft_delete_model_relation_not_strict(
            self, not_soft_related_model, product_not_soft_relation,
    ):
        product_not_soft_relation.delete(strict=False)
        product_not_soft_relation.refresh_from_db()
        assert product_not_soft_relation.is_deleted
        assert not NotSoftRelatedModel.objects.filter(
            pk=not_soft_related_model.pk
        ).exists()

    def test_delete_only_target_instances(
            self, product, another_product, option, another_option,
    ):
        product.delete()
        product.refresh_from_db()
        option.refresh_from_db()
        another_product.refresh_from_db()
        another_option.refresh_from_db()
        assert product.is_deleted
        assert option.is_deleted
        assert not another_product.is_deleted
        assert not another_option.is_deleted
