# Complete CP Platform API Reference

## Base URL
```
http://localhost:8000/api
```

---

## AUTHENTICATION ENDPOINTS

### 1. Register User
**Endpoint:** `POST /accounts/register/`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securePassword123",
  "password_confirm": "securePassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Success Response (201):**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Error Response (400):**
```json
{
  "username": ["This field may not be blank."],
  "email": ["Enter a valid email address."],
  "password": ["Passwords do not match."]
}
```

---

### 2. Login
**Endpoint:** `POST /auth/login/`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "securePassword123"
}
```

**Success Response (200):**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Response (401):**
```json
{
  "error": "Invalid username or password."
}
```

---

### 3. Refresh Token
**Endpoint:** `POST /auth/refresh/`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "refresh": "your_refresh_token"
}
```

**Success Response (200):**
```json
{
  "access": "new_access_token"
}
```

---

### 4. Logout
**Endpoint:** `POST /accounts/logout/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "refresh": "your_refresh_token"
}
```

**Success Response (200):**
```json
{
  "message": "Logout successful"
}
```

---

## ACCOUNTS ENDPOINTS

### 5. Get User Profile
**Endpoint:** `GET /accounts/profile/<int:id>/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_staff": false,
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Error Response (404):**
```json
{
  "detail": "Not found."
}
```

---

## PROBLEMS ENDPOINTS

### 6. List All Problems
**Endpoint:** `GET /problems/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Query Parameters (Optional):**
```
?search=array&difficulty=medium
```

**Success Response (200):**
```json
[
  {
    "id": 1,
    "title": "Two Sum",
    "slug": "two-sum",
    "statement": "Find two numbers that add up to target",
    "difficulty": "E",
    "time_limit": 1000,
    "memory_limit": 256,
    "tags": ["array", "hash-table"]
  }
]
```

---

### 7. Get Problem Details
**Endpoint:** `GET /problems/<slug:slug>/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
{
  "id": 1,
  "title": "Two Sum",
  "slug": "two-sum",
  "statement": "Given an array of integers nums and an integer target, return the indices of the two numbers that add up to target.",
  "constraints": "1 <= nums.length <= 10^4",
  "input_format": "First line: n, Second line: array",
  "output_format": "Array of two indices",
  "difficulty": "E",
  "time_limit": 1000,
  "memory_limit": 256,
  "tags": ["array", "hash-table"],
  "sample_test_cases": [
    {
      "id": 1,
      "input": "2 7 11 15\n9",
      "output": "0 1",
      "is_sample": true
    }
  ]
}
```

---

## SUBMISSIONS ENDPOINTS

### 8. Create Submission (Non-Contest)
**Endpoint:** `POST /submissions/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "problem_id": 1,
  "language": "PY",
  "source_code": "def solution():\n    return [0, 1]"
}
```

**Success Response (201):**
```json
{
  "id": 1,
  "user_id": 1,
  "problem_id": 1,
  "language": "PY",
  "status": "PENDING",
  "created_at": "2025-01-15T11:00:00Z"
}
```

---

### 9. Get User Submissions
**Endpoint:** `GET /submissions/me/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "problem_id": 1,
    "problem_title": "Two Sum",
    "language": "PY",
    "status": "AC",
    "execution_time_ms": 45,
    "memory_usage_kb": 128,
    "created_at": "2025-01-15T11:00:00Z"
  }
]
```

---

### 10. Get Submission Details
**Endpoint:** `GET /submissions/<int:submission_id>/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
{
  "id": 1,
  "user_id": 1,
  "problem_id": 1,
  "language": "PY",
  "source_code": "def solution():\n    return [0, 1]",
  "status": "AC",
  "execution_time_ms": 45,
  "memory_usage_kb": 128,
  "created_at": "2025-01-15T11:00:00Z"
}
```

---

## CONTEST ENDPOINTS

### 11. List All Contests
**Endpoint:** `GET /contest/contests/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
[
  {
    "id": 1,
    "title": "Python Challenge",
    "slug": "python-challenge",
    "description": "Master Python programming",
    "start_time": "2025-02-01T10:00:00Z",
    "end_time": "2025-02-02T10:00:00Z",
    "is_public": true,
    "total_problems": 5
  }
]
```

---

### 12. List Contests with Status
**Endpoint:** `GET /contest/contests/with-status/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
[
  {
    "id": 1,
    "title": "Python Challenge",
    "slug": "python-challenge",
    "description": "Master Python programming",
    "start_time": "2025-02-01T10:00:00Z",
    "end_time": "2025-02-02T10:00:00Z",
    "status": "UPCOMING",
    "is_public": true,
    "total_problems": 5,
    "total_participants": 150
  }
]
```

---

### 13. Search Contests
**Endpoint:** `GET /contest/contests/search/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Query Parameters:**
```
?query=python
```

**Success Response (200):**
```json
[
  {
    "id": 1,
    "title": "Python Challenge",
    "slug": "python-challenge",
    "description": "Master Python programming",
    "start_time": "2025-02-01T10:00:00Z",
    "end_time": "2025-02-02T10:00:00Z"
  }
]
```

---

### 14. Get My Registered Contests
**Endpoint:** `GET /contest/contests/my-registrations/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
{
  "total_registrations": 2,
  "contests": [
    {
      "contest_id": 1,
      "title": "Python Challenge",
      "slug": "python-challenge",
      "description": "Master Python programming",
      "start_time": "2025-02-01T10:00:00Z",
      "end_time": "2025-02-02T10:00:00Z",
      "status": "UPCOMING",
      "registered_at": "2025-01-15T10:00:00Z",
      "registration_status": "REGISTERED"
    }
  ]
}
```

---

### 15. Create Contest (Admin Only)
**Endpoint:** `POST /contest/contests/create/`

**Headers:**
```json
{
  "Authorization": "Bearer admin_access_token",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "title": "New Contest",
  "slug": "new-contest",
  "description": "Contest description",
  "start_time": "2025-02-01T10:00:00Z",
  "end_time": "2025-02-02T10:00:00Z",
  "is_public": true,
  "logo": "https://example.com/logo.png",
  "rules": "Contest rules here"
}
```

**Success Response (201):**
```json
{
  "id": 1,
  "title": "New Contest",
  "slug": "new-contest",
  "description": "Contest description",
  "start_time": "2025-02-01T10:00:00Z",
  "end_time": "2025-02-02T10:00:00Z",
  "is_public": true,
  "state": "DRAFT",
  "is_published": false,
  "created_by": {
    "id": 1,
    "username": "admin"
  },
  "created_at": "2025-01-15T12:00:00Z"
}
```

**Error Response (400):**
```json
{
  "start_time": ["Start time must be before end time"]
}
```

---

### 16. Get Contest Details
**Endpoint:** `GET /contest/contests/<slug:slug>/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
{
  "id": 1,
  "title": "Python Challenge",
  "slug": "python-challenge",
  "description": "Master Python programming",
  "rules": "Contest rules",
  "logo": "https://example.com/logo.png",
  "start_time": "2025-02-01T10:00:00Z",
  "end_time": "2025-02-02T10:00:00Z",
  "state": "SCHEDULED",
  "is_published": true,
  "created_by": {
    "id": 1,
    "username": "admin"
  },
  "managers": [
    {
      "id": 2,
      "username": "manager1"
    }
  ],
  "problems": [
    {
      "id": 1,
      "problem_id": 1,
      "title": "Two Sum",
      "slug": "two-sum",
      "order": 1
    }
  ],
  "current_state": "UPCOMING",
  "can_edit": false,
  "can_add_problems": false,
  "time_status": {
    "status": "UPCOMING",
    "seconds_until_start": 2592000
  }
}
```

**Error Response (404):**
```json
{
  "error": "Contest not found"
}
```

---

### 17. Get Contest with Registration Status
**Endpoint:** `GET /contest/contests/<slug:slug>/with-registration/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
{
  "id": 1,
  "title": "Python Challenge",
  "slug": "python-challenge",
  "description": "Master Python programming",
  "start_time": "2025-02-01T10:00:00Z",
  "end_time": "2025-02-02T10:00:00Z",
  "is_registered": true,
  "registration_status": "REGISTERED",
  "registered_at": "2025-01-15T10:00:00Z"
}
```

---

### 18. Get Contest Status
**Endpoint:** `GET /contest/contests/<slug:slug>/status/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
{
  "contest_id": 1,
  "title": "Python Challenge",
  "status": "UPCOMING",
  "start_time": "2025-02-01T10:00:00Z",
  "end_time": "2025-02-02T10:00:00Z",
  "time_delta_seconds": 2592000,
  "is_joined": false
}
```

---

### 19. Update Contest (Manager Only)
**Endpoint:** `PUT /contest/contests/<int:contest_id>/update/`

**Headers:**
```json
{
  "Authorization": "Bearer manager_access_token",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "title": "Updated Contest Title",
  "description": "Updated description",
  "rules": "Updated rules"
}
```

**Success Response (200):**
```json
{
  "id": 1,
  "title": "Updated Contest Title",
  "description": "Updated description",
  "rules": "Updated rules",
  "state": "DRAFT"
}
```

**Error Response (403):**
```json
{
  "error": "You don't have permission to edit this contest"
}
```

---

### 20. Publish Contest (Manager Only)
**Endpoint:** `POST /contest/contests/<int:contest_id>/publish/`

**Headers:**
```json
{
  "Authorization": "Bearer manager_access_token",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{}
```

**Success Response (200):**
```json
{
  "message": "Contest published successfully",
  "state": "SCHEDULED",
  "is_published": true
}
```

**Error Response (400):**
```json
{
  "error": "Contest must have at least one problem"
}
```

---

### 21. Register for Contest
**Endpoint:** `POST /contest/contests/<int:contest_id>/register/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{}
```

**Success Response (201):**
```json
{
  "message": "Successfully registered",
  "registered_at": "2025-01-15T10:00:00Z"
}
```

**Error Response (400):**
```json
{
  "error": "Already registered"
}
```

---

### 22. Unregister from Contest
**Endpoint:** `POST /contest/contests/<int:contest_id>/unregister/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{}
```

**Success Response (200):**
```json
{
  "message": "Successfully unregistered"
}
```

---

### 23. Check Registration Status
**Endpoint:** `GET /contest/contests/<int:contest_id>/registration-status/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
{
  "registered": true,
  "status": "REGISTERED",
  "registered_at": "2025-01-15T10:00:00Z",
  "participated_at": null
}
```

---

### 24. Get Contest Registrations List (Manager Only)
**Endpoint:** `GET /contest/contests/<int:contest_id>/registrations/`

**Headers:**
```json
{
  "Authorization": "Bearer manager_access_token"
}
```

**Success Response (200):**
```json
[
  {
    "id": 1,
    "user": {
      "id": 1,
      "username": "johndoe"
    },
    "contest": 1,
    "status": "REGISTERED",
    "registered_at": "2025-01-15T10:00:00Z",
    "participated_at": null
  }
]
```

---

### 25. Join Contest
**Endpoint:** `POST /contest/contests/<int:contest_id>/join/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{}
```

**Success Response (200):**
```json
{
  "message": "Joined contest successfully",
  "joined_at": "2025-02-01T10:05:00Z"
}
```

**Error Response (400):**
```json
{
  "error": "Contest is DRAFT, not LIVE",
  "contest_state": "DRAFT"
}
```

---

### 26. Leave Contest
**Endpoint:** `POST /contest/contests/<int:contest_id>/leave/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{}
```

**Success Response (200):**
```json
{
  "message": "Successfully left the contest"
}
```

---

### 27. Add Manager to Contest (Admin Only)
**Endpoint:** `POST /contest/contests/<int:contest_id>/add-manager/`

**Headers:**
```json
{
  "Authorization": "Bearer admin_access_token",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "user_id": 5
}
```

**Success Response (200):**
```json
{
  "message": "Manager added successfully"
}
```

---

### 28. Remove Manager from Contest (Admin Only)
**Endpoint:** `POST /contest/contests/<int:contest_id>/remove-manager/`

**Headers:**
```json
{
  "Authorization": "Bearer admin_access_token",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "user_id": 5
}
```

**Success Response (200):**
```json
{
  "message": "Manager removed successfully"
}
```

---

### 29. Add Problem to Contest (Manager Only)
**Endpoint:** `POST /contest/contests/<int:contest_id>/add-problem/`

**Headers:**
```json
{
  "Authorization": "Bearer manager_access_token",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "problem_id": 10,
  "order": 1
}
```

**Success Response (201):**
```json
{
  "message": "Problem added successfully"
}
```

**Error Response (400):**
```json
{
  "error": "Problem already in contest"
}
```

---

### 30. Remove Problem from Contest (Manager Only)
**Endpoint:** `DELETE /contest/contests/<int:contest_id>/remove-problem/<int:problem_id>/`

**Headers:**
```json
{
  "Authorization": "Bearer manager_access_token"
}
```

**Success Response (200):**
```json
{
  "message": "Problem removed successfully"
}
```

---

### 31. Get Contest Problems (LIVE Only)
**Endpoint:** `GET /contest/contests/<slug:slug>/problems/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
[
  {
    "id": 1,
    "problem_id": 1,
    "contest_id": 1,
    "problem": {
      "id": 1,
      "title": "Two Sum",
      "slug": "two-sum",
      "difficulty": "E"
    },
    "order": 1
  }
]
```

**Error Response (403):**
```json
{
  "error": "Contest is not LIVE"
}
```

---

### 32. Get Contest Problem Details (LIVE Only)
**Endpoint:** `GET /contest/contests/<slug:contest_slug>/problems/<slug:problem_slug>/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
{
  "id": 1,
  "title": "Two Sum",
  "slug": "two-sum",
  "statement": "Find two numbers that add up to target",
  "constraints": "1 <= nums.length <= 10^4",
  "difficulty": "E",
  "time_limit": 1000,
  "memory_limit": 256,
  "sample_test_cases": [
    {
      "id": 1,
      "input": "2 7 11 15\n9",
      "output": "0 1",
      "is_sample": true
    }
  ]
}
```

---

### 33. Submit Solution to Contest (LIVE Only)
**Endpoint:** `POST /contest/contests/<slug:contest_slug>/problems/<slug:problem_slug>/submit/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "language": "PY",
  "source_code": "def solution():\n    return [0, 1]"
}
```

**Success Response (201):**
```json
{
  "id": 1,
  "user_id": 1,
  "problem_id": 1,
  "contest_id": 1,
  "language": "PY",
  "status": "PENDING",
  "created_at": "2025-02-01T11:00:00Z"
}
```

**Error Response (403):**
```json
{
  "error": "Submission window closed",
  "seconds_until_end": 0
}
```

---

### 34. Get User Submissions for Problem (LIVE Only)
**Endpoint:** `GET /contest/contests/<slug:contest_slug>/problems/<slug:problem_slug>/submissions/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "problem_id": 1,
    "contest_id": 1,
    "language": "PY",
    "status": "AC",
    "created_at": "2025-02-01T11:00:00Z"
  }
]
```

---

### 35. Get Submission Details
**Endpoint:** `GET /contest/submissions/<int:submission_id>/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
{
  "id": 1,
  "user_id": 1,
  "problem_id": 1,
  "contest_id": 1,
  "language": "PY",
  "source_code": "def solution():\n    return [0, 1]",
  "status": "AC",
  "execution_time_ms": 45,
  "memory_usage_kb": 128,
  "created_at": "2025-02-01T11:00:00Z"
}
```

---

### 36. Get Contest Leaderboard
**Endpoint:** `GET /contest/contests/<slug:contest_slug>/leaderboard/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
[
  {
    "user": "johndoe",
    "user_id": 1,
    "total_score": 300,
    "problems": [
      {
        "problem_id": 1,
        "title": "Two Sum",
        "status": "AC",
        "solved_at": "2025-02-01T11:00:00Z"
      }
    ]
  }
]
```

---

### 37. Get User Contest Stats
**Endpoint:** `GET /contest/contests/<slug:slug>/my-stats/`

**Headers:**
```json
{
  "Authorization": "Bearer access_token"
}
```

**Success Response (200):**
```json
{
  "user": "johndoe",
  "contest": "Python Challenge",
  "total_problems": 5,
  "problems_solved": 3,
  "total_attempts": 8,
  "best_submission_time": "2025-02-01T11:00:00Z"
}
```

---

## MANAGER ENDPOINTS

### 38. View All Contest Submissions (Manager Only)
**Endpoint:** `GET /contest/contests/<int:contest_id>/manager/submissions/`

**Headers:**
```json
{
  "Authorization": "Bearer manager_access_token"
}
```

**Query Parameters (Optional):**
```
?user_id=1&problem_id=1&status=AC
```

**Success Response (200):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "username": "johndoe",
    "problem_id": 1,
    "problem_title": "Two Sum",
    "language": "PY",
    "status": "AC",
    "execution_time_ms": 45,
    "memory_usage_kb": 128,
    "created_at": "2025-02-01T11:00:00Z"
  }
]
```

---

### 39. View Submission Code (Manager Only)
**Endpoint:** `GET /contest/contests/<int:contest_id>/manager/submissions/<int:submission_id>/code/`

**Headers:**
```json
{
  "Authorization": "Bearer manager_access_token"
}
```

**Success Response (200):**
```json
{
  "id": 1,
  "user_id": 1,
  "problem_id": 1,
  "contest_id": 1,
  "language": "PY",
  "status": "AC",
  "source_code": "def solution():\n    nums = [2, 7, 11, 15]\n    target = 9\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]",
  "execution_time_ms": 45,
  "memory_usage_kb": 128,
  "created_at": "2025-02-01T11:00:00Z"
}
```

---

### 40. View Manager Leaderboard (Manager Only)
**Endpoint:** `GET /contest/contests/<int:contest_id>/manager/leaderboard/`

**Headers:**
```json
{
  "Authorization": "Bearer manager_access_token"
}
```

**Success Response (200):**
```json
{
  "contest_title": "Python Challenge",
  "total_participants": 150,
  "leaderboard": [
    {
      "rank": 1,
      "user": "johndoe",
      "user_id": 1,
      "total_score": 500,
      "problems": [
        {
          "problem_id": 1,
          "title": "Two Sum",
          "status": "AC",
          "submissions_count": 1
        }
      ]
    }
  ]
}
```

---

### 41. View Submission Analytics (Manager Only)
**Endpoint:** `GET /contest/contests/<int:contest_id>/manager/analytics/`

**Headers:**
```json
{
  "Authorization": "Bearer manager_access_token"
}
```

**Success Response (200):**
```json
{
  "contest_title": "Python Challenge",
  "total_submissions": 250,
  "unique_users_submitted": 120,
  "status_distribution": {
    "AC": 180,
    "WA": 40,
    "TLE": 15,
    "CE": 10,
    "RE": 5
  }
}
```

---

### 42. Export Contest Data (Manager Only)
**Endpoint:** `GET /contest/contests/<int:contest_id>/manager/export/`

**Headers:**
```json
{
  "Authorization": "Bearer manager_access_token"
}
```

**Query Parameters:**
```
?format=json
```
(Supports: `json`, `csv`)

**Success Response - JSON (200):**
```json
{
  "format": "json",
  "contest_title": "Python Challenge",
  "export_date": "2025-01-15T15:00:00Z",
  "data": [
    {
      "username": "johndoe",
      "email": "john@example.com",
      "problem": "Two Sum",
      "language": "PY",
      "status": "AC",
      "created_at": "2025-02-01T11:00:00Z"
    }
  ]
}
```

**Success Response - CSV (200):**
```
username,email,problem,language,status,created_at
johndoe,john@example.com,Two Sum,PY,AC,2025-02-01T11:00:00Z
```

---

## ERROR RESPONSES

### Common Error Codes

**400 Bad Request:**
```json
{
  "field_name": ["Error message"]
}
```

**401 Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden:**
```json
{
  "error": "You don't have permission to access this resource"
}
```

**404 Not Found:**
```json
{
  "detail": "Not found."
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error"
}
```

---

## SUMMARY TABLE

| Method | Endpoint | Permission | State Required | Response |
|--------|----------|-----------|----------------|----------|
| POST | /accounts/register/ | AllowAny | - | 201/400 |
| POST | /auth/login/ | AllowAny | - | 200/401 |
| POST | /auth/refresh/ | AllowAny | - | 200/401 |
| POST | /accounts/logout/ | IsAuthenticated | - | 200/400 |
| GET | /accounts/profile/<id>/ | IsAuthenticated | - | 200/404 |
| GET | /problems/ | AllowAny | - | 200 |
| GET | /problems/<slug>/ | AllowAny | - | 200/404 |
| POST | /submissions/ | IsAuthenticated | - | 201/400 |
| GET | /submissions/me/ | IsAuthenticated | - | 200 |
| GET | /submissions/<id>/ | IsAuthenticated | - | 200/404 |
| GET | /contest/contests/ | AllowAny | - | 200 |
| GET | /contest/contests/with-status/ | IsAuthenticated | - | 200 |
| GET | /contest/contests/search/ | IsAuthenticated | - | 200 |
| GET | /contest/contests/my-registrations/ | IsAuthenticated | - | 200 |
| POST | /contest/contests/create/ | IsAdminUser | - | 201/400 |
| GET | /contest/contests/<slug>/ | IsAuthenticated | - | 200/404 |
| GET | /contest/contests/<slug>/with-registration/ | IsAuthenticated | - | 200/404 |
| GET | /contest/contests/<slug>/status/ | IsAuthenticated | - | 200/404 |
| PUT | /contest/contests/<id>/update/ | IsContestManager | DRAFT/SCHEDULED | 200/400/403 |
| POST | /contest/contests/<id>/publish/ | IsContestManager | DRAFT | 200/400/403 |
| POST | /contest/contests/<id>/register/ | CanRegisterForContest | - | 201/400/403 |
| POST | /contest/contests/<id>/unregister/ | IsAuthenticated | - | 200/404 |
| GET | /contest/contests/<id>/registration-status/ | IsAuthenticated | - | 200 |
| GET | /contest/contests/<id>/registrations/ | IsContestManager | - | 200/403 |
| POST | /contest/contests/<id>/join/ | IsAuthenticated | LIVE | 200/400/403 |
| POST | /contest/contests/<id>/leave/ | IsAuthenticated | - | 200/404 |
| POST | /contest/contests/<id>/add-manager/ | IsAdminUser | - | 200/400 |
| POST | /contest/contests/<id>/remove-manager/ | IsAdminUser | - | 200/400 |
| POST | /contest/contests/<id>/add-problem/ | CanAddProblems | DRAFT/SCHEDULED | 201/400/403 |
| DELETE | /contest/contests/<id>/remove-problem/<id>/ | CanAddProblems | DRAFT/SCHEDULED | 200/400/403 |
| GET | /contest/contests/<slug>/problems/ | IsContestParticipant | LIVE | 200/403 |
| GET | /contest/contests/<slug>/problems/<slug>/ | IsContestParticipant | LIVE | 200/404/403 |
| POST | /contest/contests/<slug>/problems/<slug>/submit/ | CanSubmitSolution | LIVE | 201/400/403 |
| GET | /contest/contests/<slug>/problems/<slug>/submissions/ | IsContestParticipant | LIVE | 200/403 |
| GET | /contest/submissions/<id>/ | IsAuthenticated | - | 200/403/404 |
| GET | /contest/contests/<slug>/leaderboard/ | IsAuthenticated | - | 200/404 |
| GET | /contest/contests/<slug>/my-stats/ | IsAuthenticated | - | 200/404 |
| GET | /contest/contests/<id>/manager/submissions/ | IsContestManager | - | 200/403 |
| GET | /contest/contests/<id>/manager/submissions/<id>/code/ | IsContestManager | - | 200/403/404 |
| GET | /contest/contests/<id>/manager/leaderboard/ | IsContestManager | - | 200/403 |
| GET | /contest/contests/<id>/manager/analytics/ | IsContestManager | - | 200/403 |
| GET | /contest/contests/<id>/manager/export/ | IsContestManager | - | 200/403 |

---

## CONTENT-TYPE

All endpoints return/accept:
- **Request:** `Content-Type: application/json`
- **Response:** `Content-Type: application/json`

---

## AUTHENTICATION

All endpoints except `/accounts/register/` and `/auth/login/` require:
```json
{
  "Authorization": "Bearer <access_token>"
}
```

Get `access_token` by logging in at `/auth/login/`
