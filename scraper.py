import re
from urllib.parse import urlparse, urldefrag
from bs4 import BeautifulSoup
import requests
# from collections import defaultdict   # hard to load with eval()

count = 0
longest_page = ""
peak_words = 0

seen = set()
word_freqs = {}
domains = {
r".*\.informatics\.uci\.edu\/.*":0,
r".*\.ics\.uci\.edu\/.*":0,
r".*\.cs\.uci\.edu\/.*":0,
r".*\.stat\.uci\.edu\/.*":0,
r".*\.today\.uci\.edu\/department\/information_computer_sciences\/.*":0,
}
ics_subdomains = {}



with open('stopWords.txt', 'r') as f:
    stop_words = {line.rstrip() for line in f}

def scraper(url, resp):
    global count
    resp = resp.raw_response
    try:  # check for valid url

        # if not (200 <= resp.status <= 203): return []
        head = resp.headers
        if 'content-type' in head \
            and head['content-type'].find("html") == -1\
            and head['content-type'].find("text") == -1: return [] # type restriction
        # if 'content-length' in head and int(head['content-length']) > 4000000:
        #     return [] # size restriction 4MB
        soup = BeautifulSoup(resp.text, "lxml")
    except (AttributeError, KeyError):
        return []

    count += 1

    monitor_info(url)
    links = extract_next_links(soup)
    extract_info(url, soup)
    return [link for link in links if link != "" and is_valid(link, resp)]

def is_ascii(s):
    """Check if the characters in string s are in ASCII, U+0-U+7F."""
    return len(s) == len(s.encode())

def monitor_info(url, show_extra=False):
    print("="*40)
    print("\n" + url)
    print("="*40)
    print(f"UNIQUE LINKS VISITED:    {count}")
    print(f"UNIQUE LINKS DISCOVERED: {len(seen)}")
    print(f"UNIQUE WORDS: {len(word_freqs)}")
    print(f"LONGEST PAGE: {peak_words} WORDS | {longest_page}")
    if show_extra or count % 50 == 0: # every 50, print extra info
        print("-"*40)
        print("TOP FREQUENT WORDS:")
        for x in sorted(word_freqs, key=lambda x:-word_freqs[x])[:5]:
            print(f"{word_freqs[x]:<7} | {x}")
        print("-" * 40)
        print("DOMAIN COUNTS:")
        pretty = r'[\\?]'
        for k,v in domains.items():
            print(f"{v:<7} | {re.sub(pretty, '', k[1:])}")
        print("-"*40)
        print("ICS SUBDOMAIN COUNTS:")
        for k,v in ics_subdomains.items(): print(f"{v:<7} | {k}")
    print("="*40, end="\n\n")

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
        for word in re.finditer(token_pat, l):
            word = word.group().lower()
            if word not in stop_words and len(word) > 1 and is_ascii(word):
                page_word_count += 1
                if word not in word_freqs: word_freqs[word] = 0
                word_freqs[word] += 1
    if page_word_count > peak_words:
        longest_page = url
        peak_words = page_word_count

def is_valid(url, resp):
    try:    
        parsed = urlparse(url)
        s_url = (parsed.netloc + parsed.path).lower()
        if s_url == "ics.uci.edu/~kay/wordlist.txt": return False
        #head = requests.head(url)
        if not s_url or s_url in seen: return False
        if parsed.scheme not in {"http", "https"}:
            return False
        #if not 200 <= head.status_code <= 202: return False
        if not 200 <= resp.status_code <= 202: return False
        if re.match(
                r".*\.(css|js|bmp|gif|jpe?g|ico"
                + r"|png|tiff?|mid|mp2|mp3|mp4"
                + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                + r"|epub|dll|cnf|tgz|sha1"
                + r"|thmx|mso|arff|rtf|jar|csv"
                + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()): return False

        for d in domains:
            if re.match(d, s_url):
                domains[d] += 1
                if d == r".*\.ics\.uci\.edu\/.*":  # bad
                    subdomain = parsed.netloc.lower()
                    if subdomain not in ics_subdomains: ics_subdomains[subdomain] = 0
                    ics_subdomains[subdomain] += 1
                seen.add(s_url)
                return True
        return False


    except TypeError:
        print ("TypeError for ", parsed)
        raise
