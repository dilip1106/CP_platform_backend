from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Submission
from .serializers import SubmissionCreateSerializer, SubmissionSerializer


class SubmissionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubmissionCreateSerializer(data=request.data)
        if serializer.is_valid():
            submission = serializer.save(user=request.user)
            return Response(
                SubmissionSerializer(submission).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSubmissionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        submissions = Submission.objects.filter(user=request.user).order_by('-created_at')
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data)
    


# submissions/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Submission, SubmissionResult
from .serializers import SubmissionCreateSerializer, SubmissionSerializer
from .languages import LANGUAGE_CONFIG
import requests
import time

# Judge0 free API endpoint
JUDGE0_URL = "https://ce.judge0.com/submissions?base64_encoded=false&wait=true"

# Status mapping from Judge0 to our model
STATUS_MAP = {
    "Accepted": "AC",
    "Wrong Answer": "WA",
    "Time Limit Exceeded": "TLE",
    "Memory Limit Exceeded": "MLE",
    "Runtime Error (NZEC)": "RE",
    "Compilation Error": "CE",
    "Internal Error": "ERROR"
}

JUDGE0_STATUS_MAP = {
    1: "IN_QUEUE",
    2: "PROCESSING",
    3: "AC",    # Accepted
    4: "WA",    # Wrong Answer
    5: "TLE",   # Time Limit Exceeded
    6: "CE",    # Compilation Error
    7: "RE",    # Runtime Error (SIGSEGV, NZEC)
    8: "RE",    # Runtime Error
    9: "TLE",   # Time Limit Exceeded
    10: "RE",   # Runtime Error
    11: "CE",   # Compilation Error
    12: "RE",   # Runtime Error
    13: "MLE",  # Memory Limit Exceeded
    14: "RE",   # Runtime Error
}

class SubmitSolutionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SubmissionCreateSerializer(data=request.data)
        if serializer.is_valid():
            submission = serializer.save(user=request.user, status='PENDING')

            language_id = LANGUAGE_CONFIG.get(submission.language)
            if not language_id:
                return Response({"error": "Unsupported language"}, status=status.HTTP_400_BAD_REQUEST)

            test_cases = submission.problem.test_cases.all()
            all_passed = True

            for tc in test_cases:
                body = {
                    "source_code": submission.source_code,
                    "language_id": language_id,
                    "stdin": tc.input_data or "",
                    "expected_output": tc.expected_output or "",
                    "cpu_time_limit": submission.problem.time_limit / 1000,  # ms → s
                    "memory_limit": submission.problem.memory_limit * 1024  # MB → KB
                }
                try:
                    response = requests.post(JUDGE0_URL, json=body)
                    result = response.json()

                    # Determine status
                    judge_status = result.get('status', {}).get('description', 'Internal Error')
                    # status_code = STATUS_MAP.get(judge_status, 'ERROR')
                    status_code = result["status"]["id"]
                    mapped_status = JUDGE0_STATUS_MAP.get(status_code, "ERROR")

                    if mapped_status != 'AC':
                        all_passed = False

                    # Save individual test case result
                    SubmissionResult.objects.create(
                        submission=submission,
                        test_case=tc,
                        status=mapped_status,
                        stdout=result.get('stdout'),
                        stderr=result.get('stderr'),
                        execution_time_ms=int(float(result.get('time', 0)) * 1000),
                        memory_usage_kb=int(result.get('memory', 0))
                    )

                except Exception as e:
                    all_passed = False
                    SubmissionResult.objects.create(
                        submission=submission,
                        test_case=tc,
                        status='ERROR',
                        stderr=str(e)
                    )

            # Update submission status
            submission.status = 'AC' if all_passed else 'WA'
            submission.save()

            return Response(SubmissionSerializer(submission).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
