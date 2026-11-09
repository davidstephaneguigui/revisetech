
# Revisetech

**Revisetech** est une plateforme d'apprentissage (LMS) modulaire, pensée pour des élèves de filière technologique. Le concepteur est un professeur contractuel en STI2D. 
Conçue comme une Progressive Web App (PWA) "mobile-first", elle permet aux élèves de réviser leurs cours et de s'entraîner sur des quiz, tout en offrant aux enseignants et aux concepteurs des outils puissants de gestion de contenu et de suivi.

## 🎯 Objectifs du projet

L'objectif est de fournir un outil simple pour les élèves (utilisable sur iOS et Android sans passer par les stores) et suffisamment robuste pour gérer la complexité pédagogique des enseignants (classes, séquences, activités, validation).

## ✨ Fonctionnalités actuelles

### Pour les Apprenants (Élèves)
*   Connexion et inscription via un code d'invitation.
*   Navigation intuitive dans les matières, chapitres, séquences et séances.
*   Réalisation de Quiz avec calcul du score en temps réel.
*   Réception de suggestions de révision personnalisées de la part de l'enseignant.

### Pour les Enseignants
*   Création et gestion de classes (génération de codes d'invitation).
*   Association de matières validées à leurs classes.
*   Suivi détaillé des résultats de chaque élève.
*   Envoi de suggestions ciblées (cours à relire ou exercice à refaire).

### Pour les Concepteurs
*   Espace dédié à la création de contenu pédagogique.
*   Création de séquences et de séances.
*   Création d'activités (Cours, TP, Quiz) avec possibilité d'uploader des fichiers (SCORM, H5P, PDF).

### Pour les Référents et Superviseurs
*   Workflow de validation : soumission, validation et rejet des séquences et des chapitres.

## 🏗️ Architecture

Le projet suit les principes du **Domain-Driven Design (DDD)**. Chaque application Django correspond à un domaine métier spécifique :

*   `accounts` : Gestion de l'identité, des utilisateurs et du routage selon les rôles (Groupes Django).
*   `pedagogy` : Le référentiel de données pur (Matière, Chapitre, Séquence, Séance, Activité, Question). *Aucune vue métier ici.*
*   `authoring` : L'atelier du Concepteur (création de contenu).
*   `review` : Le bureau du Référent et de le Superviseur (workflow de validation).
*   `classroom` : L'espace Enseignant (gestion des classes et suggestions).
*   `learning` : L'espace Élève (navigation et résultats).

## 🛠️ Stack Technique

*   **Backend :** Python 3.13, Django 6.1.2
*   **Base de données :** SQLite (développement) / PostgreSQL (production future)
*   **Frontend :** HTML5, CSS3, Bootstrap 5
*   **Typographie :** Police Roboto (via Google Fonts)
*   **Futur :** React (îlots interactifs pour les Quiz et Dashboards), PWA (Manifest & Service Worker)

## 🚀 Installation en local

### Prérequis
*   Python 3.10+
*   Git

### Étapes

1. **Cloner le dépôt :**
   ```bash
   git clone https://github.com/davidstephaneguigui/revisetech.git
   cd revisetech

2. **Créer et activer l'environnement virtuel  :**
   ```bash
   python -m venv .venv

   # Sur Windows :
   .\.venv\Scripts\activate

   # Sur Mac/Linux :
   source .venv/bin/activate

3. **Installer les dépendances :**
   ```bash
   pip install -r requirements.txt

4. **Appliquer les migrations de base de données :**
   ```bash
   python manage.py migrate

5. **Création d'un super utilisateur (Administrateur)  :**
   ```bash
   python manage.py createsuperuser

6. **Lancer le serveur de développement :**
   ```bash
   python manage.py runserver

