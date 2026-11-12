# Revisetech

**Revisetech** is a modular Learning Management System (LMS) designed for technology students. The designer is a contract teacher in STI2D. 
Conceived as a "mobile-first" Progressive Web App (PWA), it allows students to review their courses and practice quizzes, while providing teachers and designers with powerful content management and tracking tools.

## 🎯 Project Objectives

The goal is to provide a simple tool for students (usable on iOS and Android without going through app stores) that is robust enough to handle the pedagogical complexity for teachers (classes, sequences, activities, validation, pedagogical freedom).

## ✨ Current Features

### For Learners (Students)
*   Login and registration via invitation code.
*   Intuitive navigation through subjects, chapters, sequences, and sessions.
*   Quizzes with real-time score calculation and badge rewards.
*   Receive personalized revision suggestions from the teacher.
*   Access customized content: only activities selected by their teacher (or created locally for their class) are visible.

### For Teachers
*   Create and manage classes (generate invitation codes).
*   Associate validated subjects with their classes.
*   **Detailed student tracking**: 4-level navigation (Class -> Sequence -> Session -> Student Profile) with color-coded global scores (Option B calculation).
*   **Pedagogical Freedom**: 
    *   Track session completion (Done/Not done).
    *   Create local activities specific to their class.
    *   Select, deselect, and reorder activities for their sessions.
    *   Propose local activities to Designers for global publication.
*   **Activity Bank**: Browse and import activities shared by other teachers.
*   Send targeted suggestions (courses to review or exercises to redo).

### For Designers
*   Dedicated workspace for pedagogical content creation.
*   Create sequences and sessions.
*   Create activities (Courses, Practical Work, Quizzes).
*   **Proposals Workflow**: Review and accept/reject local activities proposed by teachers to promote them to the global repository.

### For Referees and Supervisors
*   **Validation workflow**: submission, validation, and rejection of intentions and contents.
*   **Second validation**: Ensure objectivity by preventing the first referee from giving a second review.
*   **Statistics Dashboard**: View aggregated statistics (average, min, max, success rate) on published sequences, without accessing individual grades.
*   Publish sequences and monitor their usage across classes.

## 🏗️ Architecture

The project follows the principles of **Domain-Driven Design (DDD)**. Each Django app corresponds to a specific business domain:

*   `accounts`: Identity management, users, and role-based routing (Django Groups).
*   `pedagogy`: The pure data repository (Subject, Chapter, Sequence, Session, Activity, Question). *No business views here.*
*   `authoring`: The Designer's workshop (content creation, proposals review, activity bank).
*   `review`: The Referee's office (pedagogical validation).
*   `publishing`: The Supervisor's office (final publication and sequence statistics).
*   `classroom`: The Teacher's space (class management, pedagogical freedom, local activities).
*   `learning`: The Student's space (navigation and results).
*   `core`: Cross-cutting views (home dashboard, help center).

## 🛠️ Tech Stack

*   **Backend:** Python 3.13, Django 6.1.2
*   **Database:** SQLite (development) / PostgreSQL (future production)
*   **Frontend:** HTML5, CSS3, Bootstrap 5, Vanilla JavaScript (AJAX for toggles and ordering)
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