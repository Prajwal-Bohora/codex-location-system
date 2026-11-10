# MID-WEST APP

Privacy-Aware Location Consent System, an academic Flask demonstration for university transport. It provides five role dashboards, MySQL/MariaDB support, consent-gated driver GPS updates, route and checkpoint management, and role-limited location endpoints.

## Requirements

- Windows 11 and Python 3.13
- MySQL 8 or XAMPP MariaDB (SQLite is used automatically for a zero-setup local demo)
- Modern browser; GPS requires localhost or HTTPS and user permission

## Install on Windows PowerShell

```powershell
cd D:\codex-location-system
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set a random `SECRET_KEY` and a database URL. To use XAMPP MariaDB, start MySQL in XAMPP, create the database and a dedicated account, then set e.g.:

```text
DATABASE_URL=mysql+pymysql://midwest_user:YOUR_PASSWORD@127.0.0.1:3306/midwest_app?charset=utf8mb4
```

Example MariaDB SQL (run in phpMyAdmin or the MariaDB client; replace the password):

```sql
CREATE DATABASE midwest_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'midwest_user'@'localhost' IDENTIFIED BY 'replace-with-a-long-password';
GRANT ALL PRIVILEGES ON midwest_app.* TO 'midwest_user'@'localhost';
FLUSH PRIVILEGES;
```

The app creates missing tables and roles at startup. This is suitable for a fresh academic/demo database. For future production schema changes, use Flask-Migrate/Alembic migrations rather than relying on `create_all` to change existing tables.

## First Super Admin

Set a separate `INITIAL_ADMIN_SETUP_TOKEN`, run the application, and open `http://127.0.0.1:5000/setup` once. Submit the token with the new account details. Setup is disabled after the first Super Admin exists, and it is unavailable if the token is unset. It requires a unique phone number and password of at least 12 characters. Clear the setup token from the deployment environment after creating the initial administrator.

## Run

```powershell
python app.py
```

Open `http://127.0.0.1:5000`. Browser GPS works on localhost; remote deployments need HTTPS. Set `COOKIE_SECURE=1` behind HTTPS and use a strong secret. For a local demonstration, the checked-in `.env` selects SQLite so the app can start before MySQL is installed. Replace it with your own secrets and database URL for a shared environment.

## Roles and privacy

- Super Admin manages all accounts, sees consented latest locations, and reviews audit activity.
- HOD/Admin manages teachers, drivers, students, ID photos, routes, drivers, and checkpoints. The map endpoint shows consented drivers.
- Teacher sees the student directory and cannot access location APIs.
- Driver sees assigned routes and checkpoints and controls GPS consent.
- Student selects a route and sees only that route's assigned drivers and checkpoints. Student location collection is not implemented.

Location access is server-enforced. Location writes require an authenticated driver with active consent. The consent withdrawal endpoint deletes that driver's precise retained location records. The browser requests explicit consent before asking for GPS, and sends updates every 15 seconds while sharing. Super Admin location overview includes consented users with recorded positions; the driver map is the driver's own route.

## Verification

```powershell
python -m compileall app.py config.py extensions.py models routes tests
python -m unittest discover -s tests -v
```

For a full manual walkthrough, initialize Super Admin, create an HOD, create a driver and a route, assign that driver, add checkpoints by map clicks, create a student, assign the route, then sign in as driver and grant consent. Check the student's route map and test teacher location API denial. Automated coverage is currently limited to startup/import checks; use the walkthrough for database, browser GPS, uploads, and role flows.

## Project layout

- `app.py`, `config.py`: Flask app, CSRF, session settings, initialization
- `models/`: users, roles, student profiles, consents, locations, routes, assignments, audit events
- `routes/`: authentication, role dashboards, management, and permission-checked location API
- `templates/`, `static/`: responsive Bootstrap UI, Leaflet maps, and browser GPS
- `instance/`: local database and private uploaded photos (created automatically)

This is an academic demonstration, not a substitute for security review, retention policy, operational monitoring, database backups, or production migrations.
