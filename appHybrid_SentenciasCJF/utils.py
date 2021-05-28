import cassandraUtil as db
import json
import os
from selenium import webdriver
import chromedriver_autoinstaller
import requests 
import uuid
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
    url="https://bj.scjn.gob.mx/busqueda?q=*&indice=sentencias_pub&page="+str(startPage)
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
        Reads 10 judgements each time
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
            #----------------------FIRST TAB--------------------------------------------------
            #Content
            json_jud['ID']=str(uuid.uuid4())
            judg_content=devuelveElemento('/html/body/div[2]/app-root/app-sitio/div/app-viewer/main/div/div[2]/section/div/div/div/div[1]/div/div/app-vengroses/div[2]/div/div/div')
            json_jud['judgment_text']=judg_content.text
            #Title
            title=devuelveElemento('/html/body/div[2]/app-root/app-sitio/div/app-viewer/main/div/div[2]/section/div/div/nav/div/a[1]')
            json_jud['title']=title.text
            #-------------------2ND TAB 'Ficha técnica' click tab-----------------------------
            tabFT=devuelveElemento('/html/body/div[2]/app-root/app-sitio/div/app-viewer/main/div/div[2]/section/div/div/nav/div/a[2]')
            tabFT.click()
            time.sleep(5)
            #File
            exp_file=devuelveElemento('/html/body/div[2]/app-root/app-sitio/div/app-viewer/main/div/div[2]/section/div/div/div/div[2]/app-vefichatecnica/div/div[2]/table/tbody[1]/tr[1]/td')
            json_jud['file']=exp_file.text
            json_jud['strDate']=exp_file.text
            exp_file_value=exp_file.text
            #Year
            year=int(exp_file_value.split('/')[1])
            json_jud['year']=year
            #Subject
            subject=devuelveElemento('/html/body/div[2]/app-root/app-sitio/div/app-viewer/main/div/div[2]/section/div/div/div/div[2]/app-vefichatecnica/div/div[2]/table/tbody[1]/tr[2]/td')
            json_jud['subject']=subject.text
            #Minister
            minister=devuelveElemento('/html/body/div[2]/app-root/app-sitio/div/app-viewer/main/div/div[2]/section/div/div/div/div[2]/app-vefichatecnica/div/div[2]/table/tbody[1]/tr[3]/td')
            if minister.text!='':
                json_jud['minister']=minister.text
            else:
                json_jud['minister']='No value'
            #Topic    
            topic=devuelveElemento('/html/body/div[2]/app-root/app-sitio/div/app-viewer/main/div/div[2]/section/div/div/div/div[2]/app-vefichatecnica/div/div[2]/table/tbody[1]/tr[4]/td') 
            json_jud['topic']=topic.text
            #Back to main query page
            btnBack=devuelveElemento('/html/body/div[2]/app-root/app-sitio/div/app-viewer/main/div/div[1]/div/div[1]/div/div/a[2]/button')
            btnBack.click()
            


            



           
                               
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
    

    