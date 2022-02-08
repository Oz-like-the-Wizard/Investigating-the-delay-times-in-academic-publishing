import pandas as pd
import numpy as np
from os import listdir
import re

from statistics import mode, multimode
from random import sample

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
        yeardf["Sbj_Area"] = yeardf.New_Cat.map(lambda x: [cat_sbj_dict[cat.strip()] for cat in x]).map(multimode)

        # 4 - Basic Feature Engineering 
        yeardf["Issn"] = yeardf.Issn.str.split(",")
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



def explade(countdf):
    # No need to extract ISSNs as CrossRef func. accepts lists as argument
    count1_df = countdf[countdf["Sbj_Area"].map(len) == 1]
    count1_df["Sbj_Area"] = count1_df["Sbj_Area"].str[0]
    count2_df = countdf[countdf["Sbj_Area"].map(len) > 1]
    
    newcount_list = []

    for index, row in count2_df.iterrows():
        issn = row["Issn"]
        year = row["Year"] 
        s_a = row["Sbj_Area"]
        count = row["Total_Docs"]

        rmndr = count % len(s_a)
        rmndrchoice = sample(s_a,rmndr)

        for sbj in s_a:
            if sbj in rmndrchoice:
                to_append = [issn, year, sbj, int(count/len(s_a))+1]
            else:
                to_append = [issn, year, sbj, int(count/len(s_a))]
            newcount_list.append(to_append)

    expladed_df = count1_df.append(pd.DataFrame(newcount_list, columns=count1_df.columns), ignore_index=True)
    #pivot_df = pd.pivot_table(data=expladed_df, values="Total_Docs", columns="Year", index="Sbj_Area",aggfunc=sum)
    return expladed_df

def retr_ready(q1_df, target):
    # Step 1: Create a dataframe that only has the values necessasry for the final pivot table
    q_main = q1_df[["Issn","Year", "Sbj_Area", "Total_Docs"]]
    q_main = q_main[q_main.Sbj_Area.map(len) < q_main.Total_Docs]
    q_main = explade(q_main)

    # Step 2: Create the CONSTANT sample_count pivot table from pivotq1_full

    sa_pivot = pd.pivot_table(data=q_main, columns="Year", index="Sbj_Area", values="Total_Docs", aggfunc=sum)
    sa_pivot = sa_pivot.applymap(lambda x: (x*target/(sa_pivot.sum().sum())).round())

    return q_main, sa_pivot
        
