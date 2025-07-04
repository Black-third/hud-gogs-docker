import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import json
import time

# Set up virtual display
os.environ["DISPLAY"] = ":99"

# Set up Selenium
options = webdriver.FirefoxOptions()
driver = webdriver.Firefox(options=options)

# Navigate to the login page
print("Navigating to login page...")
driver.get("http://localhost:3000/user/login")

# Log in
print("Logging in...")
username_input = driver.find_element(By.ID, "user_name")
password_input = driver.find_element(By.ID, "password")
username_input.send_keys("Tadmin")  # Replace with your admin username
password_input.send_keys("admin123")  # Replace with your admin password
password_input.send_keys(Keys.RETURN)

time.sleep(3)

print("Navigating to Admin Users page...")
driver.get("http://localhost:3000/admin/users")

print("Fetching users...")
users = []
rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
print(f"Found {len(rows)} rows in the table.")

for row in rows:
    cols = row.find_elements(By.TAG_NAME, "td")
    print(f"Row data: {[col.text for col in cols]}") 
    users.append({
        "id": cols[0].text,
        "username": cols[1].text,
        "email": cols[2].text,
        "activated": bool(cols[3].find_elements(By.CSS_SELECTOR, "i.fa.fa-check-square-o")),
        "admin": bool(cols[4].find_elements(By.CSS_SELECTOR, "i.fa.fa-check-square-o")),
        "repos": cols[5].text,
        "created": cols[6].text,
    })

# Fetch repositories from /admin/repos
print("Fetching repositories...")
repositories = []
driver.get("http://localhost:3000/admin/repos")
repo_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
print(f"Found {len(repo_rows)} repositories in the table.")

for repo_row in repo_rows:
    repo_cols = repo_row.find_elements(By.TAG_NAME, "td")
    if len(repo_cols) >= 8:  # Ensure we have enough columns
        print(f"Repository row data: {[col.text for col in repo_cols]}")
        
        # Extract repository details with better error handling
        repo_data = {
            "id": repo_cols[0].text,
            "owner": repo_cols[1].text,
            "name": repo_cols[2].text,
            "private": bool(repo_cols[3].find_elements(By.CSS_SELECTOR, "i.fa.fa-lock")),
            "watches": repo_cols[4].text if len(repo_cols) > 4 else "0",
            "stars": repo_cols[5].text if len(repo_cols) > 5 else "0",
            "issues": repo_cols[6].text if len(repo_cols) > 6 else "0",
            "size": repo_cols[7].text if len(repo_cols) > 7 else "0 B",
            "created": repo_cols[8].text if len(repo_cols) > 8 else "",
            "description": ""  # Add description field for restoration
        }
        repositories.append(repo_data)

# Fetch issues for each repository
print("Fetching issues...")
issues = []
for repo in repositories:
    try:
        print(f"Checking issues for {repo['owner']}/{repo['name']}")
        driver.get(f"http://localhost:3000/{repo['owner']}/{repo['name']}/issues")
        time.sleep(2)
        
        
        issue_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        print(f"Found {len(issue_rows)} issue rows for {repo['name']}")
        
        for issue_row in issue_rows:
            try:
                issue_cols = issue_row.find_elements(By.TAG_NAME, "td")
                if len(issue_cols) >= 4:
                    issues.append({
                        "id": issue_cols[0].text.strip(),
                        "title": issue_cols[1].text.strip(),
                        "status": issue_cols[2].text.strip(),
                        "created": issue_cols[3].text.strip(),
                        "repository": repo["name"],
                        "body": ""  
                    })
            except Exception as e:
                print(f"Error processing issue row: {e}")
                continue
                
    except Exception as e:
        print(f"Error fetching issues for {repo['name']}: {e}")
        continue

# Save all data to JSON
print("Saving state to /gogs_state.json...")
with open("/gogs_state.json", "w") as f:
    json.dump({"users": users, "repositories": repositories, "issues": issues}, f, indent=2)

print("✅ Gogs state exported to /gogs_state.json")
print(f"   👥 Users: {len(users)}")
print(f"   📁 Repositories: {len(repositories)}")
print(f"   🐛 Issues: {len(issues)}")

driver.quit()