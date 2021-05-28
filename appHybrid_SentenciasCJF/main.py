#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 28 MAY 2021

@author: quart

Important data to develop the code:

-Link to get "sentencias":     
https://bj.scjn.gob.mx/busqueda?q=*&indice=sentencias_pub

"""

import json
import os
import cassandraUtil as db
import utils as tool
from InternalControl import cInternalControl

objControl= cInternalControl()
print('Running program...')
querySt="select query,page from thesis.cjf_control where id_control="+str(objControl.idControl)+"  ALLOW FILTERING"
resultSet=db.getQuery(querySt)
lsInfo=[]
if resultSet: 
    for row in resultSet:
        lsInfo.append(str(row[0]))
        lsInfo.append(str(row[1]))
        print('Value from cassandra:',str(row[0]))
        print('Value from cassandra:',str(row[1]))
startID=int(lsInfo[1])
#The limits in readUrl may vary up to the need of the search
tool.readUrl(1,startID,5000000)  

  

