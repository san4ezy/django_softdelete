import pytest
from django.template import Template, Context
from test_app.models import Employee

@pytest.mark.django_db
class TestSoftDeleteTemplates:
    def test_restore_from_template_does_nothing(self):
        # Described here: https://github.com/san4ezy/django_softdelete/issues/67

        # Create and soft-delete an object
        obj = Employee.objects.create(name="To be restored")
        obj.delete()
        
        assert Employee.objects.count() == 0
        assert Employee.deleted_objects.count() == 1
        
        deleted_obj = Employee.deleted_objects.get(pk=obj.pk)
        
        # Try to call restore from template
        template = Template("{{ obj.restore }}")
        context = Context({"obj": deleted_obj})
        template.render(context)
        
        # It should NOT be restored because restore() has alters_data=True
        assert Employee.objects.count() == 0
        assert Employee.deleted_objects.count() == 1

    def test_hard_delete_from_template_does_nothing(self):
        # Described here: https://github.com/san4ezy/django_softdelete/issues/67

        # Create an object
        obj = Employee.objects.create(name="To be hard deleted")
        
        assert Employee.objects.count() == 1
        
        # Try to call hard_delete from template
        template = Template("{{ obj.hard_delete }}")
        context = Context({"obj": obj})
        template.render(context)
        
        # It should NOT be deleted because hard_delete() has alters_data=True
        assert Employee.objects.count() == 1

    def test_queryset_hard_delete_from_template_does_nothing(self):
        # Described here: https://github.com/san4ezy/django_softdelete/issues/67

        # Create an object
        Employee.objects.create(name="To be hard deleted via QS")
        
        qs = Employee.objects.all()
        assert qs.count() == 1
        
        # Try to call hard_delete from template
        template = Template("{{ qs.hard_delete }}")
        context = Context({"qs": qs})
        template.render(context)
        
        # It should NOT be deleted because hard_delete() has alters_data=True
        assert Employee.objects.count() == 1
