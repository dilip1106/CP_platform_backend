from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Problem
from .serializers import (
    ProblemListSerializer,
    ProblemDetailSerializer
)


# -------------------------
# List all problems
# -------------------------
class ProblemListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        problems = Problem.objects.filter(is_published=True)
        serializer = ProblemListSerializer(problems, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# -------------------------
# Get single problem
# -------------------------
class ProblemDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        try:
            problem = Problem.objects.get(slug=slug, is_published=True)
        except Problem.DoesNotExist:
            return Response(
                {'error': 'Problem not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProblemDetailSerializer(problem)
        return Response(serializer.data, status=status.HTTP_200_OK)
