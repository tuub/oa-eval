# -*- coding: utf-8 -*-
#!/usr/bin/env python2.7
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# Label bar plots automatically
def autolabel(rects, ax):
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/1.8, 1.01*height,
                '%d' % int(height),
                ha='center', va='bottom')


# Create bar plot for OA publication share
def threebar(years, pubAll, pubOA, pubOACorr, pubHybrid):
    # Set values and layout
    nGroups = len(years)
    fig, ax = plt.subplots()
    index = np.arange(nGroups)
    barWidth = 0.21
    rects1 = ax.bar(index, pubAll, barWidth, color='g',
                    label='All Publications', edgecolor = "none")
    rects2 = ax.bar(index + barWidth, pubOA, barWidth,
           color='y', label='OA Publications', edgecolor = "none")
    rects4 = ax.bar(index + 2 * barWidth, pubHybrid, barWidth,
           color='r', label='Hybrid', edgecolor = "none")
    rects3 = ax.bar(index + 3 * barWidth, pubOACorr, barWidth,
           color='c', label='Gold + Corr. Auth', edgecolor = "none")
    
    # Set up labels and axes
    plt.grid()
    plt.xlabel('Year')
    plt.ylabel('# of Publications')
    plt.title('OA Publication Share')
    labels = [str(x) for x in years]
    plt.xticks(index + (2 * barWidth), tuple(labels))
    plt.legend()
    plt.tight_layout()
    plt.ylim([0, max(pubAll) * 1.1])
    plt.xlim(xmin = index[0] - barWidth)
    plt.xlim(xmax = max(index) + 1.25) 
    matplotlib.rcParams.update({'font.size': 8})
    autolabel(rects1, ax)    
    autolabel(rects2, ax)
    autolabel(rects4, ax)
    autolabel(rects3, ax)
    matplotlib.rcParams.update({'font.size': 10})
    
    # Create output
    plt.savefig('Figure_OANumbers.png', dpi=1000)
    plt.show()


# Create line plot for percentage of OA articles
def lineplot1(years, percOA, percOACorr):
    # Set up basic layout
    nGroups = len(years[0:-1]) - 1
    index = np.arange(nGroups)
    plt.figure(1)
    
    # Create upper figure
    plt.subplot(211)
    plt.plot(index, percOA[0:-2], 'r--',
             index, percOA[0:-2], 'ro')
    plt.xlabel('Year')
    plt.ylabel('Percentage [%]')
    plt.title('Percentage of OA Articles')
    plt.grid()
    labels = [str(x) for x in years[0:-1]]
    plt.xticks(index, tuple(labels))
    plt.xlim([index[0] - 0.2, max(index) + 0.2])
    plt.ylim([min(percOA[0:-2]) - 0.5, max(percOA[0:-2]) + 0.5])
    plt.tight_layout()
    
    # Create lower figure
    plt.subplot(212)
    plt.plot(index, percOACorr[0:-2], 'cs',
             index, percOACorr[0:-2], 'c-.')
    plt.xlabel('Year')
    plt.ylabel('Percentage [%]')
    plt.title('Percentage of OA Articles with First / Corresponding Author')
    plt.grid()
    plt.tight_layout()
    labels = [str(x) for x in years[0:-1]]
    plt.xticks(index, tuple(labels))
    plt.xlim([index[0] - 0.2, max(index) + 0.2])
    plt.ylim([min(percOACorr[0:-2]) - 0.5, max(percOACorr[0:-2]) + 0.5])
    
    # Create output
    plt.savefig('Figure_OAShare.png', dpi=1000)
    plt.show()


# Create bar plot of increase in publication rates
def otherbar(years, pubAll, pubOA, pubOACorr):
    # Define layout and calculate values
    nGroups = len(years[0:-1]) - 1
    fig, ax = plt.subplots()
    index = np.arange(nGroups)
    barWidth = 0.35
    difArt = []
    labels = []
    for i in range(0, nGroups):
        difArt.append(pubAll[i + 1] - pubAll[i])
        labels.append(str(years[i]) + '-' + str(years[i+1]))
    difOAArt = []
    for i in range(0, nGroups):
        difOAArt.append(pubOA[i + 1] - pubOA[i])
    rects1 = ax.bar(index, difArt, barWidth, color='g',
                    label='# of Articles Increase', edgecolor = "none")
    rects2 = ax.bar(index + barWidth, difOAArt, barWidth,
           color='r', label='# of OA Articles Increase', edgecolor = "none")
    
    # Set up labels and axes
    plt.xlabel('Years')
    plt.ylabel('# of Publications')
    plt.title('Increase in Publication Rates')
    plt.grid()
    if min(difArt) < 0 or min(difOAArt) < 0:
        ylimit = min([min(difArt), min(difOAArt)]) * 1.5
    else:
        ylimit = 0
    plt.ylim([ylimit, max(difArt) * 1.5])
    plt.xlim(xmin = index[0] - barWidth)
    plt.xlim(xmax = max(index) + 1.25) 
    plt.xticks(index + barWidth, tuple(labels))
    autolabel(rects1, ax)
    autolabel(rects2, ax)
    plt.tight_layout()
    plt.legend()
    
    # Create output
    plt.savefig('Figure_OAIncrease.png', dpi=1000)
    plt.show()
    