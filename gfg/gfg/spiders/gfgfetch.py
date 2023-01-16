import scrapy
from googlesearch import search
from bs4 import BeautifulSoup


class ExtractUrls(scrapy.Spider):
    # This name must be unique always
    name = "extract"

    # Function which will be invoked
    def start_requests(self):
        # enter the URL here
        urls = list(search("Greenhouse Gas Emissions", num_results=10))
        print(urls)

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        page = response.url.split("/")[-2]
        filename = f'ghg-{page}.html'
        with open(filename, 'wb') as f:
            f.write(response.body)
        # Get anchor tags
        links = response.css('a::attr(href)').extract()
        with open(f"ghg-{page}_links.txt", "w") as f:
            f.write(str(links))

        html = open(filename, encoding="utf8").read()
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

        with open(f"ghg-{page}_text.txt", "w", encoding="utf8") as f:
            f.write(text)
        #import pdb;pdb.set_trace()