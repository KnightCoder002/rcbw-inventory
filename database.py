import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import streamlit as st
import time

# ── Google Sheets setup ──────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
CREDS_FILE  = "rcbw-inventory-d0aca2acadd5.json"
SHEET_NAME  = "RCBW Inventory"

# Worksheet (tab) names
WS_PRODUCTS    = "Products"
WS_STOCK       = "Stock"
WS_TRANSACTIONS= "Transactions"

# Low‑stock alert threshold
LOW_STOCK_THRESHOLD = 3

# ── Product catalogue ────────────────────────────────────────────────────────
PRODUCTS = {
    "Kitchen Towel": {
        "variants": ["Small (Rs.5)", "Medium (Rs.10)", "Large (Rs.20)"]
    },
    "Kerchief": {
        "variants": ["Ladies (Rs.15)", "Gents (Rs.20)", "Cartoon (Rs.10)"]
    },
    "Bath Towel": {
        "variants": ["V.Small (Rs.60)", "Small (Rs.70)", "Medium (Rs.80)", "Big (Rs.100)", "Large (Rs.145)", "X.Large (Rs.160)"]
    },
    "Cartoon Towel": {
        "variants": ["Standard (Rs.200)"]
    },
    "Bedsheet - Single": {
        "variants": ["Plain", "Chota Bheem", "Other Design"]
    },
    "Bedsheet - Double": {
        "variants": ["Plain", "Chota Bheem", "Other Design"]
    },
    "Bedsheet - King Size": {
        "variants": ["Plain", "Other Design"]
    },
    "Bedsheet - Queen Size": {
        "variants": ["Plain", "Other Design"]
    },
    "Bedsheet - Tari": {
        "variants": ["Small (Rs.175)", "Medium (Rs.250)", "Large (Rs.350)"]
    },
    "Bed Cover": {
        "variants": ["Small (Rs.250)", "Big (Rs.300-800)", "King (Rs.1100)"]
    },
    "Quilt": {
        "variants": ["Small (Rs.500)", "Large (Rs.1500)"]
    },
    "Mat": {
        "variants": ["Small (Rs.25)", "Large (Rs.65)"]
    },
    "Yoga Mat": {
        "variants": ["Standard (Rs.300)"]
    },
    "Baby Mat": {
        "variants": ["Standard (Rs.250)"]
    },
    "Pillow": {
        "variants": ["Standard"]
    },
    "Pillow Cover": {
        "variants": ["Standard (Rs.60)"]
    },
    "Small Pillow Cover": {
        "variants": ["Standard (Rs.50)"]
    },
    "Cushion": {
        "variants": ["Small (Rs.200)", "Large (Rs.250)"]
    },
    "Cushion Cover": {
        "variants": ["Standard (Rs.150-200)"]
    },
    "Hand Gloves": {
        "variants": ["Standard (Rs.25-100)"]
    },
    "Hot Plate": {
        "variants": ["Standard (Rs.25)"]
    },
    "Wire Bag": {
        "variants": ["XXXS (Rs.120)", "XXS (Rs.150)", "XS (Rs. 160)", "S (Rs. 240)", "M (Rs.270)", "L (Rs.300)", "XL (Rs.440)", "XXL (Rs.470)", "XXXL (Rs. 500)", "UltraLarge (Rs.570)"]
    },
    "Cloth Bag": {
        "variants": ["Small (Rs.10)", "Medium (Rs.150)", "Large (Rs.300)"]
    },
    "Ladies HandBag": {
        "variants": ["XS (Rs. 100)", "S (Rs. 150)", "M (Rs.175)", "L (Rs.200)", "XL (Rs.250)", "XXL (Rs.400)", "Jolna (Rs. 150)"]
    },
    "Handbag": {
        "variants": ["Small (Rs.50)", "Medium (Rs.125)", "Large (Rs.150)"]
    },
    "Lunch Bag": {
        "variants": ["Small (Rs.150)", "Large (Rs.200)"]
    },
    "Travel Bag": {
        "variants": ["Standard (Rs.300)"]
    },
    "Laptop Jute/Cloth Bag": {
        "variants": ["Standard (Rs.450)"]
    },
    "Belt Bag": {
        "variants": ["Cloth (Rs.150)", "Jeans (Rs.150)"]
    },
    "Purse": {
        "variants": ["Varying (Rs.10-100)"]
    },
    "Pouch": {
        "variants": ["Standard (Rs.50)"]
    },
    "Cell Phone Pouch": {
        "variants": ["Side Zip (Rs.150)"]
    },
    "Toilet Gift Pouch": {
        "variants": ["Standard (Rs.150)"]
    },
    "Jute Bag / Ladies Bag": {
        "variants": ["Small (Rs.100)", "Large (Rs.200)"]
    },
    "Door Mat": {
        "variants": ["Puny (Rs.25)", "Small (Rs.60)", "Medium (Rs.65)", "Large (Rs.160)"]
    },
    "Table Mat": {
        "variants": ["Small (Rs.10-20)", "Large (Rs.250)"]
    },
    "Full Screen": {
        "variants": ["Small (Rs.25)", "Medium (Rs.100)", "Large (Rs.300)"]
    },
    "Half Screen": {
        "variants": ["Standard (Rs.20)"]
    },
    "iPad Cover": {
        "variants": ["Standard (Rs.200)"]
    },
    "Table Cloth": {
        "variants": ["Standard (Rs.100)"]
    },
    "Fridge Cover": {
        "variants": ["Standard"]
    },
    "Fridge Holder": {
        "variants": ["Standard"]
    },
    "Fruit Basket": {
        "variants": ["Standard"]
    },
    "Letter Box": {
        "variants": ["Standard"]
    },
    "Inskirt": {
        "variants": ["XS (Rs.160)", "S (Rs.170)", "M (Rs.180)", "L (Rs.190)", "XL (Rs.200)"]
    },
    "Night Dress": {
        "variants": ["XL (Rs.200)", "XXL (Rs.275)", "XXXL (Rs.350)", "Free Size"]
    },
    "Apron": {
        "variants": ["Small (Rs.25)", "Medium (Rs.100)", "Large (Rs.200)"]
    },
    "Baby Dress": {
        "variants": ["Standard (Rs.100-150)"]
    },
    "Napkin": {
        "variants": ["Standard (Rs.100-150)"]
    },
    "Candle": {
        "variants": ["Small (Rs.3)", "Medium (Rs.75)", "Large (Rs.150)"]
    },
    "Candle Packet": {
        "variants": ["Small (Rs.50)", "Medium (Rs.60)", "Large (Rs.125)"]
    },
}
PRODUCT_CATEGORIES = {
    "🧺 Towels & Kerchiefs":   ["Kitchen Towel", "Kerchief", "Bath Towel", "Cartoon Towel"],
    "🛏️ Bedsheets & Spreads":  ["Bedsheet - Single", "Bedsheet - Double", "Bedsheet - King Size", "Bedsheet - Queen Size", "Bedsheet - Tari"],
    "🛌 Bed Covers & Quilts":  ["Bed Cover", "Quilt", "Mat", "Yoga Mat", "Baby Mat"],
    "🪡 Pillows & Cushions":   ["Pillow", "Pillow Cover", "Small Pillow Cover", "Cushion", "Cushion Cover", "Hand Gloves", "Hot Plate"],
    "👜 Bags & Pouches":       ["Wire Bag", "Cloth Bag", "Ladies HandBag", "Handbag", "Lunch Bag", "Travel Bag",
                                "Laptop Jute/Cloth Bag", "Belt Bag", "Purse", "Pouch",
                                "Cell Phone Pouch", "Toilet Gift Pouch", "Jute Bag / Ladies Bag"],
    "🏠 Home Items":           ["Door Mat", "Table Mat", "Full Screen", "Half Screen", "iPad Cover",
                                "Table Cloth", "Fridge Cover", "Fridge Holder", "Fruit Basket", "Letter Box"],
    "👗 Clothing":             ["Inskirt", "Night Dress", "Apron", "Baby Dress", "Napkin"],
    "🕯️ Candles":             ["Candle", "Candle Packet"],
}
# ── Google Sheets client ─────────────────────────────────────────────────────
def get_client():
    try:
        # Running on Streamlit Cloud - use secrets
        service_account_info = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    except Exception:
        # Running locally - use JSON file
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client

def get_sheet():
    return get_client().open(SHEET_NAME)

# ── One‑time sheet initialisation ────────────────────────────────────────────
def init_sheets():
    """Create worksheets and headers only if they do not exist yet."""
    try:
        sh = get_sheet()
        existing = [ws.title for ws in sh.worksheets()]
    except Exception:
        return  # Cannot reach sheet — skip silently, app still works

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Stock sheet
    if WS_STOCK not in existing:
        ws   = sh.add_worksheet(WS_STOCK, rows=500, cols=5)
        rows = [["Product", "Variant", "Quantity", "Last Updated"]]
        for product, data in PRODUCTS.items():
            for variant in data["variants"]:
                rows.append([product, variant, 0, now])
        ws.update("A1", rows)

    # Transactions sheet
    if WS_TRANSACTIONS not in existing:
        ws = sh.add_worksheet(WS_TRANSACTIONS, rows=2000, cols=6)
        ws.append_row(["Timestamp", "Type", "Product", "Variant", "Quantity", "Notes"])

# ── Stock helpers ─────────────────────────────────────────────────────────────
def get_all_stock():
    ws      = get_sheet().worksheet(WS_STOCK)
    records = ws.get_all_records(expected_headers=["Product", "Variant", "Quantity", "Last Updated"])
    return records

def get_stock_value(product: str, variant: str) -> int:
    records = get_all_stock()
    for i, r in enumerate(records):
        if r["Product"] == product and r["Variant"] == variant:
            return int(r["Quantity"]), i + 2   # +2: 1‑indexed + header row
    return 0, None

def update_stock(product: str, variant: str, delta: int, tx_type: str, notes: str = ""):
    """Add delta (positive = produced, negative = sold) to stock."""
    sh  = get_sheet()
    ws  = sh.worksheet(WS_STOCK)
    qty, row = get_stock_value(product, variant)

    new_qty = max(0, qty + delta)
    ws.update_cell(row, 3, new_qty)
    ws.update_cell(row, 4, datetime.now().strftime("%Y-%m-%d %H:%M"))

    # Log transaction
    tx_ws = sh.worksheet(WS_TRANSACTIONS)
    tx_ws.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        tx_type,
        product,
        variant,
        abs(delta),
        notes,
    ])
    return new_qty

def get_low_stock_items(threshold: int = LOW_STOCK_THRESHOLD):
    records = get_all_stock()
    return [r for r in records if int(r["Quantity"]) <= threshold and int(r["Quantity"]) > 0]

def get_zero_stock_items():
    records = get_all_stock()
    return [r for r in records if int(r["Quantity"]) == 0]

def get_transactions():
    ws = get_sheet().worksheet(WS_TRANSACTIONS)
    return ws.get_all_records()
