from django.contrib import admin

from django_softdelete.filters import SoftDeleteFilter


class SoftDeletedModelAdmin(admin.ModelAdmin):
    """
    SoftDeletedModelAdmin
    Class representing a ModelAdmin for soft deleted objects in Django admin.
    The standard ModelAdmin works with a default object manager as well.
    """
    def get_queryset(self, request):
        super().get_queryset(request)
        qs = self.model.deleted_objects.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs


class GlobalObjectsModelAdmin(admin.ModelAdmin):
    """
    GlobalObjectsModelAdmin
    Class representing a ModelAdmin for both: deleted and alive objects in Django admin.
    The standard ModelAdmin works with a default object manager as well.
    """
    def get_queryset(self, request):
        super().get_queryset(request)
        qs = self.model.global_objects.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request) or []
        if not isinstance(list_filter, list):
            list_filter = list(list_filter)
        list_filter.append(SoftDeleteFilter)
        return list_filter
