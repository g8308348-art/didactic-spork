from playwright.sync_api import sync_playwright, Page
from .config import TEST_URL, USERNAME, PASSWORD

def login_to_firco(page: Page, url=TEST_URL, username=USERNAME, password=PASSWORD):
    page.goto(url)
    page.fill("input[name='username']", username)
    page.fill("input[name='PASSWORD']", password)
    page.click("input[type='submit'][value='Submit']")
    page.wait_for_load_state("networkidle")
