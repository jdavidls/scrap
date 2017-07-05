import sys, asyncio, aiohttp, async_timeout, collections, csv
from lxml import html, etree
from tld import get_tld
from urllib.parse import urlparse


USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1'

'''
 	analizar doctype html5
	soltar tabs
'''

columns =['url', 'origin', 'doctype', 'tableCount', 'error']
Row = collections.namedtuple('Row', columns)
headRow = Row(*columns)

def readFileSet(filename):
	with open(filename, 'r') as f:
		return set([x.strip() for x in f.readlines()])

blacklist = readFileSet('./data/blacklist.txt')

class Scrapper:
	def __init__(self, loop, timeout=10):
		self.loop = loop
		self.timeout = timeout
		self.headers = {
			'User-Agent': USER_AGENT
		}

	async def get(self, url):
		with async_timeout.timeout(self.timeout):
			async with aiohttp.ClientSession(loop=self.loop, headers=self.headers) as session:
				try:
					async with session.get(url) as response:
						## check status code
						if response.status != 200:
							print(url, 'response', response.status, ':', response.reason)
							return
						else:
							try:
								text = await response.text()
							except Exception as e:
								print(url, 'has an unicode error')
								return e
							try:
								return html.fromstring(text)
							except Exception as e:
								print(url, 'has a XML/HTML parsing error')
								return e
				except Exception as e:
					print(url, 'has a HTTP/SSL errors')
					return e


async def google(scrapper, keywords, pages=50):
	url = '/search?filter=0&query='+keywords
	for n in range(pages):
		print('GOOGLE SEARCH FOR', keywords, 'PAGE', n)
		html = await scrapper.get('https://www.google.com'+url)
		if isinstance(html, Exception) or html is None:
			print('Error loading google page', url)
			break

		organicLinks = html.xpath('//h3[@class="r"]//a/@href')
		for link in organicLinks:
			yield link, 'organic'

		# next page
		url = html.xpath('//a[@id="pnnext"]/@href')
		if not url:	break
		url = url[0]

        #sleep
        await asyncio.sleep(1)

async def bing(scrapper, keywords, pages=50):
	url = '/search?q='+keywords
	for n in range(pages):
		html = await scrapper.get('https://www.bing.com'+url)
		if isinstance(html, Exception):
			print('Error loading google page', url)
			continue;

		organicLinks = html.xpath('//h3[@class="r"]//a/@href')
		for link in organicLinks:
			yield link, 'organic'

		# next page
		url = html.xpath('//a[@id="pnnext"]/@href')
		if not url:	break
		url = url[0]

async def searchLoop(loop, searchEngine, keywords):
	scrapper = Scrapper(loop)

	pages = set()

	async for link, origin in searchEngine(scrapper, keywords):

		urlparts = urlparse(link)
		link = '{url.scheme}://{url.netloc}'.format(url=urlparts)
		tld = get_tld(link)
		if tld in pages or tld in blacklist: continue
		pages.add(tld)
		print('Scanning', tld)

		#print('scanning', link)
		page = await scrapper.get(link)
		if isinstance(page, Exception):
			yield Row(url=link, origin=origin, doctype=None, tableCount=None, error=str(page))
		else:
			# cuenta el numero de tablas
			doctType=page.getroottree().docinfo.doctype;
			tableCount = len(page.xpath('//table'))
			yield Row(url=link, origin=origin, doctype=doctType, tableCount=tableCount, error=None)

async def search(loop, keywords):
	outputFilename = './data/' + keywords + '.csv'
	with open(outputFilename, 'w', newline='') as csvFile:
		csvWriter = csv.writer(csvFile)
		csvWriter.writerow(headRow)
		async for row in searchLoop(loop, google, keywords):
			csvWriter.writerow(row)


loop = asyncio.get_event_loop()
loop.run_until_complete(search(loop, '+'.join(sys.argv[1:])))
loop.close()
