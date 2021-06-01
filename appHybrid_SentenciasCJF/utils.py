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

def readUrl(startPage,limit):
    if startPage==limit:
        print('The query is over')
        os.sys.exit(0)
    returnChromeSettings()
    print('Starting process...')
    url="https://bj.scjn.gob.mx/busqueda?q=*&indice=sentencias_pub&page="+str(startPage)
    response= requests.get(url)
    status= response.status_code
    if status==200:
        BROWSER.get(url)
        time.sleep(5)
        # Start preparing Judgment
        #This 'for page' cycle is independent from the query in cassandra, if something fails here then the page is saved in cassandra and it will start over from the page saved
        json_file='json_judgment.json'
        #Import JSON file  
        if objControl.heroku:   
            json_jud=devuelveJSON(objControl.rutaHeroku+json_file)  
        else:
            json_jud=devuelveJSON(objControl.rutaLocal+json_file)
       

        prepareJudgment(startPage,json_jud) 
        print('----------------End of Page '+str(startPage)+'---------------------------')
        query='update thesis.cjf_control set page='+str(startPage+1)+' where id_control='+str(objControl.idControl)
        db.executeNonQuery(query)


        


def printToFile(completeFileName,content):
    with open(completeFileName, 'w') as f:
        f.write(content)

def prepareJudgment(currentPage,json_jud): 
    """
    prepareJudgment:
        Reads 10 judgements each time
    """
    for x in range(3,13):
        #/html/body/div[2]/app-root/app-sitio/div/app-resultados/main/div/div/div[2]/div[3]/app-resultado/div[1]/div/div/app-engrose/div/div/a/span
        linkDoc=devuelveElemento('/html/body/div[2]/app-root/app-sitio/div/app-resultados/main/div/div/div[2]/div['+str(x)+']/app-resultado/div[1]/div/div/app-engrose/div/div/a')
        time.sleep(3)
        if linkDoc:
            print('-----------Waiting 10 secs for the link of the document to be ready--------')
            time.sleep(10)
            href=linkDoc.get_attribute('href')
            print('Value of linkDoc:',href)
            if href!='':
                BROWSER.execute_script("arguments[0].click();", linkDoc)
            time.sleep(5)
            
            #----------------Get judgment information-----------------------------------------    
            #----------------------FIRST TAB--------------------------------------------------
            #Clean JSON
            json_jud['ID']=''
            json_jud['judgment_text']=''
            json_jud['file']=''
            json_jud['strDate']=''
            json_jud['year']=0
            json_jud['subject']=''
            json_jud['minister']=''
            json_jud['topic']=''
            json_jud['title']=''
            #Content
            json_jud['ID']=str(uuid.uuid4())
            judg_content=devuelveElemento('/html/body/div[2]/app-root/app-sitio/div/app-viewer/main/div/div[2]/section/div/div/div/div[1]/div/div/app-vengroses/div[2]/div/div/div')
            #Remove any character that can break cassandra : ','
            json_jud['judgment_text']=judg_content.text.replace("'","")
            #Title
            title=devuelveElemento('/html/body/div[2]/app-root/app-sitio/div/app-viewer/main/div/div[2]/section/div/div/nav/div/a[1]')
            json_jud['title']=title.text
            #-------------------2ND TAB 'Ficha técnica' click tab-----------------------------
            tabFT=devuelveElemento('/html/body/div[2]/app-root/app-sitio/div/app-viewer/main/div/div[2]/section/div/div/nav/div/a[2]')
            #tabFT.click()
            BROWSER.execute_script("arguments[0].click();", tabFT)
            time.sleep(9)
            #File
            exp_file=devuelveElemento('/html/body/div[2]/app-root/app-sitio/div/app-viewer/main/div/div[2]/section/div/div/div/div[2]/app-vefichatecnica/div/div[2]/table/tbody[1]/tr[1]/td')
            exp_file_value=exp_file.text
            json_jud['file']=exp_file_value
            json_jud['strDate']=exp_file_value
            #Year
            if '-' in exp_file_value:
                #Other cases
                #14/2021-CA
                strgetValue=exp_file_value.split('/')[1]
                year=int(strgetValue.split('-')[0])
            else:    
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
            #-------Start Cassandra Read & Write---------------------------------------
            #Table for this service : thesis.tbjudgment
            #Check if the judgment is IN.
            strFile=json_jud['file'];
            print('Working with: ',strFile,' , row :',str(x-2),' page :',str(currentPage))
            query="select id from thesis.tbjudgment where file='"+json_jud['file']+"' and subject='"+json_jud['subject']+"' ALLOW FILTERING;"
            resultSet=db.getQuery(query)
            if len(resultSet.current_rows)>0:
                print('File: ',strFile,' existed')
            else:
                db.insertJSON('thesis.tbjudgment',json_jud) 
                print('File: ',strFile,' added')  

            time.sleep(10)
            print('Slowing down 10 seconds for cassandra')     
            #Back to main query page
            btnBack= devuelveElemento('/html/body/div[2]/app-root/app-sitio/div/app-viewer/main/div/div[1]/div/div[1]/div/div/a[2]/button')
            if btnBack:
                time.sleep(5)
                BROWSER.execute_script("arguments[0].click();",btnBack)

            
        else:
            print('-------A link to a judgment could not be open at page :',str(currentPage),'-----------')
            print('--------------------------------The program exited-----------------------------------')
            os.sys.exit(0)    
            


            



           
                               
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
    

    