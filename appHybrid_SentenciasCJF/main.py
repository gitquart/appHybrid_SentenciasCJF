#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 28 MAY 2021

@author: quart

Important data to develop the code:

-Link to get "sentencias":     
https://bj.scjn.gob.mx/busqueda?q=*&indice=sentencias_pub

"""

import cassandraUtil as db
import utils as tool
from InternalControl import * 

objControl= cInternalControl()
print('Running program...')
querySt="select query,page,limit_iteration from thesis.cjf_control where id_control="+str(objControl.idControl)+"  ALLOW FILTERING"
resultSet=db.getQuery(querySt)
lsInfo=[]
if resultSet: 
    for row in resultSet:
        lsInfo.append(str(row[0]))
        lsInfo.append(str(row[1]))
        lsInfo.append(str(row[2]))
        print('Current query :',str(row[0]))
        print('Page:',str(row[1]))
        print('Limit:',str(row[2]))
startPage=int(lsInfo[1])
limit=int(lsInfo[2])
tool.readUrl(startPage,limit)  

  

