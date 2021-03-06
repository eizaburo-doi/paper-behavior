#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quantify the variability of the time to trained over labs.

@author: Guido Meijer
16 Jan 2020
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from os.path import join
import seaborn as sns
from paper_behavior_functions import (query_subjects, seaborn_style, institution_map,
                                      group_colors, figpath)
from ibl_pipeline.analyses import behavior as behavior_analysis
from scipy import stats
import scikit_posthocs as sp

# Settings
fig_path = figpath()

# Query sessions
use_subjects = query_subjects()
ses = (use_subjects * behavior_analysis.SessionTrainingStatus * behavior_analysis.PsychResults
       & 'training_status = "in_training" OR training_status = "untrainable"').proj(
               'subject_nickname', 'n_trials_stim', 'institution_short').fetch(format='frame')
ses = ses.reset_index()
ses['n_trials'] = [sum(i) for i in ses['n_trials_stim']]

# Construct dataframe
training_time = pd.DataFrame(columns=['sessions'], data=ses.groupby('subject_nickname').size())
training_time['trials'] = ses.groupby('subject_nickname').sum()
training_time['lab'] = ses.groupby('subject_nickname')['institution_short'].apply(list).str[0]

# Change lab name into lab number
training_time['lab_number'] = training_time.lab.map(institution_map()[0])
training_time = training_time.sort_values('lab_number')

#  statistics
# Test normality
_, normal = stats.normaltest(training_time['sessions'])
if normal < 0.05:
    kruskal = stats.kruskal(*[group['sessions'].values
                              for name, group in training_time.groupby('lab')])
    if kruskal[1] < 0.05:  # Proceed to posthocs
        posthoc = sp.posthoc_dunn(training_time, val_col='sessions',
                                  group_col='lab_number')
else:
    anova = stats.f_oneway(*[group['sessions'].values
                             for name, group in training_time.groupby('lab')])
    if anova[1] < 0.05:
        posthoc = sp.posthoc_tukey(training_time, val_col='sessions',
                                   group_col='lab_number')


# %% PLOT

# Set figure style and color palette
use_palette = [[0.6, 0.6, 0.6]] * len(np.unique(training_time['lab']))
use_palette = use_palette + [[1, 1, 0.2]]
lab_colors = group_colors()

# Add all mice to dataframe seperately for plotting
training_time_no_all = training_time.copy()
training_time_no_all.loc[training_time_no_all.shape[0] + 1, 'lab_number'] = 'All'
training_time_all = training_time.copy()
training_time_all['lab_number'] = 'All'
training_time_all = training_time.append(training_time_all)

f, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
sns.set_palette(lab_colors)

sns.swarmplot(y='sessions', x='lab_number', hue='lab_number', data=training_time_no_all,
              palette=lab_colors, ax=ax1)
axbox = sns.boxplot(y='sessions', x='lab_number', data=training_time_all,
                    color='white', showfliers=False, ax=ax1)
axbox.artists[-1].set_edgecolor('black')
for j in range(5 * (len(axbox.artists) - 1), 5 * len(axbox.artists)):
    axbox.lines[j].set_color('black')
ax1.set(ylabel='Days to trained', xlabel='')
ax1.get_legend().set_visible(False)
# [tick.set_color(lab_colors[i]) for i, tick in enumerate(ax1.get_xticklabels())]
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=40)

sns.swarmplot(y='trials', x='lab_number', hue='lab_number', data=training_time_no_all,
              palette=lab_colors, ax=ax2)
axbox = sns.boxplot(y='trials', x='lab_number', data=training_time_all,
                    color='white', showfliers=False, ax=ax2)
axbox.artists[-1].set_edgecolor('black')
for j in range(5 * (len(axbox.artists) - 1), 5 * len(axbox.artists)):
    axbox.lines[j].set_color('black')
ax2.set(ylabel='Trials to trained', xlabel='', ylim=[0, 50000])
ax2.get_legend().set_visible(False)
# [tick.set_color(lab_colors[i]) for i, tick in enumerate(ax1.get_xticklabels())]
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=40)

plt.tight_layout(pad=2)
seaborn_style()

plt.savefig(join(fig_path, 'figure2d_time_to_trained.pdf'), dpi=300)
plt.savefig(join(fig_path, 'figure2d_time_to_trained.png'), dpi=300)

# Get stats in text
# Interquartile range per lab
iqtr = training_time.groupby(['lab'])[
    'sessions'].quantile(0.75) - training_time.groupby(['lab'])[
    'sessions'].quantile(0.25)
# Training time as a whole
m_train = training_time['sessions'].mean()
s_train = training_time['sessions'].std()
fastest = training_time['sessions'].max()
slowest = training_time['sessions'].min()
