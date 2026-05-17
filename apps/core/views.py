from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from apps.core.utils.mixins import BaseResponseMixin
from .models import Document, FAQ
from .serializers import DocumentSerializer, FAQSerializer

class DocumentDetailView(BaseResponseMixin, APIView):
    """
    GET /api/core/documents/<slug>/ → Retrieve Terms/Privacy/Refund policy documents
    """
    permission_classes = [AllowAny]

    def get(self, request, slug, *args, **kwargs):
        try:
            document = Document.objects.get(slug=slug, is_active=True)
            serializer = DocumentSerializer(document)
            return self.success_response(
                data=serializer.data,
                message=f"Document '{document.title}' retrieved successfully."
            )
        except Document.DoesNotExist:
            return self.error_response(
                message="Document not found.",
                error_code="DOCUMENT_NOT_FOUND",
                status_code=404
            )


class FAQListView(BaseResponseMixin, APIView):
    """
    GET /api/core/faqs/ → Retrieve all FAQs grouped by category
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        faqs = FAQ.objects.filter(is_active=True)
        serializer = FAQSerializer(faqs, many=True)
        
        # Group by category
        grouped_faqs = {}
        for faq_data in serializer.data:
            category = faq_data["category"]
            category_display = faq_data["category_display"]
            
            if category not in grouped_faqs:
                grouped_faqs[category] = {
                    "category": category,
                    "category_display": category_display,
                    "items": []
                }
            grouped_faqs[category]["items"].append({
                "id": faq_data["id"],
                "question": faq_data["question"],
                "answer": faq_data["answer"],
                "sort_order": faq_data["sort_order"]
            })
            
        return self.success_response(
            data=list(grouped_faqs.values()),
            message="Frequently Asked Questions (FAQs) retrieved successfully."
        )


# ─────────────────────────── ADMIN CRUD SUPPORT VIEWS ───────────────────────────
from rest_framework.permissions import IsAdminUser

class AdminDocumentListCreateView(BaseResponseMixin, APIView):
    """
    Admin CRUD: GET all documents, POST new document
    """
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        documents = Document.objects.all()
        serializer = DocumentSerializer(documents, many=True)
        return self.success_response(
            data=serializer.data,
            message="All documents retrieved successfully (Admin view)."
        )

    def post(self, request, *args, **kwargs):
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success_response(
                data=serializer.data,
                message="Document created successfully.",
                status_code=201
            )
        return self.error_response(
            message="Failed to create document.",
            error_code="VALIDATION_ERROR",
            errors=serializer.errors
        )


class AdminDocumentDetailView(BaseResponseMixin, APIView):
    """
    Admin CRUD: PUT update document, DELETE document
    """
    permission_classes = [IsAdminUser]

    def put(self, request, slug, *args, **kwargs):
        try:
            document = Document.objects.get(slug=slug)
        except Document.DoesNotExist:
            return self.error_response(
                message="Document not found.",
                error_code="DOCUMENT_NOT_FOUND",
                status_code=404
            )
        
        serializer = DocumentSerializer(document, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return self.success_response(
                data=serializer.data,
                message="Document updated successfully."
            )
        return self.error_response(
            message="Failed to update document.",
            error_code="VALIDATION_ERROR",
            errors=serializer.errors
        )

    def delete(self, request, slug, *args, **kwargs):
        try:
            document = Document.objects.get(slug=slug)
            document.delete()
            return self.success_response(
                message="Document deleted successfully."
            )
        except Document.DoesNotExist:
            return self.error_response(
                message="Document not found.",
                error_code="DOCUMENT_NOT_FOUND",
                status_code=404
            )


class AdminFAQListCreateView(BaseResponseMixin, APIView):
    """
    Admin CRUD: GET all FAQs, POST new FAQ
    """
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        faqs = FAQ.objects.all()
        serializer = FAQSerializer(faqs, many=True)
        return self.success_response(
            data=serializer.data,
            message="All FAQs retrieved successfully (Admin view)."
        )

    def post(self, request, *args, **kwargs):
        serializer = FAQSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success_response(
                data=serializer.data,
                message="FAQ created successfully.",
                status_code=201
            )
        return self.error_response(
            message="Failed to create FAQ.",
            error_code="VALIDATION_ERROR",
            errors=serializer.errors
        )


class AdminFAQDetailView(BaseResponseMixin, APIView):
    """
    Admin CRUD: PUT update FAQ, DELETE FAQ
    """
    permission_classes = [IsAdminUser]

    def put(self, request, pk, *args, **kwargs):
        try:
            faq = FAQ.objects.get(pk=pk)
        except FAQ.DoesNotExist:
            return self.error_response(
                message="FAQ not found.",
                error_code="FAQ_NOT_FOUND",
                status_code=404
            )
        
        serializer = FAQSerializer(faq, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return self.success_response(
                data=serializer.data,
                message="FAQ updated successfully."
            )
        return self.error_response(
            message="Failed to update FAQ.",
            error_code="VALIDATION_ERROR",
            errors=serializer.errors
        )

    def delete(self, request, pk, *args, **kwargs):
        try:
            faq = FAQ.objects.get(pk=pk)
            faq.delete()
            return self.success_response(
                message="FAQ deleted successfully."
            )
        except FAQ.DoesNotExist:
            return self.error_response(
                message="FAQ not found.",
                error_code="FAQ_NOT_FOUND",
                status_code=404
            )
