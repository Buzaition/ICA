# ICA Management System

FastAPI backend for the ICA Management System.

## Scope

This repository currently contains:

- Users
- Authentication
- Roles
- Refresh tokens
- Audit logs
- Health check
- Academic structure:
  - Branches
  - Cycles
  - Tracks
  - Levels
  - Classes
- Student enrollment and class membership
- Materials
- Assignments and submissions
- Grade ledger and assignment grade integration
- Attendance with manual entry, CSV upload, and grade ledger integration
- Quizzes with manual entry, CSV upload, and grade ledger integration
- Bonus system using the grade ledger
- Progress engine with immutable progress snapshots
- Calculated ranking
- Final projects with Admin level-completion approval
- Internal Admin notifications for low progress thresholds
- Read-only dashboards and summary endpoints

Transfer logic, automatic promotion logic, payments, live sessions, and external notifications are intentionally not implemented yet.

## Run

```bash
docker compose up --build
```

API docs are available at:

```text
http://localhost:8000/docs
```

## Tests

```bash
docker compose --profile test up --build --abort-on-container-exit tests
```

## Default Admin

```text
email: admin@ica.eg
password: Admin@123456
```

The default admin is seeded with `must_change_password = true`.
