import os, logging
import scrapy
from googlesearch import search
from bs4 import BeautifulSoup

logging.basicConfig(filename="logs.log",format='%(asctime)s %(message)s', filemode='w', level=os.environ.get("INFO"))
logger = logging.getLogger()
count = 0
class ExtractUrls(scrapy.Spider):
    # This name must be unique always
    name = "extract"

    # Function which will be invoked
    def start_requests(self):
        # enter the URL here
        urls = list(search("Gender Diversity", num_results=120))
        print(urls)

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        try:
            page = response.url.split("/")[-2]
            filename = f'gender_diversity-{page}.html'
            with open(os.path.join("gender_diversity", filename), 'wb') as f:
                f.write(response.body)
            # Get anchor tags
            links = response.css('a::attr(href)').extract()
            with open(f"gender_diversity/gender_diversity-{page}_links.txt", "w") as f:
                f.write(str(links))

            html = open(os.path.join("gender_diversity", filename), encoding="utf8").read()
            soup = BeautifulSoup(html, features="html.parser")

            # kill all script and style elements
            for script in soup(["script", "style"]):
                script.extract()  # rip it out

            # get text
            text = soup.get_text()

            # break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)

            with open(f"gender_diversity/gender_diversity-{page}_text.txt", "w", encoding="utf8") as f:
                f.write(text)
                
        except Exception as e:
            count+=1
            logger.info(e)
            logger.info(response.url())
            logger.info(f"Count: {count}")