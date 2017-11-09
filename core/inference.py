import time 
import random
import numpy as np
from data_handler import *
from inference_handler import *
import networkx as nx

# Global database setting
DB_NAME = 'gis'
DB_USER = 'jennyzhou'

def store_merged_nodes(area_id):
    # Connect to psql
    conn = connect_to_psql(dbname=DB_NAME, user=DB_USER)

    # Select transformers, cabinets
    transformers = select_transformers(area_id, conn)
    cabinets = select_cabinets(area_id, conn)
    print 'Transformers: %d \nCabinets: %d \n'% (len(transformers), len(cabinets))

    # Merge duplicate transformers and cabinets
    origin_trans = list(transformers)
    merged_trans = list(merge_nodes(origin_trans, threshold=1e-4).keys())
    print 'Original transformers %d  Merged transformers %d'%(len(transformers), len(merged_trans))

    origin_cabs = list(cabinets)
    merged_cabs = list(merge_nodes(origin_cabs, threshold=5e-3).keys())
    print 'Original cabinets %d  Merged cabinets %d'%(len(cabinets), len(merged_cabs))
    
    # Save merged transformers and cabinets in table freimann_processed_nodes
    insert_merged_nodes(area_id, merged_trans, merged_cabs, conn)

def generate_ground_truth(area_id, store_merged_nodes=False):
    '''Generate ground truth graph for the area specified by area_id'''
    # Connect to psql
    conn = connect_to_psql(dbname=DB_NAME, user=DB_USER)

    # Select merged transformers, cabinets and houses
    merged_trans, merged_cabs = select_merged_trans_cabs(area_id, conn)
    print 'Transformers: %d \nCabinets: %d '% (len(merged_trans), len(merged_cabs))
    
    # Select NSP Cables
    cables = select_cables(area_id, conn)
    print 'Cables: %d'%len(cables)
    
    # Join transformers and cabinets with cables endpoints
    origin_cables = list(cables)
    target_nodes = list(merged_cabs + merged_trans)
    joint_cables = join_cables(origin_cables, target_nodes, threshold=5e-3)

    # Generate connected graphs with joint edges
    subgraphs = generate_connected_subgraph(joint_cables)
    print 'Generated subgraphs:',len(subgraphs)

    # Select the graph with most edges
    lens = [len(graph.edges()) for graph in subgraphs]
    graph = subgraphs[np.argsort(lens)[-1]]
    print 'Largest Graph edges: %d nodes: %d connected: %s'%(len(graph.edges()), len(graph.nodes()), nx.is_connected(graph))   

    # Reduce duplicated nodes and edges
    reduced_graph = reduce_graph(graph)

    # Save graph
    sav_graph_npy('../graph/aid_%d_gt.npy'%area_id, reduced_graph)
 
def inference(area_id):
    # Connect to psql
    conn = connect_to_psql(dbname=DB_NAME, user=DB_USER)

    # Select freimann area
    center, boundary = select_freimann_subarea(area_id, conn)

    # Select roads within freimann
    roads = select_roads(area_id, conn)

    # Split roads 
    split_roads = split_by_difference(roads)
    print 'Original roads: %d Split roads: %d'%(len(roads), len(split_roads))

    # Find road nodes
    road_nodes = set()
    for rd in split_roads:
        road_nodes.add(tuple(rd[0]))
        road_nodes.add(tuple(rd[-1]))
    print 'Approximated road nodes %d' % len(road_nodes)

    # Filter out road nodes out of the area boundary
    filtered_road_nodes = filter_by_boundary(road_nodes, boundary)

    # Get node sets and its projection 
    orig_nodes, proj_nodes, map_edges = select_nodes_and_projection(area_id, conn)
    print 'Original nodes %d Proj nodes %d' % (len(orig_nodes), len(proj_nodes))

    # V2: Generate MST with projected nodes only
    mst_2 = generate_mst_improved(list(filtered_road_nodes | proj_nodes), map_edges)
    sav_graph_npy('../graph/aid_%d_inf_v2.npy'%area_id, mst_2)

    # V1: Generate MST with all nodes
    mst_1 = generate_mst_direct(list(filtered_road_nodes | orig_nodes | proj_nodes))
    sav_graph_npy('../graph/aid_%d_inf_v1.npy'%area_id, mst_1)
    
if __name__ == '__main__':
    area_id = 3
    store_merged_nodes(area_id)
    generate_ground_truth(area_id)
    inference(area_id)
    

