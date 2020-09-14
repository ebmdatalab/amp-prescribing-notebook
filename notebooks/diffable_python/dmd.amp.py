# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: all
#     notebook_metadata_filter: all,-language_info
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.3.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# ## AMP prescribing as recommended by the [NHS Dictionary of medicines and devices](https://ebmdatalab.net/what-is-the-dmd-the-nhs-dictionary-of-medicines-and-devices/)
#
# **THIS IS A WORK IN PROGRESS**
#
# The UK has over the last few decades encouraged generic prescribing for reasons of cost containment and safety. However there are important exceptions where generic prescribing is not ideal e.g. narrow therapeutic index where even slight variations between brands could cause adverse clinical responses. On OpenPrescribing we have some measures of generic prescribing where brand prescribing is recommended 
#
# - [ciclosporin and tacrolimus](https://openprescribing.net/measure/ciclosporin/)
# - [diltiazem >60mg](https://openprescribing.net/measure/diltiazem/)
#
# We have found that [12.3% of prescriptions for diltiazem, tacrolimus and ciclosporin breach prescribing guidance](https://openprescribing.net/measure/diltiazem/) on brand prescribing in a paper accted in JMIR. 
#
# Various organisations make recommendations about brand prescribing in the NHS including the [NHS dictionary of medicines and devices (dm+d)](https://ebmdatalab.net/what-is-the-dmd-the-nhs-dictionary-of-medicines-and-devices/) which is the mandated drug dictionary for electronic systems in the NHS. In the field `prescribing status` the dm+d can assign a value `caution - AMP level prescribing advised` which means you should prescribe by brand. This is assigned to 229 VMPs.
#
# In this notebook we will set out to investigate brand prescribing across all products.

#import libraries required for analysis
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from ebmdatalab import bq, charts, maps
import os

# +
sql = '''
SELECT
  month,
  pct,
  bnf_name,
  bnf_code,
  SUM(items) AS total_items
FROM
hscic.normalised_prescribing_standard AS rx
INNER JOIN
hscic.practices AS prac
ON
rx.practice = prac.code 
JOIN
  hscic.ccgs AS ccgs
ON
rx.pct=ccgs.code
WHERE
  prac.setting = 4 
  AND  
  ccgs.org_type='CCG'
  AND
  bnf_code IN (
  SELECT
    DISTINCT(bnf_code)
  FROM
    ebmdatalab.brian.amp_recommended
     )
GROUP BY
rx.month,
rx.pct,
rx.bnf_code,
rx.bnf_name
ORDER BY
month
'''

df_amp_recommended = bq.cached_read(sql, csv_path=os.path.join('..','data','df_amp_recommended.zip'))
#df_amp_recommended = bq.cached_read(sql, csv_path=os.path.join('..','data','df_amp_recommended.csv'))
df_amp_recommended['month'] = df_amp_recommended['month'].astype('datetime64[ns]')
df_amp_recommended.head(3)
# -

#lets graph to see the total number of items over time
df_amp_recommended.groupby("month")['total_items'].sum().plot(kind='line', title="Total items where AMP recommended by NHS dm+d")
plt.ylim(0, )

#create dataframe with only generically prescribed items
df_generic = df_amp_recommended.loc[df_amp_recommended["bnf_code"].str.contains('AA\w{4}$')]
df_generic.head()

#output unique BNF codes to inspect for accuracy
df_generic.bnf_code.unique()

#plot breaches
df_generic.groupby("month")['total_items'].sum().plot(kind='line', title="Total items where AMP recommended by NHS dm+d but prescribed generically \n in breach of guidance")
plt.ylim(0, )

#inspect top 25
df_generic.groupby(['bnf_code', 'bnf_name']).sum().reset_index().sort_values(by = 'total_items', ascending = False).head(25)

df_generic_ccg = df_generic.groupby(['month', 'pct']).sum().reset_index()
df_generic_ccg .head(3)

df_amp_recommended_ccg = df_amp_recommended.groupby(['month', 'pct']).sum().reset_index()
df_amp_recommended_ccg.head(3)

df_measure = pd.merge(df_generic_ccg, df_amp_recommended_ccg,  how='left', left_on=['month','pct'], right_on = ['month','pct'], suffixes=("_generic_rx", "_all_rx_rec_amp"))
df_measure["measure_value"] = 100*(df_measure.total_items_generic_rx / df_measure.total_items_all_rx_rec_amp).fillna(0)
df_measure.head()


# +
charts.deciles_chart(
    df_measure,
    period_column='month',
    column='measure_value',
    title=" CCG variation - Generic prescriptions \n in breach of dm+d brand prescribing recommendations",
    ylabel=" % ",
    show_outer_percentiles=True,
    show_legend=True
) 

#add in example CCG (Devon)
df_subject = df_measure.loc[df_measure['pct'] == '15N']
plt.plot(df_subject['month'], df_subject['measure_value'], 'r--')

plt.ylim(0, 100)
plt.show()
# -

#create choropeth map 
plt.figure(figsize=(12, 7))
last_year_df_measure = df_measure.loc[(df_measure['month'] >= '2020-04-01') & (df_measure['month'] <= '2020-12-01')]
plt = maps.ccg_map(last_year_df_measure, title="Generic prescription in breach of brand prescribing recommendations  \n CCG ", column='measure_value', separate_london=False)
plt.show()


