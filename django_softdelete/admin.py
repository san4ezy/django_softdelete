from django.contrib import admin


class SoftDeletedModelAdmin(admin.ModelAdmin):
    """
    SoftDeletedModelAdmin
    Class representing a ModelAdmin for soft deleted objects in Django admin.
    The standard ModelAdmin works with a default object manager as well.
    """
    def get_queryset(self, request):
        super().get_queryset()
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
        super().get_queryset()
        qs = self.model.global_objects.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs
