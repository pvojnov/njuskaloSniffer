# -*- coding: utf-8 -*-


'''


pip install lxml
    # if not working, install & download whl from:
        http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml
pip install requests

http://docs.python-guide.org/en/latest/scenarios/scrape/

'''
# HTMLParser
#from html.parser import HTMLParser





import sys
import os, shutil
import time
import re
import datetime, iso8601

from lxml import html
import pickle
#import requests
import grequests
from string import maketrans
from urlparse import urlparse, parse_qs
from geojson import Feature, Point, FeatureCollection


# global params
intab = u"šđčćžŠĐČĆŽ/ "
outtab = u"sdcczSDCCZ-_"
#trantab = maketrans(intab, outtab)
trantab = dict((ord(char), outtab[idx]) for idx, char in enumerate(intab))

# globals
exportFeatures = []
oglasData = {}
noMoreAdds = False
runToDate = datetime.datetime.strptime('2016-01-01T00:00:00', '%Y-%m-%dT%H:%M:%S')


def main(p_url, p_date):
    #print 'start MAIN'
    global exportFeatures
    global oglasData
    global noMoreAdds
    global runToDate

    runToDate = iso8601.parse_date(p_date)
    #Params
    class Settings:
        None

    # set url params
    Settings.baseURL = 'http://www.njuskalo.hr'
    if p_url:
        Settings.startURL = p_url
    else:
        Settings.startURL = 'http://www.njuskalo.hr/?ctl=browse_ads&sort=new&categoryId=9579&locationId=1153&locationId_level_0=1153&locationId_level_1=0&price[max]=210000&page=%i'
    #http://www.njuskalo.hr/?ctl=browse_ads&sort=new&categoryId=9579&locationId=1153&locationId_level_0=1153&locationId_level_1=0&price%5Bmin%5D=&price%5Bmax%5D=210000&mainAreaFrom=&mainAreaTo=&houseTypeId=0&floorCountId=0&roomCountFrom=0&roomCountTo=0&otherAreaFrom=&otherAreaTo=&yearBuiltFrom=&yearBuiltTo=&yearLastRebuildFrom=&yearLastRebuildTo=
    step_size = 5# number of list pages to bi processed at once


    # params setup
    dataFolder = '../Data'
    resultFolder = os.path.join(dataFolder, 'oglasi')
    tmpFolder = os.path.join(dataFolder, 'tmp')
    jobId = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")


    # del tmp data
    clearFolder(tmpFolder)

    noMoreAdds = False
    pagesCounter = 1

    while not noMoreAdds:
        #print 'page %i' % pagesCounter

        pageRequestss = (grequests.get(Settings.startURL % pageNum, stream=False) for pageNum in range(pagesCounter, pagesCounter+step_size))
        
        #pageRequestss = (grequests.get(Settings.startURL % pageNum, stream=False) for pageNum in range(1,3))   # 1-156
        #print pageRequestss
        pageResponses = grequests.map(pageRequestss)
        pageRequestss = None

        #print pageResponses
        #print 'start pageResponse LOOP'
        for pageRessponseIdx, pageResponse in enumerate(pageResponses):
            tree = html.fromstring(pageResponse.content)

            # get oglasi
            oglasi = tree.xpath('//*[@id="form_browse_detailed_search"]/div/div[1]/div[2]/div[4]/ul/li[@class!="EntityList-item--banner"]')

            # stop looping through adds if pages are empty
            if not oglasi:
                noMoreAdds = True
                break
            else:
                # update total length to be used later on
                totLen = pagesCounter + pageRessponseIdx+1


            #print pagesCounter + pageRessponseIdx
            addRequestss = []
            oglasData = {}
            for oglas in oglasi:
                dataAddId = oglas.xpath('@data-ad-id')
                #print dataAddId
                if dataAddId:
                    #dataAddId = dataAddId[0]
                    addTitle = oglas.xpath('article/h3/a/text()')
                    #print addTitle
                    addUrl = oglas.xpath('article/h3/a/@href')[0]
                    #print addUrl


                    #print Settings.baseURL + addUrl

                    oglasData[(Settings.baseURL + addUrl)] = {
                        'dataAddId': dataAddId[0],
                        'addTitle': addTitle[0],
                        #'addUrl': (Settings.baseURL + addUrl)
                    }

                    addRequestss.append(
                        grequests.get(
                            Settings.baseURL + addUrl,
                            stream=False,
                            hooks = {'response' : addProcess}
                        )
                    )

            # Saving the objects:
            with open(os.path.join(tmpFolder, 'addRequestss_%i.data' % (pagesCounter + pageRessponseIdx)), 'wb') as f:  # Python 3: open(..., 'wb')
                pickle.dump(addRequestss, f, protocol=-1)
            with open(os.path.join(tmpFolder, 'oglasData_%i.data' % (pagesCounter + pageRessponseIdx)), 'wb') as f:  # Python 3: open(..., 'wb')
                pickle.dump(oglasData, f, protocol=-1)
            #print 'END pageResponse LOOP %s' % pageResponse

        pagesCounter += step_size


    # get individual adds
    #print addRequestss

    # empty page rensponses
    pageResponses = None


    # Initial call to print 0% progress
    printProgress(0, totLen, prefix = 'Progress:', suffix = 'Complete', barLength = 50)


    noMoreAdds = False
    for pageRessponseIdx in range(1,totLen):
        # Getting back the objects:
        with open(os.path.join(tmpFolder, 'addRequestss_%i.data' % pageRessponseIdx), 'rb') as f:  # Python 3: open(..., 'rb')
            addRequestss = pickle.load(f)
        with open(os.path.join(tmpFolder, 'oglasData_%i.data' % pageRessponseIdx), 'rb') as f:  # Python 3: open(..., 'rb')
            oglasData = pickle.load(f)
        
        # empty features var
        exportFeatures = []

        # use loaded objects to trigger requests
        grequests.map(addRequestss)
        #print exportFeatures
        
        # Save exportFeatures objects:
        with open(os.path.join(tmpFolder, 'exportFeatures_%i.data' % pageRessponseIdx), 'wb') as f:  # Python 3: open(..., 'wb')
            pickle.dump(exportFeatures, f, protocol=-1)

        # brak the page call if calback function signaled noMoreAdds
        if noMoreAdds:
            totLen = pageRessponseIdx+1
            printProgress(totLen, totLen, prefix = 'Progress:', suffix = 'Complete', barLength = 50)
            break
        printProgress(pageRessponseIdx+1, totLen, prefix = 'Progress:', suffix = 'Complete', barLength = 50)



    #print addResponses



    exportFeaturesAll = []
    for pageRessponseIdx in range(1,totLen):
        with open(os.path.join(tmpFolder, 'exportFeatures_%i.data' % pageRessponseIdx), 'rb') as f:  # Python 3: open(..., 'rb')
            exportFeatures = pickle.load(f)
        exportFeaturesAll.extend(exportFeatures)

    # write results to GeoJSON
    featuresGeoJson = FeatureCollection(exportFeaturesAll)

    f = open(os.path.join(resultFolder,'data_dump_%s.geojson' % jobId),'w')
    f.write(str(featuresGeoJson)) # python will convert \n to os.linesep
    f.close()

    #print 'END main'


    # del tmp data
    clearFolder(tmpFolder)

    return featuresGeoJson, jobId









def addProcess(response, *args,  **kwargs):
    #print 'START addProcess'
    global intab
    global outtab
    global trantab

    

    global exportFeatures
    global oglasData
    global noMoreAdds
    global runToDate


    reqUrl = response.url
    addProperties={
        "title": oglasData[reqUrl]['addTitle'],
        "url": reqUrl
    }

    try:
        # open details page
        addDetailsTree = html.fromstring(response.content)

        # gMapsUrl
        gMapsUrl = addDetailsTree.xpath('//*[@id="base-entity-map-tab"]/div/a/@href')
        if gMapsUrl:
            #print gMapsUrl
            o = urlparse(gMapsUrl[0])
            #print o.query
            qs = parse_qs(o.query)
            #print qs['q']
            #print qs['q'][0]
            coords = qs['q'][0].split(',')
            #print coords
        else:
            gMapsUrl = [None]
            coords = [None]

        addProperties['mapUrl'] = gMapsUrl[0]

        addProperties['cijenaHRK'] = addDetailsTree.xpath('//strong[@class="price price--hrk"]/text()')[0].strip()
        addProperties['cijenaEUR'] = addDetailsTree.xpath('//strong[@class="price price--eur"]/text()')[0].strip()

        addProperties['objavljeno'] = addDetailsTree.xpath('//time/@datetime')[0].strip()
        if iso8601.parse_date(addProperties['objavljeno']) < runToDate:
            # ToDo - implementirat logiku kako prekinut daljnje pozive
            noMoreAdds = True

        addProperties['prikazano_puta'] = re.search(
            '"displayCountText":(.*?),"displayExpiresOnText', 
            addDetailsTree.xpath('/html/head/script')[0].text
        ).group(1)


        # Podaci o kuci
        addAttr = addDetailsTree.xpath('//*[@id="base-entity-data-tab"]/div/div[2]/div[1]/table/tbody/tr')
        for attr in addAttr:
            colName = attr.xpath('th/text()')[0].strip(':')
            if isinstance(colName, str):
                colName = unicode(colName, 'utf-8')
            colnameNew = colName.translate(trantab)
            attrVal = attr.xpath('td/time/text()')


            if attrVal == []:
                 attrVal = attr.xpath('td/text()')[0]
            else:
                attrVal = attr.xpath('td/time/text()')[0]
            addProperties[colnameNew] = attrVal

        #print addAttr


        # dodaci
        addDod = addDetailsTree.xpath('//*[@id="base-entity-data-tab"]/div/div[2]/div[2]/ul/li/text()')
        for colName in addDod:
            if isinstance(colName, str):
                colName = unicode(colName, 'utf-8')
            colnameNew = colName.translate(trantab)
            addProperties[colnameNew] = True


        my_feature = Feature(
            geometry=(
                Point((float(coords[1]), float(coords[0]))) if gMapsUrl!=[None] else None
            ),
            id=int(oglasData[reqUrl]['dataAddId']),
            properties=addProperties
        )
        #print my_feature
        exportFeatures.append(my_feature)

        #print 'END addProcess'
        response.close()
    except:
        print 'error %s' % reqUrl
        addProperties['error'] = True
        my_feature = Feature(
            geometry=(None),
            id=int(oglasData[reqUrl]['dataAddId']),
            properties=addProperties
        )
        #print my_feature
        exportFeatures.append(my_feature)

        #print 'END addProcess'
        response.close()





###########################################################
# Utils
###########################################################
def clearFolder(path):
    folder = path
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)




# Print iterations progress
def printProgress (iteration, total, prefix = '', suffix = '', decimals = 2, barLength = 100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : number of decimals in percent complete (Int)
        barLength   - Optional  : character length of bar (Int)
    """
    filledLength    = int(round(barLength * iteration / float(total)))
    percents        = round(100.00 * (iteration / float(total)), decimals)
    bar             = u'█' * filledLength + '-' * (barLength - filledLength)
    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),
    sys.stdout.flush()
    if iteration == total:
        sys.stdout.write('\n')
        sys.stdout.flush()



if __name__ == "__main__":
    start = time.time()

    main()


    end = time.time()
    print'\n'+str(end - start)