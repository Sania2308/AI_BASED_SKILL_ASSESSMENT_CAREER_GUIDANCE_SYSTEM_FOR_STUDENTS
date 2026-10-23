/**
 * SkillGuide Core Client Application Logic
 * Modern Toast System, Theme Switcher, AJAX Wrappers & Legacy Compatibility
 */

// Toast Notification Manager
function showToast(message, type = 'success', duration = 4000) {
    let shelf = document.getElementById('toastShelf');
    if (!shelf) {
        shelf = document.createElement('div');
        shelf.id = 'toastShelf';
        shelf.className = 'toast-shelf';
        document.body.appendChild(shelf);
    }

    const toast = document.createElement('div');
    toast.className = `toast-alert ${type}`;

    let iconClass = 'bi-check-circle-fill';
    if (type === 'error') iconClass = 'bi-exclamation-triangle-fill';
    else if (type === 'warning') iconClass = 'bi-info-circle-fill';

    toast.innerHTML = `
        <i class="bi ${iconClass} toast-icon"></i>
        <div class="toast-text">${message}</div>
    `;

    shelf.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 350);
    }, duration);
}

// Dark / Light Theme Manager
function initTheme() {
    const saved = localStorage.getItem('skillguide_theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    updateThemeIcon(saved);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('skillguide_theme', next);
    updateThemeIcon(next);
}

function updateThemeIcon(theme) {
    const btn = document.getElementById('themeToggleBtn');
    if (!btn) return;
    const icon = btn.querySelector('i');
    if (!icon) return;
    if (theme === 'dark') {
        icon.className = 'bi bi-sun-fill';
    } else {
        icon.className = 'bi bi-moon-stars-fill';
    }
}

// Mobile Sidebar Drawer Toggle
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('mobile-open');
    }
}

// -------------------------------------------------------------
// RESUME EXTRACTION (File Upload & Text Input)
// -------------------------------------------------------------
async function handleResumeUpload(event) {
    const fileInput = event.target;
    if (!fileInput.files || !fileInput.files[0]) return;

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('resume_file', file);

    const btn = document.getElementById('uploadResumeBtn');
    const originalText = btn ? btn.innerHTML : 'Upload';
    if (btn) btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Extracting...';

    try {
        const response = await fetch('/api/upload-resume', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (!response.ok) {
            showToast(data.error || 'Failed to parse resume document.', 'error');
            return;
        }

        showToast(data.message || `Identified ${data.count} skills!`, 'success');
        renderCategorizedSkills(data.categorized);
        setTimeout(() => window.location.reload(), 1200);
    } catch (err) {
        showToast('Network error while uploading resume document.', 'error');
    } finally {
        if (btn) btn.innerHTML = originalText;
        fileInput.value = '';
    }
}

async function extractSkills() {
    const textarea = document.getElementById('resume') || document.getElementById('resumeTextarea');
    if (!textarea) return;
    const text = textarea.value.trim();
    if (!text) {
        showToast('Please paste or write your skills/resume text first.', 'warning');
        return;
    }

    const btn = document.getElementById('extractSkillsBtn');
    if (btn) btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Analyzing NLP...';

    try {
        const response = await fetch('/api/extract-text-skills', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        const data = await response.json();

        if (!response.ok) {
            showToast(data.error || 'Extraction failed.', 'error');
            return;
        }

        showToast(data.message || `Detected ${data.count} skills!`, 'success');
        renderCategorizedSkills(data.categorized);
        setTimeout(() => window.location.reload(), 1200);
    } catch (err) {
        showToast('Network error while analyzing resume skills.', 'error');
    } finally {
        if (btn) btn.innerHTML = '<i class="bi bi-cpu me-1"></i> Extract Skills';
    }
}

function renderCategorizedSkills(categorized) {
    const container = document.getElementById('extractedSkillsContainer');
    if (!container) return;

    let html = '';
    for (const [category, skills] of Object.entries(categorized)) {
        html += `
            <div class="mb-3">
                <div class="small fw-bold text-muted text-uppercase mb-2">${category}</div>
                <div class="skill-tags-flex">
                    ${skills.map(s => `<span class="skill-tag claimed"><i class="bi bi-tag-fill me-1"></i>${s}</span>`).join('')}
                </div>
            </div>
        `;
    }
    container.innerHTML = html || '<span class="text-muted">No skills detected.</span>';
}

async function resetSkills() {
    if (!confirm('Are you sure you want to clear your extracted resume skills?')) return;
    try {
        const res = await fetch('/api/reset-skills', { method: 'POST' });
        const data = await res.json();
        showToast('Saved resume skills cleared.', 'success');
        setTimeout(() => window.location.reload(), 800);
    } catch (err) {
        showToast('Error resetting skills.', 'error');
    }
}

// -------------------------------------------------------------
// TECHNICAL MCQ ASSESSMENTS (10 Skills)
// -------------------------------------------------------------
async function startTechnicalAssessment(skill) {
    const modal = document.getElementById('techAssessmentModal');
    const form = document.getElementById('techAssessmentForm');
    const title = document.getElementById('techAssessmentModalTitle');
    const subtitle = document.getElementById('techAssessmentModalSubtitle');

    if (!modal || !form) return;

    title.innerHTML = `<i class="bi bi-patch-check-fill text-primary me-2"></i> ${skill} Technical Verification`;
    subtitle.textContent = `10 skill-specific questions. Reach 70%+ for Advanced/Expert verification.`;
    form.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-2 text-muted">Loading question bank...</p></div>';

    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();

    try {
        const res = await fetch('/api/technical-questions/' + encodeURIComponent(skill));
        const data = await res.json();
        if (!res.ok) {
            form.innerHTML = `<div class="alert alert-danger">${data.error || 'Failed to load questions.'}</div>`;
            return;
        }

        form.dataset.skill = skill;
        form.innerHTML = data.questions.map((q, idx) => `
            <div class="question-block" id="techQ_${q.id}">
                <div class="question-header">
                    <span class="question-badge">${q.id}</span>
                    <span class="question-title-text">${q.text}</span>
                    <span class="question-cat-tag">MCQ</span>
                </div>
                <div class="mcq-options-grid">
                    ${q.options.map((opt, optIdx) => `
                        <label class="mcq-option-label">
                            <input type="radio" name="tech_ans_${q.id}" value="${optIdx}" required>
                            <span>${opt}</span>
                        </label>
                    `).join('')}
                </div>
            </div>
        `).join('');
    } catch (err) {
        form.innerHTML = '<div class="alert alert-danger">Network error loading assessment questions.</div>';
    }
}

async function submitTechnicalAssessmentModal() {
    const form = document.getElementById('techAssessmentForm');
    if (!form) return;
    const skill = form.dataset.skill;
    if (!skill) return;

    const answers = {};
    for (let i = 1; i <= 10; i++) {
        const checked = form.querySelector(`input[name="tech_ans_${i}"]:checked`);
        if (!checked) {
            showToast(`Please answer question #${i} before submitting.`, 'warning');
            const qEl = document.getElementById(`techQ_${i}`);
            if (qEl) qEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }
        answers[i] = checked.value;
    }

    const submitBtn = document.getElementById('submitTechAssessmentBtn');
    if (submitBtn) submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Grading & Minting Badge...';

    try {
        const res = await fetch('/api/submit-technical/' + encodeURIComponent(skill), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answers })
        });
        const data = await res.json();

        if (!res.ok) {
            showToast(data.error || 'Grading failed.', 'error');
            return;
        }

        showToast(`${skill} verified! Score: ${data.score}% (${data.level}). Verification Hash Minted!`, 'success', 5000);
        setTimeout(() => window.location.reload(), 1500);
    } catch (err) {
        showToast('Network error submitting technical verification.', 'error');
    } finally {
        if (submitBtn) submitBtn.innerHTML = 'Submit & Verify';
    }
}

// Legacy helper compatibility
function closeTechnicalAssessment() {
    const modalEl = document.getElementById('techAssessmentModal');
    if (modalEl) {
        const bsModal = bootstrap.Modal.getInstance(modalEl);
        if (bsModal) bsModal.hide();
    }
}

// -------------------------------------------------------------
// BROAD 5-DOMAIN ASSESSMENT
// -------------------------------------------------------------
function setupBroadAssessmentForm() {
    const form = document.getElementById('broadAssessmentForm');
    if (!form) return;

    form.addEventListener('change', () => {
        const checked = form.querySelectorAll('input[type="radio"]:checked');
        const count = checked.length;
        if (count > 0) {
            const sum = Array.from(checked).reduce((acc, el) => acc + parseInt(el.value, 10), 0);
            const liveScore = Math.round((sum / (count * 5)) * 100);
            const liveEl = document.getElementById('liveAssessmentScoreDisplay');
            if (liveEl) liveEl.textContent = `${liveScore}%`;
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const answers = {};
        for (let i = 1; i <= 10; i++) {
            const checked = form.querySelector(`input[name="broad_q_${i}"]:checked`);
            if (!checked) {
                showToast(`Please answer question #${i}.`, 'warning');
                return;
            }
            answers[i] = checked.value;
        }

        const submitBtn = document.getElementById('submitBroadAssessmentBtn');
        if (submitBtn) submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Calculating Scores...';

        try {
            const res = await fetch('/api/submit-overall', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answers })
            });
            const data = await res.json();

            if (!res.ok) {
                showToast(data.error || 'Assessment submission failed.', 'error');
                return;
            }

            showToast(`Overall Assessment saved! Overall score: ${data.overall}%.`, 'success', 4000);
            setTimeout(() => window.location.reload(), 1200);
        } catch (err) {
            showToast('Network error submitting assessment.', 'error');
        } finally {
            if (submitBtn) submitBtn.innerHTML = 'Submit Comprehensive Assessment';
        }
    });
}

// -------------------------------------------------------------
// CAREER & ROADMAP INTERACTION
// -------------------------------------------------------------
async function setTargetCareerGoal(careerName) {
    try {
        const res = await fetch('/api/set-career-goal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ career_name: careerName })
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to set target role.', 'error');
            return;
        }
        showToast(data.message || `Target career set to ${careerName}!`, 'success');
        setTimeout(() => window.location.reload(), 800);
    } catch (err) {
        showToast('Network error setting career goal.', 'error');
    }
}

async function updateRoadmapMilestone(careerName, stepId, newStatus) {
    try {
        const res = await fetch('/api/update-roadmap-step', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                career_name: careerName,
                step_id: stepId,
                status: newStatus
            })
        });
        const data = await res.json();

        if (!res.ok) {
            showToast(data.error || 'Failed to update milestone status.', 'error');
            return;
        }

        showToast(`Milestone updated to ${newStatus}! Progress: ${data.completion_pct}%`, 'success');
        const badgeEl = document.getElementById(`stepBadge_${stepId}`);
        if (badgeEl) {
            badgeEl.textContent = newStatus;
            badgeEl.className = `badge ${newStatus === 'Completed' ? 'bg-success' : (newStatus === 'In Progress' ? 'bg-warning text-dark' : 'bg-secondary')}`;
        }
        const progBar = document.getElementById('roadmapProgressBar');
        if (progBar) {
            progBar.style.width = `${data.completion_pct}%`;
        }
        const pctEl = document.getElementById('roadmapCompletionPct');
        if (pctEl) {
            pctEl.textContent = `${data.completion_pct}%`;
        }
    } catch (err) {
        showToast('Network error updating milestone.', 'error');
    }
}

// -------------------------------------------------------------
// SKILL SWAP & PEER WORKFLOW
// -------------------------------------------------------------
async function addLearningSkills() {
    const input = document.getElementById('learningInput');
    if (!input || !input.value.trim()) {
        showToast('Enter a skill name to add to your learning goals.', 'warning');
        return;
    }

    try {
        const res = await fetch('/api/learning-skills', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ skills: input.value })
        });
        const data = await res.json();

        if (!res.ok) {
            showToast(data.error || 'Failed to add learning skills.', 'error');
            return;
        }

        showToast(data.message || 'Learning skill added!', 'success');
        input.value = '';
        setTimeout(() => window.location.reload(), 800);
    } catch (err) {
        showToast('Network error updating learning skills.', 'error');
    }
}

async function removeLearningSkill(skill) {
    try {
        const res = await fetch('/api/remove-learning-skill', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ skill })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Removed ${skill} from learning goals.`, 'info');
            setTimeout(() => window.location.reload(), 600);
        }
    } catch (err) {
        showToast('Error removing learning skill.', 'error');
    }
}

async function clearLearningSkills() {
    if (!confirm('Clear all skills you want to learn?')) return;
    try {
        const res = await fetch('/api/reset-learning-skills', { method: 'POST' });
        showToast('Learning skills cleared.', 'success');
        setTimeout(() => window.location.reload(), 600);
    } catch (err) {
        showToast('Error resetting learning skills.', 'error');
    }
}

function openSwapRequestModal(peerId, peerName, peerTeachSkills) {
    const modalEl = document.getElementById('swapRequestModal');
    if (!modalEl) return;

    document.getElementById('modalPeerName').textContent = peerName;
    document.getElementById('modalPeerId').value = peerId;

    const learnSelect = document.getElementById('modalLearnSkillSelect');
    if (learnSelect) {
        learnSelect.innerHTML = peerTeachSkills.length ?
            peerTeachSkills.map(s => `<option value="${s}">${s}</option>`).join('') :
            '<option value="General Guidance">General Technical Guidance</option>';
    }

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}

async function submitSwapRequestForm() {
    const receiverId = document.getElementById('modalPeerId').value;
    const learnSkill = document.getElementById('modalLearnSkillSelect').value;
    const teachSkill = document.getElementById('modalTeachSkillSelect').value;
    const notes = document.getElementById('modalSwapNotes').value;

    try {
        const res = await fetch('/api/request-swap', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                receiver_id: receiverId,
                learn_skill: learnSkill,
                teach_skill: teachSkill,
                notes: notes
            })
        });
        const data = await res.json();

        if (!res.ok) {
            showToast(data.error || 'Failed to submit exchange proposal.', 'error');
            return;
        }

        showToast(data.message || 'Swap request sent successfully!', 'success');
        const modalEl = document.getElementById('swapRequestModal');
        if (modalEl) {
            const bsModal = bootstrap.Modal.getInstance(modalEl);
            if (bsModal) bsModal.hide();
        }
        setTimeout(() => window.location.reload(), 1000);
    } catch (err) {
        showToast('Network error submitting exchange request.', 'error');
    }
}

async function updateSwapRequestStatus(requestId, newStatus) {
    try {
        const res = await fetch('/api/update-swap-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                request_id: requestId,
                status: newStatus
            })
        });
        const data = await res.json();

        if (!res.ok) {
            showToast(data.error || 'Failed to update request status.', 'error');
            return;
        }

        showToast(data.message || `Exchange marked as ${newStatus}!`, 'success');
        setTimeout(() => window.location.reload(), 900);
    } catch (err) {
        showToast('Network error updating exchange status.', 'error');
    }
}

// -------------------------------------------------------------
// BLOCKCHAIN CERTIFICATE VERIFICATION LOOKUP
// -------------------------------------------------------------
async function handleVerificationLookup(event) {
    if (event) event.preventDefault();
    const input = document.getElementById('verifyQueryInput');
    if (!input || !input.value.trim()) {
        showToast('Please enter a verification hash or ID (e.g. SG-...).', 'warning');
        return;
    }

    const query = input.value.trim();
    window.location.href = `/verification?query=${encodeURIComponent(query)}`;
}

// Global Initialization
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    setupBroadAssessmentForm();

    // Auto-dismiss standard alerts
    setTimeout(() => {
        document.querySelectorAll('.alert-auto-dismiss').forEach(el => {
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 400);
        });
    }, 4000);
});
