from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re
import os

# Initialize Chrome driver
chrome_options = webdriver.ChromeOptions()

proxy = '' # Add proxy if needed
options = {
    'proxy': {
        'http': proxy,
        'https': proxy,
        'no_proxy': 'localhost,127.0.0.1'
    }
}

driver = webdriver.Chrome(options=chrome_options)


try:
    keyword = "destinasi wisata di daerah istimewa yogyakarta"
    url = f'https://www.google.com/maps/search/{keyword}/'

    driver.get(url)
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "form:nth-child(2)"))).click()
    except Exception:
        pass
    scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
    last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)

    while True:
        driver.execute_script("arguments[0].scrollBy(0, arguments[0].scrollHeight)", scrollable_div)
        time.sleep(3)
        new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
        if new_height == last_height:
            break
        last_height = new_height    
    # Scroll back to the top
    driver.execute_script("window.scrollTo(0, 0)")

    # Click on each div element and extract data
    items = driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction]')
    results = []
    
    for item in items:
        data = {}
        driver.execute_script("arguments[0].scrollIntoView();", item)
        time.sleep(3)
        try:
            data['title'] = item.find_element(By.CSS_SELECTOR, ".fontHeadlineSmall").text
        except Exception:
            pass
        try:
            data['link'] = item.find_element(By.CSS_SELECTOR, "a").get_attribute('href')
        except Exception:
            data['link'] = None

        try:
            data['website'] = item.find_element(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction] div > a').get_attribute('href')
        except Exception:
            data['website'] = None

        try:
            rating_text = item.find_element(By.CSS_SELECTOR, '.fontBodyMedium > span[role="img"]').get_attribute('aria-label')
            parts = rating_text.split(' ')
            stars = float(parts[0].replace(",", "."))
            reviews = int(parts[2].replace(".", ""))
            data['stars'] = stars
            data['reviews'] = reviews

        except Exception:
            pass
        
        try:
            text_content = item.text
            phone_pattern = r'((\+?\d{1,2}[ -]?)?(\(?\d{3}\)?[ -]?\d{3,4}[ -]?\d{4}|\(?\d{2,3}\)?[ -]?\d{2,3}[ -]?\d{2,3}[ -]?\d{2,3}))'
            matches = re.findall(phone_pattern, text_content)

            phone_numbers = [match[0] for match in matches]
            unique_phone_numbers = list(set(phone_numbers))

            data['phone'] = unique_phone_numbers[0] if unique_phone_numbers else None   
        except Exception:
            pass

        try:
            category_element = item.find_element(By.CSS_SELECTOR, '.UaQhfb.fontBodyMedium div.W4Efsd div.W4Efsd span span')
            data['category'] = category_element.text
        except Exception:
            data['category'] = None
        try:
            item.click()  # Click on the div element
            time.sleep(3)
            data['address'] = driver.find_element(By.CSS_SELECTOR, 'div.Io6YTe').text
            close_button = driver.find_element(By.CSS_SELECTOR, 'button.VfPpkd-icon-LgbsSe.yHy1rc.eT1oJ.mN1ivc')
            close_button.click()

            #add regency
            pattern = r"(Kabupaten [\w\s]+|Kota [\w\s]+)"
            matches = re.findall(pattern, data['address'])
            data['regency'] = matches[0] if matches else None
        except Exception:
            data['address'] = None

        if data.get('title'):
            print(data)
            results.append(data)

    # Save results to a JSON file
    file_name = os.path.basename(__file__)
    file_name_without_extension = os.path.splitext(file_name)[0]
    output_file = f'{file_name_without_extension}.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

finally:
    driver.quit()
