from learning.models import Result

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