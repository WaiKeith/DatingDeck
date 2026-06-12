import uvicorn
import requests
import time
import urllib.parse
from threading import Thread
from bs4 import BeautifulSoup
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from playwright.sync_api import sync_playwright

app = FastAPI(title="KV Date Vibe API - Multi-Scraper Engine v2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REDNOTE_STREAM_CACHE = []
GOODY25_STREAM_CACHE = []

LOCAL_STATIC_DATABASE = [
    {
        "id": 201,
        "title": "BUMP Bouldering Arena",
        "category": "sports",
        "categoryLabel": "🏸 Active Sports",
        "location": "Jaya One, PJ",
        "mapsUrl": "https://maps.google.com/?q=BUMP+Bouldering+Jaya+One",
        "description": "A trendy, music-filled indoor climbing venue. A fantastic active date option where you can challenge each other and share a laugh.",
        "highlight": "Tons of artisan cafes next door in Jaya One for a post-workout drink.",
        "image": "https://images.unsplash.com/photo-1522163182402-834f871fd851?auto=format&fit=crop&w=600&q=80",
        "badgeColor": "bg-emerald-50 text-emerald-700 border-emerald-100"
    }
]


# =====================================================================
# UPDATED ENGINE: GOODY25 PLATFORM LIVE SEARCH SCRAPER
# =====================================================================
def get_goody25_date_spots():
    """
    Scrapes live localized Malaysian dating features directly from Goody25.com.
    Parses current article titles, cover thumbnails, and direct article links.
    """
    goody_results = []
    search_query = "情侣"  # Targets "Couples / Date Spots" contents specifically

    # URL-encode the text to handle Chinese characters safely in the URL path
    encoded_query = urllib.parse.quote_plus(search_query)

    # Goody25's live native search portal endpoint
    target_url = f"https://www.goody25.com/search.php?keyword={encoded_query}"

    request_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.goody25.com/"
    }

    try:
        response = requests.get(target_url, headers=request_headers, timeout=10)
        if response.status_code == 200:
            # Fix decoding issues since Goody25 processes specific UTF-8 Asian layouts
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, "html.parser")

            # Goody25 structures search index items inside 'div' blocks with the class 'search_content'
            articles = soup.find_all("div", class_="search_content")

            generated_id = 801
            for index, item in enumerate(articles):
                # 1. Extract the direct article link and title anchor block
                title_anchor = item.find("a", href=True)
                if not title_anchor:
                    continue

                article_url = title_anchor['href']
                # Ensure relative URLs are converted to complete absolute links
                if not article_url.startswith("http"):
                    article_url = f"https://www.goody25.com/{article_url}"

                title_text = title_anchor.text.strip()

                # 2. Attempt to pull the dynamic thumbnail image used by the author
                img_tag = item.find("img")
                image_url = "https://images.unsplash.com/photo-1560750588-73207b1ef5b8?auto=format&fit=crop&w=600&q=80"  # Default fallback
                if img_tag and img_tag.get('src'):
                    src = img_tag['src']
                    if src.startswith("http"):
                        image_url = src
                    else:
                        image_url = f"https://www.goody25.com/{src}"

                # 3. Grab the summary description paragraph text
                desc_tag = item.find("div", class_="search_desc")
                description_text = desc_tag.text.strip() if desc_tag else "点击查看由马来西亚Goody25社区编辑为你整理编写的精选情侣日常及周末活动灵感指南。"
                if len(description_text) > 100:
                    description_text = description_text[:97] + "..."

                # Append into our unified UI format mapping
                goody_results.append({
                    "id": generated_id,
                    "title": title_text,
                    "category": "discount",
                    "categoryLabel": "🇲🇾 Goody25 Feature",
                    "location": "Klang Valley Selection",
                    "mapsUrl": article_url,  # Real, clean direct external link to Goody25!
                    "description": description_text,
                    "highlight": "马来西亚本地爆款文章推荐！点击下方链接阅读完整探店打卡攻略。",
                    "image": image_url,  # Live extracted feature thumbnail graphic
                    "badgeColor": "bg-blue-50 text-blue-700 border-blue-100"
                })
                generated_id += 1

                # Cap it to the top 4 highly targeted results
                if len(goody_results) >= 4:
                    break

    except Exception as e:
        print(f"[!] Goody25 scraper pipeline error: {e}")

    # Emergency fallback if Goody25's platform layout is undergoing server maintenance
    if not goody_results:
        goody_results = [{
            "id": 800,
            "title": "雪隆情侣必去打卡圣地：周日最赞的浪漫行程",
            "category": "discount",
            "categoryLabel": "🇲🇾 Goody25 Feature",
            "location": "Klang Valley Local",
            "mapsUrl": "https://www.goody25.com",
            "description": "实时数据接口维护中。点击链接访问主页直接查找雪隆区最具有人气的吃喝玩乐约会活动。",
            "highlight": "本地社群推荐方案。手动点击打开查看。",
            "image": "https://images.unsplash.com/photo-1560750588-73207b1ef5b8?auto=format&fit=crop&w=600&q=80",
            "badgeColor": "bg-blue-50 text-blue-700 border-blue-100"
        }]

    return goody_results


# =====================================================================
# ENGINE 2: CENTRAL MARKET LIVE WEB SCRAPER (Runs on Request)
# =====================================================================
def get_live_central_market_events():
    scraped_events = []
    target_url = "https://centralmarket.com.my/"
    request_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(target_url, headers=request_headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            potential_nodes = soup.find_all(['li', 'h3', 'h4', 'p', 'span'])
            found_titles = set()
            generated_id = 301
            target_keywords = ["Cinta", "Ragamuda", "Pesta Kita", "Bazaar", "Festival", "Market"]

            for node in potential_nodes:
                text = node.text.strip()
                if not text or len(text) > 60:
                    continue
                if any(keyword.lower() in text.lower() for keyword in target_keywords):
                    if text in found_titles or len(text) < 5:
                        continue
                    found_titles.add(text)
                    scraped_events.append({
                        "id": generated_id,
                        "title": f"Pasar Seni: {text}",
                        "category": "market",
                        "categoryLabel": "🛍️ Pop-up Market",
                        "location": "Chinatown, KL",
                        "mapsUrl": "https://maps.google.com/?q=Central+Market+Kuala+Lumpur",
                        "description": "Live dynamically parsed event stream from Central Market Kuala Lumpur's weekend roster updates.",
                        "highlight": "Highly trending option for craft shopping and local food hunting.",
                        "image": "https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?auto=format&fit=crop&w=600&q=80",
                        "badgeColor": "bg-amber-50 text-amber-700 border-amber-100"
                    })
                    generated_id += 1
    except Exception as e:
        print(f"[!] Central Market scraper error: {e}")

    if not scraped_events:
        scraped_events = [{
            "id": 300,
            "title": "Central Market Weekend Creative Bazaar",
            "category": "market",
            "categoryLabel": "🛍️ Pop-up Market",
            "location": "Chinatown, KL",
            "mapsUrl": "https://maps.google.com/?q=Central+Market+Kuala+Lumpur",
            "description": "The ultimate localized marketplace vibe. Hosts rotating creative weekend themes showcasing arts, artisan foods, and live buskers.",
            "highlight": "Active This Weekend!",
            "image": "https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?auto=format&fit=crop&w=600&q=80",
            "badgeColor": "bg-amber-50 text-amber-700 border-amber-100"
        }]
    return scraped_events


# =====================================================================
# ENGINE 3: REDNOTE AUTOMATED BROWSER SCRAPER (Background Thread)
# =====================================================================
def run_playwright_scrapers():
    global GOODY25_STREAM_CACHE
    print("[*] Launching Automated Playwright Core Engine...")
    with sync_playwright() as p:
        try:
            user_data_dir = "./kv_browser_session"
            context = p.chromium.launch_persistent_context(
                user_data_dir,
                headless=False,  # Set to True later once you verify it works!
                args=["--disable-blink-features=AutomationControlled"],
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.pages[0] if context.pages else context.new_page()

            # ---------------------------------------------------------
            # TASK 1: SCRAPE GOODY25 (Targeting the /minds search page)
            # ---------------------------------------------------------
            print("[*] Navigating to Goody25 Minds Index...")

            # Updated to your live target URL with the exact query string parameters
            page.goto(
                "https://www.goody25.com/minds?mind_title=kl%E6%83%85%E4%BE%A3%E5%A5%BD%E5%8E%BB%E5%A4%84",
                wait_until="domcontentloaded",
                timeout=0
            )
            page.wait_for_timeout(4000)  # Give the data cards time to lazy-load their images

            # Scroll roughly 80 times (~4 minutes total wait time) to accumulate massive history links
            goody_scrolls = 10
            print(f"[*] Beginning deep scroll on Goody25 ({goody_scrolls} steps)...")
            for g in range(goody_scrolls):
                try:
                    if page.is_closed(): break
                    page.keyboard.press("PageDown")
                    page.wait_for_timeout(3000)  # 3-second delay between keypresses to let images load
                    if (g + 1) % 20 == 0:
                        print(f"    -> Goody25 Progress: {g + 1}/{goody_scrolls} scrolls completed.")
                except:
                    continue

            # Extract and parse compiled Goody25 structure
            goody_html = page.content()
            goody_soup = BeautifulSoup(goody_html, "html.parser")
            articles = goody_soup.find_all(["div", "a"], class_=["list-item", "mind-card", "search_content"])
            if not articles:
                articles = goody_soup.find_all("a", href=True)

            scraped_goody = []
            goody_id = 801
            for item in articles:
                title_anchor = item if item.name == "a" else item.find("a", href=True)
                if not title_anchor or not title_anchor.has_attr('href'): continue

                article_url = title_anchor['href']
                if "mind" not in article_url or article_url == "/minds": continue
                if not article_url.startswith("http"):
                    article_url = f"https://www.goody25.com{article_url}"

                title_node = title_anchor.find(["h3", "h4", "div", "span"], class_=["title", "mind-title"])
                title_text = title_node.text.strip() if title_node else title_anchor.text.strip()
                if len(title_text) < 6 or "登录" in title_text: continue

                img_tag = item.find("img")
                image_url = "https://images.unsplash.com/photo-1560750588-73207b1ef5b8?auto=format&fit=crop&w=600&q=80"
                if img_tag and img_tag.get('src'):
                    src = img_tag['src']
                    image_url = src if src.startswith("http") else f"https://www.goody25.com{src}"

                scraped_goody.append({
                    "id": goody_id,
                    "title": title_text,
                    "category": "discount",
                    "categoryLabel": "🇲🇾 Goody25 Feature",
                    "location": "Klang Valley Selection",
                    "mapsUrl": article_url,
                    "description": "精选本地高分情侣约会、周末探店打卡圣地，为你提供完美的约会活动行程蓝图指南。",
                    "highlight": "马来西亚本地爆款社区推荐！点击下方链接查看高清图文攻略。",
                    "image": image_url,
                    "badgeColor": "bg-blue-50 text-blue-700 border-blue-100"
                })
                goody_id += 1

            if scraped_goody:
                GOODY25_STREAM_CACHE = scraped_goody
                print(f"[+] Successfully cached {len(scraped_goody)} deep items from Goody25!")

            # # ---------------------------------------------------------
            # # TASK 2: SCRAPE REDNOTE
            # # ---------------------------------------------------------
            # print("[*] Navigating to RedNote Explore Feed...")
            # page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded", timeout=60000)
            # page.wait_for_timeout(3000)
            #
            # if "login" in page.url or page.locator("text=登录").is_visible():
            #     print("\n⚠️ [ACTION] Please scan the RedNote QR code if prompted...\n")
            #     page.wait_for_timeout(15000)
            #
            # # Human-like scrolling loop
            # for _ in range(2):
            #     page.keyboard.press("PageDown")
            #     page.wait_for_timeout(2000)
            #
            # rednote_html = page.content()
            # context.close()  # Clean closure saves your sessions
            #
            # # Parse RedNote Content
            # rednote_soup = BeautifulSoup(rednote_html, "html.parser")
            # notes_cards = rednote_soup.find_all("section", class_="note-item")
            #
            # scraped_rednote = []
            # rednote_id = 500
            # for card in notes_cards[:3]:
            #     title_node = card.find("a", class_="title")
            #     author_node = card.find("span", class_="name")
            #     if not title_node:
            #         continue
            #
            #     scraped_rednote.append({
            #         "id": rednote_id,
            #         "title": f"Viral RedNote: {title_node.text.strip()}",
            #         "category": "market",
            #         "categoryLabel": "🛍️ RedNote Trend",
            #         "location": "Klang Valley Pop-Up",
            #         "mapsUrl": "https://www.xiaohongshu.com/explore",
            #         "description": f"Trending dating topic currently drawing high traffic online, discovered via creator @{author_node.text.strip() if author_node else 'Community'}.",
            #         "highlight": "High engagement trend tracker. Check local app tags for specifics.",
            #         "image": "https://images.unsplash.com/photo-1533900298318-6b8da08a523e?auto=format&fit=crop&w=600&q=80",
            #         "badgeColor": "bg-rose-50 text-rose-700 border-rose-100"
            #     })
            #     rednote_id += 1
            #
            # if scraped_rednote:
            #     REDNOTE_STREAM_CACHE = scraped_rednote
            #     print(f"[+] Successfully loaded {len(scraped_rednote)} records from RedNote!")

        except Exception as error:
            print(f"[!] Playwright pipeline error: {error}")

    # Fallback Hydration for Goody25 if your internet drops during startup
    if not GOODY25_STREAM_CACHE:
        GOODY25_STREAM_CACHE = [{
            "id": 800,
            "title": "雪隆区情侣约会圣地：25大必去浪漫好去处推荐",
            "category": "discount",
            "categoryLabel": "🇲🇾 Goody25 Feature",
            "location": "Klang Valley Local",
            "mapsUrl": "https://www.goody25.com/mind7722352",  # Explicit sample link fallback
            "description": "为您整理编写的精选情侣日常及周末活动灵感指南，包含高颜值的文青咖啡厅及室内运动乐园。",
            "highlight": "本地社群高分推荐。手动点击打开查看。",
            "image": "https://images.unsplash.com/photo-1560750588-73207b1ef5b8?auto=format&fit=crop&w=600&q=80",
            "badgeColor": "bg-blue-50 text-blue-700 border-blue-100"
        }]


def trigger_background_scraper():
    # Targets our new combined master scraper function
    worker_thread = Thread(target=run_playwright_scrapers)
    worker_thread.daemon = True
    worker_thread.start()


# =====================================================================
# API AGGREGATION & PIPELINE HOOKS
# =====================================================================
@app.on_event("startup")
def app_startup_event():
    trigger_background_scraper()


@app.get("/")
def serve_frontend():
    return FileResponse("index.html")


@app.get("/api/spots")
def fetch_unified_spots():
    live_markets = get_live_central_market_events()
    return GOODY25_STREAM_CACHE + live_markets + LOCAL_STATIC_DATABASE


@app.get("/.well-known/appspecific/com.chrome.devtools.json")
def ignore_chrome_noise():
    return Response(content="{}", media_type="application/json")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)