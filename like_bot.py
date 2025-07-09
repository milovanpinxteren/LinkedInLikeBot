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
global liked

liked = 0


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


def like_posts_from_interesting_people(driver, xpath_label, max_people=25, max_likes_per_person=3):
    """Visits LinkedIn activity pages of selected people and likes recent posts."""
    people_str = os.getenv("INTERESTING_PEOPLE", "")
    people = [p.strip() for p in people_str.split(",") if p.strip()]
    if not people:
        print("⚠️ No INTERESTING_PEOPLE found in env.")
        return

    selected_people = random.sample(people, min(max_people, len(people)))

    for profile_url in selected_people:
        original_window = driver.current_window_handle

        try:
            activity_url = profile_url.rstrip("/") + "/recent-activity/all/"
            print(f"🔗 Visiting: {activity_url}")
            driver.get(activity_url)
            time.sleep(4)

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            posts = driver.find_elements(By.CSS_SELECTOR, '[data-view-name="feed-full-update"]')
            print(f"Found {len(posts)} posts on {profile_url}")

            for post in posts:
                try:
                    age_element = post.find_element(
                        By.CSS_SELECTOR,
                        'span.update-components-actor__sub-description'
                    )
                    age_text = age_element.text.lower()
                    if any(term in age_text for term in ["maanden geleden", "jaar geleden", "jaren geleden"]):
                        print(f"⏳ Post is too old ({age_text}), skipping user.")
                        break  # posts are chronological, so skip to next person
                except Exception as e:
                    print(f"⚠️ Could not determine age of post: {e}")

                try:
                    post_div = post.find_element(By.CSS_SELECTOR, 'div.feed-shared-update-v2[data-urn]')
                    urn = post_div.get_attribute("data-urn")
                    if not urn.startswith("urn:li:activity:"):
                        continue
                    activity_id = urn.split(":")[-1]
                    post_url = f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}/"
                    print(f"✅ Found post URL: {post_url}")
                    # Open post in new tab
                    driver.execute_script(f"window.open('{post_url}', '_blank');")
                    driver.switch_to.window(driver.window_handles[-1])
                    time.sleep(random.uniform(3, 5))
                    # Like the post via identity
                    identity_button = driver.find_element(
                        By.CSS_SELECTOR,
                        'button[aria-label^="Menu voor schakelen naar een andere identiteit openen wanneer u op deze bijdrage reageert"]'
                    )
                    identity_button.click()
                    time.sleep(1)

                    label = driver.find_element(By.XPATH, xpath_label)
                    driver.execute_script("arguments[0].scrollIntoView(true);", label)
                    driver.execute_script("arguments[0].click();", label)
                    time.sleep(1)

                    driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Selectie opslaan"]').click()
                    time.sleep(1)

                    like_button = driver.find_element(
                        By.CSS_SELECTOR,
                        'button[aria-label="Reageren met interessant"]'
                    )
                    like_button.click()
                    liked += 1
                    print(f"👍 Liked post {liked} for {profile_url}")
                    time.sleep(random.uniform(1, 3))

                    if liked >= max_likes_per_person:
                        break
                except Exception as e:
                    print(f"⚠️ Could not extract URN: {e}")
                finally:
                    # Ensure we always close the tab and return
                    if len(driver.window_handles) > 1:
                        time.sleep(4)
                        driver.close()
                        driver.switch_to.window(original_window)

        except Exception as e:
            print(f"🚫 Failed to process {profile_url}: {e}")


def run_script():
    try:
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
        like_posts_from_interesting_people(driver, xpath_label)

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
                        like_button.click()
                        liked += 1
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
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Liked {liked} posts\n")
        print(f"👍 Total likes this run: {liked}")
        print(f"📄 Log written to: {like_log_file}")

        sys.exit()


if __name__ == '__main__':
    run_script()
