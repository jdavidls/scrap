import sys
import asyncio
import aiohttp
import async_timeout
from lxml import html, etree

USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1'

class Scrapper:
	def __init__(self, loop, timeout=10):
		self.loop = loop
		self.timeout = timeout
		self.headers = {
			'User-Agent': USER_AGENT
		}

	async def get(self, url):
		__session = aiohttp.ClientSession(loop=self.loop, headers=self.headers)
		with async_timeout.timeout(self.timeout):
			async with __session as session:
				try:
					async with session.get(url) as response:
						try:
							text = await response.text()
						except:
							print(url, 'has an unicode error')
							return
						try:
							return html.fromstring(text)
						except:
							print(url, 'has a XML/HTML parsing error')
							return
				except:
					print(url, 'has a HTTP/SSL errors')
					return


class Google(Scrapper):
	async def search(self, keywords, pages=10, ads=True, organic=True):
		url = '/search?query='+keywords

		for n in range(pages):
			html = await self.get('https://www.google.com'+url)
			if html is None:
				continue;

			if ads:
				adLinks = html.xpath('//li[@class="ads-ad"]/child::a/@href')
				for link in adLinks:
					yield link

			if organic:
				organicLinks = html.xpath('//h3[@class="r"]/child::a/@href')
				for link in organicLinks:
					yield link

			# next page
			url = html.xpath('//a[@id="pnnext"]/@href')
			if not url:
				break
			url = url[0]


async def search(loop, keywords):
	scrapper = Scrapper(loop)
	google = Google(loop)

	async for link in google.search(keywords):
		#print('scanning', link)
		page = await scrapper.get(link)
		if page is None: continue

		# cuenta el numero de tablas
		tables = page.xpath('//table')
		tables and print('  ', link, 'has', len(tables), 'tables')

loop = asyncio.get_event_loop()
loop.run_until_complete(search(loop, '+'.join(sys.argv[1:])))
loop.close()
