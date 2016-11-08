import requests
from lxml import html
import re

url = 'http://www.njuskalo.hr/nekretnine/kuca-zagreb-gornji-bukovac-prizemnica-70-m2-oglas-14181782'
url = 'http://www.njuskalo.hr/nekretnine/kuca-prodaja-podsljeme-222.45m2-oglas-18522841'

resp = requests.get(url)


tree = html.fromstring(resp.content)

elem = tree.xpath('//span[@class="base-entity-display-count"]')
elem2 = tree.xpath('/html/head/script')[0].text
nt = re.search('"displayCountText":(.*?),"displayExpiresOnText', elem2).group(1)

print elem2