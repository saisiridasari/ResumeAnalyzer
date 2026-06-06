'use strict';

const API_BASE = '';

const form = document.getElementById('analyzeForm');
const resumeFileInput = document.getElementById('resumeFile');
const uploadZone = document.getElementById('uploadZone');
const uploadContent = document.getElementById('uploadContent');
const uploadPreview = document.getElementById('uploadPreview');
const previewName = document.getElementById('previewName');
const previewSize = document.getElementById('previewSize');
const removeFileBtn = document.getElementById('removeFile');
const jdTextarea = document.getElementById('jobDescription');
const jdCharCount = document.getElementById('jdCharCount');
const resumeError = document.getElementById('resumeError');
const jdError = document.getElementById('jdError');
const submitBtn = document.getElementById('submitBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingTitle = document.getElementById('loadingTitle');
const loadingSub = document.getElementById('loadingSub');

let selectedFile = null;
let uploadedFilename = null;

// ===== Drag-and-Drop =====
uploadZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadZone.classList.add('drag-over');
});

uploadZone.addEventListener('dragleave', () => {
  uploadZone.classList.remove('drag-over');
});

uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  const files = e.dataTransfer.files;
  if (files.length) handleFileSelect(files[0]);
});

uploadZone.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    resumeFileInput.click();
  }
});

resumeFileInput.addEventListener('change', () => {
  if (resumeFileInput.files.length) {
    handleFileSelect(resumeFileInput.files[0]);
  }
});

function handleFileSelect(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf', 'docx'].includes(ext)) {
    showError(resumeError, 'Only PDF and DOCX files are supported.');
    return;
  }
  if (file.size > 16 * 1024 * 1024) {
    showError(resumeError, 'File exceeds the 16 MB limit.');
    return;
  }
  clearError(resumeError);
  selectedFile = file;
  uploadedFilename = null;

  previewName.textContent = file.name;
  previewSize.textContent = formatBytes(file.size);
  uploadContent.style.display = 'none';
  uploadPreview.style.display = 'block';
}

removeFileBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  resetFile();
});

function resetFile() {
  selectedFile = null;
  uploadedFilename = null;
  resumeFileInput.value = '';
  uploadContent.style.display = 'block';
  uploadPreview.style.display = 'none';
}

// ===== JD Character Counter =====
jdTextarea.addEventListener('input', () => {
  jdCharCount.textContent = jdTextarea.value.length;
  if (jdTextarea.value.trim().length >= 20) clearError(jdError);
});

// ===== Form Submit =====
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  let valid = true;

  if (!selectedFile) {
    showError(resumeError, 'Please upload your resume (PDF or DOCX).');
    valid = false;
  }
  if (jdTextarea.value.trim().length < 20) {
    showError(jdError, 'Please paste a job description (at least 20 characters).');
    valid = false;
  }

  if (!valid) return;

  submitBtn.disabled = true;
  showLoading();

  try {
    // Step 1: Upload
    setLoadingStep(1, 'active');
    setLoadingTitle('Uploading resume…', 'Processing your document');

    const formData = new FormData();
    formData.append('resume', selectedFile);

    const uploadRes = await fetch(`${API_BASE}/api/upload`, {
      method: 'POST',
      body: formData
    });
    const uploadData = await uploadRes.json();

    if (!uploadRes.ok) throw new Error(uploadData.error || 'Upload failed');
    setLoadingStep(1, 'done');
    uploadedFilename = uploadData.filename;

    // Steps 2-5: Analyze
    setLoadingStep(2, 'active');
    setLoadingTitle('Analyzing your resume…', 'Running NLP extraction and matching');

    setTimeout(() => { setLoadingStep(2, 'done'); setLoadingStep(3, 'active'); }, 800);
    setTimeout(() => { setLoadingStep(3, 'done'); setLoadingStep(4, 'active'); }, 1800);
    setTimeout(() => { setLoadingStep(4, 'done'); setLoadingStep(5, 'active'); }, 2800);

    const analyzeRes = await fetch(`${API_BASE}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: uploadedFilename,
        job_description: jdTextarea.value.trim()
      })
    });

    const analyzeData = await analyzeRes.json();
    if (!analyzeRes.ok) throw new Error(analyzeData.error || 'Analysis failed');

    setLoadingStep(5, 'done');

    sessionStorage.setItem('resumeAnalysisResult', JSON.stringify(analyzeData));

    setTimeout(() => {
      window.location.href = '/results';
    }, 600);

  } catch (err) {
    hideLoading();
    submitBtn.disabled = false;
    showError(resumeError, err.message || 'An error occurred. Please try again.');
  }
});

// ===== Loading helpers =====
function showLoading() {
  loadingOverlay.style.display = 'flex';
  document.querySelectorAll('.loading-step').forEach(el => {
    el.classList.remove('loading-step--active', 'loading-step--done');
    el.querySelector('.loading-step__icon').textContent = '⏳';
  });
}

function hideLoading() {
  loadingOverlay.style.display = 'none';
}

function setLoadingStep(n, state) {
  const el = document.getElementById(`lstep-${n}`);
  if (!el) return;
  el.classList.remove('loading-step--active', 'loading-step--done');
  const icon = el.querySelector('.loading-step__icon');
  if (state === 'active') {
    el.classList.add('loading-step--active');
    icon.textContent = '⚡';
  } else if (state === 'done') {
    el.classList.add('loading-step--done');
    icon.textContent = '✓';
  }
}

function setLoadingTitle(title, sub) {
  loadingTitle.textContent = title;
  loadingSub.textContent = sub;
}

// ===== Validation helpers =====
function showError(el, msg) {
  el.textContent = msg;
}
function clearError(el) {
  el.textContent = '';
}

// ===== Utility =====
function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
