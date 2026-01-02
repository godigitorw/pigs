# users/mixins.py
"""
Mixins to restrict edit access for farm workers
"""
from django.contrib import messages
from django.shortcuts import redirect

class RestrictWorkerEditMixin:
    """
    Mixin to restrict farm workers from editing existing records.
    Farm workers can create new records but cannot update existing ones.
    """
    def dispatch(self, request, *args, **kwargs):
        # Check if this is an edit operation (has pk in URL)
        if self.kwargs.get('pk') and request.user.is_authenticated:
            # Check if user is a farm worker
            if hasattr(request.user, 'role') and request.user.role:
                if request.user.role.name == 'farm_worker':
                    messages.error(
                        request,
                        "Farm workers cannot edit existing records. You can only add new data."
                    )
                    # Redirect back to list view
                    return redirect(request.META.get('HTTP_REFERER', '/'))
        
        return super().dispatch(request, *args, **kwargs)


class DisableFormFieldsForWorkerMixin:
    """
    Mixin to disable all form fields for farm workers when editing.
    This provides an additional layer of protection in forms.
    """
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Check if editing (object exists) and user is farm worker
        if self.object and self.object.pk:
            if (hasattr(self.request.user, 'role') and 
                self.request.user.role and 
                self.request.user.role.name == 'farm_worker'):
                # Disable all fields
                for field in form.fields:
                    form.fields[field].disabled = True
                    form.fields[field].widget.attrs['readonly'] = True
        
        return form
