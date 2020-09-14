# -*- coding: utf-8 -*-
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

# ## Brand prescribing of Lithium ##
# It is recommended that Lithium is prescibed to ensure a person receives the same preparation each time, as lithium comes as different salts which may result in different absoprtion and bioavailability. There has been recent ["supply disruption alert"](https://www.cas.mhra.gov.uk/ViewandAcknowledgment/ViewAlert.aspx?AlertID=103087) which has emphasised the importance of ensuring people are maintained on the same brand. In this notebook we will investigate brand prescribing of lithium.

#import libraries required for analysis
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from ebmdatalab import bq, charts, maps
import os

# ## caution - AMP level prescribing advised
# Brand name prescribing is supported by assertions in the SDA and the BNF `Preparations vary widely in bioavailability; changing the preparation requires the same precautions as initiation of treatment.`
#
# We will use the [NHS dm+d](https://ebmdatalab.net/what-is-the-dmd-the-nhs-dictionary-of-medicines-and-devices/) investigate what Litium products are recommended to be prescribed by brand name in the mandated standard i.e the VMP has a recommendation `caution - AMP level prescribing advised`.

# +
sql = '''
SELECT 
id as snomed_id,
nm as name,
bnf_code,
pres_stat
FROM 
ebmdatalab.dmd.vmp_full
WHERE
bnf_code LIKE '0402030P0%' or 
bnf_code LIKE '0402030K0%'
'''

df_dmd_li_recommendations = bq.cached_read(sql, csv_path=os.path.join('..','data','df_dmd_li_recommendations.zip'))
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
df_dmd_li_recommendations


# -

# All tablets have a brand name prescribing as expected. Interstingly none of the liquids are recommended by dm+d to be prescribed by brand. The NHS dm+d editorial policy says this about it
#
# > However where only one licensed AMP is/has been available and the VMP has an ‘approved’
# generic name, then that product should not be marked with ‘Caution – AMP level prescribing
# advise
#
# There is no rationale as to why this is the case but from cursory look at our [NHS dm+d browser](https://openprescribing.net/dmd/) this does appear to hold true. If the stated aim is to reduce confusion between salts then I thik liquids should be marked as `‘Caution – AMP level prescribing advise` however this is a point for further discussion with dm+d and debate.

df_amp_recommended = pd.read_csv(os.path.join('..','data','df_amp_recommended.zip'))
df_amp_recommended['month'] = df_amp_recommended['month'].astype('datetime64[ns]')
df_amp_recommended.head(3)

df_lithium = df_amp_recommended.loc[df_amp_recommended["bnf_code"].str.startswith(('0402030P0','0402030K0'))]
df_lithium.head(5)

df_lithium.bnf_name.unique()

df_lithium_generic = df_lithium.loc[df_lithium["bnf_code"].str.contains('AA\w{4}$')]
df_lithium_generic.bnf_name.unique()

df_lithium_generic.groupby("month")['total_items'].sum().plot(kind='line', title="Total items where Lithium prescribed generically \n in breach of guidance")
plt.ylim(0, )

# There is quite a reduction in generic prescribing in mid-2012. WE could investigate this further to see if it sheds any light on effective implementation. MOst likely there are product changes, EHR change or substantial work by a meds opt teams.

df_lithium_generic.groupby(['bnf_code', 'bnf_name']).sum().reset_index().sort_values(by = 'total_items', ascending = False).head(25)

df_lithium_generic_ccg = df_lithium_generic.groupby(['month', 'pct']).sum().reset_index()
df_lithium_generic_ccg.head()

# +
df_lithium_ccg = df_lithium.groupby(['month', 'pct']).sum().reset_index()
df_lithium_ccg.head(2)
# -


df_li_measure = pd.merge(df_lithium_generic_ccg, df_lithium_ccg,  how='left', left_on=['month','pct'], right_on = ['month','pct'], suffixes=("_generic_lithium", "_all_lithum_rx"))
df_li_measure["measure_value"] =  100*(df_li_measure.total_items_generic_lithium / df_li_measure.total_items_all_lithum_rx)
df_li_measure.head()

# +
charts.deciles_chart(
    df_li_measure,
    period_column='month',
    column='measure_value',
    title=" CCG variation - Generic lithum prescriptions \n in breach of dm+d brand prescribing recommendations",
    ylabel=" % ",
    show_outer_percentiles=False,
    show_legend=True
) 

#add in example CCG (Devon)
df_subject = df_li_measure.loc[df_li_measure['pct'] == '15N']
plt.plot(df_subject['month'], df_subject['measure_value'], 'r--')

plt.ylim(0, 100)
plt.show()
# -

