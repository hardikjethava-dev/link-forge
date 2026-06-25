document.addEventListener('DOMContentLoaded', () => {
    // 1. Copy to Clipboard Functionality
    const copyBtn = document.getElementById('btn-copy-short-url');
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            const textToCopy = copyBtn.getAttribute('data-url');
            if (textToCopy) {
                navigator.clipboard.writeText(textToCopy).then(() => {
                    const originalHTML = copyBtn.innerHTML;
                    copyBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
                    copyBtn.style.background = '#10b981'; // green success color
                    
                    setTimeout(() => {
                        copyBtn.innerHTML = originalHTML;
                        copyBtn.style.background = ''; // Revert to CSS default
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy text: ', err);
                });
            }
        });
    }

    // 2. Tabbed Dynamic Chart.js Analytics (Dashboard)
    const chartCanvas = document.getElementById('clicks-trend-chart');
    if (chartCanvas && typeof Chart !== 'undefined') {
        const dailyData = JSON.parse(document.getElementById('daily-data-json').textContent);
        const weeklyData = JSON.parse(document.getElementById('weekly-data-json').textContent);
        const monthlyData = JSON.parse(document.getElementById('monthly-data-json').textContent);

        let activeChartType = 'daily';
        
        // Helper to format chart parameters
        const getChartParams = (type) => {
            let dataSrc = dailyData;
            if (type === 'weekly') dataSrc = weeklyData;
            if (type === 'monthly') dataSrc = monthlyData;
            
            return {
                labels: dataSrc.map(item => item.label),
                values: dataSrc.map(item => item.value)
            };
        };

        const initialParams = getChartParams('daily');
        const ctx = chartCanvas.getContext('2d');
        
        // Custom styling gradient for chart fill
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(99, 102, 241, 0.35)');
        gradient.addColorStop(1, 'rgba(99, 102, 241, 0.00)');

        const clickTrendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: initialParams.labels,
                datasets: [{
                    label: 'Clicks',
                    data: initialParams.values,
                    borderColor: '#6366f1',
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.3,
                    borderWidth: 3,
                    pointBackgroundColor: '#818cf8',
                    pointBorderColor: '#6366f1',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: '#f8fafc'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#0f172a',
                        titleColor: '#f8fafc',
                        bodyColor: '#cbd5e1',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: false,
                        titleFont: {
                            family: "'Outfit', sans-serif",
                            weight: 'bold'
                        },
                        bodyFont: {
                            family: "'Plus Jakarta Sans', sans-serif"
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#64748b',
                            font: {
                                family: "'Plus Jakarta Sans', sans-serif",
                                size: 11
                            }
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.04)'
                        },
                        ticks: {
                            color: '#64748b',
                            precision: 0,
                            font: {
                                family: "'Plus Jakarta Sans', sans-serif",
                                size: 11
                            }
                        },
                        beginAtZero: true
                    }
                }
            }
        });

        // Tab Switching Click Listeners
        const tabs = document.querySelectorAll('.chart-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                // Remove active classes
                tabs.forEach(t => t.classList.remove('active'));
                
                // Add active to clicked tab
                tab.classList.add('active');
                
                const type = tab.getAttribute('data-type');
                if (type && type !== activeChartType) {
                    activeChartType = type;
                    const params = getChartParams(type);
                    
                    // Update Chart Data and Redraw
                    clickTrendChart.data.labels = params.labels;
                    clickTrendChart.data.datasets[0].data = params.values;
                    clickTrendChart.update();
                }
            });
        });

        // Expose helper to update chart colors dynamically on theme switch
        window.updateChartColors = (theme) => {
            const isLight = theme === 'light';
            const gridColor = isLight ? 'rgba(15, 23, 42, 0.06)' : 'rgba(255, 255, 255, 0.04)';
            const lineColor = isLight ? '#2563eb' : '#6366f1';
            const ptColor = isLight ? '#60a5fa' : '#818cf8';
            
            // Re-create gradient for fill
            const newGradient = ctx.createLinearGradient(0, 0, 0, 300);
            if (isLight) {
                newGradient.addColorStop(0, 'rgba(37, 99, 235, 0.20)');
                newGradient.addColorStop(1, 'rgba(37, 99, 235, 0.00)');
            } else {
                newGradient.addColorStop(0, 'rgba(99, 102, 241, 0.35)');
                newGradient.addColorStop(1, 'rgba(99, 102, 241, 0.00)');
            }
            
            clickTrendChart.options.scales.y.grid.color = gridColor;
            clickTrendChart.data.datasets[0].borderColor = lineColor;
            clickTrendChart.data.datasets[0].backgroundColor = newGradient;
            clickTrendChart.data.datasets[0].pointBackgroundColor = ptColor;
            clickTrendChart.data.datasets[0].pointBorderColor = lineColor;
            clickTrendChart.update();
        };

        // If page loads in light mode, run it
        const initialTheme = document.documentElement.getAttribute('data-theme') || 'dark';
        if (initialTheme === 'light') {
            window.updateChartColors('light');
        }
    }

    // 3. Theme Toggle Switch Click Listener
    const themeToggleBtn = document.getElementById('theme-toggle');
    if (themeToggleBtn) {
        const updateThemeIcon = (theme) => {
            const icon = themeToggleBtn.querySelector('i');
            if (icon) {
                if (theme === 'light') {
                    icon.className = 'fa-solid fa-moon';
                } else {
                    icon.className = 'fa-solid fa-sun';
                }
            }
        };

        const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
        updateThemeIcon(currentTheme);

        themeToggleBtn.addEventListener('click', () => {
            const activeTheme = document.documentElement.getAttribute('data-theme') || 'dark';
            const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);

            if (window.updateChartColors) {
                window.updateChartColors(newTheme);
            }
        });
    }
});
