// Dashboard JavaScript

let requestsChart = null;
let latencyChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    loadProjectInfo();
    loadSystemStatus();
    loadSampleQueries();
    initializeGrafanaCharts();
    
    // Auto-refresh system status every 30 seconds
    setInterval(loadSystemStatus, 30000);
    setInterval(updateGrafanaCharts, 10000);
});

// Tab Management
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            // Remove active class from all buttons and contents
            tabButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            btn.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });
}

// Load Project Info
async function loadProjectInfo() {
    try {
        const response = await fetch('/api/project-info');
        const data = await response.json();
        
        // Populate bugs list
        const bugsList = document.getElementById('bugs-list');
        bugsList.innerHTML = '';
        data.bugs.forEach((bug, index) => {
            const bugItem = document.createElement('div');
            bugItem.className = 'bug-item';
            bugItem.innerHTML = `
                <h4>Bug #${index + 1}</h4>
                <p>${bug}</p>
            `;
            bugsList.appendChild(bugItem);
        });
        
        // Populate layers grid
        const layersGrid = document.getElementById('layers-grid');
        layersGrid.innerHTML = '';
        data.architecture.layers.forEach(layer => {
            const layerCard = document.createElement('div');
            layerCard.className = 'layer-card';
            layerCard.innerHTML = `
                <h4>${layer.name}</h4>
                <p class="layer-desc">${layer.description}</p>
                <span class="layer-component">${layer.component}</span>
            `;
            layersGrid.appendChild(layerCard);
        });
        
        // Populate components grid
        const componentsGrid = document.getElementById('components-grid');
        componentsGrid.innerHTML = '';
        data.components.forEach(component => {
            const componentItem = document.createElement('div');
            componentItem.className = 'component-item';
            const icon = getComponentIcon(component);
            componentItem.innerHTML = `
                <div class="component-icon">${icon}</div>
                <div class="component-name">${component}</div>
            `;
            componentsGrid.appendChild(componentItem);
        });
    } catch (error) {
        console.error('Error loading project info:', error);
    }
}

function getComponentIcon(component) {
    const icons = {
        'Frontend': '🖥️',
        'Backend': '⚙️',
        'Database': '🗄️',
        'Monitoring': '📊',
        'Service Mesh': '🌐'
    };
    for (const [key, icon] of Object.entries(icons)) {
        if (component.includes(key)) return icon;
    }
    return '📦';
}

// Load System Status
async function loadSystemStatus() {
    try {
        const response = await fetch('/api/system-status');
        const data = await response.json();
        
        // Populate pods table
        const podsTbody = document.getElementById('pods-tbody');
        podsTbody.innerHTML = '';
        Object.entries(data.pods).forEach(([name, info]) => {
            const row = document.createElement('tr');
            const statusClass = info.status === 'Running' ? 'status-running' : 'status-pending';
            row.innerHTML = `
                <td>${name}</td>
                <td><span class="status-badge ${statusClass}">${info.status}</span></td>
                <td>${info.ready}</td>
                <td>${info.restarts}</td>
                <td>${info.age}</td>
            `;
            podsTbody.appendChild(row);
        });
        
        // Populate services table
        const servicesTbody = document.getElementById('services-tbody');
        servicesTbody.innerHTML = '';
        Object.entries(data.services).forEach(([name, info]) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${name}</td>
                <td>${info.type}</td>
                <td>${info.ports}</td>
            `;
            servicesTbody.appendChild(row);
        });
        
        // Populate ingress table
        const ingressTbody = document.getElementById('ingress-tbody');
        ingressTbody.innerHTML = '';
        Object.entries(data.ingress).forEach(([name, info]) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${name}</td>
                <td>${info.hosts}</td>
                <td>${info.address}</td>
            `;
            ingressTbody.appendChild(row);
        });
        
        // Update counts
        document.getElementById('netpol-count').textContent = data.network_policies;
        document.getElementById('vs-count').textContent = data.istio_resources.virtualservices;
        document.getElementById('dr-count').textContent = data.istio_resources.destinationrules;
    } catch (error) {
        console.error('Error loading system status:', error);
    }
}

// Prometheus Query Functions
async function loadSampleQueries() {
    try {
        const response = await fetch('/api/prometheus/queries');
        const queries = await response.json();
        
        const queriesList = document.getElementById('sample-queries-list');
        queriesList.innerHTML = '';
        
        Object.entries(queries).forEach(([key, query]) => {
            const queryItem = document.createElement('div');
            queryItem.className = 'sample-query-item';
            queryItem.innerHTML = `
                <h4>${key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h4>
                <div class="query-text">${query.query}</div>
                <div class="query-desc">${query.description}</div>
            `;
            queryItem.addEventListener('click', () => {
                document.getElementById('query-input').value = query.query;
            });
            queriesList.appendChild(queryItem);
        });
    } catch (error) {
        console.error('Error loading sample queries:', error);
    }
}

async function executeQuery() {
    const queryInput = document.getElementById('query-input');
    const query = queryInput.value.trim();
    
    if (!query) {
        alert('Please enter a query');
        return;
    }
    
    const resultsDiv = document.getElementById('query-results');
    resultsDiv.innerHTML = '<p>Executing query...</p>';
    
    try {
        const response = await fetch('/api/prometheus/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });
        
        const data = await response.json();
        
        // Format and display results
        resultsDiv.textContent = JSON.stringify(data, null, 2);
        
        // Highlight JSON syntax
        resultsDiv.style.color = '#d4d4d4';
    } catch (error) {
        resultsDiv.innerHTML = `<p style="color: #e63946;">Error executing query: ${error.message}</p>`;
    }
}

// Grafana Chart Functions
async function initializeGrafanaCharts() {
    await updateGrafanaCharts();
}

async function updateGrafanaCharts() {
    try {
        const response = await fetch('/api/grafana/metrics');
        const data = await response.json();
        
        // Update requests chart
        updateRequestsChart(data.http_requests_total);
        
        // Update latency chart
        updateLatencyChart(data.http_request_duration_seconds);
        
        // Update metrics summary
        updateMetricsSummary(data);
    } catch (error) {
        console.error('Error updating Grafana charts:', error);
    }
}

function updateRequestsChart(data) {
    const ctx = document.getElementById('requests-chart').getContext('2d');
    
    const labels = data.map(d => {
        const date = new Date(d.timestamp);
        return date.toLocaleTimeString();
    });
    const values = data.map(d => d.value);
    
    if (requestsChart) {
        requestsChart.data.labels = labels;
        requestsChart.data.datasets[0].data = values;
        requestsChart.update();
    } else {
        requestsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'HTTP Requests',
                    data: values,
                    borderColor: '#00a896',
                    backgroundColor: 'rgba(0, 168, 150, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                }
            }
        });
    }
}

function updateLatencyChart(data) {
    const ctx = document.getElementById('latency-chart').getContext('2d');
    
    const labels = data.map(d => {
        const date = new Date(d.timestamp);
        return date.toLocaleTimeString();
    });
    const values = data.map(d => d.value);
    
    if (latencyChart) {
        latencyChart.data.labels = labels;
        latencyChart.data.datasets[0].data = values;
        latencyChart.update();
    } else {
        latencyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Request Duration (seconds)',
                    data: values,
                    borderColor: '#f77f00',
                    backgroundColor: 'rgba(247, 127, 0, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                }
            }
        });
    }
}

function updateMetricsSummary(data) {
    const requests = data.http_requests_total;
    const latencies = data.http_request_duration_seconds;
    
    // Calculate totals
    const totalRequests = requests.reduce((sum, d) => sum + d.value, 0);
    const avgLatency = latencies.reduce((sum, d) => sum + d.value, 0) / latencies.length;
    const maxLatency = Math.max(...latencies.map(d => d.value));
    const requestRate = totalRequests / 60; // requests per minute
    
    document.getElementById('total-requests').textContent = Math.round(totalRequests).toLocaleString();
    document.getElementById('avg-latency').textContent = avgLatency.toFixed(3) + 's';
    document.getElementById('max-latency').textContent = maxLatency.toFixed(3) + 's';
    document.getElementById('request-rate').textContent = requestRate.toFixed(1) + '/min';
}

