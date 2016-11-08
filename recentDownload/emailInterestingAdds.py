# -*- coding: utf-8 -*-

'''
iso 8601
'''

import getAdds

import datetime, iso8601, pytz
import geojson
from shapely.geometry import shape, Point


def main():
    # param setup
    ######################################
    areaOfInterest = '../Data/geom/podrucjeOdInteresa.geojson'
    lastRunInfo = 'lastRun.dat' # last full data dump; last run date
    mailData = 'mail.dat'
    addUrl = 'http://www.njuskalo.hr/?ctl=browse_ads&sort=new&categoryId=9579&locationId=1153&locationId_level_0=1153&locationId_level_1=0&price[max]=70000&page=%i'
    tz = pytz.timezone('Europe/Zagreb')

    
    # get last run info
    ######################################
    with open(lastRunInfo, 'r') as f:
        lastRunInfoDat = geojson.load(f)



    # run getAdds
    ######################################
    newAddsData, newAddsjobId = getAdds.main(addUrl, lastRunInfoDat['lastRunDate'])


    # open previous GEOJson for comparison
    ######################################
    with open('../Data/oglasi/data_dump_%s_full.geojson' % lastRunInfoDat['fullDataJobId'], 'r') as f:
        previousDataDump = geojson.load(f)


    # compare old and new json
    ######################################
    newAddsNotInOld = []
    for new in newAddsData['features']:
        if not [item for item in previousDataDump["features"] if item["id"] == new["id"]]:
            newAddsNotInOld.append(new)


    # if there is new adds create a new data_dump
    ######################################
    if newAddsNotInOld:
        previousDataDump['features'].extend(newAddsNotInOld)
        with open('../Data/oglasi/data_dump_%s_full.geojson' % newAddsjobId, 'w') as f:
            f.write(unicode(geojson.dumps(previousDataDump)))
        
        # update last run info
        with open(lastRunInfo, 'w') as f:
            f.write(unicode(
                geojson.dumps({
                    "fullDataJobId": newAddsjobId,
                    "lastRunDate": str(datetime.datetime.strptime(str(newAddsjobId), '%Y%m%d%H%M%S%f').replace(tzinfo=tz))
                })
            ))



    # if there are new adds. check if the are within a certain area
    ######################################
    with open(areaOfInterest, 'r') as f:
        aoiDataDump = geojson.load(f)
    polygon = shape(aoiDataDump['features'][0]['geometry'])
    featuresToSend = []
    for new in newAddsNotInOld:
        if new['geometry']:
            point = shape(new['geometry'])
            if polygon.contains(point):
                featuresToSend.append(new)
        else:
            featuresToSend.append(new)


    




    # send mail with interesting adds
    #################################
    if featuresToSend:
        # get mail info
        with open(mailData, 'r') as f:
            mailData = geojson.load(f)

        import smtplib
        from email.mime.text import MIMEText

        email_template = '<a href="%s">%s</a><br>'
        msg = MIMEText(
            '\n'.join([(email_template % (feature['properties']['url'], feature['properties']['title'])) for feature in featuresToSend]),
            "html", "utf-8"
        )
        
        fromaddr = mailData['from']
        toaddr = mailData['to']
        msg['Subject'] = mailData['subject']
        msg['From'] = fromaddr
        msg['To'] = ','.join(mailData['to'])

        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP(mailData['mailServer'], mailData['port'])
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(mailData['user'], mailData['pass'])
        s.sendmail(fromaddr, toaddr, msg.as_string())

        s.quit()





if __name__ == "__main__":
    main()
