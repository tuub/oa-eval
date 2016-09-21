#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

####################################################################################
# This work is distributed under a BSD 3-Clause License.
# license terms see https://opensource.org/licenses/BSD-3-Clause
# developed mainly by Eva Bunge (ORCiD:0000-0002-5587-5934, github.com/ebunge) 
# with support from Michaela Voigt (ORCiD:0000-0001-9486-3189, github.com/michaelavoigt)
# maintained by the Open Access team of TU Berlin University Library
#################################################################################### 

import numpy as np
import collections
import cPickle as pickle
import weakref
from prettytable import PrettyTable
import time
import graphics as gr
import cr

t = time.time()

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
# 1: Contact to contact the CrossRef API to crossreference your article data 
#    with the licence information available at CrossRef. The CrossRef data is
#    then saved in a file 'CRResults', so that it can be used at a later date 
#    without having to contact the API again.
# 2: Load the previously saved CrossRef data from 'CRResults'
# 0: Disable the feature completely.
contactCR = 1

# Decide what to do when a corresponding/first author of a publication can't be
# determined manually. Possible values:
# 1: Write all articles to a file (docsToBeChecked.txt) for which it is
#    impossible to determine the corresponding/first author automatically.
#    Once you have determined which aricles have a first/corresponding author
#    from a relevant institution, save the data in a tab-delimited, utf8
#    encoded text-file called 'docsChecked.txt', with the following format:
#    each line corresponds to an article and the three columns contain (in this
#    order): title, DOI, name of institution (which should be spelled identical
#    to the name of the institution as set up in this script)
# 2: Load this information into the script and have it included in the final
#    results and the statistic.
# 0: Disable this feature completely.
checkToDo = 1


# ----------------- 2. Setting up Classes and Functions -----------------------

# Set up class for institutions
class inst(object):
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
    collaborators = None
    nameVariant = None
    doajSubject = None
    publisher = None
    lizenz = None
    checks = ''
    def __init__(self, authors, title, DOI, journal, ISSN, eISSN, year,
                 affiliations, corrAuth, eMail, subject, funding, dbID):
        self.authors = authors
        self.title = title
        self.DOI = DOI
        self.journal = journal
        self.ISSN = ISSN
        self.eISSN = eISSN
        self.year = year
        self.affiliations = affiliations
        self.corrAuth = corrAuth
        self.eMail = eMail
        self.subject = subject
        self.funding = funding
        self.dbID = dbID
    def konsonanten(self):
        d = ' '.join([''.join([item for item in self.authors if item in vokale])\
                    .lower()[0:3],
                  ''.join([item for item in self.title if item in vokale])\
                    .lower()[0:19]])
        return d
    def arry(self):
        return [self.authors, self.title, self.DOI, self.journal, self.ISSN, 
                self.eISSN, self.year, self.affiliations, self.corrAuth,
                self.nameVariant, self.eMail, self.subject, self.doajSubject,
                self.funding, self.publisher, self.lizenz,
                self.dbID, self.checks, self.collaborators]

# Function that takes consonants from a title and turns them into a string
# INPUT: title of a publication (string)
# OUTPUT: first twenty consonants of the title (string)
def kons(title):
    d = ''.join([item for item in title if item in vokale]).lower()[0:19]
    return d

# Function that takes data in WoS-format and transforms the data into a list of
# Document-objects.
# INPUT: (list of records as described in section 4, database ID (integer))
# OUTPUT: list of Document-objects
def wosFormat(wosRecords, ind):
    records = []
    i = 0
    with open(wosRecords, 'rU') as f:
        for line in f:
            if i == 0:
                newDoc = Document('', '', None, None, None, 
                                  None, None, '', None, None, None, None, ind)
                i += 1
            lengths = len(line)
            if line[0:2] != '  ':
                kuerzel = line[0:2]
            if line[0:2] == 'TI':
                newDoc.title = line[3:lengths].strip('\n').strip('\r')
            elif line[0:2] == 'SO':
                newDoc.journal = line[3:lengths].strip('\n').strip('\r')
            elif line[0:2] == 'PY':
                newDoc.year = line[3:lengths].strip('\n').strip('\r')
            elif line[0:2] == 'SN':
                if '-' not in line:
                    vorl = line[3:lengths].strip('ISSN ').strip('\n').strip('\r')
                    newDoc.ISSN = vorl[0:4] + '-' + vorl[4:8]
                elif ',' in line:
                    newDoc.ISSN = line.strip('ISSN ').strip('\n').strip('\r')[0:9]
                else:
                    newDoc.ISSN = line[3:lengths].strip('ISSN ').strip('\n').strip('\r')
            elif line[0:2] == 'DI':
                newDoc.DOI = line[3:lengths].strip('\n').strip('\r')
            elif line[0:2] == 'AF':
                newDoc.authors = line[3:lengths].strip('\n').strip('\r')
            elif kuerzel == 'AF' and line[0:2] == '  ':
                newDoc.authors += '; '
                newDoc.authors += line[3:lengths].strip('\n').strip('\r')
            elif line[0:2]  == 'FN':
                records.append(newDoc)
                newDoc = Document('', '', None, None, None, 
                                  None, None, '', None, None, None, None, ind)
        records.append(newDoc)
    return records

# Checks a given name of an institution against a list of approved name variants.
# INPUT: (text string with name of an institution, database ID)
# OUTPUT: (bool stating if instition is part of list, name of institution (string))
def listCheck(institution, ide):
    val = [None] * len(institutions)
    variant = None
    for i in range(0, len(val)):
        if ide in [dbWoS.idNummer, dbSF.idNummer]:
            namensVar = institutions[i].nameVar
        else:
            namensVar = institutions[i].nameVar1
        instList = [item for item in namensVar]
        valu = [None] * len(instList)
        for j in range(0, len(instList)):
            valu[j] = all(word in institution for word in instList[j])
        if any(valu):
            variant = institutions[i].name
            val[i] = True
            break
    return (any(val), variant)

# Function that takes data in PubMed-format and transforms it into list of Documents.
# INPUT: (list of records as described in section 4, database ID (integer))
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
                newDoc = Document('', '', None, None, None, 
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

# List of consonants
vokale = ('b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r',
          's', 't', 'v', 'w', 'x', 'y', 'z', 'B', 'C', 'D', 'F', 'G', 'H', 'J',
          'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Y', 'Z')

# Duplicate check
# This function takes a set of data (= masterList) and compares incoming new 
# data with it. All duplicates are removed from the new data which is then
# added to the masterList. This action is repeated for each database.
# Comparisons are done via DOI-matching and then title/author-matching.
# doiList = list that contains all DOIs from masterList.
# konsMast = a list of strings which consist of the first four consonants of
# the authors' names and the first twenty consonants of the title for the data
# in the masterlist.
# INPUT: (iterating integer, list containing article data as described 
#         in section 4, list of DOIs (strings), list of strings for
#         title/author-matching)
# OUTPUT: list containing Documents with duplicates removed
def dubletten(iterates, masterList, dois, kons):
    if iterates == 1:
        nowList = contentSF
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
          ' - number of records removed via DOI-matching: ', \
          i-j
    nowList = [item for item in nowList if item.authors != None 
                                        and item.konsonanten() not in f]
    k = len(nowList)
    print datenbanken[iterates].name, \
          ' - number of records removed via title/author-matching: ', \
          j-k
    print datenbanken[iterates].name, \
          ' - number of records added to masterList: ', \
          k
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
TU = inst('TU', TUnames)

# Charité
Cnames = [['Charit', 'Univ'], ['Campus', 'Virchow', 'Berlin'],
          ['Campus', 'Franklin', 'Berlin'], ['Charit', 'Berlin']]
Charite = inst('Charité', Cnames)

# FU
FUnames = [['Berlin','FU'], ['Berlin','Free','Univ'], ['Berlin','Frei','Univ']]
FU = inst('FU', FUnames)

# HU
HUnames = [['Berlin', 'HU'], ['Berlin', 'Humboldt', 'Univ']]
HU = inst('HU', HUnames)

# UdK
UdKnames = [['Univ', 'Arts', 'Berlin'], ['Univ', 'Kunst', 'Berlin'],
            ['Berlin', 'UdK']]
UdK = inst('UdK', UdKnames)

# Beuth
Bnames = [['Beuth', 'Berlin']]
Beuth = inst('Beuth', Bnames)

# HTW
HTWnames = [['HTW', 'Berlin'], ['Tech', 'Wirt', 'Berlin']]
HTW = inst('HTW', HTWnames)

# HWR
HWRnames = [['HWR','Berlin'], ['Wirt','Recht','Berlin']]
HWR = inst('HWR', HWRnames)

# Alice Salomon
ASHnames = [['Alice','Salomon','Berlin'], ['ASH','Berlin']]
ASH = inst('ASH', ASHnames)

#Create list of institutions
institutions = [x for x in inst.instances]

# Set up differing name variants for PubMed data if needed
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
                ['Berlin Inst Technol'],
                ['Technical University Berlin'],
                ['Technische Universitaet de Berlin'],
                ['Technical University of Berlin'],
                ['Berlin University of Technology']]


# ------------- 4. Read in Text Files and Extract Information -----------------

# Set up databases
dbWoS = Database('Web of Science', 1)
dbSF = Database('SciFinder', 2)
dbPM = Database('PubMed', 3)
dbTEMA = Database('TEMA', 4)
dbInspec = Database('Inspec', 5)
dbIEEE = Database('IEEE', 6)
dbPQ = Database('ProQuest', 7)
dbBSC = Database('Business Source Complete', 9)
dbGf = Database('GeoRef', 10)
dbCAB = Database('CAB Abstracts', 11)
dbCIN = Database('CINAHL', 12)
dbEB = Database('EBSCO', 13)
dbEm = Database('Embase', 14)
dbLisa = Database('LISA', 15)
dbScopus = Database('Scopus', 16)
dbSD = Database('SportDiscus', 17)

# List the databases
datenbanken = [x for x in Database.instancesdb]

# Read in database contents from text-files
if doReadIn == True:
# Read in the 'Web of Science' file and extract the relevant information. 
    contentWoS = []
    with open('wos20xx.txt') as f:
        ic = 0
        for line in f:
            fields = line.split('\t')
            if ic > 0:
                contentWoS.append(Document(fields[1], fields[8], fields[54],
                                           fields[9], fields[38], fields[39], 
                                           fields[44], fields[22], fields[23],
                                           fields[24], fields[58], fields[27],
                                           dbWoS.idNummer))
            else:
                ic += 1
    dbWoS.content = contentWoS
    print 'Finished reading in Web of Science'
    
    # Read in the 'SciFinder' files and extract the relevant information.
    contentSF = []
    with open('sf20xx.txt', 'rU') as f:
        ic = 0
        for line in f:
            fields = line.split('\t')
            if ic > 0:
                contentSF.append(Document(fields[6], fields[3], 
                                          fields[49].strip('\n').strip('\r'),
                                          fields[17], fields[15], None, 
                                          fields[22], None, fields[11], 
                                          None, fields[9], None,
                                          dbSF.idNummer))
            else:
                ic += 1
    dbSF.content = contentSF
    print 'Finished reading in SciFinder'
    
    # Read in 'PubMed' file and extract relevant information.
    dbPM.content = pubmedFormat('pubmed20xx.txt', dbPM.idNummer)
    print 'Finished reading in PubMed'
    
    # Read in 'TEMA' file and extract relevant information.
    dbTEMA.content = wosFormat('tema20xx.txt', dbTEMA.idNummer)   
    print 'Finished reading in TEMA'
    
    # Read in 'Inpsec' file and extract relevant information.
    contentInspec = []
    with open('inspec20xx.txt') as f:
        ic = 0
        for line in f:
            fields = line.split('\t')
            if ic > 0:
                contentInspec.append(Document(fields[6], fields[5], fields[-5],
                                              fields[12], fields[-6], None, 
                                              fields[13], fields[-21], None, 
                                              None, None, None,
                                              dbInspec.idNummer))
            else:
                ic += 1
    dbInspec.content = contentInspec
    print 'Finished reading in Inspec'
    
    # Read in 'IEEE' file and extract relevant information.
    dbIEEE.content = wosFormat('ieee20xx.txt', dbIEEE.idNummer)
    print 'Finished reading in IEEE'
    
    # Read in 'ProQuest' file and extract relevant information.
    dbPQ.content = wosFormat('pq20xx.txt', dbPQ.idNummer) 
    print 'Finished reading in ProQuest'
    
    # Read in 'Business Source Complete' file and extract relevant information.
    dbBSC.content = wosFormat('bsc20xx.txt', dbBSC.idNummer)
    print 'Finished reading in Business Source Complete'
    
    # Read in 'GeoRef' file and extract relevant information.   
    dbGf.content = wosFormat('gf20xx.txt', dbGf.idNummer)
    print 'Finished reading in GeoRef'
    
    # Read in 'CAB Abstracts' file and extract relevant information.
    dbCAB.content = wosFormat('cab20xx.txt', dbCAB.idNummer)
    print 'Finished reading in CAB Abstracts'
    
    # Read in 'CINAHL' file and extract relevant information.
    dbCIN.content = wosFormat('cinahl20xx.txt', dbCIN.idNummer)
    print 'Finished reading in CINAHL'
    
    # Read in 'EBSCO' file and extract relevant information.
    dbEB.content = wosFormat('ebsco20xx.txt', dbEB.idNummer)
    print 'Finished reading in EBSCO'
    
    # Read in 'Embase' file and extract relevant information.
    dbEm.content = wosFormat('embase20xx.txt', dbEm.idNummer)
    print 'Finished reading in Embase'
    
    # Read in 'LISA' file and extract relevant information.
    dbLisa.content = wosFormat('lisa20xx.txt', dbLisa.idNummer)
    print 'Finished reading in LISA'
    
    # Read in 'Scopus' file and extract relevant information.
    dbScopus.content = wosFormat('scopus20xx.txt', dbScopus.idNummer)
    print 'Finished reading in Scopus'
    
    # Read in 'SportDiscus' file and extract relevant information.
    dbSD.content = wosFormat('sd20xx.txt', dbSD.idNummer)
    print 'Finished reading in Sport Discus'
    
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
    print 'Final number of publications: ', len(finalList)
elif doReadIn == False:
    with open('finalList', "rb") as f:
        finalList = pickle.load(f)

# Check for duplicates within a database via DOI-matching
seen = set()
doubles = []
for x in finalList:
    if x.DOI != '' and x.DOI != None:
        if x.DOI not in seen:
            seen.add(x.DOI)
        else:
            doubles.append(x)
for item in doubles:
    if item in finalList:
        finalList.remove(item)


# -------------------------- 6. Add DOAJ Data ---------------------------------

# Reads in the file with the data from DOAJ and crossreferences it with the 
# ISSNs and eISSNs from the database data.
doaj = np.loadtxt('doaj.txt', dtype = 'string', comments = '$#',
                  skiprows = 1, delimiter = '\t',
                  usecols = (3, 4, 0, 56, 11, 12, 5, 44))
print 'Finished reading in DOAJ data'
issns = collections.Counter(doaj[:,0])
eissns = collections.Counter(doaj[:,1])
oaList = [item for item in finalList 
          if (item.ISSN != '' and (item.ISSN in eissns or item.ISSN in issns))
          or (item.eISSN != '' and (item.eISSN in eissns or item.eISSN in issns))]
print 'Finished identifying OA articles'

# Add information about the subject, publisher and journal licence
for item in oaList:
    if item.ISSN != '' and item.ISSN != None:
        j = np.where(doaj == item.ISSN)
        item.doajSubject = str(doaj[j[0],3]).strip('[').strip(']').strip("'")
        item.publisher = str(doaj[j[0],6]).strip('[').strip(']').strip("'")
        item.lizenz = str(doaj[j[0],7]).strip('[').strip(']').strip("'")
    if item.ISSN == '' and item.eISSN != None:
        k = np.where(doaj == item.eISSN)
        item.doajSubject = str(doaj[k[0],3]).strip('[').strip(']').strip("'")
        item.publisher = str(doaj[j[0],6]).strip('[').strip(']').strip("'")
        item.lizenz = str(doaj[j[0],7]).strip('[').strip(']').strip("'")


# ----------------------- 7. Add CrossRef Data --------------------------------

# Take non-OA articles that have a DOI and send them to the CrossRef API to 
# see if there's information about a Creative Commons license. 
# For items that are found to be OA after all, the attribute 'checks' is set to 
# 'License added via CrossRef'. These are added to the list of OA publications 'oaList'
if contactCR == 1:
    print 'Begin querying CrossRef'
    nonOA = [item for item in finalList
             if item not in oaList 
             and item.DOI != None
             and item.DOI != '']
    dochOA, toDOAJ = cr.askCR(nonOA)
    for item in dochOA:
        item.lizenz = str(item.lizenz)
        item.ISSN = str(item.ISSN)
        item.checks += 'Licence added via CrossRef'
    print 'Finished querying CrossRef'
    oaDOAJ = cr.askDOAJ(toDOAJ)
    with open('CRResults', "wb") as f:
        pickle.dump(dochOA, f)
    with open('CRResultsDOAJ', "wb") as f:
        pickle.dump(oaDOAJ, f)
        print 'Saved CrossRef data to file "CRResults"'
    for item in oaDOAJ:
        if 'DOAJ=1' in item.checks:
            oaList.append(item)
    hybrid = [item for item in dochOA if item not in oaList]
elif contactCR == 2:
    dochOA = []
    oaDOAJ = []
    with open('CRResultsDOAJ', "rb") as f:
        oaDOAJ = pickle.load(f)
    with open('CRResults', "rb") as f:
        print 'Load CrossRef data from file'
        dochOA = pickle.load(f)
    for item in dochOA:
        item.lizenz = str(item.lizenz)
        item.ISSN = str(item.ISSN)
    cL1 = len([x for x in dochOA if "creativecommons.org" in x.lizenz])
    cL2 = len([x for x in dochOA if "authorchoice" in x.lizenz])
    print 'Number of DOIs for which CC license was found via CrossRef: ', cL1
    print 'Number of DOIs for which ACS license was found via CrossRef: ', cL2
    for item in dochOA:
        if len(item.authors) > 200:
            item.authors = item.authors[0:200]  
    for item in oaDOAJ:
        if len(item.authors) > 200:
            item.authors = item.authors[0:200]
    for item in oaDOAJ:
        if 'DOAJ=1' in item.checks:
            oaList.append(item)
    hybrid = [item for item in dochOA if item not in oaList]


# -- 8. Find out if Authors from relevant Institutions = First/Corr. Author ---

# Adds information about found name variants and shortens author-list
for item in finalList:
    if item.dbID in [dbWoS.idNummer, dbSF.idNummer, dbPM.idNummer]:
        i, j = listCheck(item.corrAuth, item.dbID)
        if i == True:
            item.nameVariant = j
    if len(item.authors) > 200:
        item.authors = item.authors[0:200]

# Find publications from WoS, SciFinder and PubMed for which a name variant of
# a relevant institution was found.
oaWoS = [item for item in oaList if item.dbID == dbWoS.idNummer]
oaWoS = [item for item in oaWoS if item.nameVariant != None]
oaWoS += [item for item in oaList if item.dbID == dbSF.idNummer]
pubMedTest = [item for item in oaList if item.dbID == dbPM.idNummer 
                                      and item.nameVariant != None]
if len(pubMedTest) > 0:
    oaWoS += pubMedTest

# Write list of articles that need to be checked by hand into a file
# 'docsToBeChecked.txt'
toCheck = [item for item in oaList if item.dbID not in [dbWoS.idNummer, 
                                                        dbSF.idNummer, 
                                                        dbPM.idNummer]]
ch = 'authors\ttitle\tDOI\tjournal\tISSN\teISSN\tyear\taffiliations\t\
corresponding author\tfound name variant\te-mail\tsubject\t\
DOAJ subject\tfunding\tpublisher\tlizenz\tdatabaseID\tnotes\tcollaborators'
if checkToDo == 1:
    np.savetxt('docsToBeChecked.txt', [item.arry() for item in toCheck], 
                delimiter='\t', header = ch, comments = '', fmt="%s")
# Read in articles that were checked by hand and were found to have a 
# first/corresponding author from a relevant institution. Add those articles
# to the list of OA articles with first/corresponding author from a relevant
# institution.
elif checkToDo == 2:
    addDocs = []
    doiList = [x.DOI for x in toCheck if x.DOI != None]
    titles1 = [x.konsonanten()[4:] for x in toCheck]
    dontknow = []
    with open('docsChecked.txt') as f:
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
            idDoc.checks += 'Checked by hand.'
            oaWoS.append(idDoc)
        elif kons(item[0]) in titles1:
            idDoc = next((x for x in toCheck 
                          if x.konsonanten()[4:] == kons(item[0])), None)
            idDoc.nameVariant = item[2]
            idDoc.checks += 'Checked by hand.'
            idDoc.DOI = item[1]
            oaWoS.append(idDoc)
        else:
            dontknow.append(item)
    np.savetxt('docsCheckedCantFind.txt', [item for item in dontknow], 
                delimiter='\t', header = 'Title\tDOI\tAffiliation',
                comments = '', fmt="%s")

# Write final results
finalNumber = len(oaWoS)
print 'Overall number of articles in DOAJ-journals: ', len(oaList)
if contactCR in [1, 2]:
    print 'Overall number of hybrid articles: ', len(hybrid)
print 'Number of articles in DOAJ-journals where author from relevant \
institution is corresponding author: ', finalNumber


# ----------- 9. Estimate the APCs and print results to file ------------------

# use 1) other average values or 29 add further options for APCs estimation by
# 1) replacing default values, e.g.
# change print output 'Estimated APCs (assume 1285 €)' to $amount
# change default value used for multiplication to 'finalNumber * $amount'
# 2) adding a new line, e.g.
# print 'Estimated APCs (assume 1360 €): ', finalNumber * 1360, ' €\n'

print 'Estimated APCs (assume 1285 €): ', finalNumber * 1285, ' €\n'
print 'Estimated APCs (assume 980 €): ', finalNumber * 980, ' €\n'
np.savetxt('allPubs.txt', [item.arry() for item in finalList], delimiter='\t', 
           header = ch, comments = '', fmt="%s")
np.savetxt('allOAPubs.txt', [item.arry() for item in oaList], delimiter='\t', 
           header = ch, comments = '', fmt="%s")
np.savetxt('allOAPubsWithCorrAuthor.txt', [item.arry() for item in oaWoS],
            delimiter='\t', header = ch, comments = '', fmt="%s")
if contactCR in [1, 2]:
    np.savetxt('hybridArticles.txt', [item.arry() for item in hybrid],
               delimiter='\t', header = ch, comments = '', fmt="%s")



# ------------------------- 10. Statistics ------------------------------------

# Figure out how many of each kind of publication for each year, display this
# in a table and save data to file
if doAnalysis == True:
    yearsAll = [int(x.year) for x in finalList if x.year != None]
    yearsOA = [int(x.year) for x in oaList if x.year != None]
    yearsOACorr = [int(x.year) for x in oaWoS if x.year != None]
    if contactCR in [1, 2]:
        yearsHybrid = [int(x.year) for x in hybrid if x.year != None]
    else:
        yearsHybrid = []
    years = sorted(list(set(yearsAll)))
    lenyr = len(years)
    pubAll = [None] * lenyr
    pubOA = [None] * lenyr
    pubHybrid = [None] * lenyr
    percOA = [None] * lenyr
    pubOACorr = [None] * lenyr
    percOACorr = [None] * lenyr
    percHybrid = [None] * lenyr
    ta = PrettyTable(['year', '# Publications', '# Gold OA', 
                     '# Hybrid', '# OA P. + Corr. Author'])
    for i in range(0, lenyr):
        pubAll[i] = yearsAll.count(years[i])
        pubOA[i] = yearsOA.count(years[i])
        pubOACorr[i] = yearsOACorr.count(years[i])
        pubHybrid[i] = yearsHybrid.count(years[i])
        percOA[i] = round(float(100 * pubOA[i])/float(pubAll[i]),1)
        percOACorr[i] = round(float(100 * pubOACorr[i])/float(pubOA[i]),1)
        percHybrid[i] = round(float(100 * pubHybrid[i])/float(pubAll[i]),1)
        if pubAll[i] > 0:
            i1 = str(pubOA[i]) + ' ~ ' +\
                 str(percOA[i]) + ' %'
            i3 = str(pubHybrid[i]) + ' ~ ' +\
                 str(percHybrid[i]) + ' %'
        else:
            i1 = pubOA[i]
        if pubOA[i] > 0:
            i2 = str(pubOACorr[i]) + ' ~ ' +\
                 str(percOACorr[i]) + ' %'
        else:
            i2 = pubOACorr[i]
        ta.add_row([years[i], pubAll[i], i1, i3, i2])
    ta.add_row(['----', '----', '----', '----', '----'])
    years.append('Sum')
    pubAll.append(sum(pubAll))
    pubOA.append(sum(pubOA))
    pubHybrid.append(sum(pubHybrid))
    percOA.append(round(float(100 * sum(pubOA))/float(sum(pubAll)),1))
    pubOACorr.append(sum(pubOACorr))
    percOACorr.append(round(float(100 * sum(pubOACorr))/float(sum(pubOA)),1))
    percHybrid.append(round(float(100 * sum(pubHybrid))/float(sum(pubAll)),1))
    OAStats = map(list,map(None,*[years, pubAll, pubOA, percOA, pubHybrid,
                                  percHybrid, pubOACorr, percOACorr]))
    ch = 'year\tNo. Publications\tNo. OA Publications\t% OA Publications\t\
    No. Hybrid Publications\t% Hybrid Publications\t\
    No. OA Publications + Corr. Author\t% OA Publications with Corr. Auth'    
    np.savetxt('statistics_OA.txt', OAStats,
               delimiter='\t', header = ch, comments = '', fmt="%s")
    v1 = str(pubOA[-1]) + ' ~ ' + str(percOA[-1]) + ' %'
    v3 = str(pubHybrid[-1]) + ' ~ ' + str(percHybrid[-1]) + ' %'
    if sum(pubOA) > 0:
        v2 = str(pubOACorr[-1]) + ' ~ ' + str(percOACorr[-1]) + ' %'
    else:
        v2 = sum(pubOACorr)
    ta.add_row(['Sum', pubAll[-1], v1, v3, v2])
    print ta
    print 'Prozentsätze für Gold OA und hybride Artikel beziehen sich ',\
    'jeweils auf die Gesamtzahl aller Arikel. Die Prozentangabe für OA ',\
    'Artikel mit Autor von einer relevanten Institution beziehen sich auf ',\
    'goldene OA Artikel. ' , str(len(finalList) - pubAll[-1]), 'Artikel ',\
    'wurden in diese Auswertung nicht mit einbezogen, da die von der ',\
    'Datenbank gelieferten Daten keine Jahresangabe enthalten.'
    
    # Create graphical output
    ### please note: if you run this script on a Mac the following 3 lines 
    ### have been known to cause trouble (OS X  10.9.5, Python 2.7.11). 
    ### Uncomment if you run into errors
    gr.threebar(years[0:-1], pubAll[0:-1], pubOA[0:-1], pubOACorr[0:-1],
                pubHybrid[0:-1])
    gr.lineplot1(years, percOA, percOACorr)
    gr.otherbar(years, pubAll, pubOA, pubOACorr)

# Do statistics for publishers of OA articles and save results to file
if doAnalysis == True:
    publishersAll = [x.publisher for x in oaWoS]
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
    np.savetxt('statistics_publishers.txt', publisherStats,
                   delimiter='\t', header = ch, comments = '', fmt="%s")
    print tb

print time.time() - t
