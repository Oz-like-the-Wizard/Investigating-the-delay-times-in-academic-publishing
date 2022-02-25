"""

ARTICLE DATE - AFFILIATION - KEYWORDS EXTRACTOR - SCIHUB

@author Ogi_Boi
"""

import requests
import io
import pandas as pd
import regex as re
import numpy as np
import json
from statistics import multimode

from retry import retry
import urllib3

#from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text
import PyPDF2 as pdf2

import pycountry

from keybert import KeyBERT
#from nltk.corpus import stopwords
#from nltk.corpus import words
#from nltk.tokenize import word_tokenize
#from nltk.stem import WordNetLemmatizer
#import snowballstemmer

#
urllib3.disable_warnings()

# constants
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36'}

def uni_dict_creator():
    with open('world_universities_and_domains.json', encoding="utf8") as fp:
        uni_dict = json.load(fp)

    uni_df = pd.DataFrame(uni_dict)

    uni_code_country_dict = {}
    uni_name_country_dict = {}

    for index, row in uni_df.iterrows():
        uni_code_country_dict.update({dom : row.country for dom in row.domains})
        uni_name_country_dict.update({row["name"] : row.country})

    del uni_name_country_dict["University of Technology"]

    return uni_code_country_dict, uni_name_country_dict

class FourZeroFourError(Exception):
    pass

class OgiError(Exception):
    pass

class SciHub_WaterGun(object):
    """
    Main class object
    """
    uni_code_country_dict, uni_name_country_dict = uni_dict_creator()

    cntry_name_list = [cntry.name for cntry in list(pycountry.countries)] + ["USA"]
    cntry_code_dict = {cntry.alpha_2.lower() : cntry.name for cntry in list(pycountry.countries)}

    # REGEX PATTERNS:
    # Email Pattern:
    email_reg = re.compile("[a-zA-Z0-9._-]+@([a-zA-Z0-9_-]+\.((?:[a-zA-Z0-9_-]+\.)*([a-zA-Z0-9_-]+)))")
    # Uni Names Pattern:
    uni_name_regex = re.compile("(?=("+'|'.join(list(uni_name_country_dict.keys()))+r"))")
    # Country Names Pattern:
    country_name_regex = re.compile("(?=("+'|'.join(cntry_name_list)+r"))")

    # RECEIVED & SUBMITTED:
    rec_1 = re.compile("(?:(?:received|submitted)\s?(?:on|date)?\s?\:?\s?)(\d{1,2}\s*(Jan(uary|.)?|Feb(ruary|.)?|Mar(ch|.)?|Apr(il|.)?|May|Jun(e|.)?|Jul(y|.)?|Aug(ust|.)?|Sep(tember|.)?|Oct(ober)?|Nov(ember|.)?|Dec(ember|.)?)\s*(19|20)\d{2})", re.IGNORECASE)
    rec_2 = re.compile("(?:(?:received|submitted)\s?(?:on|date)?\s?\:?\s?)((Jan(uary|.)?|Feb(ruary|.)?|Mar(ch|.)?|Apr(il|.)?|May|Jun(e|.)?|Jul(y|.)?|Aug(ust|.)?|Sep(tember|.)?|Oct(ober|.)?|Nov(ember|.)?|Dec(ember|.)?)\s?\d{1,2}\,?\s?(19|20)\d{2})", re.IGNORECASE)
    rec_3 = re.compile("(?:(?:received|submitted)\s?(?:on|date)?\s?\:?\s?)((Jan(uary|.)?|Feb(ruary|.)?|Mar(ch|.)?|Apr(il|.)?|May|Jun(e|.)?|Jul(y|.)?|Aug(ust|.)?|Sep(tember|.)?|Oct(ober|.)?|Nov(ember|.)?|Dec(ember|.)?)\s*(19|20)\d{2})", re.IGNORECASE)
    rec_4 = re.compile("(?:(?:received|submitted)\s?(?:on|date)?\s?\:?\s?)([1-3][0-9](\.|\-|\/|\:)?[0-1][0-9](\.|\-|\/\:)?(19|20)\d{2})", re.IGNORECASE)

    # ACCEPTED:
    acc_1 = re.compile("(?:(?:accepted)\s?(?:on|date|for publication on|in revised form)?\s?\:?\s?)(\d{1,2}\s*(Jan(uary|.)?|Feb(ruary|.)?|Mar(ch|.)?|Apr(il|.)?|May|Jun(e|.)?|Jul(y|.)?|Aug(ust|.)?|Sep(tember|.)?|Oct(ober|.)?|Nov(ember|.)?|Dec(ember|.)?)\s*(19|20)\d{2})", re.IGNORECASE)
    acc_2 = re.compile("(?:(?:accepted)\s?(?:on|date|for publication on|in revised form)?\s?\:?\s?)((Jan(uary|.)?|Feb(ruary|.)?|Mar(ch|.)?|Apr(il|.)?|May|Jun(e|.)?|Jul(y|.)?|Aug(ust|.)?|Sep(tember|.)?|Oct(ober|.)?|Nov(ember|.)?|Dec(ember|.)?)\s?\d{1,2}\,?\s?(19|20)\d{2})", re.IGNORECASE)
    acc_3 = re.compile("(?:(?:accepted)\s?(?:on|date|for publication on|in revised form)?\s?\:?\s?)((Jan(uary|.)?|Feb(ruary|.)?|Mar(ch|.)?|Apr(il|.)?|May|Jun(e|.)?|Jul(y|.)?|Aug(ust|.)?|Sep(tember|.)?|Oct(ober|.)?|Nov(ember|.)?|Dec(ember|.)?)\s*(19|20)\d{2})", re.IGNORECASE)
    acc_4 = re.compile("(?:(?:accepted)\s?(?:on|date|for publication on|in revised form)?\s?\:?\s?)([1-3][0-9](\.|\-|\/|\:)?[0-1][0-9](\.|\-|\/\:)?(19|20)\d{2})", re.IGNORECASE)

    def __init__(self):
        self.sess = requests.Session()
        self.sess.headers = HEADERS
        self.available_base_url_list = iter(["https://sci-hub.st/", "https://sci-hub.se/", "https://sci-hub.ee/", "https://sci-hub.wf/", "https://sci-hub.ru/", "https://sci-hub.mksa.top/"])
        self.base_url = next(self.available_base_url_list)
        self.kw_model = KeyBERT()

    def _change_base_url(self):
        try:
            self.base_url = next(self.available_base_url_list)
        except StopIteration:
            self.available_base_url_list = iter(["https://sci-hub.st/", "https://sci-hub.se/", "https://sci-hub.ee/", "https://sci-hub.wf/", "https://sci-hub.ru/", "https://sci-hub.mksa.top/"])
            self.base_url = next(self.available_base_url_list)

    def rec_date_capture(self,pdf_read):
        rec_patterns = [SciHub_WaterGun.rec_1, SciHub_WaterGun.rec_2, SciHub_WaterGun.rec_3, SciHub_WaterGun.rec_4]
        for pattern in rec_patterns:
            try:
                date = pattern.search(pdf_read).group(1)
            except AttributeError:
                pass
            else:
                return date

    def acc_date_capture(self,pdf_text):
        acc_patterns = [SciHub_WaterGun.acc_1, SciHub_WaterGun.acc_2, SciHub_WaterGun.acc_3, SciHub_WaterGun.acc_4]
        for pattern in acc_patterns:
            try:
                date = pattern.search(pdf_text).group(1)
            except AttributeError:
                pass
            else:
                return date

    def get_dates(self,pdf_read):
        rec_date = self.rec_date_capture(pdf_read)
        acc_date = self.acc_date_capture(pdf_read)
        return [rec_date, acc_date] if (rec_date != None) | (acc_date != None) else "no_date_found"

    def email_converter(self,pdf_read):
        email_caught = SciHub_WaterGun.email_reg.search(pdf_read)

        try:
            return SciHub_WaterGun.uni_code_country_dict[email_caught.group(1).lower()]
        except AttributeError:
            return np.nan
        except KeyError:
            try:
                return SciHub_WaterGun.uni_code_country_dict[email_caught.group(2).lower()]
            except KeyError:
                try:
                    return SciHub_WaterGun.cntry_code_dict[email_caught.group(3)]
                except KeyError:
                    cntry_pttrn =  email_caught.group(3)[:3]

                    if cntry_pttrn in ["com","net"]:
                        return np.nan

                    elif cntry_pttrn in ["edu","gov"]:
                        return "United States"

                    if len(cntry_pttrn)==3:
                        cntry_pttrn = cntry_pttrn[:-1]

                    try:
                        return SciHub_WaterGun.cntry_code_dict[cntry_pttrn]
                    except:
                        return np.nan
            
    def univ_converter(self,pdf_read):   
        try:
            uni_found = SciHub_WaterGun.uni_name_regex.search(pdf_read)[1]
            return SciHub_WaterGun.uni_name_country_dict[uni_found]
        except:
            return np.nan

    def country_converter(self,pdf_read):
        try:
            cntry_match = SciHub_WaterGun.country_name_regex.search(pdf_read)[1]
            return  cntry_match if cntry_match != "USA" else "United States"
        except TypeError:
            try:
                return SciHub_WaterGun.country_name_regex.search(pdf_read.title())[1]
            except:
                return np.nan

    def get_affiliations(self,pdf_read):
        email_affl = self.email_converter(pdf_read)
        uni_affl = self.univ_converter(pdf_read)
        cntry_affl = self.country_converter(pdf_read)

        affl_vote = multimode([email_affl,uni_affl,cntry_affl])

        if (len(affl_vote) == 1) & (not pd.isnull(affl_vote[0])):
            return affl_vote[0]
        elif not pd.isnull(email_affl):
            return email_affl
        elif not pd.isnull(uni_affl):
            return uni_affl
        else:
            return cntry_affl

    # Simple Preprocessing:
    def prep_simple(self,pdf_read):
        pdf_read = pdf_read.replace("\n"," ")
        pdf_read = re.sub(' +', ' ', pdf_read)
        return pdf_read

    def remove_references(self,pdf_read):
        # Removing "References":
        pdf_modified = "".join(pdf_read.split("references")[:-1])
        
        if len(pdf_modified) > 0:
            return pdf_modified 
        else:
            pdf_modified = "".join(pdf_read.split("acknowledgements")[:-1])
            if len(pdf_modified) > 0:
                return pdf_modified 
            else:
                return pdf_read
    
    # Main Preprocessing:
    def prep_main(self,pdf_read):
        # Lowercase all:
        pdf_modified = pdf_read.lower()
        # Removing "References":
        pdf_modified = self.remove_references(pdf_modified)
        # Remove URL:
        pdf_modified = re.sub(r'http\S+', '', pdf_modified)
        # Remove emails:
        pdf_modified = re.sub(r"\S*@\S*\s?", "", pdf_modified)
        # Remove everything in brackets & paranthesis:
        pdf_modified = re.sub("[\(\[].*?[\)\]]", "", pdf_modified)
        # Remove punctuation:
        pdf_modified = re.sub(r'[^\w\s]', '', pdf_modified)
        # Remove numbers
        pdf_modified = re.sub(r'[0-9]', '', pdf_modified)
        # Remove HTML tags:
        pdf_modified = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', pdf_modified)
        # Remove single letters:
        pdf_modified = re.sub(r"(?<=(^|\s))\D(\s|$)","", pdf_modified)
        # Remove multiple spaces:
        pdf_modified = re.sub(' +', ' ', pdf_modified)
        # Return pdf_modified
        return pdf_modified

    def get_keywords(self,pdf_read):
        keywords = self.kw_model.extract_keywords(pdf_read, keyphrase_ngram_range=(1, 1), stop_words="english", top_n=10)
        return keywords

    @retry((FourZeroFourError),tries=5, delay=15)
    def get_pdf_bytes(self, pdf_url):
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
                return pdf_bytes
            except:
                self._change_base_url()
                raise FourZeroFourError("can't get bytes")

    @retry((OgiError), tries=3, delay=5)
    def pdf_reader(self,pdf_bytes):
        try:
            pdf_pdf = pdf2.PdfFileReader(pdf_bytes, strict=False)
            pg_count = pdf_pdf.getNumPages()
        except:
            pg_count = 0

        if pg_count<3:
            pg_count = []
        else:
            pg_count = [0,1,2, pg_count-1, pg_count-2, pg_count-3]

        try:
            pdf_read = extract_text(pdf_bytes,page_numbers=pg_count)
            return pdf_read
        except:
            self._change_base_url()
            raise OgiError("can't read pdf")

    def get_all(self, pdf_url):

        try:
            pdf_bytes = self.get_pdf_bytes(pdf_url)       
        except FourZeroFourError:
            return "direct_url_error", "direct_url_error", "direct_url_error"

        try:
            pdf_read = self.pdf_reader(pdf_bytes)
        except OgiError:
            return "cant_read_pdf", "cant_read_pdf", "cant_read_pdf"

        else:
            pdf_read = self.prep_simple(pdf_read)

            dates = self.get_dates(pdf_read)
            affiliations = self.get_affiliations(pdf_read)

            pdf_read = self.prep_main(pdf_read)
            keywords = self.get_keywords(pdf_read)

            return dates, affiliations, keywords
