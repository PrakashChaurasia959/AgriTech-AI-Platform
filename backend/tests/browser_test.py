"""
Comprehensive Playwright browser automation test suite.
Fixes from run 1:
  - Inject JWT auth into localStorage before navigating to protected routes
  - Use correct await patterns for query_selector_all
  - Properly wait for page transitions
  - Test every feature with real interaction
"""
import asyncio
import json
import os
import uuid
import httpx
from pathlib import Path
from playwright.async_api import async_playwright, Page, BrowserContext

BASE_URL = "http://localhost:5173"
API_URL  = "http://localhost:8000"
SCREENSHOT_DIR = Path(__file__).parent.parent / "test_screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

# Global state
results = {
    "passed": [], "failed": [], "warnings": [],
    "console_errors": [], "failed_requests": [], "screenshots": [],
}
admin_token = ""
test_user_token = ""
test_user_email = f"qa_{uuid.uuid4().hex[:8]}@test.com"
test_user_password = "QaPass12345"


def P(name):
    results["passed"].append(name)
    print(f"  ✅  {name}")

def F(name, err=""):
    results["failed"].append({"test": name, "error": str(err)[:300]})
    print(f"  ❌  {name}: {str(err)[:200]}")

def W(name, msg=""):
    results["warnings"].append({"test": name, "msg": str(msg)[:200]})
    print(f"  ⚠   {name}: {str(msg)[:200]}")

async def shot(page, name):
    p = SCREENSHOT_DIR / f"{name}.png"
    await page.screenshot(path=str(p), full_page=False)
    results["screenshots"].append(str(p))
    print(f"  📸  {name}.png")

async def inject_auth(page: Page, token: str):
    """Inject JWT token into localStorage so React picks it up."""
    await page.evaluate(f"""() => {{
        localStorage.setItem('smartagri_token', '{token}');
        localStorage.setItem('smartagri_user', JSON.stringify({{
            id: 'admin', full_name: 'System Admin',
            email: 'admin@smartagri.com', role: 'admin',
            mobile_number: '0000000000'
        }}));
    }}""")

async def setup_listeners(page: Page):
    """Attach console and network listeners."""
    def on_console(msg):
        if msg.type in ("error", "warning"):
            text = msg.text[:300]
            results["console_errors"].append({"type": msg.type, "text": text})
            if msg.type == "error":
                print(f"  🔧  CONSOLE {msg.type.upper()}: {text[:150]}")
    def on_response(resp):
        if resp.status >= 400 and "/hot" not in resp.url:
            results["failed_requests"].append({"url": resp.url[:200], "status": resp.status})
            if resp.status != 401:   # 401 on bad login is expected
                print(f"  🌐  [{resp.status}] {resp.url[:120]}")
    page.on("console", on_console)
    page.on("response", on_response)

# ─────────────────────────────────────────────────────────────
#  STEP 0: Get real tokens from the API
# ─────────────────────────────────────────────────────────────
async def step_get_tokens():
    global admin_token, test_user_token
    print("\n=== STEP 0: Obtain Auth Tokens ===")
    async with httpx.AsyncClient(base_url=API_URL, timeout=15) as client:
        # Admin login
        r = await client.post("/api/auth/login",
            json={"email": "admin@smartagri.com", "password": "admin123456"})
        if r.status_code == 200:
            admin_token = r.json()["access_token"]
            P("Admin login via API")
        else:
            F("Admin login via API", r.text[:100])

        # Register test user
        r = await client.post("/api/auth/register", json={
            "full_name": "QA Tester",
            "email": test_user_email,
            "mobile_number": "9876543210",
            "password": test_user_password,
            "confirm_password": test_user_password,
        })
        if r.status_code == 201:
            test_user_token = r.json()["access_token"]
            P(f"Test user registered ({test_user_email})")
        else:
            F("Test user registration via API", r.text[:100])

        # Verify Atlas persistence
        if test_user_token:
            r2 = await client.get("/api/auth/me",
                headers={"Authorization": f"Bearer {test_user_token}"})
            if r2.status_code == 200 and r2.json()["email"] == test_user_email:
                P("Test user persisted to MongoDB Atlas")
            else:
                F("Atlas persistence check", r2.text[:100])


# ─────────────────────────────────────────────────────────────
#  TEST 1: Landing Page
# ─────────────────────────────────────────────────────────────
async def test_landing(page: Page):
    print("\n=== TEST 1: Landing Page ===")
    try:
        await page.goto(BASE_URL, wait_until="networkidle", timeout=20000)
        await page.wait_for_timeout(1500)

        title = await page.title()
        if "SmartAgri" in title:   P("Page title")
        else:                       F("Page title", title)

        h1 = page.locator("h1").first
        if await h1.count():        P("H1 hero heading")
        else:                       F("H1 hero heading")

        for label in ["Get Started", "Explore Features"]:
            btn = page.locator(f"text={label}").first
            if await btn.count():   P(f"'{label}' button")
            else:                   F(f"'{label}' button")

        for sec in ["features", "crops", "faq"]:
            el = page.locator(f"#{sec}").first
            if await el.count():    P(f"#{sec} section")
            else:                   F(f"#{sec} section")

        # Scroll animation test
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(800)
        footer = page.locator("footer").first
        if await footer.count():    P("Footer visible on scroll")
        else:                       W("Footer", "not found after scroll")
        await page.evaluate("window.scrollTo(0, 0)")
        await shot(page, "01_landing")
    except Exception as e:
        F("Landing page", e)


# ─────────────────────────────────────────────────────────────
#  TEST 2: Login Page
# ─────────────────────────────────────────────────────────────
async def test_login_page(page: Page):
    print("\n=== TEST 2: Login Page ===")
    try:
        await page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(1000)

        for field in ['input[type="email"]', 'input[type="password"]']:
            el = page.locator(field).first
            if await el.count():    P(f"Login field: {field}")
            else:                   F(f"Login field: {field}")

        # Toggle password visibility
        eye = page.locator("button:has(svg)").last
        if await eye.count():
            await eye.click()
            await page.wait_for_timeout(400)
            P("Password visibility toggle")

        # Forgot password link
        forgot = page.locator("text=Forgot password").first
        if await forgot.count():
            await forgot.click()
            await page.wait_for_url("**/forgot-password", timeout=5000)
            P("Forgot password link navigates correctly")
            await shot(page, "02_forgot_password")
        else:
            F("Forgot password link")

        # Reset password page
        await page.goto(f"{BASE_URL}/forgot-password", wait_until="networkidle", timeout=10000)
        email_in = page.locator('input[type="email"]').first
        if await email_in.count():
            await email_in.fill(test_user_email)
            await page.locator('button[type="submit"]').click()
            await page.wait_for_timeout(3000)
            msg = page.locator("text=/reset|link|email|sent/i").first
            if await msg.count():   P("Forgot password form submits and shows message")
            else:                   W("Forgot password response", "No visible message")
            await shot(page, "03_forgot_password_sent")
        else:
            F("Forgot password email input")

        await page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=10000)
        await shot(page, "04_login_page")
    except Exception as e:
        F("Login page test", e)


# ─────────────────────────────────────────────────────────────
#  TEST 3: Registration
# ─────────────────────────────────────────────────────────────
async def test_register_page(page: Page):
    print("\n=== TEST 3: Registration Page ===")
    try:
        await page.goto(f"{BASE_URL}/register", wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(1000)

        # Valid registration
        new_email = f"qa2_{uuid.uuid4().hex[:6]}@test.com"
        await page.locator('input[type="text"]').first.fill("QA New User")
        await page.locator('input[type="email"]').first.fill(new_email)
        await page.locator('input[type="tel"]').first.fill("5551234567")
        pwd_fields = page.locator('input[type="password"]')
        await pwd_fields.nth(0).fill("SecurePass99")
        await pwd_fields.nth(1).fill("SecurePass99")

        await shot(page, "05_register_filled")
        await page.locator('button[type="submit"]').click()
        await page.wait_for_timeout(5000)

        if "/app" in page.url:      P(f"Registration → dashboard ({new_email})")
        else:                       F("Registration redirect", f"URL={page.url}")

        # Password mismatch test
        await page.goto(f"{BASE_URL}/register", wait_until="networkidle", timeout=10000)
        mm_email = f"mm_{uuid.uuid4().hex[:6]}@test.com"
        await page.locator('input[type="text"]').first.fill("Mismatch User")
        await page.locator('input[type="email"]').first.fill(mm_email)
        await page.locator('input[type="tel"]').first.fill("5559999999")
        pwd_fields = page.locator('input[type="password"]')
        await pwd_fields.nth(0).fill("Password1")
        await pwd_fields.nth(1).fill("Password2")  # mismatch
        await page.locator('button[type="submit"]').click()
        await page.wait_for_timeout(2000)
        if "register" in page.url:  P("Password mismatch rejected")
        else:                       F("Password mismatch not rejected", page.url)

        # Short password test
        await page.goto(f"{BASE_URL}/register", wait_until="networkidle", timeout=10000)
        sp_email = f"sp_{uuid.uuid4().hex[:6]}@test.com"
        await page.locator('input[type="text"]').first.fill("Short User")
        await page.locator('input[type="email"]').first.fill(sp_email)
        await page.locator('input[type="tel"]').first.fill("5550000000")
        pwd_fields = page.locator('input[type="password"]')
        await pwd_fields.nth(0).fill("abc")   # too short
        await pwd_fields.nth(1).fill("abc")
        await page.locator('button[type="submit"]').click()
        await page.wait_for_timeout(2000)
        if "register" in page.url:  P("Short password rejected")
        else:                       W("Short password", f"URL={page.url}")

        await shot(page, "06_register_page")
    except Exception as e:
        F("Registration page test", e)


# ─────────────────────────────────────────────────────────────
#  TEST 4: Authenticated Login
# ─────────────────────────────────────────────────────────────
async def test_login_flow(page: Page):
    print("\n=== TEST 4: Login Flow ===")
    try:
        # Wrong credentials
        await page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=15000)
        await page.locator('input[type="email"]').fill("nobody@test.com")
        await page.locator('input[type="password"]').fill("wrongpass")
        await page.locator('button[type="submit"]').click()
        await page.wait_for_timeout(3000)
        if "login" in page.url:     P("Wrong credentials rejected")
        else:                       F("Wrong credentials not rejected", page.url)

        # Correct admin login
        await page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=10000)
        await page.locator('input[type="email"]').fill("admin@smartagri.com")
        await page.locator('input[type="password"]').fill("admin123456")
        await page.locator('button[type="submit"]').click()
        await page.wait_for_timeout(5000)
        if "/app" in page.url:      P("Admin login → dashboard")
        else:                       F("Admin login redirect", page.url)
        await shot(page, "07_after_login_dashboard")
    except Exception as e:
        F("Login flow test", e)


# ─────────────────────────────────────────────────────────────
#  Helper: Navigate to protected page with auth injected
# ─────────────────────────────────────────────────────────────
async def goto_protected(page: Page, path: str, token: str = None):
    """Go to BASE_URL/path with auth pre-injected."""
    tok = token or admin_token
    # First load any page to have a context, then inject, then navigate
    await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    await inject_auth(page, tok)
    # Use domcontentloaded — Vite's HMR WebSocket prevents "networkidle" from settling
    await page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded", timeout=20000)
    await page.wait_for_timeout(3000)  # wait for React rendering and API calls


# ─────────────────────────────────────────────────────────────
#  TEST 5: Dashboard
# ─────────────────────────────────────────────────────────────
async def test_dashboard(page: Page):
    print("\n=== TEST 5: Dashboard ===")
    try:
        await goto_protected(page, "/app")

        # Verify not redirected to login
        if "login" in page.url:
            F("Dashboard auth", "Redirected to login — auth injection failed")
            return

        welcome = page.locator("text=/Welcome back/i").first
        if await welcome.count():   P("Welcome message visible")
        else:                       F("Welcome message")

        # Check 4 stat cards
        stat_cards = await page.locator(".card").all()
        if len(stat_cards) >= 4:    P(f"Stat cards ({len(stat_cards)})")
        else:                       W("Stat cards", f"Only {len(stat_cards)}")

        # Check Quick Actions
        qa = page.locator("text=/Quick Actions/i").first
        if await qa.count():        P("Quick Actions section")
        else:                       W("Quick Actions section")

        # Check charts are rendered
        charts = await page.locator(".recharts-wrapper").all()
        if len(charts) >= 1:        P(f"Charts rendered ({len(charts)})")
        else:                       W("Charts", "No recharts-wrapper found")

        # Check sidebar navigation links
        sidebar = await page.locator("aside a, nav a").all()
        nav_texts = []
        for link in sidebar:
            t = (await link.inner_text()).strip()
            if t:
                nav_texts.append(t)
        if len(nav_texts) >= 6:     P(f"Sidebar links ({len(nav_texts)}): {nav_texts}")
        else:                       W("Sidebar links", f"Only {len(nav_texts)}: {nav_texts}")

        # Test dark mode toggle
        moon = page.locator("button:has(svg)").nth(0)
        if await moon.count():
            await moon.click()
            await page.wait_for_timeout(500)
            P("Dark mode toggle clicked")
            await shot(page, "08_dashboard_dark")
            await moon.click()
            await page.wait_for_timeout(500)

        await shot(page, "09_dashboard_light")
    except Exception as e:
        F("Dashboard test", e)


# ─────────────────────────────────────────────────────────────
#  TEST 6: Disease Detection
# ─────────────────────────────────────────────────────────────
async def test_disease_detection(page: Page):
    print("\n=== TEST 6: Disease Detection ===")
    try:
        await goto_protected(page, "/app/disease-detection")
        if "login" in page.url:
            F("Disease detection auth"); return

        # Use document.title (set by usePageTitle hook) instead of h1 to avoid sidebar brand
        title = await page.title()
        if "Disease" in title:      P(f"Page title: {title}")
        else:                       W("Page title", f"Got: {title}")

        # Crop type buttons
        tomato = page.locator("button:has-text('Tomato')").first
        if await tomato.count():
            await tomato.click()
            await page.wait_for_timeout(300)
            P("Tomato crop type selected")
        else:
            W("Crop type buttons", "Tomato button not found")

        # Upload area
        upload = page.locator("text=/Drag.*drop/i").first
        if await upload.count():    P("Drag-and-drop upload area")
        else:                       W("Upload area", "Not found")

        # Create and upload a real test image
        from PIL import Image as PILImage
        import numpy as np
        import tempfile

        img_arr = np.zeros((256, 256, 3), dtype=np.uint8)
        # Green healthy leaf
        img_arr[:, :, 1] = 110
        img_arr[:, :, 0] = 35
        img_arr[:, :, 2] = 25
        # Brown spots (disease indicator)
        img_arr[80:110, 80:110] = [90, 55, 20]
        img_arr[150:170, 130:160] = [85, 50, 15]

        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        PILImage.fromarray(img_arr).save(tmp.name)
        tmp.close()

        file_input = page.locator('input[type="file"]').first
        if await file_input.count():
            await file_input.set_input_files(tmp.name)
            await page.wait_for_timeout(2000)
            P("Leaf image uploaded via file input")
            await shot(page, "10_disease_image_uploaded")

            # Click Detect Disease
            detect_btn = page.locator("text=/Detect Disease/i").first
            if await detect_btn.count():
                await detect_btn.click()
                await page.wait_for_timeout(8000)

                # Check result
                result = page.locator("text=/Healthy|Blight|Rust|Spot|Mold|Disease/i").first
                if await result.count():
                    result_text = await result.inner_text()
                    P(f"Disease prediction returned: {result_text[:60]}")
                    await shot(page, "11_disease_result")
                else:
                    F("Disease prediction result not displayed")
            else:
                F("Detect Disease button not found")
        else:
            F("File input not found")

        # Invalid file test — should show toast error
        import tempfile as tf
        invalid_tmp = tf.NamedTemporaryFile(suffix=".pdf", delete=False)
        invalid_tmp.write(b"%PDF-1.4 fake content")
        invalid_tmp.close()
        if await file_input.count():
            await file_input.set_input_files(invalid_tmp.name)
            await page.wait_for_timeout(1500)
            # File validation runs in handleFile and shows a toast error
            error_toast = page.locator("text=/Invalid file type|Please upload/i").first
            if await error_toast.count():
                P("Invalid file type (.pdf) correctly rejected with toast")
            else:
                W("Invalid file validation", "Toast not visible (may have auto-dismissed)")
        os.unlink(tmp.name)
        os.unlink(invalid_tmp.name)
    except Exception as e:
        F("Disease detection test", e)


# ─────────────────────────────────────────────────────────────
#  TEST 7: Crop Recommendation
# ─────────────────────────────────────────────────────────────
async def test_crop_recommendation(page: Page):
    print("\n=== TEST 7: Crop Recommendation ===")
    try:
        await goto_protected(page, "/app/crop-recommendation")
        if "login" in page.url:
            F("Crop recommendation auth"); return

        title = await page.title()
        if "Crop" in title:         P(f"Page title: {title}")
        else:                       W("Page title", f"Got: {title}")

        # Check sliders (N, P, K, temp, humidity, pH, rainfall = 7 sliders)
        sliders = await page.locator('input[type="range"]').all()
        if len(sliders) >= 7:       P(f"All {len(sliders)} parameter sliders")
        else:                       W("Sliders", f"Only {len(sliders)} sliders")

        # Move some sliders to different values
        if len(sliders) >= 1:
            await sliders[0].fill("90")   # N
            await page.wait_for_timeout(200)
        if len(sliders) >= 2:
            await sliders[1].fill("55")   # P
            await page.wait_for_timeout(200)

        # Select Sandy soil type
        sandy = page.locator("button:has-text('Sandy')").first
        if await sandy.count():
            await sandy.click()
            await page.wait_for_timeout(300)
            P("Soil type Sandy selected")

        # Fill location
        loc_input = page.locator('input[placeholder*="Punjab"]').first
        if await loc_input.count():
            await loc_input.fill("Maharashtra, India")
            P("Location filled")

        await shot(page, "12_crop_form")

        # Get recommendations
        btn = page.locator("button:has-text('Get Recommendations')").first
        if await btn.count():
            await btn.click()
            await page.wait_for_timeout(6000)

            # Check top recommendation appeared
            top = page.locator("text=/Top Recommendation/i").first
            if await top.count():   P("Top recommendation displayed")
            else:                   F("Top recommendation not shown")

            # Check confidence scores
            conf = page.locator("text=/%/").first
            if await conf.count():  P("Confidence percentages shown")

            # Check farming tips
            tips = page.locator("text=/Farming Tips/i").first
            if await tips.count():  P("Farming tips displayed")

            # Download report button
            dl = page.locator("button:has-text('Download PDF')").first
            if await dl.count():
                await dl.click()
                await page.wait_for_timeout(2000)
                P("PDF report download triggered")
            else:
                W("PDF download", "Button not found after result")

            await shot(page, "13_crop_recommendation_result")
        else:
            F("Get Recommendations button not found")
    except Exception as e:
        F("Crop recommendation test", e)


# ─────────────────────────────────────────────────────────────
#  TEST 8: Yield Prediction
# ─────────────────────────────────────────────────────────────
async def test_yield_prediction(page: Page):
    print("\n=== TEST 8: Yield Prediction ===")
    try:
        await goto_protected(page, "/app/yield-prediction")
        if "login" in page.url:
            F("Yield prediction auth"); return

        title = await page.title()
        if "Yield" in title:        P(f"Page title: {title}")
        else:                       W("Page title", f"Got: {title}")

        # Select crop
        crop_sel = page.locator("select").first
        if await crop_sel.count():
            await crop_sel.select_option("Wheat")
            P("Crop type selected: Wheat")

        # Select state
        selects = await page.locator("select").all()
        if len(selects) >= 2:
            await selects[1].select_option("Karnataka")
            P("State selected: Karnataka")

        # Select season
        if len(selects) >= 3:
            await selects[2].select_option("Rabi")
            P("Season selected: Rabi")

        # Move area slider
        sliders = await page.locator('input[type="range"]').all()
        if sliders:
            await sliders[0].fill("5")     # 5 hectares
            P("Area set to 5 ha")

        await shot(page, "14_yield_form")

        # Predict
        btn = page.locator("button:has-text('Predict Yield')").first
        if await btn.count():
            await btn.click()
            await page.wait_for_timeout(6000)

            result = page.locator("text=/Predicted Yield/i").first
            if await result.count():
                P("Yield prediction result displayed")
                # Check kg/hectare unit
                unit = page.locator("text=/kg.hectare/i").first
                if await unit.count():  P("Yield unit (kg/hectare) shown")
                # Check improvement suggestions
                sugg = page.locator("text=/Improvement/i").first
                if await sugg.count():  P("Improvement suggestions shown")
                # Check estimate disclaimer
                disc = page.locator("text=/estimate/i").first
                if await disc.count():  P("Estimate disclaimer shown")
                await shot(page, "15_yield_result")
            else:
                F("Yield result not displayed")
        else:
            F("Predict Yield button not found")
    except Exception as e:
        F("Yield prediction test", e)


# ─────────────────────────────────────────────────────────────
#  TEST 9: Weather Forecast
# ─────────────────────────────────────────────────────────────
async def test_weather(page: Page):
    print("\n=== TEST 9: Weather Forecast ===")
    try:
        await goto_protected(page, "/app/weather")
        if "login" in page.url:
            F("Weather auth"); return

        # Page heading
        title = await page.title()
        if "Weather" in title:      P(f"Weather page title: {title}")
        else:                       W("Page title", f"Got: {title}")

        # Search for a city
        search_input = page.locator('input[type="text"]').first
        if await search_input.count():
            await search_input.fill("Mumbai")
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(6000)

            # Check temperature
            temp = page.locator("text=/°C/").first
            if await temp.count():  P("Temperature displayed after search")
            else:                   W("Temperature", "°C not found after search")

            # Check weather description
            desc = page.locator("text=/Clear sky|Cloudy|Rain|Overcast|Fog/i").first
            if await desc.count():  P("Weather description displayed")

            # Check 7-day forecast cards
            forecast_cards = await page.locator(".card").all()
            if len(forecast_cards) >= 7:    P(f"7-day forecast cards ({len(forecast_cards)})")
            else:                           W("Forecast cards", f"Only {len(forecast_cards)}")

            # Farming advice
            advice = page.locator("text=/Farming Advice/i").first
            if await advice.count(): P("Farming advice section")

            await shot(page, "16_weather_forecast")
        else:
            F("Weather search input not found")
    except Exception as e:
        F("Weather test", e)


# ─────────────────────────────────────────────────────────────
#  TEST 10: History Page
# ─────────────────────────────────────────────────────────────
async def test_history(page: Page):
    print("\n=== TEST 10: History ===")
    try:
        await goto_protected(page, "/app/history")
        if "login" in page.url:
            F("History auth"); return

        title = await page.title()
        if "History" in title:      P(f"History title: {title}")
        else:                       W("History title", f"Got: {title}")

        # Check tabs
        for tab in ["Disease Scans", "Crop Recommendations", "Yield Predictions"]:
            btn = page.locator(f"button:has-text('{tab}')").first
            if await btn.count():   P(f"History tab: {tab}")
            else:                   W(f"History tab", f"'{tab}' not found")

        # Click Disease Scans tab
        disease_tab = page.locator("button:has-text('Disease Scans')").first
        if await disease_tab.count():
            await disease_tab.click()
            await page.wait_for_timeout(2000)
            table = page.locator("table").first
            if await table.count(): P("History table displayed")
            else:                   W("History table", "No table found")
            await shot(page, "17_history_disease")

        # Click Crop tab
        crop_tab = page.locator("button:has-text('Crop Recommendations')").first
        if await crop_tab.count():
            await crop_tab.click()
            await page.wait_for_timeout(2000)
            await shot(page, "18_history_crop")
            P("Crop history tab switched")

        # Click Yield tab
        yield_tab = page.locator("button:has-text('Yield Predictions')").first
        if await yield_tab.count():
            await yield_tab.click()
            await page.wait_for_timeout(2000)
            P("Yield history tab switched")

    except Exception as e:
        F("History test", e)


# ─────────────────────────────────────────────────────────────
#  TEST 11: Profile Page
# ─────────────────────────────────────────────────────────────
async def test_profile(page: Page):
    print("\n=== TEST 11: Profile ===")
    try:
        await goto_protected(page, "/app/profile")
        if "login" in page.url:
            F("Profile auth"); return

        title = await page.title()
        if "Profile" in title:      P(f"Profile title: {title}")
        else:                       W("Profile title", f"Got: {title}")

        # Fill farm name
        farm_input = page.locator('input[placeholder*="Farm"]').first
        if await farm_input.count():
            await farm_input.fill("Test Farm QA")
            P("Farm name filled")

        # Fill location
        loc_input = page.locator('input[placeholder*="Punjab"]').first
        if await loc_input.count():
            await loc_input.fill("Test State, India")
            P("Location filled")

        # Save
        save_btn = page.locator("button:has-text('Save Changes')").first
        if await save_btn.count():
            await save_btn.click()
            await page.wait_for_timeout(3000)
            # Check for success toast
            toast = page.locator("text=/updated|success/i").first
            if await toast.count(): P("Profile saved successfully (toast)")
            else:                   W("Profile save toast", "No success message visible")
        await shot(page, "19_profile")
    except Exception as e:
        F("Profile test", e)


# ─────────────────────────────────────────────────────────────
#  TEST 12: Settings Page
# ─────────────────────────────────────────────────────────────
async def test_settings(page: Page):
    print("\n=== TEST 12: Settings ===")
    try:
        await goto_protected(page, "/app/settings")
        if "login" in page.url:
            F("Settings auth"); return

        title = await page.title()
        if "Settings" in title:     P(f"Settings title: {title}")
        else:                       W("Settings title", f"Got: {title}")

        # Toggle dark mode
        toggle = page.locator("button").filter(has_text="").nth(0)
        dark_toggle = page.locator("button[class*='rounded-full']").first
        if await dark_toggle.count():
            await dark_toggle.click()
            await page.wait_for_timeout(500)
            P("Theme toggle clicked")
            await dark_toggle.click()
            await page.wait_for_timeout(500)

        # Test password change (wrong current password)
        pwd_inputs = await page.locator('input[type="password"]').all()
        if len(pwd_inputs) >= 2:
            await pwd_inputs[0].fill("wrongpassword")
            await pwd_inputs[1].fill("newpassword123")
            change_btn = page.locator("button:has-text('Update Password')").first
            if await change_btn.count():
                await change_btn.click()
                await page.wait_for_timeout(3000)
                err = page.locator("text=/incorrect|wrong|failed/i").first
                if await err.count(): P("Wrong current password rejected")
                else:                 W("Password change error", "No error message visible")
        await shot(page, "20_settings")
    except Exception as e:
        F("Settings test", e)


# ─────────────────────────────────────────────────────────────
#  TEST 13: Admin Dashboard
# ─────────────────────────────────────────────────────────────
async def test_admin(page: Page):
    print("\n=== TEST 13: Admin Dashboard ===")
    try:
        await goto_protected(page, "/admin", admin_token)
        if "login" in page.url:
            F("Admin auth"); return

        title = await page.title()
        if "Admin" in title:        P(f"Admin title: {title}")
        else:                       W("Admin title", f"Got: {title}")

        # Check stat cards
        cards = await page.locator(".card").all()
        if len(cards) >= 4:         P(f"Admin stat cards ({len(cards)})")
        else:                       W("Admin stat cards", f"Only {len(cards)}")

        # Overview tab
        overview = page.locator("button:has-text('Overview')").first
        if await overview.count():
            await overview.click()
            await page.wait_for_timeout(1000)
            P("Admin Overview tab")
            await shot(page, "21_admin_overview")

        # User Management tab
        users_tab = page.locator("button:has-text('User Management')").first
        if await users_tab.count():
            await users_tab.click()
            await page.wait_for_timeout(2000)
            P("Admin User Management tab")

            # Check user table
            table = page.locator("table").first
            if await table.count():
                rows = await page.locator("table tbody tr").all()
                P(f"User table has {len(rows)} rows")
            else:
                W("User table", "No table found")
            await shot(page, "22_admin_users")
        else:
            W("User Management tab", "Not found")
    except Exception as e:
        F("Admin test", e)


# ─────────────────────────────────────────────────────────────
#  TEST 14: Responsive Layouts
# ─────────────────────────────────────────────────────────────
async def test_responsive(page: Page):
    print("\n=== TEST 14: Responsive Layouts ===")
    try:
        viewports = [
            (1920, 1080, "desktop_1920"),
            (1440, 900,  "desktop_1440"),
            (1024, 768,  "tablet_1024"),
            (768, 1024,  "tablet_768"),
            (375, 667,   "mobile_375_iphone"),
            (390, 844,   "mobile_390_iphone14"),
            (412, 915,   "mobile_412_android"),
        ]
        for w, h, name in viewports:
            await page.set_viewport_size({"width": w, "height": h})
            await page.goto(BASE_URL, wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(800)
            await shot(page, f"23_{name}")
            # Check no horizontal scroll (overflow)
            overflow = await page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
            if not overflow:        P(f"No horizontal overflow at {w}x{h}")
            else:                   W(f"Horizontal overflow", f"{w}x{h}")
        await page.set_viewport_size({"width": 1280, "height": 800})
    except Exception as e:
        F("Responsive test", e)


# ─────────────────────────────────────────────────────────────
#  TEST 15: Logout
# ─────────────────────────────────────────────────────────────
async def test_logout(page: Page):
    print("\n=== TEST 15: Logout ===")
    try:
        await goto_protected(page, "/app")
        logout_btn = page.locator("button:has-text('Logout')").first
        if await logout_btn.count():
            await logout_btn.click()
            await page.wait_for_timeout(3000)
            if "/" == page.url.replace(BASE_URL, "").rstrip("/") or "login" in page.url:
                P("Logout → landing/login page")
            else:
                W("Logout URL", page.url)

            # Verify protected route is blocked after logout
            await page.goto(f"{BASE_URL}/app/disease-detection",
                            wait_until="networkidle", timeout=10000)
            await page.wait_for_timeout(2000)
            if "login" in page.url:
                P("Protected route redirects after logout")
            else:
                F("Protected route not blocked after logout", page.url)
            await shot(page, "24_after_logout")
        else:
            W("Logout button", "Not found (may need scrolling)")
    except Exception as e:
        F("Logout test", e)


# ─────────────────────────────────────────────────────────────
#  STEP FINAL: Backend API checks
# ─────────────────────────────────────────────────────────────
async def step_api_checks():
    print("\n=== STEP FINAL: API Endpoint Checks ===")
    async with httpx.AsyncClient(base_url=API_URL, timeout=20) as client:
        hdrs = {"Authorization": f"Bearer {admin_token}"}

        checks = [
            ("GET", "/health",                  None,   200),
            ("GET", "/docs",                    None,   200),
            ("GET", "/api/auth/me",             None,   200),
            ("GET", "/api/disease/crops",       None,   200),
            ("GET", "/api/disease/history",     None,   200),
            ("GET", "/api/crop/history",        None,   200),
            ("GET", "/api/yield/history",       None,   200),
            ("GET", "/api/yield/options",       None,   200),
            ("GET", "/api/users/profile",       None,   200),
            ("GET", "/api/admin/dashboard",     None,   200),
            ("GET", "/api/admin/users",         None,   200),
        ]

        for method, path, body, expected in checks:
            try:
                if method == "GET":
                    r = await client.get(path, headers=hdrs)
                else:
                    r = await client.post(path, json=body, headers=hdrs)
                if r.status_code == expected:
                    P(f"API {method} {path} → {r.status_code}")
                else:
                    F(f"API {method} {path}", f"Expected {expected}, got {r.status_code}")
            except Exception as e:
                F(f"API {method} {path}", e)

        # POST crop recommend
        r = await client.post("/api/crop/recommend", json={
            "nitrogen": 80, "phosphorus": 45, "potassium": 40,
            "temperature": 25, "humidity": 70, "ph": 6.5,
            "rainfall": 120, "soil_type": "Loamy", "location": "Punjab",
        }, headers=hdrs)
        if r.status_code == 200 and "recommendations" in r.json():
            P(f"API POST /api/crop/recommend → top: {r.json()['top_recommendation']}")
        else:
            F("API crop recommend", r.text[:100])

        # POST yield predict
        r = await client.post("/api/yield/predict", json={
            "crop_type": "Rice", "state": "Punjab", "season": "Kharif",
            "area": 2.0, "rainfall": 1000, "temperature": 28,
            "soil_type": "Loamy", "fertilizer_usage": 100,
        }, headers=hdrs)
        if r.status_code == 200 and "predicted_yield" in r.json():
            P(f"API POST /api/yield/predict → {r.json()['predicted_yield']:.0f} kg/ha")
        else:
            F("API yield predict", r.text[:100])

        # POST auth register (duplicate → 409)
        r = await client.post("/api/auth/register", json={
            "full_name": "Dup", "email": "admin@smartagri.com",
            "mobile_number": "0000000000", "password": "test",
            "confirm_password": "test",
        })
        if r.status_code == 409:
            P("Duplicate email registration → 409 Conflict")
        else:
            W("Duplicate email check", f"Got {r.status_code}")

        # Validate invalid crop input (N > 200)
        r = await client.post("/api/crop/recommend", json={
            "nitrogen": 999, "phosphorus": 45, "potassium": 40,
            "temperature": 25, "humidity": 70, "ph": 6.5,
            "rainfall": 120, "soil_type": "Loamy", "location": "",
        }, headers=hdrs)
        if r.status_code == 422:
            P("Invalid crop input (N=999) → 422 Validation Error")
        else:
            W("Crop validation", f"Expected 422, got {r.status_code}")

        # Weather API
        r = await client.get("/api/weather/forecast?lat=19.076&lon=72.877&location=Mumbai",
                             headers=hdrs)
        if r.status_code == 200 and "current" in r.json():
            curr = r.json()["current"]
            P(f"Weather API → {curr['weather_description']} {curr['temperature']}°C at Mumbai")
        else:
            F("Weather API", r.text[:100])


# ─────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────
async def main():
    print("=" * 64)
    print("  SmartAgri ML — Full Automated Test Suite  v2")
    print("=" * 64)

    await step_get_tokens()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx     = await browser.new_context(viewport={"width": 1280, "height": 800})
        page    = await ctx.new_page()
        await setup_listeners(page)

        await test_landing(page)
        await test_login_page(page)
        await test_register_page(page)
        await test_login_flow(page)
        await test_dashboard(page)
        await test_disease_detection(page)
        await test_crop_recommendation(page)
        await test_yield_prediction(page)
        await test_weather(page)
        await test_history(page)
        await test_profile(page)
        await test_settings(page)
        await test_admin(page)
        await test_responsive(page)
        await test_logout(page)

        await browser.close()

    await step_api_checks()

    # ── Summary ──────────────────────────────────────────────
    total = len(results["passed"]) + len(results["failed"])
    console_errs_real  = [e for e in results["console_errors"] if e["type"] == "error"]
    console_warns      = [e for e in results["console_errors"] if e["type"] == "warning"]
    failed_real        = [r for r in results["failed_requests"] if r["status"] != 401]

    print("\n" + "=" * 64)
    print("  FINAL TEST RESULTS")
    print("=" * 64)
    print(f"  Total checks : {total}")
    print(f"  ✅ Passed     : {len(results['passed'])}")
    print(f"  ❌ Failed     : {len(results['failed'])}")
    print(f"  ⚠  Warnings   : {len(results['warnings'])}")
    print(f"  🔴 Console ERR: {len(console_errs_real)}")
    print(f"  🟡 Console WRN: {len(console_warns)}")
    print(f"  🌐 Failed reqs: {len(failed_real)}  (401 on bad-login excluded)")
    print(f"  📸 Screenshots: {len(results['screenshots'])}")
    print("=" * 64)

    if results["failed"]:
        print("\n  ❌ FAILED TESTS:")
        for f in results["failed"]:
            print(f"     • {f['test']}: {f['error'][:120]}")

    if results["warnings"]:
        print("\n  ⚠  WARNINGS:")
        for w in results["warnings"]:
            print(f"     • {w['test']}: {w['msg'][:120]}")

    if console_errs_real:
        print("\n  🔴 REAL CONSOLE ERRORS:")
        seen = set()
        for e in console_errs_real:
            if e["text"][:80] not in seen:
                print(f"     {e['text'][:120]}")
                seen.add(e["text"][:80])

    if failed_real:
        print("\n  🌐 UNEXPECTED FAILED REQUESTS:")
        for r in failed_real[:10]:
            print(f"     [{r['status']}] {r['url'][:120]}")

    # Save full results
    results_path = SCREENSHOT_DIR / "test_results_v2.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  📄 Full results → {results_path}")
    print("=" * 64)

    return results


if __name__ == "__main__":
    asyncio.run(main())
