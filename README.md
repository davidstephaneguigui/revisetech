# Revisetech

**Revisetech** is a modular Learning Management System (LMS) designed for technology students. The designer is a contract teacher in STI2D. 
Conceived as a "mobile-first" Progressive Web App (PWA), it allows students to review their courses and practice quizzes, while providing teachers and designers with powerful content management and tracking tools.

## 🎯 Project Objectives

The goal is to provide a simple tool for students (usable on iOS and Android without going through app stores) that is robust enough to handle the pedagogical complexity for teachers (classes, sequences, activities, validation).

## ✨ Current Features

### For Learners (Students)
*   Login and registration via invitation code.
*   Intuitive navigation through subjects, chapters, sequences, and sessions.
*   Quizzes with real-time score calculation.
*   Receive personalized revision suggestions from the teacher.

### For Teachers
*   Create and manage classes (generate invitation codes).
*   Associate validated subjects with their classes.
*   Detailed tracking of each student's results.
*   Send targeted suggestions (courses to review or exercises to redo).

### For Designers
*   Dedicated workspace for pedagogical content creation.
*   Create sequences and sessions.
*   Create activities (Courses, Practical Work, Quizzes) with the ability to upload files (SCORM, H5P, PDF).

### For Referees and Supervisors
*   Validation workflow: submission, validation, and rejection of sequences and chapters.

## 🏗️ Architecture

The project follows the principles of **Domain-Driven Design (DDD)**. Each Django app corresponds to a specific business domain:

*   `accounts`: Identity management, users, and role-based routing (Django Groups).
*   `pedagogy`: The pure data repository (Subject, Chapter, Sequence, Session, Activity, Question). *No business views here.*
*   `authoring`: The Designer's workshop (content creation).
*   `review`: The Referee and Supervisor's office (validation workflow).
*   `classroom`: The Teacher's space (class management and suggestions).
*   `learning`: The Student's space (navigation and results).

## 🛠️ Tech Stack

*   **Backend:** Python 3.13, Django 6.1.2
*   **Database:** SQLite (development) / PostgreSQL (future production)
*   **Frontend:** HTML5, CSS3, Bootstrap 5
*   **Typography:** Roboto font (via Google Fonts)
*   **Future:** React (interactive islands for Quizzes and Dashboards), PWA (Manifest & Service Worker)

## 🚀 Local Installation

### Prerequisites
*   Python 3.10+
*   Git

### Steps

1. **Clone the repository:**
```bash
git clone https://github.com/davidstephaneguigui/revisetech.git
cd revisetech
```

2. **Create and activate the virtual environment:**
```bash
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate

# On Mac/Linux:
source .venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Apply database migrations:**
```bash
python manage.py migrate
```

5. **Create a superuser (Administrator):**
```bash
python manage.py createsuperuser
```

6. **Run the development server:**
```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`.
The admin panel is available at `http://127.0.0.1:8000/admin/`.

## 📝 Development Rules

*   **Code and comments:** Written exclusively in English.
*   **User Interface:** Entirely in French.
*   **Methodology:** Step-by-step resolution mode for complex tasks.
*   **Versioning:** One commit per stable feature with a clear message in English.

## 🗺️ Roadmap

- [ ] Finalize the validation workflow (Referee / Supervisor).
- [ ] Fix the display of Inlines in the Django admin.
- [ ] Transform the application into a PWA (Progressive Web App).
- [ ] Integrate React islands for interactive components (Quizzes, Dashboards).
- [ ] Create BPMN diagrams of the platform.

---
*Project developed by David Guigui.*