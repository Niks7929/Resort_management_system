# Resort Management System (Flask + MySQL)

## 1. Install
```
python -m venv venv
venv\Scripts\activate          # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
```

## 2. Configure MySQL
```sql
CREATE DATABASE resort_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'resort_user'@'localhost' IDENTIFIED BY 'a-strong-password';
GRANT ALL PRIVILEGES ON resort_db.* TO 'resort_user'@'localhost';
FLUSH PRIVILEGES;
```
The project uses the existing `.env` file. Fill in SECRET_KEY and the MYSQL_* values there.
Generate a key with: `python -c "import secrets; print(secrets.token_hex(32))"`

## 3. Create tables and the first admin
```
flask --app app init-db
flask --app app create-admin
```
The admin password is checked against the password rules and stored as a bcrypt hash.
Public registration can only ever create Guest accounts.
After deploying updates that add database tables, run `flask --app app init-db` again. Admins can edit the public landing page from the staff sidebar.

### Local development admin

Create a Super Admin with `flask --app app create-admin`, then use the email and password entered at the prompts on `http://127.0.0.1:5000/staff/login`. Do not commit admin credentials or real secrets to GitHub.

Check the MySQL connection and (optionally) add sample rooms for the landing page:
```
flask --app app check-db
flask --app app seed-rooms
```

## 4. Run
```
python app.py
```
Open http://127.0.0.1:5000/

## Sign-in pages
- Guests: `/login` and `/register` (guest accounts only)
- Staff (admin, manager, receptionist, housekeeping, restaurant): `/staff/login`
- Staff accounts are created by an Admin at `/staff/new`; only the Super Admin can create Admins.
- Each portal rejects the other type of account.

## Connected modules

The current application connects these modules through the Flask blueprints, SQLAlchemy models, and role-based navigation:

- Authentication, guest registration, staff login, logout, password change, and lockout
- Dashboard and landing page management
- Rooms inventory with search, filters, CRUD, and availability states
- Guest and front-desk bookings with overlap checks, tax, discounts, payments, and invoices
- Check-in, check-out, room status changes, and automatic housekeeping tasks
- Housekeeping task assignment and completion
- Staff management and role-based access for Super Admin, Admin, Manager, Receptionist, Housekeeping, and Restaurant staff
- Activity logging and MySQL persistence

To verify the database connection, run `flask --app app check-db`. To create the tables and sample rooms, run `flask --app app init-db` and `flask --app app seed-rooms`.

## What is built (phase 1)
Auth (login, logout, register, change password, lockout after 5 failed attempts, CSRF, bcrypt),
role decorators, rooms CRUD with search/filter/pagination, bookings with overlap prevention and
automatic nights/discount/tax/total/balance, check-in/check-out, payments, printable invoice,
housekeeping (task auto-created at check-out, room released when cleaned), activity log records,
dashboard stats, guest dashboard, 403/404/500 pages.

## Still to add (next phases, same patterns)
Password reset by email, guests/employees/attendance, services, restaurant, inventory, suppliers,
offers, feedback, notifications, maintenance, reports/export, dashboard charts, image uploads.
