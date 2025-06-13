document.addEventListener('DOMContentLoaded', function() {
  // Mobile menu functionality
  const initMobileMenu = () => {
    const mobileMenuButton = document.querySelector('.navbar__toggle');
    const navbarMenu = document.querySelector('.navbar__menu');
    const navbar = document.querySelector('.navbar');
    
    if (!mobileMenuButton || !navbarMenu) return;

    const toggleMenu = () => {
      mobileMenuButton.classList.toggle('active');
      navbarMenu.classList.toggle('active');
      document.body.style.overflow = navbarMenu.classList.contains('active') ? 'hidden' : '';
    };

    mobileMenuButton.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleMenu();
    });

    // Close menu when clicking on links (mobile only)
    document.querySelectorAll('.navbar__menu a').forEach(link => {
      link.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
          toggleMenu();
        }
      });
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (navbarMenu.classList.contains('active') && 
          !navbar.contains(e.target)) {
        toggleMenu();
      }
    });
  };

  initMobileMenu();
});