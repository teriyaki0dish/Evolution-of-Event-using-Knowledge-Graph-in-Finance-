"""
Knowledge graph builder for constructing the financial risk knowledge graph.
"""
import logging
import networkx as nx
from typing import List, Dict, Any, Optional, Set, Tuple
import json
import community as community_louvain
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

class GraphBuilder:
    """
    Builds and analyzes the financial risk knowledge graph.
    """
    
    def __init__(self, data_store):
        """
        Initialize the graph builder with data store.
        
        Args:
            data_store: Data storage interface
        """
        self.data_store = data_store
        self.graph = nx.MultiDiGraph()  # Main graph
        self.entity_graph = nx.DiGraph()  # Entity layer
        self.event_graph = nx.DiGraph()  # Event layer
        self.risk_graph = nx.DiGraph()  # Risk layer
        
    def build_complete_graph(self) -> None:
        """
        Build the complete three-layer knowledge graph.
        """
        # Clear existing graphs
        self.graph.clear()
        self.entity_graph.clear()
        self.event_graph.clear()
        self.risk_graph.clear()
        
        # Load all data
        entities = self.data_store.get_all_entities()
        relationships = self.data_store.get_all_relationships()
        events = self.data_store.get_all_events()
        risks = self.data_store.get_all_risks()
        
        # Build entity layer
        self._build_entity_layer(entities, relationships)
        logger.info(f"Built entity layer with {len(entities)} entities and {len(relationships)} relationships")
        
        # Build event layer and connections to entity layer
        self._build_event_layer(events, entities)
        logger.info(f"Built event layer with {len(events)} events")
        
        # Build risk layer and connections to event and entity layers
        self._build_risk_layer(risks, events, entities)
        logger.info(f"Built risk layer with {len(risks)} risks")
        
        # Build the combined graph
        self._build_combined_graph()
        logger.info(f"Built combined knowledge graph with {len(self.graph.nodes)} nodes and {len(self.graph.edges)} edges")
        
        # Save the graph structure to file
        self._save_graph_to_file()
    
    def _build_entity_layer(self, entities: List, relationships: List) -> None:
        """
        Build the entity layer of the knowledge graph.
        
        Args:
            entities: List of entity objects
            relationships: List of relationship objects
        """
        # Add all entities as nodes
        for entity in entities:
            self.entity_graph.add_node(
                entity.id,
                type="entity",
                name=entity.name,
                entity_type=entity.type,
                subtype=entity.subtype,
                attributes=entity.attributes,
                mention_count=len(entity.mentions)
            )
        
        # Add relationships as edges
        for rel in relationships:
            # Skip if source or target doesn't exist
            if not self.entity_graph.has_node(rel.source_id) or not self.entity_graph.has_node(rel.target_id):
                continue
                
            self.entity_graph.add_edge(
                rel.source_id,
                rel.target_id,
                id=rel.id,
                type=rel.type,
                weight=rel.confidence,
                attributes=rel.attributes,
                mention_count=len(rel.mentions)
            )
    
    def _build_event_layer(self, events: List, entities: List) -> None:
        """
        Build the event layer of the knowledge graph.
        
        Args:
            events: List of event objects
            entities: List of entity objects
        """
        # Add all events as nodes
        for event in events:
            self.event_graph.add_node(
                event.id,
                type="event",
                title=event.title,
                description=event.description,
                event_type=event.event_type,
                event_date=event.event_date.isoformat(),
                attributes=event.attributes,
                entity_count=len(event.entities)
            )
            
            # Add edges to entities
            for entity_id in event.entities:
                # Skip if entity doesn't exist
                if not self.entity_graph.has_node(entity_id):
                    continue
                    
                # Get entity role from event attributes if available
                role = "participant"
                if "entity_roles" in event.attributes and entity_id in event.attributes["entity_roles"]:
                    role = event.attributes["entity_roles"][entity_id]
                
                # Add edge from event to entity
                self.event_graph.add_edge(
                    event.id,
                    entity_id,
                    type="involves",
                    role=role,
                    layer_edge="event_to_entity"
                )
        
        # Add event evolution relationships
        for event in events:
            # Check for predecessor events
            if "predecessors" in event.attributes:
                for pred_info in event.attributes["predecessors"]:
                    pred_id = pred_info.get("event_id")
                    rel_type = pred_info.get("type", "follows")
                    similarity = pred_info.get("similarity", 0.5)
                    
                    # Skip if predecessor doesn't exist
                    if not self.event_graph.has_node(pred_id):
                        continue
                        
                    # Add edge from predecessor to this event
                    self.event_graph.add_edge(
                        pred_id,
                        event.id,
                        type=rel_type,
                        weight=similarity,
                        layer_edge="event_to_event"
                    )
    
    def _build_risk_layer(self, risks: List, events: List, entities: List) -> None:
        """
        Build the risk layer of the knowledge graph.
        
        Args:
            risks: List of risk objects
            events: List of event objects
            entities: List of entity objects
        """
        # Add all risks as nodes
        for risk in risks:
            self.risk_graph.add_node(
                risk.id,
                type="risk",
                title=risk.title,
                description=risk.description,
                risk_type=risk.risk_type,
                severity=risk.severity,
                likelihood=risk.likelihood,
                attributes=risk.attributes,
                impact_areas=risk.impact_areas
            )
            
            # Add edges to affected entities
            for entity_id in risk.entities:
                # Skip if entity doesn't exist
                if not self.entity_graph.has_node(entity_id):
                    continue
                    
                # Get impact level from risk attributes if available
                impact = 1.0
                if "entity_impacts" in risk.attributes and entity_id in risk.attributes["entity_impacts"]:
                    impact = risk.attributes["entity_impacts"][entity_id]
                
                # Add edge from risk to entity
                self.risk_graph.add_edge(
                    risk.id,
                    entity_id,
                    type="affects",
                    impact=impact,
                    layer_edge="risk_to_entity"
                )
            
            # Add edges to triggering events
            for event_id in risk.events:
                # Skip if event doesn't exist
                if not self.event_graph.has_node(event_id):
                    continue
                    
                # Get correlation from risk attributes if available
                correlation = 1.0
                if "event_correlations" in risk.attributes and event_id in risk.attributes["event_correlations"]:
                    correlation = risk.attributes["event_correlations"][event_id]
                
                # Add edge from event to risk
                self.risk_graph.add_edge(
                    event_id,
                    risk.id,
                    type="triggers",
                    correlation=correlation,
                    layer_edge="event_to_risk"
                )
        
        # Add risk relationship edges
        for risk in risks:
            for related_id in risk.related_risks:
                # Skip if related risk doesn't exist
                if not self.risk_graph.has_node(related_id):
                    continue
                    
                # Get relationship type from risk attributes if available
                rel_type = "related_to"
                if "risk_relationships" in risk.attributes and related_id in risk.attributes["risk_relationships"]:
                    rel_type = risk.attributes["risk_relationships"][related_id]
                
                # Get relationship strength/weight if available
                weight = 0.5
                if "risk_correlations" in risk.attributes and related_id in risk.attributes["risk_correlations"]:
                    weight = risk.attributes["risk_correlations"][related_id]
                elif "risk_transmissions" in risk.attributes and related_id in risk.attributes["risk_transmissions"]:
                    weight = risk.attributes["risk_transmissions"][related_id]
                
                # Add edge between risks
                self.risk_graph.add_edge(
                    risk.id,
                    related_id,
                    type=rel_type,
                    weight=weight,
                    layer_edge="risk_to_risk"
                )
    
    def _build_combined_graph(self) -> None:
        """
        Build the combined multi-layer knowledge graph.
        """
        # Add all nodes and edges from individual layers
        
        # Add entity layer
        for node, attrs in self.entity_graph.nodes(data=True):
            self.graph.add_node(node, layer="entity", **attrs)
        
        for u, v, attrs in self.entity_graph.edges(data=True):
            self.graph.add_edge(u, v, layer="entity", **attrs)
        
        # Add event layer
        for node, attrs in self.event_graph.nodes(data=True):
            if not self.graph.has_node(node):  # Only events, not entities
                self.graph.add_node(node, layer="event", **attrs)
        
        for u, v, attrs in self.event_graph.edges(data=True):
            if attrs.get("layer_edge") == "event_to_event":
                self.graph.add_edge(u, v, layer="event", **attrs)
            elif attrs.get("layer_edge") == "event_to_entity":
                self.graph.add_edge(u, v, layer="event_to_entity", **attrs)
        
        # Add risk layer
        for node, attrs in self.risk_graph.nodes(data=True):
            if not self.graph.has_node(node):  # Only risks, not events or entities
                self.graph.add_node(node, layer="risk", **attrs)
        
        for u, v, attrs in self.risk_graph.edges(data=True):
            if attrs.get("layer_edge") == "risk_to_risk":
                self.graph.add_edge(u, v, layer="risk", **attrs)
            elif attrs.get("layer_edge") == "risk_to_entity":
                self.graph.add_edge(u, v, layer="risk_to_entity", **attrs)
            elif attrs.get("layer_edge") == "event_to_risk":
                self.graph.add_edge(u, v, layer="event_to_risk", **attrs)
    
    def _save_graph_to_file(self) -> None:
        """
        Save the knowledge graph structure to a file.
        """
        try:
            # Convert graph to serializable format
            graph_data = {
                "nodes": [],
                "edges": []
            }
            
            # Add nodes
            for node, attrs in self.graph.nodes(data=True):
                node_data = {
                    "id": node,
                    **attrs
                }
                
                # Convert non-serializable types
                if "event_date" in node_data:
                    node_data["event_date"] = str(node_data["event_date"])
                if "attributes" in node_data and isinstance(node_data["attributes"], dict):
                    for k, v in node_data["attributes"].items():
                        if not isinstance(v, (str, int, float, bool, list, dict, type(None))):
                            node_data["attributes"][k] = str(v)
                
                graph_data["nodes"].append(node_data)
            
            # Add edges
            for u, v, key, attrs in self.graph.edges(data=True, keys=True):
                edge_data = {
                    "source": u,
                    "target": v,
                    "key": str(key),
                    **attrs
                }
                
                # Convert non-serializable types
                if "attributes" in edge_data and isinstance(edge_data["attributes"], dict):
                    for k, v in edge_data["attributes"].items():
                        if not isinstance(v, (str, int, float, bool, list, dict, type(None))):
                            edge_data["attributes"][k] = str(v)
                
                graph_data["edges"].append(edge_data)
            
            # Save to file
            with open(self.data_store.graph_file, 'w') as f:
                json.dump(graph_data, f, indent=2)
                
            logger.info(f"Saved knowledge graph to {self.data_store.graph_file}")
        
        except Exception as e:
            logger.error(f"Error saving graph to file: {e}")
    
    def get_visualization_data(self, layer: str = "all") -> Dict[str, Any]:
        """
        Get graph data formatted for visualization.
        
        Args:
            layer: Graph layer to visualize ("entity", "event", "risk", or "all")
            
        Returns:
            Dictionary with nodes and edges data
        """
        # Initialize visualization data
        vis_data = {
            "nodes": [],
            "edges": [],
            "layers": {
                "entity": {"count": 0},
                "event": {"count": 0},
                "risk": {"count": 0}
            }
        }
        
        try:
            # Try to load graph data from file if graph is empty
            if not self.graph.nodes:
                try:
                    # Try to build the graph
                    self.build_complete_graph()
                except Exception as build_error:
                    logger.warning(f"Could not build graph: {build_error}")
                    # If that fails, try to read from the file directly
                    try:
                        with open(self.data_store.db_config["graph_file"], 'r') as f:
                            graph_data = json.load(f)
                            # Return the file contents directly
                            return graph_data
                    except Exception as read_error:
                        logger.warning(f"Could not read graph file: {read_error}")
                        # Return empty visualization data with error flag
                        return {
                            "nodes": [],
                            "edges": [],
                            "layers": {
                                "entity": {"count": 0},
                                "event": {"count": 0},
                                "risk": {"count": 0}
                            },
                            "error": "No graph data available. Process data to build the graph."
                        }
            
            # If we have nodes in the graph, proceed with visualization
            # Filter nodes by layer
            nodes_to_include = set()
            
            if layer == "all" or layer == "entity":
                entity_nodes = [n for n, a in self.graph.nodes(data=True) if a.get("layer") == "entity"]
                nodes_to_include.update(entity_nodes)
                vis_data["layers"]["entity"]["count"] = len(entity_nodes)
            
            if layer == "all" or layer == "event":
                event_nodes = [n for n, a in self.graph.nodes(data=True) if a.get("layer") == "event"]
                nodes_to_include.update(event_nodes)
                vis_data["layers"]["event"]["count"] = len(event_nodes)
            
            if layer == "all" or layer == "risk":
                risk_nodes = [n for n, a in self.graph.nodes(data=True) if a.get("layer") == "risk"]
                nodes_to_include.update(risk_nodes)
                vis_data["layers"]["risk"]["count"] = len(risk_nodes)
            
            # If we have no nodes to include after filtering, return empty data with message
            if not nodes_to_include:
                return {
                    "nodes": [],
                    "edges": [],
                    "layers": {
                        "entity": {"count": 0},
                        "event": {"count": 0},
                        "risk": {"count": 0}
                    },
                    "error": f"No {layer} data available. Process data to build the graph."
                }
            
            # Add nodes
            for node in nodes_to_include:
                attrs = self.graph.nodes[node]
                node_layer = attrs.get("layer", "unknown")
                
                # Base node data
                node_data = {
                    "id": node,
                    "layer": node_layer
                }
                
                # Layer-specific data
                if node_layer == "entity":
                    node_data.update({
                        "label": attrs.get("name", "Unknown Entity"),
                        "title": f"{attrs.get('name', 'Unknown')}: {attrs.get('entity_type', '')}",
                        "type": attrs.get("entity_type", ""),
                        "subtype": attrs.get("subtype", ""),
                        "mentions": attrs.get("mention_count", 0)
                    })
                
                elif node_layer == "event":
                    node_data.update({
                        "label": attrs.get("title", "Unknown Event"),
                        "title": attrs.get("description", ""),
                        "type": attrs.get("event_type", ""),
                        "date": attrs.get("event_date", ""),
                        "entities": attrs.get("entity_count", 0)
                    })
                
                elif node_layer == "risk":
                    node_data.update({
                        "label": attrs.get("title", "Unknown Risk"),
                        "title": attrs.get("description", ""),
                        "type": attrs.get("risk_type", ""),
                        "severity": attrs.get("severity", 1),
                        "likelihood": attrs.get("likelihood", 0.0),
                        "impact_areas": attrs.get("impact_areas", [])
                    })
                
                vis_data["nodes"].append(node_data)
            
            # Add edges between included nodes
            for u, v, key, attrs in self.graph.edges(data=True, keys=True):
                # Skip if either node not in our included set
                if u not in nodes_to_include or v not in nodes_to_include:
                    continue
                
                edge_layer = attrs.get("layer", "unknown")
                
                # Filter edges by layer
                if layer != "all" and edge_layer != layer and edge_layer not in [f"{layer}_to_entity", f"event_to_{layer}"]:
                    continue
                
                # Get edge weight
                weight = attrs.get("weight", 0.5)
                if "impact" in attrs:
                    weight = attrs["impact"]
                elif "correlation" in attrs:
                    weight = attrs["correlation"]
                
                edge_data = {
                    "id": f"{u}-{v}-{key}",
                    "source": u,
                    "target": v,
                    "label": attrs.get("type", "connected_to"),
                    "type": attrs.get("type", "connected_to"),
                    "layer": edge_layer,
                    "weight": weight
                }
                
                vis_data["edges"].append(edge_data)
        
        except Exception as e:
            logger.error(f"Error generating visualization data: {e}")
            import traceback
            traceback.print_exc()
            return {
                "nodes": [],
                "edges": [],
                "layers": {
                    "entity": {"count": 0},
                    "event": {"count": 0},
                    "risk": {"count": 0}
                },
                "error": f"Error loading graph data: {str(e)}"
            }
        
        return vis_data
    
    def analyze_centrality(self, measure: str = "degree") -> Dict[str, List[Dict[str, Any]]]:
        """
        Analyze node centrality in the knowledge graph.
        
        Args:
            measure: Centrality measure to use ("degree", "betweenness", "closeness", "eigenvector")
            
        Returns:
            Dictionary with centrality results by layer
        """
        results = {
            "entity": [],
            "event": [],
            "risk": []
        }
        
        try:
            # Reload the graph if empty
            if not self.graph.nodes:
                self.build_complete_graph()
            
            # Create a simplified undirected graph for centrality calculations
            simple_graph = nx.Graph()
            
            # Add nodes and edges from the main graph
            for n, attrs in self.graph.nodes(data=True):
                simple_graph.add_node(n, **attrs)
            
            for u, v, attrs in self.graph.edges(data=True):
                # Add edge with weight if not already present or with higher weight
                if not simple_graph.has_edge(u, v) or simple_graph[u][v].get("weight", 0) < attrs.get("weight", 0.5):
                    simple_graph.add_edge(u, v, weight=attrs.get("weight", 0.5))
            
            # Calculate centrality based on selected measure
            if measure == "degree":
                centrality = nx.degree_centrality(simple_graph)
            elif measure == "betweenness":
                centrality = nx.betweenness_centrality(simple_graph, weight="weight")
            elif measure == "closeness":
                centrality = nx.closeness_centrality(simple_graph, distance="weight")
            elif measure == "eigenvector":
                centrality = nx.eigenvector_centrality_numpy(simple_graph, weight="weight")
            else:
                centrality = nx.degree_centrality(simple_graph)
            
            # Group results by layer
            for node, cent_value in centrality.items():
                if node not in self.graph.nodes:
                    continue
                    
                attrs = self.graph.nodes[node]
                layer = attrs.get("layer", "unknown")
                
                if layer not in results:
                    continue
                
                node_info = {"id": node, "centrality": cent_value}
                
                # Add layer-specific information
                if layer == "entity":
                    node_info.update({
                        "name": attrs.get("name", "Unknown"),
                        "type": attrs.get("entity_type", ""),
                        "subtype": attrs.get("subtype", "")
                    })
                elif layer == "event":
                    node_info.update({
                        "title": attrs.get("title", "Unknown"),
                        "type": attrs.get("event_type", ""),
                        "date": attrs.get("event_date", "")
                    })
                elif layer == "risk":
                    node_info.update({
                        "title": attrs.get("title", "Unknown"),
                        "type": attrs.get("risk_type", ""),
                        "severity": attrs.get("severity", 1)
                    })
                
                results[layer].append(node_info)
            
            # Sort results by centrality
            for layer in results:
                results[layer] = sorted(results[layer], key=lambda x: x["centrality"], reverse=True)
        
        except Exception as e:
            logger.error(f"Error calculating {measure} centrality: {e}")
        
        return results
    
    def detect_communities(self, method: str = "louvain") -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect communities in the knowledge graph.
        
        Args:
            method: Community detection method ("louvain", "label_propagation")
            
        Returns:
            Dictionary with community detection results by layer
        """
        results = {
            "entity": [],
            "event": [],
            "risk": [],
            "combined": []
        }
        
        try:
            # Reload the graph if empty
            if not self.graph.nodes:
                self.build_complete_graph()
            
            # Create a simplified undirected graph for community detection
            simple_graph = nx.Graph()
            
            # Add nodes and edges from the main graph
            for n, attrs in self.graph.nodes(data=True):
                simple_graph.add_node(n, **attrs)
            
            for u, v, attrs in self.graph.edges(data=True):
                # Add edge with weight if not already present or with higher weight
                if not simple_graph.has_edge(u, v) or simple_graph[u][v].get("weight", 0) < attrs.get("weight", 0.5):
                    simple_graph.add_edge(u, v, weight=attrs.get("weight", 0.5))
            
            # Apply community detection based on selected method
            if method == "louvain":
                partition = community_louvain.best_partition(simple_graph, weight="weight")
            elif method == "label_propagation":
                partition = {}
                label_partition = nx.algorithms.community.label_propagation.label_propagation_communities(simple_graph)
                for i, community in enumerate(label_partition):
                    for node in community:
                        partition[node] = i
            else:
                # Default to Louvain
                partition = community_louvain.best_partition(simple_graph, weight="weight")
            
            # Count communities
            community_counts = {}
            for node, community_id in partition.items():
                if community_id not in community_counts:
                    community_counts[community_id] = 0
                community_counts[community_id] += 1
            
            # Group results by layer and community
            community_nodes = {}
            for node, community_id in partition.items():
                if node not in self.graph.nodes:
                    continue
                    
                attrs = self.graph.nodes[node]
                layer = attrs.get("layer", "unknown")
                
                if community_id not in community_nodes:
                    community_nodes[community_id] = {
                        "id": community_id,
                        "size": community_counts[community_id],
                        "entities": [],
                        "events": [],
                        "risks": []
                    }
                
                node_info = {"id": node}
                
                # Add layer-specific information
                if layer == "entity":
                    node_info.update({
                        "name": attrs.get("name", "Unknown"),
                        "type": attrs.get("entity_type", ""),
                        "subtype": attrs.get("subtype", "")
                    })
                    community_nodes[community_id]["entities"].append(node_info)
                
                elif layer == "event":
                    node_info.update({
                        "title": attrs.get("title", "Unknown"),
                        "type": attrs.get("event_type", ""),
                        "date": attrs.get("event_date", "")
                    })
                    community_nodes[community_id]["events"].append(node_info)
                
                elif layer == "risk":
                    node_info.update({
                        "title": attrs.get("title", "Unknown"),
                        "type": attrs.get("risk_type", ""),
                        "severity": attrs.get("severity", 1)
                    })
                    community_nodes[community_id]["risks"].append(node_info)
            
            # Process communities by layer
            entity_communities = []
            event_communities = []
            risk_communities = []
            
            for comm_id, comm_data in community_nodes.items():
                if comm_data["entities"]:
                    entity_communities.append({
                        "id": comm_id,
                        "size": len(comm_data["entities"]),
                        "nodes": comm_data["entities"]
                    })
                
                if comm_data["events"]:
                    event_communities.append({
                        "id": comm_id,
                        "size": len(comm_data["events"]),
                        "nodes": comm_data["events"]
                    })
                
                if comm_data["risks"]:
                    risk_communities.append({
                        "id": comm_id,
                        "size": len(comm_data["risks"]),
                        "nodes": comm_data["risks"]
                    })
            
            # Sort communities by size
            entity_communities.sort(key=lambda x: x["size"], reverse=True)
            event_communities.sort(key=lambda x: x["size"], reverse=True)
            risk_communities.sort(key=lambda x: x["size"], reverse=True)
            
            # Add to results
            results["entity"] = entity_communities
            results["event"] = event_communities
            results["risk"] = risk_communities
            results["combined"] = sorted(list(community_nodes.values()), key=lambda x: x["size"], reverse=True)
        
        except Exception as e:
            logger.error(f"Error detecting communities with {method}: {e}")
        
        return results
    
    def find_paths(self, source_id: str, target_id: str, max_length: int = 3) -> List[Dict[str, Any]]:
        """
        Find paths between two nodes in the knowledge graph.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            max_length: Maximum path length
            
        Returns:
            List of paths found
        """
        paths = []
        
        try:
            # Reload the graph if empty
            if not self.graph.nodes:
                self.build_complete_graph()
            
            # Check if both nodes exist
            if source_id not in self.graph.nodes or target_id not in self.graph.nodes:
                return paths
            
            # Create a simplified graph for path finding
            simple_graph = nx.DiGraph()
            
            # Add nodes and edges from the main graph
            for n, attrs in self.graph.nodes(data=True):
                simple_graph.add_node(n, **attrs)
            
            for u, v, attrs in self.graph.edges(data=True):
                # Add edge with weight
                simple_graph.add_edge(u, v, **attrs)
            
            # Find all simple paths within max_length
            all_paths = []
            
            try:
                all_paths = list(nx.all_simple_paths(simple_graph, source_id, target_id, cutoff=max_length))
            except nx.NetworkXNoPath:
                # Try reverse direction
                try:
                    all_paths = list(nx.all_simple_paths(simple_graph, target_id, source_id, cutoff=max_length))
                    # Reverse paths
                    all_paths = [list(reversed(p)) for p in all_paths]
                except:
                    pass
            
            # Format each path
            for path in all_paths:
                path_data = {
                    "nodes": [],
                    "edges": [],
                    "length": len(path) - 1
                }
                
                # Add nodes
                for node_id in path:
                    attrs = self.graph.nodes[node_id]
                    layer = attrs.get("layer", "unknown")
                    
                    node_info = {"id": node_id, "layer": layer}
                    
                    # Add layer-specific information
                    if layer == "entity":
                        node_info.update({
                            "name": attrs.get("name", "Unknown"),
                            "type": attrs.get("entity_type", "")
                        })
                    elif layer == "event":
                        node_info.update({
                            "title": attrs.get("title", "Unknown"),
                            "type": attrs.get("event_type", "")
                        })
                    elif layer == "risk":
                        node_info.update({
                            "title": attrs.get("title", "Unknown"),
                            "type": attrs.get("risk_type", "")
                        })
                    
                    path_data["nodes"].append(node_info)
                
                # Add edges
                for i in range(len(path) - 1):
                    u, v = path[i], path[i+1]
                    
                    # Get edge data from graph
                    if simple_graph.has_edge(u, v):
                        edge_attrs = simple_graph[u][v]
                        edge_info = {
                            "source": u,
                            "target": v,
                            "type": edge_attrs.get("type", "connected_to"),
                            "layer": edge_attrs.get("layer", "unknown")
                        }
                        path_data["edges"].append(edge_info)
                    else:
                        # If edge doesn't exist in this direction, check reverse
                        if simple_graph.has_edge(v, u):
                            edge_attrs = simple_graph[v][u]
                            edge_info = {
                                "source": v,
                                "target": u,
                                "type": edge_attrs.get("type", "connected_to"),
                                "layer": edge_attrs.get("layer", "unknown"),
                                "reversed": True
                            }
                            path_data["edges"].append(edge_info)
                
                paths.append(path_data)
            
            # Sort paths by length
            paths.sort(key=lambda x: x["length"])
        
        except Exception as e:
            logger.error(f"Error finding paths between {source_id} and {target_id}: {e}")
        
        return paths
    
    def search_entities(self, term: str) -> List[Dict[str, Any]]:
        """
        Search for entities by name.
        
        Args:
            term: Search term
            
        Returns:
            List of matching entities
        """
        results = []
        
        try:
            # Case-insensitive search
            term = term.lower()
            
            entities = self.data_store.get_all_entities()
            
            for entity in entities:
                if term in entity.name.lower():
                    results.append({
                        "id": entity.id,
                        "name": entity.name,
                        "type": entity.type,
                        "subtype": entity.subtype,
                        "mentions": len(entity.mentions)
                    })
            
            # Sort by relevance (exact match first, then by mentions)
            results.sort(key=lambda x: (0 if x["name"].lower() == term else 1, -x["mentions"]))
        
        except Exception as e:
            logger.error(f"Error searching entities for '{term}': {e}")
        
        return results
    
    def search_events(self, term: str) -> List[Dict[str, Any]]:
        """
        Search for events by title or description.
        
        Args:
            term: Search term
            
        Returns:
            List of matching events
        """
        results = []
        
        try:
            # Case-insensitive search
            term = term.lower()
            
            events = self.data_store.get_all_events()
            
            for event in events:
                if term in event.title.lower() or term in event.description.lower():
                    results.append({
                        "id": event.id,
                        "title": event.title,
                        "description": event.description,
                        "type": event.event_type,
                        "date": event.event_date.isoformat(),
                        "entities": len(event.entities)
                    })
            
            # Sort by relevance (title match first, then description)
            results.sort(key=lambda x: (0 if term in x["title"].lower() else 1, x["date"], -x["entities"]))
        
        except Exception as e:
            logger.error(f"Error searching events for '{term}': {e}")
        
        return results
    
    def search_risks(self, term: str) -> List[Dict[str, Any]]:
        """
        Search for risks by title or description.
        
        Args:
            term: Search term
            
        Returns:
            List of matching risks
        """
        results = []
        
        try:
            # Case-insensitive search
            term = term.lower()
            
            risks = self.data_store.get_all_risks()
            
            for risk in risks:
                if term in risk.title.lower() or term in risk.description.lower():
                    results.append({
                        "id": risk.id,
                        "title": risk.title,
                        "description": risk.description,
                        "type": risk.risk_type,
                        "severity": risk.severity,
                        "likelihood": risk.likelihood
                    })
            
            # Sort by relevance (title match first, then by severity and likelihood)
            results.sort(key=lambda x: (0 if term in x["title"].lower() else 1, -x["severity"], -x["likelihood"]))
        
        except Exception as e:
            logger.error(f"Error searching risks for '{term}': {e}")
        
        return results
