import re
from urllib.parse import urlparse, urldefrag
from bs4 import BeautifulSoup
from collections import defaultdict

seen = set()
word_freqs = defaultdict(int)
longest_page = ""
peak_words = -1


with open('stopWords.txt', 'r') as f:
    stop_words = {line for line in f}

def scraper(url, resp):
    resp = resp.raw_response
    if not resp: return []
    print(url, end='')
    try:
        head = resp.headers
        print(' ||', head['content-type'])
        if 'content-type' in head and head['content-type'].find("html") == -1: return []
        if 'content-length' in head and int(head['content-length']) > 4000000: return []
    except (AttributeError, KeyError):
        pass
    monitor_info()
    seen.add(url)

    soup = BeautifulSoup(resp.text, "lxml")
    links = extract_next_links(soup)
    extract_info(url, soup)
    return [link for link in links if is_valid(link)]

def monitor_info():
    print("\n" + "="*20)
    print(f"UNIQUE LINKS: {len(seen)}")
    print(f"UNIQUE WORDS: {len(word_freqs)}")
    print(f"LONGEST PAGE: {longest_page} || # WORDS: {peak_words}")
    print("="*20, end="\n\n")

def extract_next_links(soup):
    return [urldefrag(a.get('href')).url for a in soup.find_all('a')]

token_pat = r"[^_\W]+"
def extract_info(url, soup):
    global peak_words, longest_page
    lines = soup.get_text().split("\n")
    page_word_count = 0
    for l in lines:
        l = l.strip()
        if not l: continue
        words = re.finditer(token_pat, l)
        for w in words:
            w = w.group().lower()
            if w not in stop_words:
                page_word_count += 1
                word_freqs[w] += 1
    if page_word_count > peak_words:
        longest_page = url
        peak_words = page_word_count

domains = [
r".*\.cs\.uci\.edu\/.*",
r".*\.ics\.uci\.edu\/.*",
r".*\.informatics\.uci\.edu\/.*",
r".*\.stat\.uci\.edu\/.*",
r"today\.uci\.edu\/department\/information_computer_sciences\/.*",
]
def is_valid(url):
    try:
        if not url or url in seen: return False
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        correct_domain = sum(1 for d in domains if re.match(d, url))
        if correct_domain == 0: return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise