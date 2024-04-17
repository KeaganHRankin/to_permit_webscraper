# Webscraper for City of Toronto permits webpage
## Main
This repo contains a python package that can systematically webscrap data from the City of Toronto's permits website and dump it to a local csv file. An instance of the webscraper requires some starting address, around which it will perform a maximum radius circular search to get permit applications around that address.

## Usage
The webscraper requires:
- the numpy, pandas, and selenium browser automation python packages
- the version of chromedriver (found here https://chromedriver.chromium.org/) that matches your chromium webbrowser's version, added to the `selenium webdriver` directory

the `coa_webscrapung_clean.ipynb` notebook demonstrates how the webscraper is used. Example outputs are given in the `scraped data` directory.
