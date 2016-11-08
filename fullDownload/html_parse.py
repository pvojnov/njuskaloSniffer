'''


pip install lxml
	# if not working, install & download whl from:
		http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml
pip install requests

http://docs.python-guide.org/en/latest/scenarios/scrape/

'''
# HTMLParser
#from html.parser import HTMLParser


from lxml import html
import requests



import time
from lxml import html
import requests
from urlparse import urlparse, parse_qs
from geojson import Feature, Point, FeatureCollection




def main():
    #Params
    class Settings:
        None

    Settings.baseURL = 'http://www.njuskalo.hr'
    Settings.startURL = 'http://www.njuskalo.hr/prodaja-kuca/zagreb'
    Settings.startURL = 'http://www.njuskalo.hr/prodaja-kuca/zagreb?page=%i'

    exportFeatures = []

    #for pageNum in range(1,155):
    for pageNum in range(1,2):
        print pageNum,

        # get HTML
        tree = getUrlTree(Settings.startURL % pageNum)


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

                # open details page
                addDetailsTree = getUrlTree(Settings.baseURL + addUrl)


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


                my_feature = Feature(
                    geometry=(
                        Point((float(coords[0]), float(coords[1]))) if gMapsUrl!=[None] else None
                    ),
                    id=dataAddId[0],
                    properties={
                        "title": addTitle[0],
                        "url": addUrl,
                        "mappUrl": gMapsUrl[0]
                    }
                )
                #print my_feature
                exportFeatures.append(my_feature)

    featuresGeoJson = FeatureCollection(exportFeatures)

    f = open('data_dump_20161022.geojson','w')
    f.write(str(featuresGeoJson)) # python will convert \n to os.linesep
    f.close()







def getUrlTree(url):
    page = requests.get(url)
    tree = html.fromstring(page.content)
    return tree



if __name__ == "__main__":
    start = time.time()

    main()


    end = time.time()
    print'\n'+str(end - start)