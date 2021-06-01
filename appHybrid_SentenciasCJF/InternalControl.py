import os

class cInternalControl(object):
    idControl=12
    timeout=70
    hfolder='appHybrid_SentenciasCJF' 
    heroku=True
    rutaHeroku='/app/'+hfolder+'/'
    rutaLocal=os.getcwd()+'\\'+hfolder+'\\'
    download_dir=''
      