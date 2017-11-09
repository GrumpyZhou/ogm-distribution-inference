import networkx as nx
from itertools import tee
import time 
import os
from geopy.distance import vincenty
import numpy as np
import shapely.geometry as geo


# ------------------- Generate ground truth -----------------

# Merge nodes close enough by their mean center
def merge_nodes(nodes, threshold):
    t1 = time.time()
    merged_nodes = {}
    nodes.sort()
    origin_queue = list(nodes)
 
    while len(origin_queue) > 0:
        left_queue = []
        to_merged = []
        to_merged.append(origin_queue.pop())
        #print '>>>',to_merged, origin_queue
        while len(origin_queue) > 0:
            node = origin_queue.pop()
            merged_mean = np.mean(to_merged, axis=0)
            #print '::', node
            if vincenty(merged_mean, node).kilometers < threshold:
                #print 'merge', node
                to_merged.append(node)
            else:
                left_queue.append(node)
                #print 'left', node
        origin_queue = left_queue
        mean = tuple(np.mean(to_merged, axis=0))
        merged_nodes[mean] = to_merged
    print 'Merging time %s s'%(time.time()-t1)
    return merged_nodes


# Merge endpoints of cables with cabinets
def join_cables(origin_cables, target_nodes, threshold=5e-3):
    t1 = time.time()
    joint_cables = []
    count_joint = 0
    print 'Target nodes: %d'%len(target_nodes)
    for cable in origin_cables:
        for tp in target_nodes: 
            if vincenty(cable[0], tp).kilometers <= threshold:
                cable[0] = tp 
                count_joint += 1
            if vincenty(cable[-1], tp).kilometers <= threshold:
                cable[-1] = tp 
                count_joint += 1
        joint_cables.append(cable)
    print 'Joining cables took: %s s; Joint endpoints: %d'%(time.time()-t1, count_joint)
    return joint_cables


def generate_connected_subgraph(roads):
    graph = nx.Graph()
    for road in roads:
        sid, eid = tee(road) # Initial index of edge start and end node
        next(eid) # Move end node next to start
        for n1, n2 in zip(sid, eid):
            graph.add_edge(tuple(n1), tuple(n2))        
    subgraphs = nx.connected_component_subgraphs(graph)
    
    # Assign edge length
    #for e1, e2 in subgraph.edges_iter():
    #    subgraph[e1][e2]["length"] = vincenty(e1, e2).kilometers  
    return list(subgraphs)

def reduce_graph(graph, threshold=1e-3):
    to_replace = {}
    t1 = time.time()
    for n1 in graph.nodes():
        for n2 in graph.nodes():
            if n1 == n2 or n1 in to_replace:
                continue
            if vincenty(n1, n2).kilometers < 0.001:
                if graph.neighbors(n1) > graph.neighbors(n2):
                    to_replace[n2] = n1

    for n1 in to_replace:
        n1_ = to_replace[n1]
        for edge in graph.edges(n1):
            st, ed = edge
            if st == n1 and ed == n1_ or st == n1_ and ed == n1 :
                continue
            if st == n1 and ed != n1_:
                graph.add_edge(n1_, ed)
            if ed == n1 and st != n1_:
                graph.add_edge(st,n1_)
        graph.remove_node(n1)
    print 'Reducing graph took: %s Reduced Graph: %d edges, %d nodes Connected: %s'%(time.time() - t1, len(graph.edges()), len(graph.nodes()), nx.is_connected(graph))
    return graph


# -------------------- Inference --------------------

def split_by_difference(lines):
    # Split given lines by intersection between every pair
    total = len(lines)
    split_lines = []
    split_lines_coords = []

    for i in range(total):
        l1 = geo.LineString(lines[i])
        #print list(l1.coords)
        crossed = []
        for j in range(total):
            if i == j:
                continue
            l2 = geo.LineString(lines[j])
            if l1.crosses(l2):
                crossed.append(l2)
        if not crossed:
            # l1 has no intersection with other roads
            split_lines.append(l1)
            split_lines_coords.append(list(l1.coords))
        else:
            # Split l2 by its intersection with l1
            for l2 in crossed:
                split = l1.difference(l2)
                if split.geom_type == "MultiLineString":
                    for line in split.geoms:
                        split_lines.append(line)
                        split_lines_coords.append(list(line.coords))
                elif split.geom_type == "LineString":
                    split_lines.append(split)
                    split_lines_coords.append(list(split.coords))
    return split_lines_coords


def filter_by_boundary(nodes, boundary):
    '''
    nodes: list of coordiantes representing set of points
    boundary: list of coordinates representing a polygon
    '''
    # Filter out nodes that are not within the area
    points = geo.MultiPoint(list(nodes))
    polygon = geo.Polygon(boundary)
    contained = filter(polygon.contains, points)
    filtered = set() 
    for p in contained:
        filtered.update(set(p.coords))
    print 'Original nodes %d >> Strictly within area %d'%(len(nodes),len(filtered))
    return filtered   


def generate_mst_direct(nodes):
    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    for i in range(len(nodes)):
        for j in range(len(nodes)):
            if i < j:
                u = nodes[i]
                v = nodes[j]
                d = vincenty(u, v).kilometers
                graph.add_edge(u, v, weight=d)
                #graph.append("%s %s %f" % (u, v, d))
    #G = nx.parse_edgelist(graph, nodetype = float, data=(('weight',float),))
    mst = nx.minimum_spanning_tree(graph)
    print 'Graph edges %d, nodes %d'%(len(mst.edges()), len(mst.nodes()))
    return mst


def generate_mst_improved(nodes, map_edges):
    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    for i in range(len(nodes)):
        for j in range(len(nodes)):
            if i < j:
                u = nodes[i]
                v = nodes[j]
                d = vincenty(u, v).kilometers
                graph.add_edge(u, v, weight=d)
                #graph.append("%s %s %f" % (u, v, d))
    #G = nx.parse_edgelist(graph, nodetype = float, data=(('weight',float),))
    mst = nx.minimum_spanning_tree(graph)
    print 'Graph edges %d, nodes %d'%(len(mst.edges()), len(mst.nodes()))

    # Add house connection
    mst.add_edges_from(map_edges)
    print 'After adding house connection >> edges %d, nodes %d'%(len(mst.edges()), len(mst.nodes()))
    return mst


# --------------------- Graph saving and loading ------------------------
def sav_graph_npy(sav_path, graph):
    graph_dict = {}
    graph_dict['nodes'] = graph.nodes()
    graph_dict['edges'] = graph.edges()
    np.save(sav_path, graph_dict)
    print 'Save graph as %s'%sav_path
    
def load_graph_npy(path, set_lentgh=True):
    data = np.load(path).item()
    G = nx.Graph()
    G.add_nodes_from(data['nodes'])
    G.add_edges_from(data['edges'])
    total_length = set_edge_length(G)
    return G, total_length

def set_edge_length(graph):
    attr = {}
    total = 0
    for edge in graph.edges():
        length = vincenty(edge[0], edge[1]).meters
        attr[edge] = length
        total += length
    nx.set_edge_attributes(graph, 'length',attr)
    return  total


def sav_graph_to_csv(save_dir, prefix, graph):
    node_file = os.path.join(save_dir,'%s_nodes.csv'%prefix)
    with open(node_file,'wb') as nf:
        # Save nodes
        for node in graph.nodes():
            nf.write('POINT(%s %s);\n'%(node[1],node[0]))
    print 'Save to %s'%node_file

    edge_file = os.path.join(save_dir,'%s_edges.csv'%prefix)
    with open(edge_file,'wb') as ef:
        # Save edges
        for edge in graph.edges():
            n1 = edge[0]
            n2 = edge[1]
            ef.write('LINESTRING(%s %s, %s %s);\n'%(n1[1],n1[0],n2[1],n2[0]))    
    print 'Save to %s'%edge_file


# --------------------- Graph Evaluation----------------------


# Map the mean node in gt graph with any one node from merged nodes that is also in the inference graph 
def map_merged_pair(merged_dict, graph_gt, graph_inf):
    pair = {}
    for n1 in merged_dict:
        if n1 in graph_gt.nodes():
            mapped = merged_dict[n1]
            for n2 in mapped:
                if tuple(n2) in graph_inf.nodes():
                    pair[n1] = tuple(n2)
                    break
    return pair


