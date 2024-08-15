import scrapy
from scrapy.crawler import CrawlerProcess
from multiprocessing import Process, Queue


class ReversoContextScraperSpider(scrapy.Spider):
    # identidade
    name = 'tradutorbot'

    def __init__(self, words):
        super(ReversoContextScraperSpider, self).__init__()
        self.words = words

    def start_requests(self):
        palavras = list(self.words)
        urls = []
        for palavra in palavras:
            urls.append((palavra, f'https://context.reverso.net/traducao/ingles-portugues/{palavra}'))
        for palavra, url in urls:
            yield scrapy.Request(url=url, callback=self.parse, cb_kwargs={'palavra': palavra},
                                 dont_filter=True,
                                 headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'})

    def parse(self, response, palavra, **kwargs):
        for item in response.xpath('//div[@id="translations-content"]'):
            yield {
                'Palavra': palavra,
                'Tradução': item.xpath('//div[@id="translations-content"]//'
                                       'span[@class="display-term"]/text()').getall()[0:3],
            }


def run_in_new_process(queue, spider, words):
    try:
        process = CrawlerProcess({
            'FEEDS': {
                'last_translate.json': {
                    'format': 'json',
                    'encoding': 'utf-8',
                    'overwrite': True
                }
            }
        })
        process.crawl(spider, words=words)
        process.start(stop_after_crawl=True)
        queue.put(None)
    except Exception as e:
        queue.put(e)


def run_spider(spider, words):
    queue = Queue()
    process = Process(target=run_in_new_process, args=(queue, spider, words))
    process.start()
    result = queue.get()
    process.join()

    if result is not None:
        raise result
