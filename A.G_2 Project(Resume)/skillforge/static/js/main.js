/**
 * Skill Forge — Main JavaScript
 * Global utilities, navigation, search, toasts, and dropdowns
 */

// ─── CSRF Token ────────────────────────────────────────────────────
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// ─── Toast Notifications ───────────────────────────────────────────
function showToast(message, type = 'info', duration = 5000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${icons[type] || 'ℹ️'}</span>
    <span>${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()">×</button>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'slideInRight 0.3s ease-out reverse forwards';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ─── Dropdown Toggle ───────────────────────────────────────────────
function toggleDropdown(id) {
  const dropdown = document.getElementById(id);
  document.querySelectorAll('.dropdown.active').forEach(d => {
    if (d.id !== id) d.classList.remove('active');
  });
  dropdown.classList.toggle('active');
}

// Close dropdowns on outside click
document.addEventListener('click', function(e) {
  if (!e.target.closest('.dropdown')) {
    document.querySelectorAll('.dropdown.active').forEach(d => d.classList.remove('active'));
  }
});

// ─── Global Search ─────────────────────────────────────────────────
const searchInput = document.getElementById('globalSearch');
const searchResults = document.getElementById('searchResults');
let searchTimeout;

if (searchInput) {
  searchInput.addEventListener('input', function() {
    clearTimeout(searchTimeout);
    const query = this.value.trim();
    if (query.length < 2) {
      searchResults.style.display = 'none';
      return;
    }

    searchTimeout = setTimeout(() => {
      fetch(`/api/v1/courses/search/?q=${encodeURIComponent(query)}`)
        .then(r => r.json())
        .then(data => {
          if (data.results && data.results.length > 0) {
            searchResults.innerHTML = data.results.map(c => `
              <a href="/courses/${c.slug}/" class="dropdown-item" style="text-decoration: none;">
                <span>📚</span>
                <div>
                  <div style="font-weight: 600; font-size: 0.85rem;">${c.title}</div>
                  <div style="font-size: 0.75rem; color: var(--text-muted);">${c.instructor || ''}</div>
                </div>
              </a>
            `).join('');
            searchResults.style.display = 'block';
            searchResults.style.opacity = '1';
            searchResults.style.visibility = 'visible';
            searchResults.style.transform = 'translateY(0)';
          } else {
            searchResults.innerHTML = '<div style="padding: 0.75rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">No results found</div>';
            searchResults.style.display = 'block';
            searchResults.style.opacity = '1';
            searchResults.style.visibility = 'visible';
          }
        })
        .catch(() => {
          searchResults.style.display = 'none';
        });
    }, 300);
  });

  searchInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      window.location.href = `/courses/browse/?search=${encodeURIComponent(this.value)}`;
    }
  });

  document.addEventListener('click', function(e) {
    if (!e.target.closest('.navbar-search')) {
      searchResults.style.display = 'none';
    }
  });
}

// ─── Notifications ─────────────────────────────────────────────────
function loadNotifications() {
  fetch('/api/v1/notifications/')
    .then(r => r.json())
    .then(data => {
      const badge = document.getElementById('notifBadge');
      const list = document.getElementById('notifList');
      if (!badge || !list) return;

      const unread = data.results ? data.results.filter(n => !n.is_read) : [];
      if (unread.length > 0) {
        badge.textContent = unread.length;
        badge.classList.remove('hidden');
      } else {
        badge.classList.add('hidden');
      }

      if (data.results && data.results.length > 0) {
        list.innerHTML = data.results.slice(0, 10).map(n => `
          <div class="dropdown-item" onclick="markNotifRead('${n.id}')" style="${n.is_read ? '' : 'background: var(--primary-light);'}">
            <span>${n.notification_type === 'enrollment' ? '📚' : n.notification_type === 'completion' ? '✅' : n.notification_type === 'certificate' ? '🎓' : '🔔'}</span>
            <div>
              <div style="font-size: 0.85rem; font-weight: ${n.is_read ? 400 : 600};">${n.title}</div>
              <div style="font-size: 0.75rem; color: var(--text-muted);">${n.message || ''}</div>
            </div>
          </div>
        `).join('');
      }
    })
    .catch(() => {});
}

function markNotifRead(id) {
  fetch(`/api/v1/notifications/${id}/read/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken') }
  }).then(() => loadNotifications());
}

// Load notifications on page load (if authenticated)
if (document.getElementById('notifBadge')) {
  loadNotifications();
  setInterval(loadNotifications, 30000); // Poll every 30s
}

// ─── Intersection Observer Animations ──────────────────────────────
const observerOptions = { threshold: 0.1, rootMargin: '0px 0px -50px 0px' };
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '';
      entry.target.style.animationPlayState = 'running';
      observer.unobserve(entry.target);
    }
  });
}, observerOptions);

document.querySelectorAll('.animate-fade-in-up, .animate-fade-in, .animate-slide-right').forEach(el => {
  el.style.animationPlayState = 'paused';
  observer.observe(el);
});

// ─── Modal Helpers ─────────────────────────────────────────────────
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

// Close modal on backdrop click
document.querySelectorAll('[id$="Modal"]').forEach(modal => {
  modal.addEventListener('click', function(e) {
    if (e.target === this) closeModal(this.id);
  });
});

// ─── Smooth Scroll ─────────────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

// ─── Form Validation ───────────────────────────────────────────────
document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', function(e) {
    const inputs = this.querySelectorAll('[required]');
    let valid = true;
    inputs.forEach(input => {
      if (!input.value.trim()) {
        input.classList.add('error');
        valid = false;
      } else {
        input.classList.remove('error');
      }
    });
    if (!valid) {
      e.preventDefault();
      showToast('Please fill in all required fields', 'warning');
    }
  });
});

// Remove error class on input
document.querySelectorAll('.form-input').forEach(input => {
  input.addEventListener('input', function() {
    this.classList.remove('error');
  });
});

// ─── Keyboard Shortcuts ────────────────────────────────────────────
document.addEventListener('keydown', function(e) {
  // Cmd/Ctrl + K → Focus search
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    const searchInput = document.getElementById('globalSearch');
    if (searchInput) searchInput.focus();
  }
});

console.log('%c⚡ Skill Forge', 'font-size: 24px; font-weight: 800; color: #2563EB;');
console.log('%cLearn · Create · Grow', 'font-size: 12px; color: #94A3B8;');
