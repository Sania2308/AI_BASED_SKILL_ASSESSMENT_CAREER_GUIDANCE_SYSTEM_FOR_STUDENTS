/**
 * SkillGuide Dashboard Visualizations using Chart.js
 * Radar Chart: Competency Profile
 * Bar Chart: Domain Scores vs Institutional Benchmark
 * Doughnut Chart: Target Career Readiness
 * Line Chart: Assessment Progress Timeline
 */

let radarChart = null;
let barChart = null;
let doughnutChart = null;
let lineChart = null;

async function initDashboardCharts() {
    try {
        const response = await fetch('/api/dashboard-charts');
        if (!response.ok) return;
        const data = await response.json();

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const textColor = isDark ? '#94a3b8' : '#64748b';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';

        // 1. Radar Chart: Skill Profile
        const radarCanvas = document.getElementById('skillRadarChart');
        if (radarCanvas) {
            radarChart = new Chart(radarCanvas, {
                type: 'radar',
                data: {
                    labels: data.radar.labels,
                    datasets: [{
                        label: 'Your Competency Score',
                        data: data.radar.data,
                        backgroundColor: 'rgba(79, 70, 229, 0.25)',
                        borderColor: '#4f46e5',
                        borderWidth: 2,
                        pointBackgroundColor: '#7c3aed',
                        pointBorderColor: '#fff',
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            min: 0,
                            max: 100,
                            ticks: { stepSize: 20, color: textColor, backdropColor: 'transparent' },
                            grid: { color: gridColor },
                            angleLines: { color: gridColor },
                            pointLabels: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' } }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }

        // 2. Bar Chart: Domain Scores & Academic Benchmark
        const barCanvas = document.getElementById('domainBarChart');
        if (barCanvas) {
            barChart = new Chart(barCanvas, {
                type: 'bar',
                data: {
                    labels: data.bar.labels,
                    datasets: [
                        {
                            label: 'Your Score',
                            data: data.bar.student,
                            backgroundColor: '#4f46e5',
                            borderRadius: 6
                        },
                        {
                            label: 'Industry Target',
                            data: data.bar.benchmark,
                            backgroundColor: isDark ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.12)',
                            borderRadius: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            min: 0,
                            max: 100,
                            ticks: { color: textColor },
                            grid: { color: gridColor }
                        },
                        x: {
                            ticks: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 11 } },
                            grid: { display: false }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: { color: textColor, boxWidth: 12 }
                        }
                    }
                }
            });
        }

        // 3. Doughnut Chart: Target Role Readiness
        const doughnutCanvas = document.getElementById('readinessDoughnutChart');
        if (doughnutCanvas) {
            doughnutChart = new Chart(doughnutCanvas, {
                type: 'doughnut',
                data: {
                    labels: ['Readiness', 'Gap'],
                    datasets: [{
                        data: [data.doughnut.readiness, data.doughnut.gap],
                        backgroundColor: ['#10b981', isDark ? '#1e293b' : '#f1f5f9'],
                        borderWidth: 0,
                        hoverOffset: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '76%',
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => ` ${ctx.label}: ${ctx.raw}%`
                            }
                        }
                    }
                }
            });
        }

        // 4. Line Chart: Assessment Timeline
        const lineCanvas = document.getElementById('progressLineChart');
        if (lineCanvas) {
            lineChart = new Chart(lineCanvas, {
                type: 'line',
                data: {
                    labels: data.line.labels,
                    datasets: [{
                        label: 'Assessment Score (%)',
                        data: data.line.data,
                        borderColor: '#7c3aed',
                        backgroundColor: 'rgba(124, 58, 237, 0.12)',
                        borderWidth: 3,
                        tension: 0.35,
                        fill: true,
                        pointBackgroundColor: '#4f46e5',
                        pointBorderColor: '#fff',
                        pointRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            min: 0,
                            max: 100,
                            ticks: { color: textColor },
                            grid: { color: gridColor }
                        },
                        x: {
                            ticks: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 11 } },
                            grid: { color: gridColor }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
    } catch (e) {
        console.warn('Dashboard visualization error:', e);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('skillRadarChart')) {
        initDashboardCharts();
    }
});
