(function () {
    'use strict';

    const forms = document.querySelectorAll('form');

    forms.forEach((form) => {
        if (!form.querySelector('[required]')) return;

        form.addEventListener('submit', (event) => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
})();