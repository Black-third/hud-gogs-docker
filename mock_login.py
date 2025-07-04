import os
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

os.environ["DISPLAY"] = ":99"

options = Options()
driver = webdriver.Firefox(options=options)

print("Navigating to login page...")
driver.get("http://localhost:3000/user/login")
time.sleep(4)

print("Filling in username...")
driver.find_element(By.ID, "user_name").send_keys("Tadmin")
time.sleep(1)
print("Filling in password...")
driver.find_element(By.ID, "password").send_keys("admin123")

print("Submitting form with ENTER...")
driver.find_element(By.ID, "password").send_keys(Keys.RETURN)
time.sleep(5)
driver.save_screenshot("/login_after_submit.png")
print("✅ Login script finished. Page title:", driver.title)

#driver.quit()