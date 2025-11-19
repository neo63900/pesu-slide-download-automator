from playwright.sync_api import sync_playwright
import os
import re
import getpass

downloaded_urls = set()

def sanitize(name: str):
    return re.sub(r"[^\w\- ]", "", name).strip()

# 1. LOGIN
def login(page, username, password):
    page.goto("https://www.pesuacademy.com/Academy/")
    page.fill("#j_scriptusername", username)
    page.fill("input[name='j_password']", password)
    page.click("button.btn.btn-lg.btn-primary.btn-block")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    print("Logged in successfully.")

# 2. SELECT COURSE
def select_course(page):
    page.wait_for_selector("span.menu-name:has-text('My Courses')", timeout=15000)
    page.click("span.menu-name:has-text('My Courses')")
    page.wait_for_selector("table.table.table-hover", timeout=15000)

    rows = page.locator("table.table.table-hover tbody tr")
    count = rows.count()

    courses = []
    for i in range(count):
        title = rows.nth(i).locator("td:nth-child(2)").inner_text().strip()
        courses.append(title)

    print("\nAvailable Courses:")
    for index, course in enumerate(courses, 1):
        print(f"{index}. {course}")

    choice = int(input("\nEnter course number to open: "))
    selected_row = rows.nth(choice - 1)
    selected_row.click()

    course_name = sanitize(courses[choice - 1])
    print(f"Opening: {course_name}")

    return course_name

# 4. CLICK FIRST SLIDE
def open_first_slide(page):
    page.wait_for_selector("span.pesu-icon-presentation-graphs", timeout=15000)
    page.locator("a:has(span.pesu-icon-presentation-graphs)").first.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    print("Clicked first slide entry.")

# 5. DOWNLOAD SLIDES
def download_slides(page, course_name, unit_name, downloaded_urls):
    page.wait_for_timeout(800)
    page.wait_for_selector(".link-preview a", timeout=15000)

    slide_links = page.locator(".link-preview a")
    slide_count = slide_links.count()
    print(f"\nFound {slide_count} files.")

    folder = f"{course_name} {unit_name}"
    os.makedirs(folder, exist_ok=True)

    existing = [
        int(f.split(".")[0]) for f in os.listdir(folder)
        if f.split(".")[0].isdigit()
    ]
    next_number = max(existing) + 1 if existing else 101

    for i in range(slide_count):
        link = slide_links.nth(i)
        onclick = link.get_attribute("onclick")
        matches = re.findall(r"loadIframe\('([^']+)", onclick)

        if not matches:
            print("Could not extract URL.")
            continue

        for url in matches:
            pdf_url = "https://www.pesuacademy.com" + url
            pdf_url = pdf_url.split("#")[0]

            if pdf_url in downloaded_urls:
                print(f"Skipping already downloaded: {pdf_url}")
                continue

            print(f"\nDownloading: {pdf_url}")
            response = page.request.get(pdf_url)
            if response.status != 200:
                print(f"Failed ({response.status})")
                continue

            filename = f"{next_number}.pdf"
            filepath = os.path.join(folder, filename)

            with open(filepath, "wb") as f:
                f.write(response.body())

            print(f"Saved → {filepath}")
            downloaded_urls.add(pdf_url)
            next_number += 1
            page.wait_for_timeout(300)

# 6. PAGE NAVIGATION + SLIDE DOWNLOAD
def navigate_through_pages(page, course_name, unit_name, downloaded_urls):
    while True:
        page.wait_for_selector(".coursecontent-navigation-area a.pull-right", timeout=15000)
        next_button = page.locator(".coursecontent-navigation-area a.pull-right")
        label = next_button.inner_text().strip()
        print("\nCurrent button:", label)

        # Open slides tab
        slides_tab = page.locator("#contentType_2")
        slides_tab.click()
        page.wait_for_timeout(600)

        no_slides = page.locator(
            "h2:text('No Slides Content to Display')"
        )

        if no_slides.is_visible():
            print("No slides available. Skipping download.")
        else:
            download_slides(page, course_name, unit_name, downloaded_urls)

        if "Back to Units" in label:
            print("Reached 'Back to Units'. Stopping navigation.")
            break

        next_button.click()
        print("Clicked next… waiting for next page load")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

# MAIN
def main():
    username = input("Enter Username: ")
    password = getpass.getpass("Enter Password: ")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())

        login(page, username, password)
        course_name = select_course(page)
        unit_name = select_unit(page)
        open_first_slide(page)
        download_slides(page, course_name, unit_name, downloaded_urls)
        navigate_through_pages(page, course_name, unit_name, downloaded_urls)

        page.wait_for_timeout(2000)

if __name__ == "__main__":
    main()
