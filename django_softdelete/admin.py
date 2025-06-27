from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.template.response import TemplateResponse

from django_softdelete.filters import SoftDeleteFilter


@admin.action(description="Soft-delete selected %(verbose_name_plural)s")
def soft_delete_selected(modeladmin, request, queryset):
    """Soft delete selected objects with confirmation."""
    # Check if confirmation was posted
    if request.POST.get('post') and request.POST.get('_selected_action'):
        deleted_count = queryset.count()
        for obj in queryset:
            obj.delete()

        messages.success(request, f"Successfully soft-deleted {deleted_count} {modeladmin.model._meta.verbose_name_plural}.")
        return None

    # Show confirmation page
    context = {
        'title': f"Are you sure you want to soft-delete the selected {modeladmin.model._meta.verbose_name_plural}?",
        'objects_name': modeladmin.model._meta.verbose_name_plural,
        'deletable_objects': [str(obj) for obj in queryset],
        'queryset': queryset,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'opts': modeladmin.model._meta,
        'action_name': 'soft_delete_selected',
        'preserved': [],
        'protected': [],
    }

    return TemplateResponse(
        request,
        'admin/soft_delete_confirmation.html',
        context
    )


@admin.action(description="Hard-delete selected %(verbose_name_plural)s")
def hard_delete_selected(modeladmin, request, queryset):
    """Hard delete selected objects with confirmation."""
    # Check if confirmation was posted
    if request.POST.get('post') and request.POST.get('_selected_action'):
        deleted_count = queryset.count()
        for obj in queryset:
            obj.hard_delete()

        messages.success(request, f"Successfully hard-deleted {deleted_count} {modeladmin.model._meta.verbose_name_plural}.")
        return None

    # Show confirmation page
    context = {
        'title': f"Are you sure you want to permanently delete the selected {modeladmin.model._meta.verbose_name_plural}?",
        'objects_name': modeladmin.model._meta.verbose_name_plural,
        'deletable_objects': [str(obj) for obj in queryset],
        'queryset': queryset,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'opts': modeladmin.model._meta,
        'action_name': 'hard_delete_selected',
        'preserved': [],
        'protected': [],
    }

    return TemplateResponse(
        request,
        'admin/hard_delete_confirmation.html',
        context
    )


@admin.action(description="Restore selected %(verbose_name_plural)s")
def restore_selected(modeladmin, request, queryset):
    """Restore selected objects with confirmation."""
    # Check if confirmation was posted
    if request.POST.get('post') and request.POST.get('_selected_action'):
        restored_count = queryset.count()
        queryset.restore()

        messages.success(request, f"Successfully restored {restored_count} {modeladmin.model._meta.verbose_name_plural}.")
        return None

    # Show confirmation page
    context = {
        'title': f"Are you sure you want to restore the selected {modeladmin.model._meta.verbose_name_plural}?",
        'objects_name': modeladmin.model._meta.verbose_name_plural,
        'deletable_objects': [str(obj) for obj in queryset],
        'queryset': queryset,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'opts': modeladmin.model._meta,
        'action_name': 'restore_selected',
        'preserved': [],
        'protected': [],
    }

    return TemplateResponse(
        request,
        'admin/restore_confirmation.html',
        context
    )


REGULAR_DELETE_ACTION_NAME = "delete_selected"
SOFT_DELETE_ACTION = {"soft_delete_selected": (soft_delete_selected, "soft_delete_selected", "Soft-delete selected %(verbose_name_plural)s")}
HARD_DELETE_ACTION = {"hard_delete_selected": (hard_delete_selected, "hard_delete_selected", "Hard-delete selected %(verbose_name_plural)s")}
RESTORE_ACTION = {"restore_selected": (restore_selected, "restore_selected", "Restore selected %(verbose_name_plural)s")}


class SoftDeletedModelAdmin(admin.ModelAdmin):
    """
    SoftDeletedModelAdmin
    Class representing a ModelAdmin for soft deleted objects in Django admin.
    The standard ModelAdmin works with a default object manager as well.
    """
    def get_queryset(self, request):
        qs = self.model.deleted_objects.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop(REGULAR_DELETE_ACTION_NAME, None)  # Remove regular delete action
        actions.update(HARD_DELETE_ACTION)
        actions.update(RESTORE_ACTION)
        return actions


class GlobalObjectsModelAdmin(admin.ModelAdmin):
    """
    GlobalObjectsModelAdmin
    Class representing a ModelAdmin for both: deleted and alive objects in Django admin.
    The standard ModelAdmin works with a default object manager as well.
    """
    def get_queryset(self, request):
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

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop(REGULAR_DELETE_ACTION_NAME, None)  # Remove regular delete action
        actions.update(SOFT_DELETE_ACTION)
        actions.update(HARD_DELETE_ACTION)
        actions.update(RESTORE_ACTION)
        return actions
