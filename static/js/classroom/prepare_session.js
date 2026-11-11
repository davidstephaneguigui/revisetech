document.addEventListener("DOMContentLoaded", function() {
    const toggleSwitches = document.querySelectorAll('.toggle-activity-btn');
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    
    toggleSwitches.forEach(switchBtn => {
        switchBtn.addEventListener('change', function() {
            const classId = this.dataset.class;
            const activityId = this.dataset.activity;
            
            fetch(`/class/${classId}/activity/${activityId}/toggle-usage/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                // On peut ajouter une animation ou un feedback visuel ici si besoin
                console.log(`Activité ${activityId} utilisée : ${data.is_used}`);
            })
            .catch(error => console.error('Erreur:', error));
        });
    });
});