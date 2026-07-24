# Habitz — Build Better Habits, Stay Consistent

Habitz is a secure **Flask-based habit tracking web application** that helps users build consistency through streak tracking, task management, and activity visualization.

It is designed to solve a common problem: **maintaining habits over time**. By combining streak mechanics, progress tracking, and a clean dashboard, Habitz encourages users to stay accountable and develop long-term routines.

---

### Video Demo Link: https://youtu.be/hUch3M5wgBg
##  Live Features

###  Authentication System

* User registration & login
* Secure password hashing (`werkzeug.security`)
* Session-based authentication (`Flask-Session`)
* Logout functionality
* Token-based password reset (expires in 10 minutes)

---

###  Dashboard

* View active habits
* Track completed habits
* Quick overview of progress
* Central hub for user activity

---

###  Habit Management

Users can:

* Create habits with:

  * Name
  * Description
  * Start & end dates
* Edit existing habits
* Mark habits as completed
* Favorite important habits
* Sort habits by:

  * Start date
  * End date
  * Alphabetical order
  * Favorite priority

---

### Streak Tracking System

Habitz includes a powerful streak system that tracks:

* Current streak
* Longest streak
* Last completion date

**Logic:**

* If completed yesterday → streak increases
* If missed → streak resets to 1

This system encourages **daily consistency and long-term discipline**.

---

### Login Streak & Activity Tracking

* Tracks daily logins
* Prevents duplicate entries
* Maintains login streaks
* Stores login history

---

### Calendar View

* Displays last **30 days of login activity**
* Highlights active days
* Shows current login streak

This provides a **visual consistency tracker**, similar to GitHub’s contribution graph.

---

### Settings Page

Users can:

* Update username
* Change password
* Reset all habit streaks
* Clear completion history
* Delete account (with confirmation modal)

---

### Dark Mode

* Toggle between light and dark themes
* Stored in `localStorage`
* Persistent across sessions

---


## Tech Stack

| Layer          | Technology                       |
| -------------- | -------------------------------- |
| Backend        | Flask (Python)                   |
| Database       | SQLite3                          |
| Frontend       | HTML, Bootstrap 5, Jinja2        |
| Authentication | Flask Sessions                   |
| Security       | Password Hashing + Secure Tokens |

---

## Core Concepts Implemented

### Streak Logic

```python
if last_date == today - timedelta(days=1):
    streak += 1
else:
    streak = 1
```

---

### Secure Password Reset

* Token generated using `secrets.token_hex(32)`
* Expires after **10 minutes**
* One-time use only
* Stored securely in database

---

### Login Tracking

* Uses server-side time (prevents manipulation)
* Tracks daily activity
* Updates login streak automatically

---

## Database Schema

The application uses **SQLite (`habit.db`)** with the following tables:

* `users` → user credentials & login streaks
* `habits` → habit/task data
* `completions` → completed habits
* `login_activity` → login history
* `password_resets` → reset tokens

---

## Project Structure

```
habitz/
│
├── app.py
├── habit.db
│
├── templates/
│   ├── layout.html
│   ├── dashboard.html
│   ├── overview.html
│   ├── tasks.html
│   ├── calendar.html
│   ├── settings.html
│   ├── login.html
│   ├── register.html
│   └── password.html
│
├── static/
    ├── styles.css
    ├── icons/
    └── images/
```

---

## Key Routes

### Authentication

| Route       | Method   | Description   |
| ----------- | -------- | ------------- |
| `/login`    | GET/POST | Login user    |
| `/register` | GET/POST | Register user |
| `/logout`   | GET      | Logout        |

### Core Features

| Route        | Method   | Description       |
| ------------ | -------- | ----------------- |
| `/dashboard` | GET      | Dashboard         |
| `/tasks`     | GET/POST | Create habits     |
| `/overview`  | GET/POST | Manage habits     |
| `/calendar`  | GET      | Activity calendar |

### Settings

| Action          | Description             |
| --------------- | ----------------------- |
| Update username | Change display name     |
| Change password | Update credentials      |
| Reset streaks   | Reset all habit streaks |
| Clear history   | Delete completions      |
| Delete account  | Remove all user data    |

### Password Reset

| Route            | Description          |
| ---------------- | -------------------- |
| `/reset`         | Generate reset token |
| `/reset/<token>` | Reset password       |

---

## Setup Instructions

### 1. Install Dependencies

```bash
pip install flask flask-session
```

### 2. Run Application

```bash
python app.py
```

### 3. Open Browser

```
http://127.0.0.1:5000 (add port 5000 if its not available)
python -m flask run in command prompt
```

---

## Security Features

* Password hashing (`generate_password_hash`)
* Password verification (`check_password_hash`)
* Secure token generation (`secrets`)
* Token expiration & one-time use
* SQL injection protection (parameterized queries)
* Server-side validation for streak logic

---
## What This Project Demonstrates

* Full-stack Flask development
* Authentication & session management
* Secure system design
* Database modeling (SQLite)
* Real-world feature implementation (streak systems, tokens)
* Clean UI design with Bootstrap

---

## Author

Built as a full-stack project to practice backend development, security, and UI integration using Flask. I took CS50.

---

## License

This project is for educational purposes.
I took CS50.
