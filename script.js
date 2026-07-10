const body = document.body;
const themeToggle = document.getElementById('themeToggle');
const navToggle = document.getElementById('navToggle');
const navbar = document.querySelector('.navbar');
const navLinks = Array.from(document.querySelectorAll('.nav-links a'));
const sections = navLinks
  .map((link) => document.querySelector(link.getAttribute('href')))
  .filter(Boolean);
const progressBar = document.getElementById('scrollProgress');
const typingText = document.getElementById('typingText');
const contactForm = document.getElementById('contactForm');
const formMessage = document.getElementById('formMessage');

const savedTheme = localStorage.getItem('portfolio-theme');
if (savedTheme === 'dark') {
  body.classList.add('dark');
}

function updateThemeButton() {
  const isDark = body.classList.contains('dark');
  themeToggle.textContent = isDark ? '☀️' : '🌙';
  themeToggle.setAttribute('aria-label', isDark ? 'Switch to light theme' : 'Switch to dark theme');
}

updateThemeButton();

themeToggle.addEventListener('click', () => {
  body.classList.toggle('dark');
  const isDark = body.classList.contains('dark');
  localStorage.setItem('portfolio-theme', isDark ? 'dark' : 'light');
  updateThemeButton();
});

navToggle.addEventListener('click', () => {
  navbar.classList.toggle('open');
});

navLinks.forEach((link) => {
  link.addEventListener('click', () => {
    navbar.classList.remove('open');
  });
});

window.addEventListener('scroll', () => {
  const scrollTop = window.scrollY;
  const height = document.documentElement.scrollHeight - window.innerHeight;
  const progress = height > 0 ? scrollTop / height : 0;
  progressBar.style.transform = `scaleX(${progress})`;

  let currentSection = sections[0]?.id || '';

  sections.forEach((section) => {
    if (scrollTop + 180 >= section.offsetTop) {
      currentSection = section.id;
    }
  });

  navLinks.forEach((link) => {
    const isActive = link.getAttribute('href') === `#${currentSection}`;
    link.classList.toggle('active', isActive);
  });
});

const revealItems = document.querySelectorAll('.reveal');
const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.12 }
);

revealItems.forEach((item) => revealObserver.observe(item));

const words = ['Developer', 'AI Enthusiast', 'Problem Solver'];
let wordIndex = 0;
let charIndex = 0;
let isDeleting = false;

function typeLoop() {
  const currentWord = words[wordIndex];
  typingText.textContent = currentWord.slice(0, charIndex);

  if (!isDeleting && charIndex < currentWord.length) {
    charIndex += 1;
  } else if (isDeleting && charIndex > 0) {
    charIndex -= 1;
  } else {
    isDeleting = !isDeleting;
    if (!isDeleting) {
      wordIndex = (wordIndex + 1) % words.length;
    }
  }

  const speed = isDeleting ? 80 : 120;
  setTimeout(typeLoop, speed);
}

typeLoop();

contactForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const name = contactForm.querySelector('input[type="text"]').value.trim();
  const email = contactForm.querySelector('input[type="email"]').value.trim();
  const message = contactForm.querySelector('textarea').value.trim();
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  formMessage.className = 'form-message error';

  if (!name || !email || !message) {
    formMessage.textContent = 'Zəhmət olmasa bütün sahələri doldurun.';
    return;
  }

  if (!emailPattern.test(email)) {
    formMessage.textContent = 'Zəhmət olmasa etibarlı bir email daxil edin.';
    return;
  }

  try {
    const response = await fetch('/api/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, message }),
    });
    const result = await response.json();

    formMessage.className = `form-message ${result.success ? 'success' : 'error'}`;
    formMessage.textContent = result.message || 'İşlem tamamlandı.';
    if (result.success) {
      contactForm.reset();
    }
  } catch (error) {
    formMessage.className = 'form-message error';
    formMessage.textContent = 'Mesaj göndərilmədi. Sonra yenidən cəhd edin.';
  }
});
