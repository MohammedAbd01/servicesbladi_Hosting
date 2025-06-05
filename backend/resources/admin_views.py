from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Resource, ResourceFile
from django.utils.translation import gettext_lazy as _

@login_required
def admin_edit_resource(request, resource_id):
    """Edit a resource (admin only)"""
    # Get resource
    resource = get_object_or_404(Resource, id=resource_id)
    
    # Check if user is admin
    if request.user.account_type.lower() != 'admin':
        messages.error(request, _('Vous n\'avez pas les permissions nécessaires.'))
        return redirect('admin_ressources')
    
    if request.method == 'POST':
        try:
            # Update resource data
            resource.title = request.POST.get('title', resource.title)
            resource.description = request.POST.get('description', resource.description)
            resource.category = request.POST.get('category', resource.category)
            resource.is_active = 'is_active' in request.POST
            resource.save()
            
            # Handle file uploads
            files = request.FILES.getlist('files')
            for file in files:
                ResourceFile.objects.create(
                    resource=resource,
                    file=file,
                    file_name=file.name,
                    file_size=file.size,
                    uploaded_by=request.user
                )
            
            messages.success(request, _('La ressource a été mise à jour avec succès.'))
            return redirect('admin_ressources')
            
        except Exception as e:
            messages.error(request, _(f'Erreur lors de la mise à jour de la ressource: {str(e)}'))
    
    # Prepare data for form
    context = {
        'resource': resource,
        'files': resource.files.all(),
    }
    
    return render(request, 'admin/ressources.html', context) 