document.addEventListener("DOMContentLoaded", function() {
    const toggleButtons = document.querySelectorAll('.toggle-session-btn');
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const classId = this.dataset.class;
            const sessionId = this.dataset.session;
            
            fetch(`/class/${classId}/session/${sessionId}/toggle/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.is_completed) {
                    this.classList.remove('btn-outline-secondary');
                    this.classList.add('btn-success');
                    this.innerHTML = '<i class="bi bi-check-circle-fill"></i> Réalisée';
                } else {
                    this.classList.remove('btn-success');
                    this.classList.add('btn-outline-secondary');
                    this.innerHTML = '<i class="bi bi-circle"></i> À faire';
                }
            })
            .catch(error => console.error('Erreur:', error));
        });
    });
});