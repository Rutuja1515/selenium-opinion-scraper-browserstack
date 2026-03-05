from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from googletrans import Translator
import requests
import os
import time
from collections import Counter
import threading


translator = Translator()

image_folder = "images"
os.makedirs(image_folder, exist_ok=True)

spanish_titles = []
translated_titles = []


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

driver.get("https://elpais.com/opinion/")
time.sleep(5)

print("\nOpened El País Opinion page\n")

articles = driver.find_elements(By.CSS_SELECTOR, "h2 a")

print("Total articles found:", len(articles))

article_links = []

for article in articles[:5]:

    title = article.text
    link = article.get_attribute("href")

    spanish_titles.append(title)

    print("\nTitle (Spanish):", title)
    print("Link:", link)

    article_links.append(link)


for i, link in enumerate(article_links):

    driver.get(link)
    time.sleep(4)

    print("\n==============================")

    try:
        title = driver.find_element(By.TAG_NAME, "h1").text
        print("Article Title (Spanish):", title)
    except:
        print("Title not found")

    paragraphs = driver.find_elements(By.TAG_NAME, "p")

    print("\nContent:")
    for p in paragraphs[:10]:
        print(p.text)

       # Download Image

    try:
        image = driver.find_element(By.CSS_SELECTOR, "figure img")
        image_url = image.get_attribute("src")

        img_data = requests.get(image_url).content

        file_path = f"{image_folder}/article_{i+1}.jpg"

        with open(file_path, "wb") as f:
            f.write(img_data)

        print("Image saved:", file_path)

    except:
        print("No image found")

    print("==============================")

driver.quit()

# Translate Titles

print("\n\nTranslated Headers (Spanish → English)\n")

for title in spanish_titles:

    translated = ""

    for attempt in range(3):

        try:
            translation = translator.translate(title, src='es', dest='en')
            translated = translation.text
            break

        except:
            print("Translation retry...")
            time.sleep(2)

    if translated == "":
        translated = "Translation failed"

    translated_titles.append(translated)

    print("Spanish:", title)
    print("English:", translated)
    print("--------------------------------")

# Word Frequency

all_words = []

for title in translated_titles:
    words = title.lower().split()
    all_words.extend(words)

word_counts = Counter(all_words)

print("\nRepeated Words in Translated Headers (more than twice):")

found = False

for word, count in word_counts.items():
    if count > 2:
        print(word, ":", count)
        found = True

if not found:
    print("No words repeated more than twice.")

# BrowserStack Testing

BROWSERSTACK_USERNAME = "YOUR_USERNAME"
BROWSERSTACK_ACCESS_KEY = "YOUR_ACCESS_KEY"

def run_browserstack_test(browser):

    try:

        if browser == "chrome":

            caps = {
                "browserName": "Chrome",
                "browserVersion": "latest",
                "bstack:options": {
                    "os": "Windows",
                    "osVersion": "11",
                    "sessionName": "Chrome Test"
                }
            }

        elif browser == "firefox":

            caps = {
                "browserName": "Firefox",
                "browserVersion": "latest",
                "bstack:options": {
                    "os": "Windows",
                    "osVersion": "11",
                    "sessionName": "Firefox Test"
                }
            }

        elif browser == "edge":

            caps = {
                "browserName": "Edge",
                "browserVersion": "latest",
                "bstack:options": {
                    "os": "Windows",
                    "osVersion": "11",
                    "sessionName": "Edge Test"
                }
            }

        elif browser == "android":

            caps = {
                "browserName": "Chrome",
                "bstack:options": {
                    "deviceName": "Samsung Galaxy S22",
                    "osVersion": "12.0",
                    "realMobile": "true",
                    "sessionName": "Android Test"
                }
            }

        elif browser == "ios":

            caps = {
                "browserName": "Safari",
                "bstack:options": {
                    "deviceName": "iPhone 13",
                    "osVersion": "15",
                    "realMobile": "true",
                    "sessionName": "iOS Test"
                }
            }

        driver = webdriver.Remote(
            command_executor=f"https://{BROWSERSTACK_USERNAME}:{BROWSERSTACK_ACCESS_KEY}@hub-cloud.browserstack.com/wd/hub",
            desired_capabilities=caps
        )

        driver.get("https://elpais.com/opinion/")

        print(f"Running test on {browser}")
        print("Page title:", driver.title)

        driver.quit()

    except Exception as e:
        print(f"Error on {browser}:", e)


browsers = ["chrome", "firefox", "edge", "android", "ios"]

threads = []

for browser in browsers:

    t = threading.Thread(target=run_browserstack_test, args=(browser,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("\nAll images saved in folder:", os.path.abspath(image_folder))
print("Cross-browser testing completed.")