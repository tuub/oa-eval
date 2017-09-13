#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

###############################################################################
# This work is distributed under a BSD 3-Clause License.
# license terms see https://opensource.org/licenses/BSD-3-Clause
# developed mainly by Eva Bunge (ORCiD:0000-0002-5587-5934, github.com/ebunge) 
# with support from Michaela Voigt (ORCiD:0000-0001-9486-3189, 
# github.com/michaelavoigt) and maintained by the Open Access team of
# TU Berlin University Library
###############################################################################

import numpy as np
import collections
import cPickle as pickle
import weakref
from prettytable import PrettyTable
import urllib2
import json

# ----------------- 1. Enable/Disable Functionalities -------------------------

# Detailed instructions for querying databases and preparing DOAJ data 
# are included in the manual (in German).

# These variables are used to run only certain parts of the script. Set 
# them all to 'True' to run the whole script.
# doAnalysis: If True - do some statistics and analysis of the final data. If
# False - disable this feature.
# doReadIn: If True - read in the database data from the text files and save it
# to file 'finalList'. If False - data is loaded from file 'finalList'
doAnalysis = True
doReadIn = True

# Variable that determines whether to contact CrossRef. Possible values:
# 1: Contact the CrossRef API to add missing ISSNs. Write results to file.
# 2: Read results from previously created file instead
# 0: Disable this feature
contactCR = 2

# Variable that determines whether to contact oaDOI in order to retrieve data 
# on green and hybrid OA. Possible values:
# 1: Contact the oaDOI-API to retrieve OA-article-data. Write results to file.
# 2: Read results from previously created file instead
# 0: Disable this feature
contactOaDOI = 2

# Decide what to do when a corresponding/first author of a publication can't be
# determined manually. Possible values:
# 1: Write all of those articles to a file (docsToBeChecked.txt).
#    Once you have determined which aricles have a first/corresponding author
#    from a relevant institution, save the data in a tab-delimited, utf8-
#    encoded text-file called 'docsChecked.txt', with the following format:
#    each line corresponds to an article and the three columns contain (in this
#    order): title, DOI, name of institution (which should be spelled identical
#    to the name of the institution as set up in this script = 'inst.name')
#    Place this file in the subfolder 'input-files'
# 2: Load this information into the script and have it included in the final
#    results and the statistic.
# 0: Disable this feature completely.
checkToDo = 1

# Clarify which years of publication are of interest to you
yearMin = 2016
yearMax = 2016

# ----------------- 2. Setting up Classes and Functions -----------------------

# Set up class for institutions
class Inst(object):
    instances = []
    nameVar1 = None
    def __init__(self, name, nameVariants):
        self.__class__.instances.append(weakref.proxy(self))
        self.name = name
        self.nameVar = nameVariants

# Set up class for databases
class Database(object):
    instancesdb = []
    content = None
    def __init__(self, name, idNummer):
        self.__class__.instancesdb.append(weakref.proxy(self))
        self.name = name
        self.idNummer = idNummer

# Set up class for documents
class Document(object):
    nameVariant = None
    allNameVariants = None
    doajSubject = None
    lizenz = None
    oaStatus = None
    APCValue = None
    APCCurrency = None
    checks = ''
    oaDOI1 = 0
    oaDOI2 = 0
    oaDOI3 = 0
    oaDOI4 = 0
    
    def __init__(self, authors, title, DOI, journal, ISSN, eISSN, publisher,
                 year, affiliations, corrAuth, eMail, subject, funding, dbID):
        self.authors = authors
        self.title = title
        self.DOI = DOI
        self.journal = journal
        self.ISSN = ISSN
        self.eISSN = eISSN
        self.publisher = publisher
        self.year = year
        self.affiliations = affiliations
        self.corrAuth = corrAuth
        self.eMail = eMail
        self.subject = subject
        self.funding = funding
        self.dbID = dbID
        
    # Return first three consonants of the author's name concatenated with the
    # first 19 consonants of the title
    def konsonanten(self):
        d = ' '.join([''.join([i for i in self.authors if i in co]).lower()[0:3],
        ''.join([i for i in self.title if i in co]).lower()[0:19]])
        return d
    
    # Return all values associated with a certain publication
    def arry(self):
        return [self.authors, self.title, self.oaStatus, self.DOI,
                self.journal, self.ISSN, self.eISSN, self.publisher, self.year,
                self.affiliations, self.allNameVariants, self.corrAuth,
                self.nameVariant, self.eMail, self.subject, self.doajSubject,
                self.funding, self.lizenz, self.dbID, self.checks, self.oaDOI1,
                self.oaDOI2, self.oaDOI3, self.oaDOI4, self.APCValue,
                self.APCCurrency]

# Function that takes consonants from a title and turns them into a string
# INPUT: title of a publication (string)
# OUTPUT: first twenty consonants of the title (string)
def kons(title):
    d = ''.join([item for item in title if item in co]).lower()[0:19]
    return d

# Function that checks if an ISSN/eISSN is in the DOAJ and adds doaj-data
# to the document
# INPUT: List of documents to be checked, case = 1 in general, case = 2 if 
# finalList is being read in from a file
def checkISSN(docList, case):
    for item in docList:
            test1 = (item.ISSN in eissns or item.ISSN in issns)
            test2 = (item.eISSN in eissns or item.eISSN in issns)
            test3 = False
            if test1:
                t1 = [rec for rec in doaj if rec[0] == item.ISSN]
                if t1 == []:
                    t1 = [rec for rec in doaj if rec[1] == item.ISSN]
                test3 = int(t1[0][8]) <= int(item.year)
            elif test2:
                t1 = [rec for rec in doaj if rec[0] == item.eISSN]
                if t1 == []:
                    t1 = [rec for rec in doaj if rec[1] == item.eISSN]
                test3 = int(t1[0][8]) <= int(item.year)
            if test3:
                if (item.ISSN != None and test1) \
                or (item.eISSN != None and test2):
                    if case == 1:
                        item.oaStatus = 'gold'
                        item.checks += 'Identified via DOAJ '
                        if t1[0][4] != '':
                            item.APCValue = t1[0][4]
                            item.APCCurrency = t1[0][5]
                    elif case == 2:
                        doc = filter(lambda x: x.DOI == item.DOI, finalList)
                        doc[0].oaStatus = 'gold'
                        doc[0].checks += 'Identified via DOAJ '
                        if t1[0][4] != '':
                            doc[0].APCValue = t1[0][4]
                            doc[0].APCCurrency = t1[0][5]
                    if test1:
                        j = np.where(doaj == item.ISSN)
                    elif test2:
                        j = np.where(doaj == item.eISSN)
                    item.doajSubject = str(doaj[j[0],3]).strip("['").strip("']")
                    item.publisher = str(doaj[j[0],6]).strip("['").strip("']")
                    if '\n' in item.publisher:
                        item.publisher = ''.join([s for s in item.publisher
                                                  if s != '\n'])
                    item.lizenz = str(doaj[j[0],7]).strip("['").strip("']")
    return

# Function to identify corresponding authors (= first authors) in Inspec data
# INPUT: list of authors of a publication, list of their affiliations
# OUTPUT: first author; associated affiliation (string)
def inspecCorrAuth(auth, affil):
    authorList = auth.split('; ')
    affilList = affil.split('; ')
    if authorList[0] in affilList:
        firstAuth = affilList.index(authorList[0])
    else:
        return None
    while firstAuth < len(affilList) and affilList[firstAuth] in authorList:
        firstAuth += 1
    if firstAuth + 1 == len(affilList):
        tempor = affilList[-1]
    elif firstAuth < len(affilList):
        tempor = affilList[firstAuth].split('.')[:-2]
    return authorList[0] + '; ' + ''.join(tempor) 

# Function that takes a list of documents and contacts CrossRef to find
# missing ISSNs/eISSNs
# INPUT: List of documents that have a DOI but no ISSN of eISSN
def askCR(missISSN):
    print 'Begin contacting CrossRef'
    c = 0
    reCheck = []
    baseurl = 'http://api.crossref.org/works/'
    for doc in missISSN:
        doi = doc.DOI
        myurl = baseurl + doi
        try:
            response = urllib2.urlopen(myurl)
            cr_data = json.load(response)
            cr_data_msg = cr_data["message"]
            if cr_data_msg.has_key("ISSN"):
                c += 1
                reCheck.append(doc)
                doc.ISSN = str(cr_data_msg["ISSN"][0])
                if len(cr_data_msg["ISSN"]) > 1:
                    doc.eISSN = str(cr_data_msg["ISSN"][1])
        except urllib2.HTTPError, err:
            if err.code == 404:
                fehler = "404"
    print str(c) + ' ISSNs added via CrossRef'
    return reCheck

# Contacts the oaDOI-API to retrieve data on green / hybrid (& gold) OA status
# Also retrieve publisher data if provided.
# INPUT: List of publications that have a DOI but whose ISSN is not listed in
#        the DOAJ
# OUTPUT: Results printed to file oaDOI-response.txt: one line per publication,
#         containing the following information: DOI, is_oa, journal_is_oa,
#         host_type [repository or publisher], license, publisher, oaStatus
def askOaDOI(needInfo):
    print 'Begin contacting oaDOI'
    baseurl = 'https://api.oadoi.org/v2/'
    eMail = '?email=e.bunge@deutsches-museum.de'
    relKeys = {1:'is_oa', 2:'journal_is_oa', 3:'host_type', 4:'license',
               5:'publisher'}
    replies = [[0 for x in range(7)] for y in range(len(needInfo))]
    i = 0
    for doc in needInfo:
        doi = doc.DOI
        replies[i][0] = doi
        myurl = baseurl + doi + eMail
        try:
            response = urllib2.urlopen(myurl)
            response = json.load(response)
            for item in relKeys:
                if response.has_key(relKeys[item]):
                    replies[i][item] = response[relKeys[item]]
                elif response.has_key('best_oa_location'):
                    subresponse = response['best_oa_location']
                    if subresponse != None:
                        replies[i][item] = subresponse[relKeys[item]]
                if replies[i][1] == True and replies[i][2] == True:
                    doc.oaStatus = 'gold'
                    doc.checks += 'Identified via oaDOI '
                elif replies[i][1] == True and replies[i][2] == False \
                                           and replies[i][3] == 'repository':
                    doc.oaStatus = 'green'
                    doc.checks += 'Identified via oaDOI '
                elif replies[i][1] == True and replies[i][2] == False \
                                           and replies[i][3] == 'publisher':
                    if 'cc' in str(replies[i][4]):
                        doc.oaStatus = 'hybrid'
                        doc.checks += 'Identified via oaDOI '
                doc.oaDOI1 = replies[i][1]
                doc.oaDOI2 = replies[i][2]
                doc.oaDOI3 = str(replies[i][3])
                doc.oaDOI4 = str(replies[i][4])
                doc.lizenz = str(replies[i][4])
                doc.publisher = str(replies[i][5])
                replies[i][6] = doc.oaStatus
        except urllib2.HTTPError, err:
            fehler = "error"
        i += 1
        if i % 500 == 0:
            print 'Now received responses for ', i, ' documents from oaDOI'
    ch = 'DOI\tis_oa\tjournal_is_oa\thost_type\tlicense\tpublisher\toaStatus'
    np.savetxt('output-files/oaDOI-response.txt', replies, delimiter='\t',
               header = ch, comments = '', fmt='"%s"')
    print 'Saved oaDOI-responses to file "oaDOI-responses.txt"'
    return

# Function that takes data in WoS-format and transforms the data into a list of
# Document-objects.
# !This function is not really needed in this script as it is right now!
# It's being included for the purpose of easily adding new databases to the
# script. To do this export article data from Citavi in the WoS-format and use
# this function to do the read-in for the data
# INPUT: (list of records in WoS-format, database ID (integer))
# OUTPUT: list of Document-objects
def wosFormat(wosRecords, ind):
    records = []
    i = 0
    with open(wosRecords, 'rU') as f:
        for line in f:
            if i == 0:
                newDoc = Document('', '', None, None, None, None, 
                                  None, None, '', None, None, None, None, ind)
                i += 1
            le = len(line)
            if line[0:2] != '  ':
                kuerzel = line[0:2]
            if line[0:2] == 'TI':
                newDoc.title = line[3:le].strip('\n').strip('\r')
            elif line[0:2] == 'SO':
                newDoc.journal = line[3:le].strip('\n').strip('\r')
            elif line[0:2] == 'PY':
                newDoc.year = line[3:le].strip('\n').strip('\r')
            elif line[0:2] == 'SN':
                if '-' not in line:
                    vorl = line[3:le].strip('ISSN ').strip('\n').strip('\r')
                    newDoc.ISSN = vorl[0:4] + '-' + vorl[4:8]
                elif ',' in line:
                    newDoc.ISSN = line.strip('ISSN ').strip('\n').strip('\r')[0:9]
                else:
                    newDoc.ISSN = line[3:le].strip('ISSN ').strip('\n').strip('\r')
            elif line[0:2] == 'DI':
                newDoc.DOI = line[3:le].strip('\n').strip('\r')
            elif line[0:2] == 'AF':
                newDoc.authors = line[3:le].strip('\n').strip('\r')
            elif kuerzel == 'AF' and line[0:2] == '  ':
                newDoc.authors += '; '
                newDoc.authors += line[3:le].strip('\n').strip('\r')
            elif line[0:2]  == 'FN':
                records.append(newDoc)
                newDoc = Document('', '', None, None, None, None,
                                  None, None, '', None, None, None, None, ind)
        records.append(newDoc)
    return records

# Checks a given name of an institution against a list of approved name
# variants and returns the names of institutions that have been identified.
# INPUT: (text string with name of an institution, database ID)
# OUTPUT: (bool stating if instition is part of approved list, names of 
#         institutions that have been found)
def listCheck(institution, case):
    val = [None] * len(institutions)
    variant = None
    for i in range(0, len(val)):
        if case == 0:
            instList = institutions[i].nameVar
        elif case == 1:
            instList = institutions[i].nameVar1
        valu = [None] * len(instList)
        for j in range(0, len(instList)):
            valu[j] = all(word in institution for word in instList[j])
        if any(valu):
            if variant == None:
                variant = institutions[i].name
            else:
                variant += '; ' + institutions[i].name
            val[i] = True
    return (any(val), variant)

# Function that takes data in PubMed-format and transforms it into a list of 
# Documents.
# INPUT: (PubMed-records, database ID (integer))
# OUTPUT: list of Documents
def pubmedFormat(pmRecords, ind):
    records = []
    i = 0
    authorCount = 0
    newDoc = None
    with open(pmRecords, 'rU') as f:
        for line in f:
            lengths = len(line)
            if line[0:2] != '  ':
                kuerzel = line[0:4]
            if line[0:4]  == 'PMID':
                authorCount = 0
                if i > 0:
                    records.append(newDoc)
                newDoc = Document('', '', None, None, None, None,
                                  None, None, '', None, None, None, None, ind)
                i += 1
            elif line[0:2] == 'TI':
                newDoc.title = line[6:lengths].strip('\n').strip('\r')
            elif kuerzel == 'TI  ' and line[0:2] == '  ':
                newDoc.title += ' ';
                newDoc.title += line[6:lengths].strip('\n').strip('\r')
            elif line[0:2] == 'IS' and line[-5:-2] == 'nic':
                newDoc.eISSN = line[6:15]
            elif line[0:2] == 'IS' and line[-5:-2] == 'ing':
                newDoc.ISSN = line[6:15]
            elif line[0:3] == 'FAU' and authorCount > 0:
                newDoc.authors += '; '
                newDoc.authors += line[6:lengths].strip('\n').strip('\r')
                authorCount += 1
            elif line[0:3] == 'FAU' and authorCount == 0:
                newDoc.authors = line[6:lengths].strip('\n').strip('\r')
                newDoc.corrAuth = newDoc.authors + '; '
                authorCount += 1
            elif authorCount == 1 and line[0:2] == 'AD':
                newDoc.corrAuth += line[6:lengths].strip('\n').strip('\r')
                newDoc.affiliations = line[6:lengths].strip('\n').strip('\r')
            elif line[0:2] == '  ' and kuerzel == 'AD  ' and authorCount == 1:
                newDoc.affiliations += line[5:lengths].strip('\n').strip('\r')
                newDoc.corrAuth += line[5:lengths].strip('\n').strip('\r')
            elif line[0:2] == '  ' and kuerzel == 'AD  ' and authorCount > 1:
                newDoc.affiliations += line[5:lengths].strip('\n').strip('\r')
            elif authorCount > 1 and line[0:2] == 'AD':
                newDoc.affiliations += '; '
                newDoc.affiliations += line[5:lengths].strip('\n').strip('\r')
            elif line[0:2] == 'JT':
                newDoc.journal = line[6:lengths].strip('\n').strip('\r')
            elif line[0:2] == 'DP':
                newDoc.year = line[6:10]
            elif line[0:3] == 'LID' and 'doi' in line:
                newDoc.DOI = line[6:lengths].strip('\n').strip('\r').strip(' [doi]')
        records.append(newDoc)
    return records

# Read in table mapping RIS-fields of databases to document-attributes
risFields = np.genfromtxt('RIS-fields.csv', delimiter=';', dtype = None)

# Valid characters for ISSNs
numX = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'X']

# Read in RIS-files
# INPUT: RIS-records, database-ID
# OUTPUT: List of documents
def risFormat(risRecords, ind):
    records = []
    newDoc = None
    relMap = risFields[:,np.where(risFields[0,:] == str(ind))]
    with open(risRecords, 'rU') as f:
        for line in f:
            twoL = line[0:2]
            textL = line[6:-1]
            if ind == 12:
                newDocInd = 'ID'
            else:
                newDocInd = 'TY'
            if twoL == newDocInd:
                if newDoc != None:
                    records.append(newDoc)
                newDoc = Document('', '', None, None, None, None, None, None,
                                  '', None, None, None, None, ind)
            if twoL.isupper() and line[2] == ' ':
                if twoL in relMap:
                    ab = str(risFields[np.where(relMap == twoL)[0],0][0])
                    if getattr(newDoc, ab) in ('', None):
                        
                        # Authors
                        if ab == 'authors' and ind in [4, 7, 9, 10, 11, 12, 17]:
                            setattr(newDoc, ab, textL)
                            setattr(newDoc, 'corrAuth', textL)
                            
                        # DOIs
                        elif ab == 'DOI':
                            if '10.' in textL and 'y.com/' not in textL:
                                if 'doi.org' in textL:
                                    s1 = textL.find('.org')
                                    textL = textL[s1 + 5:]
                                if ' ' in textL:
                                    textL = textL[:textL.find(' ')]
                                setattr(newDoc, ab, textL.strip('doi:'))
                        
                        # ISSNs
                        elif ab == 'ISSN':
                            if textL[0:4] != '978-':
                                isInt = filter(lambda x: x in numX, textL)
                                if isInt != '':
                                    setattr(newDoc, ab,
                                            isInt[0:4] + '-' + isInt[4:8])
                                if len(isInt) > 8:
                                    setattr(newDoc, 'eISSN',
                                            isInt[8:12] + '-' + isInt[12:16])
                        
                        # Year
                        elif ab == 'year' and len(textL) > 4:
                            setattr(newDoc, ab, int(line[6:10]))
                        
                        # affiliations
                        elif ab == 'affiliations' and ind in [4, 7, 10, 11, 12]:
                            setattr(newDoc, ab, textL)
                            setattr(newDoc, 'corrAuth',
                                    getattr(newDoc, 'corrAuth') + "; " + textL)
                        # Embase
                        elif ab == 'affiliations' and ind == 14:
                            if getattr(newDoc, 'corrAuth') == None:
                                t1 = getattr(newDoc, 'authors')
                                p1 = t1.find('; ')
                                if p1 < 0:
                                    p1 = len(t1)
                                t1 = t1[:p1]
                                t2 = getattr(newDoc, 'affiliations')
                                p2 = t2.find('; ')
                                if p2 < 0:
                                    p2 = len(t2)
                                p3 = t2.find(')') + 2
                                t2 = t2[p3:p2]
                                setattr(newDoc, 'corrAuth', t1 + '; ' + t2)
                        # BSC, EBSCO, SportDiscus
                        elif ab == 'affiliations' and ind in [9, 13, 17]:
                            q1 = -1
                            if ind == 17:
                                if 'Affiliation' in textL:
                                    q1 = textL.find('Affiliation') + 15
                            else:
                                if 'Affiliation' in textL:
                                    q1 = textL.find('Affiliation') + 17
                            if q1 > 0:
                                if textL[q1-1] != ' ' and textL[q1] != ' ':
                                    while textL[q1-1] != ' ':
                                        q1 -= 1
                                beTe = getattr(newDoc, 'corrAuth')
                                if beTe == None:
                                    beTe = ''
                                # BSC
                                if ind == 9:
                                    q2 = textL.find('Issue Info:') - 2
                                    q3 = textL[q1:q2+2].find('; ')
                                    qd = q1 + 3
                                    setattr(newDoc, 'corrAuth',
                                            beTe + "; " + textL[q1:qd])
                                # EBSCO
                                elif ind == 13:
                                    q2 = textL.find('Source Info:') - 2
                                    if q2 < 0:
                                        q2 = textL.find('Issue Info:') - 2
                                    if q2 < 0:
                                        q2 = textL.find('Document Type:') - 2
                                    if q2 < 0:
                                        q2 = textL.find('Release Date:') - 2
                                    q3 = textL[q1:].find(' 2:')
                                    if q3 < 0:
                                        q3 = textL[q1:].find(' 2 :')
                                    if q3 > 0:
                                        qd = q1 + q3
                                    else:
                                        qd = q2
                                    if getattr(newDoc, 'corrAuth') == None:
                                        setattr(newDoc, 'corrAuth', '')
                                    setattr(newDoc, 'corrAuth',
                                            beTe + "; " + textL[q1:qd])
                                # SportDiscus
                                elif ind == 17:
                                    q2 = textL.find('No. of Pages:') - 2
                                    q3 = textL[q1:].find(': 2 ')
                                    if q3 > 0:
                                        qd = q1 + q3
                                    else:
                                        qd = q2
                                    setattr(newDoc, 'corrAuth',
                                            beTe + "; " + textL[q1:qd])
                                setattr(newDoc, ab, textL[q1:q2])
                            # Find E-Mail-Adresses
                            if ind == 17:
                                p1 = textL.find('email:')
                            else:
                                p1 = textL.find('Email Address:')
                            if p1 > 0:
                                if ind == 17:
                                    p1 += 7
                                else:
                                    p1 += 15
                                if ind == 9:
                                    p2 = textL[p1:-1].find(';')
                                elif ind == 13:
                                    p2 = textL[p1:-1].find(' ')
                                elif ind == 17:
                                    p2 = textL[p1:-1].find('. ')
                                setattr(newDoc, 'eMail', textL[p1:p1 + p2].strip(';'))
                        
                        # Corresponding Authors
                        elif ab == 'corrAuth' and ind == 14:
                            setattr(newDoc, ab, textL)
                            p1 = textL.find('E-mail:')
                            if p1 > 0:
                                p1 += 8
                                setattr(newDoc, 'eMail', textL[p1:].strip(';'))
                        elif ab == 'corrAuth' and ind == 16:
                            if 'Correspondence Address' in textL:
                                o1 = textL.find('Correspondence Address') + 24
                                setattr(newDoc, ab, textL[o1:])
                        else:
                            setattr(newDoc, ab, textL)
                    # If something is already written in this attribute
                    elif getattr(newDoc, ab) not in ('', None) \
                                             and ab != 'ISSN' and ab != 'DOI':
                        if (ab != 'corrAuth' or ind != 16) and \
                           (ab != 'corrAuth' or ind != 13):
                            setattr(newDoc, ab,
                                    getattr(newDoc, ab) + "; " + textL)
                    elif getattr(newDoc, ab) not in ('', None) \
                                             and ab == 'ISSN' and ab != 'DOI':
                        if textL[0:4] != '978-':
                            if ind == 13:
                                setattr(newDoc, ab, textL)
                            else:
                                setattr(newDoc, 'eISSN',
                                        line[6:10] + '-' + line[10:-1])
                # Scopus: If no corresponding author was provided, use first
                # author instead
                if twoL == 'UR' and ind == 16:
                    if newDoc.corrAuth == None:
                        authorList = newDoc.authors.split('; ')
                        affilList = newDoc.affiliations.split('; ')
                        setattr(newDoc, 'corrAuth',
                                authorList[0] + '; ' + affilList[0])
        records.append(newDoc)
    return records

# List of consonants
co = ('b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r',
          's', 't', 'v', 'w', 'x', 'y', 'z', 'B', 'C', 'D', 'F', 'G', 'H', 'J',
          'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Y', 'Z')

# Duplicate check
# This function takes a set of data (= masterList) and compares incoming new 
# data with it. All duplicates are removed from the new data which is then
# added to the masterList. This action is repeated for each database.
# Comparisons are done via DOI-matching and then title/author-matching.
# doiList = list that contains all DOIs from masterList.
# konsMast = a list of strings which consist of the first three consonants of
# the authors' names and the first 19 consonants of the title for the data
# in the masterlist.
# INPUT: (iterating integer, list containing article data,
#         list of DOIs (strings), list of strings for title/author-matching)
# OUTPUT: list containing Documents with duplicates removed
def dubletten(iterates, masterList, dois, kons):
    if iterates == 1:
        nowList = dbSF.content
    else:
        nowList = datenbanken[iterates].content
    if iterates == 1:
        doiList = [x.DOI for x in masterList]
        konsMast = [item.konsonanten() for item in masterList]
    else:
        doiList = dois
        konsMast = kons
    f = collections.Counter(konsMast)
    i = len(nowList)
    print datenbanken[iterates].name, ' - number of records: ', i
    nowList = [item for item in nowList if item.DOI == None
                                        or item.DOI.strip('"') == ''
                                        or item.DOI.strip('"') not in doiList]
    j = len(nowList)
    print datenbanken[iterates].name, \
          ' - number of records removed via DOI-matching: ', i-j
    nowList = [item for item in nowList if item.authors != None
                                        and item.konsonanten() not in f]
    k = len(nowList)
    print datenbanken[iterates].name, \
          ' - number of records removed via title/author-matching: ', j-k
    print datenbanken[iterates].name, \
          ' - number of records added to masterList: ', k
    if k > 0:
        masterList += nowList
        doiList += [x.DOI for x in nowList]
        konsMast += [item.konsonanten() for item in nowList]
    iterates += 1
    if iterates < len(datenbanken):
        masterList = dubletten(iterates, masterList, doiList, konsMast)
    return masterList


# -------------------- 3. Set up Institutions ---------------------------------

# Set up institutions. Format for name variants: 
# [[var1,var2],[var3]] is equivalent to: (var1 AND var2) OR (var3)
# Careful: the name variant used when querying the database is not
# necessarily the same name variant used in the raw data.

# TU
TUnames = [['Tech', 'Univ', 'Berlin'], ['Berlin', 'TU'],
           ['Berlin', 'Inst', 'Technol']]
TU = Inst('TU', TUnames)

# Charité
Cnames = [['Charit', 'Univ'],
          ['Campus', 'Virchow', 'Berlin'],
          ['Campus', 'Franklin', 'Berlin'],
          ['Charit', 'Berlin']]
Charite = Inst('Charité', Cnames)

# FU
FUnames = [['Berlin','FU'], ['Berlin','Free','Univ'],
           ['Berlin','Frei','Univ'], ['Univ', 'Libre', 'Berlin']]
FU = Inst('FU', FUnames)

# HU
HUnames = [['Berlin', 'HU'],
           ['Berlin', 'Humboldt', 'Univ']]
HU = Inst('HU', HUnames)

# UdK
UdKnames = [['Univ', 'Arts', 'Berlin'],
            ['Univ', 'Kunst', 'Berlin'],
            ['Berlin', 'UdK']]
UdK = Inst('UdK', UdKnames)

# Beuth
Bnames = [['Beuth', 'Berlin']]
Beuth = Inst('Beuth', Bnames)

# HTW
HTWnames = [['HTW', 'Berlin'],
            ['Tech', 'Wirt', 'Berlin']]
HTW = Inst('HTW', HTWnames)

# HWR
HWRnames = [['HWR','Berlin'],
            ['Wirt','Recht','Berlin'],
            ['Berlin', 'Economics', 'Law', 'School']]
HWR = Inst('HWR', HWRnames)

# Alice Salomon
ASHnames = [['Alice','Salomon','Berlin'], ['ASH','Berlin'],
            ['Universidad Alice Salomon']]
ASH = Inst('ASH', ASHnames)

#Create list of institutions
institutions = [x for x in Inst.instances]

# If the name of the institution is very generic, a second set of name
# variants can be defined here. These are used when searching strings with
# more than one affiliation in them
for item in institutions:
    item.nameVar1 = item.nameVar

TU.nameVar1 = [['Technische Universitat Berlin'],
                ['Technische Universitaet Berlin'],
                ['Technische Universität Berlin'],
                ['Berlin Institute of Techn'],
                ['Tech Univ Berlin'],
                ['Berlin Univ Technol'],
                ['Univ Technol Berlin'],
                ['TU Berlin'],
                ['Tech. Univ. Berlin'],
                ['Technical Univ. of Berlin'],
                ['Berlin Inst Technol'],
                ['Technical University Berlin'],
                ['Technische Universitaet de Berlin'],
                ['Technical University of Berlin'],
                ['Berlin University of Technology']]



# ------------- 4. Read in Text Files and Extract Information -----------------

# Set up databases
# The order of the databases here determines the order in which they are
# considered. Therefore databases with good/complete metadata should be near
# the top
dbWoS = Database('Web of Science', 1)
dbSF = Database('SciFinder', 2)
dbPM = Database('PubMed', 3)
dbScopus = Database('Scopus', 16)
dbInspec = Database('Inspec', 5)
dbTEMA = Database('TEMA', 4)
dbPQ = Database('ProQuest', 7)
dbBSC = Database('Business Source Complete', 9)
dbGf = Database('GeoRef', 10)
dbCIN = Database('CINAHL', 12)
dbLisa = Database('LISA', 15)
dbCAB = Database('CAB Abstracts', 11)
dbEm = Database('Embase', 14)
dbSD = Database('SportDiscus', 17)
dbIEEE = Database('IEEE', 6)
dbEB = Database('EBSCO', 13)

# List the databases
datenbanken = [x for x in Database.instancesdb]

# Read in database contents from text-files
if doReadIn == True:
# Read in the 'Web of Science' file and extract the relevant information. 
    contentWoS = []
    with open('input-files/wos2016.txt') as f:
        ic = 0
        for line in f:
            fields = line.split('\t')
            if ic > 0:
                contentWoS.append(Document(fields[1], fields[8], fields[54],
                                 fields[9], fields[38], fields[39], fields[35],
                                 fields[44], fields[22], fields[23],
                                 fields[24], fields[58], fields[27],
                                 dbWoS.idNummer))
            else:
                ic += 1
    dbWoS.content = contentWoS
    print 'Finished reading in Web of Science'
    
    # Read in the 'SciFinder' files and extract the relevant information.
    contentSF = []
    with open('input-files/sf2016.txt', 'rU') as f:
        ic = 0
        for line in f:
            fields = line.split('\t')
            if ic > 0:
                contentSF.append(Document(fields[6].strip('"'), 
                                fields[3].strip('"'),
                                fields[49].strip('\n').strip('\r').strip('"'),
                                fields[17].strip('"'), fields[15].strip('"'),
                                None, None, fields[22].strip('"'),
                                fields[11].strip('"'), fields[11].strip('"'),
                                None, fields[9].strip('"'), None,
                                dbSF.idNummer))
            else:
                ic += 1
    dbSF.content = contentSF
    for item in dbSF.content:
        firstAuthor = item.authors.split('; ')[0]
        item.corrAuth = firstAuthor + '; ' + item.corrAuth
    print 'Finished reading in SciFinder'
    
    # Read in 'PubMed' file and extract relevant information.
    dbPM.content = pubmedFormat('input-files/pubmed2016.txt', dbPM.idNummer)
    print 'Finished reading in PubMed'

    # Read in 'Scopus' file and extract relevant information.
    dbScopus.content = risFormat('input-files/scopus2016.ris',
                                 dbScopus.idNummer)
    print 'Finished reading in Scopus'
    
    # Read in 'Inpsec' file and extract relevant information.
    contentInspec = []
    with open('input-files/inspec2016.txt') as f:
        ic = 0
        for line in f:
            fields = line.split('\t')
            if ic > 0:
                contentInspec.append(Document(fields[6], fields[5], fields[-8],
                                    fields[12], fields[50], None, fields[41],
                                    fields[13], fields[-24],
                                    inspecCorrAuth(fields[6], fields[-24]), 
                                    None, None, None, dbInspec.idNummer))
            else:
                ic += 1
    dbInspec.content = contentInspec
    print 'Finished reading in Inspec'

    # Read in 'TEMA' file and extract relevant information.
    dbTEMA.content = risFormat('input-files/tema2016.ris', dbTEMA.idNummer)   
    print 'Finished reading in TEMA'
    
    # Read in 'ProQuest' file and extract relevant information.
    dbPQ.content = risFormat('input-files/pq2016.ris', dbPQ.idNummer)
    print 'Finished reading in ProQuest'
    
    # Read in 'Business Source Complete' file and extract relevant information.
    dbBSC.content = risFormat('input-files/bsc2016.ris', dbBSC.idNummer)
    print 'Finished reading in Business Source Complete'
    
    # Read in 'GeoRef' file and extract relevant information.   
    dbGf.content = risFormat('input-files/gf2016.ris', dbGf.idNummer)
    print 'Finished reading in GeoRef'
    
    # Read in 'CINAHL' file and extract relevant information.
    dbCIN.content = risFormat('input-files/cinahl2016.ris', dbCIN.idNummer)
    print 'Finished reading in CINAHL'
    
    # Read in 'LISA' file and extract relevant information.
    dbLisa.content = risFormat('input-files/lisa2016.ris', dbLisa.idNummer)
    print 'Finished reading in LISA'

    # Read in 'CAB Abstracts' file and extract relevant information.
    dbCAB.content = risFormat('input-files/cab2016.ris', dbCAB.idNummer)
    print 'Finished reading in CAB Abstracts'

    # Read in 'Embase' file and extract relevant information.
    dbEm.content = risFormat('input-files/embase2016.ris', dbEm.idNummer)
    print 'Finished reading in Embase'
    
    # Read in 'SportDiscus' file and extract relevant information.
    dbSD.content = risFormat('input-files/sd2016.ris', dbSD.idNummer)
    print 'Finished reading in Sport Discus'

    # Read in 'IEEE' file and extract relevant information.
    dbIEEE.content = risFormat('input-files/IEEE2016.ris', dbIEEE.idNummer)
    print 'Finished reading in IEEE'
    
    # Read in 'EBSCO' file and extract relevant information.
    dbEB.content = risFormat('input-files/ebsco2016-v2.ris', dbEB.idNummer)
    print 'Finished reading in EBSCO'
    
# do not set up a new database below this line!    
    
    # Transform all characters in DOIs to lower case    
    for item in datenbanken:
        for article in item.content:
            if article.DOI != None:
                article.DOI = article.DOI.lower()


# ----------------------- 5. Duplicate Check ----------------------------------

# Calls the function 'dubletten' above and prints statistics or reads in data
# from previous run of the script
if doReadIn == True:
    print 'Remove Duplicates:'
    print 'Number of records in "Web of Science": ', len(contentWoS)
    finalList = dubletten(1, contentWoS, None, None)
    with open('finalList', "wb") as f:
        pickle.dump(finalList, f)
elif doReadIn == False:
    with open('finalList', "rb") as f:
        finalList = pickle.load(f)

# Check for duplicates within a database via DOI-matching
seen = set()
seen1 = set()
doubles = []
for x in finalList:
    if x.DOI != '' and x.DOI != None:
        if x.DOI not in seen:
            seen.add(x.DOI)
        else:
            doubles.append(x)
    else:
        if x.konsonanten() not in seen1:
            seen1.add(x.konsonanten())
        else:
            doubles.append(x)
for item in doubles:
    if item in finalList:
        finalList.remove(item)
print 'Removed an additional ', len(doubles), ' records due to them being ',\
      'duplicates within a database'

# Remove articles which were published before or after the time period that is
# of interest to you
l1 = len(finalList)
finalList = [item for item in finalList if int(item.year) >= yearMin
             and int(item.year) <= yearMax]
l2 = len(finalList)
print 'Removed ', l1 - l2, ' records that do not fit the specified time frame'

# Shortens author-list when very long
for item in finalList:
    if len(item.authors) > 300:
        item.authors = item.authors[0:300] + \
        '... [List shortened due to excessive length]'

# Make some adjustments to EBSCO data. These are due to several metadata-
# schemes being present in the data. This approach is suboptimal and shoud
# be cleaned up and rewritten
for item in finalList:
    if item.dbID == 13 and item.corrAuth != None:
        if item.corrAuth[0:2] == '; ':
            g = item.authors.split('; ')[0]
            setattr(item, 'corrAuth', g + getattr(item, 'corrAuth'))
        if item.affiliations == '' or item.affiliations == None:
            item.affiliations = item.corrAuth
        g = item.authors.split('; ')
        for auto in g:
            if auto in item.corrAuth:
                auto = True
        if all(g) and len(g) > 1:
            h = item.corrAuth.find(item.authors.split('; ')[1])
            setattr(item, 'corrAuth', getattr(item, 'corrAuth')[:h])


# ------------ 6. Identify Affiliations of Corresponding Authors --------------

# Adds information about found name variants
for item in finalList:
    if item.corrAuth not in [None, '']:
        i, j = listCheck(item.corrAuth, 0)
        if i == True:
            item.nameVariant = j
    if item.affiliations not in [None, '']:
        k, l = listCheck(item.affiliations, 1)
        if k == True:
            item.allNameVariants = l


# ------------- 7. Identify OA-articles and add DOAJ Data ---------------------

# Reads in the file with the data from DOAJ and crossreferences it with the 
# ISSNs and eISSNs from the database data.
# Add information about the subject, publisher and journal licence
doaj = np.loadtxt('input-files/doaj.txt', dtype = 'string', comments = '$#',
                  skiprows = 1, delimiter = '\t',
                  usecols = (3, 4, 0, 56, 11, 12, 5, 44, 29))
print 'Finished reading in DOAJ data'
issns = collections.Counter(doaj[:,0])
eissns = collections.Counter(doaj[:,1])
for item in finalList:
    if item.ISSN == '':
        item.ISSN = None
    if item.eISSN == '':
        item.eISSN = None
checkISSN(finalList, 1)
print 'Finished identifying OA articles'


# ----------------------- 8. Add CrossRef Data --------------------------------

# Contact the CrossRef-API with documents that have a DOI but no ISSN. Add
# missing ISSNs and crossreference them with the DOAJ
if contactCR == 1:
    nonOA = [item for item in finalList
             if item.oaStatus == None 
             and item.DOI != None
             and item.DOI != ''
             and item.ISSN == None and item.eISSN == None]
    newlyISSNed = askCR(nonOA)
    with open('CRResults', "wb") as f:
        pickle.dump(newlyISSNed, f)
    checkISSN(newlyISSNed, contactCR)
elif contactCR == 2:
    with open('CRResults', "rb") as f:
        newlyISSNed = pickle.load(f)
    checkISSN(newlyISSNed, contactCR)


# -------------------------- 9. Get oaDOI-Data --------------------------------

# Contact the oaDOI-API to retrieve information on hybrid / green / gold
# OA-Status and to add publisher info.
if contactOaDOI == 1:
    toOaDOI = [item for item in finalList if item.DOI not in [None, '']
               and item.oaStatus == None]
    askOaDOI(toOaDOI)
elif contactOaDOI == 2:
    c = 0
    with open('output-files/oaDOI-response.txt') as f:
        for line in f:
            if c > 0:
                fields = line.split('\t')
                doc = filter(lambda x: x.DOI == fields[0].strip('"'), finalList)
                doc[0].oaDOI1 = fields[1].strip('"')
                doc[0].oaDOI2 = fields[2].strip('"')
                doc[0].oaDOI3 = fields[3].strip('"')
                doc[0].oaDOI4 = fields[4].strip('"')
                doc[0].lizenz = fields[4].strip('"')
                doc[0].publisher = fields[5].strip('"')
                doc[0].oaStatus = fields[6].strip('\n').strip('"')
                doc[0].checks += 'Identified via oaDOI '
            else:
                c += 1


# -------- 10. Identify Articles Where CorrAuth needs to be checked by Hand ---

# Write list of articles that need to be checked by hand into a file
# 'docsToBeChecked.txt'
toCheck = [item for item in finalList if item.corrAuth in [None, '']]
ch = 'authors\ttitle\tOA-Status\tDOI\tjournal\tISSN\teISSN\tpublisher\tyear\t\
affiliations\tall identified name variants\tcorresponding author\t\
found name variant\te-mail\tsubject\tDOAJ subject\tfunding\tlicence\t\
databaseID\tnotes\toaDOI[is_oa]\toaDOI[journal_is_oa]\toaDOI[host_type]\t\
oaDOI[license]\tAPC Amount\tAPC Currency'
if checkToDo == 1:
    np.savetxt('output-files/docsToBeChecked.txt',
               [item.arry() for item in toCheck], 
               delimiter='\t', header = ch, comments = '', fmt='"%s"')

# Read in articles that were checked by hand and were found to have a 
# first/corresponding author from a relevant institution.
# Format: One line for each puclication. Three columns in this order:
# Title, DOI, found name variant. Tab-separated.
elif checkToDo == 2:
    addDocs = []
    doiList = [x.DOI for x in toCheck if x.DOI not in [None, '']]
    titles1 = [x.konsonanten()[4:] for x in toCheck]
    dontknow = []
    with open('input-files/docsChecked.txt') as f:
        for line in f:
            fields = line.split('\t')
            fields[0] = fields[0].strip('\xef\xbb\xbf')
            fields[0] = fields[0].strip('\n').strip('\r').strip(' ')
            fields[2] = fields[2].strip('\n').strip('\r')
            addDocs.append(fields)
    for item in addDocs:
        if item[1] in doiList:
            idDoc = next((x for x in toCheck if x.DOI == item[1]), None)
            idDoc.nameVariant = item[2]
            idDoc.checks += 'Checked by hand. '
        elif kons(item[0]) in titles1:
            idDoc = next((x for x in toCheck 
                          if x.konsonanten()[4:] == kons(item[0])), None)
            idDoc.nameVariant = item[2]
            idDoc.checks += 'Checked by hand. '
            idDoc.DOI = item[1]
        else:
            dontknow.append(item)
    if dontknow != []:
        np.savetxt('output-files/docsCheckedCantFind.txt',
                   [item for item in dontknow], 
                   delimiter='\t', header = 'Title\tDOI\tAffiliation',
                   comments = '', fmt='"%s"')


# ---------------- 11. Print final results and estimate APCs ------------------

# Print results to console
print '\n'
print 'Overall number of articles: ', len(finalList), '\n'
oaGoldNumber = len([item for item in finalList if item.oaStatus == 'gold'])
print 'Number of gold OA articles ', oaGoldNumber, '\n'
oaHybridNumber = len([item for item in finalList if item.oaStatus == 'hybrid'])
print 'Number of hybrid OA articles ', oaHybridNumber, '\n'
oaGreenNumber = len([item for item in finalList if item.oaStatus == 'green'])
print 'Number of green OA articles ', oaGreenNumber, '\n'
corrAuthNumber = len([item for item in finalList if item.oaStatus == 'gold'
                      and item.nameVariant != None])
print 'Number of articles in DOAJ-journals where author from relevant \
institution is corresponding author: ', corrAuthNumber, '\n'

# Estimate APCs
print u'Estimated APCs (assume 1285 €): ', corrAuthNumber * 1285, u' €\n'
print u'Estimated APCs (assume 980 €): ', corrAuthNumber * 980, u' €\n'

# Estimate APCs based on DOAJ
withAPC = [item for item in finalList if item.oaStatus == 'gold'
           and item.nameVariant != None and item.APCValue != None]
allCurrencies = set([item.APCCurrency for item in withAPC])
APCAmounts = [[0 for x in range(2)] for y in range(len(allCurrencies))]
h = 0
for curr in allCurrencies:
    APCAmounts[h][0] = sum([int(item.APCValue) for item in withAPC 
                            if item.APCCurrency == curr])
    APCAmounts[h][1] = curr
    h += 1
print 'The DOAJ provides APC-amounts for ', len(withAPC), ' of ', \
corrAuthNumber, ' gold OA-publications where the corresponding author is from \
a relevant institution. These add up to the following amounts:\n'
for h in range(len(allCurrencies)):
    print APCAmounts[h][0], '\t', APCAmounts[h][1], '\n' 

# Save results to file
np.savetxt('output-files/allPubs.txt', [item.arry() for item in finalList],
           delimiter='\t', header = ch, comments = '', fmt='"%s"')


# ------------------------- 12. Basic Statistics ------------------------------

# Figure out how many of each kind of publication for each year, display this
# in a table and save data to file
if doAnalysis == True:
    # Count OA/Hybrid/CorrAuth for every year in dataset
    yearsAll = [int(x.year) for x in finalList if x.year != None]
    yearsOA = [int(x.year) for x in finalList if x.year != None 
               and x.oaStatus == 'gold']
    yearsOACorr = [int(x.year) for x in finalList if x.year != None 
                   and x.nameVariant != None and x.oaStatus == 'gold']
    yearsHybrid = [int(x.year) for x in finalList if x.year != None 
                   and x.oaStatus == 'hybrid']
    yearsGreen = [int(x.year) for x in finalList if x.year != None 
                   and x.oaStatus == 'green']
    years = sorted(list(set(yearsAll)))
    lenyr = len(years)
    pubAll = [None] * lenyr
    pubOA = [None] * lenyr
    pubHybrid = [None] * lenyr
    pubGreen = [None] * lenyr
    percOA = [None] * lenyr
    pubOACorr = [None] * lenyr
    percOACorr = [None] * lenyr
    percHybrid = [None] * lenyr
    percGreen = [None] * lenyr
    ta = PrettyTable(['year', '# Publications', '# Gold', 
                     '# Hybrid', '# Green', '# OA P. + Corr. Author'])
    
    # Create table content
    for i in range(0, lenyr):
        pubAll[i] = yearsAll.count(years[i])
        pubOA[i] = yearsOA.count(years[i])
        pubOACorr[i] = yearsOACorr.count(years[i])
        pubHybrid[i] = yearsHybrid.count(years[i])
        pubGreen[i] = yearsGreen.count(years[i])
        percOA[i] = round(float(100 * pubOA[i])/float(pubAll[i]),1)
        if pubOA[i] > 0:
            percOACorr[i] = round(float(100 * pubOACorr[i])/float(pubOA[i]),1)
        else:
            percOACorr[i] = 0
        if pubAll[i] > 0:
            percHybrid[i] = round(float(100 * pubHybrid[i])/float(pubAll[i]),1)
            percGreen[i] = round(float(100 * pubGreen[i])/float(pubAll[i]),1)
        else:
            percHybrid[i] = 0
            percGreen[i] = 0
        if pubAll[i] > 0:
            i1 = str(pubOA[i]) + ' ~ ' +\
                 str(percOA[i]) + ' %'
            i3 = str(pubHybrid[i]) + ' ~ ' +\
                 str(percHybrid[i]) + ' %'
            i4 = str(pubGreen[i]) + ' ~ ' +\
                 str(percGreen[i]) + ' %'
        else:
            i1 = pubOA[i]
        if pubOA[i] > 0:
            i2 = str(pubOACorr[i]) + ' ~ ' +\
                 str(percOACorr[i]) + ' %'
        else:
            i2 = pubOACorr[i]
        ta.add_row([years[i], pubAll[i], i1, i3, i4, i2])
    ta.add_row(['----', '----', '----', '----', '----', '----'])
    years.append('Sum')
    pubAll.append(sum(pubAll))
    pubOA.append(sum(pubOA))
    pubHybrid.append(sum(pubHybrid))
    pubGreen.append(sum(pubGreen))
    pubOACorr.append(sum(pubOACorr))
    percOACorr.append(round(float(100 * sum(pubOACorr))/float(sum(pubOA)),1))
    percOA.append(round(float(100 * sum(pubOA))/float(sum(pubAll)),1))
    percHybrid.append(round(float(100 * sum(pubHybrid))/float(sum(pubAll)),1))
    percGreen.append(round(float(100 * sum(pubGreen))/float(sum(pubAll)),1))
    
    # Save results to file
    ch = 'year\tNo. Publications\tNo. OA Publications\t% OA Publications\t\
    No. Hybrid Publications\t% Hybrid Publications\tNo. Green Publications\t\
    % Green Publications\tNo. OA Publications + Corr. Author\t\
    % OA Publications with Corr. Auth'
    OAStats = map(list,map(None,*[years, pubAll, pubOA, percOA, pubHybrid,
                                  percHybrid, pubGreen, percGreen, pubOACorr,
                                  percOACorr]))
    np.savetxt('output-files/statistics_OA.txt', OAStats,
               delimiter='\t', header = ch, comments = '', fmt='"%s"')
    
    # Add last line to table in console
    v1 = str(pubOA[-1]) + ' ~ ' + str(percOA[-1]) + ' %'
    v3 = str(pubHybrid[-1]) + ' ~ ' + str(percHybrid[-1]) + ' %'
    v4 = str(pubGreen[-1]) + ' ~ ' + str(percGreen[-1]) + ' %'
    if sum(pubOA) > 0:
        v2 = str(pubOACorr[-1]) + ' ~ ' + str(percOACorr[-1]) + ' %'
    else:
        v2 = sum(pubOACorr)
    ta.add_row(['Sum', pubAll[-1], v1, v3, v4, v2])
    print ta
    print u'Percentages for Gold OA and hybrid and green publications refer \
to the overall number of articles. The percentage for OA publications \
with a corresponding author from a relevant institution refer to the \
number of gold OA publications. ' , str(len(finalList) - pubAll[-1]), \
'publications were not included in this table, because the data provided \
by the database does not contain a year.'

# Do statistics for publishers of OA articles and save results to file
if doAnalysis == True:
    publishersAll = [x.publisher for x in finalList if x.oaStatus == 'gold']
    pAN = float(len(publishersAll))
    publishers = collections.Counter(publishersAll)
    pN = len(publishers)
    print 'Number of publishers: ', pN
    haeuf = publishers.most_common(pN)
    publisherStats = [None] * pN
    tally = 0.
    noPubl = ['x', 'UNKNOWN', 0, 0, 0] 
    tb = PrettyTable(['Rank', 'Publisher', '# Publications', 
                      '% of Publications', 'Cumulative % of Publications'])
    counts = 0
    for i in range(0, pN):
        if haeuf[i][0] == '':
            noPubl[2] += haeuf[i][1]
        elif haeuf[i][0] == None:
            noPubl[2] += haeuf[i][1]
        else:
            tally += haeuf[i][1]
            publisherStats[i] = [counts + 1, haeuf[i][0], haeuf[i][1],
                                 round(100. * haeuf[i][1]/pAN, 2),
                                 round(100. * tally/pAN, 2)]
            counts += 1
            if counts < 21:
                tb.add_row(publisherStats[i])
    tally += noPubl[2]
    noPubl[3] = round(100. * noPubl[2]/pAN, 2)         
    noPubl[4] = round(100. * tally/pAN, 2)
    publisherStats.append(noPubl)
    publisherStats = [item for item in publisherStats if item != None]
    ch = 'Rank\tPublisher\t# Publications\t% Publications\t\
    Cumulative % of Publications'
    np.savetxt('output-files/statistics_goldPublishers.txt', publisherStats,
                   delimiter='\t', header = ch, comments = '', fmt='"%s"')
    print tb
