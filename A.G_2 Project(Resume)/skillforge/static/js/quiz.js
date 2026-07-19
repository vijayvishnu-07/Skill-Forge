/**
 * Skill Forge — Quiz Interface
 * Interactive quiz player with question navigation, scoring,
 * immediate feedback, explanations, and result submission.
 */

let quizData = null;
let currentQuestion = 0;
let answers = {};

function loadQuiz(quizId) {
  const container = document.getElementById('quizContent');
  container.innerHTML = '<div class="flex-center" style="padding: 2rem;">Loading quiz...</div>';

  fetch(`/api/v1/quizzes/${quizId}/`)
    .then(r => r.json())
    .then(data => {
      quizData = data;
      currentQuestion = 0;
      answers = {};
      renderQuestion();
    })
    .catch(() => {
      container.innerHTML = '<div class="empty-state"><div class="icon">❌</div><h3>Failed to load quiz</h3></div>';
    });
}

function renderQuestion() {
  if (!quizData || !quizData.questions) return;
  const container = document.getElementById('quizContent');
  const q = quizData.questions[currentQuestion];
  const total = quizData.questions.length;

  // Progress dots
  let progressHTML = '<div class="quiz-progress">';
  for (let i = 0; i < total; i++) {
    let cls = 'quiz-progress-dot';
    if (i === currentQuestion) cls += ' active';
    if (answers[i] !== undefined) cls += ' answered';
    progressHTML += `<div class="${cls}"></div>`;
  }
  progressHTML += '</div>';

  // Question
  let html = progressHTML;
  html += `<div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.75rem;">Question ${currentQuestion + 1} of ${total}</div>`;
  html += `<div class="quiz-question">${q.text}</div>`;

  // Options
  const labels = ['A', 'B', 'C', 'D', 'E', 'F'];
  q.options.forEach((opt, i) => {
    const selected = answers[currentQuestion] === i;
    html += `
      <div class="quiz-option ${selected ? 'selected' : ''}" onclick="selectOption(${i})" data-option="${i}">
        <div class="quiz-option-label">${labels[i]}</div>
        <span>${opt.text}</span>
      </div>
    `;
  });

  // Navigation
  html += '<div class="quiz-nav">';
  html += currentQuestion > 0
    ? `<button class="btn btn-ghost" onclick="prevQuestion()">← Previous</button>`
    : '<div></div>';
  html += currentQuestion < total - 1
    ? `<button class="btn btn-primary" onclick="nextQuestion()">Next →</button>`
    : `<button class="btn btn-accent" onclick="submitQuiz()">Submit Quiz</button>`;
  html += '</div>';

  container.innerHTML = html;
}

function selectOption(idx) {
  answers[currentQuestion] = idx;
  // Update UI
  document.querySelectorAll('.quiz-option').forEach((el, i) => {
    el.classList.toggle('selected', i === idx);
    const label = el.querySelector('.quiz-option-label');
    if (label) label.style.transition = 'all 0.2s';
  });
}

function nextQuestion() {
  if (currentQuestion < quizData.questions.length - 1) {
    currentQuestion++;
    renderQuestion();
  }
}

function prevQuestion() {
  if (currentQuestion > 0) {
    currentQuestion--;
    renderQuestion();
  }
}

function submitQuiz() {
  const total = quizData.questions.length;
  const unanswered = [];
  for (let i = 0; i < total; i++) {
    if (answers[i] === undefined) unanswered.push(i + 1);
  }

  if (unanswered.length > 0) {
    if (!confirm(`You have ${unanswered.length} unanswered question(s). Submit anyway?`)) return;
  }

  // Build submission
  const submission = [];
  for (let i = 0; i < total; i++) {
    const q = quizData.questions[i];
    const selectedIdx = answers[i];
    submission.push({
      question_id: q.id,
      selected_option_id: selectedIdx !== undefined ? q.options[selectedIdx].id : null,
    });
  }

  fetch(`/api/v1/quizzes/${quizData.id}/submit/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify({ answers: submission }),
  })
  .then(r => r.json())
  .then(result => {
    showQuizResults(result);
  })
  .catch(() => showToast('Error submitting quiz', 'error'));
}

function showQuizResults(result) {
  const container = document.getElementById('quizContent');
  const passed = result.passed;
  const pct = result.percentage;

  let html = `
    <div style="text-align: center; padding: 2rem 0;">
      <div style="font-size: 4rem; margin-bottom: 1rem;">${passed ? '🎉' : '📝'}</div>
      <h2 style="margin-bottom: 0.5rem;">${passed ? 'Congratulations!' : 'Keep Practicing!'}</h2>
      <p style="font-size: 1.1rem; color: var(--text-secondary); margin-bottom: 1.5rem;">
        You scored <strong style="color: ${passed ? 'var(--success)' : 'var(--error)'};">${result.score}/${result.total_marks}</strong>
        (${pct}%)
      </p>
      <div style="width: 200px; height: 200px; border-radius: 50%; border: 8px solid ${passed ? 'var(--success)' : 'var(--error)'}; display: flex; align-items: center; justify-content: center; margin: 0 auto 2rem;">
        <span style="font-size: 2.5rem; font-weight: 800; color: ${passed ? 'var(--success)' : 'var(--error)'};">${pct}%</span>
      </div>
  `;

  if (passed) {
    html += `
      <p style="color: var(--success); font-weight: 600; margin-bottom: 1.5rem;">✅ Pass mark: ${result.pass_percentage}%</p>
      <button class="btn btn-primary" onclick="markComplete('${result.lesson_id}')">Continue to Next Lesson →</button>
    `;
  } else {
    html += `
      <p style="color: var(--error); font-weight: 600; margin-bottom: 1.5rem;">❌ Required: ${result.pass_percentage}%</p>
      <button class="btn btn-primary" onclick="loadQuiz('${quizData.id}')">Try Again</button>
    `;
  }

  html += '</div>';

  // Show detailed results
  if (result.details) {
    html += '<div style="margin-top: 2rem;"><h3 style="margin-bottom: 1rem;">Detailed Results</h3>';
    result.details.forEach((d, i) => {
      const q = quizData.questions[i];
      html += `
        <div style="margin-bottom: 1rem; padding: 1rem; border-radius: var(--radius-sm); border: 1px solid ${d.correct ? 'var(--success)' : 'var(--error)'}; background: ${d.correct ? '#F0FDF4' : '#FEF2F2'};">
          <div style="font-weight: 600; margin-bottom: 0.5rem;">${d.correct ? '✅' : '❌'} Q${i+1}: ${q.text}</div>
          ${!d.correct && d.correct_answer ? `<div style="font-size: 0.85rem; color: var(--success);">Correct answer: ${d.correct_answer}</div>` : ''}
          ${d.explanation ? `<div class="quiz-explanation">${d.explanation}</div>` : ''}
        </div>
      `;
    });
    html += '</div>';
  }

  container.innerHTML = html;
}
