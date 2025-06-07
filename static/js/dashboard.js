// Dashboard JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard components
    initializeCharts();
    initializeRealTimeUpdates();
    initializeAnimations();
    setupEventListeners();
});

// Chart initialization and management
function initializeCharts() {
    // Set default chart configuration
    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    
    // Apply dark theme if active
    if (document.documentElement.getAttribute('data-bs-theme') === 'dark') {
        Chart.defaults.color = '#dee2e6';
        Chart.defaults.borderColor = '#495057';
        Chart.defaults.backgroundColor = 'rgba(108, 117, 125, 0.1)';
    }
}

// Real-time updates for dashboard statistics
function initializeRealTimeUpdates() {
    // Update dashboard stats every 30 seconds
    setInterval(updateDashboardStats, 30000);
    
    // Initial update
    updateDashboardStats();
}

function updateDashboardStats() {
    fetch('/api/dashboard_stats')
        .then(response => response.json())
        .then(data => {
            updateStatCards(data);
            updateCharts(data);
        })
        .catch(error => {
            console.error('Error fetching dashboard stats:', error);
        });
}

function updateStatCards(data) {
    // Update stat cards with animation
    const statCards = document.querySelectorAll('.stat-card .h4');
    statCards.forEach(card => {
        const currentValue = parseInt(card.textContent);
        const newValue = getNewValue(card, data);
        
        if (newValue !== currentValue) {
            animateCounter(card, currentValue, newValue);
        }
    });
}

function animateCounter(element, start, end) {
    const duration = 1000;
    const increment = (end - start) / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

function getNewValue(card, data) {
    // Extract new value based on card type
    const cardContainer = card.closest('.stat-card');
    const cardText = cardContainer.querySelector('.small').textContent.toLowerCase();
    
    if (cardText.includes('students')) return data.total_students || 0;
    if (cardText.includes('certificates')) return data.total_certificates || 0;
    if (cardText.includes('sent')) return data.sent_certificates || 0;
    if (cardText.includes('success')) return data.success_rate || 0;
    
    return parseInt(card.textContent);
}

function updateCharts(data) {
    // Update existing charts with new data
    Chart.helpers.each(Chart.instances, function(chart) {
        if (chart.canvas.id === 'generationChart') {
            updateGenerationChart(chart, data.daily_generation);
        } else if (chart.canvas.id === 'statusChart') {
            updateStatusChart(chart, data.status_distribution);
        }
    });
}

function updateGenerationChart(chart, data) {
    if (data && data.length > 0) {
        chart.data.labels = data.map(item => formatDate(item.date));
        chart.data.datasets[0].data = data.map(item => item.count);
        chart.update('none');
    }
}

function updateStatusChart(chart, data) {
    if (data && data.length > 0) {
        chart.data.labels = data.map(item => capitalizeFirst(item.status));
        chart.data.datasets[0].data = data.map(item => item.count);
        chart.update('none');
    }
}

// Animation effects for dashboard elements
function initializeAnimations() {
    // Animate cards on page load
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Animate statistics on scroll
    observeStatCards();
}

function observeStatCards() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-stat');
                animateStatValue(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    document.querySelectorAll('.stat-card').forEach(card => {
        observer.observe(card);
    });
}

function animateStatValue(card) {
    const valueElement = card.querySelector('.h4');
    const finalValue = parseInt(valueElement.textContent);
    
    if (!isNaN(finalValue)) {
        valueElement.textContent = '0';
        animateCounter(valueElement, 0, finalValue);
    }
}

// Event listeners for dashboard interactions
function setupEventListeners() {
    // Refresh button functionality
    const refreshBtn = document.getElementById('refreshStats');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Refreshing...';
            this.disabled = true;
            
            updateDashboardStats();
            
            setTimeout(() => {
                this.innerHTML = '<i class="fas fa-sync me-1"></i>Refresh';
                this.disabled = false;
            }, 2000);
        });
    }
    
    // Export functionality
    const exportBtn = document.getElementById('exportReport');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportDashboardReport);
    }
    
    // Filter functionality
    setupFilterListeners();
    
    // Card hover effects
    setupCardHoverEffects();
    
    // Progress tracking
    setupProgressTracking();
}

function setupFilterListeners() {
    const filterSelects = document.querySelectorAll('.filter-select');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            const filterType = this.dataset.filter;
            const filterValue = this.value;
            applyDashboardFilter(filterType, filterValue);
        });
    });
}

function applyDashboardFilter(type, value) {
    // Apply filters to dashboard data
    console.log(`Applying filter: ${type} = ${value}`);
    // Implementation would depend on specific filtering requirements
}

function setupCardHoverEffects() {
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 8px 25px rgba(0,0,0,0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
        });
    });
}

function setupProgressTracking() {
    // Track bulk operations progress
    const progressElements = document.querySelectorAll('.progress-tracker');
    progressElements.forEach(element => {
        const batchId = element.dataset.batchId;
        if (batchId) {
            trackBatchProgress(batchId, element);
        }
    });
}

function trackBatchProgress(batchId, element) {
    const interval = setInterval(() => {
        fetch(`/api/upload_progress/${batchId}`)
            .then(response => response.json())
            .then(data => {
                updateProgressElement(element, data);
                
                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(interval);
                    handleProgressComplete(element, data);
                }
            })
            .catch(error => {
                console.error('Error tracking progress:', error);
                clearInterval(interval);
            });
    }, 2000);
}

function updateProgressElement(element, data) {
    const progressBar = element.querySelector('.progress-bar');
    const progressText = element.querySelector('.progress-text');
    
    if (progressBar) {
        progressBar.style.width = `${data.progress_percentage}%`;
        progressBar.setAttribute('aria-valuenow', data.progress_percentage);
    }
    
    if (progressText) {
        progressText.textContent = `${data.processed_records}/${data.total_records} processed`;
    }
}

function handleProgressComplete(element, data) {
    const statusClass = data.status === 'completed' ? 'bg-success' : 'bg-danger';
    const progressBar = element.querySelector('.progress-bar');
    
    if (progressBar) {
        progressBar.className = `progress-bar ${statusClass}`;
        progressBar.style.width = '100%';
    }
    
    // Show completion notification
    showNotification(
        data.status === 'completed' ? 'success' : 'error',
        `Batch processing ${data.status}: ${data.successful_records} successful, ${data.failed_records} failed`
    );
}

// Export functionality
function exportDashboardReport() {
    const reportData = gatherReportData();
    const csvContent = generateCSVReport(reportData);
    downloadCSV(csvContent, 'dashboard-report.csv');
}

function gatherReportData() {
    // Gather all dashboard data for export
    const stats = {
        timestamp: new Date().toISOString(),
        total_students: getStatValue('Total Students'),
        total_certificates: getStatValue('Certificates Generated'),
        sent_certificates: getStatValue('Certificates Sent'),
        success_rate: getStatValue('Success Rate')
    };
    
    return stats;
}

function getStatValue(label) {
    const cards = document.querySelectorAll('.stat-card');
    for (let card of cards) {
        const cardLabel = card.querySelector('.small').textContent;
        if (cardLabel.includes(label)) {
            return card.querySelector('.h4').textContent;
        }
    }
    return '0';
}

function generateCSVReport(data) {
    const headers = Object.keys(data).join(',');
    const values = Object.values(data).join(',');
    return `${headers}\n${values}`;
}

function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Notification system
function showNotification(type, message) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 1060; min-width: 300px;';
    
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Responsive chart handling
function handleChartResize() {
    Chart.helpers.each(Chart.instances, function(chart) {
        chart.resize();
    });
}

// Listen for window resize
window.addEventListener('resize', debounce(handleChartResize, 250));

// Debounce utility function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Dark mode chart updates
function updateChartsForTheme(isDark) {
    const textColor = isDark ? '#dee2e6' : '#495057';
    const borderColor = isDark ? '#495057' : '#dee2e6';
    
    Chart.helpers.each(Chart.instances, function(chart) {
        chart.options.plugins.legend.labels.color = textColor;
        chart.options.scales.x.ticks.color = textColor;
        chart.options.scales.y.ticks.color = textColor;
        chart.options.scales.x.grid.color = borderColor;
        chart.options.scales.y.grid.color = borderColor;
        chart.update('none');
    });
}

// Theme change listener
const themeObserver = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.attributeName === 'data-bs-theme') {
            const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
            updateChartsForTheme(isDark);
        }
    });
});

themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-bs-theme']
});
