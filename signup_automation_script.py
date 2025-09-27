from playwright.sync_api import sync_playwright, expect
from mailslurp_client import Configuration, ApiClient, InboxControllerApi, WaitForControllerApi
import re, random

# Setup MailSlurp
API_KEY = "057348b203ea800068d293330506c14cae3215f3de50a2caf6d0a3cd516d733c"

def get_new_inbox():
    """mailslurp config"""
    config = Configuration()
    config.api_key["x-api-key"] = API_KEY
    with ApiClient(config) as api_client:
        inbox_controller = InboxControllerApi(api_client)
        inbox = inbox_controller.create_inbox()
        return inbox

def wait_for_otp(inbox_id, timeout=60000):
    config = Configuration()
    config.api_key["x-api-key"] = API_KEY
    with ApiClient(config) as api_client:
        wait_for_controller = WaitForControllerApi(api_client)
        email = wait_for_controller.wait_for_latest_email(
            inbox_id=inbox_id,
            timeout=timeout,
            unread_only=True
        )
        print(f"Email received: {email.subject}")

        matches = re.findall(r"\d{6}", email.body or "")

        if not matches:
            raise Exception("Could not find OTP in email.")
        otp = matches[4]
        print(f"Using OTP: {otp}")

        return otp

# randomly generate number for unique phone number
def generate_phone():
    return "980" + str(random.randint(1000000, 9999999))

# main
def test_signup_with_mailslurp():
    inbox = get_new_inbox()
    print(f"Created inbox: {inbox.email_address}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Go to login page
        page.goto("https://authorized-partner.netlify.app/login")

        # Click sign up link
        page.get_by_role("link", name="Sign Up").click()
        expect(page).to_have_url("https://authorized-partner.netlify.app/register")

        # Click check box
        page.get_by_role("checkbox").click()
        page.get_by_role("button", name="continue").click()
        expect(page).to_have_url("https://authorized-partner.netlify.app/register?step=setup")

        # Fill signup form
        page.fill("input[name='firstName']", "demo")
        page.fill("input[name='lastName']", "test")
        phone = generate_phone()
        page.fill("input[name='phoneNumber']", phone)
        page.get_by_placeholder("Enter Your Email").type(inbox.email_address)
        page.fill("input[name='password']", "Demotest1*")
        page.fill("input[name='confirmPassword']", "Demotest1*")
        page.get_by_role("button", name="Next").click()

        # Wait for OTP email
        otp = wait_for_otp(inbox.id)
        # print(f"OTP received: {otp}")

        # Enter OTP
        page.fill("input[autocomplete='one-time-code']", otp)
        page.get_by_role("button", name="Verify Code").click()

        expect(page).to_have_url("https://authorized-partner.netlify.app/register?step=details")

        # Agency details form
        page.fill("input[name='agency_name']", "xyz ltd")
        page.fill("input[name='role_in_agency']", "consultancy")
        page.fill("input[name='agency_email']", "demo@gmail.com")
        page.fill("input[name='agency_website']", "xyz.org")
        page.fill("input[name='agency_address']", "putalisadak")

        page.get_by_role("combobox").click()
        page.locator("div", has_text="Nepal").first.click()

        page.get_by_role("button", name="Next").click()

        expect(page).to_have_url("https://authorized-partner.netlify.app/register?step=professional-experience")

        # Professional experience form
        page.get_by_role("combobox").click()
        page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")

        page.fill("input[name='number_of_students_recruited_annually']", "500")
        page.fill("input[name='focus_area']", "graduate")
        page.fill("input[name='success_metrics']", "90")
        page.get_by_role("checkbox", name="Career Counseling").click()

        page.get_by_role("button", name="Next").click()

        expect(page).to_have_url("https://authorized-partner.netlify.app/register?step=verification")

        # Verification process
        page.fill("input[name='business_registration_number']", "123654789321654987")

        page.get_by_role("combobox").click()
        page.locator("div", has_text="Australia").first.click()

        page.get_by_role("checkbox", name="Universities").click()
        page.set_input_files("input[type='file']", "data/sample.csv")

        page.get_by_role("button", name="Submit").click()

        # Redirected to dashboard
        page.wait_for_timeout(4000)
        expect(page).to_have_url("https://authorized-partner.netlify.app/admin/profile")
        browser.close()
