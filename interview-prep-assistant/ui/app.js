let sessionData = null;
let currentQuestion = null;
let iterationCount = 0;

const views = {
    input: document.getElementById('view-input'),
    list: document.getElementById('view-list'),
    answer: document.getElementById('view-answer'),
    summary: document.getElementById('view-summary')
};

function switchView(viewName) {
    Object.values(views).forEach(v => v.classList.add('hidden'));
    views[viewName].classList.remove('hidden');
    views[viewName].classList.add('active');
}

// --- FILE UPLOAD LOGIC ---
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('resume-file');

if(dropZone && fileInput) {
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', e => {
      e.preventDefault();
      dropZone.classList.add('drag-over');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', e => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
      const file = e.dataTransfer.files[0];
      if (file) handleFileSelect(file);
    });
    fileInput.addEventListener('change', e => {
      if (e.target.files[0]) handleFileSelect(e.target.files[0]);
    });
}

async function handleFileSelect(file) {
  if (!['application/pdf', 'text/plain'].includes(file.type) && 
      !file.name.endsWith('.pdf') && !file.name.endsWith('.txt')) {
    showError('Only .pdf and .txt files are supported.');
    return;
  }
  if (file.size > 2 * 1024 * 1024) {
    showError('File must be under 2MB.');
    return;
  }

  document.getElementById('drop-zone').hidden = true;
  document.getElementById('file-selected').hidden = false;
  document.getElementById('file-name').textContent = file.name;

  document.getElementById('parse-status').hidden = false;
  const formData = new FormData();
  formData.append('resume', file);
  formData.append('company', document.getElementById('company').value.trim() || 'Unknown');
  formData.append('role', document.getElementById('role').value.trim() || 'Unknown');

  try {
    const res = await fetch('/api/session/upload-resume', {
      method: 'POST', body: formData
    });
    const data = await res.json();
    document.getElementById('parse-status').hidden = true;
    
    if (data.parsed && data.parsed.skills && data.parsed.skills.length > 0) {
      const skillsList = document.getElementById('skills-list');
      skillsList.innerHTML = data.parsed.skills
        .slice(0, 10)
        .map(s => `<span class="skill-tag">${s}</span>`)
        .join('');
      document.getElementById('resume-tags').hidden = false;
    }

    window._resumeParsed = data.parsed;
  } catch (err) {
    document.getElementById('parse-status').hidden = true;
    showError('Resume upload failed. You can still continue without it.');
  }
}

document.getElementById('remove-file').addEventListener('click', () => {
  document.getElementById('drop-zone').hidden = false;
  document.getElementById('file-selected').hidden = true;
  document.getElementById('resume-tags').hidden = true;
  document.getElementById('parse-status').hidden = true;
  document.getElementById('skills-list').innerHTML = '';
  window._resumeParsed = null;
  fileInput.value = '';
});

function showError(msg) {
    const el = document.getElementById('error-msg');
    el.textContent = msg;
    el.classList.remove('hidden');
}

// --- START SESSION ---
document.getElementById('btn-start').addEventListener('click', async () => {
    const company = document.getElementById('company').value.trim();
    const role = document.getElementById('role').value.trim();
    
    if (!company || !role) return alert('Please enter both company and role.');
    
    const btn = document.getElementById('btn-start');
    const bar = document.getElementById('progress-bar');
    const originalText = btn.textContent;
    
    btn.disabled = true;
    document.getElementById('error-msg').classList.add('hidden');
    
    const steps = [
      { text: "Researching company...", progress: 20 },
      { text: "Fetching past interview questions...", progress: 45 },
      { text: "Generating questions...", progress: 70 },
      { text: "Almost done...", progress: 90 },
    ];

    let stepIndex = 0;
    const interval = setInterval(() => {
      if (stepIndex < steps.length) {
        btn.textContent = steps[stepIndex].text;
        bar.style.width = steps[stepIndex].progress + '%';
        stepIndex++;
      }
    }, 2000);
    
    try {
        const bodyData = { company, role };
        if (window._resumeParsed) {
            bodyData.resume_data = window._resumeParsed;
        }
        
        const res = await fetch('/api/start_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bodyData)
        });
        
        if (!res.ok) throw new Error('Failed to generate questions');
        
        sessionData = await res.json();
        
        // Success: jump to 100%
        clearInterval(interval);
        bar.style.width = '100%';
        btn.textContent = "Done!";
        
        setTimeout(() => {
            document.getElementById('session-info').textContent = `${sessionData.company} — ${sessionData.role}`;
            renderQuestions();
            switchView('list');
            
            // Reset button for next time
            btn.disabled = false;
            btn.textContent = originalText;
            bar.style.width = '0%';
        }, 500);
        
    } catch (err) {
        clearInterval(interval);
        btn.disabled = false;
        btn.textContent = originalText;
        bar.style.width = '0%';
        showError(err.message);
    }
});

// --- RENDER QUESTIONS ---
function renderQuestions() {
    const container = document.getElementById('questions-container');
    container.innerHTML = '';
    
    sessionData.final_questions.forEach((q, idx) => {
        const card = document.createElement('div');
        card.className = 'q-card';
        card.dataset.id = idx;
        
        const cat = q.category || 'general';
        const catClass = cat.toLowerCase();
        
        card.innerHTML = `
          <div class="q-card-header">
            <span class="q-category-badge ${catClass}">${cat}</span>
            <span class="q-text">${q.text}</span>
            <span class="q-chevron">›</span>
          </div>
          <div class="q-card-body" hidden>
            <button class="action-btn primary" onclick="startAnswer(${idx})">
              Answer this question →
            </button>
            <button class="action-btn secondary" onclick="alert('Template feature coming soon!')">
              Show answer template
            </button>
            <button class="action-btn secondary" onclick="alert('Mock feature coming soon!')">
              Start mock interview
            </button>
          </div>
        `;
        
        const header = card.querySelector('.q-card-header');
        header.addEventListener('click', () => {
            const isOpen = card.classList.contains('open');
            document.querySelectorAll('.q-card').forEach(c => {
                c.classList.remove('open');
                c.querySelector('.q-card-body').hidden = true;
            });
            if (!isOpen) {
                card.classList.add('open');
                card.querySelector('.q-card-body').hidden = false;
            }
        });
        
        container.appendChild(card);
    });
}

// Expose startAnswer to global window object
window.startAnswer = function(idx) {
    const q = sessionData.final_questions[idx];
    currentQuestion = q;
    iterationCount = 0;
    
    document.getElementById('current-question-text').textContent = q.text;
    document.getElementById('current-question-meta').textContent = q.category || 'General';
    document.getElementById('user-answer').value = '';
    document.getElementById('feedback-panel').classList.add('hidden');
    document.getElementById('btn-submit-answer').classList.remove('hidden');
    document.getElementById('refinement-prompt').classList.add('hidden');
    
    switchView('answer');
};

document.getElementById('btn-back').addEventListener('click', () => {
    switchView('list');
});

// --- EVALUATE ANSWER ---
document.getElementById('btn-submit-answer').addEventListener('click', async () => {
    const answer = document.getElementById('user-answer').value.trim();
    if (!answer) return alert('Please provide an answer first.');
    
    document.getElementById('btn-submit-answer').classList.add('hidden');
    document.getElementById('eval-loading').classList.remove('hidden');
    
    iterationCount++;
    
    try {
        const res = await fetch('/api/evaluate_answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: currentQuestion.text,
                user_answer: answer,
                role_context: sessionData.role,
                company_context: sessionData.company,
                iteration_count: iterationCount
            })
        });
        
        if (!res.ok) throw new Error('Evaluation failed');
        
        const feedback = await res.json();
        renderFeedback(feedback);
        
    } catch (err) {
        alert(err.message);
        document.getElementById('btn-submit-answer').classList.remove('hidden');
    } finally {
        document.getElementById('eval-loading').classList.add('hidden');
    }
});

function animateScore(targetScore) {
  const el = document.getElementById('final-score');
  const duration = 800;
  const start = performance.now();
  function tick(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const current = (targetScore * progress).toFixed(1);
    el.textContent = current;
    if (progress < 1) requestAnimationFrame(tick);
    else {
        // Apply final colour
        el.className = 'score-number';
        if (targetScore < 5) el.classList.add('score-low');
        else if (targetScore < 7) el.classList.add('score-mid');
        else el.classList.add('score-high');
    }
  }
  requestAnimationFrame(tick);
}

function renderFeedback(feedback) {
    const panel = document.getElementById('feedback-panel');
    panel.classList.remove('hidden');
    
    // Animate overall score
    animateScore(feedback.score);
    
    // Render breakdown bars
    const breakdownContainer = document.getElementById('breakdown-container');
    breakdownContainer.innerHTML = '';
    
    const criteria = [
        { key: 'clarity', label: 'Clarity' },
        { key: 'depth', label: 'Depth' },
        { key: 'relevance', label: 'Relevance' },
        { key: 'starFormat', label: 'STAR Format' },
        { key: 'roleFit', label: 'Role Fit' }
    ];
    
    criteria.forEach(c => {
        const score = feedback.breakdown[c.key] || 0;
        const row = document.createElement('div');
        row.className = 'breakdown-row';
        row.innerHTML = `
          <span class="breakdown-label">${c.label}</span>
          <div class="breakdown-track">
            <div class="breakdown-fill" style="width: 0%"></div>
          </div>
          <span class="breakdown-score">${score.toFixed(1)}</span>
        `;
        breakdownContainer.appendChild(row);
        
        // Trigger animation after a tiny delay
        setTimeout(() => {
            row.querySelector('.breakdown-fill').style.width = (score * 10) + '%';
        }, 100);
    });
    
    document.getElementById('feedback-gaps').innerHTML = feedback.gaps.map(g => `<li>${g}</li>`).join('');
    document.getElementById('feedback-tips').innerHTML = feedback.tips.map(t => `<li>${t}</li>`).join('');
    document.getElementById('feedback-improved').textContent = feedback.improvedAnswer;
    
    const prompt = document.getElementById('refinement-prompt');
    const submitBtn = document.getElementById('btn-submit-answer');
    
    if (feedback.score < 7 && iterationCount < 5) {
        prompt.classList.remove('hidden');
        submitBtn.classList.remove('hidden');
        submitBtn.textContent = 'Submit Refined Answer';
    } else {
        prompt.classList.add('hidden');
        submitBtn.classList.add('hidden');
    }
}

// --- SUMMARY ---
document.getElementById('btn-summary').addEventListener('click', () => {
    document.getElementById('summary-content').innerHTML = `
        <p>Session completed for <strong>${sessionData.company}</strong> as <strong>${sessionData.role}</strong>.</p>
        <p>Total Questions Generated: ${sessionData.final_questions.length}</p>
    `;
    switchView('summary');
});

document.getElementById('btn-restart').addEventListener('click', () => {
    sessionData = null;
    document.getElementById('company').value = '';
    document.getElementById('role').value = '';
    document.getElementById('remove-file').click();
    switchView('input');
});
