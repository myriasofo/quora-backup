#!/bin/python3

from bs4 import BeautifulSoup
import urllib.error
import urllib.request
import re
import sys
import time
from random import randint

from crawler import parse_quora_date

# crawler.py assumes one has access to the nicely-formatted JSON of the
# answers and their timestamps.  However, one can only obtain this if
# one has access to the "Your Content" page of a user.  In other cases
# one must effectively find all the URLs for the answers of a user by
# other means.  Here we assume a user has scrolled to the very bottom of
# a user's answers page and saved that as an HTML.  This is passed in as
# INPUT_FILE (for now); the rest is the same as crawler.py, so
# converter.py will work on the output files of this script.

# One subtlety is that on the "Your Content" page, the timestamp shown
# is for when a user first added the answer(?), but on an answer page,
# it only displays the timestamp of when the answer was last updated.
# Therefore the timestamp in the filename will be altered accordingly.

# Change this
INPUT_FILE = "changeme.html"
USERNAME = "Change-Me-Too"

def make_soup(path):
    return BeautifulSoup(open(path))

def extract_answers(soup):
    '''\
    Given a BeautifulSoup soup, return the set of all valid Quora answer
    URLs.
    '''
    want = set()
    for link in soup.find_all("a"):
        url = link.get("href")
        class_ = link.get("class")
        if isinstance(url, str) and isinstance(class_, list) and\
            "question_link" in class_:
            want.add(url + "/answer/" + USERNAME)

        # When I was testing this before, the question links had a
        # different format, for some reason.  If the above produces an
        # empty set, then try the following (or some boolean operation
        # combination of the components of the following) instead (or
        # just look at the input HTML and figure out the pattern
        # yourself)
        #if isinstance(url, str) and "quora" in url and\
            #"/answer/" in url and url[0] == "/":
            #want.add("https://quora.com" + url)
    return want

def download_page(url):
    '''\
    Given the string of a url, try to download it; return the string of
    the HTML page.
    '''
    try:
        page_html = urllib.request.urlopen(url).read()
        return page_html
    except urllib.error.URLError as error:
        print('[ERROR] Failed to download answer from URL %s (%s)' %
            (url, error.reason), file=sys.stderr)

def extract_date_from_answer(page_html):
    '''\
    Given the HTML of a page, extract the Quora date string of the
    answer (so "Just Now", "Sat", "11 Nov" are all possible return
    values).  If an answer has been updated since it was originally
    written, then return that date instead.  (Ideally one would want the
    date when an answer was first written, but this is harder to obtain
    without access to the "Your Content" page.)
    '''
    soup = BeautifulSoup(page_html)
    possible = []
    for link in soup.find_all("a"):
        text = link.string
        if isinstance(text, str) and ("Written " in text or\
            "Updated " in text):
            # Append all but the "Written " or "Updated "; it's actually
            # just a coincidence that both have the same length...
            possible.append(text[len("Written "):])
    # The only way there could be more than one occurrence of such a
    # link (i.e. a link containing "Written " or "Updated " is for the
    # user to be clever and have inserted this into their answer.  Since
    # all the answer text appears above the time stamp, we will just
    # return the very last such string.
    if len(possible) > 1:
        print("[WARNING] Date string is ambiguous; "
            "returning the last occurrence")
    if not possible:
        print("[WARNING] Could not find a date; we'll just use 'just now'")
        return "just now"
    return possible[-1]

def get_filename(url, timestamp, origin):
    '''\
    Given the URL and timestamp of an answer, as well as origin
    (timestamp offset by time zone), return what the filename for the
    downloaded HTML should be and return that as a string.
    '''
    # Determine the date when this answer was written
    try:
        added_time = parse_quora_date(origin, "Added " + timestamp)
    except ValueError as error:
        print('[WARNING] Failed to parse date: %s' %
            str(error), file=sys.stderr)
        added_time = 'xxxx-xx-xx'
    print('Date: %s' % added_time, file=sys.stderr)

    # Get the part of the URL indicating the question title; we will
    # save under this name
    m1 = re.search('quora\.com/([^/]+)/answer', url)
    # if there's a context topic
    m2 = re.search('quora\.com/[^/]+/([^/]+)/answer', url)
    filename = added_time + ' '
    if not m1 is None:
        filename += m1.group(1)
    elif not m2 is None:
        filename += m2.group(1)
    else:
        print('[ERROR] Could not find question part of URL %s; skipping' %
            url, file=sys.stderr)
    # Trim the filename if it's too long. 255 bytes is the limit on many
    # filesystems.
    total_length = len(filename + '.html')
    if len(filename + '.html') > 255:
        filename = filename[:(255 - len(filename + '.html'))]
        #log_if_v('Filename was truncated to 255 characters.')
    filename += '.html'
    return filename

def get_origin(origin_timestamp=None, origin_timezone=None):
    '''\
    Determine the origin for relative date computation.
    '''
    if origin_timestamp is None:
        #log_if_v('Using current time')
        origin_timestamp = time.time()
    else:
        origin_timestamp //= 1000
    if origin_timezone is None:
        #log_if_v('Using system time zone')
        origin_timezone = time.timezone
    else:
        origin_timezone *= 60
    origin = origin_timestamp - origin_timezone
    return origin

def write_file(filename, content):
    '''\
    Write content to filename; content should be raw bytes(?).
    '''
    with open(filename, "wb") as f:
        f.write(content)
        print("Written: " + filename)

def process_urls(want):
    for url in want:
        page = download_page(url)
        datestamp = extract_date_from_answer(page)
        #origin = get_origin(1425465100551, 480)
        origin = get_origin()
        filename = get_filename(url, datestamp, origin)
        write_file(filename, page)
        num = randint(5, 10)
        print("Sleeping for {} seconds".format(str(num)))
        time.sleep(num)

if __name__ == "__main__":
    if INPUT_FILE == "changeme.html" or USERNAME == "Change-Me-Too":
        print("Oops, you must change INPUT_FILE and USERNAME first")
    else:
        #want = extract_answers(make_soup(INPUT_FILE))
        want = list(extract_answers(make_soup(INPUT_FILE)))
        #print(len(want))
        print(want)
        #process_urls(want)
