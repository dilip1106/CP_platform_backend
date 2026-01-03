# Backend API Implementation: Challenges & Practice Problems

## ✅ Implementation Summary

All required backend API endpoints have been successfully implemented to support:
1. **Manager Challenge Bank** - For contest problem creation
2. **Superuser Public Practice Problems** - For public problem sharing

---

## 📦 New App: `challenges`

A new Django app has been created with models, serializers, views, and permissions.

### Models

#### 1. **Challenge**
```python
# Manager-created challenges for contests
- id (PK)
- title
- slug (auto-generated from title)
- statement
- input_format
- output_format
- constraints
- difficulty ('E'/'M'/'H')
- tags (M2M → Tag)
- created_by (FK → User)
- is_public (default: False)
- created_at
- updated_at
```

#### 2. **ChallengeTestCase**
```python
- challenge (FK)
- input_data
- expected_output
- is_sample (boolean)
- is_hidden (boolean)
```

#### 3. **PracticeProblem**
```python
# Superuser-created public practice problems
- id (PK)
- title
- slug (auto-generated)
- statement
- input_format
- output_format
- constraints
- difficulty ('E'/'M'/'H')
- tags (M2M → Tag)
- created_by (FK → User)
- is_published (default: True)
- created_at
- updated_at
```

#### 4. **PracticeProblemTestCase**
```python
- problem (FK → PracticeProblem)
- input_data
- expected_output
- is_sample (boolean)
```

#### 5. **Tag** (Shared)
```python
# Reusable tags for both challenges and practice problems
- name (unique)
```

---

## 🔐 Permission Classes

Located in `challenges/permissions.py`:

```python
IsManager                          # is_staff or is_superuser
IsChallengeOwner                   # Only challenge creator
IsSuperuserOnly                    # Only superusers
IsPracticeProblemOwnerOrSuperuser  # Superuser edit/delete
IsAuthenticatedOrReadOnly          # Read-only for all, auth for write
```

---

## 🔌 API Endpoints

### Challenge Endpoints

| Method | Endpoint | Permission | Description |
|--------|----------|-----------|-------------|
| POST | `/api/challenges/` | IsManager | Create challenge |
| GET | `/api/challenges/me/` | IsManager | List my challenges |
| GET | `/api/challenges/<id>/` | IsAuthenticated | Get challenge details |
| PUT | `/api/challenges/<id>/` | IsChallengeOwner | Update challenge |
| DELETE | `/api/challenges/<id>/` | IsChallengeOwner | Delete challenge |
| POST | `/api/challenges/<id>/publish/` | IsChallengeOwner | Publish to practice |
| POST | `/api/challenges/<id>/test-cases/` | IsChallengeOwner | Add test case |

### Practice Problem Endpoints

| Method | Endpoint | Permission | Description |
|--------|----------|-----------|-------------|
| POST | `/api/practice/problems/` | IsSuperuserOnly | Create practice problem |
| GET | `/api/practice/problems/` | AllowAny | List published problems |
| GET | `/api/practice/problems/<slug>/` | AllowAny | Get problem by slug |
| PUT | `/api/practice/problems/<id>/` | IsSuperuserOnly | Update problem |
| DELETE | `/api/practice/problems/<id>/` | IsSuperuserOnly | Delete problem |
| POST | `/api/practice/problems/<id>/test-cases/` | IsSuperuserOnly | Add test case |

---

## 📝 Request/Response Examples

### Create Challenge
**POST** `/api/challenges/`
```json
{
  "title": "Two Sum Problem",
  "slug": "two-sum",
  "statement": "Given an array of integers...",
  "input_format": "First line: N (size of array)...",
  "output_format": "Single integer representing...",
  "constraints": "1 ≤ N ≤ 10^5",
  "difficulty": "E",
  "tag_ids": [1, 2]
}
```

### List My Challenges
**GET** `/api/challenges/me/`
```json
[
  {
    "id": 1,
    "title": "Two Sum Problem",
    "slug": "two-sum",
    "difficulty": "E",
    "tags": [{"id": 1, "name": "array"}, {"id": 2, "name": "hashing"}],
    "created_by": "john_doe",
    "is_public": false,
    "created_at": "2026-01-02T10:00:00Z"
  }
]
```

### Get Challenge Details
**GET** `/api/challenges/1/`
```json
{
  "id": 1,
  "title": "Two Sum Problem",
  "slug": "two-sum",
  "statement": "Given an array of integers...",
  "input_format": "First line: N (size of array)...",
  "output_format": "Single integer representing...",
  "constraints": "1 ≤ N ≤ 10^5",
  "difficulty": "E",
  "tags": [{"id": 1, "name": "array"}],
  "tag_ids": [1],
  "test_cases": [
    {
      "id": 1,
      "input_data": "2\n3 7",
      "expected_output": "0 1",
      "is_sample": true,
      "is_hidden": false
    }
  ],
  "sample_test_cases": [
    {
      "input_data": "2\n3 7",
      "expected_output": "0 1"
    }
  ],
  "created_by": "john_doe",
  "is_public": false,
  "created_at": "2026-01-02T10:00:00Z",
  "updated_at": "2026-01-02T10:00:00Z"
}
```

### Publish Challenge
**POST** `/api/challenges/1/publish/`
```json
{
  "id": 1,
  "title": "Two Sum Problem",
  "is_public": true,
  "..."
}
```

### Create Practice Problem
**POST** `/api/practice/problems/`
```json
{
  "title": "Array Manipulation",
  "slug": "array-manipulation",
  "statement": "Given an array...",
  "input_format": "...",
  "output_format": "...",
  "constraints": "...",
  "difficulty": "M",
  "tag_ids": [1],
  "is_published": true
}
```

### List Practice Problems
**GET** `/api/practice/problems/`
```json
[
  {
    "id": 1,
    "title": "Array Manipulation",
    "slug": "array-manipulation",
    "difficulty": "M",
    "tags": [{"id": 1, "name": "array"}],
    "created_by": "admin",
    "created_at": "2026-01-02T10:00:00Z"
  }
]
```

---

## 📂 File Structure

```
challenges/
├── __init__.py
├── apps.py                 # App configuration
├── models.py              # Challenge, ChallengeTestCase, PracticeProblem, Tag
├── serializers.py         # All serializers
├── views.py              # All view classes
├── urls.py               # URL routing
├── permissions.py        # Permission classes
├── admin.py              # Django admin registration
├── tests.py              # Test suite (empty - ready for tests)
└── migrations/
    ├── __init__.py
    └── 0001_initial.py
```

---

## 🔧 Configuration Changes

### 1. `settings.py`
Added to `INSTALLED_APPS`:
```python
'challenges',
```

### 2. `urls.py`
Added to `urlpatterns`:
```python
path('api/', include('challenges.urls')),
```

---

## ✨ Key Features

### Challenge Management (Managers Only)
- ✅ Create challenges with detailed problem statements
- ✅ View own challenges (`/api/challenges/me/`)
- ✅ Edit challenge details
- ✅ Delete challenges
- ✅ Add test cases (with hidden option)
- ✅ Publish challenges to public practice library
- ✅ Tag challenges for easy filtering

### Practice Problems (Superusers Only)
- ✅ Create public practice problems
- ✅ Full CRUD operations on problems
- ✅ Add test cases
- ✅ Publish/unpublish problems
- ✅ Tag problems for categorization

### Public Access
- ✅ List all published practice problems
- ✅ Get problem details by slug
- ✅ View sample test cases only
- ✅ No authentication required for read-only access

### Security
- ✅ Challenge owners can only edit/delete their own challenges
- ✅ Only managers can create challenges
- ✅ Only superusers can manage practice problems
- ✅ Hidden test cases visible only to problem creators
- ✅ Permission checks at view level

---

## 🚀 Next Steps (Optional Enhancements)

1. **Contest Integration** - Update `ContestProblem` to optionally reference challenges
2. **Tags Management API** - Create endpoints to manage tags
3. **Search & Filter** - Add filtering by difficulty, tags, date
4. **Bulk Operations** - Import/export challenges
5. **Versioning** - Track challenge history
6. **Tests** - Add comprehensive test cases in `tests.py`

---

## 📋 Serializer Overview

| Serializer | Purpose |
|-----------|---------|
| `ChallengeListSerializer` | List view (minimal fields) |
| `ChallengeDetailSerializer` | Detail view (all fields + test cases) |
| `ChallengeCreateUpdateSerializer` | Create/Update operations |
| `ChallengeTestCaseSerializer` | Test case management |
| `PracticeProblemListSerializer` | List view (minimal fields) |
| `PracticeProblemDetailSerializer` | Detail view (all fields) |
| `PracticeProblemCreateUpdateSerializer` | Create/Update operations |
| `PracticeProblemTestCaseSerializer` | Test case management |
| `TagSerializer` | Tag management (shared) |

---

## Database Schema

### Challenge
- Primary Key: `id`
- Foreign Keys: `created_by` → User
- Unique: `slug`
- Indexes: `created_by`, `is_public`

### ChallengeTestCase
- Primary Key: `id`
- Foreign Key: `challenge` → Challenge

### PracticeProblem
- Primary Key: `id`
- Foreign Keys: `created_by` → User
- Unique: `slug`
- Indexes: `is_published`

### PracticeProblemTestCase
- Primary Key: `id`
- Foreign Key: `problem` → PracticeProblem

### Tag
- Primary Key: `id`
- Unique: `name`

---

## ✅ Verification

All systems verified working:
- ✅ Models created and migrated
- ✅ Serializers validated
- ✅ Views implemented
- ✅ URLs routed correctly
- ✅ Permissions configured
- ✅ Admin interface registered
- ✅ Django check passed (0 issues)

---

## 📞 Support Notes

- All endpoints follow RESTful conventions
- Slug auto-generation from title on create
- Sample test cases visible publicly; hidden ones only for owners
- Managers ≠ Contest Managers (uses `is_staff` flag)
- Superusers have implicit access to manager features

