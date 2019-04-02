[![DOI](https://zenodo.org/badge/68797013.svg)](https://zenodo.org/badge/latestdoi/68797013)

# Share of open access journal articles
We want to analyse an institution's publication output and determine the share of open access articles. To do so we retrieve data from different bibliographic databases and match it with data from the Directory of Open Access Journals (DOAJ) and Unpaywall to identify OA articles in OA jouranls.
The python script described here analyses the retrieved data and produces both total numbers and a list of articles as downloadable files. To identify OA articles in hybrid journals and green OA articles in repositories the Unpaywall API is called. 

## Project description
The python scripts analyses article data and identifies those articles that were published in a) gold open access journals, b) hybrid journals, and c) repositories as green OA. 
The script DOES aggregate, normalise and duplicate check for article data. The script outputs different files (tab-separated txt) for further analysis.
The script DOES NOT retrieve article data from databases -- this has to be done beforehand! Instructions for retrieval of article data are included in the (German) manual.

## How to
See the manual for further information on input/output files and the most important script variables.

A full manual in German is available as [PDF file](/manual.pdf) and [LaTeX project](/manual-tex). See the manual for information on
* how to retrieve article data from different databases (e.g. Web of Science, SciFinder, PubMed),
* how to prepare article data for the python script,
* output files,
* how to add or delete databases from the analysis.

Please note: Some compatibility issues have cropped up since NumPy v1.14 was released last year. The script should work with NumPy v1.12. An updated version of the script should become available during the summer.

## Contribution history
The python script was developed mainly by [Eva Bunge](https://github.com/ebunge) with support from [Michaela Voigt](https://github.com/michaelavoigt). The script is maintained by the Open Access team of TU Berlin University Library.


## Contribute
Contribute to this project by
* committing to the github repository,
* improving the manual or translating it into English (see [LaTeX files here](/manual-tex)),
* contacting us via e-mail (openaccess at ub.tu-berlin.de) to report conceptual flaws and suggest possible improvements, to discuss ways to enhance the script or to let us know what you are using this script for.
Please note that the script is licensed under [BSD-3 clause license](https://opensource.org/licenses/BSD-3-Clause). By contributing you agree to do so under these terms.

## Contact
Please e-mail openaccess at ub.tu-berlin.de.

## License
Some rights reserved, this work is distributed under [BSD-3 clause license](https://opensource.org/licenses/BSD-3-Clause).
See [License](/LICENSE) for more information.
