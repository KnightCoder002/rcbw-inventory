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
        "variants": ["Small (Rs.5)", "Medium (Rs.10)", "Large (Rs.25)"]
    },
    "Ladies Kerchief": {
        "variants": ["Standard (Rs.20-25)"]
    },
    "Gents Kerchief": {
        "variants": ["Standard (Rs.20-25)"]
    },
    "Bath Towel": {
        "variants": ["Small (Rs.100)", "Medium (Rs.145)", "Large (Rs.250)"]
    },
    "Cartoon Towel": {
        "variants": ["Standard (Rs.145)"]
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
    "Bed Cover": {
        "variants": ["Small (Rs.250)", "Medium (Rs.500)", "Large (Rs.1200)"]
    },
    "Quilt": {
        "variants": ["Small (Rs.500)", "Large (Rs.1500)"]
    },
    "Yoga Mat / Baby Mat": {
        "variants": ["Standard (Rs.250-750)"]
    },
    "Sleeping Mat": {
        "variants": ["Standard"]
    },
    "Pillow": {
        "variants": ["Standard"]
    },
    "Pillow Cover": {
        "variants": ["Standard (Rs.60-150)"]
    },
    "Small Pillow Cover": {
        "variants": ["Standard (Rs.60-200)"]
    },
    "Cushion": {
        "variants": ["Standard (Rs.150-200)"]
    },
    "Cushion Cover": {
        "variants": ["Standard (Rs.150-200)"]
    },
    "Hand Gloves": {
        "variants": ["Standard (Rs.25-100)"]
    },
    "Hot Plate": {
        "variants": ["Standard (Rs.25-100)"]
    },
    "Wire Bag": {
        "variants": ["Small (Rs.200)", "Medium (Rs.750)", "Large (Rs.1500)"]
    },
    "Cloth Bag / Small Bag": {
        "variants": ["Small (Rs.10)", "Medium (Rs.150)", "Large (Rs.300)"]
    },
    "Lunch Bag": {
        "variants": ["Standard (Rs.150-300)"]
    },
    "Travel Bag": {
        "variants": ["Standard (Rs.300)"]
    },
    "Laptop Jute/Cloth Bag": {
        "variants": ["Standard (Rs.450)"]
    },
    "Purse": {
        "variants": ["Standard (Rs.45)"]
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
        "variants": ["Small (Rs.60)", "Medium (Rs.150)", "Large (Rs.225)"]
    },
    "Table Mat": {
        "variants": ["Small (Rs.10)", "Large (Rs.250)"]
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
    "Fruit Basket": {
        "variants": ["Standard"]
    },
    "Letter Box": {
        "variants": ["Standard"]
    },
    "Inskirt": {
        "variants": ["XS (Rs.150)", "S (Rs.170)", "M (Rs.190)", "L (Rs.210)", "XL (Rs.220)"]
    },
    "Nighty": {
        "variants": ["XL (Rs.200)", "XXL (Rs.275)", "XXXL (Rs.350)"]
    },
    "Apron": {
        "variants": ["Small (Rs.50)", "Medium (Rs.120)", "Large (Rs.200)"]
    },
    "Night Dress": {
        "variants": ["Medium (Rs.300)"]
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
    "🧺 Towels & Kerchiefs":   ["Kitchen Towel", "Ladies Kerchief", "Gents Kerchief", "Bath Towel", "Cartoon Towel"],
    "🛏️ Bedsheets & Spreads":  ["Bedsheet - Single", "Bedsheet - Double", "Bedsheet - King Size", "Bedsheet - Queen Size"],
    "🛌 Bed Covers & Quilts":  ["Bed Cover", "Quilt", "Yoga Mat / Baby Mat", "Sleeping Mat"],
    "🪡 Pillows & Cushions":   ["Pillow", "Pillow Cover", "Small Pillow Cover", "Cushion", "Cushion Cover", "Hand Gloves", "Hot Plate"],
    "👜 Bags & Pouches":       ["Wire Bag", "Cloth Bag / Small Bag", "Lunch Bag", "Travel Bag", "Laptop Jute/Cloth Bag",
                                "Purse", "Cell Phone Pouch", "Toilet Gift Pouch", "Jute Bag / Ladies Bag"],
    "🏠 Home Items":           ["Door Mat", "Table Mat", "iPad Cover", "Table Cloth", "Fridge Cover", "Fruit Basket", "Letter Box"],
    "👗 Clothing":             ["Inskirt", "Nighty", "Apron", "Night Dress", "Baby Dress", "Napkin"],
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
