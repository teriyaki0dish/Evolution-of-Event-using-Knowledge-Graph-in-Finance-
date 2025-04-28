// Global variables
let network = null;
let graphData = null;
let options = {
    nodes: {
        shape: 'dot',
        size: 20,
        font: {
            size: 14,
            color: '#ffffff'
        },
        borderWidth: 2,
        shadow: true
    },
    edges: {
        width: 2,
        color: {
            color: 'rgba(255, 255, 255, 0.5)',
            highlight: '#ffffff',
            hover: '#ffffff'
        },
        font: {
            size: 12,
            color: '#ffffff',
            strokeWidth: 0,
            background: 'rgba(33, 37, 41, 0.7)'
        },
        smooth: {
            type: 'continuous',
            forceDirection: 'none'
        }
    },
    physics: {
        enabled: true,
        barnesHut: {
            gravitationalConstant: -2000,
            centralGravity: 0.3,
            springLength: 150,
            springConstant: 0.04,
            damping: 0.09
        }
    },
    interaction: {
        hover: true,
        tooltipDelay: 200,
        navigationButtons: true,
        keyboard: true
    },
    layout: {
        improvedLayout: true
    },
    groups: {
        entity: {
            color: {
                background: '#3498db',
                border: '#2980b9',
                highlight: {
                    background: '#5faee3',
                    border: '#3498db'
                }
            }
        },
        event: {
            color: {
                background: '#e74c3c',
                border: '#c0392b',
                highlight: {
                    background: '#ec7063',
                    border: '#e74c3c'
                }
            }
        },
        risk: {
            color: {
                background: '#f39c12',
                border: '#d35400',
                highlight: {
                    background: '#f5b041',
                    border: '#f39c12'
                }
            }
        }
    }
};

// CSS variables for colors
document.documentElement.style.setProperty('--entity-color', '#3498db');
document.documentElement.style.setProperty('--event-color', '#e74c3c');
document.documentElement.style.setProperty('--risk-color', '#f39c12');

/**
 * Initialize the graph visualization
 * @param {string} containerId - DOM element ID for the graph container
 * @param {Object} data - Graph data from the API
 */
function initializeGraph(containerId, data) {
    // Check if there's an error message in the data
    if (data.error) {
        document.getElementById(containerId).innerHTML = 
            `<div class="alert alert-info p-5 m-5 text-center">
                <h4 class="alert-heading mb-4">No Knowledge Graph Data Available</h4>
                <p>${data.error}</p>
                <p>Use the data collection and processing pipeline to generate the knowledge graph.</p>
                <ol class="text-start mx-auto" style="max-width: 500px;">
                    <li>Go to the <strong>News</strong> tab to collect financial news</li>
                    <li>Use the "Process" button to extract entities, model events, and analyze risks</li>
                    <li>Return to this page to view the generated knowledge graph</li>
                </ol>
                <p class="mt-3">You can also use the "Process All" button on the dashboard to run the complete pipeline</p>
            </div>`;
        return;
    }

    // Check if there's no data or empty nodes
    if (!data || !data.nodes || data.nodes.length === 0) {
        document.getElementById(containerId).innerHTML = 
            `<div class="alert alert-info p-5 m-5 text-center">
                <h4 class="alert-heading mb-4">No Knowledge Graph Data Available</h4>
                <p>The knowledge graph has no nodes. Use the data collection and processing pipeline to generate the graph.</p>
                <ol class="text-start mx-auto" style="max-width: 500px;">
                    <li>Go to the <strong>News</strong> tab to collect financial news</li>
                    <li>Use the "Process" button to extract entities, model events, and analyze risks</li>
                    <li>Return to this page to view the generated knowledge graph</li>
                </ol>
                <p class="mt-3">You can also use the "Process All" button on the dashboard to run the complete pipeline</p>
            </div>`;
        return;
    }

    // Store the data globally
    graphData = data;
    
    // Create a data set for the graph
    const nodes = new vis.DataSet(data.nodes.map(node => {
        // Set the group based on the layer
        const group = node.layer || 'entity';
        
        // Set node shape and size based on node type
        let size = 20;
        let shape = 'dot';
        
        if (node.layer === 'entity') {
            if (node.mentions > 10) {
                size = 30;
            } else if (node.mentions > 5) {
                size = 25;
            }
        } else if (node.layer === 'risk') {
            if (node.severity >= 4) {
                size = 30;
                shape = 'diamond';
            } else if (node.severity >= 2) {
                size = 25;
                shape = 'diamond';
            } else {
                shape = 'diamond';
            }
        } else if (node.layer === 'event') {
            shape = 'square';
        }
        
        // Create tooltip based on node type
        let title = '';
        if (node.layer === 'entity') {
            title = `<div class="p-2">
                <strong>${node.label}</strong><br>
                Type: ${node.type}${node.subtype ? ', ' + node.subtype : ''}<br>
                Mentions: ${node.mentions || '0'}
            </div>`;
        } else if (node.layer === 'event') {
            title = `<div class="p-2">
                <strong>${node.label}</strong><br>
                Type: ${node.type}<br>
                Date: ${node.date || 'N/A'}<br>
                Connected Entities: ${node.entities || '0'}
            </div>`;
        } else if (node.layer === 'risk') {
            title = `<div class="p-2">
                <strong>${node.label}</strong><br>
                Type: ${node.type}<br>
                Severity: ${node.severity}/5<br>
                Likelihood: ${Math.round(node.likelihood * 100)}%<br>
                Impact Areas: ${Array.isArray(node.impact_areas) ? node.impact_areas.join(', ') : 'N/A'}
            </div>`;
        }
        
        return {
            id: node.id,
            label: node.label,
            group: group,
            size: size,
            shape: shape,
            title: title,
            // Saving the original data for later use
            originalData: node
        };
    }));
    
    const edges = new vis.DataSet(data.edges.map(edge => {
        // Set edge style based on edge type
        let width = 2;
        let dashes = false;
        let arrows = { to: { enabled: true, scaleFactor: 0.5 } };
        
        if (edge.layer === 'entity') {
            width = 1;
        } else if (edge.layer === 'risk') {
            width = 3;
            dashes = [5, 5];
        } else if (edge.layer.includes('_to_')) {
            dashes = [2, 2];
            width = 1;
        }
        
        if (edge.weight) {
            width = 1 + (edge.weight * 4);
        }
        
        // Create tooltip for edge
        const title = `<div class="p-2">
            <strong>${edge.type}</strong><br>
            Strength: ${Math.round(edge.weight * 100)}%
        </div>`;
        
        return {
            id: edge.id,
            from: edge.source,
            to: edge.target,
            label: edge.label,
            width: width,
            dashes: dashes,
            arrows: arrows,
            title: title,
            // Saving the original data for later use
            originalData: edge
        };
    }));
    
    // Create a network
    const container = document.getElementById(containerId);
    const data_vis = { nodes, edges };
    network = new vis.Network(container, data_vis, options);
    
    // Event handling
    network.on("click", function (params) {
        if (params.nodes.length > 0) {
            // Node click
            const nodeId = params.nodes[0];
            const node = nodes.get(nodeId);
            displayNodeDetails(node);
        } else {
            // Background click
            hideNodeDetails();
        }
    });
    
    // Fill the node selectors for path finding
    populateNodeSelectors(nodes);
    
    // Update layer counts
    updateLayerCounts(data.layers);
}

/**
 * Display node details in the side panel
 * @param {Object} node - The node that was clicked
 */
function displayNodeDetails(node) {
    const nodeDetails = document.getElementById('node-details');
    const nodeTitle = document.getElementById('node-title');
    const nodeContent = document.getElementById('node-content');
    
    nodeTitle.textContent = node.label;
    
    let content = '<div class="mb-3">';
    
    // Different content based on node type
    if (node.group === 'entity') {
        content += `<p><strong>Type:</strong> ${node.originalData.type}${node.originalData.subtype ? ', ' + node.originalData.subtype : ''}</p>`;
        content += `<p><strong>Mentions:</strong> ${node.originalData.mentions || '0'}</p>`;
    } else if (node.group === 'event') {
        content += `<p><strong>Type:</strong> ${node.originalData.type}</p>`;
        content += `<p><strong>Date:</strong> ${node.originalData.date || 'N/A'}</p>`;
        content += `<p><strong>Description:</strong> ${node.originalData.title || 'No description available'}</p>`;
    } else if (node.group === 'risk') {
        content += `<p><strong>Type:</strong> ${node.originalData.type}</p>`;
        content += `<p><strong>Severity:</strong> ${node.originalData.severity}/5</p>`;
        content += `<p><strong>Likelihood:</strong> ${Math.round(node.originalData.likelihood * 100)}%</p>`;
        
        if (node.originalData.impact_areas && node.originalData.impact_areas.length > 0) {
            content += `<p><strong>Impact Areas:</strong> ${node.originalData.impact_areas.join(', ')}</p>`;
        }
        
        content += `<p><strong>Description:</strong> ${node.originalData.title || 'No description available'}</p>`;
    }
    
    content += '</div>';
    
    // Connection information
    content += '<div class="mt-4"><h6>Connections</h6>';
    
    // Find connected nodes
    const connectedNodes = network.getConnectedNodes(node.id);
    
    if (connectedNodes.length > 0) {
        content += '<ul class="list-group list-group-flush small">';
        connectedNodes.forEach(connectedId => {
            const connectedNode = network.body.nodes[connectedId];
            if (connectedNode && connectedNode.options) {
                content += `<li class="list-group-item bg-dark text-light border-secondary">
                    <span class="badge rounded-pill me-2" style="background-color: ${getColorForGroup(connectedNode.options.group)};">
                        ${connectedNode.options.group}
                    </span>
                    ${connectedNode.options.label}
                </li>`;
            }
        });
        content += '</ul>';
    } else {
        content += '<p class="small text-muted">No connections found</p>';
    }
    
    content += '</div>';
    
    nodeContent.innerHTML = content;
    nodeDetails.style.display = 'block';
}

/**
 * Hide the node details panel
 */
function hideNodeDetails() {
    const nodeDetails = document.getElementById('node-details');
    nodeDetails.style.display = 'none';
}

/**
 * Get the color for a node group
 * @param {string} group - The node group (entity, event, risk)
 * @returns {string} - The CSS color variable
 */
function getColorForGroup(group) {
    switch(group) {
        case 'entity':
            return 'var(--entity-color)';
        case 'event':
            return 'var(--event-color)';
        case 'risk':
            return 'var(--risk-color)';
        default:
            return '#777777';
    }
}

/**
 * Update the layer counts display
 * @param {Object} layers - Layer count data
 */
function updateLayerCounts(layers) {
    if (!layers) return;
    
    // Update entity count
    const entityToggle = document.getElementById('toggle-entity-layer');
    if (entityToggle) {
        const entityCount = layers.entity ? layers.entity.count : 0;
        entityToggle.innerHTML = `<span class="legend-color" style="background-color: var(--entity-color);"></span>
            <span>Entities (${entityCount})</span>`;
    }
    
    // Update event count
    const eventToggle = document.getElementById('toggle-event-layer');
    if (eventToggle) {
        const eventCount = layers.event ? layers.event.count : 0;
        eventToggle.innerHTML = `<span class="legend-color" style="background-color: var(--event-color);"></span>
            <span>Events (${eventCount})</span>`;
    }
    
    // Update risk count
    const riskToggle = document.getElementById('toggle-risk-layer');
    if (riskToggle) {
        const riskCount = layers.risk ? layers.risk.count : 0;
        riskToggle.innerHTML = `<span class="legend-color" style="background-color: var(--risk-color);"></span>
            <span>Risks (${riskCount})</span>`;
    }
}

/**
 * Populate the node selectors for path finding
 * @param {vis.DataSet} nodes - The nodes dataset
 */
function populateNodeSelectors(nodes) {
    const sourceSelect = document.getElementById('source-node');
    const targetSelect = document.getElementById('target-node');
    
    // Clear existing options
    sourceSelect.innerHTML = '<option value="">Select source...</option>';
    targetSelect.innerHTML = '<option value="">Select target...</option>';
    
    // Group nodes by type
    const nodesByType = {
        entity: [],
        event: [],
        risk: []
    };
    
    // Add nodes to appropriate groups
    nodes.forEach(node => {
        if (node.group && nodesByType[node.group]) {
            nodesByType[node.group].push(node);
        }
    });
    
    // Add option groups to selects
    for (const type in nodesByType) {
        if (nodesByType[type].length > 0) {
            const sourceGroup = document.createElement('optgroup');
            sourceGroup.label = type.charAt(0).toUpperCase() + type.slice(1) + 's';
            
            const targetGroup = document.createElement('optgroup');
            targetGroup.label = type.charAt(0).toUpperCase() + type.slice(1) + 's';
            
            // Sort nodes alphabetically by label
            nodesByType[type].sort((a, b) => a.label.localeCompare(b.label));
            
            // Add options
            nodesByType[type].forEach(node => {
                const sourceOption = document.createElement('option');
                sourceOption.value = node.id;
                sourceOption.textContent = node.label;
                sourceGroup.appendChild(sourceOption);
                
                const targetOption = document.createElement('option');
                targetOption.value = node.id;
                targetOption.textContent = node.label;
                targetGroup.appendChild(targetOption);
            });
            
            sourceSelect.appendChild(sourceGroup);
            targetSelect.appendChild(targetGroup);
        }
    }
}

/**
 * Set up event listeners for graph controls
 */
function setupGraphControls() {
    // Layer toggling
    document.getElementById('toggle-entity-layer').addEventListener('click', function() {
        toggleLayer('entity');
    });
    
    document.getElementById('toggle-event-layer').addEventListener('click', function() {
        toggleLayer('event');
    });
    
    document.getElementById('toggle-risk-layer').addEventListener('click', function() {
        toggleLayer('risk');
    });
    
    document.getElementById('show-all-layers').addEventListener('click', function() {
        loadGraphData('all');
    });
    
    // Layout selection
    document.getElementById('layout-selector').addEventListener('change', function() {
        changeLayout(this.value);
    });
    
    // Physics toggle
    document.getElementById('physics-toggle').addEventListener('change', function() {
        togglePhysics(this.checked);
    });
    
    // Search functionality
    document.getElementById('search-button').addEventListener('click', function() {
        searchNodes();
    });
    
    document.getElementById('search-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchNodes();
        }
    });
    
    // Centrality analysis
    document.getElementById('run-centrality').addEventListener('click', function() {
        const measure = document.getElementById('centrality-measure').value;
        runCentralityAnalysis(measure);
    });
    
    // Community detection
    document.getElementById('run-community').addEventListener('click', function() {
        const method = document.getElementById('community-method').value;
        runCommunityDetection(method);
    });
    
    // Path finding
    document.getElementById('find-path').addEventListener('click', function() {
        const sourceId = document.getElementById('source-node').value;
        const targetId = document.getElementById('target-node').value;
        findPath(sourceId, targetId);
    });
}

/**
 * Toggle the visibility of a layer
 * @param {string} layer - The layer to toggle (entity, event, risk)
 */
function toggleLayer(layer) {
    loadGraphData(layer);
}

/**
 * Load graph data with the specified layer filter
 * @param {string} layer - The layer to display (entity, event, risk, all)
 */
function loadGraphData(layer) {
    fetch(`/api/get-graph-data?layer=${layer}`)
        .then(response => response.json())
        .then(data => {
            initializeGraph('graph-container', data);
        })
        .catch(error => {
            console.error('Error fetching graph data:', error);
            document.getElementById('graph-container').innerHTML = 
                '<div class="alert alert-danger p-5 m-5 text-center">Error loading graph data</div>';
        });
}

/**
 * Change the graph layout
 * @param {string} layout - The layout type (force, circular, hierarchical)
 */
function changeLayout(layout) {
    if (!network) return;
    
    let layoutOptions = {};
    
    switch(layout) {
        case 'force':
            layoutOptions = {
                improvedLayout: true,
                hierarchical: {
                    enabled: false
                }
            };
            
            // Reset physics to default
            network.setOptions({
                physics: {
                    enabled: true,
                    barnesHut: {
                        gravitationalConstant: -2000,
                        centralGravity: 0.3,
                        springLength: 150,
                        springConstant: 0.04,
                        damping: 0.09
                    }
                }
            });
            break;
            
        case 'circular':
            // Turn off physics first
            network.setOptions({
                physics: {
                    enabled: false
                }
            });
            
            // Get the nodes
            const nodes = network.body.nodes;
            const nodeIds = Object.keys(nodes);
            
            // Calculate positions in a circle
            const radius = Math.min(network.canvas.canvasViewCenter.x, network.canvas.canvasViewCenter.y) * 0.8;
            const angleStep = (2 * Math.PI) / nodeIds.length;
            
            const positions = {};
            nodeIds.forEach((id, index) => {
                const angle = angleStep * index;
                positions[id] = {
                    x: radius * Math.cos(angle) + network.canvas.canvasViewCenter.x,
                    y: radius * Math.sin(angle) + network.canvas.canvasViewCenter.y
                };
            });
            
            network.moveNodes(positions);
            break;
            
        case 'hierarchical':
            layoutOptions = {
                hierarchical: {
                    enabled: true,
                    direction: 'UD',
                    sortMethod: 'directed',
                    nodeSpacing: 150,
                    treeSpacing: 200
                }
            };
            
            // Adjust physics for hierarchical layout
            network.setOptions({
                physics: {
                    enabled: true,
                    hierarchicalRepulsion: {
                        nodeDistance: 200,
                        centralGravity: 0.1,
                        springLength: 100,
                        springConstant: 0.01,
                        damping: 0.09
                    }
                }
            });
            break;
    }
    
    network.setOptions({ layout: layoutOptions });
}

/**
 * Toggle physics simulation
 * @param {boolean} enabled - Whether physics should be enabled
 */
function togglePhysics(enabled) {
    if (!network) return;
    
    network.setOptions({
        physics: {
            enabled: enabled
        }
    });
}

/**
 * Search for nodes matching the search term
 */
function searchNodes() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const searchType = document.getElementById('search-type').value;
    const resultsContainer = document.getElementById('search-results');
    
    if (!searchTerm) {
        resultsContainer.innerHTML = '<div class="text-muted small">Enter a search term</div>';
        return;
    }
    
    if (!graphData || !graphData.nodes) {
        resultsContainer.innerHTML = '<div class="text-danger small">No graph data available</div>';
        return;
    }
    
    // Filter nodes
    const filteredNodes = graphData.nodes.filter(node => {
        // Filter by type if needed
        if (searchType !== 'all' && node.layer !== searchType) {
            return false;
        }
        
        // Search in label
        if (node.label && node.label.toLowerCase().includes(searchTerm)) {
            return true;
        }
        
        // Search in type
        if (node.type && node.type.toLowerCase().includes(searchTerm)) {
            return true;
        }
        
        // Search in description/title for events and risks
        if (node.title && node.title.toLowerCase().includes(searchTerm)) {
            return true;
        }
        
        return false;
    });
    
    // Display results
    if (filteredNodes.length > 0) {
        let resultsHtml = '<div class="list-group mt-2">';
        
        filteredNodes.forEach(node => {
            let badgeClass = 'bg-secondary';
            
            if (node.layer === 'entity') {
                badgeClass = 'bg-primary';
            } else if (node.layer === 'event') {
                badgeClass = 'bg-danger';
            } else if (node.layer === 'risk') {
                badgeClass = 'bg-warning text-dark';
            }
            
            resultsHtml += `<a href="#" class="list-group-item list-group-item-action bg-dark text-light border-secondary search-result-item" data-node-id="${node.id}">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <div class="mb-1">${node.label}</div>
                        <small class="text-muted">${node.type || ''}</small>
                    </div>
                    <span class="badge ${badgeClass}">${node.layer}</span>
                </div>
            </a>`;
        });
        
        resultsHtml += '</div>';
        resultsContainer.innerHTML = resultsHtml;
        
        // Add click event to results
        document.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                const nodeId = this.getAttribute('data-node-id');
                focusOnNode(nodeId);
            });
        });
    } else {
        resultsContainer.innerHTML = '<div class="text-muted small">No results found</div>';
    }
}

/**
 * Focus on a specific node
 * @param {string} nodeId - The ID of the node to focus on
 */
function focusOnNode(nodeId) {
    if (!network) return;
    
    // Focus on the node
    network.focus(nodeId, {
        scale: 1.2,
        animation: {
            duration: 1000,
            easingFunction: 'easeInOutQuad'
        }
    });
    
    // Select the node
    network.selectNodes([nodeId]);
    
    // Trigger the click event to show node details
    const node = network.body.nodes[nodeId];
    if (node) {
        displayNodeDetails({
            id: nodeId,
            label: node.options.label,
            group: node.options.group,
            originalData: node.options.originalData || {}
        });
    }
}

/**
 * Run centrality analysis
 * @param {string} measure - The centrality measure to use
 */
function runCentralityAnalysis(measure) {
    fetch(`/api/query-graph`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            type: 'centrality',
            params: {
                measure: measure
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'error') {
            alert('Error: ' + data.message);
            return;
        }
        
        // Get the results
        const results = data.results;
        
        // Update node sizes based on centrality
        if (!network || !results) return;
        
        const nodes = network.body.data.nodes;
        const updates = [];
        
        // Process each layer
        for (const layer in results) {
            results[layer].forEach(item => {
                if (item.id) {
                    // Get the original node
                    const node = nodes.get(item.id);
                    if (node) {
                        // Calculate new size based on centrality value
                        // This assumes the values are normalized between 0-1
                        const value = item.value || 0;
                        const minSize = 15;
                        const maxSize = 50;
                        const newSize = minSize + (value * (maxSize - minSize));
                        
                        // Update the node
                        updates.push({
                            id: item.id,
                            size: newSize,
                            label: node.label,
                            title: node.title + `<br><strong>${measure} Centrality:</strong> ${value.toFixed(3)}`
                        });
                    }
                }
            });
        }
        
        // Apply updates
        nodes.update(updates);
        
        // Notification
        alert(`Applied ${measure} centrality analysis to the graph. Node sizes now reflect their centrality values.`);
    })
    .catch(error => {
        console.error('Error running centrality analysis:', error);
        alert('Error running centrality analysis. See console for details.');
    });
}

/**
 * Run community detection
 * @param {string} method - The community detection method to use
 */
function runCommunityDetection(method) {
    fetch(`/api/query-graph`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            type: 'community',
            params: {
                method: method
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'error') {
            alert('Error: ' + data.message);
            return;
        }
        
        // Get the results
        const results = data.results;
        
        // Update node colors based on communities
        if (!network || !results) return;
        
        const nodes = network.body.data.nodes;
        const updates = [];
        
        // Generate colors for communities
        const communityColors = {};
        let communityCount = 0;
        
        // Process each layer
        for (const layer in results) {
            results[layer].forEach(item => {
                if (item.id && item.community !== undefined) {
                    // Get the original node
                    const node = nodes.get(item.id);
                    if (node) {
                        // Ensure we have a color for this community
                        const communityKey = `${layer}_${item.community}`;
                        if (!communityColors[communityKey]) {
                            communityColors[communityKey] = getRandomColor(communityCount);
                            communityCount++;
                        }
                        
                        // Update the node
                        updates.push({
                            id: item.id,
                            color: {
                                background: communityColors[communityKey],
                                border: lightenDarkenColor(communityColors[communityKey], -40)
                            },
                            title: node.title + `<br><strong>Community:</strong> ${item.community}`
                        });
                    }
                }
            });
        }
        
        // Apply updates
        nodes.update(updates);
        
        // Notification
        alert(`Applied ${method} community detection to the graph. Node colors now reflect their community memberships.`);
    })
    .catch(error => {
        console.error('Error running community detection:', error);
        alert('Error running community detection. See console for details.');
    });
}

/**
 * Find a path between two nodes
 * @param {string} sourceId - The ID of the source node
 * @param {string} targetId - The ID of the target node
 */
function findPath(sourceId, targetId) {
    if (!sourceId || !targetId) {
        alert('Please select both source and target nodes');
        return;
    }
    
    fetch(`/api/query-graph`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            type: 'path',
            params: {
                source_id: sourceId,
                target_id: targetId,
                max_length: 5
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'error') {
            alert('Error: ' + data.message);
            return;
        }
        
        const results = data.results;
        
        if (!results || results.length === 0) {
            alert('No path found between the selected nodes');
            return;
        }
        
        // Highlight the path
        highlightPath(results);
    })
    .catch(error => {
        console.error('Error finding path:', error);
        alert('Error finding path. See console for details.');
    });
}

/**
 * Highlight a path in the graph
 * @param {Array} pathSegments - The segments of the path
 */
function highlightPath(pathSegments) {
    if (!network || !pathSegments || pathSegments.length === 0) return;
    
    // Reset all nodes and edges
    network.body.data.nodes.forEach(node => {
        node.color = undefined;
    });
    
    network.body.data.edges.forEach(edge => {
        edge.color = undefined;
        edge.width = undefined;
    });
    
    // Update network to reset colors
    network.redraw();
    
    // Create sets for nodes and edges in the path
    const pathNodeIds = new Set();
    const pathEdgeIds = new Set();
    
    // Collect all nodes and edges in the path
    pathSegments.forEach(segment => {
        pathNodeIds.add(segment.source_id);
        pathNodeIds.add(segment.target_id);
        
        // Find the edge between these nodes
        network.body.data.edges.forEach(edge => {
            if ((edge.from === segment.source_id && edge.to === segment.target_id) || 
                (edge.from === segment.target_id && edge.to === segment.source_id)) {
                pathEdgeIds.add(edge.id);
            }
        });
    });
    
    // Highlight the nodes
    network.body.data.nodes.update(Array.from(pathNodeIds).map(id => ({
        id: id,
        borderWidth: 3,
        color: {
            border: '#ffffff'
        }
    })));
    
    // Highlight the edges
    network.body.data.edges.update(Array.from(pathEdgeIds).map(id => ({
        id: id,
        width: 4,
        color: {
            color: '#ffffff',
            highlight: '#ffffff',
            hover: '#ffffff'
        }
    })));
    
    // Focus on the path
    const nodeIds = Array.from(pathNodeIds);
    if (nodeIds.length > 0) {
        network.fit({
            nodes: nodeIds,
            animation: {
                duration: 1000,
                easingFunction: 'easeInOutQuad'
            }
        });
    }
    
    // Create a description of the path
    let pathDescription = 'Path found: ';
    
    pathSegments.forEach((segment, index) => {
        if (index > 0) {
            pathDescription += ' → ';
        }
        
        const sourceNode = network.body.nodes[segment.source_id];
        if (sourceNode && index === 0) {
            pathDescription += sourceNode.options.label;
        }
        
        const targetNode = network.body.nodes[segment.target_id];
        if (targetNode) {
            pathDescription += ' → ' + targetNode.options.label;
        }
    });
    
    alert(pathDescription);
}

/**
 * Generate a random color for a community
 * @param {number} index - The index of the community
 * @returns {string} - A hex color code
 */
function getRandomColor(index) {
    // Use a set of visually distinct colors
    const colors = [
        '#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#42d4f4', '#f032e6',
        '#bfef45', '#fabed4', '#469990', '#dcbeff', '#9A6324', '#fffac8', '#800000', '#aaffc3',
        '#808000', '#ffd8b1', '#000075', '#a9a9a9'
    ];
    
    return colors[index % colors.length];
}

/**
 * Lighten or darken a color
 * @param {string} color - The hex color code
 * @param {number} amount - The amount to lighten (positive) or darken (negative)
 * @returns {string} - The adjusted hex color code
 */
function lightenDarkenColor(color, amount) {
    let usePound = false;
    
    if (color[0] === '#') {
        color = color.slice(1);
        usePound = true;
    }
    
    const num = parseInt(color, 16);
    
    let r = (num >> 16) + amount;
    r = Math.max(Math.min(r, 255), 0);
    
    let g = ((num >> 8) & 0x00FF) + amount;
    g = Math.max(Math.min(g, 255), 0);
    
    let b = (num & 0x0000FF) + amount;
    b = Math.max(Math.min(b, 255), 0);
    
    return (usePound ? '#' : '') + (g | (r << 8) | (b << 16)).toString(16).padStart(6, '0');
}