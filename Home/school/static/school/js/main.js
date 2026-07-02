/* ═══════════════════════════════════════════════════════
   SchoolMS — Main JavaScript
   ═══════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

    // ── Sidebar Toggle ──
    const sidebar = document.getElementById('sidebar');
    const hamburger = document.getElementById('hamburger');
    const sidebarClose = document.getElementById('sidebarClose');
    const mainContent = document.getElementById('mainContent');

    if (hamburger && sidebar) {
        hamburger.addEventListener('click', function () {
            sidebar.classList.toggle('open');
        });
    }

    if (sidebarClose && sidebar) {
        sidebarClose.addEventListener('click', function () {
            sidebar.classList.remove('open');
        });
    }

    // Close sidebar when clicking outside on mobile
    if (mainContent && sidebar) {
        mainContent.addEventListener('click', function () {
            if (window.innerWidth <= 768 && sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
            }
        });
    }

    // ── Auto-dismiss flash messages ──
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function (msg, index) {
        setTimeout(function () {
            msg.style.transition = 'opacity 0.5s, transform 0.5s';
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-10px)';
            setTimeout(function () {
                if (msg.parentNode) {
                    msg.remove();
                }
            }, 500);
        }, 4000 + (index * 500));
    });

    // ── Animate elements on scroll ──
    const animateElements = document.querySelectorAll('.stat-card, .chart-card, .info-card, .glass-card');
    animateElements.forEach(function (el) {
        el.classList.add('animate-in');
    });

});

/* ── Chart.js Initialization Helpers ── */

function initDoughnutChart(canvasId, labels, data, colors) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    return new Chart(canvas.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors || [
                    'rgba(102, 126, 234, 0.8)',
                    'rgba(236, 72, 153, 0.8)',
                    'rgba(52, 211, 153, 0.8)',
                ],
                borderColor: 'rgba(15, 15, 35, 0.8)',
                borderWidth: 3,
                hoverOffset: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#a0a0c0',
                        padding: 16,
                        font: {
                            family: "'Inter', sans-serif",
                            size: 12,
                        },
                        usePointStyle: true,
                        pointStyle: 'circle',
                    }
                }
            }
        }
    });
}

function initBarChart(canvasId, labels, data, label) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    return new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label || 'Count',
                data: data,
                backgroundColor: 'rgba(102, 126, 234, 0.6)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 1,
                borderRadius: 6,
                hoverBackgroundColor: 'rgba(102, 126, 234, 0.8)',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#6b6b8d',
                        font: { family: "'Inter', sans-serif" },
                        stepSize: 1,
                    },
                    grid: {
                        color: 'rgba(102, 126, 234, 0.06)',
                    }
                },
                x: {
                    ticks: {
                        color: '#6b6b8d',
                        font: { family: "'Inter', sans-serif" },
                    },
                    grid: {
                        display: false,
                    }
                }
            },
            plugins: {
                legend: {
                    display: false,
                }
            }
        }
    });
}
