import subprocess
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Problem, Submission, TestCase, Contest
# Add TestCaseSerializer to your imports
from .serializers import ProblemSerializer, SubmissionSerializer, ContestSerializer, TestCaseSerializer

# --------------------------
# List all problems
# --------------------------
class ProblemListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        problems = Problem.objects.all().order_by('id')
        serializer = ProblemSerializer(problems, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# --------------------------
# Get specific problem details
# --------------------------
class ProblemDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            problem = Problem.objects.get(pk=pk)
            serializer = ProblemSerializer(problem)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Problem.DoesNotExist:
            return Response({'error': 'Problem not found'}, status=status.HTTP_404_NOT_FOUND)

# --------------------------
# Submit code and get result
# --------------------------
class SubmissionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        problem_id = request.data.get('problem_id')
        source_code = request.data.get('source_code')
        language = request.data.get('language')

        if not problem_id or not source_code or not language:
            return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            problem = Problem.objects.get(pk=problem_id)
        except Problem.DoesNotExist:
            return Response({'error': 'Problem not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Create the submission record
        submission = Submission.objects.create(
            user=request.user,
            problem=problem,
            language=language,
            source_code=source_code,
            status='Pending'
        )

        # Judging Engine Execution
        final_status = self.run_judge(submission)
        submission.status = final_status
        submission.save()

        # Update Statistics if Accepted
        if final_status == 'Accepted':
            stats = getattr(request.user, 'statistics', None)
            if stats:
                stats.total_solved += 1
                stats.save()

        return Response(SubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)

    def run_judge(self, submission):
        test_cases = TestCase.objects.filter(problem=submission.problem)
        if not test_cases.exists():
            return 'Accepted'

        for test in test_cases:
            try:
                # Local Execution logic
                process = subprocess.run(
                    ['python', '-c', submission.source_code],
                    input=test.input_data,
                    capture_output=True,
                    text=True,
                    timeout=2
                )

                if process.returncode != 0:
                    return 'Runtime Error'
                
                if process.stdout.strip() != test.expected_output.strip():
                    return 'Wrong Answer'
            except subprocess.TimeoutExpired:
                return 'Time Limit Exceeded'
            except Exception:
                return 'Runtime Error'
        
        return 'Accepted'

# --------------------------
# Get User Submissions
# --------------------------
class UserSubmissionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        submissions = Submission.objects.filter(user=request.user).order_by('-submitted_at')
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# --------------------------
# List all Contests
# --------------------------
class ContestListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        contests = Contest.objects.all().order_by('-start_time')
        serializer = ContestSerializer(contests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
# --------------------------
# Admin: Create a Problem
# --------------------------
class AdminProblemCreateView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        serializer = ProblemSerializer(data=request.data)
        if serializer.is_valid():
            problem = serializer.save()
            return Response(ProblemSerializer(problem).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --------------------------
# Admin: Add a Test Case
# --------------------------
class AdminTestCaseCreateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = TestCaseSerializer(data=request.data)
        if serializer.is_valid():
            test_case = serializer.save()
            return Response(TestCaseSerializer(test_case).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)