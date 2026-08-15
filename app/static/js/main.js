// Client-side JavaScript for Medical Appointment Manager
document.addEventListener('DOMContentLoaded', () => {
    console.log('MedCare Manager JavaScript initialized.');
    
    // Auto-dismiss alert messages after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach((alert) => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });
});
