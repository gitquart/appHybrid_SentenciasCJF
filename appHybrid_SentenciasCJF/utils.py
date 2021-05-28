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
BROWSER=''
ls_months=['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']
thesis_added=False



def returnChromeSettings():
    global BROWSER
    chromedriver_autoinstaller.install()
    if objControl.heroku:
        #Chrome configuration for heroku
        chrome_options= webdriver.ChromeOptions()
        chrome_options.binary_location=os.environ.get("GOOGLE_CHROME_BIN")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")

        BROWSER=webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"),chrome_options=chrome_options)

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
        BROWSER=webdriver.Chrome(options=options)  



"""
readUrl

Reads the url from the jury web site
"""

def readUrl(startPage):
    returnChromeSettings()
    print('Starting process...')
    url="https://bj.scjn.gob.mx/busqueda?q=*&indice=sentencias_pub"
    response= requests.get(url)
    status= response.status_code
    if status==200:
        BROWSER.get(url)
        #Check the current page to decide if stay or click "Next"
        if startPage>1:
            for click in range(1,startPage):
                btnNext=devuelveElemento('//*[@id="wrapper"]/app-root/app-sitio/div/app-resultados/main/div/div/div[2]/div[1]/div/div[1]/div[2]/ngb-pagination/ul/li[9]/a')
                btnNext.click()
        #End of clicking     
        # Start preparing Judgment
        prepareJudgment()   
        


def printToFile(completeFileName,content):
    with open(completeFileName, 'w') as f:
        f.write(content)

def prepareJudgment(): 
    """
    prepareJudgment:
        Reads the url where the service is fetching data from judgment
    """
    for x in range(3,13):
        linkDoc=devuelveElemento('/html/body/div[2]/app-root/app-sitio/div/app-resultados/main/div/div/div[2]/div['+str(x)+']/app-resultado/div[1]/div/div/app-engrose/div/div/a')
        if linkDoc:
            linkDoc.click()
            time.sleep(5)
            json_file='json_judgment.json'
            #Import JSON file  
            if objControl.heroku:   
                json_jud=devuelveJSON(objControl.rutaHeroku+json_file)  
            else:
                json_jud=devuelveJSON(objControl.rutaLocal+json_file)
            #----------------Get judgment information-----------------------------------------    
            #Get judgment content
            judg_content=devuelveElemento('/html/body/div[2]/app-root/app-sitio/div/app-viewer/main/div/div[2]/section/div/div/div/div[1]/div/div/app-vengroses/div[2]/div/div/div')
            json_jud['judgment_text']=judg_content.text
            
           
            
       




def fillJson(json_thesis,browser,strIdThesis): 
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



           
                               
def devuelveJSON(jsonFile):
    with open(jsonFile) as json_file:
        jsonObj = json.load(json_file)
    
    return jsonObj 

def devuelveElemento(xPath):
    cEle=0
    while (cEle==0):
        cEle=len(BROWSER.find_elements_by_xpath(xPath))
        if cEle>0:
            ele=BROWSER.find_elements_by_xpath(xPath)[0]

    return ele  

def devuelveListaElementos(xPath):
    cEle=0
    while (cEle==0):
        cEle=len(BROWSER.find_elements_by_xpath(xPath))
        if cEle>0:
            ele=BROWSER.find_elements_by_xpath(xPath)

    return ele     
    

    