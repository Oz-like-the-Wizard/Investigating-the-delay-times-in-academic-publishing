from bs4 import BeautifulSoup, NavigableString
import requests
import regex as re
import pandas as pd

from os import listdir

# As Scimago uses Fields for Subj Area mapping,mwe can use the official website table for Sbuj Ara & Category mapping.
# If a Field name starts with "General", it is a new Subject Area for Scimago

sci_web = requests.get("https://service.elsevier.com/app/answers/detail/a_id/15181/supporthub/scopus/")
sci_soup = BeautifulSoup(sci_web.content, "html.parser")

# Creating a dict "sbj_dict" for Subject Area & Category mapping

sbj_dict = {"Multidisciplinary": ["Multidisciplinary"]}
sbj_key = ""
cat_list= []

for row in sci_soup.find("table").findAll("tr")[2:]:
    cat_name = row.getText().split("\n")[2]
    
    if (("General" in cat_name) | ("Speech and Hearing" in cat_name)):
        sbj_dict[sbj_key] = cat_list
        cat_list = []
        sbj_key = cat_name.replace("General ", "")
    else:
        cat_list.append(cat_name)

sbj_dict.pop("")

# Checking the number of Subject Areas in sbj_dcit (supposed to be 27)
#len(sbj_dict)

# Collect all "Subject Category"s in a list, in case we need to use them in the future

web_sbj_set = []

for k in sbj_dict:
    web_sbj_set.extend(sbj_dict[k])

sbj_set = set(web_sbj_set)

#print(f"The number of categories scraped: {len(web_sbj_set)}")

# Check if there are any duplicate Subject Categories in the captured categories

#control_list = web_sbj_set[:]
# ...

# The resulting control_list shows that, there are  no duplicates, however we have missing categories (313 vs 307)

# Check which Categories are missing in the sbj_dict by looping through the all the years

yearCsv = listdir("Years")

all_sbj_set = set()

for csv_name in yearCsv:
    yeardf = pd.read_csv("Years\\" + csv_name, sep=";", error_bad_lines=False)
    year_sbj = yeardf["Categories"].str.replace(r"\s\(\w\d\)", "", regex=True).str.split("; ")

    year_sbj_set = []

    for lst in year_sbj:
        year_sbj_set.extend(lst)

    year_sbj_set = {cat.strip() for cat in year_sbj_set}
    
    all_sbj_set = all_sbj_set.union(year_sbj_set)

#print(f"The number of categories between 2010 - 2020: {len(all_sbj_set)}")

# E-learning -> "Social Sciences"
# Nanoscience and Nanotechnology -> "Material Science"
# Social Work -> "Social Sciences"
# Speech and Hearing -> "Health Professions"
# Sports Science -> "Health Professions"

sbj_dict["Social Sciences"].append('E-learning')
sbj_dict["Materials Science"].append('Nanoscience and Nanotechnology')
sbj_dict["Social Sciences"].append('Social Work')
sbj_dict["Health Professions"].append("Speech and Hearing")
sbj_dict["Health Professions"].append("Sports Science")

# Collect all "Subject Category"s in a list, in case we need to use them in the future

web_sbj_set = []

for k in sbj_dict:
    web_sbj_set.extend(sbj_dict[k])

sbj_set = set(web_sbj_set)

#print(f"The total number of included categories: {len(web_sbj_set)}")

cat_sbj_dict = {}

for sbj in sbj_dict:
    for cat in sbj_dict[sbj]:
        cat_sbj_dict[cat] = sbj

