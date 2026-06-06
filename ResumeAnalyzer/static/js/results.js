'use strict';

const data = (() => {
  try {
    const raw = sessionStorage.getItem('resumeAnalysisResult');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
})();

const $ = (id) => document.getElementById(id);

window.addEventListener('DOMContentLoaded', () => {
  if (!data) {
    $('resultsLoading').style.display = 'none';
    $('noData').style.display = 'block';
    return;
  }
  renderAll(data);
});

function renderAll(d) {
  $('resultsLoading').style.display = 'none';
  $('resultsDashboard').style.display = 'block';
  $('resultsDashboard').classList.add('animate-in');

  renderHeader(d);
  renderScore(d.scores);
  renderBreakdown(d.scores);
  renderProfile(d);
  renderSkills(d);
  renderKeywords(d.match_result.keyword_match);
  renderExperience(d.match_result.experience_match);
  renderEducation(d.match_result.education_match);
  renderCertifications(d.match_result.certification_match);
  renderStrengths(d.suggestions.strengths);
  renderActionPlan(d.suggestions.overall_action_plan);
  renderSuggestionTabs(d.suggestions);
  setupTabs();
  setupDownload(d);
}

// ===== Header =====
function renderHeader(d) {
  const name = d.candidate.name !== 'Not Found' ? d.candidate.name : 'Candidate';
  const initial = name.charAt(0).toUpperCase();

  $('candidateAvatar').textContent = initial;
  $('candidateName').textContent = name;
  $('candidateEmail').textContent = d.candidate.email !== 'Not Found' ? d.candidate.email : '—';
  $('candidatePhone').textContent = d.candidate.phone !== 'Not Found' ? d.candidate.phone : '—';
}

// ===== Score Ring =====
function renderScore(scores) {
  const overall = scores.overall;
  const fill = $('scoreRingFill');
  const circumference = 2 * Math.PI * 84;

  // B&W theme: use grey scale based on score
  const ringColor = scores.overall >= 70 ? '#111111' : scores.overall >= 45 ? '#555555' : '#999999';
  fill.style.stroke = ringColor;

  setTimeout(() => {
    const offset = circumference - (overall / 100) * circumference;
    fill.style.strokeDashoffset = offset;
  }, 200);

  // Animate number counter
  animateCounter($('overallScore'), 0, overall, 1400);

  $('scoreRating').textContent = scores.rating;
  $('scoreRating').style.color = 'var(--text)';
  $('atsScore').textContent = scores.ats_score + '%';
  $('percentile').textContent = scores.percentile;
}

function animateCounter(el, from, to, duration) {
  const start = performance.now();
  function step(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(from + (to - from) * eased);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ===== Breakdown =====
function renderBreakdown(scores) {
  const items = [
    { key: 'skills', label: 'Skills (50%)' },
    { key: 'experience', label: 'Experience (20%)' },
    { key: 'education', label: 'Education (15%)' },
    { key: 'certifications', label: 'Certifications (10%)' },
    { key: 'keywords', label: 'Keywords (5%)' },
  ];

  const container = $('breakdownList');
  container.innerHTML = '';

  items.forEach(({ key, label }, i) => {
    const item = scores.breakdown[key];
    const score = item.score;
    const barShade = score >= 70 ? '#111' : score >= 45 ? '#555' : '#999';

    const el = document.createElement('div');
    el.className = 'breakdown-item';
    el.innerHTML = `
      <div class="breakdown-item__header">
        <span class="breakdown-item__label">${label}</span>
        <span class="breakdown-item__score">${score}%</span>
      </div>
      <div class="breakdown-bar">
        <div class="breakdown-bar__fill" data-width="${score}" style="background:${barShade}; width:0;"></div>
      </div>
    `;
    container.appendChild(el);
  });

  // Animate bars
  setTimeout(() => {
    document.querySelectorAll('.breakdown-bar__fill').forEach(bar => {
      bar.style.width = bar.dataset.width + '%';
    });
  }, 300);
}

// ===== Profile =====
function renderProfile(d) {
  const resume = d.parsed_resume;
  const container = $('profileList');
  container.innerHTML = '';

  const items = [
    { key: 'Email', val: d.candidate.email },
    { key: 'Phone', val: d.candidate.phone },
    { key: 'Experience', val: resume.years_of_experience ? `${resume.years_of_experience} yr(s)` : 'N/A' },
    { key: 'LinkedIn', val: resume.linkedin || '—' },
    { key: 'GitHub', val: resume.github || '—' },
  ];

  if (resume.summary) {
    const summaryEl = document.createElement('div');
    summaryEl.className = 'profile-item';
    summaryEl.style.flexDirection = 'column';
    summaryEl.innerHTML = `
      <span class="profile-item__key">Summary</span>
      <span class="profile-item__val" style="margin-top:0.25rem; font-size:0.8rem; color:var(--text-muted); line-height:1.5;">
        ${escapeHtml(resume.summary.substring(0, 180))}${resume.summary.length > 180 ? '…' : ''}
      </span>
    `;
    container.appendChild(summaryEl);
  }

  items.forEach(({ key, val }) => {
    if (!val || val === 'Not Found' || val === '—') return;
    const el = document.createElement('div');
    el.className = 'profile-item';
    el.innerHTML = `
      <span class="profile-item__key">${key}</span>
      <span class="profile-item__val">${escapeHtml(val)}</span>
    `;
    container.appendChild(el);
  });
}

// ===== Skills =====
function renderSkills(d) {
  const sm = d.match_result.skill_match;
  const matched = sm.matched || [];
  const missing = sm.missing || [];
  const extra = sm.extra || [];

  $('skillBadge').textContent = `${matched.length}/${sm.required_count || (matched.length + missing.length)} skills`;

  renderTagList('matchedSkills', matched, 'match');
  renderTagList('missingSkills', missing, 'missing');
  renderTagList('extraSkills', extra.slice(0, 15), 'extra');

  if (extra.length === 0) {
    $('extraSkillsBlock').style.display = 'none';
  }
}

function renderTagList(containerId, items, type) {
  const container = $(containerId);
  container.innerHTML = '';
  if (!items.length) {
    container.innerHTML = '<span style="font-size:0.8rem; color:var(--text-muted);">None detected</span>';
    return;
  }
  items.forEach(skill => {
    const tag = document.createElement('span');
    tag.className = `skill-tag skill-tag--${type}`;
    tag.textContent = skill;
    container.appendChild(tag);
  });
}

// ===== Keywords =====
function renderKeywords(km) {
  const matchedEl = $('matchedKeywords');
  const missingEl = $('missingKeywords');
  matchedEl.innerHTML = '';
  missingEl.innerHTML = '';

  (km.matched_keywords || []).slice(0, 20).forEach(kw => {
    const tag = document.createElement('span');
    tag.className = 'kw-tag kw-tag--match';
    tag.textContent = kw;
    matchedEl.appendChild(tag);
  });

  (km.missing_keywords || []).slice(0, 15).forEach(kw => {
    const tag = document.createElement('span');
    tag.className = 'kw-tag kw-tag--missing';
    tag.textContent = kw;
    missingEl.appendChild(tag);
  });
}

// ===== Experience =====
function renderExperience(exp) {
  const container = $('experienceBlock');
  container.innerHTML = '';

  const scoreEl = document.createElement('div');
  scoreEl.className = 'info-score';
  scoreEl.innerHTML = `
    <span style="color:var(--text); font-weight:700; font-size:1.1rem;">${exp.score}%</span>
    <span style="color:var(--text-muted); font-size:0.78rem;">match</span>
  `;
  container.appendChild(scoreEl);

  const statusEl = document.createElement('div');
  statusEl.className = 'info-status';
  statusEl.textContent = exp.status;
  container.appendChild(statusEl);

  if (exp.experience_entries && exp.experience_entries.length > 0) {
    const divider = document.createElement('div');
    divider.style.cssText = 'height:1px; background:var(--border); margin:0.75rem 0;';
    container.appendChild(divider);

    exp.experience_entries.slice(0, 3).forEach(entry => {
      const el = document.createElement('div');
      el.className = 'info-item';
      el.textContent = entry.length > 80 ? entry.substring(0, 80) + '…' : entry;
      container.appendChild(el);
    });
  }
}

// ===== Education =====
function renderEducation(edu) {
  const container = $('educationBlock');
  container.innerHTML = '';

  const scoreEl = document.createElement('div');
  scoreEl.className = 'info-score';
  scoreEl.innerHTML = `
    <span style="color:var(--text); font-weight:700; font-size:1.1rem;">${edu.score}%</span>
    <span style="color:var(--text-muted); font-size:0.78rem;">match</span>
  `;
  container.appendChild(scoreEl);

  const levelEl = document.createElement('div');
  levelEl.className = 'info-status';
  levelEl.innerHTML = `Detected: <strong>${edu.resume_level}</strong> · Required: <strong>${edu.required_level}</strong>`;
  container.appendChild(levelEl);

  if (edu.resume_education && edu.resume_education.length > 0) {
    const divider = document.createElement('div');
    divider.style.cssText = 'height:1px; background:var(--border); margin:0.75rem 0;';
    container.appendChild(divider);
    edu.resume_education.slice(0, 3).forEach(e => {
      const el = document.createElement('div');
      el.className = 'info-item';
      el.textContent = e.length > 70 ? e.substring(0, 70) + '…' : e;
      container.appendChild(el);
    });
  }
}

// ===== Certifications =====
function renderCertifications(cert) {
  const container = $('certBlock');
  container.innerHTML = '';

  const scoreEl = document.createElement('div');
  scoreEl.className = 'info-score';
  scoreEl.innerHTML = `
    <span style="color:var(--text); font-weight:700; font-size:1.1rem;">${cert.score}%</span>
    <span style="color:var(--text-muted); font-size:0.78rem;">match</span>
    <span style="color:var(--text-muted); font-size:0.78rem; margin-left:0.5rem;">· ${cert.status}</span>
  `;
  container.appendChild(scoreEl);

  const certs = cert.resume_certifications || [];
  if (certs.length) {
    const divider = document.createElement('div');
    divider.style.cssText = 'height:1px; background:var(--border); margin:0.75rem 0;';
    container.appendChild(divider);
    certs.slice(0, 5).forEach(c => {
      const el = document.createElement('div');
      el.className = 'cert-item';
      el.innerHTML = `<span class="cert-item__icon">🏆</span><span>${escapeHtml(c)}</span>`;
      container.appendChild(el);
    });
  } else {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.textContent = 'No certifications detected in resume.';
    container.appendChild(empty);
  }
}

// ===== Strengths =====
function renderStrengths(strengths) {
  const list = $('strengthList');
  list.innerHTML = '';
  (strengths || []).forEach(s => {
    const li = document.createElement('li');
    li.className = 'strength-item';
    li.textContent = s;
    list.appendChild(li);
  });
}

// ===== Action Plan =====
function renderActionPlan(plan) {
  const list = $('actionList');
  list.innerHTML = '';
  (plan || []).forEach(step => {
    const li = document.createElement('li');
    li.className = 'action-item';
    li.textContent = step;
    list.appendChild(li);
  });
}

// ===== Suggestion Tabs =====
function renderSuggestionTabs(suggestions) {
  // Skills tab
  const skillsTab = $('tab-skills');
  skillsTab.innerHTML = '';
  const skillSugs = suggestions.skill_suggestions || [];
  if (!skillSugs.length) {
    skillsTab.innerHTML = '<div class="empty-state">No missing skills identified — great coverage!</div>';
  } else {
    skillSugs.forEach(s => {
      skillsTab.appendChild(makeSuggestionItem(s.skill, s.action, s.priority));
    });
  }

  // Keywords tab
  const kwTab = $('tab-keywords');
  kwTab.innerHTML = '';
  const kwSugs = suggestions.keyword_suggestions || [];
  if (!kwSugs.length) {
    kwTab.innerHTML = '<div class="empty-state">Keyword coverage looks good!</div>';
  } else {
    kwSugs.forEach(s => {
      kwTab.appendChild(makeSuggestionItem(s.keyword, s.action, 'Medium'));
    });
  }

  // Certs tab
  const certTab = $('tab-certs');
  certTab.innerHTML = '';
  const certSugs = suggestions.certification_suggestions || [];
  if (!certSugs.length) {
    certTab.innerHTML = '<div class="empty-state">No specific certifications flagged.</div>';
  } else {
    certSugs.forEach(s => {
      certTab.appendChild(makeSuggestionItem(s.certification, s.reason, s.priority));
    });
  }

  // ATS tab
  const atsTab = $('tab-ats');
  atsTab.innerHTML = '';
  const atsSugs = suggestions.ats_suggestions || [];
  atsSugs.forEach(tip => {
    const el = document.createElement('div');
    el.className = 'suggestion-item';
    el.textContent = tip;
    atsTab.appendChild(el);
  });

  // Projects tab
  const projTab = $('tab-projects');
  projTab.innerHTML = '';
  const projSugs = suggestions.project_suggestions || [];
  projSugs.forEach(tip => {
    const el = document.createElement('div');
    el.className = 'suggestion-item';
    el.textContent = tip;
    projTab.appendChild(el);
  });
}

function makeSuggestionItem(label, desc, priority) {
  const el = document.createElement('div');
  el.className = 'suggestion-item';
  const priorityClass = (priority || '').toLowerCase() === 'high' ? 'priority--high'
    : (priority || '').toLowerCase() === 'medium' ? 'priority--medium'
    : 'priority--low';
  el.innerHTML = `
    <div class="suggestion-item__label">
      ${escapeHtml(label)}
      ${priority ? `<span class="suggestion-priority ${priorityClass}">${escapeHtml(priority)}</span>` : ''}
    </div>
    <div>${escapeHtml(desc)}</div>
  `;
  return el;
}

// ===== Tabs =====
function setupTabs() {
  const tabs = document.querySelectorAll('.stab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => { t.classList.remove('stab--active'); t.setAttribute('aria-selected', 'false'); });
      tab.classList.add('stab--active');
      tab.setAttribute('aria-selected', 'true');

      document.querySelectorAll('.stab-content').forEach(c => c.classList.add('stab-content--hidden'));
      const target = document.getElementById(`tab-${tab.dataset.tab}`);
      if (target) target.classList.remove('stab-content--hidden');
    });
  });
}

// ===== Download Report =====
function setupDownload(d) {
  $('downloadReport').addEventListener('click', () => {
    const report = generateTextReport(d);
    const blob = new Blob([report], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `resume-analysis-${d.candidate.name.replace(/\s+/g, '-').toLowerCase()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  });
}

function generateTextReport(d) {
  const sep = '='.repeat(60);
  const sec = '-'.repeat(40);

  return `${sep}
RESUME ANALYSIS REPORT — ResumeIQ
${sep}
Candidate: ${d.candidate.name}
Email:     ${d.candidate.email}
Phone:     ${d.candidate.phone}
Generated: ${new Date().toLocaleString()}

${sep}
OVERALL MATCH SCORE: ${d.scores.overall}/100 — ${d.scores.rating}
ATS Score: ${d.scores.ats_score}%  |  Estimated Top ${d.scores.percentile}% of applicants
${sep}

SCORE BREAKDOWN
${sec}
Skills (50%):         ${d.scores.breakdown.skills.score}%
Experience (20%):     ${d.scores.breakdown.experience.score}%
Education (15%):      ${d.scores.breakdown.education.score}%
Certifications (10%): ${d.scores.breakdown.certifications.score}%
Keywords (5%):        ${d.scores.breakdown.keywords.score}%

MATCHED SKILLS (${d.match_result.skill_match.matched.length})
${sec}
${d.match_result.skill_match.matched.join(', ') || 'None'}

MISSING SKILLS (${d.match_result.skill_match.missing.length})
${sec}
${d.match_result.skill_match.missing.join(', ') || 'None'}

EXPERIENCE
${sec}
${d.match_result.experience_match.status}

EDUCATION
${sec}
Detected: ${d.match_result.education_match.resume_level}
Required: ${d.match_result.education_match.required_level}
Status:   ${d.match_result.education_match.status}

CERTIFICATIONS
${sec}
${d.match_result.certification_match.resume_certifications.join(', ') || 'None detected'}

STRENGTHS
${sec}
${(d.suggestions.strengths || []).map((s, i) => `${i + 1}. ${s}`).join('\n')}

ACTION PLAN
${sec}
${(d.suggestions.overall_action_plan || []).map((s, i) => `${i + 1}. ${s}`).join('\n')}

SKILL SUGGESTIONS
${sec}
${(d.suggestions.skill_suggestions || []).map(s => `• [${s.priority}] Add "${s.skill}": ${s.action}`).join('\n')}

ATS OPTIMIZATION TIPS
${sec}
${(d.suggestions.ats_suggestions || []).map((s, i) => `${i + 1}. ${s}`).join('\n')}

${sep}
Generated by ResumeIQ — AI-Powered Resume Analysis
${sep}
`;
}

// ===== Utilities =====
function scoreToColor(score) {
  if (score >= 80) return 'var(--green)';
  if (score >= 60) return 'var(--blue)';
  if (score >= 40) return 'var(--amber)';
  return 'var(--red)';
}

function escapeHtml(str) {
  if (typeof str !== 'string') return String(str || '');
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
