import pandas as pd
import numpy as np
from os import listdir
import re

from statistics import mode
from collections import Counter
from random import sample, choices

import warnings
warnings.filterwarnings("ignore")

from scimago import cat_sbj_dict

def only_highest(qlist):
    for i in range(5):
        new_list = [re.sub(r"\s\(\w{2}\)", "", cat) for cat in qlist if str(i) in cat]
        if len(new_list)>0:
            quartile = i
            break
    try:
        return new_list, quartile
    except:
        return [], np.nan


def quar_df_creator(quartile):

    if quartile == "all":
        q1_df = pd.DataFrame()
        q2_df = pd.DataFrame()
        q3_df = pd.DataFrame()
        q4_df = pd.DataFrame()
    else:
        q_df = pd.DataFrame()

    yearList = listdir("Years")

    for year in yearList:
        yearnow = re.split("[.\s]", year)[1].strip()

        yeardf = pd.read_csv("Years\\" + year, sep=";", error_bad_lines=False)

        # 1 - SJR Best Quartile
        yeardf = yeardf[yeardf['SJR Best Quartile'] != "-"]

        # 2 - Type
        yeardf = yeardf[yeardf['Type'] == "journal"]

        # 3 - Category & Sbj Area
        yeardf[["New_Cat", "Quartile"]] = yeardf.apply(lambda x: only_highest(qlist=x.Categories.split("; ")), axis=1, result_type="expand")
        yeardf["Sbj_Area"] = yeardf.New_Cat.map(lambda x: [cat_sbj_dict[cat.strip()] for cat in x]).map(Counter)

        # 4 - Basic Feature Engineering
        yeardf["Issn"] = yeardf.Issn.str.split(",")
        yeardf["Issn"] = yeardf.Issn.map(lambda x: [iss.strip() for iss in x])
        yeardf["Year"] = yearnow
        yeardf["Total_Docs"] = yeardf[f"Total Docs. ({yearnow})"]
        yeardf.drop(["SJR Best Quartile", "Categories", f"Total Docs. ({yearnow})"], axis=1, inplace=True)

        if quartile == "all":
            
            q1_df = q1_df.append(yeardf[yeardf.Quartile == 1])
            q2_df = q2_df.append(yeardf[yeardf.Quartile == 2])
            q3_df = q3_df.append(yeardf[yeardf.Quartile == 3])
            q4_df = q4_df.append(yeardf[yeardf.Quartile == 4])
        else:
            q_df = q_df.append(yeardf[yeardf.Quartile == quartile])

    if quartile == "all":
        return q1_df, q2_df, q3_df, q4_df
    else:
        return q_df   


def jrnl_meta_simplifier(jrnl_df, n_id):

    jrnl_df.rename(columns={"Issn":"ISSN"}, inplace=True)
    jrnl_df["ISSN"] = jrnl_df.ISSN.map(tuple)
    
    jrnl_df["Year"] = jrnl_df.Year.astype(int)

    jrnl_df = jrnl_df[jrnl_df.Total_Docs>20]

    jrnl_df.sort_values("ISSN", inplace=True)

    jrnl_df.insert(loc=0, column='ID', value=jrnl_id_creator(n_id,jrnl_df))
    jrnl_df.set_index("ID", inplace=True)

    return jrnl_df[["ISSN", "Year", "Title", "Sbj_Area", "Total_Docs", 'Country', 'Region', 'Publisher', 'Coverage', 'SJR', 'H index', 'Total Docs. (3years)', 'Total Refs.', 'Total Cites (3years)', 'Citable Docs. (3years)', 'Cites / Doc. (2years)', 'Ref. / Doc.']]


def explade(countdf):
    # No need to extract ISSNs as CrossRef func. accepts lists as argument
    count1_df = countdf[countdf["Sbj_Area"].map(len) == 1]
    count1_df["Sbj_Area"] = count1_df["Sbj_Area"].map(list).str[0]
    count2_df = countdf[countdf["Sbj_Area"].map(len) > 1]
    
    newcount_list = []

    for index, row in count2_df.iterrows():
        issn = row["ISSN"]
        year = row["Year"] 
        s_a = row["Sbj_Area"]
        #cr_ = row["CR_Results"]
        sh_ = row["SH_Results"]
        #crc = row["CR_Count"]
        tot_docs = row["Total_Docs"]

        tot_sa_count = sum(list(s_a.values()))

        rmndr = tot_docs % tot_sa_count
        rmndrchoice = Counter(choices(list(s_a.keys()), weights=list(s_a.values()), k= rmndr))

        for sbj, val in s_a.items():
            count = tot_docs*val/tot_sa_count

            if sbj in list(rmndrchoice.keys()):
                #to_append = [issn, year, sbj, cr_, sh_, crc, int(count+rmndrchoice[sbj])]
                to_append = [issn, year, sbj, sh_, int(count+rmndrchoice[sbj])]
                
            else:
                to_append = [issn, year, sbj, sh_, int(count)]
            newcount_list.append(to_append)

    expladed_df = count1_df.append(pd.DataFrame(newcount_list, columns=count1_df.columns), ignore_index=True)
    return expladed_df


def retr_ready(q_df):
    # Step 1: Create a dataframe that only has the values necessasry for the final pivot table
    #q_main = q1_df[["ISSN", "Year", "Sbj_Area", "CR_Results", "SH_Results", "CR_Count", "Total_Docs"]]
    q_main = q_df[["ISSN", "Year", "Sbj_Area", "SH_Results", "Total_Docs"]]

    #q1_df = q1_df[q1_df.Sbj_Area.map(len) < q1_df.Total_Docs]
    q_main = explade(q_main)

    # Step 2: Create the CONSTANT sample_count pivot table from pivotq1_full

    sa_pivot_full = pd.pivot_table(data=q_main, columns="Year", index="Sbj_Area", values="Total_Docs", aggfunc=sum)

    sa_pivot_meta_only = pd.pivot_table(data=q_main[q_main.SH_Results == True], columns="Year", index="Sbj_Area", values="Total_Docs", aggfunc=sum)

    return q_main, sa_pivot_full, sa_pivot_meta_only

def jrnl_id_creator(n_id, df):
     return [f"{n_id}_{x}" for x in range(len(df))]