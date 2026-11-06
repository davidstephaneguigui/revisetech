document.addEventListener('DOMContentLoaded', function() {
    const addBtn = document.getElementById('add-session-btn');
    const deleteBtn = document.getElementById('delete-session-btn');
    const sortBtn = document.getElementById('sort-session-btn');
    const tableBody = document.getElementById('session-formset-body');
    const totalFormsInput = document.getElementById('id_planned_sessions-TOTAL_FORMS');
    const emptyFormTemplate = document.getElementById('empty-form-template');

    // 1. Add a new row
    if (addBtn && tableBody && totalFormsInput && emptyFormTemplate) {
        addBtn.addEventListener('click', function() {
            const formCount = parseInt(totalFormsInput.value);
            let newFormHtml = emptyFormTemplate.innerHTML.replace(/__prefix__/g, formCount);
            
            const tr = document.createElement('tr');
            tr.innerHTML = newFormHtml;
            tableBody.appendChild(tr);
            
            totalFormsInput.value = formCount + 1;

            const newCheckbox = tr.querySelector('input[type="checkbox"]');
            if (newCheckbox) {
                newCheckbox.classList.add('form-check-input');
            }
        });
    }

    // 2. Delete checked rows
    if (deleteBtn && tableBody) {
        deleteBtn.addEventListener('click', function() {
            const rows = tableBody.querySelectorAll('tr');
            rows.forEach(row => {
                const checkbox = row.querySelector('input[type="checkbox"]');
                if (checkbox && checkbox.checked) {
                    row.style.display = 'none'; // Hide visually
                    // Do not remove from DOM, let Django Formset handle deletion via the checked box
                }
            });
        });
    }

    // 3. Sort rows by order
    if (sortBtn && tableBody) {
        sortBtn.addEventListener('click', function() {
            // Get all rows, even hidden ones
            const rows = Array.from(tableBody.querySelectorAll('tr'));
            
            rows.sort((a, b) => {
                const orderInputA = a.querySelector('input[name$="-order"]');
                const orderInputB = b.querySelector('input[name$="-order"]');
                
                const valA = orderInputA ? parseInt(orderInputA.value) || 0 : 0;
                const valB = orderInputB ? parseInt(orderInputB.value) || 0 : 0;
                
                return valA - valB;
            });
            
            // Re-append rows in the sorted order
            tableBody.innerHTML = '';
            rows.forEach(row => tableBody.appendChild(row));
        });
    }
});