#!/bin/bash
if [ ! -d "sql" ]; then
        mkdir sql
fi

# Point
shp2pgsql  -I -s  31464  Hausanschluss.shp Freimann_Hausanschluss > sql/Hausanschluss.sql

# Point
shp2pgsql  -I -s  31464  Kabelverteilerschrank.shp Freimann_Kabelverteilerschrank > sql/Kabelverteilerschrank.sql

# MultiPolygon 
shp2pgsql  -I -s  31464  Netzstation.shp Freimann_Netzstation > sql/Netzstation.sql

# MultiLineString 
shp2pgsql  -I -s  31464  NSP-Kabel.shp Freimann_NSP_Kabel > sql/NSP-Kabel.sql


# Point
#shp2pgsql  -I -s  31464  Mast.shp Freimann_Mast > Mast.sql

# MultiLineString 
#shp2pgsql  -I -s  31464  MSP-Freileitung.shp Freimann_MSP_Freileitung > sql/MSP-Freileitung.sql

# MultiLineString 
#shp2pgsql  -I -s  31464  MSP-Kabel.shp Freimann_MSP_Kabel > sql/MSP-Kabel.sql

# MultiPolygon 
#shp2pgsql  -I -s  31464  Umspannwerk.shp Freimann_Umspannwerk > sql/Umspannwerk.sql

# MULTILINESTRING
#shp2pgsql  -I -s  31464  HSP-Freileitung.shp Freimann_HSP_Freileitung > sql/HSP-Freileitung.sql

# MultiLineString
#shp2pgsql  -I -s  31464  HSP-Kabel.shp Freimann_HSP_Kabel > sql/HSP-Kabel.sql

# MultiLineString 
#shp2pgsql  -I -s  31464  NSP-Freileitungen.shp Freimann_NSP_Freileitungen > sql/NSP-Freileitungen.sql

