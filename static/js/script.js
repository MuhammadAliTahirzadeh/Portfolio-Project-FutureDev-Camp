const body = document.body;
const navbar = document.getElementById('navbar');
const themeToggle = document.getElementById('themeToggle');
const navToggle = document.getElementById('navToggle');
const navLinks = Array.from(document.querySelectorAll('.nav-links a'));
const progressBar = document.getElementById('scrollProgress');
const typingText = document.getElementById('typingText');
const contactForm = document.getElementById('contactForm');
const formMessage = document.getElementById('formMessage');
const submitBtn = document.getElementById('submitBtn');
const footerYear = document.getElementById('footerYear');
const backToTop = document.getElementById('backToTop');
const projectForm = document.getElementById('projectForm');
const projectMessage = document.getElementById('projectMessage');
const projectList = document.getElementById('projectList');
const messageList = document.getElementById('messageList');

const getTargetId = (link) => {
  const href = link.getAttribute('href') || '';
  const hashIndex = href.indexOf('#');
  return hashIndex >= 0 ? href.slice(hashIndex + 1) : '';
};

const sections = navLinks
  .map((link) => {
    const targetId = getTargetId(link);
    return targetId ? document.getElementById(targetId) : null;
  })
  .filter(Boolean);

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
    const targetId = getTargetId(link);
    const target = targetId ? document.getElementById(targetId) : null;

    if (target) {
      event.preventDefault();
      const offset = 100;
      const top = target.getBoundingClientRect().top + window.scrollY - offset;
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
    link.classList.toggle('active', getTargetId(link) === currentSection);
  });
});

const revealItems = document.querySelectorAll('.reveal, .reveal-stagger');
const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);

        if (entry.target.classList.contains('skills-grid') || entry.target.closest('#skills')) {
          animateSkillBars();
        }

        if (entry.target.querySelector('[data-count]')) {
          animateCounters(entry.target);
        }
      }
    });
  },
  { threshold: 0.12 }
);

revealItems.forEach((item) => revealObserver.observe(item));

const skillObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        animateSkillBars();
        skillObserver.disconnect();
      }
    });
  },
  { threshold: 0.2 }
);

const skillsSection = document.getElementById('skills');
if (skillsSection) {
  skillObserver.observe(skillsSection);
}

function animateSkillBars() {
  document.querySelectorAll('.skill-item').forEach((item) => {
    const level = item.dataset.level || '0';
    const fill = item.querySelector('.skill-fill');
    if (fill) {
      fill.style.width = `${level}%`;
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
      const value = Math.floor(progress * target);
      counter.textContent = value;
      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        counter.textContent = target;
      }
    }

    requestAnimationFrame(step);
  });
}

const heroStats = document.querySelector('.hero-stats');
if (heroStats) {
  const statsObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateCounters(entry.target);
          statsObserver.disconnect();
        }
      });
    },
    { threshold: 0.5 }
  );
  statsObserver.observe(heroStats);
}

const words = ['Developer', 'AI Enthusiast', 'Problem Solver'];
let wordIndex = 0;
let charIndex = 0;
let isDeleting = false;

function typeLoop() {
  if (!typingText) return;

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

  setTimeout(typeLoop, isDeleting ? 80 : 120);
}

typeLoop();

function getAdminToken() {
  return localStorage.getItem('admin-token') || '';
}

function isAdmin() {
  return Boolean(getAdminToken());
}

function adminHeaders() {
  const token = getAdminToken();
  return token ? { 'X-Admin-Token': token } : {};
}

async function postJson(url, data) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...adminHeaders() },
    body: JSON.stringify(data),
  });
  return response.json();
}

async function updateJson(url, data, method = 'PUT') {
  const response = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json', ...adminHeaders() },
    body: JSON.stringify(data),
  });
  return response.json();
}

async function deleteJson(url) {
  const response = await fetch(url, { method: 'DELETE', headers: adminHeaders() });
  return response.json();
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function renderProjects(projects) {
  if (!projectList) return;

  if (!projects.length) {
    projectList.innerHTML = '<div class="empty-state">No projects yet. Add your first project below.</div>';
    return;
  }

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
}

function renderMessages(messages) {
  if (!messageList) return;

  if (!messages.length) {
    messageList.innerHTML = '<div class="empty-state">No messages yet.</div>';
    return;
  }

  messageList.innerHTML = messages
    .map(
      (message) => `
      <article class="message-card">
        <strong>${escapeHtml(message.name)} · ${escapeHtml(message.email)}</strong>
        <p>${escapeHtml(message.message)}</p>
        <p><small>Status: ${escapeHtml(message.status)}</small></p>
        <div class="message-actions">
          <button data-action="update" data-id="${message.id}">Update</button>
          <button data-action="delete" data-id="${message.id}">Delete</button>
        </div>
      </article>
    `
    )
    .join('');
}

async function loadMessages() {
  if (!messageList || !isAdmin()) return;

  try {
    const response = await fetch('/api/messages', { headers: adminHeaders() });
    if (!response.ok) {
      messageList.innerHTML = '<div class="empty-state">Unauthorized. Set a valid admin token to view messages.</div>';
      return;
    }
    const messages = await response.json();
    renderMessages(messages);
  } catch {
    messageList.innerHTML = '<div class="empty-state">Unable to load messages.</div>';
  }
}

async function loadProjects() {
  try {
    const response = await fetch('/api/projects');
    const projects = await response.json();
    renderProjects(projects);
  } catch {
    /* Server-side rendered projects remain visible */
  }
}

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
      const result = await postJson('/api/messages', { name, email, message });
      formMessage.className = `form-message ${result.success ? 'success' : 'error'}`;
      formMessage.textContent = result.message || 'Request completed.';
      if (result.success) {
        contactForm.reset();
        loadMessages();
      }
    } catch {
      formMessage.className = 'form-message error';
      formMessage.textContent = 'Failed to send message. Please try again later.';
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Send Message';
      }
    }
  });
}

if (projectForm) {
  projectForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(projectForm);
    const payload = Object.fromEntries(formData.entries());

    const result = await postJson('/api/projects', payload);
    projectMessage.className = `form-message ${result.success ? 'success' : 'error'}`;
    projectMessage.textContent = result.message || 'Request completed.';
    projectForm.reset();
    loadProjects();
  });
}

messageList?.addEventListener('click', async (event) => {
  const button = event.target.closest('button');
  if (!button) return;

  const id = button.dataset.id;
  const action = button.dataset.action;

  if (action === 'delete') {
    const result = await deleteJson(`/api/messages/${id}`);
    alert(result.message || 'Message deleted.');
    loadMessages();
  }

  if (action === 'update') {
    const updatedText = prompt('Update message:', '');
    if (!updatedText) return;
    const result = await updateJson(`/api/messages/${id}`, { message: updatedText, status: 'updated' });
    alert(result.message || 'Message updated.');
    loadMessages();
  }
});

function applyAdminVisibility() {
  const adminSections = document.querySelectorAll('.admin-panel, #messages');
  adminSections.forEach((section) => {
    section.hidden = !isAdmin();
  });
}

applyAdminVisibility();
loadProjects();
loadMessages();
