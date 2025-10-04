// Simple JavaScript to demonstrate container runtime
document.addEventListener('DOMContentLoaded', function() {
    // Display current time (shows container is running)
    const buildTimeElement = document.getElementById('build-time');
    if (buildTimeElement) {
        buildTimeElement.textContent = new Date().toLocaleString();
    }

    // Add interactive hover effects
    const cards = document.querySelectorAll('.info-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.transition = 'transform 0.3s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    console.log('🐳 Docker container is running!');
    console.log('Container started at:', new Date().toISOString());
});
