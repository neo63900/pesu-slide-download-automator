from playwright.sync_api import sync_playwright
import os
import re
from help import select_unit

def sanitize(name: str):
    return re.sub(r"[^\w\- ]", "", name).strip()

# 1. LOGIN
def login(page, username, password):
    page.goto("https://www.pesuacademy.com/Academy/")
    page.fill("#j_scriptusername", username)
    page.fill("input[name='j_password']", password)
    page.click("button.btn.btn-lg.btn-primary.btn-block")
    page.wait_for_load_state("networkidle")
    print("Logged in successfully.")


# 2. SELECT COURSE
def select_course(page):
    page.click("span.menu-name:has-text('My Courses')")
    page.wait_for_selector("select#semesters")
    page.wait_for_selector("table.table.table-hover")

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


# 3. SELECT UNIT FUNCTION
def select_unit(page):
    page.wait_for_selector("#courselistunit li")

    units = page.locator("#courselistunit li a")
    unit_count = units.count()

    names = []
    for i in range(unit_count):
        names.append(units.nth(i).inner_text().strip())

    print("\nAvailable Units:")
    for index, name in enumerate(names, 1):
        print(f"{index}. {name}")

    choice = int(input("\nEnter unit number to open: "))
    selected_unit = units.nth(choice - 1)

    unit_name = sanitize(names[choice - 1])
    selected_unit.click()

    print(f"Opening {unit_name}...")

    return unit_name

# 4. CLICK FIRST SLIDE
def open_first_slide(page):
    page.wait_for_selector("span.pesu-icon-presentation-graphs")
    page.locator("a:has(span.pesu-icon-presentation-graphs)").first.click()
    print("Clicked first slide entry.")

    
# 5. DOWNLOAD SLIDE
def download_slides(page, course_name, unit_name):
    page.wait_for_selector("a:has(span.glyphicon-eye-open)")

    slide_links = page.locator("a:has(span.glyphicon-eye-open)")
    slide_count = slide_links.count()

    print(f"\nFound {slide_count} slides.")

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

        match = re.search(r"loadIframe\('([^']+)", onclick)
        if not match:
            print("Could not extract URL.")
            continue

        pdf_url = "https://www.pesuacademy.com" + match.group(1)
        pdf_url = pdf_url.split("#")[0]

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
        next_number += 1

    print("\nFirst slide downloaded!")


def main():
    username = input("Enter Username: ")
    password = input("Enter Password: ")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        login(page, username, password)
        course_name = select_course(page)
        unit_name = select_unit(page)
        open_first_slide(page)
        download_slides(page, course_name, unit_name)
        
        page.wait_for_timeout(5000)


if __name__ == "__main__":
    main()
