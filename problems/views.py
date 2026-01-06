from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404

from .models import Problem
from .serializers import (
    ProblemListSerializer,
    ProblemDetailSerializer
)


# ============================================================
# Problem Views
# ============================================================

class ProblemListView(APIView):
    """
    List all published problems.
    
    Accessible to: All users (no auth required)
    Returns: Problem list with basic info (no test cases)
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        problems = Problem.objects.filter(
            state='PUBLISHED'
        ).order_by('-created_at')
        
        serializer = ProblemListSerializer(problems, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProblemDetailView(APIView):
    """
    Get single problem with all details.
    
    Accessible to: All users (no auth required)
    Returns: Problem detail with sample test cases (hidden tests excluded)
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        problem = get_object_or_404(
            Problem,
            slug=slug,
            state='PUBLISHED'
        )
        
        serializer = ProblemDetailSerializer(
            problem,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
