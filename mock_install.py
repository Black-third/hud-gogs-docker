#!/usr/bin/env python3
import os
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

os.environ["DISPLAY"] = ":99"

options = Options()
# options.add_argument("--headless")
driver = webdriver.Firefox(options=options)

print("Navigating to install page...")
driver.get("http://localhost:3000/install")
time.sleep(3)

print("Selecting SQLite3 as database type...")
driver.execute_script("""
    document.querySelector('input#db_type').value = 'SQLite3';
    document.querySelector('div.ui.selection.database.type.dropdown .text').textContent = 'SQLite3';
    document.querySelector('#sql_settings').style.display = 'none';
    document.querySelector('#pgsql_settings').style.display = 'none';
    document.querySelector('#sqlite_settings').style.display = '';
""")
time.sleep(1)


print("Expanding Admin Account Settings section...")
accordion_titles = driver.find_elements(By.CSS_SELECTOR, "div.ui.accordion .title")
found = False
for title in accordion_titles:
    if "Admin Account Settings" in title.text:
        driver.execute_script("arguments[0].scrollIntoView(true);", title)
        title.click()
        found = True
        time.sleep(1)
        break
if not found:
    print("❌ Could not find Admin Account Settings accordion title!")
    driver.save_screenshot("/accordion_not_found.png")
    driver.quit()
    exit(1)


print("Filling admin account settings...")
admin_name = driver.find_element(By.ID, "admin_name")
driver.execute_script("arguments[0].scrollIntoView(true);", admin_name)
admin_name.clear()
admin_name.send_keys("Tadmin")
print("Admin username: Tadmin")

admin_passwd = driver.find_element(By.ID, "admin_passwd")
admin_passwd.clear()
admin_passwd.send_keys("admin123")
print("Admin password: admin123")

admin_confirm = driver.find_element(By.ID, "admin_confirm_passwd")
admin_confirm.clear()
admin_confirm.send_keys("admin123")

admin_email = driver.find_element(By.ID, "admin_email")
admin_email.clear()
admin_email.send_keys("admin@example.com")
time.sleep(0.5)

# Submit the install form
print("Submitting install form...")
driver.find_element(By.CSS_SELECTOR, "button.ui.primary.button").click()
time.sleep(5)

driver.save_screenshot("/install_after_submit.png")
print("✅ Install script finished. Page title:", driver.title)

driver.quit()