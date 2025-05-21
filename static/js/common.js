// Mobile menu functionality
document.addEventListener('DOMContentLoaded', function() {
  const menu = document.querySelector('#mobile-menu');
  const menuLinks = document.querySelector('.navbar__menu');
  
  // Mobile menu toggle
  if (menu) {
    menu.addEventListener('click', function() {
      menu.classList.toggle('is-active');
      menuLinks.classList.toggle('active');
    });
  }
  
  // Close mobile menu when a link is clicked
  const navLinks = document.querySelectorAll('.navbar__links');
  navLinks.forEach(link => {
    link.addEventListener('click', function() {
      if (menuLinks.classList.contains('active')) {
        menu.classList.remove('is-active');
        menuLinks.classList.remove('active');
      }
    });
  });
}); 