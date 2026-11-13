from apps.learning.models import Result


def get_student_global_score(student):
    """
    Calcule le score global d'un élève (Option B : total des points / total possible).
    Retourne un tuple (score_sur_20, couleur_hex).
    """
    results = Result.objects.filter(student=student)
    
    total_obtained = 0
    total_possible = 0
    
    for r in results:
        if r.activity:
            total_obtained += r.score
            # On compte le nombre de questions de l'activité
            total_possible += r.activity.questions.count()
            
    if total_possible == 0:
        return None, "secondary" # Gris (pas de note)
        
    percentage = (total_obtained / total_possible) * 100
    score_20 = (percentage * 20) / 100
    
    if score_20 >= 15:
        color = "#198754" # Vert
    elif score_20 >= 10:
        color = "#ffc107" # Jaune
    elif score_20 >= 5:
        color = "#fd7e14" # Orange
    else:
        color = "#dc3545" # Rouge
        
    return round(score_20, 1), color


def compute_sequence_stats(sequence, classe=None):
    """
    Calcule les stats (moyenne, min, max, nb_élèves) pour une séquence donnée.
    Si une classe est fournie, filtre sur cette classe.
    """
    # 1. On récupère toutes les activités de la séquence
    activities = []
    for session in sequence.sessions.all():
        for activity in session.activities.all():
            activities.append(activity)

    # 2. On récupère les résultats pour ces activités
    results = Result.objects.filter(activity__in=activities)
    if classe:
        results = results.filter(student__student_classes=classe).distinct()

    # 3. On regroupe par élève pour calculer leur score global sur la séquence
    student_scores = {}
    for res in results:
        if res.student_id not in student_scores:
            student_scores[res.student_id] = {'obtained': 0, 'total': 0}
        student_scores[res.student_id]['obtained'] += res.score
        student_scores[res.student_id]['total'] += res.activity.questions.count()

    # 4. On calcule les notes sur 20
    scores_sur_20 = []
    for s_id, data in student_scores.items():
        if data['total'] > 0:
            score = (data['obtained'] / data['total']) * 20
            scores_sur_20.append(score)

    if not scores_sur_20:
        return None, None, None, 0

    # 5. On retourne moyenne, min, max, effectif
    return (sum(scores_sur_20) / len(scores_sur_20)), min(scores_sur_20), max(scores_sur_20), len(scores_sur_20)