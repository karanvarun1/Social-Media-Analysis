# -*- coding: utf-8 -*-
"""
Created on Sun Nov 20 10:29:32 2016


"""
print ()

import networkx
from operator import itemgetter
import operator
import matplotlib.pyplot

# Lets read the data from the amazon-books.txt;
# populate amazonProducts nested dicitonary;
# key = ASIN; value = MetaData associated with ASIN
fhr = open('./amazon-books.txt', 'r', encoding='utf-8', errors='ignore')
amazonBooks = {}
fhr.readline()
for line in fhr:
    cell = line.split('\t')
    MetaData = {}
    MetaData['Id'] = cell[0].strip() 
    ASIN = cell[1].strip()
    MetaData['Title'] = cell[2].strip()
    MetaData['Categories'] = cell[3].strip()
    MetaData['Group'] = cell[4].strip()
    MetaData['SalesRank'] = int(cell[5].strip())
    MetaData['TotalReviews'] = int(cell[6].strip())
    MetaData['AvgRating'] = float(cell[7].strip())
    MetaData['DegreeCentrality'] = int(cell[8].strip())
    MetaData['ClusteringCoeff'] = float(cell[9].strip())
    amazonBooks[ASIN] = MetaData
fhr.close()

# Lets read the data from amazon-books-copurchase.adjlist;
# assign it to copurchaseGraph weighted Graph;
# node = ASIN, edge= copurchase, edge weight = category similarity
fhr=open("amazon-books-copurchase.edgelist", 'rb')
copurchaseGraph=networkx.read_weighted_edgelist(fhr)
fhr.close()

# Now let's assume a person is considering buying the following book;
# what else can we recommend to them based on copurchase behavior 
# we've seen from other users?
print ("Looking for Recommendations for Customer Purchasing this Book:")
print ("--------------------------------------------------------------")
purchasedAsin = '0805047905'

# Let's first get some metadata associated with this book
print ("ASIN = ", purchasedAsin) 
print ("Title = ", amazonBooks[purchasedAsin]['Title'])
print ("SalesRank = ", amazonBooks[purchasedAsin]['SalesRank'])
print ("TotalReviews = ", amazonBooks[purchasedAsin]['TotalReviews'])
print ("AvgRating = ", amazonBooks[purchasedAsin]['AvgRating'])
print ("DegreeCentrality = ", amazonBooks[purchasedAsin]['DegreeCentrality'])
print ("ClusteringCoeff = ", amazonBooks[purchasedAsin]['ClusteringCoeff'])
    
# Now let's look at the ego network associated with purchasedAsin in the
# copurchaseGraph - which is esentially comprised of all the books 
# that have been copurchased with this book in the past
#     Get the depth-1 ego network of purchasedAsin from copurchaseGraph,
#     and assign the resulting graph to purchasedAsinEgoGraph.
purchasedAsinEgoGraph = networkx.ego_graph(copurchaseGraph, purchasedAsin, radius = 1)

# The edge weights in the copurchaseGraph is a measure of
# the similarity between the books connected by the edge. So we can use the 
# island method to only retain those books that are highly simialr to the 
# purchasedAsin
#     Use the island method on purchasedAsinEgoGraph to only retain edges with 
#     threshold >= 0.5, and assign resulting graph to purchasedAsinEgoTrimGraph
threshold = 0.5
purchasedAsinEgoTrimGraph = networkx.Graph()
for f, t, e in purchasedAsinEgoGraph.edges(data = True):
    if e['weight'] >= threshold:
        purchasedAsinEgoTrimGraph.add_edge(f,t,e)

# Given the purchasedAsinEgoTrimGraph we constructed above, 
# we can get at the list of nodes connected to the purchasedAsin by a single 
# hop (called the neighbors of the purchasedAsin) 
#     Following is a list of neighbors of the purchasedAsin in the 
#     purchasedAsinEgoTrimGraph assigned to purchasedAsinNeighbors
purchasedAsinNeighbors = []
for f, t, e in purchasedAsinEgoTrimGraph.edges(data = True):
    if f == purchasedAsin:  
        purchasedAsinNeighbors.append(t)

# Next, let's pick the Top Five book recommendations from among the 
# purchasedAsinNeighbors based on one or more of the following data of the 
# neighboring nodes: SalesRank, AvgRating, TotalReviews, DegreeCentrality, 
# and ClusteringCoeff
#     Note that, given an asin, we can get at the metadata associated with  
#     it using amazonBooks.
#     Now, lets come up with a composite measure to make Top Five book 
#     recommendations based on one or more of the following metrics associated 
#     with nodes in purchasedAsinNeighbors: SalesRank, AvgRating, 
#     TotalReviews, DegreeCentrality, and ClusteringCoeff 
recommendedD = {}
scoresD = {}
scores = []
# n is a parameter of our algorithm
n=4
# we'll fetch only that records that meet a specific criteria as per our n
for asin in amazonBooks:
    if (asin in purchasedAsinNeighbors):  
        if(amazonBooks[asin]['DegreeCentrality']>min(2*n,amazonBooks[purchasedAsin]['DegreeCentrality']/n)):
            if amazonBooks[asin]['TotalReviews'] > min(n*n, amazonBooks[purchasedAsin]['TotalReviews']/n):
                if amazonBooks[asin]['ClusteringCoeff']>(amazonBooks[purchasedAsin]['ClusteringCoeff']/n):
                    MetaData = {}
                    MetaData['Title'] = amazonBooks[asin]['Title']
                    MetaData['SalesRank'] = amazonBooks[asin]['SalesRank']
                    MetaData['TotalReviews'] = amazonBooks[asin]['TotalReviews']
                    MetaData['AvgRating'] = amazonBooks[asin]['AvgRating']
                    MetaData['DegreeCentrality'] = amazonBooks[asin]['DegreeCentrality']
                    MetaData['ClusteringCoeff'] = amazonBooks[asin]['ClusteringCoeff']
                    # A score is calculated as per the below formula
                    MetaData['Score'] =  amazonBooks[asin]['AvgRating']**(n)+amazonBooks[asin]['TotalReviews']*n-\
                    amazonBooks[asin]['SalesRank']/n
                    recommendedD[asin]=MetaData
                    scores.append(MetaData['Score'])

#our score is scaled on a .5 to 5, rounded to the nearest .5 and dictionary is
#arranged in descending order
maxscore = max(scores)
minscore = min(scores)

for asin in recommendedD.keys():
    recommendedD[asin]['ScaledScore'] = round(1+(recommendedD[asin]['Score']-minscore)*(10-1)/(maxscore - minscore),1)/2
    scoresD[asin] = recommendedD[asin]['ScaledScore']
    
temp = sorted(scoresD.items(), key=operator.itemgetter(1),reverse=True)
scoresD = dict(temp)

# Print Top 5 recommendations (ASIN, and associated Title, Sales Rank, 
# TotalReviews, AvgRating, DegreeCentrality, ClusteringCoeff)

count = 1

for asin in scoresD.keys():
    if count>5:
        break
    print("")
    print("=======Recommendation", count, "=============")
    print("ASIN:", asin)
    print("Title:", recommendedD[asin]["Title"])
    print('SalesRank:', recommendedD[asin]['SalesRank'])
    print('TotalReviews:', recommendedD[asin]['TotalReviews'])
    print('AvgRating:', recommendedD[asin]['AvgRating'])
    print('DegreeCentrality:', recommendedD[asin]['DegreeCentrality'])
    print('ClusteringCoeff:', recommendedD[asin]['ClusteringCoeff'])
    print('Our predicted rating:', recommendedD[asin]['ScaledScore'])
    count+=1