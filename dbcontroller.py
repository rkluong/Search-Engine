# "NAME: Randy Luong , Ngoc Nguyen, Nam Nguyen
#"ID# 43351454_72114439_49699153

import string
import re
import math
import os
import collections
import sys
from itertools import combinations
from stop_words import get_stop_words
from pymongo import *
from pprint import pprint
import time

totalDocCount=0;
word_dict = dict();
doc_dict = dict();

K = 30;
#used to help find the pages with most intersections between the query terms
# Term1 & Term2 & Term3 ..& N Terms
# on each interation use the combination of  N/N...N-1/N ...N-2/N ... 1/N
#loop runs until we populate K results of unique docIds, we also only take the top K tf-idfs of each
#term dictionary of docids shown by the sorted function

def softConjunction(query: set) -> 'list[docids]':
	temp_list = list();
	result_list = list();
	for term in query:
		if term in word_dict :
			temp_list.append(set([x for x,y in sorted(word_dict[term].items(), key=lambda item: -item[1][1])[0:K]]));
	k = len(temp_list);

	while(k > 0):
		for combo in combinations(temp_list, k):
			result_list.extend(list(set.intersection(*list(combo))));
			result_list = list(set(result_list));
			if(len(result_list) > K):
				return result_list;
		k-=1;	

	return result_list;


#cosine Score ranking function with soft conjunction
def cosineScore(query: set) -> 'list of (docid,scores)':

   ##implementation: first choose top 30 docs of each term first
   ##then find the intersection of each term among docs depend on the ratio' 5/5 5results 4/5 10 3/5 until we get 50

	Scores = dict();
	Length = dict();
	if(len(query) == 1):
		for term in query:
			if term in word_dict:
				return sorted(word_dict[term].items(), key=lambda item: -item[1][1])[0:K];
			else:
				return [];
				
	for docid in softConjunction(query):
		for term in query:
			if term in word_dict:
				if docid in word_dict[term].keys():
					if docid not in Scores:
						Scores[docid] = 0;
					if docid not in Length:
						Length[docid] = 0;
					Scores[docid]+= word_dict[term][docid][1];
					Length[docid]+= word_dict[term][docid][1]**2;

	for docid in Length.keys():
		Scores[docid] = Scores[docid]/math.sqrt(Length[docid]);

	return sorted(Scores.items(), key=lambda item: -item[1])[0:K];


def add_tf_idf()->'dict term:{docid: [tf, tf-df]}':
	for k,v in word_dict.items():
		for k2, v2 in v.items():
			word_dict[k][k2] = [v2, round((1 + math.log10(v2))*math.log10( (totalDocCount/(len(word_dict[k].keys())))),5)]

#builds word_dict from all the files used as a helper to load data into the database  
def parsefile(filename: str):
	global totalDocCount;
	try:
		file = open(filename, "r", encoding="utf-8");
	except:
		return;
	file.close();

	with open(filename, "r", encoding = "utf-8") as file:
		totalDocCount+=1
		
		doc_dict[filename] = 0;
		for line in file:
			cur_line = re.split('[^a-zA-Z0-9]$', line)
			
			for i in range(len(cur_line)): 
				#remove tags
				cur_line[i].strip();
				clean_word = re.sub("<.*?>$", ' ', cur_line[i]);
				cur_line[i] = clean_word;
				clean_word = re.sub("[^a-zA-Z]", ' ', cur_line[i]);
				cur_line[i] = clean_word;
				
			cur_line =  "".join(cur_line).lower();
			for word in cur_line.split():
				if(word not in get_stop_words('english')):
					doc_dict[filename] += 1;
					if word not in word_dict:
						word_dict[word] = collections.OrderedDict();
						word_dict[word][filename] = 1;
					else:
						if filename not in word_dict[word]:
							word_dict[word][filename] = 1
						else:
							word_dict[word][filename] +=1

#sets up the database if its already been setup then do nothing
#IMPORTANT: remember to change reading the files for loop
def setupDB(mydb: 'db'):
	for i in range(75):
		for j in range(500):
			parsefile("WEBPAGES_CLEAN/{}/{}".format(i,j));
	
	add_tf_idf();
	
	for term, value in word_dict.items():
		mydb.search.insert_one({'termid': term, 'keys': value});	

#searches the database and returns a list of result pairs (docid, cosScore)
#only function called in the front end
def search(query: str, mydb: 'db' ):
	query = query.lower();
	query = set([word for word in query.split() if word not in get_stop_words('english')]);	
	#builds word_dict with only query terms
	#if we set up the word_dict means this is the first time so we do not need to populate from the DB
	#if we did not set up the word_dict mean we have parsed the data into the database before
		#just get the query terms from the DB to populate the word_dictionary
	for term in query:	
		cursor = mydb.search.find({'termid': term});
		for doc in cursor:
			if doc['termid'] not in word_dict.keys():
				word_dict[doc['termid']] = doc['keys'];
	return cosineScore(query);

if __name__ == '__main__':
	#backend
	now = time.time();
	client = MongoClient()
	db = client.search;
	db.search.drop();
	setupDB(db);
	print("SetupDB time: {} seconds".format(time.time()-now));