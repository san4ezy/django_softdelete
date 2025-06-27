from django.contrib import admin

from django_softdelete.admin import SoftDeletedModelAdmin, GlobalObjectsModelAdmin
from test_app.models import (
    Product, Employee, DeletedEmployeeProxy, GlobalEmployeeProxy, NotSoftRelatedModel
)


# @admin.register(Shop)
# class ShopAdmin(admin.ModelAdmin):
#     actions = (
#         "custom",
#     )
#
#     def custom(self, request, queryset):
#         for instance in queryset:
#             print(instance)
#
#
# @admin.register(Category)
# class CategoryAdmin(SoftDeletedModelAdmin):
#     actions = (
#         "custom",
#     )
#
#     def custom(self, request, queryset):
#         for instance in queryset:
#             print(instance)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    actions = [
        "custom",
    ]

    def custom(self, request, queryset):
        for instance in queryset:
            print(instance)


@admin.register(DeletedEmployeeProxy)
class DeletedEmployeeProxyAdmin(SoftDeletedModelAdmin):
    list_display = ("id", "name")
    actions = [
        "custom",
    ]

    def custom(self, request, queryset):
        for instance in queryset:
            print(instance)


@admin.register(GlobalEmployeeProxy)
class GlobalEmployeeProxyAdmin(GlobalObjectsModelAdmin):
    list_display = ("id", "name")
    actions = [
        "custom",
    ]

    def custom(self, request, queryset):
        for instance in queryset:
            print(instance)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass


@admin.register(NotSoftRelatedModel)
class NotSoftRelatedModelAdmin(admin.ModelAdmin):
    pass
