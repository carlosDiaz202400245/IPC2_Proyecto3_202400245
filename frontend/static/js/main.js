// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Confirmación para acciones peligrosas
    const dangerousButtons = document.querySelectorAll('.btn-danger[onclick*="confirm"]');
    dangerousButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('¿Está seguro de que desea realizar esta acción?')) {
                e.preventDefault();
            }
        });
    });

    // Validación de fechas
    const fechaInicio = document.getElementById('fecha_inicio');
    const fechaFin = document.getElementById('fecha_fin');
    
    if (fechaInicio && fechaFin) {
        // Establecer fecha mínima como hoy
        const today = new Date().toISOString().split('T')[0];
        fechaInicio.min = today;
        fechaFin.min = today;

        fechaInicio.addEventListener('change', function() {
            fechaFin.min = this.value;
        });
        
        fechaFin.addEventListener('change', function() {
            if (fechaInicio.value && this.value < fechaInicio.value) {
                alert('La fecha fin no puede ser anterior a la fecha inicio');
                this.value = '';
            }
        });
    }

    // Validación de NIT
    const nitInputs = document.querySelectorAll('input[pattern="\\d+-[\\dK]"]');
    nitInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const nitPattern = /^\d+-[\dK]$/;
            if (this.value && !nitPattern.test(this.value)) {
                this.setCustomValidity('Formato de NIT inválido. Use: 12345-6 o 12345678-K');
                this.reportValidity();
            } else {
                this.setCustomValidity('');
            }
        });
    });

    // Auto-submit en selects de filtro
    const autoSubmitSelects = document.querySelectorAll('select[onchange*="submit"]');
    autoSubmitSelects.forEach(select => {
        select.addEventListener('change', function() {
            this.form.submit();
        });
    });

    /*
const submitButtons = document.querySelectorAll('button[type="submit"], input[type="submit"]');
submitButtons.forEach(button => {
    button.addEventListener('click', function() {
        if (this.form.checkValidity()) {
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...';
            this.disabled = true;
        }
    });
});
*/

    // Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Animación para alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        
        setTimeout(() => {
            alert.style.transition = 'all 0.3s ease';
            alert.style.opacity = '1';
            alert.style.transform = 'translateY(0)';
        }, 100);
    });

    // Auto-ocultar alerts después de 5 segundos
    setTimeout(() => {
        alerts.forEach(alert => {
            if (alert.classList.contains('alert-dismissible')) {
                const closeButton = alert.querySelector('.btn-close');
                if (closeButton) {
                    closeButton.click();
                }
            }
        });
    }, 5000);

    // Mejorar experiencia en formularios
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = this.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('Por favor, complete todos los campos requeridos.');
            }
        });
    });

    // Remover clases de validación al escribir
    const formInputs = document.querySelectorAll('input, select, textarea');
    formInputs.forEach(input => {
        input.addEventListener('input', function() {
            this.classList.remove('is-invalid');
        });
    });
});

// Funciones globales
function formatCurrency(amount) {
    return 'Q' + parseFloat(amount).toFixed(2);
}

function showLoading() {
    const loader = document.createElement('div');
    loader.className = 'loading-overlay';
    loader.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Cargando...</span>
        </div>
    `;
    document.body.appendChild(loader);
}

function hideLoading() {
    const loader = document.querySelector('.loading-overlay');
    if (loader) {
        loader.remove();
    }
}