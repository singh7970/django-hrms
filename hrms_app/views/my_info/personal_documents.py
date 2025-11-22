from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from hrms_app.models.my_info.documents import PersonalDocument
from hrms_app.models import UserProfile  # only if needed for additional profile info

@login_required
def personal_documents_view(request):
    user = request.user

    # Fetch all documents for user
    documents = PersonalDocument.objects.filter(user=user)
    
    # Separate profile photo document
    profile_photo_doc = documents.filter(document_type='profile_photo').first()
    documents = documents.exclude(document_type='profile_photo')

    if request.method == 'POST':
        document_type = request.POST.get('document_type')
        document_file = request.FILES.get('document_file')

        # Basic validation
        if not document_type or not document_file:
            messages.error(request, "Both document type and document file are required.")
            return redirect('personal_documents')

        # Handle profile photo separately (store in User model)
        if document_type == 'profile_photo':
            # Delete previous profile photo (if any)
            if user.profile_photo:
                user.profile_photo.delete(save=False)

            # Save new profile photo
            user.profile_photo = document_file
            user.save()

            messages.success(request, "Profile photo uploaded successfully.")
            return redirect('personal_documents')

        # Prevent duplicate document type for user (except profile photo)
        if PersonalDocument.objects.filter(user=user, document_type=document_type).exists():
            messages.warning(request, f"A document of type '{document_type}' already exists.")
            return redirect('personal_documents')

        # Save new document
        PersonalDocument.objects.create(
            user=user,
            document_type=document_type,
            document_file=document_file
        )

        messages.success(request, "Document uploaded successfully.")
        return redirect('personal_documents')

    return render(request, 'my_info/personal_documents.html', {
        'profile_photo_doc': profile_photo_doc,
        'documents': documents,
    })


@login_required
def delete_personal_document(request, doc_id):
    if request.method == "POST":
        document = get_object_or_404(PersonalDocument, id=doc_id, user=request.user)

        # Delete actual file
        document.document_file.delete(save=False)

        # Delete DB record
        document.delete()

        messages.success(request, "Document deleted successfully.")

    return redirect('personal_documents')
