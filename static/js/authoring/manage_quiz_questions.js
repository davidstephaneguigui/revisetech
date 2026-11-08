document.addEventListener('DOMContentLoaded', function() {
    const addBtn = document.getElementById('add-question-btn');
    const container = document.getElementById('questions-container');
    const totalFormsInput = document.getElementById('id_question_set-TOTAL_FORMS'); // Check the actual ID in your HTML
    const emptyFormTemplate = document.getElementById('empty-form-template');

    if (addBtn && container && totalFormsInput && emptyFormTemplate) {
        addBtn.addEventListener('click', function() {
            const formCount = parseInt(totalFormsInput.value);
            let newFormHtml = emptyFormTemplate.innerHTML.replace(/__prefix__/g, formCount);
            
            const div = document.createElement('div');
            div.innerHTML = newFormHtml;
            container.appendChild(div.firstElementChild);
            
            totalFormsInput.value = formCount + 1;
        });
    }
});