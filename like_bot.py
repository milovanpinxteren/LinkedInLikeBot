import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import urllib
from langdetect import detect
import signal
import sys
import platform
import os
from dotenv import load_dotenv


load_dotenv()


# Timeout function
def timeout_handler(signum, frame):
    raise Exception("Script Timeout: The script took too long to complete.")

if platform.system() != 'Windows':  # Check for non-Windows OS
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(600)

keywords = [
    "Gebouwbeheer", "Duurzame werkomgeving", "Energiebesparing", "Technologische innovaties",
    "Facilitair management", "Workplace management", "Werkplekoptimalisatie", "Hybride werken",
    "Gezonde werkomgeving", "Wellbeing op kantoor", "Ergonomie", "Voeding op de werkplek",
    "Gezond eten op kantoor", "Stressmanagement op de werkvloer",
    "Afvalmanagement", "Duurzaamheid op de werkvloer", "Klimaatvriendelijk kantoor",
    "Zero waste oplossingen", "F&B manager taken", "Manager People & Workplace",
    "Facility management trends", "HR & facilitair samenwerking", "Tenderprocessen bij cateringbedrijven",
    "Human capital", "Wellbeing", "Duurzaamheid", "Duurzaamheidsmanagement", "Energieneutraliteit", "Milieuvriendelijke catering",
    "Smart building technologie", "Digitalisering in facilitair management", "Circulaire economie", "Bouwinnovatie",
    "Gebouwautomatisering", "IoT in gebouwbeheer", "Robotica in facilitair management", "Flexibele werkplekken",
    "Innovatieve kantoorinrichting", "Preventieve gezondheidszorg op het werk", "Medewerkerstevredenheid",
    "Gezondheidstrends op de werkvloer", "Plantaardige voeding op kantoor", "Clean tech oplossingen",
    "Innovatieve cateringconcepten", "Datagedreven facilitair management", "Ergonomisch ontwerp"
]

excludewords = ['vacature', 'overlijden', 'recruiter', 'student', 'hiring', '#hiring', '#opentowork', 'opentowork', 'internship', 'stage', 'corona', 'trump']

def is_relevant(post_text):
    try:
        lower_text = post_text.lower()
        found_words = [word for word in excludewords if word.lower() in lower_text]
        if found_words:
            print(f"Excludeword(s) found: {found_words}")
            return False
        lang_code = detect(post_text)
        return lang_code == 'nl'
    except Exception as e:
        print(f"Error in relevance check: {e}")
        return False

def run_script():
    try:
        email = os.getenv("EMAIL")
        linkedin_password = os.getenv("PASSWORD")
        xpath_label = os.getenv("XPATH_LABEL")
        options = Options()
        options.headless = False
        driver = webdriver.Chrome(options=options)
        driver.get('https://www.linkedin.com/login')
        time.sleep(2)

        # Log in
        username = driver.find_element(By.ID, 'username')
        password = driver.find_element(By.ID, 'password')
        username.send_keys(email)
        password.send_keys(linkedin_password)
        password.send_keys(Keys.RETURN)
        time.sleep(5)

        for keyword in keywords:
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = f'https://www.linkedin.com/search/results/content/?keywords={encoded_keyword}&origin=FACETED_SEARCH&sid=%3B%3BW&sortBy="date_posted"'
            print(f"\nSearching for posts with keyword: {keyword}")
            driver.get(search_url)
            time.sleep(5)

            for _ in range(2):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(3, 5))

            search_posts = driver.find_elements(By.CLASS_NAME, 'artdeco-card')
            print(f"Found {len(search_posts)} posts for keyword: {keyword}")

            for post in search_posts:
                try:
                    text = post.text
                    if is_relevant(text):
                        print(f"Would like this message from search results: {text.strip()[13:23]}")
                        time.sleep(random.uniform(1, 4))
                        identity_button = post.find_element(By.CSS_SELECTOR, 'button[aria-label^="Menu voor schakelen naar een andere identiteit openen"]')
                        identity_button.click()
                        time.sleep(1)
                        label = driver.find_element(By.XPATH, xpath_label)
                        driver.execute_script("arguments[0].scrollIntoView(true);", label)
                        driver.execute_script("arguments[0].click();", label)
                        time.sleep(2)
                        driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Selectie opslaan"]').click()
                        like_button = post.find_element(By.CSS_SELECTOR, 'button[aria-label="Reageren met interessant"]')
                        like_button.click()
                        time.sleep(random.uniform(0, 3))
                except Exception as e:
                    print(f"Error processing a search post: {e}")
                    continue
    except Exception as e:
        print(f"Error in script: {e}")
    finally:
        driver.quit()
        print("Driver closed successfully.")

if __name__ == '__main__':
    run_script()
