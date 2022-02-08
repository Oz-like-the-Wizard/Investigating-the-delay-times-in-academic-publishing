import io
import re

from datetime import datetime
from pdfminer.high_level import extract_text
import PyPDF2 as pdf2


from unpywall import Unpywall
from unpywall.utils import UnpywallCredentials
UnpywallCredentials('oguzkokes@gmail.com')


def Unpy_filterer(oa_dict):
    if len(oa_dict) == 0:
        return "Scihub"
    else:
        pdf_urls = []
        for key in oa_dict:
            if "version" in key:
                if key["version"] is not None:
                    if ("publish" in key["version"]):
                        if key["url_for_pdf"] is not None:
                            pdf_urls.append(key["url_for_pdf"]) 
                
        return "Scihub" if len(pdf_urls) == 0 else list(set(pdf_urls))


def rec_date_capture(pdf_text):
    # REGEX PATTERNS - RECEIVED & SUBMITTED
    # 1 - 10 MAY 1960:
    rec_1 =  "(?:(?:received|submitted)\s?(?:on|date)?\s?\:?\s?)(\d{1,2}\s*(Jan(uary)?|Feb(ruary)?|Mar(ch)|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)\s*(19|20)\d{2})"
    # 2 - MAY 10, 1960
    rec_2 = "(?:(?:received|submitted)\s?(?:on|date)?\s?\:?\s?)((Jan(uary)?|Feb(ruary)?|Mar(ch)|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)\s?\d{1,2}\,?\s?(19|20)\d{2})"
    # 3 - MAY 1960
    rec_3 = "(?:(?:received|submitted)\s?(?:on|date)?\s?\:?\s?)((Jan(uary)?|Feb(ruary)?|Mar(ch)|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)\s*(19|20)\d{2})"
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

def acc_date_capture(pdf_text):
    # REGEX PATTERNS - ACCEPTED
    # 1 - 10 MAY 1960:
    acc_1 =  "(?:(?:accepted)\s?(?:on|date|for publication on)?\s?\:?\s?)(\d{1,2}\s*(Jan(uary)?|Feb(ruary)?|Mar(ch)|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)\s*(19|20)\d{2})"
    # 2 - MAY 10, 1960
    acc_2 = "(?:(?:accepted)\s?(?:on|date|for publication on)?\s?\:?\s?)((Jan(uary)?|Feb(ruary)?|Mar(ch)|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)\s?\d{1,2}\,?\s?(19|20)\d{2})"
    # 3 - MAY 1960
    acc_3 = "(?:(?:accepted)\s?(?:on|date|for publication on)?\s?\:?\s?)((Jan(uary)?|Feb(ruary)?|Mar(ch)|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)\s*(19|20)\d{2})"
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

def pdf_counter(pdf_io):
    try:
        pdf_pdf = pdf2.PdfFileReader(pdf_io)
        pg_count = pdf_pdf.getNumPages()
    except:
        pg_count = 0

    return [] if pg_count<3 else [0,1,2, pg_count-1, pg_count-2, pg_count-3]

def Unpy_dates(url_list,sess):
    #error_list = []
    for doi_url in url_list:
        try:
            req_direct = sess.get(doi_url, timeout=10)
            doi_file = io.BytesIO(req_direct.content)
            pg_count = pdf_counter(doi_file)
            pdf_read = extract_text(doi_file,page_numbers=pg_count).replace("\n", "")
        except:
            pass
        else:
            rec_date = rec_date_capture(pdf_read)
            acc_date = acc_date_capture(pdf_read)                    
            if (rec_date != None) | (acc_date != None):
                return [doi_url, rec_date, acc_date]
    #return error_list

"""
def try_parsing_date(text):
    for fmt in ('%d%B%Y', '%d %B %Y', '%B %d, %Y'):
        try:
            resres = datetime.strptime(str(text), fmt)
        except ValueError:
            pass
    try:
        return resres
    except:
        return text

"""
