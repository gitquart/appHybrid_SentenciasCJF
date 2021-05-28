import cassandraUtil as db
import json
import os
from selenium import webdriver
import chromedriver_autoinstaller
import requests 
from bs4 import BeautifulSoup
import time
from InternalControl import cInternalControl
from selenium.webdriver.chrome.options import Options

objControl=cInternalControl()

date_null='1000-01-01'
msg_error="Error Page!"
thesis_id=[ 'lblTesisBD','lblInstancia','lblFuente','lblLocMesAño','lblEpoca','lblLocPagina','lblTJ','lblRubro','lblTexto','lblPrecedentes']
thesis_class=['publicacion']
precedentes_list=['francesa','nota']
ls_months=['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']
thesis_added=False



def returnChromeSettings():
    browser=''
    chromedriver_autoinstaller.install()
    if objControl.heroku:
        #Chrome configuration for heroku
        chrome_options= webdriver.ChromeOptions()
        chrome_options.binary_location=os.environ.get("GOOGLE_CHROME_BIN")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")

        browser=webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"),chrome_options=chrome_options)

    else:
        options = Options()
        profile = {"plugins.plugins_list": [{"enabled": True, "name": "Chrome PDF Viewer"}], # Disable Chrome's PDF Viewer
               "download.default_directory": objControl.download_dir , 
               "download.prompt_for_download": False,
               "download.directory_upgrade": True,
               "download.extensions_to_open": "applications/pdf",
               "plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome
               }           

        options.add_experimental_option("prefs", profile)
        browser=webdriver.Chrome(options=options)  

    

    return browser 


"""
readUrl

Reads the url from the jury web site
"""

def readUrl(sense,l_bot,l_top):
    
    res=''
    #Can use noTesis as test variable too
    browser=returnChromeSettings()
    noTesis=0
    print('Starting process...')
    #Import JSON file  
    if objControl.heroku:   
        json_thesis=devuelveJSON(objControl.rutaHeroku+'thesis_json_base.json')  
    else:
        json_thesis=devuelveJSON(objControl.rutaLocal+'thesis_json_base.json')

    for x in range(l_bot,l_top):
        print('Current thesis:',str(x))
        res=prepareThesis(x,json_thesis,browser)
        # "m" means it is a missing space, no thesis found, then stop the program
        if res=='m':
            print("Main program is done")
            os.sys.exit(0)
        if res!='':
            #Check if the record exist
            idThesis=res['id_thesis']
            heading=res['heading']
            querySt="select id_thesis from thesis.tbthesis where id_thesis="+str(idThesis)+" and heading='"+heading+"'"
            resultSet=db.getQuery(querySt)
            if resultSet:
                pass
            else:
                #Insert JSON
                res=db.insertJSON(res)  
                if res:
                    print('Thesis ready ID: ',x) 
                    querySt="update thesis.cjf_control set page="+str(x)+" where  id_control=4;"
                    db.executeNonQuery(querySt)                  
    browser.quit()  
    
    return 'It is all done'
   

"""
prepareThesis:
    Reads the url where the service is fetching data from thesis
"""

def prepareThesis(id_thesis,json_thesis,browser): 
    
    result=''
    strIdThesis=str(id_thesis) 
    url="https://sjf2.scjn.gob.mx/detalle/tesis/"+strIdThesis
    response= requests.get(url)
    status= response.status_code
    if status==200:
        browser.get(url)
        #30 seconds of waiting
        time.sleep(30)
        thesis_html = BeautifulSoup(browser.page_source, 'lxml')
        title=thesis_html.find('title')
        title_text=title.text
        if strIdThesis in title_text.strip():   
            json_full=fillJson(json_thesis,browser,strIdThesis)
            result=json_full
        else:
            print('Missing thesis at ID:',strIdThesis)
            querySt="update thesis.cjf_control set page="+strIdThesis+" where  id_control=4;"
            db.executeNonQuery(querySt)
            print('-------------------------------------------')
            print('Hey, you can turn me off now!')
            print('-------------------------------------------')
            result='m'
                  
    else:
        print('Server failure:',strIdThesis)
        result=''
        
    return  result

def clearJSON(json_thesis):
    json_thesis['id_thesis']=''
    json_thesis['lst_precedents'].clear()
    json_thesis['thesis_number']=''
    json_thesis['instance']=''
    json_thesis['source']=''
    json_thesis['book_number']=''  
    json_thesis['publication_date']='' 
    json_thesis['dt_publication_date']=''
    json_thesis['period']=''
    json_thesis['page']=''
    json_thesis['jurisprudence_type']=''
    json_thesis['type_of_thesis']=''
    json_thesis['subject']=''
    json_thesis['subject_1']=''
    json_thesis['subject_2']=''
    json_thesis['subject_3']=''
    json_thesis['heading']=''
    json_thesis['text_content']=''
    json_thesis['publication']=''
    json_thesis['multiple_subjects']=''


def fillJson(json_thesis,browser,strIdThesis):
    clearJSON(json_thesis)   
    json_thesis['id_thesis']=int(strIdThesis)
    #Get values from header, and body of thesis
    val=''
    val=devuelveElemento('//*[@id="divStickyTbody"]/div[3]/div[1]/p',browser).text
    val=val.replace('Tesis:','').strip()
    json_thesis['thesis_number']=val
    val=''
    val=devuelveElemento('//*[@id="divStickyTbody"]/div[2]/div[1]/p',browser).text
    val=val.replace('Instancia:','').strip()
    json_thesis['instance']=val
    val=''
    val=devuelveElemento('//*[@id="divStickyTbody"]/div[3]/div[2]/p',browser).text
    val=val.replace('Fuente:','').strip()
    json_thesis['source']=val
    chunks=val.split('.')
    json_thesis['book_number']=chunks[1].replace('\n','')
    #Dates fields
    val=''
    val=devuelveElemento('//*[@id="divDetalle"]/div/div/div/div/div[3]/jhi-tesis-detalle/div[4]/div[4]',browser).text
    json_thesis['publication']=val  
    chunks=val.split(' ')
    dateStr=chunks[6]+'-'+chunks[8]+'-'+chunks[10]
    json_thesis['dt_publication_date']=getCompleteDate(dateStr) 
    json_thesis['publication_date']=json_thesis['dt_publication_date']
    val=''
    val=devuelveElemento('//*[@id="divStickyTbody"]/div[2]/div[2]/p',browser).text
    json_thesis['period']=val.strip()
    if val.strip()=='Quinta Época':
        json_thesis['period_number']=5
    if val.strip()=='Sexta Época':
        json_thesis['period_number']=6
    if val.strip()=='Séptima Época':
        json_thesis['period_number']=7
    if val.strip()=='Octava Época':
        json_thesis['period_number']=8        
    if val.strip()=='Novena Época':
        json_thesis['period_number']=9
    if val.strip()=='Décima Época':
        json_thesis['period_number']=10

    val=''
    val=devuelveElemento('//*[@id="divStickyTbody"]/div[3]/div[3]/p',browser).text
    val=val.replace('Tipo:','').strip()
    json_thesis['type_of_thesis']=val  
    val=''
    val=devuelveElemento('//*[@id="divStickyTbody"]/div[2]/div[3]/p',browser).text
    val=val.replace('Materia(s):','').strip() 
    if ',' in val:
        chunks=val.split(',')
        count=len(chunks)
        json_thesis['subject']=chunks[0]
        json_thesis['subject_1']=chunks[1]   
        if count==3:
            json_thesis['subject_2']=chunks[1]
        json_thesis['multiple_subjects']=True    

    else:
        json_thesis['subject']=val
        json_thesis['multiple_subjects']=False

    val=''
    #Heading
    val=devuelveElemento('//*[@id="divRubro"]/p',browser).text
    val=val.replace("'",'').strip()  
    json_thesis['heading']=val 
    #Main text
    val=devuelveElemento('//*[@id="divTexto"]',browser).text
    val=val.replace("'",'').strip() 
    json_thesis['text_content']=val 
    #Precedent
    val=devuelveElemento('//*[@id="divPrecedente"]',browser).text
    val=val.replace("'",'').strip() 
    json_thesis['lst_precedents'].append(val)



    return json_thesis    
                                 

def getCompleteDate(pub_date):
    pub_date=pub_date.strip()
    if pub_date!='':
        chunks=pub_date.split('-')
        month=str(chunks[1].strip())
        day=str(chunks[0].strip())
        year=str(chunks[2].strip())
        month_lower=month.lower()
        for item in ls_months:
            if month_lower==item:
                month=str(ls_months.index(item)+1)
                if len(month)==1:
                    month='0'+month
                    break
        if day=='':
            day='01'        
                
    completeDate=year+'-'+month+'-'+day                   
    return completeDate



def getIDLimit(sense,l_bot,l_top,period):
    
    if period==10:
        strperiod='Décima Época'
  
    #Onwars for    
    if(sense==1):
        for x in range(l_bot,l_top):
            res=searchInUrl(x,strperiod)
            if res==1:
                break
                
    #Backwards For             
    if(sense==2):
        for x in range(l_top,l_bot,-1): 
            res=searchInUrl(x,strperiod)
            if res==1:
                break
           
            
def searchInUrl(x,strperiod):
    strIdThesis=str(x) 
    url="https://sjf.scjn.gob.mx/SJFSist/Paginas/DetalleGeneralV2.aspx?ID="+strIdThesis+"&Clase=DetalleTesisBL&Semanario=0"
    response= requests.get(url)
    status= response.status_code
    if status==200:
        print('ID:',str(x))
        browser.get(url)
        time.sleep(1)
        thesis_html = BeautifulSoup(browser.page_source, 'lxml')
        title=thesis_html.find('title')
        title_text=title.text
        if title_text.strip() != msg_error:
            thesis_period=thesis_html.find(id='lblEpoca')
            data=thesis_period.text
            if data!='':
                if data.strip()=='Décima Época':
                    print('ID for ',strperiod,' found in :',strIdThesis)
                    return 1
               
                    
def devuelveJSON(jsonFile):
    with open(jsonFile) as json_file:
        jsonObj = json.load(json_file)
    
    return jsonObj 

def devuelveElemento(xPath, browser):
    cEle=0
    while (cEle==0):
        cEle=len(browser.find_elements_by_xpath(xPath))
        if cEle>0:
            ele=browser.find_elements_by_xpath(xPath)[0]

    return ele  

def devuelveListaElementos(xPath, browser):
    cEle=0
    while (cEle==0):
        cEle=len(browser.find_elements_by_xpath(xPath))
        if cEle>0:
            ele=browser.find_elements_by_xpath(xPath)

    return ele     
    

    