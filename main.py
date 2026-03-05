import threading
import time
import os
import requests
from io import BytesIO
from collections import Counter
from PIL import Image
from googletrans import Translator

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from webdriver_manager.chrome import ChromeDriverManager

# -----------------------
# 0️⃣ Helper: Safe page load with retries
# -----------------------
def safe_get(driver, url, retries=3):
    for i in range(retries):
        try:
            driver.get(url)
            return True
        except Exception as e:
            print(f"Attempt {i+1} failed for {url}: {e}")
            time.sleep(5)  # wait before retrying
    return False

# -----------------------
# 1️⃣ Create images folder
# -----------------------
IMAGE_FOLDER = "images"
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# -----------------------
# 2️⃣ Initialize Chrome driver (local testing)
# -----------------------
chrome_options = ChromeOptions()
prefs = {"profile.managed_default_content_settings.images": 2}  # disable images for faster load
chrome_options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
driver.set_page_load_timeout(300)  # Wait up to 300 seconds for page load

if not safe_get(driver, "https://elpais.com/opinion/"):
    print("Failed to load main page. Exiting...")
    driver.quit()
    exit()

time.sleep(5)
print("Current URL:", driver.current_url)

# -----------------------
# 3️⃣ Get first 5 article links
# -----------------------
articles = driver.find_elements(By.CSS_SELECTOR, "h2 a")
article_links = [article.get_attribute("href") for article in articles[:5]]
print("First 5 article links:", article_links)

# -----------------------
# 4️⃣ Initialize translator
# -----------------------
translator = Translator()
translated_titles = []
image_count = 1

# -----------------------
# 5️⃣ Scrape each article
# -----------------------
for link in article_links:
    if not safe_get(driver, link):
        print("Skipping this link due to timeout:", link)
        continue
    time.sleep(4)

    # ----- Title in Spanish -----
    try:
        title_es = driver.find_element(By.TAG_NAME, "h1").text
    except:
        title_es = "No Title Found"
    print("\nArticle Title (Spanish):", title_es)

    # ----- Translate title to English -----
    translation = translator.translate(title_es, src='es', dest='en')
    title_en = translation.text
    translated_titles.append(title_en)
    print("Translated Title (English):", title_en)

    # ----- Download first valid image -----
    try:
        images = driver.find_elements(By.CSS_SELECTOR, "article img")
        img_saved = False
        for img in images[:3]:
            img_url = img.get_attribute("src")
            if img_url and "http" in img_url:
                response = requests.get(img_url)
                image_obj = Image.open(BytesIO(response.content))
                file_name = os.path.join(IMAGE_FOLDER, f"article_{image_count}.jpg")
                rgb_im = image_obj.convert('RGB')
                rgb_im.save(file_name, "JPEG")
                print("Image saved as:", file_name)
                image_count += 1
                img_saved = True
                break
        if not img_saved:
            print("No valid image found for this article")
    except Exception as e:
        print("Error downloading image:", e)

    # ----- Print first 15 paragraphs -----
    paragraphs = driver.find_elements(By.TAG_NAME, "p")
    print("\nArticle Content:\n")
    count = 0
    for p in paragraphs:
        text = p.text.strip()
        if text:
            print(text)
            count += 1
        if count >= 15:
            break

driver.quit()

# -----------------------
# 6️⃣ Analyze translated headers
# -----------------------
all_words = []
for t in translated_titles:
    words = t.lower().replace(",", "").replace(".", "").split()
    all_words.extend(words)

word_counts = Counter(all_words)
print("\nRepeated Words in Translated Headers (more than twice):")
found = False
for word, count in word_counts.items():
    if count > 2:
        print(f"{word}: {count}")
        found = True
if not found:
    print("No words repeated more than twice in the translated headers.")

# -----------------------
# 7️⃣ BrowserStack Cross-Browser Testing (Selenium 4 fix)
# -----------------------
BROWSERSTACK_USERNAME = "6NiFay"       # your BrowserStack username
BROWSERSTACK_ACCESS_KEY = "ieCDRgP4BzAEcaz65CdU"   # your BrowserStack access key

browsers = [
    {"os": "Windows", "os_version": "10", "browser": "Chrome", "browser_version": "latest"},
    {"os": "Windows", "os_version": "10", "browser": "Firefox", "browser_version": "latest"},
    {"os": "OS X", "os_version": "Ventura", "browser": "Safari", "browser_version": "latest"},
    {"os": "iOS", "os_version": "16", "device": "iPhone 14", "real_mobile": True, "browser": "Safari"},
    {"os": "Android", "os_version": "13", "device": "Samsung Galaxy S22", "real_mobile": True, "browser": "Chrome"}
]

def run_browserstack_test(cap):
    driver = None
    try:
        browser_name = cap.get("browser", "").lower()

        if browser_name == "chrome":
            options = ChromeOptions()
        elif browser_name == "firefox":
            options = FirefoxOptions()
        elif browser_name == "safari":
            options = SafariOptions()
        else:
            options = ChromeOptions()  # fallback

        # BrowserStack capabilities
        bstack_options = {
            "os": cap.get("os"),
            "osVersion": cap.get("os_version"),
            "deviceName": cap.get("device"),
            "realMobile": cap.get("real_mobile", False),
            "userName": "rutujadadasahebg_6NiFay",
            "accessKey": "ieCDRgP4BzAEcaz65CdU",
            "buildName": "Python Selenium Build",
            "sessionName": f"Testing {browser_name}"
        }

        options.set_capability("bstack:options", bstack_options)
        options.set_capability("browserName", cap.get("browser"))
        if cap.get("browser_version"):
            options.set_capability("browserVersion", cap.get("browser_version"))

        driver = webdriver.Remote(

            command_executor="https://hub.browserstack.com/wd/hub",
            options=options
        )

        if safe_get(driver, "https://elpais.com/opinion/"):
            print(f"Title on {cap.get('browser')} ({cap.get('os', cap.get('device', ''))}):", driver.title)
        else:
            print(f"Failed to load page on {cap.get('browser')} ({cap.get('os', cap.get('device', ''))})")

    except Exception as e:
        print(f"Error on {cap.get('browser')}: {e}")

    finally:
        if driver is not None:
            driver.quit()

threads = []
for cap in browsers:
    t = threading.Thread(target=run_browserstack_test, args=(cap,))
    threads.append(t)
    t.start()
for t in threads:
    t.join()

print("\nAll images saved in folder:", os.path.abspath(IMAGE_FOLDER))
print("Cross-browser testing completed on BrowserStack (if credentials are set).")