"""

ARTICLE DATE EXTRACTOR - SCIHUB

@author Ogi_Boi
"""

import argparse
import logging
import io
import regex as re

import requests
import urllib3
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text
from retry import retry
import PyPDF2 as pdf2



# log config
logging.basicConfig()
logger = logging.getLogger('Sci-Hub')
logger.setLevel(logging.DEBUG)

#
urllib3.disable_warnings()

# constants
#HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'}
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36'}

class OgiError(Exception):
    pass

class FourZeroFourError(Exception):
    pass

class SciHub(object):
    """
    Main class object
    """

    def __init__(self):
        self.sess = requests.Session()
        self.sess.headers = HEADERS
        self.available_base_url_list = iter(["https://sci-hub.st/", "https://sci-hub.se/", "https://sci-hub.ee/", "https://sci-hub.wf/", "https://sci-hub.ru/", "https://sci-hub.mksa.top/"])
        self.base_url = next(self.available_base_url_list)

    #def _get_available_scihub_urls(self):
    #    '''
    #    Finds available scihub urls via https://sci-hub.now.sh/
    #    '''
    #    res = requests.get('https://sci-hub.now.sh/')
    #    s = self._get_soup(res.content)
    #    urls = [link.text for link in s.find_all("a", {"rel":"nofollow noopener", "target":"_blank"}) if "http" in link.text]
    #    #pt_banned_urls = ["https://sci-hub.tw", "https://sci-hub.shop", "https://sci-hub.se"]
    #    #urls = [url for url in urls if url not in pt_banned_urls]
    #    return urls



    def _change_base_url(self):
        try:
            self.base_url = next(self.available_base_url_list)
        except StopIteration:
            self.available_base_url_list = iter(["https://sci-hub.st/", "https://sci-hub.se/", "https://sci-hub.ee/", "https://sci-hub.wf/", "https://sci-hub.ru/", "https://sci-hub.mksa.top/"])
            self.base_url = next(self.available_base_url_list)



    def rec_date_capture(self, pdf_text):

        # REGEX PATTERNS - RECEIVED & SUBMITTED
        # 1 - 10 MAY 1960:
        rec_1 =  "(?:(?:received|submitted)\s?(?:on|date)?\s?\:?\s?)(\d{1,2}\s*(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)\s*(19|20)\d{2})"
        # 2 - MAY 10, 1960
        rec_2 = "(?:(?:received|submitted)\s?(?:on|date)?\s?\:?\s?)((Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)\s?\d{1,2}\,?\s?(19|20)\d{2})"
        # 3 - MAY 1960
        rec_3 = "(?:(?:received|submitted)\s?(?:on|date)?\s?\:?\s?)((Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)\s*(19|20)\d{2})"
        # 4 - 10/05/1960 OR 10.05.1960 OR 10/05/1960
        rec_4 = "(?:(?:received|submitted)\s?(?:on|date)?\s?\:?\s?)([1-3][0-9](\.|\-|\/|\:)?[0-1][0-9](\.|\-|\/\:)?(19|20)\d{2})"

        rec_patterns = [rec_1, rec_2, rec_3, rec_4]

        for pattern in rec_patterns:
            comp_pattern = re.compile(pattern, re.IGNORECASE) 
            try:
                date = re.search(comp_pattern,pdf_text).group(1)
            except AttributeError:
                pass
            else:
                return date

    def acc_date_capture(self, pdf_text):

        # REGEX PATTERNS - ACCEPTED
        # 1 - 10 MAY 1960:
        acc_1 =  "(?:(?:accepted)\s?(?:on|date|for publication on)?\s?\:?\s?)(\d{1,2}\s*(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)\s*(19|20)\d{2})"
        # 2 - MAY 10, 1960
        acc_2 = "(?:(?:accepted)\s?(?:on|date|for publication on)?\s?\:?\s?)((Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)\s?\d{1,2}\,?\s?(19|20)\d{2})"
        # 3 - MAY 1960
        acc_3 = "(?:(?:accepted)\s?(?:on|date|for publication on)?\s?\:?\s?)((Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)\s*(19|20)\d{2})"
        # 4 - 10/05/1960 OR 10.05.1960 OR 10/05/1960
        acc_4 = "(?:(?:accepted)\s?(?:on|date|for publication on)?\s?\:?\s?)([1-3][0-9](\.|\-|\/|\:)?[0-1][0-9](\.|\-|\/\:)?(19|20)\d{2})"

        acc_patterns = [acc_1, acc_2, acc_3, acc_4]

        for pattern in acc_patterns:
            comp_pattern = re.compile(pattern, re.IGNORECASE) 
            try:
                date = re.search(comp_pattern,pdf_text).group(1)
            except AttributeError:
                pass
            else:
                return date

    def _get_soup(self, html):
        """
        Return html soup.
        """
        return BeautifulSoup(html, 'html.parser')

    #def pdf_counter(self,pdf_io):
    #    try:
    #        pdf_pdf = pdf2.PdfFileReader(pdf_io)
    #        pg_count = pdf_pdf.getNumPages()
    #    except:
    #        pg_count = 0
    #    return [] if pg_count<3 else [0,1,2, pg_count-1, pg_count-2, pg_count-3]
    

    @retry((OgiError),tries=5, delay=75)
    @retry((FourZeroFourError),tries=4, delay=15)
    def get_pdf_bytes(self, identifier):

        try:
            total_url = self.base_url + identifier
            res = self.sess.get(total_url, verify=False, timeout=30)
            s = self._get_soup(res.content)

        except :
            self._change_base_url
            self.sess = requests.Session()
            self.sess.headers = HEADERS

            raise OgiError("cant_connect_to Scihub")

        try:
            iframe = s.find(re.compile(r"(iframe|embed)"), {"id": "pdf"})["src"]

            if not iframe.startswith('//'):
                pdf_url = iframe
            else: 
                pdf_url = 'http:' + iframe

        except TypeError:
            if ("article not found" in s.text) |  ("sci-hub has not included this article yet" in s.text):
                return "article_not_in Scihub", "article_not_in Scihub"

            elif not s.text:
                self._change_base_url()
                raise OgiError("Nothing here!")

            elif "для " in s.text:
                self._change_base_url()
                print("Discovered CAPTCHA!")
                raise OgiError("Discovered CAPTCHA!") 

            else:
                self._change_base_url()
                raise OgiError("Unknown issue!")

        try:
            pdf_cont = self.sess.get(pdf_url, verify=False, timeout=15)

            if pdf_cont.status_code == 404:
                self._change_base_url()
                raise FourZeroFourError("Threat Level: 404")

        except:
            self._change_base_url()
            raise FourZeroFourError(f"Can't connect to direct URL: {pdf_url}")

        else:
            try:
                pdf_bytes = io.BytesIO(pdf_cont.content)
                return pdf_url, pdf_bytes
            except:
                self._change_base_url()
                raise FourZeroFourError("can't get bytes")

    @retry((OgiError), tries=3, delay=5)
    def pdf_reader(self,pdf_bytes):
        try:
            pdf_pdf = pdf2.PdfFileReader(pdf_bytes)
            pg_count = pdf_pdf.getNumPages()
        except:
            pg_count = 0

        if pg_count<3:
            pg_count = []
        else:
            pg_count = [0,1,2, pg_count-1, pg_count-2, pg_count-3]

        try:
            pdf_read = extract_text(pdf_bytes,page_numbers=pg_count).replace("\n", "")
            return pdf_read
        except:
            self._change_base_url()
            raise OgiError("can't read pdf")

    def get_dates(self, identifier):
        try:
            pdf_url, pdf_bytes = self.get_pdf_bytes(identifier)
            if pdf_bytes == "article_not_in Scihub":
                return "article_not_in Scihub"

        except OgiError:
            return "direct_url_error"

        except FourZeroFourError:
            return "pdf_bytes_error"

        try:
            pdf_read = self.pdf_reader(pdf_bytes)

        except OgiError:
            return "cant_read_pdf"

        else:
            rec_date = self.rec_date_capture(pdf_read)
            acc_date = self.acc_date_capture(pdf_read)                    
            return [pdf_url, rec_date, acc_date] if (rec_date != None) | (acc_date != None) else [pdf_url, "no_date_found"]


def main():
    sh = SciHub()

    parser = argparse.ArgumentParser(description='SciHub - To remove all barriers in the way of science.')
    parser.add_argument('-d', '--download', metavar='(DOI|PMID|URL)', help='tries to find and download the paper',
                        type=str)
    parser.add_argument('-f', '--file', metavar='path', help='pass file with list of identifiers and download each',
                        type=str)
    parser.add_argument('-s', '--search', metavar='query', help='search Google Scholars', type=str)
    parser.add_argument('-sd', '--search_download', metavar='query',
                        help='search Google Scholars and download if possible', type=str)
    parser.add_argument('-l', '--limit', metavar='N', help='the number of search results to limit to', default=10,
                        type=int)
    parser.add_argument('-o', '--output', metavar='path', help='directory to store papers', default='', type=str)
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    parser.add_argument('-p', '--proxy', help='via proxy format like socks5://user:pass@host:port', action='store', type=str)

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    if args.proxy:
        sh.set_proxy(args.proxy)

    if args.download:
        result = sh.download(args.download, args.output)
        if 'err' in result:
            logger.debug('%s', result['err'])
        else:
            logger.debug('Successfully downloaded file with identifier %s', args.download)
    elif args.search:
        results = sh.search(args.search, args.limit)
        if 'err' in results:
            logger.debug('%s', results['err'])
        else:
            logger.debug('Successfully completed search with query %s', args.search)
        print(results)
    elif args.search_download:
        results = sh.search(args.search_download, args.limit)
        if 'err' in results:
            logger.debug('%s', results['err'])
        else:
            logger.debug('Successfully completed search with query %s', args.search_download)
            for paper in results['papers']:
                result = sh.download(paper['url'], args.output)
                if 'err' in result:
                    logger.debug('%s', result['err'])
                else:
                    logger.debug('Successfully downloaded file with identifier %s', paper['url'])
    elif args.file:
        with open(args.file, 'r') as f:
            identifiers = f.read().splitlines()
            for identifier in identifiers:
                result = sh.download(identifier, args.output)
                if 'err' in result:
                    logger.debug('%s', result['err'])
                else:
                    logger.debug('Successfully downloaded file with identifier %s', identifier)


if __name__ == '__main__':
    main()
