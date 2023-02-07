import os, logging, uuid
import time, random
import scrapy
from googlesearch import search
from bs4 import BeautifulSoup

logging.basicConfig(filename="logs.log",format='%(asctime)s %(message)s', filemode='w', level=os.environ.get("DEBUG"))
logger = logging.getLogger()
domain = "esg_financing"
current_search = "extended" #extended or basic
phrases_path = f"D:\scrapy\scrapy_with_googlesearch\gfg\{domain}_keywords.txt"


class ExtractUrls(scrapy.Spider):
    # This name must be unique always
    name = "extract"

    # Function which will be invoked
    def start_requests(self):
        # enter the URL here
        os.makedirs(f"{domain}_{current_search}", mode=777, exist_ok=True)
        #with open("proxy_list.txt", "r", encoding="utf-8") as f:
            #proxies = f.readlines()
        if current_search == "extended":
            with open(phrases_path, "r", encoding="utf-8") as f:
                extracted_phrases = f.readlines()

            urls = set()
            extracted_phrases = [item[:-1] for item in extracted_phrases]
            length_url = 0
            for item in extracted_phrases[7:]:
                print(item)
                urls_phrase = []
                #proxy_current = proxies[random.randint(0, 2)]
                #print(proxy_current)

                urls_phrase.extend(list(search(item, num_results=120)))
                urls.update(urls_phrase)
                length_url += len(urls_phrase)

                time.sleep(random.randint(180, 240))
                try:
                    with open(f"{domain}_urls.txt", "a", encoding="utf-8") as f:
                        for url in urls_phrase:
                            f.write(f"{url}\n")
                except:
                    pass
            print(length_url)
            print(len(urls))
            print("***********************************")
        else:
            #proxy_current = proxies[random.randint(0, 2)]
            #print(proxy_current)
            domain_name = " ".join(domain.split("_"))
            print(domain_name)
            urls = list(search(domain_name, num_results=100))

        count = 0
        for url in urls:
            if count % 10 == 0:
                print(f"{count} Done")
            yield scrapy.Request(url=url, callback=self.parse)
            count += 1

    def parse(self, response):
        try:
            page = uuid.uuid4()
            filename = f'{domain}-{page}.html'
            with open(os.path.join(f"{domain}_{current_search}", filename), 'wb') as f:
                f.write(response.body)
            # Get anchor tags
            links = response.css('a::attr(href)').extract()
            with open(f"{domain}_{current_search}/{domain}-{page}_links.txt", "w", encoding="utf8") as f:
                f.write(str(links))

            html = open(os.path.join(f"{domain}_{current_search}", filename), encoding="utf8").read()
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

            with open(f"{domain}_{current_search}/{domain}-{page}_text.txt", "w", encoding="utf8") as f:
                f.write(text)
                
        except Exception as e:
            print(e)
            print(response.url())
