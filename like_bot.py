import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import urllib
from langdetect import detect
import signal
import sys
import platform
import os
from dotenv import load_dotenv

# $env:CLIENT_ENV = "orderpiqr"; C:\Code\LinkedInBot\.venv\Scripts\python.exe C:\Code\LinkedInBot\like_bot.py


env_name = os.getenv("CLIENT_ENV", "default")
env_filename = f".env_{env_name}"
env_path = os.path.join(os.path.dirname(__file__), env_filename)
like_log_file = os.path.join(os.path.dirname(__file__), f"like_log_{env_name}.txt")

if not os.path.exists(env_path):
    raise FileNotFoundError(f"Environment file not found: {env_path}")

print(f'envpath: {env_path}')
load_dotenv(dotenv_path=env_path, override=True)
print(f"✅ Loaded environment: {env_filename}")


# Timeout function
def timeout_handler(signum, frame):
    raise Exception("Script Timeout: The script took too long to complete.")


if platform.system() != 'Windows':  # Check for non-Windows OS
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(600)

keywords_str = os.getenv("KEYWORDS", "")
excludewords_str = os.getenv("EXCLUDEWORDS", "")

# Convert to lists
keywords = [kw.strip() for kw in keywords_str.split(",") if kw.strip()]
excludewords = [ew.strip().lower() for ew in excludewords_str.split(",") if ew.strip()]
random.shuffle(keywords)


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
    global like_count
    try:
        like_count = 0
        email = os.getenv("EMAIL")
        print(f'email: {email}')
        linkedin_password = os.getenv("PASSWORD")
        xpath_label = os.getenv("XPATH_LABEL")

        print(f'xpath_label: {xpath_label}')
        service = Service(ChromeDriverManager().install())
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        options.add_experimental_option("detach", False)
        # options.add_argument(f"--window-size={512},{258}")
        # options.add_argument(f"--window-position={3400},{1800}")
        options.add_argument(f"--disable-extensions")
        options.add_argument(f"--disable-renderer-backgrounding")
        options.page_load_strategy = 'normal'
        driver = webdriver.Chrome(service=service, options=options)

        driver.get('https://www.linkedin.com/login')
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
                        identity_button = post.find_element(By.CSS_SELECTOR,
                                                            'button[aria-label^="Menu voor schakelen naar een andere identiteit openen"]')
                        identity_button.click()
                        time.sleep(1)
                        label = driver.find_element(By.XPATH, xpath_label)
                        driver.execute_script("arguments[0].scrollIntoView(true);", label)
                        driver.execute_script("arguments[0].click();", label)
                        time.sleep(2)
                        driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Selectie opslaan"]').click()
                        like_button = post.find_element(By.CSS_SELECTOR,
                                                        'button[aria-label="Reageren met interessant"]')
                        like_count += 1
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
        with open(like_log_file, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Liked {like_count} posts\n")
        print(f"👍 Total likes this run: {like_count}")
        print(f"📄 Log written to: {like_log_file}")

        sys.exit()


if __name__ == '__main__':
    run_script()
