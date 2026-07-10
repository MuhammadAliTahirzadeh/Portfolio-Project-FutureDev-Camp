const body = document.body;
const navbar = document.getElementById('navbar');
const themeToggle = document.getElementById('themeToggle');
const navToggle = document.getElementById('navToggle');
const navLinks = Array.from(document.querySelectorAll('.nav-links a'));
const sections = navLinks
  .map((link) => document.querySelector(link.getAttribute('href')))
  .filter(Boolean);
const progressBar = document.getElementById('scrollProgress');
const typingText = document.getElementById('typingText');
const contactForm = document.getElementById('contactForm');
const formMessage = document.getElementById('formMessage');
const submitBtn = document.getElementById('submitBtn');
const footerYear = document.getElementById('footerYear');
const backToTop = document.getElementById('backToTop');
const projectList = document.getElementById('projectList');

if (footerYear) {
  footerYear.textContent = new Date().getFullYear();
}

const savedTheme = localStorage.getItem('portfolio-theme');
if (savedTheme === 'dark') {
  body.classList.add('dark');
}

function updateThemeButton() {
  if (!themeToggle) return;
  const isDark = body.classList.contains('dark');
  themeToggle.textContent = isDark ? '☀️' : '🌙';
  themeToggle.setAttribute('aria-label', isDark ? 'Switch to light theme' : 'Switch to dark theme');
}

updateThemeButton();

themeToggle?.addEventListener('click', () => {
  body.classList.toggle('dark');
  localStorage.setItem('portfolio-theme', body.classList.contains('dark') ? 'dark' : 'light');
  updateThemeButton();
});

navToggle?.addEventListener('click', () => {
  navbar?.classList.toggle('open');
});

navLinks.forEach((link) => {
  link.addEventListener('click', (event) => {
    const target = document.querySelector(link.getAttribute('href'));
    if (target) {
      event.preventDefault();
      const top = target.getBoundingClientRect().top + window.scrollY - 100;
      window.scrollTo({ top, behavior: 'smooth' });
    }
    navbar?.classList.remove('open');
  });
});

backToTop?.addEventListener('click', () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

window.addEventListener('scroll', () => {
  const scrollTop = window.scrollY;
  const height = document.documentElement.scrollHeight - window.innerHeight;
  const progress = height > 0 ? scrollTop / height : 0;

  if (progressBar) {
    progressBar.style.transform = `scaleX(${progress})`;
  }

  navbar?.classList.toggle('scrolled', scrollTop > 40);
  backToTop?.classList.toggle('visible', scrollTop > 400);

  let currentSection = sections[0]?.id || '';
  sections.forEach((section) => {
    if (scrollTop + 180 >= section.offsetTop) {
      currentSection = section.id;
    }
  });

  navLinks.forEach((link) => {
    link.classList.toggle('active', link.getAttribute('href') === `#${currentSection}`);
  });
});

const revealItems = document.querySelectorAll('.reveal, .reveal-stagger');
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

function animateSkillBars() {
  document.querySelectorAll('.skill-item').forEach((item) => {
    const fill = item.querySelector('.skill-fill');
    if (fill) {
      fill.style.width = `${item.dataset.level || 0}%`;
    }
  });
}

function animateCounters(container) {
  container.querySelectorAll('[data-count]').forEach((counter) => {
    const target = Number(counter.dataset.count);
    const duration = 1200;
    const start = performance.now();

    function step(now) {
      const progress = Math.min((now - start) / duration, 1);
      counter.textContent = Math.floor(progress * target);
      if (progress < 1) requestAnimationFrame(step);
      else counter.textContent = target;
    }

    requestAnimationFrame(step);
  });
}

const skillsSection = document.getElementById('skills');
if (skillsSection) {
  new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) {
        animateSkillBars();
      }
    },
    { threshold: 0.2 }
  ).observe(skillsSection);
}

const heroStats = document.querySelector('.hero-stats');
if (heroStats) {
  new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) {
        animateCounters(entries[0].target);
      }
    },
    { threshold: 0.5 }
  ).observe(heroStats);
}

const words = ['Developer', 'AI Enthusiast', 'Problem Solver'];
let wordIndex = 0;
let charIndex = 0;
let isDeleting = false;

function typeLoop() {
  if (!typingText) return;
  const currentWord = words[wordIndex];
  typingText.textContent = currentWord.slice(0, charIndex);

  if (!isDeleting && charIndex < currentWord.length) charIndex += 1;
  else if (isDeleting && charIndex > 0) charIndex -= 1;
  else {
    isDeleting = !isDeleting;
    if (!isDeleting) wordIndex = (wordIndex + 1) % words.length;
  }

  setTimeout(typeLoop, isDeleting ? 80 : 120);
}

typeLoop();

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

async function loadProjects() {
  if (!projectList) return;

  try {
    const response = await fetch('/api/projects');
    if (!response.ok) {
      throw new Error(`Failed to load projects: ${response.status} ${response.statusText}`);
    }
    const projects = await response.json();
    if (!projects.length) return;

    projectList.innerHTML = projects
      .map(
        (project) => `
        <a class="project-card" href="/project/${project.id}">
          <div class="project-icon">${escapeHtml(project.title.charAt(0))}</div>
          <h3>${escapeHtml(project.title)}</h3>
          <p>${escapeHtml(project.summary)}</p>
          <span class="project-link">View details →</span>
        </a>
      `
      )
      .join('');
  } catch (error) {
    console.error('Could not load projects, keeping static fallback cards.', error);
  }
}

loadProjects();

if (contactForm) {
  contactForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const name = contactForm.querySelector('input[type="text"]').value.trim();
    const email = contactForm.querySelector('input[type="email"]').value.trim();
    const message = contactForm.querySelector('textarea').value.trim();
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    formMessage.className = 'form-message error';

    if (!name || !email || !message) {
      formMessage.textContent = 'Please fill in all fields.';
      return;
    }

    if (!emailPattern.test(email)) {
      formMessage.textContent = 'Please enter a valid email address.';
      return;
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Sending...';
    }

    try {
      const response = await fetch('/api/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, message }),
      });
      const result = await response.json();

      formMessage.className = `form-message ${result.success ? 'success' : 'error'}`;
      formMessage.textContent = result.message || 'Request completed.';
      if (result.success) contactForm.reset();
    } catch (error) {
      console.error('Failed to submit contact form.', error);
      formMessage.className = 'form-message error';
      formMessage.textContent = 'Failed to send message. Run the Flask server or try again later.';
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Send Message';
      }
    }
  });
}
