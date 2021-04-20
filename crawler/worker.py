from threading import Thread

from utils.download import download
from utils import get_logger
import scraper
import time


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.count = 0
        super().__init__(daemon=True)

    def load_data(self, filepath="saveData.txt"):
        with open(filepath, 'r') as f:
            scraper.count        = eval(f.readline().rstrip())
            scraper.longest_page = eval(f.readline().rstrip())
            scraper.peak_words   = eval(f.readline().rstrip())
            scraper.seen         = eval(f.readline().rstrip())
            scraper.word_freqs   = eval(f.readline().rstrip())

    def save_data(self, filepath="saveData.txt"):
        with open(filepath, 'w') as f:
            f.write(f"{repr(scraper.count)}\n{repr(scraper.longest_page)}\n"
                    f"{repr(scraper.peak_words)}\n")
            print(repr(scraper.seen))
            f.write(f"{repr(scraper.seen)}\n{repr(scraper.word_freqs)}"
                    f"\n{repr(scraper.domains)}\n{repr(scraper.ics_subdomains)}\n")

    def run(self):
        try: self.load_data()
        except FileNotFoundError: pass
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
            self.count += 1
            if self.count % 50 == 0:
                self.save_data()
        self.save_data()
        scraper.monitor_info("", True)