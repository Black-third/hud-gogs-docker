#!/usr/bin/env python3

import os
import time
import re
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

os.environ["DISPLAY"] = ":99"

def create_api_token():
    """Create an API token for the admin user using browser automation"""
    
    print("🔑 Creating API token for admin user...")
    
    # Set up Firefox options for headless operation
    options = Options()
    options.add_argument('--display=:99')
    
    driver = None
    try:
        # Initialize the WebDriver
        driver = webdriver.Firefox(options=options)
        wait = WebDriverWait(driver, 10)
        
        # Step 1: Login
        print("   🌐 Navigating to login page...")
        driver.get("http://localhost:3000/user/login")
        
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "user_name")))
        username_field.send_keys("Tadmin")
        
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys("admin123")
        password_field.send_keys(Keys.RETURN)
        
        print("   ✅ Logged in successfully")
        time.sleep(2)
        
        # Step 2: Navigate to applications page
        print("   🔧 Navigating to applications page...")
        driver.get("http://localhost:3000/user/settings/applications")
        time.sleep(2)
        
        # Step 3: Click "Generate New Token" button to show the form
        print("   🎯 Looking for 'Generate New Token' button...")
        generate_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-panel="#add-access-token-panel"]')))
        generate_button.click()
        print("   ✅ Clicked 'Generate New Token' button - form should now be visible")
        time.sleep(1)
        
        # Step 4: Fill in the token name in the now-visible form
        print("   📝 Filling in token name...")
        token_name_field = wait.until(EC.element_to_be_clickable((By.ID, "name")))
        token_name_field.clear()
        token_name_field.send_keys("api-extraction-token")
        print("   ✅ Token name filled: 'api-extraction-token'")
        
        # Step 5: Click "Generate Token" to submit the form
        print("   🔄 Submitting token generation form...")
        generate_token_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Generate Token')]")))
        generate_token_button.click()
        print("   ✅ Form submitted")
        
        # Step 6: Wait for page to process and extract the token
        time.sleep(3)
        print("   🔍 Looking for generated token...")
        
        # Save page source for debugging
        with open("/token_page_debug.html", "w") as f:
            f.write(driver.page_source)
        
        # Try multiple strategies to find the token
        token = None
        
        # Strategy 1: Look for the specific token display element based on actual HTML structure
        print("   🎯 Looking for token in '.ui.info.message p' element...")
        try:
            # Wait for the info message to appear and then extract token
            info_message = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui.info.message p")))
            token_text = info_message.text.strip()
            
            print(f"   📝 Found info message text: '{token_text}'")
            
            # Gogs tokens are typically 40+ character hex strings
            if token_text and len(token_text) >= 40 and re.match(r'^[a-f0-9]+$', token_text.lower()):
                token = token_text
                print(f"   ✅ Found valid token in info message: {token[:10]}...")
            elif token_text and len(token_text) >= 30:  # Be more lenient with length
                token = token_text
                print(f"   ✅ Found potential token (relaxed validation): {token[:10]}...")
            else:
                print(f"   ⚠️  Found info message but content doesn't look like a token (len={len(token_text)}): '{token_text[:50]}...'")
        except Exception as e:
            print(f"   ⚠️  Could not find .ui.info.message p element: {e}")
        
        # Strategy 2: Fallback - Look for other common token display elements
        if not token:
            print("   🔍 Trying fallback selectors...")
            token_selectors = [
                ".ui.info.message",         # Info message div (get text content)
                ".ui.message p",            # Any message paragraph
                ".ui.positive.message + .ui.info.message",  # Info message after positive message
                "code",                     # Often displayed in <code> tags
                ".ui.message code",         # Success message with code
                "input[readonly]",          # Readonly input fields
                "[data-clipboard-text]",    # Clipboard copy elements
                "pre",                      # Sometimes in preformatted text
                ".token",                   # Token class
            ]
            
            for selector in token_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        # Try different ways to get text
                        text_candidates = [
                            element.text.strip(),
                            element.get_attribute("value"),
                            element.get_attribute("data-clipboard-text"),
                            element.get_attribute("textContent"),
                        ]
                        
                        for text in text_candidates:
                            if not text:
                                continue
                            text = text.strip()
                            # Look for token patterns: 40+ chars, mostly hex (but allow alphanumeric for flexibility)
                            if len(text) >= 30 and re.match(r'^[a-zA-Z0-9]+$', text):
                                token = text
                                print(f"   ✅ Found token using fallback selector '{selector}': {token[:10]}...")
                                break
                        if token:
                            break
                    if token:
                        break
                except Exception as e:
                    continue
        
        # Strategy 2: Look for token patterns in page source
        if not token:
            print("   🔍 Searching page source for token patterns...")
            page_source = driver.page_source
            # Look for 40+ character alphanumeric strings that could be tokens
            token_pattern = r'\b[a-zA-Z0-9]{40,}\b'
            matches = re.findall(token_pattern, page_source)
            
            for match in matches:
                # Skip common false positives
                if not any(skip in match.lower() for skip in ['csrf', 'avatar', 'gravatar', 'octicon', 'commit']):
                    token = match
                    print(f"   ✅ Found token in page source: {token[:10]}...")
                    break
        
        # Strategy 3: Look for tokens in table rows (if they're listed)
        if not token:
            print("   🔍 Checking token list tables...")
            try:
                # Look for table cells that might contain tokens
                table_cells = driver.find_elements(By.CSS_SELECTOR, "td, .ui.label")
                for cell in table_cells:
                    text = cell.text.strip()
                    if len(text) >= 40 and re.match(r'^[a-zA-Z0-9]+$', text):
                        token = text
                        print(f"   ✅ Found token in table: {token[:10]}...")
                        break
            except:
                pass
        
        # Save results
        if token:
            print(f"   🎉 Token generated successfully!")
            print(f"   🔑 Token: {token}")
            
            with open("/api_token.txt", "w") as f:
                f.write(token)
            print("   💾 Token saved to /api_token.txt")
            
            # Also save to a local file for easy access
            try:
                local_token_file = os.path.join(os.path.dirname(__file__), "api_token.txt")
                with open(local_token_file, "w") as f:
                    f.write(token)
                print(f"   � Token also saved to {local_token_file}")
            except:
                pass
            
            return token
        else:
            print("   ⚠️  Could not extract token from page")
            print("   💡 Token may have been created - check the debug file")
            print("   🐛 Page source saved to /token_page_debug.html")
            
            # Take a screenshot for debugging
            driver.save_screenshot("/token_creation_debug.png")
            print("   📸 Screenshot saved to /token_creation_debug.png")
            
            return "TOKEN_CREATED_CHECK_MANUALLY"
            
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        if driver:
            try:
                driver.save_screenshot("/token_creation_error.png")
                print("   📸 Error screenshot saved to /token_creation_error.png")
            except:
                pass
        return None
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    print("🚀 Starting API token creation...")
    token = create_api_token()
    
    if token and token != "TOKEN_CREATED_CHECK_MANUALLY":
        print(f"\n✅ Token creation completed successfully!")
        print(f"🔑 Your API token: {token}")
        print("\n💡 Usage examples:")
        print(f"   curl -H 'Authorization: token {token}' http://localhost:3000/api/v1/user")
        print(f"   curl -H 'Authorization: token {token}' http://localhost:3000/api/v1/user/repos")
        print(f"   curl -H 'Authorization: token {token}' http://localhost:3000/api/v1/repos/Tadmin/ncie/issues")
        print("\n🔧 You can now use this token with the API extraction script!")
    elif token == "TOKEN_CREATED_CHECK_MANUALLY":
        print(f"\n⚠️  Token was likely created but couldn't be extracted automatically")
        print("   💡 Check /token_page_debug.html and /token_creation_debug.png")
        print("   🌐 Or visit http://localhost:3000/user/settings/applications manually")
    else:
        print("\n❌ Token creation failed")
        print("   💡 Check /token_creation_error.png for debugging")
