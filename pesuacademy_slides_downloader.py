from playwright.sync_api import sync_playwright
import os
import re

def sanitize(name: str):
    return re.sub(r"[^\w\- ]", "", name).strip()


def main():
    username = input("Enter Username: ")
    password = input("Enter Password: ")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 1. Open PESU Academy login page
        page.goto("https://www.pesuacademy.com/Academy/")

        # 2. Enter username and password
        page.fill("#j_scriptusername", username)
        page.fill("input[name='j_password']", password)

        # 3. Click login button
        page.click("button.btn.btn-lg.btn-primary.btn-block")
        page.wait_for_load_state("networkidle")

        # 5. Click "My Courses"
        page.click("span.menu-name:has-text('My Courses')")
        page.wait_for_selector("table.table.table-hover")

        # 6. Extract Course Titles
        rows = page.locator("table.table.table-hover tbody tr")
        count = rows.count()

        courses = []
        for i in range(count):
            title = rows.nth(i).locator("td:nth-child(2)").inner_text().strip()
            courses.append(title)

        # 7. User input to select course
        print("\nAvailable Courses:")
        for index, course in enumerate(courses, 1):
            print(f"{index}. {course}")
        choice = int(input("\nEnter course number to open: "))
        selected_row = rows.nth(choice - 1)
        selected_row.click()
        course_name = sanitize(courses[choice - 1])

        print(f"Opening: {course_name}")

        # Keep window open a moment
        page.wait_for_timeout(5000)


if __name__ == "__main__":
    main()




