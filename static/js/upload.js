// Upload page functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeFileUpload();
    setupFormValidation();
    setupProgressTracking();
    initializeDragAndDrop();
});

// File upload initialization
function initializeFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    const filePreview = document.getElementById('filePreview');
    const submitBtn = document.getElementById('submitBtn');
    
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelection);
    }
    
    if (uploadArea) {
        uploadArea.addEventListener('click', () => fileInput.click());
    }
}

// Drag and drop functionality
function initializeDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');
    
    if (!uploadArea) return;
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    uploadArea.addEventListener('drop', handleDrop, false);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight() {
    const uploadArea = document.getElementById('uploadArea');
    uploadArea.classList.add('dragover');
}

function unhighlight() {
    const uploadArea = document.getElementById('uploadArea');
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length > 0) {
        const fileInput = document.getElementById('fileInput');
        fileInput.files = files;
        handleFileSelection();
    }
}

// File selection handling
function handleFileSelection() {
    const fileInput = document.getElementById('fileInput');
    const filePreview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');
    const fileInfo = document.getElementById('fileInfo');
    const submitBtn = document.getElementById('submitBtn');
    const uploadContent = document.getElementById('uploadContent');
    
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        
        // Validate file
        if (!validateFile(file)) {
            return;
        }
        
        // Show file preview
        fileName.textContent = file.name;
        fileInfo.textContent = `${formatFileSize(file.size)} • ${getFileExtension(file.name).toUpperCase()} file`;
        
        uploadContent.style.display = 'none';
        filePreview.style.display = 'block';
        submitBtn.disabled = false;
        
        // Preview file contents if possible
        previewFileContents(file);
        
    } else {
        resetFileSelection();
    }
}

function validateFile(file) {
    const allowedTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
        'application/vnd.ms-excel', // .xls
        'text/csv' // .csv
    ];
    
    const maxSize = 16 * 1024 * 1024; // 16MB
    
    if (!allowedTypes.includes(file.type) && !file.name.toLowerCase().endsWith('.csv')) {
        showAlert('error', 'Invalid file type. Please upload Excel (.xlsx, .xls) or CSV files only.');
        return false;
    }
    
    if (file.size > maxSize) {
        showAlert('error', 'File size too large. Maximum allowed size is 16MB.');
        return false;
    }
    
    return true;
}

function previewFileContents(file) {
    if (file.name.toLowerCase().endsWith('.csv')) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const csv = e.target.result;
            const lines = csv.split('\n').slice(0, 5); // First 5 lines
            showFilePreview(lines, 'CSV');
        };
        reader.readAsText(file);
    } else {
        showFilePreview(['Excel file selected - content preview not available'], 'Excel');
    }
}

function showFilePreview(lines, fileType) {
    const previewContainer = document.getElementById('fileContentPreview');
    if (previewContainer) {
        previewContainer.innerHTML = `
            <div class="mt-3">
                <h6>File Preview (${fileType}):</h6>
                <div class="bg-light p-2 rounded" style="font-family: monospace; font-size: 0.8rem; max-height: 100px; overflow-y: auto;">
                    ${lines.map(line => `<div>${escapeHtml(line.substring(0, 100))}${line.length > 100 ? '...' : ''}</div>`).join('')}
                </div>
            </div>
        `;
    }
}

function removeFile() {
    const fileInput = document.getElementById('fileInput');
    const filePreview = document.getElementById('filePreview');
    const uploadContent = document.getElementById('uploadContent');
    const submitBtn = document.getElementById('submitBtn');
    
    fileInput.value = '';
    filePreview.style.display = 'none';
    uploadContent.style.display = 'block';
    submitBtn.disabled = true;
    
    // Remove preview content
    const previewContainer = document.getElementById('fileContentPreview');
    if (previewContainer) {
        previewContainer.innerHTML = '';
    }
}

function resetFileSelection() {
    removeFile();
}

// Form validation
function setupFormValidation() {
    const uploadForm = document.getElementById('uploadForm');
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (validateForm()) {
                submitForm();
            }
        });
    }
}

function validateForm() {
    const fileInput = document.getElementById('fileInput');
    
    if (!fileInput.files.length) {
        showAlert('error', 'Please select a file to upload.');
        return false;
    }
    
    return validateFile(fileInput.files[0]);
}

function submitForm() {
    const form = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const progressContainer = document.getElementById('progressContainer');
    
    // Disable form and show progress
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
    
    if (progressContainer) {
        progressContainer.style.display = 'block';
        startProgressSimulation();
    }
    
    // Create FormData and submit
    const formData = new FormData(form);
    
    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            return response.text();
        }
        throw new Error('Network response was not ok');
    })
    .then(html => {
        // Handle successful response
        document.body.innerHTML = html;
        showAlert('success', 'File uploaded and processed successfully!');
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('error', 'An error occurred while processing the file. Please try again.');
        resetForm();
    });
}

// Progress tracking
function setupProgressTracking() {
    // This would be used with actual progress endpoints
    const progressElements = document.querySelectorAll('[data-batch-id]');
    progressElements.forEach(element => {
        const batchId = element.dataset.batchId;
        if (batchId) {
            trackUploadProgress(batchId);
        }
    });
}

function startProgressSimulation() {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 10;
        if (progress > 90) {
            progress = 90;
            clearInterval(interval);
        }
        
        updateProgress(progress, 'Processing file...');
    }, 500);
}

function trackUploadProgress(batchId) {
    const interval = setInterval(() => {
        fetch(`/api/upload_progress/${batchId}`)
            .then(response => response.json())
            .then(data => {
                updateProgress(data.progress_percentage, getProgressMessage(data));
                
                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(interval);
                    handleUploadComplete(data);
                }
            })
            .catch(error => {
                console.error('Error tracking progress:', error);
                clearInterval(interval);
            });
    }, 2000);
}

function updateProgress(percentage, message) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    
    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
        progressBar.setAttribute('aria-valuenow', percentage);
    }
    
    if (progressText) {
        progressText.textContent = message;
    }
}

function getProgressMessage(data) {
    if (data.status === 'completed') {
        return `Completed: ${data.successful_records} successful, ${data.failed_records} failed`;
    } else if (data.status === 'failed') {
        return 'Processing failed';
    } else {
        return `Processing: ${data.processed_records}/${data.total_records} records`;
    }
}

function handleUploadComplete(data) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    
    if (data.status === 'completed') {
        progressBar.className = 'progress-bar bg-success';
        progressBar.style.width = '100%';
        progressText.textContent = `Processing completed successfully!`;
        
        setTimeout(() => {
            window.location.href = '/admin/certificates';
        }, 2000);
    } else {
        progressBar.className = 'progress-bar bg-danger';
        progressText.textContent = 'Processing failed. Please try again.';
        
        setTimeout(() => {
            resetForm();
        }, 3000);
    }
}

function resetForm() {
    const submitBtn = document.getElementById('submitBtn');
    const progressContainer = document.getElementById('progressContainer');
    
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fas fa-upload me-2"></i>Upload and Process';
    
    if (progressContainer) {
        progressContainer.style.display = 'none';
    }
    
    removeFile();
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getFileExtension(filename) {
    return filename.slice((filename.lastIndexOf(".") - 1 >>> 0) + 2);
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

function showAlert(type, message) {
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alert.innerHTML = `
        <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at top of form
    const form = document.getElementById('uploadForm');
    if (form) {
        form.insertAdjacentElement('beforebegin', alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

// File format validation helper
function validateFileFormat(file) {
    const allowedExtensions = ['xlsx', 'xls', 'csv'];
    const fileExtension = getFileExtension(file.name).toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
        return {
            valid: false,
            message: `Invalid file format. Allowed formats: ${allowedExtensions.join(', ')}`
        };
    }
    
    return { valid: true };
}

// Advanced file validation
function performAdvancedValidation(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            try {
                const content = e.target.result;
                
                if (file.name.toLowerCase().endsWith('.csv')) {
                    validateCSVContent(content, resolve, reject);
                } else {
                    // For Excel files, basic validation
                    resolve({ valid: true });
                }
            } catch (error) {
                reject({ valid: false, message: 'Error reading file content' });
            }
        };
        
        reader.onerror = function() {
            reject({ valid: false, message: 'Error reading file' });
        };
        
        if (file.name.toLowerCase().endsWith('.csv')) {
            reader.readAsText(file);
        } else {
            reader.readAsArrayBuffer(file);
        }
    });
}

function validateCSVContent(content, resolve, reject) {
    const lines = content.split('\n');
    
    if (lines.length < 2) {
        reject({ valid: false, message: 'CSV file must contain header and at least one data row' });
        return;
    }
    
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    const requiredHeaders = ['student_name', 'roll_number', 'branch', 'college_name', 'email', 'internship_name'];
    
    const missingHeaders = requiredHeaders.filter(header => !headers.includes(header));
    
    if (missingHeaders.length > 0) {
        reject({
            valid: false,
            message: `Missing required columns: ${missingHeaders.join(', ')}`
        });
        return;
    }
    
    resolve({ valid: true });
}

// Sample data download functionality
function downloadSampleFile(format) {
    const sampleData = generateSampleData();
    
    if (format === 'csv') {
        downloadCSV(sampleData, 'sample_certificate_data.csv');
    } else {
        // For Excel, we'll provide a CSV for now since creating Excel files requires a library
        downloadCSV(sampleData, 'sample_certificate_data.csv');
    }
}

function generateSampleData() {
    const headers = [
        'Student Name', 'Roll Number', 'Branch', 'College Name', 'Email',
        'Internship Name', 'Internship Start Date', 'Internship End Date',
        'Phone Number', 'Duration Weeks', 'Mentor Name', 'Mentor Email',
        'Company Name', 'Internship Location', 'Performance Rating',
        'Skills Acquired', 'Project Title', 'Remarks'
    ];
    
    const sampleRows = [
        [
            'John Doe', 'CS001', 'Computer Science', 'ABC University', 'john.doe@email.com',
            'Web Development Internship', '2024-01-15', '2024-03-15',
            '+1234567890', '8', 'Jane Smith', 'jane.smith@company.com',
            'Tech Corp Ltd', 'New York', 'Excellent',
            'React, Node.js, MongoDB', 'E-commerce Platform Development', 'Outstanding performance'
        ],
        [
            'Jane Wilson', 'CS002', 'Computer Science', 'ABC University', 'jane.wilson@email.com',
            'Data Science Internship', '2024-02-01', '2024-04-01',
            '+1234567891', '8', 'Bob Johnson', 'bob.johnson@company.com',
            'Data Analytics Inc', 'San Francisco', 'Good',
            'Python, Pandas, Machine Learning', 'Customer Behavior Analysis', 'Good analytical skills'
        ]
    ];
    
    return [headers, ...sampleRows];
}

function downloadCSV(data, filename) {
    const csvContent = data.map(row => 
        row.map(cell => `"${cell.toString().replace(/"/g, '""')}"`).join(',')
    ).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}
