# ICA Management System

Clean full-stack project root for the ICA platform.

## Structure

```text
Final_ICA/
  Back_End/    FastAPI backend, database models, migrations, services, tests
  Front_End/   React + Vite frontend
```

The backend remains the source of truth for business logic, permissions, roles, workflows, and validation. The frontend connects through `/api/*` during local development by using the Vite proxy.

Authentication uses one public login screen only. Accounts are created by admins through the backend user workflow; public registration is intentionally unavailable.

## Run locally

Start the backend:

```bash
cd Back_End
docker compose up --build
```

Start the frontend in another terminal:

```bash
cd Front_End
npm install
npm run dev
```

Frontend: `http://localhost:5173`

Backend docs: `http://localhost:8000/docs`

The frontend redirects users after login based on the backend account:

- `admin` -> Admin workspace
- `teacher` with `teacher_type=instructor` -> Instructor workspace
- `teacher` with `teacher_type=mentor` -> Mentor workspace
- `student` -> Student workspace

Default backend admin:

```text
email: admin@ica.eg
password: Admin@123456
```
