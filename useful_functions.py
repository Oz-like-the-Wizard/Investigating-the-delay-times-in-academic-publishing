import regex as re
import pickle
import pandas as pd
import numpy as np


def earlier_date_part(row):
    try:
        pp_year = row["published-print"]["date-parts"][0][0]
    except TypeError:
        pp_year = None

    try:   
        po_year = row["published-online"]["date-parts"][0][0]
    except TypeError:
        po_year = None

    if po_year is None:
        return row["published-print"]

    elif pp_year is None:
        return row["published-online"]

    else:
        if pp_year<po_year:
            return row["published-print"]
        elif po_year<pp_year:
            return row["published-online"]
        else:
            try:
                pp_month = row["published-print"]["date-parts"][0][1]
            except IndexError:
                pp_month = 12
            try:
                po_month = row["published-online"]["date-parts"][0][1]
            except IndexError:
                po_month = 12
            if pp_month<po_month:
                return row["published-print"]
            elif po_month<pp_month:
                return row["published-online"]
            else:
                return row["published-online"]



def sbj_area_query_creator(sbj_list):
    scopus_codes_dict = {'Agricultural and Biological Sciences': 'AGRI',
    'Arts and Humanities': 'ARTS',
    'Biochemistry, Genetics and Molecular Biology': 'BIOC',
    'Business, Management and Accounting': 'BUSI',
    'Chemical Engineering': 'CENG',
    'Chemistry': 'CHEM',
    'Computer Science': 'COMP',
    'Decision Sciences': 'DECI',
    'Dentistry': 'DENT',
    'Earth and Planetary Sciences': 'EART',
    'Economics, Econometrics and Finance': 'ECON',
    'Energy': 'ENER',
    'Engineering': 'ENGI',
    'Environmental Science': 'ENVI',
    'Health Professions': 'HEAL',
    'Immunology and Microbiology': 'IMMU',
    'Materials Science': 'MATE',
    'Mathematics': 'MATH',
    'Medicine': 'MEDI',
    'Neuroscience': 'NEUR',
    'Nursing': 'NURS',
    'Pharmacology, Toxicology and Pharmaceutics': 'PHAR',
    'Physics and Astronomy': 'PHYS',
    'Psychology': 'PSYC',
    'Social Sciences': 'SOCI',
    'Veterinary': 'VETE',
    'Multidisciplinary': 'MULT'}
    
    query = " AND ".join([f"SUBJAREA({scopus_codes_dict[sbj]})" for sbj in sbj_list])
    return query


def name_simplifier(pdf_read):
    # Lowercase all:
    pdf_modified = pdf_read.lower()
    # Remove everything in brackets & paranthesis:
    pdf_modified = re.sub("[\(\[\{].*?[\)\]\}]", "", pdf_modified)
    # Remove quote names:
    pdf_modified = re.sub('["“].*?["”]', "", pdf_modified)
    # Remove numbers
    pdf_modified = re.sub(r'[0-9]', '', pdf_modified)
    # Remove weird punct.
    pdf_modified = re.sub(r'[&\?\$\+\\\*\^\|]', '', pdf_modified)
    # Simplify acct. a:
    pdf_modified = re.sub(r'[áạàảãăặằẳẵâấậầẩẫā]', 'a', pdf_modified)
    # Simplify acct. i:
    pdf_modified = re.sub(r'[íịìỉĩïǐĭīĩįɨıî]', 'i', pdf_modified)
    # Simplify acct. i:
    pdf_modified = re.sub(r'[éẹèẻẽêếệềểễ]', 'e', pdf_modified)
    # Simplify acct. o:
    pdf_modified = re.sub(r'[óòȯôöǒŏōõǫőốồøṓṑ]', 'o', pdf_modified)
    # Simplify acct. u:
    pdf_modified = re.sub(r'[úùûüǔŭūũů]', 'u', pdf_modified)
    # Remove multiple spaces:
    pdf_modified = re.sub(' +', ' ', pdf_modified)
    # Return pdf_modified
    return pdf_modified

def flatten(l):
    return [item for sublist in l for item in sublist]


def pickle_loader(filename):
    with open(filename, "rb") as fp:
        return pickle.load(fp)


def pickle_dumper(variable, filename):
    with open(filename,"wb") as p:
        pickle.dump(variable, p)


def main_subd_converter(sub_d):
    try:
        if bool(re.search("[A-Za-z]",sub_d)):
            try:
                return pd.to_datetime(sub_d, infer_datetime_format=True)
            except:
                sub_d = re.sub('(\d+(\.\d+)?)', r' \1', sub_d)
                return pd.to_datetime(sub_d, infer_datetime_format=True)

        else:
            try:
                return pd.to_datetime(sub_d, format='%d-%m-%Y')
            except:
                return pd.to_datetime(sub_d, format='%d.%m.%Y')
    except:
        return np.nan


def publ_date_filler(pub_d):
    if len(pub_d) == 3:
        return pub_d
    elif len(pub_d) == 2:
        pub_d.append(15)
        return pub_d
    elif len(pub_d) == 1:
        pub_d.append(6)
        pub_d.append(15)
        return pub_d
