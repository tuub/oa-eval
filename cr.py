# -*- coding: utf-8 -*-
#!/usr/bin/env python2.7
import json
import urllib2
import re
import numpy as np

# INPUT: List of Document-objects
# OUTPUT: List of OA Document-objects with license information added & list of
#         document objects that need to be send to DOAJ-API due to missing 
#         ISSNs
def askCR(nonOA):
    dochs = nonOA
    counts = 0
    
    # Define base url and strings to identify relevant licenses
    baseurl = 'http://api.crossref.org/works/'
    myfavlic = "creativecommons.org"
    myfavlic2 = "authorchoice"
    
    results = []
    toDOAJ = []
    c1, c2, c3, c4, c5, c6 = 0, 0, 0, 0, 0, 0
    for doid in dochs:
        counts += 1
        if counts % 1000 == 0:
            print 'Queried ', counts, ' articles'
        doi = doid.DOI
        myurl = baseurl + doi
        field = ''
        try:
            response = urllib2.urlopen(myurl)
            cr_data = json.load(response)
            cr_data_msg = cr_data["message"]
            
            # Check if relevant license can be found in the field "license"
            if cr_data_msg.has_key("license"):
                field = 'license'
                cr_data_license = cr_data_msg["license"]
                for lic_element in cr_data_license:
                    if lic_element.has_key("URL"):
                        if re.search(myfavlic, lic_element["URL"]):
                            doid.lizenz = lic_element["URL"]
                            if doid.ISSN == None:
                                doid.ISSN = cr_data_msg["ISSN"][0]
                                toDOAJ.append(doid)
                            c1 += 1
                        elif re.search(myfavlic2, lic_element["URL"]):
                            doid.lizenz = lic_element["URL"]
                            if doid.ISSN == None:
                                doid.ISSN = cr_data_msg["ISSN"][0]
                                toDOAJ.append(doid)
                            c4 += 1
                            
            # Check if relevant license can be found in the field "assertion"
            elif cr_data_msg.has_key("assertion"):
                field = 'assertion'
                cr_data_assertion = cr_data_msg["assertion"]
                for ass_element in cr_data_assertion:
                    if ass_element.has_key("URL"):
                        if re.search(myfavlic, ass_element["URL"]):
                            doid.lizenz = ass_element["URL"]
                            if doid.ISSN == None:
                                doid.ISSN = cr_data_msg["ISSN"][0]
                                toDOAJ.append(doid)
                            c2 += 1
                        elif re.search(myfavlic2, ass_element["URL"]):
                            doid.lizenz = ass_element["URL"]
                            if doid.ISSN == None:
                                doid.ISSN = cr_data_msg["ISSN"][0]
                                toDOAJ.append(doid)
                            c5 += 1
                            
            # Check if relevant license can be found in the field "message"
            else:
                cr_data_msg_str = str(cr_data_msg)
                field = 'message'
                if re.search(myfavlic, cr_data_msg_str):
                    doid.lizenz = myfavlic
                    if doid.ISSN == None:
                        doid.ISSN = cr_data_msg["ISSN"][0]
                        toDOAJ.append(doid)
                    c3 += 1
                elif re.search(myfavlic2, cr_data_msg_str):
                    doid.lizenz = myfavlic2
                    if doid.ISSN == None:
                        doid.ISSN = cr_data_msg["ISSN"][0]
                        toDOAJ.append(doid)
                    c6 += 1
            results.append([doi, doid.ISSN, doid.lizenz, field])
            
        # Handle errors
        except urllib2.HTTPError, err:
            if err.code == 404:
                results.append([doi, doid.ISSN,
                                '', 'Error 404'])
    ch = 'DOI\tISSN\tLicense\tField'
    np.savetxt('CRResults.txt', results, delimiter='\t', header = ch,
               comments = '', fmt="%s")
    print
    print 'CrossRef Statistics:'
    print 'Number of DOIs for which requested license #1 was included in',\
          ' json lement LICENSE :', c1
    print 'Number of DOIs for which requested license #1 was included in',\
          ' json element ASSERTION :', c2
    print 'Number of DOIs for which requested license #1 was included in',\
          ' json element MESSAGE :', c3
    print 
    print 'Number of DOIs for which requested license #2 was included in',\
          ' json element LICENSE :', c4
    print 'Number of DOIs for which requested license #2 was included in',\
          ' json element ASSERTION :', c5
    print 'Number of DOIs for which requested license #2 was included in',\
          ' json element MESSAGE :', c6
    print 
    c = c1 + c2 + c3
    cc = c4 + c5 + c6
    print 'Total number of DOIs with requested license #1 included :', c
    print 'Total number of DOIs with requested license #2 included :', cc
    print 'Total number of DOIs with one of the requested licenses',\
          ' included :', c + cc
    print
    
    return [x for x in dochs if x.lizenz != None], toDOAJ


# INPUT: List of document objects
# OUTPUT: List of document objects for which the ISSN is registered with DOAJ
def askDOAJ(toDOAJ):
    baseurl = 'https://doaj.org/api/v1/search/journals/issn%3A'
    results = []
    positives = []
    for item in toDOAJ:
        # Create URLs for single GET REQUESTS
        # ISSN is registered with DOAJ if response["total"] == 1
        myurl = baseurl + str(item.ISSN)
        try:
            response = urllib2.urlopen(myurl)
            doaj = json.load(response)
            doaj_total = str(doaj["total"])
            results.append([item.ISSN, doaj_total])
            if doaj_total == '1':
                item.checks += 'DOAJ=1'
                positives.append(item)
        except  urllib2.HTTPError, err:
            if err.code == 404:
                results.append([item.ISSN, 'Error 404'])
    ch = 'ISSN\tResponse'
    np.savetxt('DOAJResults.txt', results, delimiter='\t', header = ch,
               comments = '', fmt="%s") 
    return positives