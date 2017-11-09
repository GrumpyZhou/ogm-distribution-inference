""" This script contains interfaces to manipulate and process data required by the inference. """
import psycopg2
import json

def connect_to_psql(dbname='gis', user='', password='', hostaddr='', port='5432', remote=False):
    try:
        if remote:
            token = "dbname=%s user=%s host=%s port=%s password=%s"%(dbname, user, hostaddr, port, password)
            conn =  psycopg2.connect(token)
        else:
            conn = psycopg2.connect("dbname=%s user=%s"%(dbname, user))
        print('Connection established. DNS info: %s' % conn.dsn)
    except:
        print('Fail to connect to Postgres Server')
    return conn


def insert_freimann_subarea(area_id, center_geo_txt, bounday_geo_txt, conn):
    cur = conn.cursor()
    cur.execute("INSERT INTO freimann(id, center, boundary) SELECT %d, ST_Transform(ST_SetSRID(ST_FlipCoordinates(ST_GeomFromText(\'%s\')), 4326), 31464),ST_Transform(ST_SetSRID(ST_FlipCoordinates(ST_GeomFromText(\'%s\')), 4326), 31464);"%(area_id, center_geo_txt, bounday_geo_txt))
    conn.commit()
    cur.close()
    print 'Insert freimann subarea with id=%d'%save_id


def insert_merged_nodes(aread_id, merged_trans, merged_cabs, conn):
    cur = conn.cursor()
    for cab in merged_cabs:
        cab_wkt = "'POINT(%f %f)'"%(cab[0], cab[1])
        insert_sql = "INSERT INTO freimann_processed_nodes(area_id, node_type, way) VALUES (%d, 'cabinet', ST_Transform(ST_SetSRID(ST_FlipCoordinates(ST_GeomFromText(%s)), 4326), 31464));"%(aread_id, cab_wkt)
        cur.execute(insert_sql)

    for trans in merged_trans:
        trans_wkt = "'POINT(%f %f)'"%(trans[0], trans[1])
        insert_sql = "INSERT INTO freimann_processed_nodes(area_id, node_type, way) VALUES (%d, 'transformer', ST_Transform(ST_SetSRID(ST_FlipCoordinates(ST_GeomFromText(%s)), 4326), 31464));"%(aread_id, trans_wkt)
        cur.execute(insert_sql)
    conn.commit()
    cur.close()
    print 'Insert merged transfomers and cabinets into freimann processed nodes'
    

def select_freimann_subarea(area_id, conn):
    cur = conn.cursor()
    cur.execute("SELECT ST_AsGeoJSON(ST_FlipCoordinates(ST_Transform(center, 4326))), "
            "ST_AsGeoJSON(ST_FlipCoordinates(ST_Transform(boundary, 4326))) FROM freimann WHERE id=%d;"%area_id)
    freimann = cur.fetchall()
    cur.close()
    core_center, core_boundary = json.loads(freimann[0][0])['coordinates'], json.loads(freimann[0][1])['coordinates'][0]
    print 'Select freimann subarea with id=%d'%area_id
    return core_center, core_boundary

def select_transformers(area_id, conn):
    # Transformers
    cur = conn.cursor()
    cur.execute("SELECT ST_AsGeoJSON(ST_Collect(ST_FlipCoordinates(ST_Transform(ST_Centroid(t1.geom), 4326))))"
                "From freimann_netzstation AS t1, freimann AS t2 "
                "WHERE ST_Within(t1.geom, t2.boundary) AND t2.id=%d;"%area_id)
    transformers = cur.fetchall()
    cur.close()
    return json.loads(transformers[0][0])['coordinates']

def select_cabinets(area_id, conn):
    # Cabinets
    cur = conn.cursor()
    cur.execute("SELECT ST_AsGeoJSON(ST_Collect(ST_FlipCoordinates(ST_Transform(ST_Centroid(t1.geom), 4326))))"
                "From freimann_kabelverteilerschrank AS t1, freimann AS t2 "
                "WHERE  ST_Intersects(t1.geom, t2.boundary) AND t2.id=%d;"%area_id)
    cabinets = cur.fetchall()
    cur.close()
    return json.loads(cabinets[0][0])['coordinates']

def select_merged_trans_cabs(area_id, conn):
    cur = conn.cursor()
    cur.execute("SELECT ST_AsGeoJSON(ST_Collect(ST_FlipCoordinates(ST_Transform(way, 4326)))) FROM freimann_processed_nodes "
                "WHERE node_type='transformer' AND area_id=%d;"%area_id)
    processed_trans = cur.fetchall()
    merged_trans = json.loads(processed_trans[0][0])['coordinates']
    cur.execute("SELECT ST_AsGeoJSON(ST_Collect(ST_FlipCoordinates(ST_Transform(way, 4326)))) FROM freimann_processed_nodes "
                "WHERE node_type='cabinet' AND area_id=%d;"%area_id)
    processed_cabs = cur.fetchall()
    merged_cabs = json.loads(processed_cabs[0][0])['coordinates']
    cur.close()
    return merged_trans, merged_cabs

def select_houses(area_id, conn):
    # Houses
    cur = conn.cursor()
    cur.execute("SELECT ST_AsGeoJSON(ST_Collect(ST_FlipCoordinates(ST_Transform(ST_Centroid(t1.geom), 4326))))"
                "From freimann_hausanschluss AS t1, freimann AS t2 "
                "WHERE ST_Within(t1.geom, t2.boundary) AND t2.id=%d;"%area_id)
    houses = cur.fetchall()
    cur.close()
    return json.loads(houses[0][0])['coordinates']

def select_cables(area_id, conn):
    cur = conn.cursor()
    cur.execute("SELECT ST_AsGeoJSON(ST_FlipCoordinates(ST_Transform(t1.geom, 4326)))"
                "From freimann_nsp_kabel AS t1, freimann AS t2 "
                "WHERE ST_Within(t1.geom, t2.boundary) AND t2.id=%d;"%area_id)
    cables = cur.fetchall()
    cur.close()
    return [json.loads(line[0])['coordinates'][0] for line in cables]

def select_roads(area_id, conn):
    cur = conn.cursor()
    cur.execute("SELECT ST_AsGeoJSON(ST_Collect((ST_FlipCoordinates(ST_Transform(way, 4326))))) "
                "FROM planet_osm_line AS t1, freimann AS t2 "
                "WHERE ST_Intersects(t1.way, ST_Transform(t2.boundary, 900913)) " 
                "AND t2.id=%d;"%area_id)
    roads = cur.fetchall()
    cur.close()
    return json.loads(roads[0][0])['coordinates']

def select_nodes_and_projection(area_id, conn):
    # Select roads near a house, transformer or a cabinet 
    cur = conn.cursor()
    # Create intermediate table
    cur.execute("CREATE TABLE IF NOT EXISTS tempHsRd (hway geometry(Point,900913), rway geometry(LineString,900913), distance float);")
    conn.commit()   
    # clean entries
    cur.execute("DELETE FROM temphsrd;")
    conn.commit()

    """ Original transformation and cabinets
    cur.execute("INSERT INTO temphsrd "
                "(SELECT t1.way, t2.way, ST_Distance(t1.way, t2.way) "
                "FROM "
                "(SELECT ST_Transform(ST_Centroid(geom), 900913) AS way "
                "FROM "
                "(SELECT geom from freimann_kabelverteilerschrank "
                "UNION SELECT geom from freimann_netzstation "
                "UNION SELECT geom from freimann_hausanschluss) AS t, freimann "
                "WHERE ST_Within(geom, boundary) AND id=%d) AS t1 LEFT JOIN "
                "(SELECT way FROM planet_osm_line, freimann AS t0 "
                "WHERE ST_Intersects(way, ST_Transform(t0.boundary, 900913)) " 
                "AND t0.id=%d) AS t2 "            
                "ON ST_DWithin(t1.way, t2.way, 20) = true);" %(area_id,area_id))
    """
    cur.execute("INSERT INTO temphsrd "
                "(SELECT t1.way, t2.way, ST_Distance(t1.way, t2.way) "
                "FROM (SELECT ST_Transform(geom, 900913) AS way "
                "FROM (SELECT way AS geom FROM freimann_processed_nodes WHERE area_id = %d "
                "UNION SELECT ST_Centroid(geom) FROM freimann_hausanschluss) AS t, freimann "
                "WHERE ST_Within(geom, boundary) AND id=%d) AS t1 LEFT JOIN "
                "(SELECT way FROM planet_osm_line, freimann AS t0 "
                "WHERE ST_Intersects(way, ST_Transform(t0.boundary, 900913)) "
                "AND t0.id=%d) AS t2 "
                "ON ST_DWithin(t1.way, t2.way, 20) = true); "%(area_id, area_id, area_id))
    conn.commit()
    
    cur.execute("SELECT ST_AsGeoJSON(ST_FlipCoordinates(ST_Transform(hway, 4326))), "
                "ST_AsGeoJSON(ST_FlipCoordinates(ST_Transform(ST_ClosestPoint(rway, hway), 4326))) "
                "FROM temphsrd "
                "WHERE (hway, distance) IN "
                "(SELECT hway, MIN(distance) FROM temphsrd GROUP BY hway);")
    node_proj_map = cur.fetchall()
    cur.close()
    
    # return origin_nodes and proj_nodes
    orig_nodes = set()
    proj_nodes = set()
    map_edges = []
    for i in range(len(node_proj_map)):
        orig = json.loads(node_proj_map[i][0])['coordinates']
        orig_nodes.add(tuple(orig))
        proj = json.loads(node_proj_map[i][1])['coordinates']
        proj_nodes.add(tuple(proj))
        map_edges.append([tuple(orig),tuple(proj)])

    return orig_nodes, proj_nodes, map_edges
