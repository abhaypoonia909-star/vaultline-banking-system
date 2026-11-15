# Banking Management System with Brute Force Simulation

Vaultline is the web version of the original command-line banking program. Customers can register, open accounts, deposit, withdraw, and review history. Administrators can see the whole book and deactivate accounts. A local brute-force simulation checks demo accounts inside this application only.

The original program is still in `bankingsysbruteforce.py`. The web app does not read `accounts.txt`.

## Layout

```
frontend/     React, Vite, React Router, Axios, Chart.js
backend/      Flask REST API, SQLAlchemy, JWT, Flask-Migrate
bankingsysbruteforce.py
accounts.txt  legacy CLI file, gitignored, not used by the API
```

Python cannot import a module named `app.py` and a package named `app` from the same folder. The API lives in the `backend/app` package, so production starts with `gunicorn app:app`. Local development uses `python run.py`.

## Local setup

Requirements: Python 3.11, Node.js 22, and PostgreSQL when you want the production database. The API reads `DATABASE_URL`. If that variable is missing in development, it uses a local SQLite file so the app can boot. Production refuses SQLite.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
copy .env.example .env
```

Edit `backend/.env` and set long random values for `SECRET_KEY`, `JWT_SECRET_KEY`, and `ADMIN_PASSWORD`. For PostgreSQL:

```text
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/banking
```

Create the database, then apply migrations:

```powershell
.\.venv\Scripts\python -m flask --app "app:create_app" db upgrade
.\.venv\Scripts\python run.py
```

The API listens on `http://127.0.0.1:5000`. Health check: `GET /api/health`.

```powershell
cd frontend
npm install
npm run dev
```

The UI listens on `http://127.0.0.1:5173` and reads `VITE_API_BASE_URL` from `frontend/.env.development`.

### Tests

```powershell
cd backend
.\.venv\Scripts\python -m pytest
```

The automated suite uses an in-memory SQLite database through the same models and migrations. On this machine it passed 10 tests covering health, registration, login, JWT logout, accounts, deposits, withdrawals, history, authorization, admin deactivation, and the local simulation.

`npm run build` in `frontend/` completed successfully.

## Original command-line program

```powershell
$env:ADMIN_USERNAME="your-admin"
$env:ADMIN_PASSWORD="your-admin-password"
python bankingsysbruteforce.py
```

The CLI still stores rows in `accounts.txt`. That file contains plaintext secrets, is listed in `.gitignore`, and must not be uploaded. The previous hardcoded admin password was removed from `bankingsysbruteforce.py` so it would not be published with the source.

## API

All protected routes expect `Authorization: Bearer <access_token>`. Errors use `{ "error": "message" }` and standard status codes.

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| GET | `/api/health` | Public | Process and database status |
| POST | `/api/auth/register` | Public | Create a customer and return a JWT |
| POST | `/api/auth/login` | Public | Sign in. Limited to 5 requests a minute per IP |
| POST | `/api/auth/logout` | Customer | Revoke the current token |
| GET | `/api/auth/me` | Customer | Current profile |
| POST | `/api/auth/change-password` | Customer | Replace the password hash |
| GET | `/api/accounts` | Customer | Own active accounts and total balance |
| POST | `/api/accounts` | Customer | Open an account. Maximum 10 |
| GET | `/api/accounts/balance` | Customer | Balance summary |
| GET | `/api/accounts/<id>` | Owner | Account plus recent transactions |
| POST | `/api/transactions/deposit` | Owner | Deposit. Requires the account PIN |
| POST | `/api/transactions/withdraw` | Owner | Withdraw. Rejects insufficient funds and non-positive amounts |
| GET | `/api/transactions/history` | Customer | History and deposit/withdrawal totals |
| GET | `/api/admin/dashboard` | Admin | Bank-wide totals and alerts |
| GET | `/api/admin/accounts` | Admin | Every active account |
| DELETE | `/api/admin/accounts/<id>` | Admin | Deactivate an account |
| POST | `/api/security/brute-force-simulation` | Customer | Local weak-password simulation |
| GET | `/api/security/logs` | Customer | Attempts, alerts, and simulation history |

Deposit and withdraw body:

```json
{ "account_id": 1, "amount": "25.00", "pin": "2468" }
```

Simulation body:

```json
{ "account_id": 1, "attempts": 6, "acknowledge": true }
```

`attempts` must be from 1 to 6. Custom wordlists are rejected. The response reports counts only. It does not return a password, PIN, or hash.

Passwords and PINs are stored with Werkzeug PBKDF2 hashes. Money movement runs in a database transaction. On PostgreSQL the account row is locked for the update. Customers receive 404 for accounts they do not own.

An administrator is created at startup when `ADMIN_USERNAME`, `ADMIN_PASSWORD` (at least 8 characters), and `ADMIN_EMAIL` are set and that username does not already exist. Changing the environment variable later does not reset an existing admin password.

## Security simulation

The simulation uses the original six-word list from `bankingsysbruteforce.py` and compares those guesses to the account owner's password hash. It can target only an account in this database, and only when the caller owns it or is an admin. Repeated failures and a weak-password match are written to the security log without the secret.

Do not point this feature at any system outside this application. There is no setting for a remote host or a user-supplied password list.

## GitHub

This folder is not a git repository, and no remote is configured. Nothing has been pushed.

1. On GitHub, under [abhaypoonia909-star](https://github.com/abhaypoonia909-star), create an empty repository. Do not add a generated README or license, or the first push will diverge.
2. From this project folder:

```powershell
git init
git add .
git status
git commit -m "Add the Vaultline banking web application."
git branch -M main
git remote add origin https://github.com/abhaypoonia909-star/YOUR-REPO.git
git push -u origin main
```

Check `git status` before the commit. `accounts.txt`, `.env`, `backend/.venv`, `frontend/node_modules`, and database files must stay untracked. Say if you want this commit created for you. I will not push without an explicit request.

## Render backend

These steps prepare the service. They do not create a live URL.

1. Push the repository first.
2. In Render, create a PostgreSQL database and copy its external URL.
3. Create a Web Service from the same repository.
4. Set the root directory to `backend`.
5. Build command: `pip install -r requirements.txt`
6. Start command: `gunicorn app:app`
7. Health check path: `/api/health`
8. Set environment variables:
   - `APP_ENV=production`
   - `DATABASE_URL` from the Render Postgres URL (`postgres://` is rewritten to `postgresql+psycopg2://`)
   - `SECRET_KEY` and `JWT_SECRET_KEY`, each a different long random string
   - `CORS_ORIGINS` set to the Vercel site origin after the frontend exists, for example `https://your-app.vercel.app`
   - `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_EMAIL`
   - `PYTHON_VERSION=3.11.9`

`gunicorn.conf.py` binds `0.0.0.0:$PORT`, so the start command stays `gunicorn app:app`. Optional release command:

```text
python -m flask --app "app:create_app" db upgrade
```

The process also runs `create_all()` when `AUTO_CREATE_TABLES=1`, which is the default. A root `render.yaml` describes the same service and leaves secrets unset. Do not treat a guessed `onrender.com` address as deployed.

Gunicorn is installed and the `app:app` import loads. Gunicorn cannot boot its worker on Windows; Render runs Linux, which is the environment that command targets.

## Vercel frontend

These steps prepare the project. They do not create a live URL.

1. In the [Vercel dashboard](https://vercel.com/abhaypoonia909-stars-projects), import this repository.
2. Set the root directory to `frontend`.
3. Framework preset: Vite. Build command: `npm run build`. Output directory: `dist`.
4. Add `VITE_API_BASE_URL` with the Render origin and no trailing slash, for example `https://your-api.onrender.com`.
5. Deploy again after saving the variable. Vite copies it into the bundle at build time.
6. `frontend/vercel.json` rewrites unknown paths to `index.html` so client-side routes survive a refresh.

Then set Render `CORS_ORIGINS` to the exact Vercel origin and redeploy the API. The browser will show the configured API host on the sign-in page.

## What is not live yet

No Render service and no Vercel project were created from this session. There are no production URLs to report.
