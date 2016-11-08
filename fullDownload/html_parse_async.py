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






import time
from lxml import html
import sys
import requests
import grequests
from string import maketrans
from urlparse import urlparse, parse_qs
from geojson import Feature, Point, FeatureCollection


# global params
intab = "aeiou"
outtab = "12345"
trantab = maketrans(intab, outtab)

# globals
exportFeatures = []
oglasData = {}


def main():
    print 'start MAIN'
    global exportFeatures
    global oglasData
    #Params
    class Settings:
        None

    Settings.baseURL = 'http://www.njuskalo.hr'
    Settings.startURL = 'http://www.njuskalo.hr/prodaja-kuca/zagreb'
    Settings.startURL = 'http://www.njuskalo.hr/prodaja-kuca/zagreb?page=%i'


    addRequestss = []


    pageRequestss = (grequests.get(Settings.startURL % pageNum) for pageNum in range(1,156))   # 1-156
    #print pageRequestss
    pageResponses = grequests.map(pageRequestss)

    #print pageResponses
    #print 'start pageResponse LOOP'
    for pageResponse in pageResponses:
        tree = html.fromstring(pageResponse.content)

        # get oglasi
        oglasi = tree.xpath('//*[@id="form_browse_detailed_search"]/div/div[1]/div[2]/div[4]/ul/li[@class!="EntityList-item--banner"]')

        #//*[@id="form_browse_detailed_search"]/div/div[1]/div[2]/div[4]/ul/li[1]/article/h3/a




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
                    'addUrl': (Settings.baseURL + addUrl)
                }

                addRequestss.append(
                    grequests.get(
                        Settings.baseURL + addUrl,
                        hooks = {'response' : addProcess}
                    )
                )


        #print 'END pageResponse LOOP %s' % pageResponse

    # get individual adds
    #print addRequestss

    # Initial call to print 0% progress
    cnt = 0
    totLen = len(addRequestss)
    printProgress(cnt, totLen, prefix = 'Progress:', suffix = 'Complete', barLength = 50)

    n = 20
    for requestsChunk in [addRequestss[i:i + n] for i in xrange(0, len(addRequestss), n)]:
        addResponses = grequests.map(requestsChunk)
        cnt +=n
        printProgress(cnt, totLen, prefix = 'Progress:', suffix = None, barLength = 50)


    #print addResponses


    featuresGeoJson = FeatureCollection(exportFeatures)

    f = open('data_dump_20161022.geojson','w')
    f.write(str(featuresGeoJson)) # python will convert \n to os.linesep
    f.close()

    #print 'END main'










def addProcess(response, *args,  **kwargs):
    #print 'START addProcess'
    #global intab
    #global outtab
    #global trantab

    intab = u"šđčćžŠĐČĆŽ/ "
    outtab = u"sdcczSDCCZ-_"
    #trantab = maketrans(intab, outtab)

    trantab = dict((ord(char), outtab[idx]) for idx, char in enumerate(intab))

    global exportFeatures
    global oglasData


    reqUrl = response.url
    addProperties={
        "title": oglasData[reqUrl]['addTitle'],
        "url": oglasData[reqUrl]['addUrl']
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
            id=oglasData[reqUrl]['dataAddId'],
            properties=addProperties
        )
        #print my_feature
        exportFeatures.append(my_feature)

        #print 'END addProcess'
        return response
    except:
        print 'error %s' % reqUrl
        addProperties['error'] = True
        my_feature = Feature(
            geometry=(None),
            id=oglasData[reqUrl]['dataAddId'],
            properties=addProperties
        )
        #print my_feature
        exportFeatures.append(my_feature)

        #print 'END addProcess'
        return response








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