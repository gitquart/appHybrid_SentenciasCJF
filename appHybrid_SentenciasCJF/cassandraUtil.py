import json
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import os
from InternalControl import cInternalControl
objControl= cInternalControl()


def getCluster():
    #Connect to Cassandra
    objCC=CassandraConnection()
    cloud_config={}
    zip_file='secure-connect-dbquart_serverless.zip'
    if objControl.heroku:
        cloud_config['secure_connect_bundle']=objControl.rutaHeroku+'/'+zip_file
    else:
        cloud_config['secure_connect_bundle']=objControl.rutaLocal+zip_file

    cloud_config['init-query-timeout']=10
    cloud_config['connect_timeout']=10
    cloud_config['set-keyspace-timeout']=10  


    auth_provider = PlainTextAuthProvider(objCC.cc_user,objCC.cc_pwd)
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider) 

    return cluster  
  



def executeNonQuery(query):

    cluster=getCluster()
    session = cluster.connect()
    session.default_timeout=70
    future = session.execute_async(query)
    future.result()
                         
    return True
   
def getQuery(query):

    cluster=getCluster()
    session = cluster.connect()
    session.default_timeout=70         
    future = session.execute_async(query)
    resultSet=future.result()
    cluster.shutdown()
                                           
    return resultSet    
          
def insertJSON(keySpaceTable,json_file):

    cluster=getCluster()
    session = cluster.connect()
    session.default_timeout=70           
    #Insert Data as JSON
    json_record=json.dumps(json_file)              
    insertSt="INSERT INTO "+keySpaceTable+" JSON '"+json_record+"';" 
    future = session.execute_async(insertSt)
    future.result()  
    cluster.shutdown()     
                    
                         
    return True


class CassandraConnection():
    cc_user='psXzplCMoTnTjWLSeAblXSkr'
    cc_keyspace='thesis'
    cc_pwd='_vGwtwEUsOxj9ZuSbm6SOJhyQOsU-s9QEzX7ZWZcRYKeew9sOqPeFmKr-pDzsIoisiF8aInS1HjSs7_fqZ9EZaMS96TNCwn_yReyjZvHuys+_fGSBuHKZz_+NTj6Z6L0'