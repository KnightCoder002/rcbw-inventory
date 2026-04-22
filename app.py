import streamlit as st
import pandas as pd
from database import (
    init_sheets, get_all_stock, update_stock,
    get_low_stock_items, get_zero_stock_items,
    get_transactions, PRODUCTS, PRODUCT_CATEGORIES,
    LOW_STOCK_THRESHOLD
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RCBW Inventory",
    page_icon="🧺",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Accessibility CSS  (large text, high contrast, big buttons) ───────────────
st.markdown("""
<style>
    /* Base font size bump */
    html, body, [class*="css"] { font-size: 18px !important; }

    /* Big, readable buttons */
    .stButton > button {
        font-size: 1.3rem !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        width: 100%;
    }

    /* Produced = green */
    .btn-produce > button { background-color: #1a7a3a !important; color: white !important; }
    /* Sold = blue */
    .btn-sell    > button { background-color: #1a4a8a !important; color: white !important; }
    /* Confirm = dark green */
    .btn-confirm > button { background-color: #0d5c2a !important; color: white !important; font-size:1.5rem !important; }
    /* Back = grey */
    .btn-back    > button { background-color: #555 !important; color: white !important; }

    /* Alert boxes */
    .alert-red  { background:#ff4444; color:white; padding:1rem; border-radius:10px; font-size:1.2rem; font-weight:700; margin-bottom:0.5rem; }
    .alert-warn { background:#ff9900; color:white; padding:1rem; border-radius:10px; font-size:1.1rem; font-weight:700; margin-bottom:0.5rem; }

    /* Selectbox & number input bigger */
    .stSelectbox label, .stNumberInput label { font-size: 1.2rem !important; font-weight: 600 !important; }
    div[data-baseweb="select"] { font-size: 1.2rem !important; }
    input[type="number"] { font-size: 1.3rem !important; height: 3rem !important; }

    /* Headers */
    h1 { font-size: 2rem !important; }
    h2 { font-size: 1.6rem !important; }
    h3 { font-size: 1.3rem !important; }
</style>
""", unsafe_allow_html=True)

DIRECTOR_PASSWORD = "rcbw"   

# ── Session state defaults ────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "page":          "home",
        "tx_type":       None,
        "sel_category":  None,
        "sel_product":   None,
        "sel_variant":   None,
        "director_auth": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ── Initialise Google Sheets once ─────────────────────────────────────────────
init_sheets()

# ═════════════════════════════════════════════════════════════════════════════
# HOME PAGE
# ═════════════════════════════════════════════════════════════════════════════
def page_home():
    st.title("🧺 RCBW Inventory")
    st.markdown("### Who are you?")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="btn-produce">', unsafe_allow_html=True)
        if st.button("👩‍🦯 I am a\nWorker", key="go_worker"):
            st.session_state.page = "worker_choice"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="btn-sell">', unsafe_allow_html=True)
        if st.button("👩‍💼 I am the\nDirector", key="go_director"):
            st.session_state.page = "director_login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# WORKER — CHOOSE ACTION
# ═════════════════════════════════════════════════════════════════════════════
def page_worker_choice():
    st.title("👩‍🦯 Worker Menu")
    st.markdown("### What would you like to do?")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="btn-produce">', unsafe_allow_html=True)
        if st.button("✅ We MADE\nnew items", key="go_produce"):
            st.session_state.tx_type = "Produced"
            st.session_state.page    = "select_category"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="btn-sell">', unsafe_allow_html=True)
        if st.button("💰 We SOLD\nan item", key="go_sell"):
            st.session_state.tx_type = "Sold"
            st.session_state.page    = "select_category"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="btn-back">', unsafe_allow_html=True)
    if st.button("⬅️ Back", key="back_home"):
        st.session_state.page = "home"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# WORKER — SELECT CATEGORY
# ═════════════════════════════════════════════════════════════════════════════
def page_select_category():
    action_label = "MADE" if st.session_state.tx_type == "Produced" else "SOLD"
    st.title(f"Item we {action_label}")
    st.markdown("### Select a category:")
    st.markdown("---")

    for category in PRODUCT_CATEGORIES:
        if st.button(category, key=f"cat_{category}"):
            st.session_state.sel_category = category
            st.session_state.page         = "select_product"
            st.rerun()

    st.markdown("---")
    st.markdown('<div class="btn-back">', unsafe_allow_html=True)
    if st.button("⬅️ Back", key="back_worker"):
        st.session_state.page = "worker_choice"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# WORKER — SELECT PRODUCT & VARIANT, ENTER QUANTITY
# ═════════════════════════════════════════════════════════════════════════════
def page_select_product():
    action_label = "MADE" if st.session_state.tx_type == "Produced" else "SOLD"
    category     = st.session_state.sel_category
    products_in  = PRODUCT_CATEGORIES[category]

    st.title(f"Item we {action_label}")
    st.markdown(f"**Category:** {category}")
    st.markdown("---")

    product = st.selectbox("📦 Which product?", products_in, key="product_sel")
    variants = PRODUCTS[product]["variants"]
    variant  = st.selectbox("📐 Which type / size?", variants, key="variant_sel")
    quantity = st.number_input("🔢 How many?", min_value=1, max_value=500, value=1, step=1, key="qty_input")

    st.markdown("---")
    st.markdown('<div class="btn-confirm">', unsafe_allow_html=True)
    if st.button(f"✅ CONFIRM — {action_label} {quantity} × {product} ({variant})", key="confirm_btn"):
        delta = quantity if st.session_state.tx_type == "Produced" else -quantity
        new_qty = update_stock(product, variant, delta, st.session_state.tx_type)
        st.session_state.page = "success"
        st.session_state.success_msg = (
            f"✅ Recorded!\n\n"
            f"**{product}** ({variant})\n\n"
            f"{'Added' if delta > 0 else 'Removed'}: **{quantity}**\n\n"
            f"New stock: **{new_qty}**"
        )
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="btn-back">', unsafe_allow_html=True)
    if st.button("⬅️ Back", key="back_category"):
        st.session_state.page = "select_category"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# SUCCESS PAGE
# ═════════════════════════════════════════════════════════════════════════════
def page_success():
    st.title("🎉 Done!")
    st.success(st.session_state.get("success_msg", "Entry recorded successfully!"))
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="btn-produce">', unsafe_allow_html=True)
        if st.button("➕ Add another entry", key="another"):
            st.session_state.page = "worker_choice"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="btn-back">', unsafe_allow_html=True)
        if st.button("🏠 Home", key="success_home"):
            st.session_state.page = "home"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# DIRECTOR — LOGIN
# ═════════════════════════════════════════════════════════════════════════════
def page_director_login():
    st.title("👩‍💼 Director Login")
    st.markdown("---")
    pwd = st.text_input("🔒 Enter password:", type="password", key="pwd_input")

    if st.button("Login", key="login_btn"):
        if pwd == DIRECTOR_PASSWORD:
            st.session_state.director_auth = True
            st.session_state.page          = "director_dashboard"
            st.rerun()
        else:
            st.error("❌ Wrong password. Please try again.")

    st.markdown("---")
    st.markdown('<div class="btn-back">', unsafe_allow_html=True)
    if st.button("⬅️ Back", key="back_login"):
        st.session_state.page = "home"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# DIRECTOR — DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
def page_director_dashboard():
    if not st.session_state.director_auth:
        st.session_state.page = "director_login"
        st.rerun()

    st.title("📊 Director Dashboard")

    # Refresh button
    col_r, col_b = st.columns([3, 1])
    with col_r:
        st.markdown(f"*Last loaded: just now*")
    with col_b:
        if st.button("🔄 Refresh", key="refresh"):
            st.cache_resource.clear()
            st.rerun()

    st.markdown("---")

    # ── Pull data ──
    stock        = get_all_stock()
    low_items    = get_low_stock_items(LOW_STOCK_THRESHOLD)
    zero_items   = get_zero_stock_items()
    transactions = get_transactions()

    # ── ALERTS ──
    if zero_items:
        st.markdown(
            f'<div class="alert-red">🚨 OUT OF STOCK ({len(zero_items)} items):<br>'
            + "<br>".join([f"• {r['Product']} — {r['Variant']}" for r in zero_items])
            + "</div>",
            unsafe_allow_html=True,
        )

    if low_items:
        st.markdown(
            f'<div class="alert-warn">⚠️ LOW STOCK — only {LOW_STOCK_THRESHOLD} or fewer left ({len(low_items)} items):<br>'
            + "<br>".join([f"• {r['Product']} ({r['Variant']}) — {r['Quantity']} left" for r in low_items])
            + "</div>",
            unsafe_allow_html=True,
        )

    if not zero_items and not low_items:
        st.success("✅ All stock levels are healthy!")

    st.markdown("---")

    # ── TABS ──
    tab1, tab2, tab3 = st.tabs(["📦 Current Stock", "📈 Produced vs Sold", "📋 Transaction Log"])

    # ── Tab 1: Current Stock ──
    with tab1:
        st.subheader("Current Stock by Category")
        df_stock = pd.DataFrame(stock)
        if not df_stock.empty:
            df_stock = df_stock[["Product", "Variant", "Quantity", "Last Updated"]]
            df_stock["Quantity"] = df_stock["Quantity"].astype(int)

            for category, products in PRODUCT_CATEGORIES.items():
                cat_df = df_stock[df_stock["Product"].isin(products)]
                cat_df = cat_df[cat_df["Quantity"] > 0]
                if not cat_df.empty:
                    st.markdown(f"**{category}**")
                    st.dataframe(
                        cat_df.reset_index(drop=True),
                        use_container_width=True,
                        hide_index=True,
                    )

    # ── Tab 2: Produced vs Sold ──
    with tab2:
        st.subheader("Production vs Sales Summary")
        if transactions:
            df_tx = pd.DataFrame(transactions)
            df_tx["Quantity"] = pd.to_numeric(df_tx["Quantity"], errors="coerce").fillna(0).astype(int)

            summary = (
                df_tx.groupby(["Product", "Type"])["Quantity"]
                .sum()
                .unstack(fill_value=0)
                .reset_index()
            )
            # Ensure both columns exist
            for col in ["Produced", "Sold"]:
                if col not in summary.columns:
                    summary[col] = 0

            summary["Remaining"] = summary["Produced"] - summary["Sold"]
            summary = summary[summary[["Produced","Sold"]].sum(axis=1) > 0]
            summary = summary.sort_values("Produced", ascending=False)

            st.dataframe(summary.reset_index(drop=True), use_container_width=True, hide_index=True)

            # Simple bar chart of top 15 produced
            top = summary.nlargest(15, "Produced")
            chart_data = top.set_index("Product")[["Produced", "Sold"]]
            st.bar_chart(chart_data)
        else:
            st.info("No transactions recorded yet.")

    # ── Tab 3: Transaction Log ──
    with tab3:
        st.subheader("All Transactions")
        if transactions:
            df_tx = pd.DataFrame(transactions)
            df_tx = df_tx.sort_values("Timestamp", ascending=False) if "Timestamp" in df_tx.columns else df_tx
            st.dataframe(df_tx.reset_index(drop=True), use_container_width=True, hide_index=True)
        else:
            st.info("No transactions recorded yet.")

    st.markdown("---")
    st.markdown('<div class="btn-back">', unsafe_allow_html=True)
    if st.button("🚪 Logout", key="logout"):
        st.session_state.director_auth = False
        st.session_state.page          = "home"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═════════════════════════════════════════════════════════════════════════════
PAGE_MAP = {
    "home":             page_home,
    "worker_choice":    page_worker_choice,
    "select_category":  page_select_category,
    "select_product":   page_select_product,
    "success":          page_success,
    "director_login":   page_director_login,
    "director_dashboard": page_director_dashboard,
}

PAGE_MAP.get(st.session_state.page, page_home)()
