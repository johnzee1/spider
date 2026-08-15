from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def main():
    page = Path(__file__).with_name("dynamic_demo.html").as_uri()
    driver = webdriver.Chrome()
    try:
        driver.get(page)
        driver.find_element(By.ID, "load-button").click()
        wait = WebDriverWait(driver, 5)
        items = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".news-item"))
        )
        for item in items:
            print(item.text)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
