"""
Views for the resume API.
"""
import os
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .authentication import APIKeyAuthentication
from .throttling import TenantRateThrottle
from .models import Resume
from .tasks import parse_resume
from .serializers import (
    ResumeSubmitSerializer,
    ResumeListSerializer,
    ResumeDetailsSerializer,
)


from drf_spectacular.utils import extend_schema


@extend_schema(tags=["Resumes"])
class ResumeListCreateView(generics.ListCreateAPIView):
    """Submit a resume or list all resumes."""

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [TenantRateThrottle]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ResumeSubmitSerializer
        return ResumeListSerializer

    def get_queryset(self):
        """Return only resumes belonging to the authenticated tenant."""

        queryset = Resume.objects.filter(tenant=self.request.user).order_by(
            "-created_at"
        )
        status_filter = self.request.query_params.get("status")
        source_filter = self.request.query_params.get("source_type")

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if source_filter:
            queryset = queryset.filter(source_type=source_filter)

        return queryset

    def perform_create(self, serializer):
        """Save a resume and increment rte limit counter."""
        resume = serializer.save(tenant=self.request.user)

        self.request.auth
        throttle = TenantRateThrottle()
        throttle.increment(self.request.user)

        parse_resume.delay(str(resume.id))
        self.resume = resume

    def create(self, request, *args, **kwargs):
        """Ovverride to return 202 with resume id."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {
                "resume_id": str(self.resume.id),
                "status": "pending",
                "message": "Resume submitted. Poll /v1/resumes/{id}/ for results.",
            },
            status=status.HTTP_202_ACCEPTED,
        )


@extend_schema(tags=["Resumes"])
class ResumeDetailView(generics.RetrieveDestroyAPIView):
    """Retrieve or delte a specific resume."""

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ResumeDetailsSerializer

    def get_queryset(self):
        """Ensure tenants can only access their own resumes."""
        return Resume.objects.filter(tenant=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Allow tenants to delete their resumes."""
        instance = self.get_object()

        if instance.file:
            if os.path.isfile(instance.file.path):
                os.remove(instance.file.path)

        instance.delete()

        return Response(
            {"message": "Resume deleted successfully."},
            status=status.HTTP_200_OK,
        )
