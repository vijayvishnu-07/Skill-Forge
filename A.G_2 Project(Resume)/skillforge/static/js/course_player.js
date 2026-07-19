/**
 * Skill Forge — Course Video Player
 * Custom HTML5 video player with progress tracking, keyboard shortcuts,
 * playback speed, PiP, fullscreen, and auto-save position.
 */

let player, progressBar, progressFill, timeDisplay, playPauseBtn;
let currentLessonId, courseSlug;
let saveInterval;

function initPlayer(savedPosition, lessonId, slug) {
  player = document.getElementById('videoPlayer');
  progressBar = document.getElementById('progressBar');
  progressFill = document.getElementById('progressFill');
  timeDisplay = document.getElementById('timeDisplay');
  playPauseBtn = document.getElementById('playPauseBtn');
  currentLessonId = lessonId;
  courseSlug = slug;

  if (!player) return;

  // Set saved position
  player.addEventListener('loadedmetadata', () => {
    if (savedPosition > 0 && savedPosition < player.duration - 5) {
      player.currentTime = savedPosition;
    }
    updateTimeDisplay();
  });

  // Play/Pause
  player.addEventListener('play', () => { playPauseBtn.textContent = '⏸️'; });
  player.addEventListener('pause', () => { playPauseBtn.textContent = '▶️'; });

  playPauseBtn.addEventListener('click', togglePlayPause);

  // Progress bar
  player.addEventListener('timeupdate', () => {
    if (player.duration) {
      const pct = (player.currentTime / player.duration) * 100;
      progressFill.style.width = pct + '%';
      updateTimeDisplay();
    }
  });

  // Click on progress bar to seek
  progressBar.addEventListener('click', (e) => {
    const rect = progressBar.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    player.currentTime = pct * player.duration;
  });

  // Speed selector
  document.getElementById('speedSelector').addEventListener('change', function () {
    player.playbackRate = parseFloat(this.value);
  });

  // PiP
  document.getElementById('pipBtn').addEventListener('click', async () => {
    try {
      if (document.pictureInPictureElement) {
        await document.exitPictureInPicture();
      } else {
        await player.requestPictureInPicture();
      }
    } catch (err) {
      showToast('Picture-in-Picture not supported', 'warning');
    }
  });

  // Fullscreen
  document.getElementById('fullscreenBtn').addEventListener('click', () => {
    const container = document.getElementById('videoContainer');
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      container.requestFullscreen().catch(() => { });
    }
  });

  // Video ended → auto-complete
  player.addEventListener('ended', () => {
    markComplete(currentLessonId);
    saveProgress(currentLessonId, player.duration, true);
  });

  // Auto-save progress every 15 seconds
  saveInterval = setInterval(() => {
    if (!player.paused && player.currentTime > 0) {
      saveProgress(currentLessonId, player.currentTime, false);
    }
  }, 15000);

  // Keyboard shortcuts
  document.addEventListener('keydown', handlePlayerKeyboard);
}

function togglePlayPause() {
  if (!player) return;
  if (player.paused) player.play();
  else player.pause();
}

function updateTimeDisplay() {
  if (!player || !timeDisplay) return;
  timeDisplay.textContent = `${formatTime(player.currentTime)} / ${formatTime(player.duration || 0)}`;
}

function formatTime(seconds) {
  if (isNaN(seconds)) return '0:00';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function handlePlayerKeyboard(e) {
  // Don't capture when typing in inputs
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;

  switch (e.key) {
    case ' ':
    case 'k':
      e.preventDefault();
      togglePlayPause();
      break;
    case 'ArrowLeft':
      e.preventDefault();
      player.currentTime = Math.max(0, player.currentTime - 10);
      break;
    case 'ArrowRight':
      e.preventDefault();
      player.currentTime = Math.min(player.duration, player.currentTime + 10);
      break;
    case 'ArrowUp':
      e.preventDefault();
      player.volume = Math.min(1, player.volume + 0.1);
      break;
    case 'ArrowDown':
      e.preventDefault();
      player.volume = Math.max(0, player.volume - 0.1);
      break;
    case 'f':
      e.preventDefault();
      document.getElementById('fullscreenBtn').click();
      break;
    case 'm':
      e.preventDefault();
      player.muted = !player.muted;
      break;
    case ',':
      if (e.shiftKey) { // < key
        e.preventDefault();
        const speedSel = document.getElementById('speedSelector');
        const idx = speedSel.selectedIndex;
        if (idx > 0) {
          speedSel.selectedIndex = idx - 1;
          player.playbackRate = parseFloat(speedSel.value);
        }
      }
      break;
    case '.':
      if (e.shiftKey) { // > key
        e.preventDefault();
        const speedSel = document.getElementById('speedSelector');
        const idx = speedSel.selectedIndex;
        if (idx < speedSel.options.length - 1) {
          speedSel.selectedIndex = idx + 1;
          player.playbackRate = parseFloat(speedSel.value);
        }
      }
      break;
  }
}

// ─── Progress Tracking ─────────────────────────────────────────────
function saveProgress(lessonId, position, completed) {
  fetch('/api/v1/courses/progress/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify({
      lesson_id: lessonId,
      last_position: Math.floor(position),
      completed: completed,
    }),
  }).catch(() => { });
}

function markComplete(lessonId) {
  fetch('/api/v1/courses/progress/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify({
      lesson_id: lessonId,
      completed: true,
    }),
  })
    .then(r => r.json())
    .then(data => {
      const btn = document.getElementById('completeBtn');
      if (btn) { btn.textContent = '✅ Completed!'; btn.disabled = true; }
      // Update sidebar progress
      if (data.course_progress) {
        const courseProgress = document.getElementById('courseProgress');
        if (courseProgress) courseProgress.style.width = data.course_progress + '%';
      }
      showToast('Lesson marked as complete! ✅', 'success');
    })
    .catch(() => showToast('Failed to save progress', 'error'));
}

function toggleBookmark(lessonId) {
  fetch('/api/v1/courses/bookmark/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify({ lesson_id: lessonId }),
  })
    .then(r => r.json())
    .then(data => {
      const btn = document.getElementById('bookmarkBtn');
      if (data.bookmarked) {
        btn.textContent = '🔖 Bookmarked';
        showToast('Lesson bookmarked', 'success');
      } else {
        btn.textContent = '🔖 Bookmark';
        showToast('Bookmark removed', 'info');
      }
    })
    .catch(() => showToast('Error', 'error'));
}

// Cleanup on page leave
window.addEventListener('beforeunload', () => {
  if (saveInterval) clearInterval(saveInterval);
  if (player && currentLessonId && !player.paused) {
    saveProgress(currentLessonId, player.currentTime, false);
  }
});
