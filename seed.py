from pedagogy.models import Matiere, Chapter, Sequence, Session, Activity, Question, Choice
from django.contrib.auth import get_user_model

User = get_user_model()
student = User.objects.get(username='apprenant1')
creator = User.objects.filter(username='Concepteur1').first() or student
classe = student.student_classes.first()

matiere, _ = Matiere.objects.get_or_create(name="Test React", defaults={'color_hex': '#6a1b9a', 'creator': creator})
chapter, _ = Chapter.objects.get_or_create(name="Chapitre React", matiere=matiere, defaults={'status': 'PUBLISHED'})
seq, _ = Sequence.objects.get_or_create(name="Séquence Quiz React", chapter=chapter, defaults={'status': 'PUBLISHED', 'creator': creator})
seq.classes.add(classe)
session, _ = Session.objects.get_or_create(name="Séance Quiz", sequence=seq, defaults={'status': 'PUBLISHED'})

# --- CORRECTION ICI ---
quiz, _ = Activity.objects.get_or_create(title="Le grand Quiz React", defaults={'activity_type': 'QUIZ', 'status': 'PUBLISHED'})
quiz.sessions.add(session) # On ajoute la séance après la création
# ----------------------

quiz.questions.all().delete()

q1 = Question.objects.create(activity=quiz, text="Quelle est la capitale de la France ?")
Choice.objects.create(question=q1, text="Paris", is_correct=True)
Choice.objects.create(question=q1, text="Londres", is_correct=False)
Choice.objects.create(question=q1, text="Berlin", is_correct=False)

q2 = Question.objects.create(activity=quiz, text="Combien font 2 + 2 ?")
Choice.objects.create(question=q2, text="3", is_correct=False)
Choice.objects.create(question=q2, text="4", is_correct=True)
Choice.objects.create(question=q2, text="5", is_correct=False)

q3 = Question.objects.create(activity=quiz, text="Quel framework JS utilisons-nous ?")
Choice.objects.create(question=q3, text="Angular", is_correct=False)
Choice.objects.create(question=q3, text="React", is_correct=True)
Choice.objects.create(question=q3, text="Vue", is_correct=False)

from classroom.models import ActivitySelection
ActivitySelection.objects.get_or_create(classe=classe, activity=quiz, defaults={'is_used': True})

print(f"✅ QUIZ CREE AVEC SUCCES ! ID = {quiz.id}")