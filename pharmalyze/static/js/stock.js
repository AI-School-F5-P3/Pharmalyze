// static/js/stock.js

document.addEventListener('DOMContentLoaded', function() {
    // Pharmacy type selector
    const pharmacyType = document.getElementById('pharmacy_type');
    const customDaysContainer = document.getElementById('custom_days_container');
    
    if (pharmacyType && customDaysContainer) {
        pharmacyType.addEventListener('change', function() {
            if (this.value === 'libre') {
                customDaysContainer.classList.remove('d-none');
            } else {
                customDaysContainer.classList.add('d-none');
            }
        });
    }

    // Search functionality
    const searchInput = document.getElementById('searchInput');
    const productsTable = document.getElementById('productsTable');
    
    if (searchInput && productsTable) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = productsTable.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
            
            Array.from(rows).forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            const dismissButton = alert.querySelector('.btn-close');
            if (dismissButton) {
                dismissButton.click();
            }
        }, 5000);
    });
});