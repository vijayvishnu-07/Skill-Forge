/**
 * Skill Forge — Course Creator JavaScript
 * Handles module CRUD, video upload with preview, quiz creation,
 * drag-and-drop reordering, and step navigation.
 */

// ─── Module Management ────────────────────────────────────────────
function addModule() {
  const title = prompt('Module title:');
  if (!title) return;

  fetch(`/api/v1/courses/${courseId}/modules/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify({ title: title }),
  })
  .then(r => r.json())
  .then(data => {
    if (data.id) {
      showToast(`Module "${title}" added`, 'success');
      location.reload();
    } else {
      showToast(data.error || 'Failed to add module', 'error');
    }
  })
  .catch(() => showToast('Error adding module', 'error'));
}

function deleteModule(moduleId) {
  if (!confirm('Delete this module and all its lessons?')) return;

  fetch(`/api/v1/courses/${courseId}/modules/${moduleId}/`, {
    method: 'DELETE',
    headers: { 'X-CSRFToken': getCookie('csrftoken') },
  })
  .then(r => {
    if (r.ok) {
      showToast('Module deleted', 'success');
      location.reload();
    } else {
      showToast('Failed to delete module', 'error');
    }
  })
  .catch(() => showToast('Error', 'error'));
}

// ─── Video Lesson ──────────────────────────────────────────────────
function addVideoLesson(moduleId) {
  document.getElementById('videoModuleId').value = moduleId;
  openModal('videoModal');
}

function getVideoDuration(input) {
  if (input.files && input.files[0]) {
    const video = document.createElement('video');
    video.preload = 'metadata';
    video.onloadedmetadata = function() {
      document.getElementById('videoDuration').value = Math.floor(video.duration);
      // Show preview
      const preview = document.getElementById('videoPreview');
      preview.src = URL.createObjectURL(input.files[0]);
      document.getElementById('videoPreviewContainer').style.display = 'block';
      URL.revokeObjectURL(video.src);
    };
    video.src = URL.createObjectURL(input.files[0]);
  }
}

document.getElementById('videoForm')?.addEventListener('submit', function(e) {
  e.preventDefault();
  const formData = new FormData(this);

  showToast('Uploading video...', 'info');

  fetch(`/api/v1/courses/${courseId}/lessons/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken') },
    body: formData,
  })
  .then(r => r.json())
  .then(data => {
    if (data.id) {
      showToast('Video lesson added! 🎬', 'success');
      closeModal('videoModal');
      location.reload();
    } else {
      showToast(data.error || 'Upload failed', 'error');
    }
  })
  .catch(() => showToast('Upload error', 'error'));
});

// ─── Quiz Lesson ───────────────────────────────────────────────────
function addQuizLesson(moduleId) {
  document.getElementById('quizModuleId').value = moduleId;
  openModal('quizModal');
}

document.getElementById('quizForm')?.addEventListener('submit', function(e) {
  e.preventDefault();
  const formData = new FormData(this);
  const data = Object.fromEntries(formData);

  fetch(`/api/v1/courses/${courseId}/lessons/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify(data),
  })
  .then(r => r.json())
  .then(result => {
    if (result.id) {
      showToast('Quiz lesson added! 📝', 'success');
      closeModal('quizModal');
      location.reload();
    } else {
      showToast(result.error || 'Failed', 'error');
    }
  })
  .catch(() => showToast('Error', 'error'));
});

// ─── Delete Lesson ─────────────────────────────────────────────────
function deleteLesson(lessonId) {
  if (!confirm('Delete this lesson?')) return;

  fetch(`/api/v1/courses/${courseId}/lessons/${lessonId}/`, {
    method: 'DELETE',
    headers: { 'X-CSRFToken': getCookie('csrftoken') },
  })
  .then(r => {
    if (r.ok) {
      showToast('Lesson deleted', 'success');
      location.reload();
    } else {
      showToast('Failed to delete lesson', 'error');
    }
  })
  .catch(() => showToast('Error', 'error'));
}
