# Undergraduate Thesis (MTH40A/B): Lending Club 
# By: Paul Desroches (500699067) at Ryerson University

# Objective: To predict whether a loan will default,  
# using a Decision Tree involving specified features.

#############################################################
###### Step 0. Import Libraries and Lending Club Data #######
#############################################################

import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Set working directory
dir = 'C:/Users/pdesr/OneDrive/School/Ryerson University/Undergraduate Thesis/Machine Learning in Business/Lending Club'
os.chdir(dir)

# Import data
excel_file = 'lendingclub_v3.xlsx'
raw = pd.read_excel(excel_file)
#raw = raw.sample(frac=1,replace=True) #randomize observations

# View table head
raw.head()

# Customize/clean data
raw = raw[raw.home_ownership.isin(['OWN','RENT','MORTGAGE','OTHER'])]
raw = raw[raw.verification_status.isin(['Verified','Source Verified'])]
raw = raw[raw.dti < 300]
raw.annual_inc = (raw.annual_inc)/1000
raw.loan_amnt = (raw.loan_amnt)/1000
raw.tot_cur_bal = (raw.tot_cur_bal)/1000
raw = raw.replace({'home_ownership': {'OWN':1, 'MORTGAGE':1, 'RENT':0, 'OTHER':0}})
raw = raw.replace({'loan_status': {'Fully Paid':1, 'Current':1, 'In Grace Period':1, 
                                   'Does not meet the credit policy. Status:Fully Paid':1, 
                                   'Does not meet the credit policy. Status:Charged Off':0, 
                                   'Default':0, 'Charged Off':0, 'Late (16-30 days)':0, 'Late (31-120 days)':0}})
raw = raw.replace({'term': {' 36 months':0, ' 60 months':1}})

# Assign specified features to Python variables
#raw = raw.drop(columns=['home_ownership','loan_amnt','verification_status'])
raw = raw[['dti','fico_range_low','annual_inc','term','int_rate','loan_status']]
raw.columns = ['f1','f2','f3','f4','f5','target']
raw = raw.reset_index(drop=True)

# Split into training set and validation set
train = raw[0:round((len(raw))*0.7)]
val = raw[round((len(raw))*0.7):len(raw)]

data = train

##################################################
###### Step 1. Standardized Functions ############
##################################################

# Let this function be defined as the Information Gain (IG) of logical (1 or 0) feature X:

def IGL(frame,X):
    threshold = (min(frame[X])+max(frame[X]))/2
    pos_good = (frame[(frame[X] == 1) & (frame.target == 1)].count()[0])/obs
    pos_default = (frame[(frame[X] == 1) & (frame.target == 0)].count()[0])/obs
    neg_good = (frame[(frame[X] == 0) & (frame.target == 1)].count()[0])/obs
    neg_default = (frame[(frame[X] == 0) & (frame.target == 0)].count()[0])/obs
    prob_pos = pos_good + pos_default
    prob_neg = neg_good + neg_default
    # Compute conditional probabilities needed for information gain
    prob_good_if_pos = pos_good/prob_pos
    prob_default_if_pos = pos_default/prob_pos
    prob_good_if_neg = neg_good/prob_neg
    prob_default_if_neg = neg_default/prob_neg
    # Compute expected entropy given new information
    expected_entropy = -1*(prob_pos*(prob_good_if_pos*np.log(prob_good_if_pos)+prob_default_if_pos*np.log(prob_default_if_pos))+prob_neg*(prob_good_if_neg*np.log(prob_good_if_neg)+prob_default_if_neg*np.log(prob_default_if_neg)))
    # Compute information gain from first feature (home ownership)
    info_gain_X = entropy - expected_entropy
    #print("Information Gain is: ",info_gain_X)
    return [info_gain_X,threshold]

# Let this function be defined as the Information Gain (IG) of numerical feature X:
def IGN(frame,X,a,b,h):
    thrX = np.arange(a,b,h) # set of thresholds 
    exp_entropy_set = [] #storage for entropy values
    for threshold in thrX:
        pos_good = (frame[(frame[X] > threshold) & (frame.target == 1)].count()[0])/obs
        pos_default = (frame[(frame[X] > threshold) & (frame.target == 0)].count()[0])/obs
        neg_good = (frame[(frame[X] <= threshold) & (frame.target == 1)].count()[0])/obs
        neg_default = (frame[(frame[X] <= threshold) & (frame.target == 0)].count()[0])/obs
        prob_pos = pos_good + pos_default
        prob_neg = neg_good + neg_default
        prob_good_if_pos = pos_good/prob_pos
        prob_default_if_pos = pos_default/prob_pos
        prob_good_if_neg = neg_good/prob_neg
        prob_default_if_neg = neg_default/prob_neg
        exp_entropy_set.append(-1*(prob_pos*(prob_good_if_pos*np.log(prob_good_if_pos)+prob_default_if_pos*np.log(prob_default_if_pos))+prob_neg*(prob_good_if_neg*np.log(prob_good_if_neg)+prob_default_if_neg*np.log(prob_default_if_neg))))
    #plt.plot(thrX,exp_entropy_set) #plot the expected entropy over threshold values
    threshX = thrX[exp_entropy_set==np.nanmin(exp_entropy_set)][0]
    #print("Threshold is: ",threshX)
    expected_entropy = np.nanmin(exp_entropy_set)
    #print("Expected Entropy is: ",expected_entropy)
    info_gain_X = entropy - expected_entropy
    #print("Information Gain is: ",info_gain_X)
    return [info_gain_X,threshX]

# Plot expected entropy
# fig = plt.figure()
# plt.plot(thrX,exp_entropy_set)
# #fig.suptitle('test title', fontsize=20)
# plt.xlabel('Loan Amount Threshold', fontsize=12)
# plt.ylabel('Expected Entropy', fontsize=12)
# fig.savefig('dti.png')

# Let this function determine the feature and its threshold at each node:
def node(prev,curr):
        # Entropy given current situation
        obs = data.shape[0] #number of observations
        outcomes = data['target'].value_counts()
        good = (outcomes[1])/obs #good loans percentage
        default = 1 - good #defaulted loans percentage
        entropy = -1*((good*np.log(good))+(default*np.log(default)))
        if prev[-1] in prune:
            print('This decision point does not exist. Node:',curr)
            prune.append(curr)
            tree.append(['NA','NA',good])
        else:
            if obs <= 1000:
                print('Prune this decision point. Probability of a good loan is: ', good)
                prune.append(curr)
                tree.append(['End','NA',good])
            else:
                # IG for each feature (except those in existing nodes)
                info_gain_f1 = [0,0]
                info_gain_f2 = [0,0]
                info_gain_f3 = [0,0]
                info_gain_f4 = [0,0]
                info_gain_f5 = [0,0]
                for i in prev:
                    if 'f1' not in tree[i][0]:
                        info_gain_f1 = IGN(data,'f1',min(data.f1)+0.0001,max(data.f1),0.1) #numerical
                    else:
                        info_gain_f1 = [0,0]
                        break
                for i in prev:
                    if 'f2' not in tree[i][0]:
                        info_gain_f2 = IGN(data,'f2',min(data.f2)+0.0001,max(data.f2),1) #numerical
                    else:
                        info_gain_f2 = [0,0]
                        break
                for i in prev:
                    if 'f3' not in tree[i][0]:
                        info_gain_f3 = IGN(data,'f3',min(data.f3)+0.0001,max(data.f3),1) #numerical
                    else:
                        info_gain_f3 = [0,0]
                        break
                for i in prev:
                    if 'f4' not in tree[i][0]:
                        info_gain_f4 = IGL(data,'f4')
                    else:
                        info_gain_f4 = [0,0]
                        break
                for i in prev:
                    if 'f5' not in tree[i][0]:
                        info_gain_f5 = IGN(data,'f5',min(data.f5)+0.0001,max(data.f5),0.1) #numerical
                    else:
                        info_gain_f5 = [0,0]
                        break
                # We may now determine the root node by taking the highest information gain
                dic = {info_gain_f1[0]:"f1",info_gain_f2[0]:"f2",info_gain_f3[0]:"f3",info_gain_f4[0]:"f4",info_gain_f5[0]:"f5"}
                node = dic.get(max(dic))
                dic2 = {'f1':info_gain_f1[1],'f2':info_gain_f2[1],'f3':info_gain_f3[1],'f4':info_gain_f4[1],'f5':info_gain_f5[1]}
                threshold = dic2.get(node)
                tree.append([node,threshold,good])
                print("The Node is: ",node)
                print("The Threshold is: ",threshold)

##################################################
###### Step 2. Determination of Root Node ########
##################################################

# First, we need to evaluate entropy given the current situation
obs = data.shape[0] #number of observations
outcomes = data['target'].value_counts()
good = (outcomes[1])/obs #good loans percentage
default = 1 - good #defaulted loans percentage
entropy = -1*((good*np.log(good))+(default*np.log(default)))
tree = [] #create storage for tree thresholds
prune = [] #create storage for pruned nodes

# Determine IG for each feature
info_gain_f1 = IGN(data,'f1',min(data.f1)+0.0001,max(data.f1),0.1) #numerical
info_gain_f2 = IGN(data,'f2',min(data.f2)+0.0001,max(data.f2),1) #numerical
info_gain_f3 = IGN(data,'f3',min(data.f3)+0.01,max(data.f3),1) #numerical
info_gain_f4 = IGL(data,'f4')
info_gain_f5 = IGN(data,'f5',min(data.f5)+0.0001,max(data.f5),0.1) #numerical

# We may now determine the root node by taking the highest information gain
dic = {info_gain_f1[0]:"f1",info_gain_f2[0]:"f2",info_gain_f3[0]:"f3",info_gain_f4[0]:"f4",info_gain_f5[0]:"f5"}
root = dic.get(max(dic))
dic2 = {'f1':info_gain_f1[1],'f2':info_gain_f2[1],'f3':info_gain_f3[1],'f4':info_gain_f4[1],'f5':info_gain_f5[1]}
threshold = dic2.get(root)
tree.append([root,threshold,good])
print("The Root Node is: ",root)
print("The Threshold is: ",threshold)

####################################################################
###### Step 3. Determine feature and threshold at each node ########
####################################################################

# Node 1
# Filter dataframe to current situation
prev = [0]
curr = 1
try:
    data = data[data[root] > dic2.get(root)]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 2
# Filter dataframe to current situation
prev = [0]
curr = 2
try:
    data = data[data[root] <= dic2.get(root)]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 3
prev = [0,1]
curr = 3
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] > tree[1][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 4
prev = [0,1]
curr = 4
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] <= tree[1][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 5
prev = [0,2]
curr = 5
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] > tree[2][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 6
prev = [0,2]
curr = 6
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] <= tree[2][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 7
prev = [0,1,3]
curr = 7
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] > tree[1][1]]
    data = data[data[tree[3][0]] > tree[3][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 8
prev = [0,1,3]
curr = 8
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] > tree[1][1]]
    data = data[data[tree[3][0]] <= tree[3][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 9
prev = [0,1,4] 
curr = 9
# Update dataframe
try:
    data = data[(data[root] > dic2.get(root))]
    data = data[(data[tree[1][0]] <= tree[1][1])]
    data = data[(data[tree[4][0]] > tree[4][1])]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 10
prev = [0,1,4] 
curr = 10
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] <= tree[1][1]]
    data = data[data[tree[4][0]] <= tree[4][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 11
prev = [0,2,5]
curr = 11
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] > tree[2][1]]
    data = data[data[tree[5][0]] > tree[5][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 12
prev = [0,2,5]
curr = 12
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] > tree[2][1]]
    data = data[data[tree[5][0]] <= tree[5][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 13
prev = [0,2,6]
curr = 13
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] <= tree[2][1]]
    data = data[data[tree[6][0]] > tree[6][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 14
prev = [0,2,6]
curr = 14
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] <= tree[2][1]]
    data = data[data[tree[6][0]] <= tree[6][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 15
prev = [0,1,3,7]
curr = 15
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] > tree[1][1]]
    data = data[data[tree[3][0]] > tree[3][1]]
    data = data[data[tree[7][0]] > tree[7][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 16
prev = [0,1,3,7]
curr = 16
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] > tree[1][1]]
    data = data[data[tree[3][0]] > tree[3][1]]
    data = data[data[tree[7][0]] <= tree[7][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 17
prev = [0,1,3,8]
curr = 17
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] > tree[1][1]]
    data = data[data[tree[3][0]] <= tree[3][1]]
    data = data[data[tree[8][0]] > tree[8][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 18
prev = [0,1,3,8]
curr = 18
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] > tree[1][1]]
    data = data[data[tree[3][0]] <= tree[3][1]]
    data = data[data[tree[8][0]] <= tree[8][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 19
prev = [0,1,4,9]
curr = 19
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] <= tree[1][1]]
    data = data[data[tree[4][0]] > tree[4][1]]
    data = data[data[tree[9][0]] > tree[9][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 20
prev = [0,1,4,9]
curr = 20
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] <= tree[1][1]]
    data = data[data[tree[4][0]] > tree[4][1]]
    data = data[data[tree[9][0]] <= tree[9][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 21
prev = [0,1,4,10]
curr = 21
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] <= tree[1][1]]
    data = data[data[tree[4][0]] <= tree[4][1]]
    data = data[data[tree[10][0]] > tree[10][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 22
prev = [0,1,4,10]
curr = 22
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] <= tree[1][1]]
    data = data[data[tree[4][0]] <= tree[4][1]]
    data = data[data[tree[10][0]] <= tree[10][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 23
prev = [0,2,5,11]
curr = 23
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] > tree[2][1]]
    data = data[data[tree[5][0]] > tree[5][1]]
    data = data[data[tree[11][0]] > tree[11][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 24
prev = [0,2,5,11]
curr = 24
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] > tree[2][1]]
    data = data[data[tree[5][0]] > tree[5][1]]
    data = data[data[tree[11][0]] <= tree[11][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 25
prev = [0,2,5,12]
curr = 25
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] > tree[2][1]]
    data = data[data[tree[5][0]] <= tree[5][1]]
    data = data[data[tree[12][0]] > tree[12][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 26
prev = [0,2,5,12]
curr = 26
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] > tree[2][1]]
    data = data[data[tree[5][0]] <= tree[5][1]]
    data = data[data[tree[12][0]] <= tree[12][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 27
prev = [0,2,6,13]
curr = 27
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] <= tree[2][1]]
    data = data[data[tree[6][0]] > tree[6][1]]
    data = data[data[tree[13][0]] > tree[13][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 28
prev = [0,2,6,13]
curr = 28
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] <= tree[2][1]]
    data = data[data[tree[6][0]] > tree[6][1]]
    data = data[data[tree[13][0]] <= tree[13][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 29
prev = [0,2,6,14]
curr = 29
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] <= tree[2][1]]
    data = data[data[tree[6][0]] <= tree[6][1]]
    data = data[data[tree[14][0]] > tree[14][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 30
prev = [0,2,6,14]
curr = 30
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] <= tree[2][1]]
    data = data[data[tree[6][0]] <= tree[6][1]]
    data = data[data[tree[14][0]] <= tree[14][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 31
prev = [0,1,3,7,15]
curr = 31
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] > tree[1][1]]
    data = data[data[tree[3][0]] > tree[3][1]]
    data = data[data[tree[7][0]] > tree[7][1]]
    data = data[data[tree[15][0]] > tree[15][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 32
prev = [0,1,3,7,15]
curr = 32
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] > tree[1][1]]
    data = data[data[tree[3][0]] > tree[3][1]]
    data = data[data[tree[7][0]] > tree[7][1]]
    data = data[data[tree[15][0]] <= tree[15][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 33
prev = [0,1,3,7,16]
curr = 33
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] > tree[1][1]]
    data = data[data[tree[3][0]] > tree[3][1]]
    data = data[data[tree[7][0]] <= tree[7][1]]
    data = data[data[tree[16][0]] > tree[16][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 34
prev = [0,1,3,7,16]
curr = 34
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] > tree[1][1]]
    data = data[data[tree[3][0]] > tree[3][1]]
    data = data[data[tree[7][0]] <= tree[7][1]]
    data = data[data[tree[16][0]] <= tree[16][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 35
prev = [0,1,3,8,17]
curr = 35
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] > tree[1][1]]
    data = data[data[tree[3][0]] <= tree[3][1]]
    data = data[data[tree[8][0]] > tree[8][1]]
    data = data[data[tree[17][0]] > tree[17][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 36
prev = [0,1,3,8,17]
curr = 36
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] > tree[1][1]]
    data = data[data[tree[3][0]] <= tree[3][1]]
    data = data[data[tree[8][0]] > tree[8][1]]
    data = data[data[tree[17][0]] <= tree[17][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 37
prev = [0,1,3,8,18]
curr = 37
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] > tree[1][1]]
    data = data[data[tree[3][0]] <= tree[3][1]]
    data = data[data[tree[8][0]] <= tree[8][1]]
    data = data[data[tree[18][0]] > tree[18][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 38
prev = [0,1,3,8,18]
curr = 38
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] > tree[1][1]]
    data = data[data[tree[3][0]] <= tree[3][1]]
    data = data[data[tree[8][0]] <= tree[8][1]]
    data = data[data[tree[18][0]] <= tree[18][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 39
prev = [0,1,4,9,19]
curr = 39
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] <= tree[1][1]]
    data = data[data[tree[4][0]] > tree[4][1]]
    data = data[data[tree[9][0]] > tree[9][1]]
    data = data[data[tree[19][0]] > tree[19][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 40
prev = [0,1,4,9,19]
curr = 40
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] <= tree[1][1]]
    data = data[data[tree[4][0]] > tree[4][1]]
    data = data[data[tree[9][0]] > tree[9][1]]
    data = data[data[tree[19][0]] <= tree[19][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 41
prev = [0,1,4,9,20]
curr = 41
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] <= tree[1][1]]
    data = data[data[tree[4][0]] > tree[4][1]]
    data = data[data[tree[9][0]] <= tree[9][1]]
    data = data[data[tree[20][0]] > tree[20][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 42
prev = [0,1,4,9,20]
curr = 42
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] <= tree[1][1]]
    data = data[data[tree[4][0]] > tree[4][1]]
    data = data[data[tree[9][0]] <= tree[9][1]]
    data = data[data[tree[20][0]] <= tree[20][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 43
prev = [0,1,4,10,21]
curr = 43
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] <= tree[1][1]]
    data = data[data[tree[4][0]] <= tree[4][1]]
    data = data[data[tree[10][0]] > tree[10][1]]
    data = data[data[tree[21][0]] > tree[21][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 44
prev = [0,1,4,10,21]
curr = 44
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] <= tree[1][1]]
    data = data[data[tree[4][0]] <= tree[4][1]]
    data = data[data[tree[10][0]] > tree[10][1]]
    data = data[data[tree[21][0]] <= tree[21][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 45
prev = [0,1,4,10,22]
curr = 45
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] <= tree[1][1]]
    data = data[data[tree[4][0]] <= tree[4][1]]
    data = data[data[tree[10][0]] <= tree[10][1]]
    data = data[data[tree[22][0]] > tree[22][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 46
prev = [0,1,4,10,22]
curr = 46
try:
    data = data[data[root] > dic2.get(root)]
    data = data[data[tree[1][0]] <= tree[1][1]]
    data = data[data[tree[4][0]] <= tree[4][1]]
    data = data[data[tree[10][0]] <= tree[10][1]]
    data = data[data[tree[22][0]] <= tree[22][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 47
prev = [0,2,5,11,23]
curr = 47
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] > tree[2][1]]
    data = data[data[tree[5][0]] > tree[5][1]]
    data = data[data[tree[11][0]] > tree[11][1]]
    data = data[data[tree[23][0]] > tree[23][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 48
prev = [0,2,5,11,23]
curr = 48
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] > tree[2][1]]
    data = data[data[tree[5][0]] > tree[5][1]]
    data = data[data[tree[11][0]] > tree[11][1]]
    data = data[data[tree[23][0]] <= tree[23][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 49
prev = [0,2,5,11,24]
curr = 49
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] > tree[2][1]]
    data = data[data[tree[5][0]] > tree[5][1]]
    data = data[data[tree[11][0]] <= tree[11][1]]
    data = data[data[tree[24][0]] > tree[24][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 50
prev = [0,2,5,11,24]
curr = 50
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] > tree[2][1]]
    data = data[data[tree[5][0]] > tree[5][1]]
    data = data[data[tree[11][0]] <= tree[11][1]]
    data = data[data[tree[24][0]] <= tree[24][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 51
prev = [0,2,5,12,25]
curr = 51
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] > tree[2][1]]
    data = data[data[tree[5][0]] <= tree[5][1]]
    data = data[data[tree[12][0]] > tree[12][1]]
    data = data[data[tree[25][0]] > tree[25][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 52
prev = [0,2,5,12,25]
curr = 52
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] > tree[2][1]]
    data = data[data[tree[5][0]] <= tree[5][1]]
    data = data[data[tree[12][0]] > tree[12][1]]
    data = data[data[tree[25][0]] <= tree[25][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 53
prev = [0,2,5,12,26]
curr = 53
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] > tree[2][1]]
    data = data[data[tree[5][0]] <= tree[5][1]]
    data = data[data[tree[12][0]] <= tree[12][1]]
    data = data[data[tree[26][0]] > tree[26][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 54
prev = [0,2,5,12,26]
curr = 54
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] > tree[2][1]]
    data = data[data[tree[5][0]] <= tree[5][1]]
    data = data[data[tree[12][0]] <= tree[12][1]]
    data = data[data[tree[26][0]] <= tree[26][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 55
prev = [0,2,6,13,27]
curr = 55
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] <= tree[2][1]]
    data = data[data[tree[6][0]] > tree[6][1]]
    data = data[data[tree[13][0]] > tree[13][1]]
    data = data[data[tree[27][0]] > tree[27][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 56
prev = [0,2,6,13,27]
curr = 56
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] <= tree[2][1]]
    data = data[data[tree[6][0]] > tree[6][1]]
    data = data[data[tree[13][0]] > tree[13][1]]
    data = data[data[tree[27][0]] <= tree[27][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 57
prev = [0,2,6,13,28]
curr = 57
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] <= tree[2][1]]
    data = data[data[tree[6][0]] > tree[6][1]]
    data = data[data[tree[13][0]] <= tree[13][1]]
    data = data[data[tree[28][0]] > tree[28][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 58
prev = [0,2,6,13,28]
curr = 58
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] <= tree[2][1]]
    data = data[data[tree[6][0]] > tree[6][1]]
    data = data[data[tree[13][0]] <= tree[13][1]]
    data = data[data[tree[28][0]] <= tree[28][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 59
prev = [0,2,6,14,29]
curr = 59
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] <= tree[2][1]]
    data = data[data[tree[6][0]] <= tree[6][1]]
    data = data[data[tree[14][0]] > tree[14][1]]
    data = data[data[tree[29][0]] > tree[29][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 60
prev = [0,2,6,14,29]
curr = 60
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] <= tree[2][1]]
    data = data[data[tree[6][0]] <= tree[6][1]]
    data = data[data[tree[14][0]] > tree[14][1]]
    data = data[data[tree[29][0]] <= tree[29][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 61
prev = [0,2,6,14,30]
curr = 61
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] <= tree[2][1]]
    data = data[data[tree[6][0]] <= tree[6][1]]
    data = data[data[tree[14][0]] <= tree[14][1]]
    data = data[data[tree[30][0]] > tree[30][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train

# Node 62
prev = [0,2,6,14,30]
curr = 62
try:
    data = data[data[root] <= dic2.get(root)]
    data = data[data[tree[2][0]] <= tree[2][1]]
    data = data[data[tree[6][0]] <= tree[6][1]]
    data = data[data[tree[14][0]] <= tree[14][1]]
    data = data[data[tree[30][0]] <= tree[30][1]]
except:
    pass
# Run node function
node(prev,curr)
data = train


##############################
###### Step 4. Results #######
##############################

print("Classification Tree is ready. Please use Results script to observe accuracy.")















