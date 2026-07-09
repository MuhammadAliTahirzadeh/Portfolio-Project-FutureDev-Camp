const body = document.body;
const themeToggle = document.getElementById('themeToggle');
const navToggle = document.getElementById('navToggle');
const navbar = document.querySelector('.navbar');
const navLinks = Array.from(document.querySelectorAll('.nav-links a'));
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
    const targetId = getTargetId(link);
    const isActive = targetId === currentSection;
    link.classList.toggle('active', isActive);
  });
});

const projectForm = document.getElementById('projectForm');
const projectMessage = document.getElementById('projectMessage');
const projectList = document.getElementById('projectList');
const messageList = document.getElementById('messageList');

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
  if (!typingText) {
    return;
  }

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

async function postJson(url, data) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return response.json();
}

async function updateJson(url, data, method = 'PUT') {
  const response = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return response.json();
}

async function deleteJson(url) {
  const response = await fetch(url, { method: 'DELETE' });
  return response.json();
}

function renderProjects(projects) {
  if (!projectList) return;
  projectList.innerHTML = '';
  projects.forEach((project) => {
    const item = document.createElement('li');
    item.innerHTML = `<a href="/project/${project.id}">${project.title}</a>`;
    projectList.appendChild(item);
  });
}

function renderMessages(messages) {
  if (!messageList) return;
  if (!messages.length) {
    messageList.innerHTML = '<p>Henüz mesaj yoxdur.</p>';
    return;
  }

  messageList.innerHTML = messages
    .map(
      (message) => `
      <article class="message-card">
        <strong>${message.name} · ${message.email}</strong>
        <p>${message.message}</p>
        <p><small>Status: ${message.status}</small></p>
        <div class="message-actions">
          <button data-action="update" data-id="${message.id}">Güncelle</button>
          <button data-action="delete" data-id="${message.id}">Sil</button>
        </div>
      </article>
    `
    )
    .join('');
}

async function loadMessages() {
  const response = await fetch('/api/messages');
  const messages = await response.json();
  renderMessages(messages);
}

async function loadProjects() {
  const response = await fetch('/api/projects');
  const projects = await response.json();
  renderProjects(projects);
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
      formMessage.textContent = 'Zəhmət olmasa bütün sahələri doldurun.';
      return;
    }

    if (!emailPattern.test(email)) {
      formMessage.textContent = 'Zəhmət olmasa etibarlı bir email daxil edin.';
      return;
    }

    const result = await postJson('/api/messages', { name, email, message });
    formMessage.className = `form-message ${result.success ? 'success' : 'error'}`;
    formMessage.textContent = result.message || 'İşlem tamamlandı.';
    contactForm.reset();
    loadMessages();
  });
}

if (projectForm) {
  projectForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(projectForm);
    const payload = Object.fromEntries(formData.entries());
    const result = await postJson('/api/projects', payload);
    projectMessage.className = `form-message ${result.success ? 'success' : 'error'}`;
    projectMessage.textContent = result.message || 'İşlem tamamlandı.';
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
    alert(result.message || 'Mesaj silindi.');
    loadMessages();
  }

  if (action === 'update') {
    const updatedText = prompt('Mesajı güncelleyin:', '');
    if (!updatedText) return;
    const result = await updateJson(`/api/messages/${id}`, { message: updatedText, status: 'updated' });
    alert(result.message || 'Mesaj güncellendi.');
    loadMessages();
  }
});

loadProjects();
loadMessages();
