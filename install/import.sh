#!/bin/bash

SQL_DIR=sql/
USERNAME=jennyzhou
DB=gis

psql -U $USERNAME -d $DB -f $SQL_DIR/Hausanschluss.sql
psql -U $USERNAME -d $DB -f $SQL_DIR/Kabelverteilerschrank.sql
psql -U $USERNAME -d $DB -f $SQL_DIR/Netzstation.sql
psql -U $USERNAME -d $DB -f $SQL_DIR/NSP-Kabel.sql

