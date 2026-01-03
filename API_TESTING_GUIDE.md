# API Testing Guide

## Quick Test Scenarios

### Scenario 1: Manager Creates a Challenge

#### Step 1: Create a Challenge
```bash
POST /api/challenges/
Authorization: Bearer {MANAGER_TOKEN}
Content-Type: application/json

{
  "title": "Two Sum",
  "slug": "two-sum",
  "statement": "Given an array of integers nums and an integer target, return the indices of the two numbers that add up to target.",
  "input_format": "First line: N (size of array)\nSecond line: N space-separated integers\nThird line: target",
  "output_format": "Two space-separated integers representing indices",
  "constraints": "1 ≤ N ≤ 10^4\n-10^9 ≤ nums[i] ≤ 10^9",
  "difficulty": "E",
  "tag_ids": [1, 2]
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "title": "Two Sum",
  "slug": "two-sum",
  "statement": "Given an array of integers nums...",
  "input_format": "First line: N (size of array)...",
  "output_format": "Two space-separated integers...",
  "constraints": "1 ≤ N ≤ 10^4...",
  "difficulty": "E",
  "tags": [{"id": 1, "name": "array"}, {"id": 2, "name": "hashing"}],
  "tag_ids": [1, 2],
  "test_cases": [],
  "sample_test_cases": [],
  "created_by": "manager_user",
  "is_public": false,
  "created_at": "2026-01-02T16:00:00Z",
  "updated_at": "2026-01-02T16:00:00Z"
}
```

#### Step 2: Add a Sample Test Case
```bash
POST /api/challenges/1/test-cases/
Authorization: Bearer {MANAGER_TOKEN}
Content-Type: application/json

{
  "input_data": "2\n2 7\n9",
  "expected_output": "0 1",
  "is_sample": true,
  "is_hidden": false
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "input_data": "2\n2 7\n9",
  "expected_output": "0 1",
  "is_sample": true,
  "is_hidden": false
}
```

#### Step 3: Add a Hidden Test Case
```bash
POST /api/challenges/1/test-cases/
Authorization: Bearer {MANAGER_TOKEN}
Content-Type: application/json

{
  "input_data": "3\n1 2 3\n5",
  "expected_output": "1 2",
  "is_sample": false,
  "is_hidden": true
}
```

#### Step 4: View Challenge with Test Cases
```bash
GET /api/challenges/1/
Authorization: Bearer {MANAGER_TOKEN}
```

**Response:**
```json
{
  "id": 1,
  "title": "Two Sum",
  "slug": "two-sum",
  "statement": "Given an array of integers nums...",
  "input_format": "First line: N (size of array)...",
  "output_format": "Two space-separated integers...",
  "constraints": "1 ≤ N ≤ 10^4...",
  "difficulty": "E",
  "tags": [{"id": 1, "name": "array"}, {"id": 2, "name": "hashing"}],
  "tag_ids": [1, 2],
  "test_cases": [
    {
      "id": 1,
      "input_data": "2\n2 7\n9",
      "expected_output": "0 1",
      "is_sample": true,
      "is_hidden": false
    },
    {
      "id": 2,
      "input_data": "3\n1 2 3\n5",
      "expected_output": "1 2",
      "is_sample": false,
      "is_hidden": true
    }
  ],
  "sample_test_cases": [
    {
      "input_data": "2\n2 7\n9",
      "expected_output": "0 1"
    }
  ],
  "created_by": "manager_user",
  "is_public": false,
  "created_at": "2026-01-02T16:00:00Z",
  "updated_at": "2026-01-02T16:00:00Z"
}
```

#### Step 5: List My Challenges
```bash
GET /api/challenges/me/
Authorization: Bearer {MANAGER_TOKEN}
```

**Response:**
```json
[
  {
    "id": 1,
    "title": "Two Sum",
    "slug": "two-sum",
    "difficulty": "E",
    "tags": [{"id": 1, "name": "array"}, {"id": 2, "name": "hashing"}],
    "created_by": "manager_user",
    "is_public": false,
    "created_at": "2026-01-02T16:00:00Z"
  }
]
```

#### Step 6: Publish Challenge to Practice
```bash
POST /api/challenges/1/publish/
Authorization: Bearer {MANAGER_TOKEN}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Two Sum",
  "slug": "two-sum",
  "statement": "Given an array of integers nums...",
  "input_format": "First line: N (size of array)...",
  "output_format": "Two space-separated integers...",
  "constraints": "1 ≤ N ≤ 10^4...",
  "difficulty": "E",
  "tags": [{"id": 1, "name": "array"}, {"id": 2, "name": "hashing"}],
  "tag_ids": [1, 2],
  "test_cases": [...],
  "sample_test_cases": [...],
  "created_by": "manager_user",
  "is_public": true,
  "created_at": "2026-01-02T16:00:00Z",
  "updated_at": "2026-01-02T16:00:00Z"
}
```

---

### Scenario 2: Superuser Creates Practice Problem

#### Step 1: Create Practice Problem
```bash
POST /api/practice/problems/
Authorization: Bearer {SUPERUSER_TOKEN}
Content-Type: application/json

{
  "title": "Fibonacci Sequence",
  "slug": "fibonacci",
  "statement": "Find the Nth Fibonacci number.",
  "input_format": "Single integer N",
  "output_format": "The Nth Fibonacci number",
  "constraints": "0 ≤ N ≤ 100",
  "difficulty": "E",
  "tag_ids": [3],
  "is_published": true
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "title": "Fibonacci Sequence",
  "slug": "fibonacci",
  "statement": "Find the Nth Fibonacci number.",
  "input_format": "Single integer N",
  "output_format": "The Nth Fibonacci number",
  "constraints": "0 ≤ N ≤ 100",
  "difficulty": "E",
  "tags": [{"id": 3, "name": "dynamic-programming"}],
  "tag_ids": [3],
  "test_cases": [],
  "sample_test_cases": [],
  "created_by": "superuser",
  "is_published": true,
  "created_at": "2026-01-02T16:05:00Z",
  "updated_at": "2026-01-02T16:05:00Z"
}
```

#### Step 2: Add Test Case
```bash
POST /api/practice/problems/1/test-cases/
Authorization: Bearer {SUPERUSER_TOKEN}
Content-Type: application/json

{
  "input_data": "5",
  "expected_output": "5",
  "is_sample": true
}
```

---

### Scenario 3: User Views Public Practice Problems

#### Step 1: List All Published Practice Problems
```bash
GET /api/practice/problems/
```

**Response (200 OK, No Auth Required):**
```json
[
  {
    "id": 1,
    "title": "Fibonacci Sequence",
    "slug": "fibonacci",
    "difficulty": "E",
    "tags": [{"id": 3, "name": "dynamic-programming"}],
    "created_by": "superuser",
    "created_at": "2026-01-02T16:05:00Z"
  }
]
```

#### Step 2: View Problem Details
```bash
GET /api/practice/problems/fibonacci/
```

**Response (200 OK, No Auth Required):**
```json
{
  "id": 1,
  "title": "Fibonacci Sequence",
  "slug": "fibonacci",
  "statement": "Find the Nth Fibonacci number.",
  "input_format": "Single integer N",
  "output_format": "The Nth Fibonacci number",
  "constraints": "0 ≤ N ≤ 100",
  "difficulty": "E",
  "tags": [{"id": 3, "name": "dynamic-programming"}],
  "tag_ids": [3],
  "test_cases": [...],
  "sample_test_cases": [
    {
      "input_data": "5",
      "expected_output": "5"
    }
  ],
  "created_by": "superuser",
  "is_published": true,
  "created_at": "2026-01-02T16:05:00Z",
  "updated_at": "2026-01-02T16:05:00Z"
}
```

---

### Scenario 4: Permission Tests

#### Test 1: Non-Manager Cannot Create Challenge
```bash
POST /api/challenges/
Authorization: Bearer {USER_TOKEN}
```

**Response (403 Forbidden):**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### Test 2: Non-Owner Cannot Edit Challenge
```bash
PUT /api/challenges/1/
Authorization: Bearer {OTHER_MANAGER_TOKEN}

{
  "title": "Updated Title"
}
```

**Response (403 Forbidden):**
```json
{
  "error": "You can only edit your own challenges"
}
```

#### Test 3: Non-Superuser Cannot Create Practice Problem
```bash
POST /api/practice/problems/
Authorization: Bearer {MANAGER_TOKEN}
```

**Response (403 Forbidden):**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### Test 4: User Can View Public Problem Without Auth
```bash
GET /api/practice/problems/fibonacci/
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Fibonacci Sequence",
  ...
}
```

---

## cURL Examples

### Create Challenge
```bash
curl -X POST http://localhost:8000/api/challenges/ \
  -H "Authorization: Bearer YOUR_MANAGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Two Sum",
    "slug": "two-sum",
    "statement": "Find two numbers that add up to target",
    "input_format": "N and target on first line, then N integers",
    "output_format": "Indices of the two numbers",
    "constraints": "1 ≤ N ≤ 10^4",
    "difficulty": "E",
    "tag_ids": [1]
  }'
```

### List My Challenges
```bash
curl -X GET http://localhost:8000/api/challenges/me/ \
  -H "Authorization: Bearer YOUR_MANAGER_TOKEN"
```

### Get Challenge Details
```bash
curl -X GET http://localhost:8000/api/challenges/1/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### List Public Practice Problems
```bash
curl -X GET http://localhost:8000/api/practice/problems/
```

### Get Practice Problem by Slug
```bash
curl -X GET http://localhost:8000/api/practice/problems/fibonacci/
```

---

## Error Responses

### 400 Bad Request (Invalid Data)
```json
{
  "title": ["This field is required."],
  "difficulty": ["Invalid choice. Expected 'E', 'M', or 'H'."]
}
```

### 403 Forbidden (Permission Denied)
```json
{
  "error": "You can only edit your own challenges"
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

---

## Setup for Testing

### Create Test Users
```bash
python manage.py createsuperuser
# Create superuser account for practice problems

python manage.py shell
>>> from accounts.models import User
>>> user = User.objects.create_user(username='manager', email='manager@test.com', password='test123')
>>> user.is_staff = True
>>> user.save()
```

### Get Token
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "manager", "password": "test123"}'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

Use the `access` token in Authorization headers:
```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

