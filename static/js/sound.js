// Sound effects for UI interactions
const clickSound = new Audio('/static/sounds/click.mp3');
const hoverSound = new Audio('/static/sounds/hover.mp3');

// Function to play click sound
function playClickSound() {
    clickSound.currentTime = 0; // Reset sound to start
    clickSound.play();
}

// Function to play hover sound
function playHoverSound() {
    hoverSound.currentTime = 0;
    hoverSound.play();
}

// Add click sound to all buttons
document.addEventListener('DOMContentLoaded', function() {
    // Expanded selector to include all button-like elements
    const buttons = document.querySelectorAll('button, .button, .action-btn, .create-btn, .search-btn, .upload-btn, .save-btn, .primary-btn, .secondary-btn, .danger-btn, .add-btn, .remove-tag, .hero-btn, a[href], input[type="submit"], .interest-btn, .tab, .navbar__links, #navbar__logo');
    
    buttons.forEach(button => {
        // Add click sound
        button.addEventListener('click', playClickSound);
        
        // Add hover sound
        button.addEventListener('mouseenter', playHoverSound);
    });
    
    // Also add sound to dynamically created elements using event delegation
    document.body.addEventListener('click', function(e) {
        if (e.target.tagName === 'BUTTON' || 
            e.target.tagName === 'A' || 
            e.target.classList.contains('button') ||
            e.target.classList.contains('btn') ||
            e.target.getAttribute('role') === 'button') {
            playClickSound();
        }
    });
    
    document.body.addEventListener('mouseenter', function(e) {
        if (e.target.tagName === 'BUTTON' || 
            e.target.tagName === 'A' || 
            e.target.classList.contains('button') ||
            e.target.classList.contains('btn') ||
            e.target.getAttribute('role') === 'button') {
            playHoverSound();
        }
    }, true);
}); 