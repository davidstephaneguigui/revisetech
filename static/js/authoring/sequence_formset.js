document.addEventListener('DOMContentLoaded', function() {
    const addBtn = document.getElementById('add-session-btn');
    const deleteBtn = document.getElementById('delete-session-btn');
    const sortBtn = document.getElementById('sort-session-btn');
    const tableBody = document.getElementById('session-formset-body');
    const totalFormsInput = document.getElementById('id_planned_sessions-TOTAL_FORMS');
    const emptyFormTemplate = document.getElementById('empty-form-template');

    // Fonction utilitaire pour trier le tableau par numéro d'ordre
    function sortTableByOrder() {
        const rows = Array.from(tableBody.querySelectorAll('tr'));
        
        rows.sort((a, b) => {
            const orderInputA = a.querySelector('input[name$="-order"]');
            const orderInputB = b.querySelector('input[name$="-order"]');
            
            const valA = orderInputA ? parseInt(orderInputA.value) || 9999 : 9999;
            const valB = orderInputB ? parseInt(orderInputB.value) || 9999 : 9999;
            
            return valA - valB;
        });
        
        tableBody.innerHTML = '';
        rows.forEach(row => tableBody.appendChild(row));
    }

    // 1. Ajouter une nouvelle ligne
    if (addBtn && tableBody && totalFormsInput && emptyFormTemplate) {
        addBtn.addEventListener('click', function() {
            const formCount = parseInt(totalFormsInput.value);
            let newFormHtml = emptyFormTemplate.innerHTML.replace(/__prefix__/g, formCount);
            
            const tr = document.createElement('tr');
            tr.innerHTML = newFormHtml;
            tableBody.appendChild(tr);
            
            totalFormsInput.value = formCount + 1;

            // --- CALCUL DU PROCHAIN NUMERO ---
            const activeOrders = [];
            tableBody.querySelectorAll('tr').forEach(row => {
                const checkbox = row.querySelector('input[type="checkbox"]');
                if (!(checkbox && checkbox.checked)) {
                    const orderInput = row.querySelector('input[name$="-order"]');
                    if (orderInput) {
                        const val = parseInt(orderInput.value);
                        if (!isNaN(val)) {
                            activeOrders.push(val);
                        }
                    }
                }
            });

            let newOrder = 1;
            while (activeOrders.includes(newOrder)) {
                newOrder++;
            }

            const newOrderInput = tr.querySelector('input[name$="-order"]');
            if (newOrderInput) {
                newOrderInput.value = newOrder;
            }

            const newCheckbox = tr.querySelector('input[type="checkbox"]');
            if (newCheckbox) {
                newCheckbox.classList.add('form-check-input');
            }

            // On trie le tableau immédiatement après l'ajout
            sortTableByOrder();
        });
    }

    // 2. Supprimer les lignes cochées
    if (deleteBtn && tableBody) {
        deleteBtn.addEventListener('click', function() {
            const rows = tableBody.querySelectorAll('tr');
            rows.forEach(row => {
                const checkbox = row.querySelector('input[type="checkbox"]');
                if (checkbox && checkbox.checked) {
                    row.style.display = 'none';
                    const orderInput = row.querySelector('input[name$="-order"]');
                    if (orderInput) orderInput.value = '';
                }
            });
        });
    }

    // 3. Bouton "Trier par numéro"
    if (sortBtn && tableBody) {
        sortBtn.addEventListener('click', function() {
            sortTableByOrder();
        });
    }
});