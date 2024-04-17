"""
Keagan Rankin 21-06-2022

This file contains v1.1 of the webscraper for City of Toronto's CoA website.
The webscraper returns information about applications within the maximum radius of
a given address. It dumps them into a csv for filtering, EDA, NLP, etc.
Read the object and functions that perform the full loop for more information.

This webscraper can be used to find relevant drawings for takeoff, and theoretically
could be used to gridsearch the entire city.

dependencies: 

selenium 4.1.5

beautifulsoup4 4.11.1

numpy 1.21.5

pandas 1.4.2
"""

# Data
import numpy as np
import pandas as pd

import re
import time

# Webscraping
# Selenium
#basics
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

#wait tools
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# chaining actions
from selenium.webdriver.common.action_chains import ActionChains

# selecting items from a dropdown.
from selenium.webdriver.support.ui import Select

# Beautiful Soup
from bs4 import BeautifulSoup



class CoAWebscraper:
    """
    A webscraper that scrapes data from Toronto's
    Committee of Adjustments web portal.
    """
    
    # Initialize with the webdriver and link.
    def __init__(self, path, webaddress):
        """
        instantiate the path to the webdriver
        and the address of the portal
        """
        # Vars def by user
        self.path = path
        self.web_address = webaddress
        
        # Vars for storing webscraped data.
        self.addresses = []
        self.descriptions = []
    
    
    def open_webdriver(self):
        """
        Opens the webdriver to the correct web_address.
        """
        # Open the chrome driver
        path = "selenium webdriver/chromedriver.exe"
        self.driver = webdriver.Chrome(self.path)

        # Get the CoA website and print the website title
        self.driver.get(self.web_address)
        

    def close_webdriver(self, delay):
        """
        CLoses the webdriver after a given time delay
        """
        time.sleep(delay)
        self.driver.quit()
        print('[Info] driver closed :)')
        
        
    def next_page(self):
        """
        Proceeds to the next page of the CoA results table (DataTables_Table_0).
        """
        # Find the next button by class, scroll to it, click
        next_button = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, "DataTables_Table_0_next")))
        self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        next_button.click()
        

    def search_address(self, address):
        """
        Searches for the given Toronto address in the webdriver. Opens the search results table.
        """
        # First maximize the search radius under the more_filters dropdown.
        more_filters = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.ID, "mapSearchBtn1"))).click()
        search_radius = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, "radius")))
        actions = ActionChains(self.driver)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", search_radius)
        time.sleep(0.5)
        select = Select(self.driver.find_element_by_id('radius'))
        select.select_by_value('1000')
        
        # Get Search Bar: ID>NAME>CLASS[i]
        search = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, "address")))
        self.driver.execute_script("arguments[0].scrollIntoView(true);", search)
        time.sleep(0.5)

        # Search for address and hit enter
        search.send_keys(address)
        search.send_keys(Keys.RETURN)
        
        # Scroll to make sure the buttons are in view. Find the dropdown button. Click on it https://stackoverflow.com/questions/41744368/scrolling-to-element-using-webdriver
        show_results = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, "showResultsLink")))
        self.driver.execute_script("arguments[0].scrollIntoView(true);", show_results)
        #time.sleep(0.8)
        show_results = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.ID, "showResultsLink")))
        show_results.click()


    def loop_first_instance(self):
        """
        Performs one instance of the scrape loop. Used for testing/tweaking scraper.
        """
        # Scroll to make sure the buttons are in view. Find the dropdown button. Click on it.
        show_results = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, "showResultsLink")))
        self.driver.execute_script("arguments[0].scrollIntoView(true);", show_results)
        time.sleep(0.5)
        show_results.click()

        # Click on the first address and open the hyperlink of the application.
        address = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.ID, "195314"))).click()
        application = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.CLASS_NAME, "detailLink"))).click()

        # Store the address. Access the panel and return the enclosed HTML information.
        address = WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.ID, 'main-Property')))
        address_soup = address.get_attribute('innerHTML')
        print(address_soup)

        description = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'detail0')))
        self.driver.execute_script("arguments[0].scrollIntoView(true);", description)
        time.sleep(0.5)
        description_soup = description.get_attribute('innerHTML')
        print(description_soup)

        # Close the window so we can continue looping through the results.
        # only clickable if the XPATH is called.
        closer = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="printThis"]/div/div[1]/button'))) 
        self.driver.execute_script("arguments[0].scrollIntoView(true);", closer)
        self.driver.execute_script("arguments[0].click();", closer)
    
        
    def open_one_page(self):
        """
        Loops through the first page of the results table, opening all development applications.
        """
        # Try using XPATH and loop through child instances under the noticeSearchResults results table id.
        # TRY LOOPING THROUGH COUNT*2+1 OF RESULT INSTANCES
        c = self.driver.find_elements(By.XPATH, "//tbody/tr")
        count = len(c)
        
        for i in range(1,count*2+1): #This was 21 before, but trying to make it dynamic for the last page <10 to still work.
            # Click on the i-th address and open the hyperlink of the application.
            # use formatted string and the XPATH to get the ith class propertyeven or property odd.
            # You need 2n loops through tags, probably because of the 2nd tr tag.
            address = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, "//tbody/tr[{}]".format(i))))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", address)
            address.click()
            
            
    def count_results_on_page(self):
        """
        Counts the number of applications on a given page.
        Used for stop condition for looping an entire data table.
        """
        c = self.driver.find_elements(By.XPATH, "//tbody/tr")
        count = len(c)
        
        return count

        
    def return_one_page_soup(self):        
        """
        Loops through applications on a given page, returning information in a nice text format.
        loop_one_page() MUST be run BEFORE this function for a given page to open up the applications.
        """
        # Loop through the the tr tags in the data table. 11 SHOULD BE MADE DYNAMIC.
        for i in range(1,11):
            # Click on i-th detail link, get the description and other info in the soup, extract it.
            application = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="DataTables_Table_0"]/tbody/tr[{}]/td/table/tbody/tr/td[1]/a'.format(2*i))))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", application)
            application.click()
            
            # Store the address. Access the panel and return the enclosed HTML information.
            address_txt = WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.ID, 'main-Property')))
            address_soup = address_txt.get_attribute('innerHTML')
            
            # Use Beautiful soup to return in a nice format
            # How I will output the values.
            address_soup = BeautifulSoup(address_soup, 'html.parser')
            a_text = str(address_soup.get_text())
            a_text_nice = [x.strip() for x in a_text.split('\n')]
            a_text_nice = [x for x in a_text_nice if x]
            
            print(a_text_nice)
            
            description_txt = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'detail0')))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", description_txt)
            time.sleep(0.5)
            description_soup = description_txt.get_attribute('innerHTML')
            description_soup = BeautifulSoup(description_soup, 'html.parser')
            d_text = str(description_soup.get_text())
            d_text_nice = [x.strip() for x in d_text.split('\n')]
            d_text_nice = [x for x in d_text_nice if x]
            
            print(d_text_nice)
            
            # Close the window so we can continue looping through the results.
            # only clickable if the XPATH is called.
            closer = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="printThis"]/div/div[1]/button'))) 
            self.driver.execute_script("arguments[0].scrollIntoView(true);", closer)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", closer)
        
        


    
def full_loop_test(webscraper, address):
    """
    testing a full loop of the CoA results table for an address.
    Defines a stoping condition for looping when the final page is reached.
    """
    # Open the driver
    webscraper.open_webdriver()
    time.sleep(0.1)
    
    # Search an address
    webscraper.search_address(address)
    time.sleep(0.1)
    
    i = 0
    res_count = 0
    # Loop through pages
    while True:
        i= i+1 
        try:
            # for the stop condition: count elements on a page.
            res = webscraper.count_results_on_page()
            res_count = res_count + res
            
            # Loop through the pages, skipping pages that hang.
            webscraper.open_one_page()
            time.sleep(0.5)
            
            # Stop check before proceeding to next page.
            print('Page: {}, Results: {} '.format(i, res))
            if res < 10:
                print('[Stop Condition] reached final page.')
                break
                
            webscraper.next_page()
            time.sleep(0.5)
                      
        except:
            print('[Error] page {} hanging, skipped.'.format(i))
            webscraper.next_page()
 
    print('[Info] Total Results: {} '.format(res_count))
    print('[Info] complete.')
    webscraper.close_webdriver(0.1)
   