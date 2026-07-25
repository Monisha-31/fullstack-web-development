document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const roleSelect = document.getElementById('role-select');
    const fileUpload = document.getElementById('file-upload');
    const dropArea = document.getElementById('drop-area');
    const fileNameDisplay = document.getElementById('file-name-display');
    const analyzeForm = document.getElementById('analysis-form');
    const analyzeBtn = document.getElementById('analyze-btn');
    
    const emptyState = document.getElementById('empty-state');
    const errorState = document.getElementById('error-state');
    const errorMessage = document.getElementById('error-message');
    const resultsContent = document.getElementById('results-content');
    
    // API config
    const API_URL = ''; // Same origin
    
    // Fetch categories on load
    fetchCategories();
    
    // Setup File Drag & Drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.add('dragover'), false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.remove('dragover'), false);
    });
    
    dropArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if(files.length) {
            fileUpload.files = files;
            updateFileName();
        }
    }, false);
    
    fileUpload.addEventListener('change', updateFileName);
    
    function updateFileName() {
        if(fileUpload.files.length > 0) {
            fileNameDisplay.textContent = fileUpload.files[0].name;
            fileNameDisplay.style.animation = 'fadeIn 0.3s ease';
        } else {
            fileNameDisplay.textContent = '';
        }
    }
    
    // Fetch available roles from Backend
    async function fetchCategories() {
        try {
            const res = await fetch(`${API_URL}/api/categories`);
            if (!res.ok) throw new Error('Failed to load roles');
            const data = await res.json();
            
            roleSelect.innerHTML = '<option value="" disabled selected>Select a role...</option>';
            data.categories.forEach(cat => {
                const opt = document.createElement('option');
                opt.value = cat;
                opt.textContent = cat;
                roleSelect.appendChild(opt);
            });
        } catch (err) {
            console.error(err);
            roleSelect.innerHTML = '<option value="" disabled selected>Error loading roles</option>';
        }
    }
    
    // Handle Form Submit
    analyzeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const file = fileUpload.files[0];
        const role = roleSelect.value;
        
        if (!file || !role) return;
        
        // Show loading state
        analyzeBtn.classList.add('loading');
        analyzeBtn.disabled = true;
        
        hideAllResults();
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('target_role', role);
        
        try {
            const res = await fetch(`${API_URL}/api/analyze`, {
                method: 'POST',
                body: formData
            });
            
            const data = await res.json();
            
            if (!res.ok) {
                throw new Error(data.error || 'Server error occurred');
            }
            
            displayResults(data);
            
        } catch (err) {
            errorMessage.textContent = err.message;
            errorState.classList.remove('hidden');
        } finally {
            analyzeBtn.classList.remove('loading');
            analyzeBtn.disabled = false;
        }
    });
    
    function hideAllResults() {
        emptyState.classList.add('hidden');
        errorState.classList.add('hidden');
        resultsContent.classList.add('hidden');
    }
    
    function displayResults(data) {
        const { score, matched_skills, missing_skills } = data;
        
        // Show result container
        resultsContent.classList.remove('hidden');
        
        // Render Gauge Chart using Plotly
        renderGaugeChart(score);
        
        // Suitability Message
        const msgDiv = document.getElementById('suitability-message');
        msgDiv.className = 'suitability-alert';
        
        if (score >= 75) {
            msgDiv.classList.add('alert-success');
            msgDiv.innerHTML = '🌟 <strong>Strong Fit:</strong> This candidate is highly suitable for the role based on keyword matching.';
        } else if (score >= 50) {
            msgDiv.classList.add('alert-warning');
            msgDiv.innerHTML = '👍 <strong>Moderate Fit:</strong> The candidate has some relevant skills but may require additional training.';
        } else {
            msgDiv.classList.add('alert-danger');
            msgDiv.innerHTML = '⚠️ <strong>Weak Fit:</strong> This candidate is currently lacking many foundational skills for the role.';
        }
        
        // Render Skills Lists
        renderList('matched-skills-list', matched_skills, 'No major skills matched.');
        renderList('missing-skills-list', missing_skills, 'Candidate possesses all top industry keywords!');
    }
    
    function renderGaugeChart(score) {
        const containerInfo = document.getElementById('gauge-container').getBoundingClientRect();
        
        let barColor = "rgba(239, 68, 68, 0.8)"; // red
        if (score >= 70) barColor = "rgba(16, 185, 129, 0.8)"; // emerald/green
        else if (score >= 40) barColor = "rgba(245, 158, 11, 0.8)"; // amber/orange
            
        const data = [
          {
            domain: { x: [0, 1], y: [0, 1] },
            value: score,
            title: { text: "Suitability Score", font: { size: 18, color: '#f8fafc' } },
            type: "indicator",
            mode: "gauge+number",
            number: { font: { color: '#f8fafc' }, valueformat: ".1f", suffix: "%" },
            gauge: {
              axis: { range: [null, 100], tickwidth: 1, tickcolor: "#475569" },
              bar: { color: barColor },
              bgcolor: "transparent",
              borderwidth: 0,
              steps: [
                { range: [0, 40], color: "rgba(239, 68, 68, 0.1)" },
                { range: [40, 70], color: "rgba(245, 158, 11, 0.1)" },
                { range: [70, 100], color: "rgba(16, 185, 129, 0.1)" }
              ]
            }
          }
        ];

        const layout = { 
            width: containerInfo.width, 
            height: 300, 
            margin: { t: 50, b: 20, l: 20, r: 20 },
            paper_bgcolor: "transparent",
            font: { color: "#f8fafc", family: "Outfit, sans-serif" }
        };

        Plotly.newPlot('gauge-container', data, layout, {displayModeBar: false, responsive: true});
    }
    
    function renderList(elementId, items, emptyMessage) {
        const ul = document.getElementById(elementId);
        ul.innerHTML = '';
        
        // Take top 15 items
        const displayItems = items.slice(0, 15);
        if (displayItems.length === 0) {
            const li = document.createElement('li');
            li.style.color = 'var(--text-muted)';
            li.style.border = 'none';
            li.style.fontStyle = 'italic';
            li.textContent = emptyMessage;
            li.style.setProperty('--before-content', 'none'); // Hide bullet
            li.className = "empty-list-msg";
            ul.appendChild(li);
            return;
        }
        
        displayItems.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            ul.appendChild(li);
        });
    }
});
