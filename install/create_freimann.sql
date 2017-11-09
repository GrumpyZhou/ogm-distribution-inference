CREATE TABLE freimann_processed_nodes (
	id int NOT NULL,
	area_id int NOT NULL,
	node_type text,
	way geometry(Point, 31464)
);

CREATE SEQUENCE freimann_processed_nodes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE freimann_processed_nodes_id_seq OWNED BY freimann_processed_nodes.id;
ALTER TABLE ONLY freimann_processed_nodes ALTER COLUMN id SET DEFAULT nextval('freimann_processed_nodes_id_seq'::regclass);

CREATE TABLE freimann (
	id int NOT NULL,
	center geometry(Point,31464),	
	boundary geometry(Polygon,31464)
);

-- Almost whole:
INSERT INTO freimann(id, center, boundary) SELECT 1, ST_Transform(ST_SetSRID(ST_FlipCoordinates(ST_GeomFromText('POINT(48.2053 11.6039)')), 4326), 31464), 
ST_Transform(ST_SetSRID(ST_FlipCoordinates(ST_GeomFromText('POLYGON((48.20965 11.59493, 48.20757 11.61433,48.19972 11.61199,48.20181 11.59332,48.20965 11.59493))')), 4326), 31464);

-- Sub area1:
INSERT INTO freimann(id, center, boundary) SELECT 2, ST_Transform(ST_SetSRID(ST_FlipCoordinates(ST_GeomFromText('POINT(48.20737 11.59864)')), 4326), 31464), 
ST_Transform(ST_SetSRID(ST_FlipCoordinates(ST_GeomFromText('POLYGON((48.20965 11.59493, 48.20879 11.60122,48.20641 11.60081,48.20687 11.59431,48.20965 11.59493))')), 4326),31464);

-- Sub area more clear separate:
INSERT INTO freimann(id, center, boundary) SELECT 3, ST_Transform(ST_SetSRID(ST_FlipCoordinates(ST_GeomFromText('POINT(48.20737 11.59864)')), 4326), 31464), 
ST_Transform(ST_SetSRID(ST_FlipCoordinates(ST_GeomFromText('POLYGON((48.20963 11.59488, 48.20884 11.59997, 48.20674 11.59947,  48.20720 11.59440,48.20963 11.59488))')), 4326),31464);






