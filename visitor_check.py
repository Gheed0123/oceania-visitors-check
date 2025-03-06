# -*- coding: utf-8 -*-
"""
checks a list of supplied names with the friends.json data using fuzzy matching
fuzzy matching meaning you do not have to type in the names correctly :)
Now you can view your visitors sorted by reputation 
I use this to do friendrun faster
"""

import json
import pandas as pd
import re
import fuzzywuzzy as fw
from fuzzywuzzy import process
import numpy as np
import os


def repl(m):
    innernum = ''.join(list(m.group(2)))
    innernum = innernum.replace('0', 'o')
    return (m.group(1)+innernum+m.group(3))


def merge_db(friendlist, p=None):
    if (p):
        if (os.path.exists(p)):
            df = pd.read_csv(p)
        sz = len(df)

        df = df.merge(friendlist, how='outer', on='fname')
        df['rep'] = df[['rep_x', 'rep_y']].max(axis=1)
        df = df[['fname', 'rep']]

        if (len(df) > sz):
            df.to_csv(p, index=False)

        return df
    return friendlist


def regex_fixes_names(col):
    col = col.str.split(' ', expand=True)[0].str.lower()
    col = col.str.replace('(\D)\d+$', '\g<1>', regex=True)
    col = col.str.replace('(\D)([0]+)(\D)', repl, regex=True)
    col = col.str.replace('^0([^0-9])', 'o\g<1>', regex=True)
    col = col.str.replace('_', '')
    col = col.str.replace(';', 'l')
    col = col.str.replace('[', 'p')
    return col


# %%settings
cutoffscore = 85  # lower = worse matches, higher = you need to type better
cutofflen = 4  # using different matching on strings len <= cutoff due to low accuracy
cutoffdate = 7  # after X days friends not visited -> to unfriend :(
day_str = '----'  # string that defines the new day

cwd = os.getcwd()
database_path = cwd + '/all_friends.csv'
input_names_path = cwd + '/visitors.txt'
pd.set_option('display.max_rows', None)

print('starting friendsorter!')

# %%load data
with open(cwd+"/friends.json") as f:
    json_friends = json.load(f)

friends = pd.DataFrame(
    [[friend['name'], int(friend['reputation'])] for friend in json_friends])
friends.columns = ['fname', 'rep']

allfriends = merge_db(friends, p=database_path)

with open(input_names_path) as f:
    visitors = pd.read_fwf(f, header=None)[0]

# %%some fixes
friends['frname'] = regex_fixes_names(friends.fname)
friends = pd.concat([friends, pd.DataFrame(
    np.array([(day_str, 0, day_str)]), columns=['fname', 'rep', 'frname'])])
allfriends['frname'] = regex_fixes_names(allfriends.fname)

# %%
# only consider visitors in the past X days
day = visitors.isin([day_str]).cumsum()
visitors = visitors[day > day.max()-cutoffdate].reset_index(drop=True)
day = visitors.isin([day_str]).cumsum()

visitors = visitors[visitors != day_str]
day = day[visitors.index].reset_index(drop=True)
visitors = visitors.reset_index(drop=True)

# some common spelling fixes
visitors = regex_fixes_names(visitors)

# %%fuzzy matching
e1 = [[name]+list(process.extractOne(name, friends['frname'].values))
      for name in visitors]
e2 = [[name]+list(process.extractOne(name, friends['frname'].values,
                  scorer=fw.fuzz.token_set_ratio)) for name in visitors]

e1 = [e2[i] if ((len(e[0]) <= cutofflen) | (len(e[1]) < cutofflen))
      else e for i, e in enumerate(e1)]

# %%printing non-matches to check manually, to add as friends
notmatched = [e for e in e1 if e[2] <= cutoffscore]
print('check this, they have had bad match in past week, might not be friends')
print(['input', 'matched name', 'score'])
for v in (notmatched):
    print(v)

# notmatched = [e for i, e in enumerate(
#     e1) if e[2] <= cutoffscore and day[i] >= 6]
# print('check this, they have bad match last 2 days, might not be friends')
# print(['input', 'matched name', 'score'])
# for v in notmatched:
#     print(v)

# %%merge stuff
df_visitors = pd.DataFrame(e1)
df_visitors.columns = ['input', 'frname', 'score']
df_visitors = df_visitors.merge(friends, how='inner')

visitors_weekly = df_visitors.copy()

# last ~2 days to_visit
df_visitors = df_visitors.iloc[day[day ==
                                   6].index[0]-5:].reset_index(drop=True)
df_visitors = df_visitors.drop_duplicates(
    subset=['fname', 'rep']).reset_index(drop=True)
df_visitors = df_visitors.sort_values(by=['rep', 'fname', 'input'], axis=0)
df_visitors = df_visitors[['fname', 'rep', 'input']]

visitors_2days = df_visitors.copy()
visits_weekly = (visitors_weekly.fname.value_counts())
visitors_2days = visitors_2days.merge(
    visits_weekly, left_on='fname', right_on='fname', how='left').sort_values('rep', ascending=False)

# who did not visit in last X days -> unfriend
to_unfriend = friends.copy()
to_unfriend = to_unfriend['fname']
to_unfriend = visitors_weekly[['fname', 'rep']].merge(to_unfriend, how='outer')
to_unfriend = to_unfriend[to_unfriend.rep.isna()
                          ]['fname'].reset_index(drop=True)
to_unfriend = to_unfriend.sort_values().drop_duplicates(keep=False)

# %%check for names in input that were not matched properly with current friends but might match with full database
notmatched = [nm[0] for nm in notmatched]

e1 = [[name]+list(process.extractOne(name, allfriends['frname'].values))
      for name in notmatched]
e2 = [[name]+list(process.extractOne(name, allfriends['frname'].values,
                  scorer=fw.fuzz.token_set_ratio)) for name in notmatched]
e1 = [e2[i] if ((len(e[0]) <= cutofflen) | (len(e[1]) < cutofflen))
      else e for i, e in enumerate(e1)]

unfriended_friends = [[e[0], e[1]] for e in e1 if e[2] > cutoffscore]
unfriended_friends = pd.DataFrame(unfriended_friends)
if (not unfriended_friends.empty):
    unfriended_friends.columns = ['input', 'frname']
unfriended_friends_set = unfriended_friends.drop_duplicates(subset='frname')['frname']
unfriended_friends_set.name = 'add these friends again!'

# %%print and save stuff
print('-'*50)
print('check this, they might not have visited in '+str(cutoffdate)+' days')
print(to_unfriend.to_markdown(index=False))

print('-'*50)
print(f'Names of visitors of last 2 days & number of visits in the last {cutoffdate} days:')
print(visitors_2days.to_markdown(index=False))

print('-'*50)
if (not unfriended_friends.empty):
    print(unfriended_friends_set.to_markdown(index=False))
else:
    print('all friends already added, no missing found in db')

print('-'*50)
print('Amount of visitors in last 2 days:')
print(str(len(visitors_2days))+'/'+str(len(friends.fname)))

print('-'*50)
df_visitors.to_csv(cwd+"/df_visitors.txt", index=False, header=None, sep='\t')
