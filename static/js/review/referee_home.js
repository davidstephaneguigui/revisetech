document.addEventListener('DOMContentLoaded', function() {
    // If the URL contains a hash (e.g., #collapseContent5), open that accordion
    if (window.location.hash) {
        const target = document.querySelector(window.location.hash);
        if (target) {
            // Bootstrap 5 command to show the collapse
            const collapse = bootstrap.Collapse.getOrCreateInstance(target);
            collapse.show();
        }
    }
});