# Quick Reference: New API Endpoints

## Challenge Endpoints (Manager Only)

### Create Challenge
```bash
POST /api/challenges/
Authorization: Bearer {token}

{
  "title": "string",
  "slug": "string",
  "statement": "string",
  "input_format": "string",
  "output_format": "string",
  "constraints": "string",
  "difficulty": "E|M|H",
  "tag_ids": [1, 2, ...]
}
```

### List My Challenges
```bash
GET /api/challenges/me/
Authorization: Bearer {token}
```

### Get Challenge Details
```bash
GET /api/challenges/{id}/
Authorization: Bearer {token}
```

### Update Challenge
```bash
PUT /api/challenges/{id}/
Authorization: Bearer {token}

{
  "title": "string",
  "statement": "string",
  ...
}
```

### Delete Challenge
```bash
DELETE /api/challenges/{id}/
Authorization: Bearer {token}
```

### Publish Challenge
```bash
POST /api/challenges/{id}/publish/
Authorization: Bearer {token}
```

### Add Test Case
```bash
POST /api/challenges/{id}/test-cases/
Authorization: Bearer {token}

{
  "input_data": "string",
  "expected_output": "string",
  "is_sample": true|false,
  "is_hidden": true|false
}
```

---

## Practice Problem Endpoints (Superuser Only)

### Create Practice Problem
```bash
POST /api/practice/problems/
Authorization: Bearer {token}

{
  "title": "string",
  "slug": "string",
  "statement": "string",
  "input_format": "string",
  "output_format": "string",
  "constraints": "string",
  "difficulty": "E|M|H",
  "tag_ids": [1, 2, ...],
  "is_published": true|false
}
```

### List All Practice Problems
```bash
GET /api/practice/problems/
```

### Get Practice Problem by Slug
```bash
GET /api/practice/problems/{slug}/
```

### Update Practice Problem
```bash
PUT /api/practice/problems/{id}/
Authorization: Bearer {token}

{
  "title": "string",
  "statement": "string",
  ...
}
```

### Delete Practice Problem
```bash
DELETE /api/practice/problems/{id}/
Authorization: Bearer {token}
```

### Add Test Case
```bash
POST /api/practice/problems/{id}/test-cases/
Authorization: Bearer {token}

{
  "input_data": "string",
  "expected_output": "string",
  "is_sample": true|false
}
```

---

## Response Examples

### Challenge List Response
```json
[
  {
    "id": 1,
    "title": "Two Sum",
    "slug": "two-sum",
    "difficulty": "E",
    "tags": [{"id": 1, "name": "array"}],
    "created_by": "manager_user",
    "is_public": false,
    "created_at": "2026-01-02T10:00:00Z"
  }
]
```

### Challenge Detail Response
```json
{
  "id": 1,
  "title": "Two Sum",
  "slug": "two-sum",
  "statement": "...",
  "input_format": "...",
  "output_format": "...",
  "constraints": "...",
  "difficulty": "E",
  "tags": [...],
  "test_cases": [...],
  "sample_test_cases": [...],
  "created_by": "manager_user",
  "is_public": false,
  "created_at": "2026-01-02T10:00:00Z",
  "updated_at": "2026-01-02T10:00:00Z"
}
```

### Practice Problem List Response
```json
[
  {
    "id": 1,
    "title": "Fibonacci Sequence",
    "slug": "fibonacci",
    "difficulty": "E",
    "tags": [...],
    "created_by": "superuser",
    "created_at": "2026-01-02T10:00:00Z"
  }
]
```

---

## Error Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | GET /api/challenges/1/ |
| 201 | Created | POST /api/challenges/ |
| 204 | No Content | DELETE /api/challenges/1/ |
| 400 | Bad Request | Invalid field data |
| 403 | Forbidden | Non-owner updating challenge |
| 404 | Not Found | Challenge ID doesn't exist |
| 500 | Server Error | Database error |

---

## Permission Requirements

| Operation | Permission |
|-----------|-----------|
| Create Challenge | is_staff (manager) |
| Edit Own Challenge | Owner or is_staff |
| Delete Own Challenge | Owner or is_staff |
| List Own Challenges | is_staff |
| View Any Challenge | Authenticated |
| Publish Challenge | Owner or is_staff |
| Create Practice Problem | is_superuser |
| Edit Practice Problem | is_superuser |
| Delete Practice Problem | is_superuser |
| List Practice Problems | Public (no auth) |
| View Practice Problem | Public (no auth) |

---

## Quick Setup Test

### 1. Create a test manager user
```bash
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.create_user(username='manager', email='m@test.com', password='pass')
>>> user.is_staff = True
>>> user.save()
```

### 2. Get authentication token
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "manager", "password": "pass"}'
```

### 3. Create a challenge
```bash
curl -X POST http://localhost:8000/api/challenges/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Challenge",
    "slug": "test-challenge",
    "statement": "Test statement",
    "input_format": "Test input",
    "output_format": "Test output",
    "constraints": "Test constraints",
    "difficulty": "E",
    "tag_ids": []
  }'
```

### 4. List challenges
```bash
curl -X GET http://localhost:8000/api/challenges/me/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. View practice problems (no auth needed)
```bash
curl http://localhost:8000/api/practice/problems/
```

---

## Common Questions

**Q: What's the difference between Challenge and PracticeProblem?**
A: Challenges are for contests (managers), Practice Problems are for public library (superusers).

**Q: Can a user see hidden test cases?**
A: No. Only the problem creator can see hidden test cases.

**Q: Can I publish a challenge multiple times?**
A: Yes, is_public is a boolean flag that can be toggled.

**Q: Do I need authentication to view practice problems?**
A: No, they are publicly accessible.

**Q: Can a manager create practice problems?**
A: No, only superusers can create practice problems.

**Q: Can a superuser manage challenges?**
A: Superusers have is_staff flag, so yes they can.

**Q: How are slugs generated?**
A: Automatically from title using Django's slugify. You can also provide custom slugs.

**Q: Can I change a slug after creation?**
A: Yes, but be careful as it will break existing slug-based links.

---

## Database Queries

### Get all challenges by a user
```python
from challenges.models import Challenge
challenges = Challenge.objects.filter(created_by=user)
```

### Get all public practice problems
```python
from challenges.models import PracticeProblem
problems = PracticeProblem.objects.filter(is_published=True)
```

### Get test cases for a challenge
```python
challenge = Challenge.objects.get(id=1)
test_cases = challenge.test_cases.all()
sample_cases = challenge.test_cases.filter(is_sample=True)
hidden_cases = challenge.test_cases.filter(is_hidden=True)
```

### Count problems by difficulty
```python
from django.db.models import Count
from challenges.models import PracticeProblem

stats = PracticeProblem.objects.filter(
    is_published=True
).values('difficulty').annotate(count=Count('id'))
```

---

## Admin Interface

All models are registered in Django admin:
- `/admin/challenges/tag/`
- `/admin/challenges/challenge/`
- `/admin/challenges/challengetestcase/`
- `/admin/challenges/practiceproblem/`
- `/admin/challenges/practiceproblmtestcase/`

---

## File Locations

```
/challenges
  /models.py           - Challenge, PracticeProblem models
  /serializers.py      - All serializers
  /views.py            - All view classes
  /permissions.py      - Permission classes
  /urls.py             - URL routing
  /admin.py            - Admin interface
  /migrations/0001     - Initial migration
```

