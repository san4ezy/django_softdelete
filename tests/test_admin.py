import pytest
import uuid
from unittest.mock import Mock, MagicMock
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import RequestFactory
from django.utils import timezone

from django_softdelete.admin import (
    SoftDeletedModelAdmin,
    GlobalObjectsModelAdmin,
    hard_delete_selected,
    restore_selected,
)
from django_softdelete.filters import SoftDeleteFilter
from test_app.models import Category, Employee, Shop, Product



@pytest.fixture
def category_admin(admin_site):
    """Create CategoryAdmin instance"""
    return SoftDeletedModelAdmin(Category, admin_site)


@pytest.fixture
def employee_admin(admin_site):
    """Create EmployeeAdmin instance"""
    return GlobalObjectsModelAdmin(Employee, admin_site)


@pytest.fixture
def shop_admin(admin_site):
    """Create regular ModelAdmin for comparison"""
    return admin.ModelAdmin(Shop, admin_site)


@pytest.fixture
def setup_test_data(name):
    """Create test data for admin tests"""
    # Create alive objects
    alive_category = Category.objects.create(name=f"Alive {name}")
    alive_employee = Employee.objects.create(name=f"Alive {name}")
    alive_shop = Shop.objects.create(name=f"Alive {name}")

    # Create and soft delete objects
    deleted_category = Category.objects.create(name=f"Deleted {name}")
    deleted_employee = Employee.objects.create(name=f"Deleted {name}")
    deleted_shop = Shop.objects.create(name=f"Deleted {name}")

    # Soft delete some objects
    deleted_category.delete()
    deleted_employee.delete()
    deleted_shop.delete()

    return {
        'alive': {
            'category': alive_category,
            'employee': alive_employee,
            'shop': alive_shop,
        },
        'deleted': {
            'category': deleted_category,
            'employee': deleted_employee,
            'shop': deleted_shop,
        }
    }


@pytest.mark.django_db
class TestRegularAdmin:
    # ShopAdmin is a regular ModelAdmin
    def test_list(self, admin_request, shop, shop_admin):
        adm_list_count = shop_admin.get_queryset(admin_request).count()
        obj_count = shop_admin.model.objects.count()
        assert adm_list_count == obj_count

    def test_delete(self, admin_request, shop, shop_admin):
        init_count = shop_admin.model.objects.count()
        qs = shop_admin.model.objects.filter(id=shop.id)
        shop_admin.delete_queryset(admin_request, qs)
        # check it softly deleted
        assert init_count - 1 == shop_admin.model.objects.count()
        assert 1 == shop_admin.model.deleted_objects.count()


@pytest.mark.django_db
class TestDeletedAdmin:
    # CategoryAdmin is a SoftDeletedModelAdmin
    def test_list(self, admin_request, category, category_admin):
        adm_list_count = category_admin.get_queryset(admin_request).count()
        obj_count = category_admin.model.deleted_objects.count()
        assert adm_list_count == obj_count

    def test_delete(self, admin_request, category, category_admin):
        init_count = category_admin.model.objects.count()
        qs = category_admin.model.objects.filter(id=category.id)
        category_admin.delete_queryset(admin_request, qs)
        # check it hardly deleted
        assert init_count - 1 == category_admin.model.objects.count()
        assert 1 == category_admin.model.deleted_objects.count()


@pytest.mark.django_db
class TestGlobalAdmin:
    # EmployeeAdmin is a GlobalObjectsModelAdmin
    def test_list(self, admin_request, employee, employee_admin):
        adm_list_count = employee_admin.get_queryset(admin_request).count()
        obj_count = employee_admin.model.global_objects.count()
        assert adm_list_count == obj_count


# class TestSoftDeletedModelAdmin:
#     """Test SoftDeletedModelAdmin functionality"""
#
#     # def test_initialization(self, category_admin):
#     #     """Test that SoftDeletedModelAdmin initializes correctly"""
#     #     assert isinstance(category_admin, SoftDeletedModelAdmin)
#     #     assert category_admin.model == Category
#     #
#     # def test_actions_include_custom_actions(self, category_admin):
#     #     """Test that custom admin actions are included"""
#     #     actions = category_admin.actions
#     #     assert hard_delete_selected_items in actions
#     #     assert restore_selected_items in actions
#     #
#     # def test_actions_include_default_actions(self, category_admin):
#     #     """Test that default ModelAdmin actions are preserved"""
#     #     actions = category_admin.actions
#     #     # Default admin actions should be included
#     #     assert len(actions) >= 3  # At least default + 2 custom actions
#     #
#     def test_get_queryset_returns_deleted_objects_only(self, category_admin, admin_request, setup_test_data):
#         """Test that get_queryset returns only soft-deleted objects"""
#         queryset = category_admin.get_queryset(admin_request)
#
#         # Should only contain deleted objects
#         assert queryset.count() == 1
#         deleted_category = setup_test_data['deleted']['category']
#         assert deleted_category in queryset
#
#         # Should not contain alive objects
#         alive_category = setup_test_data['alive']['category']
#         assert alive_category not in queryset
#
#     def test_get_queryset_respects_ordering(self, category_admin, admin_request, setup_test_data):
#         """Test that get_queryset respects ordering"""
#         # Create multiple deleted objects with different names
#         cat1 = Category.objects.create(name="ZZZ Category")
#         cat2 = Category.objects.create(name="AAA Category")
#         cat1.delete()
#         cat2.delete()
#
#         # Mock get_ordering to return name ordering
#         category_admin.get_ordering = Mock(return_value=['name'])
#
#         queryset = category_admin.get_queryset(admin_request)
#         names = list(queryset.values_list('name', flat=True))
#
#         # Should be ordered by name
#         assert names == sorted(names)
#
#     def test_get_queryset_calls_super(self, category_admin, admin_request):
#         """Test that get_queryset calls super().get_queryset()"""
#         with pytest.mock.patch.object(admin.ModelAdmin, 'get_queryset') as mock_super:
#             mock_super.return_value = Category.objects.none()
#             category_admin.get_queryset(admin_request)
#             mock_super.assert_called_once_with(admin_request)
#
#     def test_get_queryset_with_no_ordering(self, category_admin, admin_request, setup_test_data):
#         """Test get_queryset when no ordering is specified"""
#         category_admin.get_ordering = Mock(return_value=None)
#
#         queryset = category_admin.get_queryset(admin_request)
#         # Should still work and return deleted objects
#         assert queryset.count() == 1
#
#
# class TestGlobalObjectsModelAdmin:
#     """Test GlobalObjectsModelAdmin functionality"""
#
#     def test_initialization(self, employee_admin):
#         """Test that GlobalObjectsModelAdmin initializes correctly"""
#         assert isinstance(employee_admin, GlobalObjectsModelAdmin)
#         assert employee_admin.model == Employee
#
#     def test_actions_include_custom_actions(self, employee_admin):
#         """Test that custom admin actions are included"""
#         actions = employee_admin.actions
#         assert hard_delete_selected_items in actions
#         assert restore_selected_items in actions
#
#     def test_get_queryset_returns_all_objects(self, employee_admin, admin_request, setup_test_data):
#         """Test that get_queryset returns all objects (deleted and alive)"""
#         queryset = employee_admin.get_queryset(admin_request)
#
#         # Should contain both alive and deleted objects
#         assert queryset.count() == 2
#
#         alive_employee = setup_test_data['alive']['employee']
#         deleted_employee = setup_test_data['deleted']['employee']
#
#         assert alive_employee in queryset
#         assert deleted_employee in queryset
#
#     def test_get_queryset_respects_ordering(self, employee_admin, admin_request):
#         """Test that get_queryset respects ordering"""
#         # Create employees with different names
#         emp1 = Employee.objects.create(name="ZZZ Employee")
#         emp2 = Employee.objects.create(name="AAA Employee")
#         emp1.delete()  # Mix of deleted and alive
#
#         employee_admin.get_ordering = Mock(return_value=['name'])
#
#         queryset = employee_admin.get_queryset(admin_request)
#         names = list(queryset.values_list('name', flat=True))
#
#         # Should be ordered by name
#         assert names == sorted(names)
#
#     def test_get_list_filter_includes_soft_delete_filter(self, employee_admin, admin_request):
#         """Test that get_list_filter includes SoftDeleteFilter"""
#         list_filter = employee_admin.get_list_filter(admin_request)
#
#         assert SoftDeleteFilter in list_filter
#
#     def test_get_list_filter_preserves_existing_filters(self, employee_admin, admin_request):
#         """Test that existing list_filter values are preserved"""
#         # Mock existing list_filter
#         existing_filters = ['name', 'is_active']
#         employee_admin.list_filter = existing_filters
#
#         list_filter = employee_admin.get_list_filter(admin_request)
#
#         # Should include existing filters plus SoftDeleteFilter
#         assert 'name' in list_filter
#         assert 'is_active' in list_filter
#         assert SoftDeleteFilter in list_filter
#
#     def test_get_list_filter_handles_tuple_list_filter(self, employee_admin, admin_request):
#         """Test that get_list_filter handles tuple list_filter correctly"""
#         # Set list_filter as tuple
#         employee_admin.list_filter = ('name', 'created_at')
#
#         list_filter = employee_admin.get_list_filter(admin_request)
#
#         # Should convert to list and add SoftDeleteFilter
#         assert isinstance(list_filter, list)
#         assert 'name' in list_filter
#         assert 'created_at' in list_filter
#         assert SoftDeleteFilter in list_filter
#
#     def test_get_list_filter_handles_none_list_filter(self, employee_admin, admin_request):
#         """Test that get_list_filter handles None list_filter"""
#         # Mock super().get_list_filter to return None
#         with pytest.mock.patch.object(admin.ModelAdmin, 'get_list_filter') as mock_super:
#             mock_super.return_value = None
#
#             list_filter = employee_admin.get_list_filter(admin_request)
#
#             # Should just contain SoftDeleteFilter
#             assert list_filter == [SoftDeleteFilter]
#
#
# class TestCustomAdminActions:
#     """Test custom admin actions"""
#
#     def test_hard_delete_selected_items_action(self, setup_test_data, admin_request):
#         """Test hard_delete_selected_items action"""
#         deleted_category = setup_test_data['deleted']['category']
#         alive_category = setup_test_data['alive']['category']
#
#         # Create queryset with both deleted and alive objects
#         queryset = Category.global_objects.filter(
#             id__in=[deleted_category.id, alive_category.id]
#         )
#
#         mock_admin = Mock()
#
#         # Mock hard_delete method
#         deleted_category.hard_delete = Mock()
#         alive_category.hard_delete = Mock()
#
#         # Execute action
#         hard_delete_selected_items(mock_admin, admin_request, queryset)
#
#         # Both objects should have hard_delete called
#         deleted_category.hard_delete.assert_called_once()
#         alive_category.hard_delete.assert_called_once()
#
#     def test_restore_selected_items_action(self, setup_test_data, admin_request):
#         """Test restore_selected_items action"""
#         deleted_category = setup_test_data['deleted']['category']
#
#         # Create queryset with deleted objects
#         queryset = Category.deleted_objects.filter(id=deleted_category.id)
#
#         mock_admin = Mock()
#
#         # Execute action
#         restore_selected_items(mock_admin, admin_request, queryset)
#
#         # Object should be restored
#         deleted_category.refresh_from_db()
#         assert not deleted_category.is_deleted
#         assert deleted_category.restored_at is not None
#
#     def test_custom_admin_actions_list(self):
#         """Test that custom_admin_actions contains expected actions"""
#         assert hard_delete_selected_items in custom_admin_actions
#         assert restore_selected_items in custom_admin_actions
#         assert len(custom_admin_actions) == 2
#
#     def test_action_descriptions(self):
#         """Test that actions have proper descriptions"""
#         assert hard_delete_selected_items.short_description == "Hard delete selected items"
#         assert restore_selected_items.short_description == "Restore selected items"
#
#
# class TestAdminIntegration:
#     """Test admin integration with soft delete functionality"""
#
#     def test_soft_deleted_admin_with_real_queryset(self, category_admin, admin_request, setup_test_data):
#         """Test SoftDeletedModelAdmin with real database queries"""
#         # Get the actual queryset
#         queryset = category_admin.get_queryset(admin_request)
#
#         # Verify it uses deleted_objects manager
#         assert queryset.model == Category
#         # Should only show deleted objects
#         for obj in queryset:
#             assert obj.is_deleted
#
#     def test_global_objects_admin_with_real_queryset(self, employee_admin, admin_request, setup_test_data):
#         """Test GlobalObjectsModelAdmin with real database queries"""
#         queryset = employee_admin.get_queryset(admin_request)
#
#         # Should show both deleted and alive objects
#         deleted_count = sum(1 for obj in queryset if obj.is_deleted)
#         alive_count = sum(1 for obj in queryset if not obj.is_deleted)
#
#         assert deleted_count > 0
#         assert alive_count > 0
#
#     def test_admin_actions_with_transaction_id(self, setup_test_data, admin_request):
#         """Test admin actions respect transaction_id for related objects"""
#         # Create related objects with same transaction_id
#         shop = setup_test_data['alive']['shop']
#         category = setup_test_data['alive']['category']
#
#         product = Product.objects.create(
#             name="Test Product",
#             shop=shop,
#             category=category,
#             price=100
#         )
#
#         # Delete with transaction_id
#         transaction_id = uuid.uuid4()
#         product.delete(transaction_id=transaction_id)
#
#         # Create queryset and restore
#         queryset = Product.deleted_objects.filter(id=product.id)
#         mock_admin = Mock()
#
#         restore_selected_items(mock_admin, admin_request, queryset)
#
#         # Verify restoration
#         product.refresh_from_db()
#         assert not product.is_deleted
#         assert product.transaction_id is None
#
#     def test_admin_with_ordering_and_filters(self, employee_admin, admin_request):
#         """Test admin with both ordering and filters"""
#         # Create test data
#         emp1 = Employee.objects.create(name="Alpha")
#         emp2 = Employee.objects.create(name="Beta")
#         emp3 = Employee.objects.create(name="Gamma")
#
#         emp2.delete()  # Delete middle one
#
#         # Set ordering
#         employee_admin.ordering = ['name']
#
#         # Get queryset
#         queryset = employee_admin.get_queryset(admin_request)
#
#         # Should include all objects in correct order
#         names = list(queryset.values_list('name', flat=True))
#         assert names == ['Alpha', 'Beta', 'Gamma']
#
#         # Test filter functionality
#         list_filter = employee_admin.get_list_filter(admin_request)
#         assert SoftDeleteFilter in list_filter
#
#
# class TestAdminErrors:
#     """Test error handling in admin classes"""
#
#     def test_soft_deleted_admin_handles_empty_queryset(self, category_admin, admin_request):
#         """Test SoftDeletedModelAdmin handles empty queryset gracefully"""
#         # Clear all categories
#         Category.global_objects.all().hard_delete()
#
#         queryset = category_admin.get_queryset(admin_request)
#         assert queryset.count() == 0
#
#     def test_global_objects_admin_handles_empty_queryset(self, employee_admin, admin_request):
#         """Test GlobalObjectsModelAdmin handles empty queryset gracefully"""
#         # Clear all employees
#         Employee.global_objects.all().hard_delete()
#
#         queryset = employee_admin.get_queryset(admin_request)
#         assert queryset.count() == 0
#
#     def test_hard_delete_action_with_empty_queryset(self, admin_request):
#         """Test hard_delete action with empty queryset"""
#         queryset = Category.objects.none()
#         mock_admin = Mock()
#
#         # Should not raise error
#         hard_delete_selected_items(mock_admin, admin_request, queryset)
#
#     def test_restore_action_with_empty_queryset(self, admin_request):
#         """Test restore action with empty queryset"""
#         queryset = Category.objects.none()
#         mock_admin = Mock()
#
#         # Should not raise error
#         restore_selected_items(mock_admin, admin_request, queryset)
#
#
# class TestAdminActionsDescription:
#     """Test admin action descriptions and metadata"""
#
#     def test_hard_delete_action_has_correct_decorator(self):
#         """Test that hard_delete action has correct admin.action decorator"""
#         assert hasattr(hard_delete_selected_items, 'short_description')
#         assert hard_delete_selected_items.short_description == "Hard delete selected items"
#
#     def test_restore_action_has_correct_decorator(self):
#         """Test that restore action has correct admin.action decorator"""
#         assert hasattr(restore_selected_items, 'short_description')
#         assert restore_selected_items.short_description == "Restore selected items"
#
#
# @pytest.mark.django_db
# class TestAdminDatabaseOperations:
#     """Test admin operations that require database transactions"""
#
#     def test_bulk_hard_delete_through_admin(self, setup_test_data, admin_request):
#         """Test bulk hard delete through admin action"""
#         # Create multiple objects
#         cats = []
#         for i in range(3):
#             cat = Category.objects.create(name=f"Category {i}")
#             cat.delete()  # Soft delete
#             cats.append(cat)
#
#         # Get deleted objects queryset
#         queryset = Category.deleted_objects.filter(
#             id__in=[cat.id for cat in cats]
#         )
#
#         initial_count = Category.global_objects.count()
#         mock_admin = Mock()
#
#         # Execute hard delete action
#         hard_delete_selected_items(mock_admin, admin_request, queryset)
#
#         # Verify objects are actually deleted from database
#         final_count = Category.global_objects.count()
#         assert final_count == initial_count - 3
#
#         # Verify objects can't be found in any manager
#         for cat in cats:
#             assert not Category.global_objects.filter(id=cat.id).exists()
#
#     def test_bulk_restore_through_admin(self, setup_test_data, admin_request):
#         """Test bulk restore through admin action"""
#         # Create and soft delete multiple objects
#         cats = []
#         for i in range(3):
#             cat = Category.objects.create(name=f"Category {i}")
#             cat.delete()
#             cats.append(cat)
#
#         # Get deleted objects queryset
#         queryset = Category.deleted_objects.filter(
#             id__in=[cat.id for cat in cats]
#         )
#
#         mock_admin = Mock()
#
#         # Execute restore action
#         restore_selected_items(mock_admin, admin_request, queryset)
#
#         # Verify all objects are restored
#         for cat in cats:
#             cat.refresh_from_db()
#             assert not cat.is_deleted
#             assert cat.restored_at is not None
#
#         # Verify they appear in normal manager
#         alive_count = Category.objects.filter(
#             id__in=[cat.id for cat in cats]
#         ).count()
#         assert alive_count == 3
