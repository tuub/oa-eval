overview on 
* expected input files
* output files produced by scripts
* most important variables used in the main script (not a complete list!)

## script files

|  script file | note                           |
| ------------ | ------------------------------ |
| cr.py        | calling CrossRef and DOAJ APIs |
| graphics.py  | visualizing results            |
| main.py      | main script                    |

## script variables

|  script variable | note                                                                              |
| ---------------- | --------------------------------------------------------------------------------- |
| checkToDo        | (de)activiate script feature: check corresponding author manually                 |
| contactCR        | (de)activiate script feature: calling CrossRef and DOAJ APIs                      |
| doAnalysis       | (de)activiate script feature: data analysis (statistics, plots)                   |
| doReadIn         | (de)activiate script feature: read in article data from database retrieval        |
| finalList        | list of all identified articles                                                   |
| hybrid           | list of OA articles in hybrid journals                                            |
| oaList           | list of OA articles in OA journals                                                |
| oaWoS            | list of articles for which author of analysed institution is corresponding author |

## input files

|  input file     | note                                                                                |
| --------------- | ----------------------------------------------------------------------------------- |
| docsChecked.txt | list of articles for which affiliation of corresponding author was checked manually |
| doaj.txt        | DOAJ metadata                                                                       |
| bsc20xx.txt     | article data Business Source Complete                                               |
| cab20xx.txt     | article data CAB Abstracts                                                          |
| cinahl20xx.txt  | article data CINAHL                                                                 |
| ebsco20xx.txt   | article data Academic Search Premier (EBSCO)                                        |
| embase20xx.txt  | article data Embase                                                                 |
| gf20xx.txt      | article data GeoRef                                                                 |
| ieee20xx.txt    | article data IEEE Xplore                                                            |
| inspec20xx.txt  | article data InSpec                                                                 |
| lisa20xx.txt    | article data LISA                                                                   |
| pq20xx.txt      | article data ProQuest Social Sciences                                               |
| pubmed20xx.txt  | article data PubMed                                                                 |
| scopus20xx.txt  | article data Scopus                                                                 |
| sd20xx.txt      | article data Sport Discus                                                           |
| sf20xx.txt      | article data SciFinder                                                              |
| tema20xx.txt    | article data TEMA                                                                   |
| wos20xx.txt     | article data Web of Science                                                         |

## output files

|  output file                | note                                                                                         |
| --------------------------- | ---------------------------------------------------------------------------------------- |
| allOAPubs.txt               | list of all OA articles                                                                  |
| allOAPubsWithCorrAuthor.txt | list of articles for which author of analysed institution is corresponding author        |
| allPubs.txt                 | list of all articles                                                                     |
| CRResults                   | internal file: data for CrossRef API call and results                                    |
| CRResults.txt               | list of DOIs for CrossRef API call and results                                           |
| CRResultsDOAJ               | internal file: data for CrossRef API call and results (journals' OA status)              |
| DOAJResults.txt             | list of ISSNs for DOAJ API call and results (journals' OA status)                        |
| docstobechecked.txt         | list of articles for which affiliation of corresponding author has to be checked manually|
| finalList                   | internal file: article data                                                              |
| hybridArticles.txt          | list of OA articles in hybrid journals                                                   |
| statistics_OA.txt           | statistics on analysed articles                                                          |
| statistics_publishers.txt   | frequency distribution of OA articles per publisher                                      |
| Figure_OAIncrease.png       | plot: growth in OA articles                                                              |
| Figure_OANumbers.png        | plot: analysed (OA) articles                                                             |
| Figure_OAShare.png          | plot: development of OA share                                                            |