document.addEventListener("DOMContentLoaded", function() {
    const toggleSwitches = document.querySelectorAll('.toggle-activity-btn');
    const toggleHideBtn = document.getElementById('toggle-hide-btn');
    const activityRows = document.querySelectorAll('.activity-row');
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    
    let isHiding = false;

    // Fonction pour filtrer l'affichage
    function updateVisibility() {
        activityRows.forEach(row => {
            const isActive = row.dataset.isActive === 'true';
            if (isHiding && !isActive) {
                row.classList.add('d-none');
            } else {
                row.classList.remove('d-none');
            }
        });
    }

    // Gestion du bouton "Masquer"
    if (toggleHideBtn) {
        toggleHideBtn.addEventListener('click', function() {
            isHiding = !isHiding;
            if (isHiding) {
                this.classList.replace('btn-outline-secondary', 'btn-secondary');
                this.innerHTML = '<i class="bi bi-eye"></i> Afficher toutes';
            } else {
                this.classList.replace('btn-secondary', 'btn-outline-secondary');
                this.innerHTML = '<i class="bi bi-eye-slash"></i> Masquer inactives';
            }
            updateVisibility();
        });
    }

    // Gestion des switchs d'activation
    toggleSwitches.forEach(switchBtn => {
        switchBtn.addEventListener('change', function() {
            const classId = this.dataset.class;
            const activityId = this.dataset.activity;
            const row = this.closest('.activity-row');
            
            fetch(`/class/${classId}/activity/${activityId}/toggle-usage/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                row.dataset.isActive = data.is_used ? 'true' : 'false';
                updateVisibility(); // Mettre à jour le filtre si on désactive une activité
            })
            .catch(error => console.error('Erreur:', error));
        });
    });
});