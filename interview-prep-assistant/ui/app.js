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

// Start Session
document.getElementById('btn-start').addEventListener('click', async () => {
    const company = document.getElementById('company').value.trim();
    const role = document.getElementById('role').value.trim();
    
    if (!company || !role) return alert('Please enter both company and role.');
    
    document.getElementById('btn-start').classList.add('hidden');
    document.getElementById('loading-msg').classList.remove('hidden');
    document.getElementById('error-msg').classList.add('hidden');
    
    try {
        const res = await fetch('/api/start_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company, role })
        });
        
        if (!res.ok) throw new Error('Failed to generate questions');
        
        sessionData = await res.json();
        
        document.getElementById('session-info').textContent = `${sessionData.company} — ${sessionData.role}`;
        renderQuestions();
        switchView('list');
        
    } catch (err) {
        document.getElementById('error-msg').textContent = err.message;
        document.getElementById('error-msg').classList.remove('hidden');
    } finally {
        document.getElementById('btn-start').classList.remove('hidden');
        document.getElementById('loading-msg').classList.add('hidden');
    }
});

function renderQuestions() {
    const container = document.getElementById('questions-container');
    container.innerHTML = '';
    
    sessionData.final_questions.forEach((q, idx) => {
        const card = document.createElement('div');
        card.className = 'card question-item';
        card.innerHTML = `
            <h3>Question ${idx + 1}</h3>
            <p>${q.text}</p>
            <p class="category-tag">${q.category || 'General'} | Difficulty: ${q.difficulty || 'N/A'}</p>
        `;
        card.addEventListener('click', () => openQuestion(q));
        container.appendChild(card);
    });
}

function openQuestion(q) {
    currentQuestion = q;
    iterationCount = 0;
    
    document.getElementById('current-question-text').textContent = q.text;
    document.getElementById('current-question-meta').textContent = q.category || 'General';
    document.getElementById('user-answer').value = '';
    document.getElementById('feedback-panel').classList.add('hidden');
    document.getElementById('btn-submit-answer').classList.remove('hidden');
    document.getElementById('refinement-prompt').classList.add('hidden');
    
    switchView('answer');
}

document.getElementById('btn-back').addEventListener('click', () => {
    switchView('list');
});

// Evaluate Answer
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

function renderFeedback(feedback) {
    const panel = document.getElementById('feedback-panel');
    panel.classList.remove('hidden');
    
    const scoreEl = document.getElementById('final-score');
    scoreEl.textContent = feedback.score.toFixed(1);
    
    // Set colour
    scoreEl.className = 'score-number'; // reset
    if (feedback.score < 5) scoreEl.classList.add('score-red');
    else if (feedback.score < 7) scoreEl.classList.add('score-amber');
    else scoreEl.classList.add('score-green');
    
    document.getElementById('score-clarity').textContent = feedback.breakdown.clarity;
    document.getElementById('score-depth').textContent = feedback.breakdown.depth;
    document.getElementById('score-relevance').textContent = feedback.breakdown.relevance;
    document.getElementById('score-star').textContent = feedback.breakdown.starFormat;
    document.getElementById('score-role').textContent = feedback.breakdown.roleFit;
    
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

// Summary
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
    switchView('input');
});
