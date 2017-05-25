const chromedriver = require('chromedriver');
import * as webdriverio from 'webdriverio';
import { Builder, WebDriver } from 'selenium-webdriver';

function start(backend: 'chrome'|'phantomjs') {
	return webdriverio.remote({
		desiredCapabilities: {
			browserName: backend
		}
	}).init();
}

const browser = start('chrome');


function googleSearch(browser, keywords) {
	return browser
	.url(`https://www.google.com/search?query=${keywords}`)
	.elements(`//h3[@class="r"]`)
	.then( links => {
		for(const link of links.value )
			console.log(link);

	});
}

googleSearch(browser, 'peluqueria');
