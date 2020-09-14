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


