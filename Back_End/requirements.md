# ICA Management System - Requirements

## Scope

Build the ICA Management System incrementally.

Completed scope:

- Phase 1: authentication and user management foundation.
- Phase 2: academic structure.
- Phase 3: student enrollment and class membership.
- Phase 4: class materials management.
- Phase 5: assignments and submissions.
- Phase 6: grade ledger and assignment grade integration.
- Phase 7: attendance, CSV upload, and grade ledger integration.
- Phase 8: quizzes, CSV upload, and grade ledger integration.
- Phase 9: bonus system and grade ledger integration.
- Phase 10: progress engine and progress snapshots.
- Phase 11: ranking.
- Phase 12: final projects and level completion approval.

Do not implement notifications, transfer logic, or automatic promotion logic yet.

## Tech Stack

- Python 3.13+
- FastAPI
- PostgreSQL only
- SQLAlchemy 2.0 async
- Alembic
- Pydantic v2
- JWT authentication
- Refresh tokens stored in the database
- Argon2 password hashing
- Docker
- Docker Compose
- Pytest

## Required Modules

- Users
- Authentication
- Roles
- Refresh Tokens
- Audit Logs
- Health Check

## Roles

- Admin
- Teacher
- Student

## Teacher Types

- Mentor
- Instructor
- InstructorAndMentor

Implementation assumption: API enum values use snake_case for consistency with the project naming rule:

- `mentor`
- `instructor`
- `instructor_and_mentor`

## Entities

### User

- id UUID
- email unique
- password_hash
- role
- is_active
- must_change_password
- created_at
- updated_at
- deleted_at

### AdminProfile

- id UUID
- user_id
- full_name
- created_at
- updated_at

### TeacherProfile

- id UUID
- user_id
- teacher_code
- full_name
- phone_number
- teacher_type
- is_team_leader
- created_at
- updated_at

### StudentProfile

- id UUID
- user_id
- student_code
- full_name
- phone_number
- status
- created_at
- updated_at

### RefreshToken

- id UUID
- user_id
- token_hash
- expires_at
- revoked_at
- created_at

### AuditLog

- id UUID
- actor_id
- action
- entity_name
- entity_id
- old_value
- new_value
- created_at

## Endpoints

- GET /health
- POST /api/auth/login
- POST /api/auth/refresh
- POST /api/auth/logout
- POST /api/auth/change-password
- POST /api/auth/reset-password
- GET /api/auth/me
- POST /api/users
- GET /api/users
- GET /api/users/{id}
- PUT /api/users/{id}
- DELETE /api/users/{id}

## Business Rules

- No public registration.
- Only Admin can create users.
- Only Admin can reset passwords.
- Delete users using soft delete.
- Password must never be returned.
- Email must be unique.
- New users must have `must_change_password = true`.
- Default admin must be seeded.

## Default Admin

- email: `admin@ica.eg`
- password: `Admin@123456`
- must_change_password: `true`

## API Response Format

Success:

```json
{
  "success": true,
  "message": "Operation completed",
  "data": {}
}
```

Error:

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": []
}
```

## Architecture Rules

- FastAPI routes must contain no business logic.
- Business logic must be inside services/use cases.
- Database access must be inside repositories.
- Domain models must not depend on FastAPI.
- Avoid circular imports.
- Do not leave TODO comments.
- Do not create placeholder code.
- Do not leave broken imports.

## Database Rules

- Use UUID primary keys.
- Use snake_case table and column names.
- Use Alembic migrations.
- Initial migration must create:
  - users
  - admin_profiles
  - teacher_profiles
  - student_profiles
  - refresh_tokens
  - audit_logs

## Docker

The project must run with:

```bash
docker compose up --build
```

## Testing

Create pytest tests for:

- health endpoint
- admin login
- refresh token
- protected endpoint without token
- GET /api/auth/me with token
- admin creates user
- non-admin cannot create user
- soft delete user

Tests must pass before marking Phase 1 complete.

## Current Implementation Assumptions

- User creation accepts a nested profile object matching the selected role: `admin_profile`, `teacher_profile`, or `student_profile`.
- The API uses unified response envelopes for success and handled error responses.
- Refresh token raw values are returned only at issue/rotation time; only SHA-256 token hashes are stored.
- Soft-deleted users are excluded from normal read/list/auth flows.
- Test profile uses a separate `ica_test` PostgreSQL database.

# Phase 2 Requirements - Academic Structure

## Scope

Implement academic structure only:

- Branch
- Cycle
- Track
- Level
- Class

Do not implement student enrollment, attendance, assignments, quizzes, materials, ranking, progress engine, notifications, or final projects.

## Entities

### Branch

- id UUID
- name unique
- created_at
- updated_at
- deleted_at

### Cycle

- id UUID
- cycle_number unique
- name
- start_date
- end_date
- status: active, closed
- created_at
- updated_at
- deleted_at

### Track

- id UUID
- code unique
- name unique
- track_number unique
- created_at
- updated_at
- deleted_at

### Level

- id UUID
- track_id
- level_number
- title
- duration_months default 2
- created_at
- updated_at
- deleted_at

Rules:

- Each Track has 3 levels by default.
- Level number must be 1, 2, or 3.
- Level must belong to one Track.
- Prevent duplicate level_number inside the same Track.

### Class

- id UUID
- code unique
- branch_id
- cycle_id
- track_id
- level_id
- instructor_id
- mentor_id
- schedule_text
- max_students default 25
- class_type: onsite, online
- start_date
- end_date
- status: planned, active, completed, cancelled
- created_at
- updated_at
- deleted_at

Rules:

- Class belongs to Branch, Cycle, Track, and Level.
- Class has one Instructor and one Mentor.
- The same Teacher may be both Instructor and Mentor.
- instructor_id and mentor_id must reference TeacherProfile.
- Class max_students cannot exceed 25.
- schedule_text is plain text for now.
- Class code must be unique.
- Level must belong to the same Track selected for the Class.

## Class Code Format

Example: `BE1001`

- First two letters: Track code.
- First digit after letters:
  - `1` = online
  - `5` = onsite
- Last three digits: class sequence.

Examples:

- `BE1001` = Backend online class #001
- `BE5001` = Backend onsite class #001

## Authorization

- Admin can create/update/delete Branch, Cycle, Track, Level, and Class.
- Teachers can view only classes assigned to them.
- Students can view only their active class later; student-class enrollment is not implemented in Phase 2.

## Endpoints

Branches:

- POST /api/branches
- GET /api/branches
- GET /api/branches/{id}
- PUT /api/branches/{id}
- DELETE /api/branches/{id}

Cycles:

- POST /api/cycles
- GET /api/cycles
- GET /api/cycles/{id}
- PUT /api/cycles/{id}
- DELETE /api/cycles/{id}

Tracks:

- POST /api/tracks
- GET /api/tracks
- GET /api/tracks/{id}
- PUT /api/tracks/{id}
- DELETE /api/tracks/{id}

Levels:

- POST /api/levels
- GET /api/levels
- GET /api/levels/{id}
- PUT /api/levels/{id}
- DELETE /api/levels/{id}

Classes:

- POST /api/classes
- GET /api/classes
- GET /api/classes/{id}
- PUT /api/classes/{id}
- DELETE /api/classes/{id}
- GET /api/teachers/me/classes

## Database

Create Alembic migration for:

- branches
- cycles
- tracks
- levels
- classes

Indexes and constraints:

- unique branch name
- unique cycle_number
- unique track code
- unique track_number
- unique class code
- unique track_id + level_number
- foreign keys for branch_id, cycle_id, track_id, level_id, instructor_id, mentor_id

## Seed Data

- Branch: Main Branch
- Cycle: Cycle 1, active
- Tracks:
  - Backend, code BE, track_number 14
  - Frontend, code FE, track_number 13
- For each track, create levels 1, 2, 3.

## Phase 2 Tests

- Admin can create branch.
- Non-admin cannot create branch.
- Admin can create cycle.
- Admin can create track.
- Creating a track auto-creates 3 levels if requested.
- Cannot create duplicate track code.
- Cannot create duplicate level number inside same track.
- Cannot create class with max_students > 25.
- Cannot create class when level does not belong to selected track.
- Teacher can view only assigned classes.
- Soft delete works.

# Phase 3 Requirements - Student Enrollment and Class Membership

## Scope

Implement student enrollment into classes only.

Do not implement attendance, assignments, quizzes, materials, ranking, progress engine, notifications, final projects, transfer logic, or promotion logic.

## Entity

### ClassEnrollment

- id UUID
- student_id FK -> student_profiles.id
- class_id FK -> classes.id
- status: active, completed, removed
- enrolled_at
- completed_at nullable
- removed_at nullable
- created_at
- updated_at
- deleted_at

## Business Rules

- A student cannot belong to more than one active class at the same time.
- Class maximum capacity is 25 students.
- Enrollment connects a StudentProfile to a Class.
- Student transfer between classes is not implemented in Phase 3.
- Student promotion to next level is not implemented in Phase 3.
- Student active class is determined through enrollment records.
- Enrollment must be soft-deletable and auditable.
- Only Admin can enroll or remove students from classes.
- Teachers can view students only in their assigned classes.
- Students can view only their own active class.
- Cannot enroll into a class if class status is cancelled or completed.
- Cannot enroll inactive, suspended, dropped, or graduated students into class.
- Cannot exceed class max_students.
- Removing enrollment sets status to removed and removed_at.
- Removing enrollment does not delete history.
- Soft-deleted enrollment history must remain queryable for Admin.
- If student already has active enrollment, return validation error.

## Endpoints

Admin:

- POST /api/enrollments
- GET /api/enrollments
- GET /api/enrollments/{id}
- DELETE /api/enrollments/{id}

Teacher:

- GET /api/teachers/me/classes/{class_id}/students

Student:

- GET /api/students/me/class

## Database

Create Alembic migration for:

- class_enrollments

Constraints and indexes:

- FK student_id
- FK class_id
- index student_id
- index class_id
- index status
- partial unique index to enforce one active enrollment per student where status = `active` and deleted_at is null

## Current Phase 3 Assumptions

- Student statuses include `active`, `inactive`, `suspended`, `dropped`, and `graduated`.
- Enrollment removal uses status `removed`, sets removed_at, and sets deleted_at for soft-delete semantics.
- Admin enrollment list/get includes removed soft-deleted enrollment history.
- There is no endpoint to view another student's enrollment; the student endpoint always resolves from the authenticated student.

# Phase 4 Requirements - Materials Module

## Scope

Implement class materials management using external links only.

Do not implement file upload, attendance, assignments, quizzes, grade ledger, progress engine, ranking, notifications, final projects, transfer logic, or promotion logic.

## Material Types

- pdf
- video
- external_file

## Creator Roles

- instructor
- mentor

## Entity

### Material

- id UUID
- class_id FK -> classes.id
- creator_id FK -> teacher_profiles.id
- creator_role: instructor, mentor
- title
- description nullable
- material_type
- url
- is_active boolean default true
- created_at
- updated_at
- deleted_at

## Business Rules

- Material belongs to exactly one class.
- Material creator must be a TeacherProfile.
- Teacher can create material only for classes assigned to them.
- If the teacher is assigned as instructor, creator_role can be instructor.
- If the teacher is assigned as mentor, creator_role can be mentor.
- If same teacher is both instructor and mentor in same class, they may choose either creator_role.
- Teacher cannot create material for unassigned classes.
- Teacher can update/delete only materials they created.
- Admin can view/update/delete all materials.
- Students can view only active materials for their active class.
- Materials must be soft deleted.
- URL must be a valid URL.
- Title is required.

## Endpoints

Teacher/Admin:

- POST /api/materials
- GET /api/materials
- GET /api/materials/{id}
- PUT /api/materials/{id}
- DELETE /api/materials/{id}

Student:

- GET /api/students/me/materials

Teacher assigned class materials:

- GET /api/teachers/me/classes/{class_id}/materials

## Database

Create Alembic migration for:

- materials

Constraints and indexes:

- FK class_id
- FK creator_id
- index class_id
- index creator_id
- index material_type
- index creator_role
- index deleted_at

# Phase 5 Requirements - Assignments and Submissions

## Scope

Implement assignments, student submissions, pending assignment review pages, reviewed assignments pages, and late assignments pages.

Do not implement attendance, quizzes, grade ledger, progress engine, ranking, notifications, final projects, transfer logic, or promotion logic.

This phase stores assignment review data but must not create GradeEntry records. Grade Ledger will be implemented in Phase 6 and will backfill or connect reviewed assignment grades.

Corrections are not implemented in Phase 5. Correction history and grade correction workflows will be implemented with Grade Ledger in Phase 6. Do not create correction tables in Phase 5.

## Entities

### Assignment

- id UUID
- class_id FK -> classes.id
- created_by_teacher_id FK -> teacher_profiles.id
- title
- description nullable
- requirement_url
- deadline
- max_grade
- is_active boolean default true
- created_at
- updated_at
- deleted_at

### AssignmentSubmission

- id UUID
- assignment_id FK -> assignments.id
- student_id FK -> student_profiles.id
- submission_url
- submitted_at
- grade nullable
- feedback nullable
- status: submitted, reviewed, late, replaced, rejected
- reviewed_at nullable
- reviewed_by_teacher_id nullable FK -> teacher_profiles.id
- created_at
- updated_at
- deleted_at

## Assignment Rules

- Assignment belongs to exactly one class.
- Only assigned Instructor or assigned Mentor can create assignments for their assigned classes.
- Admin can create assignments for any class but must provide created_by_teacher_id.
- Assignment max_grade must be greater than 0.
- requirement_url must be a valid URL.
- Assignment title is required.
- Assignment deadline is required.
- Students can view only assignments for their active class.
- Teachers can view only assignments for assigned classes.
- Admin can view all assignments.
- Assignments are soft-deleted.

## Submission Rules

- Student can submit only to assignments in their active class.
- Student can submit a link only.
- submission_url must be a valid URL.
- If submitted before or at deadline, status is submitted.
- If submitted after deadline, status is late.
- Student can resubmit before deadline.
- When student resubmits before deadline, old latest active submission status becomes replaced and new submission status becomes submitted.
- Old submissions are not deleted.
- Student cannot resubmit after deadline if there is already a reviewed submission.
- Student can view own submissions only.
- Teachers can view submissions only for assigned classes.
- Admin can view all submissions.

## Review Rules

- Teacher must be assigned to the submission class to review.
- Admin can review any submission but must provide reviewed_by_teacher_id.
- Validate grade >= 0.
- Validate grade <= assignment.max_grade.
- Save grade.
- Save feedback if provided.
- Set reviewed_at.
- Set reviewed_by_teacher_id.
- Set status = reviewed.
- Reviewed submission disappears from Pending Assignments.
- Do not create GradeEntry in Phase 5.
- Do not update student progress in Phase 5.

## Pending, Reviewed, and Late Pages

Pending submissions:

- reviewed_at is null
- grade is null
- status is submitted or late
- current student progress returns null because progress engine is not implemented yet

Reviewed assignments include reviewed submissions and review metadata.

Late assignments show submissions with status = late and reviewed_at is null.

Teachers can reject late submissions:

- status = rejected
- reviewed_at is set
- reviewed_by_teacher_id is set
- grade remains null
- feedback may be stored
- no GradeEntry is created later in Phase 5

## Endpoints

Assignments:

- POST /api/assignments
- GET /api/assignments
- GET /api/assignments/{id}
- PUT /api/assignments/{id}
- DELETE /api/assignments/{id}

Student:

- GET /api/students/me/assignments
- POST /api/assignments/{assignment_id}/submit
- GET /api/students/me/submissions

Teacher:

- GET /api/teachers/me/classes/{class_id}/assignments
- GET /api/teachers/me/assignments/pending
- GET /api/teachers/me/assignments/reviewed
- GET /api/teachers/me/assignments/late
- POST /api/assignment-submissions/{submission_id}/review
- POST /api/assignment-submissions/{submission_id}/reject

Admin:

- GET /api/assignment-submissions
- GET /api/assignment-submissions/{id}

## Database

Create Alembic migration for:

- assignments
- assignment_submissions

Assignment indexes and constraints:

- FK class_id
- FK created_by_teacher_id
- index class_id
- index created_by_teacher_id
- index deadline
- index deleted_at

Submission indexes and constraints:

- FK assignment_id
- FK student_id
- FK reviewed_by_teacher_id nullable
- index assignment_id
- index student_id
- index status
- index reviewed_at
- index deleted_at

# Phase 6 Requirements - Grade Ledger and Assignment Grade Integration

## Scope

Implement the grade ledger and integrate assignment review with it.

Do not implement attendance, quizzes, progress engine, ranking, notifications, final projects, transfer logic, or promotion logic.

## Entity

### GradeEntry

- id UUID
- student_id FK -> student_profiles.id
- class_id FK -> classes.id
- teacher_id nullable FK -> teacher_profiles.id
- category: assignment, attendance, quiz, bonus, correction
- earned_grade
- max_grade
- source_type: manual, csv_upload, system_bonus, correction
- reason nullable
- related_entry_id nullable FK -> grade_entries.id
- assignment_submission_id nullable FK -> assignment_submissions.id
- created_by_user_id FK -> users.id
- created_at
- deleted_at nullable

## Business Rules

- GradeEntry records are immutable.
- Grade entries must not be updated or hard-deleted.
- Corrections are new GradeEntry records with category `correction`, source_type `correction`, related_entry_id pointing to the original entry, reason required, max_grade `0`, and earned_grade allowed to be positive or negative.
- Cannot create a correction for a correction entry.
- Assignment review creates one GradeEntry exactly once.
- Assignment GradeEntry values use category `assignment`, earned_grade equal to the reviewed grade, max_grade equal to assignment.max_grade, source_type `manual`, reason `Assignment Review`, assignment_submission_id set, student_id set, class_id set, teacher_id equal to reviewed_by_teacher_id, and created_by_user_id equal to the authenticated user.
- Rejected late submissions create no GradeEntry.
- Assignment review responses include grade_entry_id.
- Reviewed assignment pages include grade_entry_id.
- Admin can view all grade entries and create corrections for any entry.
- Teachers can view and correct grade entries only for assigned classes.
- Students can view only their own grade entries and corrections.

## Endpoints

- GET /api/grade-entries
- GET /api/grade-entries/{id}
- GET /api/students/me/grade-entries
- GET /api/teachers/me/classes/{class_id}/grade-entries
- POST /api/grade-entries/{grade_entry_id}/corrections
- GET /api/grade-entries/{grade_entry_id}/corrections
- GET /api/teachers/me/corrections-history
- GET /api/admin/corrections-history

## Database

Create Alembic migration for:

- grade_entries

Constraints and indexes:

- FK student_id
- FK class_id
- FK teacher_id nullable
- FK created_by_user_id
- FK related_entry_id nullable self-reference
- FK assignment_submission_id nullable
- index student_id
- index class_id
- index teacher_id
- index category
- index source_type
- index related_entry_id
- index assignment_submission_id
- index deleted_at
- partial unique index for assignment_submission_id where assignment_submission_id is not null and deleted_at is null

## Current Phase 6 Assumptions

- `/api/grade-entries` returns entries visible to the authenticated user: Admin all entries, Teacher assigned-class entries, Student own entries.
- Correction history `corrected_by` is returned as the user email that created the correction.
- Re-reviewing an already reviewed submission returns the existing reviewed result and grade_entry_id without changing the recorded submission grade.

# Phase 7 Requirements - Attendance, CSV Upload, and Grade Ledger Integration

## Scope

Implement attendance sessions, attendance records, CSV upload, manual attendance editing, and attendance GradeEntry creation.

Do not implement quizzes, progress engine, ranking, notifications, final projects, transfer logic, or promotion logic.

## Entities

### AttendanceSession

- id UUID
- class_id FK -> classes.id
- teacher_id FK -> teacher_profiles.id
- session_type: instructor, mentor
- session_date
- max_grade default 1
- source_type: manual, csv_upload
- created_by_user_id FK -> users.id
- created_at
- updated_at
- deleted_at

### AttendanceRecord

- id UUID
- attendance_session_id FK -> attendance_sessions.id
- student_id FK -> student_profiles.id
- status: present, late, absent
- grade_entry_id nullable FK -> grade_entries.id
- created_at
- updated_at
- deleted_at

## Business Rules

- Attendance is per session.
- Each month defaults conceptually to 8 instructor sessions and 4 mentor sessions; no monthly generation is implemented in Phase 7.
- Present earns 1/1, late earns 0.5/1, absent earns 0/1.
- Attendance session belongs to exactly one class.
- Only assigned teachers can create or upload attendance for assigned classes.
- Assigned instructors can create instructor sessions.
- Assigned mentors can create mentor sessions.
- If the same teacher is both instructor and mentor, they can choose either session_type.
- Admin can create or upload attendance for any class but must provide teacher_id.
- session_date is required.
- Duplicate active sessions are prevented by class_id, teacher_id, session_type, and session_date.
- If CSV or manual attendance is submitted for an existing same session, the existing session is reused.
- For each student in attendance, create or update AttendanceRecord.
- Create the original attendance GradeEntry only once per AttendanceRecord.
- If attendance status changes later, do not mutate the original GradeEntry; create a correction GradeEntry for the grade difference.
- Attendance records apply only to active students enrolled in the class.
- Invalid or non-enrolled CSV rows are skipped and returned in an error report.
- CSV upload supports partial success.
- No progress calculation is implemented in Phase 7.

## Endpoints

Teacher/Admin:

- POST /api/attendance/manual
- POST /api/attendance/upload-csv
- GET /api/attendance/sessions
- GET /api/attendance/sessions/{id}
- GET /api/attendance/sessions/{id}/records
- PUT /api/attendance/records/{id}

Teacher:

- GET /api/teachers/me/classes/{class_id}/attendance

Student:

- GET /api/students/me/attendance

Admin:

- GET /api/attendance

## Database

Create Alembic migration for:

- attendance_sessions
- attendance_records

AttendanceSession constraints and indexes:

- FK class_id
- FK teacher_id
- FK created_by_user_id
- index class_id
- index teacher_id
- index session_date
- index session_type
- index deleted_at
- unique partial index on class_id, teacher_id, session_type, session_date where deleted_at is null

AttendanceRecord constraints and indexes:

- FK attendance_session_id
- FK student_id
- FK grade_entry_id
- index attendance_session_id
- index student_id
- index status
- index deleted_at
- unique partial index on attendance_session_id, student_id where deleted_at is null

## Current Phase 7 Assumptions

- Manual attendance returns the same result envelope shape as CSV upload, including session, records, counts, and errors.
- Admin-provided teacher_id must match the selected session role for the class.
- Updating an attendance record is allowed for Admin or the assigned teacher matching the session_type.
- Non-enrolled manual records are skipped in the returned error list, matching CSV partial-success behavior.

# Phase 8 Requirements - Quizzes, CSV Upload, and Grade Ledger Integration

## Scope

Implement quizzes, manual quiz result entry, CSV upload for quiz results, and quiz GradeEntry creation.

Do not implement progress engine, ranking, notifications, final projects, transfer logic, or promotion logic.

## Entities

### Quiz

- id UUID
- class_id FK -> classes.id
- teacher_id FK -> teacher_profiles.id
- title
- description nullable
- quiz_date
- max_grade
- source_type: manual, csv_upload
- created_by_user_id FK -> users.id
- created_at
- updated_at
- deleted_at

### QuizResult

- id UUID
- quiz_id FK -> quizzes.id
- student_id FK -> student_profiles.id
- earned_grade
- max_grade
- grade_entry_id nullable FK -> grade_entries.id
- created_at
- updated_at
- deleted_at

## Business Rules

- Quiz belongs to exactly one class.
- Only assigned teachers can create or upload quiz results for assigned classes.
- Admin can create or upload quiz results for any class but must provide teacher_id.
- Quiz max_grade must be greater than 0.
- Quiz earned_grade must be between 0 and quiz.max_grade.
- Quiz results apply only to active students enrolled in the class.
- Invalid or non-enrolled CSV rows are skipped and returned in an error report.
- CSV upload supports partial success.
- Duplicate active quizzes are prevented by class_id, teacher_id, title, and quiz_date.
- For the same quiz and student, do not create duplicate QuizResult.
- If a result is resubmitted or changed, update QuizResult but do not mutate the original GradeEntry.
- Result changes create a correction GradeEntry for the grade difference.
- GradeEntry category is `quiz`.
- GradeEntry source_type is `manual` or `csv_upload`.
- No progress calculation is implemented in Phase 8.

## CSV Upload

CSV columns:

- student_code
- earned_grade
- max_grade

CSV max_grade must match quiz.max_grade for each valid row. Invalid numeric values, max_grade mismatches, and earned_grade greater than max_grade are skipped and reported.

## Endpoints

Teacher/Admin:

- POST /api/quizzes/manual
- POST /api/quizzes/upload-csv
- GET /api/quizzes
- GET /api/quizzes/{id}
- GET /api/quizzes/{id}/results
- PUT /api/quiz-results/{id}

Teacher:

- GET /api/teachers/me/classes/{class_id}/quizzes

Student:

- GET /api/students/me/quizzes

Admin:

- GET /api/quiz-results

## Database

Create Alembic migration for:

- quizzes
- quiz_results

Quiz constraints and indexes:

- FK class_id
- FK teacher_id
- FK created_by_user_id
- index class_id
- index teacher_id
- index quiz_date
- index deleted_at
- unique partial index on class_id, teacher_id, title, quiz_date where deleted_at is null

QuizResult constraints and indexes:

- FK quiz_id
- FK student_id
- FK grade_entry_id
- index quiz_id
- index student_id
- index deleted_at
- unique partial index on quiz_id, student_id where deleted_at is null

## Current Phase 8 Assumptions

- Manual quiz entry returns the same result envelope shape as CSV upload, including quiz, results, counts, and errors.
- Admin-provided teacher_id must reference an existing TeacherProfile, but it does not have to be assigned to the class.
- Reusing an existing quiz with a different max_grade is rejected to protect existing result grading.
- Non-enrolled manual result rows are skipped in the returned error list, matching CSV partial-success behavior.

# Phase 9 Requirements - Bonus System and Grade Ledger Integration

## Scope

Implement bonus grades using the existing GradeEntry ledger.

Do not implement progress engine, ranking, notifications, final projects, transfer logic, or promotion logic.

## Entity

No new bonus table is required. Bonus records are GradeEntry rows.

Bonus GradeEntry fields:

- category = bonus
- earned_grade = 1
- max_grade = 0
- source_type = system_bonus
- reason = provided reason or `Bonus`
- teacher_id = authenticated teacher profile id when a Teacher gives bonus
- teacher_id = null when an Admin gives bonus
- created_by_user_id = authenticated user id

## Business Rules

- Bonus is a separate grade category.
- Bonus does not belong to attendance, quiz, or assignment.
- Each click/action gives +1 bonus grade.
- Maximum bonus per student per class per ISO week is 5.
- Weekly count uses GradeEntry.created_at and ISO week/year.
- Bonus can be given only to active enrolled students.
- Teacher can give bonus only to students in assigned classes.
- Admin can give bonus to any active enrolled student.
- Student cannot give bonus.
- Bonus entries are immutable.
- Bonus corrections are allowed through the existing GradeEntry correction mechanism.
- Bonus must not calculate progress in Phase 9.

## Endpoints

- POST /api/bonus
- GET /api/bonus
- GET /api/students/me/bonus
- GET /api/teachers/me/classes/{class_id}/bonus

## Database

No migration is required for Phase 9 because the existing grade_entries table already stores:

- student_id
- class_id
- teacher_id nullable
- category
- earned_grade
- max_grade
- source_type
- reason
- created_by_user_id
- created_at
- deleted_at

Weekly bonus limits are calculated from created_at.

## Current Phase 9 Assumptions

- `/api/bonus` list visibility follows role scope: Admin all, Teacher assigned classes, Student own entries.
- Weekly bonus count is per student and class, matching the Phase 9 requirement.
- The response includes weekly count and remaining values for each listed entry using that entry's ISO week.

# Phase 10 Requirements - Progress Engine and Progress Snapshots

## Scope

Implement progress calculation from GradeEntry records and immutable progress snapshots.

Do not implement ranking, notifications, final projects, transfer logic, or promotion logic.

## Formula

- Attendance contributes 20%.
- Quizzes contribute 30%.
- Assignments contribute 50%.
- Bonus is added after weighted progress.
- Final progress is capped at 100.

For attendance, quiz, and assignment:

- category_score = sum earned_grade including applicable corrections / sum max_grade excluding correction max_grade.
- If a category has no max_grade, category score is 0.
- Correction entries affect the category of their related original entry.
- Bonus entries have max_grade = 0 and add earned_grade as points after weighted progress.

Student final progress:

- attendance_progress = attendance_score * 20
- quiz_progress = quiz_score * 30
- assignment_progress = assignment_score * 50
- bonus_progress = sum bonus earned_grade
- final_progress = min(100, attendance_progress + quiz_progress + assignment_progress + bonus_progress)

Class progress is the average final_progress of active students in the class.

Instructor progress equals class progress. Mentor progress equals 50 + class_progress / 2.

## Entity

### ProgressSnapshot

- id UUID
- student_id FK -> student_profiles.id
- class_id FK -> classes.id
- week_number
- year
- attendance_progress
- quiz_progress
- assignment_progress
- bonus_progress
- final_progress
- created_at

## Business Rules

- Do not store editable progress on StudentProfile.
- Progress is calculated from GradeEntry.
- Snapshots are immutable historical records.
- Snapshots are created on demand in Phase 10.
- Do not auto-schedule weekly snapshots yet.
- Snapshot creation creates one snapshot per active enrolled student in the class.
- Admin can create snapshots for any class.
- Teacher can create snapshots only for assigned classes.
- Student cannot create snapshots.
- Progress is calculated for active enrollments/classes only unless Admin requests history.

## Endpoints

Student:

- GET /api/students/me/progress

Teacher:

- GET /api/teachers/me/classes/{class_id}/progress
- POST /api/teachers/me/classes/{class_id}/progress-snapshots

Admin:

- GET /api/progress/students/{student_id}
- GET /api/progress/classes/{class_id}
- GET /api/progress/classes/{class_id}/snapshots
- POST /api/progress/classes/{class_id}/snapshots
- GET /api/progress/teachers/{teacher_id}

## Database

Create Alembic migration for:

- progress_snapshots

Indexes:

- student_id
- class_id
- week_number
- year
- created_at

## Current Phase 10 Assumptions

- Admin student progress endpoint uses the student's active enrollment.
- Teacher progress averages class progress across classes where the teacher is instructor, and averages mentor-adjusted progress across classes where the teacher is mentor.
- Snapshot list endpoints return historical rows in newest-first order.

# Phase 11 Requirements - Ranking

## Scope

Implement ranking endpoints based on current calculated progress.

Do not implement notifications, final projects, transfer logic, or promotion logic.

## Business Rules

- Ranking is based on final_progress from Phase 10.
- Higher final_progress ranks first.
- Duplicate ranks are allowed.
- Ties use dense ranking:
  - 100 => rank 1
  - 95 => rank 2
  - 95 => rank 2
  - 90 => rank 3
- Student can see only top 3 ranking for their active class.
- Teacher can see full ranking only for assigned classes.
- Admin can view ranking by class and by track.
- Current ranking includes active enrollments only.
- Removed, suspended, dropped, graduated, or otherwise inactive students are excluded through active enrollment and active student filters.
- Ranking responses include calculated progress fields from Phase 10.

## Endpoints

Student:

- GET /api/students/me/ranking/top3

Teacher:

- GET /api/teachers/me/classes/{class_id}/ranking

Admin:

- GET /api/ranking/classes/{class_id}
- GET /api/ranking/tracks/{track_id}

## Database

No migration is required. Ranking is calculated from current progress and is not stored.

## Current Phase 11 Assumptions

- Track ranking includes active students from active classes under the selected track.
- Tied students are ordered by student_code within the same rank for deterministic responses.

# Phase 12 Requirements - Final Projects and Level Completion Approval

## Scope

Implement final project submission and Admin review for level completion.

Do not implement notifications, transfer logic, or automatic promotion logic.

## Entity

### FinalProject

- id UUID
- student_id FK -> student_profiles.id
- class_id FK -> classes.id
- level_id FK -> levels.id
- project_link
- grade nullable
- feedback nullable
- status: pending, approved, rejected
- submitted_at
- reviewed_at nullable
- reviewed_by_admin_id nullable FK -> admin_profiles.id
- created_at
- updated_at
- deleted_at

## Business Rules

- Student can submit final project only for active class.
- Final project belongs to the current class level.
- project_link must be a valid URL.
- Student can have only one active final project submission per class and level.
- If project is pending, student may update project_link.
- If project is approved or rejected, student cannot edit it.
- Admin can review final projects.
- Teacher can view final projects only for assigned classes.
- Student can view own final project only.
- Approval does not automatically move student to next level.
- Promotion or creating next class enrollment will be handled by a later phase/manual Admin action.
- Final projects are soft-deletable in schema; no delete endpoint is implemented in Phase 12.

## Endpoints

Student:

- POST /api/students/me/final-project
- GET /api/students/me/final-project
- PUT /api/students/me/final-project

Teacher:

- GET /api/teachers/me/classes/{class_id}/final-projects

Admin:

- GET /api/final-projects
- GET /api/final-projects/{id}
- POST /api/final-projects/{id}/review

## Database

Create Alembic migration for:

- final_projects

Constraints and indexes:

- FK student_id
- FK class_id
- FK level_id
- FK reviewed_by_admin_id
- index student_id
- index class_id
- index level_id
- index status
- index deleted_at
- unique partial index on student_id, class_id, level_id where deleted_at is null

## Current Phase 12 Assumptions

- Re-submitting while the existing project is pending updates the pending project_link and returns the same project.
- Admin review may update an already reviewed project, but does not create promotion/enrollment changes.

# Phase 13: Admin Notifications

Implement internal Admin notifications based on current progress thresholds.

Do not implement transfer, automatic promotion, payments, live sessions, or external notifications.

## Entity

### Notification

- id UUID
- type: student_low_progress, instructor_low_progress, mentor_low_progress
- title
- message
- target_user_id nullable
- target_student_id nullable
- target_teacher_id nullable
- class_id nullable
- severity: info, warning, critical
- is_read boolean default false
- read_at nullable
- created_at
- updated_at
- deleted_at

## Notification Rules

- Notify Admin when Student Progress is below 50%.
- Notify Admin when Instructor Progress is below 50%.
- Notify Admin when Mentor Progress is below 70%.
- Notifications are internal only.
- Do not use Email, SMS, WhatsApp, push, or external providers.
- Avoid duplicate unread notification for the same target, same type, and same class.
- If progress improves above threshold, existing notifications are not auto-deleted.

## Endpoints

Admin only:

- GET /api/admin/notifications
- GET /api/admin/notifications/unread-count
- POST /api/admin/notifications/check-progress
- POST /api/admin/notifications/{id}/mark-read
- POST /api/admin/notifications/mark-all-read

## Business Rules

- Only Admin can view and manage notifications.
- check-progress calculates current progress using Phase 10 services.
- If threshold is violated, create notification.
- Do not create duplicate unread notification for same type, target, and class.
- Mark-read sets is_read=true and read_at.
- Soft delete is supported in schema; no delete endpoint is implemented in Phase 13.

## Database

Create Alembic migration for:

- notifications

Constraints and indexes:

- FK target_user_id
- FK target_student_id
- FK target_teacher_id
- FK class_id
- index type
- index target_user_id
- index target_student_id
- index target_teacher_id
- index class_id
- index is_read
- index deleted_at

## Current Phase 13 Assumptions

- Progress checks create one notification per threshold violation per class.
- Instructor low progress is evaluated per assigned instructor class using class progress.
- Mentor low progress is evaluated per assigned mentor class using the Phase 10 mentor formula for that class.

# Phase 14: Dashboards & Summary Endpoints

Implement read-only dashboard endpoints for Admin, Teacher, and Student using existing data.

Do not implement transfer, automatic promotion, payments, live sessions, external notifications, or external analytics.

No new tables are required for Phase 14.

## Endpoints

- GET /api/admin/dashboard
- GET /api/teachers/me/dashboard
- GET /api/students/me/dashboard

## Admin Dashboard

Returns:
- total_students
- active_students
- suspended_students
- graduated_students
- dropped_students
- total_teachers
- total_classes
- active_classes
- low_progress_students_count
- low_progress_instructors_count
- low_progress_mentors_count
- unread_notifications_count
- tracks_summary
- classes_summary

## Teacher Dashboard

Returns:
- teacher_id
- teacher_name
- assigned_classes_count
- assigned_classes
- average_instructor_progress
- average_mentor_progress
- pending_assignments_count
- reviewed_assignments_count
- late_assignments_count
- low_progress_students_count
- materials_count
- attendance_sessions_count
- quizzes_count

## Student Dashboard

Returns:
- student_id
- student_code
- student_name
- status
- active_class
- progress
- ranking_top3
- materials_count
- assignments_count
- submissions_count
- attendance_summary
- quizzes_summary
- final_project_status

Student dashboard does not include unread_notifications_count because notifications are Admin-only.

## Business Rules

- Dashboards are read-only.
- Use existing services where possible.
- Do not duplicate progress logic.
- Do not create new business rules.
- Admin dashboard can see all data.
- Teacher dashboard only includes assigned classes.
- Student dashboard only includes own data.
- Use unified API response format.

## Current Phase 14 Assumptions

- Low-progress dashboard counts use current calculated progress, not notification rows.
- Student attendance and quiz summaries are scoped to the student's active class.
- Teacher assigned_classes includes one item per role when the same teacher is both instructor and mentor for a class.
