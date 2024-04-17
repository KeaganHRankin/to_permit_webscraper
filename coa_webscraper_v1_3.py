"""
Keagan Rankin 23-06-2022

-- LAUNCHABLE VERSION --
This file contains v1.3 of the webscraper for City of Toronto's CoA website.
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

# Python modules: time and tkinter for accessing clipboard
from tkinter import Tk
import time
import os
import re

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


#--- THE WEBSCAPER ---

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
        This function is cleaner because it uses find_elements, but raises exceptions after the
        previous page has been looped.
        """
        # XPATH seems to not work, try using even/odd class names instead 
        # Store the elements then loop through child instances.
        # simpler and more stable then 2n + 1 loop.
        results = self.driver.find_elements(By.CLASS_NAME, "propertyAddr")
        
        for re in results:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", re)
            re.click()

            
    def count_results_on_page(self):
        """
        Counts the number of applications on a given page.
        Used for stop condition for looping an entire data table.
        """
        c = self.driver.find_elements(By.CLASS_NAME, "propertyAddr")
        count = len(c)
        
        return count

        
    def return_one_page_soup(self, long):        
        """
        Loops through applications on a given page, returning information in a nice text format.
        loop_one_page() MUST be run BEFORE this function for a given page to open up the applications.
        long = Boolean, whether to print longform stored data at the end.
        """
        
        # Create a list for the address and description text
        a_list = []
        d_list = []
        
        # Loop through the the tr tags in the data table dynamically.
        # We can try using a better XPATH, or use the "detail link" CLASS_NAME and loop through them on the page.
        apps = self.driver.find_elements(By.CLASS_NAME, "detailLink")
        print("[Info] storing addresses and descriptions.")
        
        for app in apps:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", app)
            app.click()
            
            # Store the address. Access the panel and return the enclosed HTML information.
            address_txt = WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.ID, 'main-Property')))
            address_soup = address_txt.get_attribute('innerHTML')
            
            # Use Beautiful soup to return in a nice format
            # How I will output the values.
            address_soup = BeautifulSoup(address_soup, 'html.parser')
            a_text = str(address_soup.get_text())
            a_text_nice = [x.strip().lower() for x in a_text.split('\n')]
            a_text_nice = [x for x in a_text_nice if x]
            
            print("Address instance: {}".format(a_text_nice[0]))
            a_list.append(a_text_nice)
            
            description_txt = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'detail0')))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", description_txt)
            time.sleep(0.5)
            description_soup = description_txt.get_attribute('innerHTML')
            description_soup = BeautifulSoup(description_soup, 'html.parser')
            d_text = str(description_soup.get_text())
            d_text_nice = [x.strip().lower() for x in d_text.split('\n')]
            d_text_nice = [x for x in d_text_nice if x]
            
            # Here we get the application link as the final part of the description list.
            # Using the method get_application_link() defined below.
            a_link = self.get_application_link()
            
            # For description info, we want to store them in a list of dictionaries.
            # to retain the format and compare across instances.
            # Try except this. If we get an IndexError (missing description or other),
            # Then we can fill that row with Nulls and continue.
            try:
                d_dict = {"application number": d_text_nice[1],
                          "application type": d_text_nice[3],
                          "date submitted": d_text_nice[5],
                          "status": d_text_nice[7],
                          "description": d_text_nice[9],
                          "link": a_link
                         }
            except (IndexError):
                print('[Info] missing value, filling w/ null')
                d_dict = {"application number": '',
                          "application type": '',
                          "date submitted": '',
                          "status": '',
                          "description": '',
                          "link": a_link
                         }
            
            #print(d_text_nice)
            d_list.append(d_dict)
            
            # Close the window so we can continue looping through the results.
            # only clickable if the XPATH is called.
            closer = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="printThis"]/div/div[1]/button'))) 
            self.driver.execute_script("arguments[0].scrollIntoView(true);", closer)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", closer)

        # Print total aggregated data.
        if long == True:
            print("address headers:")
            print(a_list)
            print("description dict list:")
            print(d_list)
        
        print("[Info] page scraping complete.")
        return a_list, d_list
        
        
    def get_application_link(self):
        """
        Function gets the application link text when in the application details pop up.
        During webscraping this needs to be embedded into the return_on_page_soup() function.
        """
        # Scroll to the accordion dropdown, open it.
        accordion = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH,'//*[@id="headingAppDtlUrl"]/h2/a')))
        self.driver.execute_script("arguments[0].scrollIntoView(true);", accordion)
        time.sleep(0.1)
        self.driver.execute_script("arguments[0].click();", accordion)
        
        # Copy the app link to the clipboard, return to a variable using built-in python module.
        # https://stackoverflow.com/questions/64720945/python-selenium-code-to-save-text-in-a-variable-from-clipboard-which-is-copied-t
        app_clipboard = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="collapseAppDtlUrl"]/div/div/div/div/div/span/button')))
        self.driver.execute_script("arguments[0].click();", app_clipboard)
        time.sleep(0.1)
        app_clipboard.send_keys(Keys.CONTROL, "c")
        
        # Return the link using tkinter.
        return Tk().clipboard_get()
    
        
        
        
        
# --- FULL SCRAPING FUNCTIONS ---    
def full_scrap_store(webscraper, address):
    """
    testing a full loop of the CoA results table for an address.
    Defines a stoping condition for looping when the final page is reached.
    input -> webscraper instance, an address to search.
    output -> pandas df of unique instances.
    
    Close the webdriver at any time to halt the function, and
    you will get whatever has been stored up to that point.
    """
    # Open the driver
    webscraper.open_webdriver()
    time.sleep(0.1)
    
    # Search an address
    try:
        webscraper.search_address(address)
        time.sleep(0.1)
    except:
        print('[Error] search failed. Something went wrong, try running the function again.')
    
    # Init counters and the dataframe
    i = 0
    res_count = 0
    cols = ['address', 'ward', 'application number', 'application type', 'date submitted', 'status', 'description', 'link']
    output_df = pd.DataFrame(columns = cols)
    
    # Loop through pages
    while True:
        i= i+1
        try:
            # init the stop condition: count elements on a page.
            res = webscraper.count_results_on_page()
            res_count = res_count + res

            # Loop through the pages, skipping pages that hang.
            webscraper.open_one_page()
            time.sleep(0.5)

            # Extract text data for each page, suppress long print.
            ta, td = webscraper.return_one_page_soup(long=False)

            # Append the data to the df, drop exact duplicate rows,
            # reset the index to default increasing integers.
            td_df = pd.DataFrame(td)
            ta_df = pd.DataFrame(ta, columns = ['address','ward'])

            page_data = pd.concat([ta_df, td_df], axis=1)
            output_df = pd.concat([output_df, page_data], axis=0)
            output_df = output_df.drop_duplicates()
            output_df = output_df.reset_index(drop=True)

            # Stop check before proceeding to next page.
            print('Page: {}, Results: {} '.format(i, res))
            if res <= 10:
                print('[Stop Condition] reached final page.')
                break

            webscraper.next_page()
            time.sleep(0.5)
        
        except Exception as e:
            print('[Error] something went wrong. Exception: ')
            print(e)
            break

 
    print('[Info] complete. Summary:')
    print('[Info] Total Addresses looped: {} '.format(res_count))
    print('[Info] Total Unique Results: {}'.format(output_df.shape[0]))
    
    webscraper.close_webdriver(0.1)
    
    return output_df
 

    
# --- MISC FUNCTIONS ---
def scrapped_to_csv(path, output):
    """
    Small function to store scraped data to csv.
    input -> path, the output table for the run.
    checks if path exists then appends.
    """
    print('[Info] printing to {}'.format(path))
    output.to_csv(path, mode='a', header=not os.path.exists(path))