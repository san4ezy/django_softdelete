from django.contrib import admin


class SoftDeletedModelAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = self.model.deleted_objects.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs
