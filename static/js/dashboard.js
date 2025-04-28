/**
 * Dashboard functionality for the Financial Risk Knowledge Graph system
 */

// Initialize timeline visualization
function initializeTimeline(containerId, timelineData) {
    const container = document.getElementById(containerId);
    
    if (!container || !timelineData || timelineData.length === 0) {
        return;
    }
    
    // Prepare data for Chart.js timeline
    const eventsByDate = {};
    
    // Group events by date
    timelineData.forEach(event => {
        const date = event.start.split('T')[0]; // Extract date part
        if (!eventsByDate[date]) {
            eventsByDate[date] = [];
        }
        eventsByDate[date].push(event);
    });
    
    // Convert to arrays for Chart.js
    const dates = Object.keys(eventsByDate).sort();
    const eventCounts = dates.map(date => eventsByDate[date].length);
    
    // Format dates for display
    const formattedDates = dates.map(date => {
        const d = new Date(date);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    
    // Create chart
    const ctx = container.getContext('2d');
    
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: formattedDates,
            datasets: [{
                label: 'Events',
                data: eventCounts,
                backgroundColor: '#fd7e14',
                borderColor: '#fd7e14',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        color: '#fff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: '#fff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const date = dates[context.dataIndex];
                            const events = eventsByDate[date];
                            return events.map(e => '• ' + e.title);
                        }
                    }
                },
                legend: {
                    labels: {
                        color: '#fff'
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const date = dates[index];
                    const events = eventsByDate[date];
                    
                    // Show event details in a modal
                    showEventsModal(date, events);
                }
            }
        }
    });
    
    // Function to show events in a modal
    function showEventsModal(date, events) {
        // Create modal if it doesn't exist
        let modal = document.getElementById('events-modal');
        
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'events-modal';
            modal.className = 'modal fade';
            modal.setAttribute('tabindex', '-1');
            modal.setAttribute('aria-hidden', 'true');
            
            modal.innerHTML = `
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Events on <span id="event-date"></span></h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" id="events-list">
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
        }
        
        // Populate modal with event details
        const formattedDate = new Date(date).toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
        
        document.getElementById('event-date').textContent = formattedDate;
        
        const eventsList = document.getElementById('events-list');
        eventsList.innerHTML = '';
        
        events.forEach(event => {
            const eventElement = document.createElement('div');
            eventElement.className = 'card mb-3';
            eventElement.innerHTML = `
                <div class="card-body">
                    <h5 class="card-title">${event.title}</h5>
                    <h6 class="card-subtitle mb-2 text-muted">${event.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</h6>
                    <p class="card-text">${event.content}</p>
                </div>
            `;
            eventsList.appendChild(eventElement);
        });
        
        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
}

// Initialize graph preview visualization
function initializeGraphPreview(containerId, graphData) {
    const container = document.getElementById(containerId);
    
    if (!container || !graphData || !graphData.nodes || graphData.nodes.length === 0) {
        container.innerHTML = '<div class="alert alert-secondary">No graph data available</div>';
        return;
    }
    
    // Limit the number of nodes for the preview
    const maxPreviewNodes = 50;
    let previewNodes = graphData.nodes;
    let previewEdges = graphData.edges;
    
    if (graphData.nodes.length > maxPreviewNodes) {
        // Sample nodes from each layer
        const entityNodes = graphData.nodes.filter(n => n.layer === 'entity').slice(0, 20);
        const eventNodes = graphData.nodes.filter(n => n.layer === 'event').slice(0, 15);
        const riskNodes = graphData.nodes.filter(n => n.layer === 'risk').slice(0, 15);
        
        previewNodes = [...entityNodes, ...eventNodes, ...riskNodes];
        
        // Get edges between these nodes
        const nodeIds = new Set(previewNodes.map(n => n.id));
        previewEdges = graphData.edges.filter(e => 
            nodeIds.has(e.source) && nodeIds.has(e.target)
        );
    }
    
    // Create network nodes and edges
    const nodes = new vis.DataSet(
        previewNodes.map(node => ({
            id: node.id,
            label: node.label || '',
            title: node.title || node.label || '',
            group: node.layer,
            color: getNodeColor(node.layer),
            shape: 'dot',
            size: getNodeSize(node)
        }))
    );
    
    const edges = new vis.DataSet(
        previewEdges.map(edge => ({
            from: edge.source,
            to: edge.target,
            color: {
                color: getEdgeColor(edge.layer),
                highlight: '#ffffff'
            },
            width: edge.weight ? (edge.weight * 3) : 1,
            arrows: {
                to: {
                    enabled: true,
                    scaleFactor: 0.5
                }
            }
        }))
    );
    
    // Network configuration
    const options = {
        nodes: {
            font: {
                color: '#ffffff',
                size: 10
            }
        },
        edges: {
            smooth: {
                type: 'continuous'
            }
        },
        physics: {
            stabilization: {
                iterations: 100
            },
            barnesHut: {
                gravitationalConstant: -2000,
                centralGravity: 0.3,
                springLength: 95,
                springConstant: 0.04
            }
        },
        groups: {
            entity: {
                color: {
                    background: '#ffc107',
                    border: '#fff',
                    highlight: {
                        background: '#ffda6a',
                        border: '#fff'
                    }
                }
            },
            event: {
                color: {
                    background: '#fd7e14',
                    border: '#fff',
                    highlight: {
                        background: '#feb272',
                        border: '#fff'
                    }
                }
            },
            risk: {
                color: {
                    background: '#dc3545',
                    border: '#fff',
                    highlight: {
                        background: '#ef7784',
                        border: '#fff'
                    }
                }
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 200
        }
    };
    
    // Initialize network
    const network = new vis.Network(container, { nodes, edges }, options);
    
    // Helper functions
    function getNodeColor(layer) {
        switch (layer) {
            case 'entity': return { background: '#ffc107', border: '#fff' };
            case 'event': return { background: '#fd7e14', border: '#fff' };
            case 'risk': return { background: '#dc3545', border: '#fff' };
            default: return { background: '#6c757d', border: '#fff' };
        }
    }
    
    function getEdgeColor(layer) {
        switch (layer) {
            case 'entity': return 'rgba(255, 193, 7, 0.6)';
            case 'event': return 'rgba(253, 126, 20, 0.6)';
            case 'risk': return 'rgba(220, 53, 69, 0.6)';
            case 'event_to_entity': return 'rgba(253, 126, 20, 0.4)';
            case 'risk_to_entity': return 'rgba(220, 53, 69, 0.4)';
            case 'event_to_risk': return 'rgba(237, 91, 45, 0.4)';
            default: return 'rgba(108, 117, 125, 0.6)';
        }
    }
    
    function getNodeSize(node) {
        // Base size by layer
        let size = 10;
        
        switch (node.layer) {
            case 'entity':
                size = 15;
                if (node.mentions > 5) size += 5;
                if (node.mentions > 10) size += 5;
                break;
            case 'event':
                size = 20;
                if (node.entities > 3) size += 5;
                break;
            case 'risk':
                size = 25;
                if (node.severity > 3) size += 5;
                break;
        }
        
        return size;
    }
}
