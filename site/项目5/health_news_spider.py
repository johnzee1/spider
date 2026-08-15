import scrapy


class HealthNewsSpider(scrapy.Spider):
    name = "health_news"
    start_urls = ["https://health.people.com.cn/"]
    custom_settings = {"DOWNLOAD_DELAY": 1}

    def parse(self, response):
        seen = set()
        for link in response.css("a[href]"):
            title = " ".join(link.css("::text").getall()).strip()
            url = response.urljoin(link.attrib["href"])
            if len(title) < 8 or title in seen:
                continue
            seen.add(title)
            yield {"title": title, "url": url, "source": "人民网健康"}
