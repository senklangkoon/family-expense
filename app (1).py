import streamlit as st
import pandas as pd
import json
import os
import base64
from datetime import date, datetime
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="บันทึกค่าใช้จ่ายครอบครัว",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DATA_FILE = "expenses.json"
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

CATEGORIES = [
    "🏗️ งานโครงสร้าง",
    "🎨 งานตกแต่ง",
    "🔧 งานซ่อม",
    "🛠️ เครื่องมือช่าง",
    "🪑 เฟอร์นิเจอร์",
    "🖌️ สี",
    "👷 ค่าแรงงาน",
]

# ─── Data helpers ──────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(records):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def save_image(uploaded_file):
    if uploaded_file is None:
        return None
    path = UPLOAD_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(path)

def image_to_b64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@300;400;500;600;700&family=IBM+Plex+Mono&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    background: #0f1117 !important;
    font-family: 'IBM Plex Sans Thai', sans-serif !important;
    color: #e2e8f0 !important;
}

/* Hide default Streamlit header */
header[data-testid="stHeader"] { display: none !important; }
.stDeployButton { display: none !important; }

/* ── NAV ── */
.top-nav {
    display: flex;
    align-items: center;
    gap: 0;
    background: #161b27;
    border-bottom: 1px solid #2a3147;
    padding: 0 32px;
    margin: -1rem -1rem 2rem -1rem;
    position: sticky;
    top: 0;
    z-index: 100;
}
.nav-brand {
    font-size: 1.1rem;
    font-weight: 700;
    color: #7dd3fc;
    padding: 18px 0;
    margin-right: 32px;
    letter-spacing: -0.02em;
    display: flex;
    align-items: center;
    gap: 8px;
}
.nav-brand span { color: #e2e8f0; }

/* ── SECTION HEADER ── */
.section-header {
    font-size: 1.4rem;
    font-weight: 700;
    color: #f1f5f9;
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid #2a3147;
    letter-spacing: -0.02em;
}
.section-sub {
    font-size: 0.8rem;
    color: #64748b;
    font-weight: 400;
    margin-left: 8px;
}

/* ── CARDS ── */
.form-card {
    background: #161b27;
    border: 1px solid #2a3147;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.field-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}
.required { color: #f87171; margin-left: 3px; }

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stTextArea textarea,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {
    background: #0f1117 !important;
    border: 1px solid #2a3147 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'IBM Plex Sans Thai', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 10px 14px !important;
    transition: border-color 0.2s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus,
.stNumberInput > div > div > input:focus {
    border-color: #7dd3fc !important;
    box-shadow: 0 0 0 3px rgba(125,211,252,0.1) !important;
}

/* ── NUMBER STEPPER ── */
.stNumberInput > div {
    background: #0f1117 !important;
    border: 1px solid #2a3147 !important;
    border-radius: 8px !important;
}
.stNumberInput button {
    background: #1e2535 !important;
    color: #7dd3fc !important;
    border: none !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
}
.stNumberInput button:hover {
    background: #2a3147 !important;
}

/* ── CATEGORY PILLS ── */
.cat-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 4px;
}
.cat-pill {
    cursor: pointer;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 0.82rem;
    border: 1px solid #2a3147;
    background: #0f1117;
    color: #94a3b8;
    transition: all 0.15s;
    white-space: nowrap;
    user-select: none;
}
.cat-pill:hover { border-color: #7dd3fc; color: #7dd3fc; }
.cat-pill.active {
    background: #1e3a5f;
    border-color: #7dd3fc;
    color: #7dd3fc;
    font-weight: 600;
}

/* ── SUBMIT BUTTON ── */
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #1d4ed8, #0ea5e9) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 14px 28px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    font-family: 'IBM Plex Sans Thai', sans-serif !important;
    letter-spacing: 0.01em !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
    margin-top: 0.5rem !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(14,165,233,0.3) !important;
}

/* ── SUCCESS / ERROR ── */
.stSuccess, .stError { border-radius: 10px !important; }

/* ── UPLOAD ── */
.stFileUploader > div {
    border: 2px dashed #2a3147 !important;
    border-radius: 10px !important;
    background: #0f1117 !important;
}
.stFileUploader label { color: #94a3b8 !important; }

/* ── DATE INPUT ── */
.stDateInput > div > div {
    background: #0f1117 !important;
    border: 1px solid #2a3147 !important;
    border-radius: 8px !important;
}

/* ── TABLE PAGE ── */
.filter-bar {
    background: #161b27;
    border: 1px solid #2a3147;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
}
.metric-row {
    display: flex;
    gap: 16px;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}
.metric-card {
    flex: 1;
    min-width: 160px;
    background: #161b27;
    border: 1px solid #2a3147;
    border-radius: 12px;
    padding: 1.25rem;
}
.metric-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #7dd3fc;
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: -0.03em;
}
.metric-unit {
    font-size: 0.8rem;
    color: #64748b;
    margin-left: 4px;
}

/* Dataframe */
.stDataFrame {
    border: 1px solid #2a3147 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}
iframe { border-radius: 12px !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #161b27 !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid #2a3147 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #64748b !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Sans Thai', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 8px 24px !important;
}
.stTabs [aria-selected="true"] {
    background: #1e2535 !important;
    color: #7dd3fc !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.5rem !important;
}

/* Selectbox */
.stSelectbox [data-baseweb="select"] > div {
    background: #0f1117 !important;
    border-color: #2a3147 !important;
    color: #e2e8f0 !important;
}

/* Multiselect */
.stMultiSelect [data-baseweb="select"] > div {
    background: #0f1117 !important;
    border-color: #2a3147 !important;
}

/* Slider */
.stSlider > div > div { color: #7dd3fc !important; }

div[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

/* Receipt thumbnail */
.receipt-thumb {
    width: 80px;
    height: 60px;
    object-fit: cover;
    border-radius: 6px;
    border: 1px solid #2a3147;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

# ─── NAV ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-nav">
  <div class="nav-brand">🏠 <span>Family</span>Expense</div>
</div>
""", unsafe_allow_html=True)

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["➕  เพิ่มรายการ", "📊  ตารางรายจ่าย"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FORM
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">บันทึกรายจ่ายใหม่ <span class="section-sub">กรอกข้อมูลแล้วกด บันทึก</span></div>', unsafe_allow_html=True)

    # init session state
    if "qty" not in st.session_state:
        st.session_state.qty = 1
    if "selected_cat" not in st.session_state:
        st.session_state.selected_cat = None

    with st.form("expense_form", clear_on_submit=True):

        # ── Row 1: ชื่อ + ยี่ห้อ ──────────────────────────────────────────
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="field-label">ชื่ออุปกรณ์ / วัสดุ <span class="required">*</span></div>', unsafe_allow_html=True)
            name = st.text_input("ชื่อ", placeholder="เช่น ปูนซีเมนต์, โต๊ะ, หลอดไฟ", label_visibility="collapsed")
        with col2:
            st.markdown('<div class="field-label">ยี่ห้อ</div>', unsafe_allow_html=True)
            brand = st.text_input("ยี่ห้อ", placeholder="เช่น SCG, IKEA, Philips", label_visibility="collapsed")

        # ── Row 2: ร้านค้า + วันที่ ────────────────────────────────────────
        col3, col4 = st.columns(2)
        with col3:
            st.markdown('<div class="field-label">ร้านค้า / แหล่งซื้อ</div>', unsafe_allow_html=True)
            store = st.text_input("ร้านค้า", placeholder="เช่น HomePro, Lazada, ตลาดนัด", label_visibility="collapsed")
        with col4:
            st.markdown('<div class="field-label">วันที่ซื้อ <span class="required">*</span></div>', unsafe_allow_html=True)
            col4a, col4b = st.columns([3, 1])
            with col4a:
                purchase_date = st.date_input("วันที่", value=date.today(), label_visibility="collapsed",
                                               min_value=date(2000, 1, 1), max_value=date(2099, 12, 31),
                                               format="DD/MM/YYYY")
            with col4b:
                today_btn = st.form_submit_button("📅 วันนี้", use_container_width=True)

        # ── Row 3: ราคา + จำนวน ───────────────────────────────────────────
        col5, col6 = st.columns(2)
        with col5:
            st.markdown('<div class="field-label">ราคา (บาท) <span class="required">*</span></div>', unsafe_allow_html=True)
            price = st.number_input("ราคา", min_value=0.0, step=1.0, format="%.2f",
                                     placeholder="0.00", label_visibility="collapsed")
        with col6:
            st.markdown('<div class="field-label">จำนวน <span class="required">*</span></div>', unsafe_allow_html=True)
            quantity = st.number_input("จำนวน", min_value=1, max_value=9999, step=1,
                                        value=1, label_visibility="collapsed")

        # ── หมวดหมู่ ──────────────────────────────────────────────────────
        st.markdown('<div class="field-label" style="margin-top:1rem">หมวดหมู่วัสดุ <span class="required">*</span></div>', unsafe_allow_html=True)
        category = st.selectbox(
            "หมวดหมู่",
            options=["— เลือกหมวดหมู่ —"] + CATEGORIES,
            label_visibility="collapsed"
        )

        # ── หมายเหตุ ──────────────────────────────────────────────────────
        st.markdown('<div class="field-label" style="margin-top:1rem">หมายเหตุ</div>', unsafe_allow_html=True)
        note = st.text_area("หมายเหตุ", placeholder="รายละเอียดเพิ่มเติม...", height=80, label_visibility="collapsed")

        # ── รูปใบเสร็จ ────────────────────────────────────────────────────
        st.markdown('<div class="field-label" style="margin-top:1rem">รูปถ่ายใบเสร็จ</div>', unsafe_allow_html=True)
        receipt = st.file_uploader("รูปใบเสร็จ", type=["jpg", "jpeg", "png", "webp", "pdf"],
                                    label_visibility="collapsed")

        st.markdown("<div style='margin-top: 1rem'></div>", unsafe_allow_html=True)

        # ── ยอดรวม preview ────────────────────────────────────────────────
        if price > 0 and quantity > 0:
            total = price * quantity
            st.markdown(f"""
            <div style="background:#0f1117; border:1px solid #2a3147; border-radius:10px;
                        padding:14px 20px; margin-bottom:1rem; display:flex;
                        justify-content:space-between; align-items:center;">
                <span style="color:#64748b; font-size:0.85rem;">ยอดรวม</span>
                <span style="color:#34d399; font-size:1.3rem; font-weight:700;
                             font-family:'IBM Plex Mono',monospace;">
                    ฿{total:,.2f}
                </span>
            </div>
            """, unsafe_allow_html=True)

        submitted = st.form_submit_button("💾  บันทึกรายการ", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("⚠️ กรุณากรอกชื่ออุปกรณ์ / วัสดุ")
            elif category == "— เลือกหมวดหมู่ —":
                st.error("⚠️ กรุณาเลือกหมวดหมู่")
            elif price <= 0:
                st.error("⚠️ กรุณากรอกราคา")
            else:
                receipt_path = save_image(receipt)
                record = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                    "name": name.strip(),
                    "brand": brand.strip(),
                    "store": store.strip(),
                    "date": str(purchase_date),
                    "price": float(price),
                    "quantity": int(quantity),
                    "total": float(price) * int(quantity),
                    "category": category,
                    "note": note.strip(),
                    "receipt": receipt_path,
                    "created_at": datetime.now().isoformat(),
                }
                records = load_data()
                records.append(record)
                save_data(records)
                st.success(f"✅ บันทึกรายการ **{name}** เรียบร้อยแล้ว! ยอดรวม ฿{price*quantity:,.2f}")
                st.balloons()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TABLE
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    records = load_data()

    if not records:
        st.markdown("""
        <div style="text-align:center; padding:60px 20px; color:#4a5568;">
            <div style="font-size:3rem; margin-bottom:12px;">📭</div>
            <div style="font-size:1.1rem; font-weight:600; color:#64748b;">ยังไม่มีรายการ</div>
            <div style="font-size:0.85rem; color:#4a5568; margin-top:6px;">ไปที่แท็บ "เพิ่มรายการ" เพื่อเริ่มบันทึกค่าใช้จ่าย</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"])

        # ── METRICS ───────────────────────────────────────────────────────
        total_all = df["total"].sum()
        total_items = len(df)
        avg_price = df["price"].mean()
        top_cat = df.groupby("category")["total"].sum().idxmax() if len(df) > 0 else "-"

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">ยอดรวมทั้งหมด</div>
                <div class="metric-value">฿{total_all:,.0f}</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">จำนวนรายการ</div>
                <div class="metric-value">{total_items}<span class="metric-unit">รายการ</span></div>
            </div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">ราคาเฉลี่ย</div>
                <div class="metric-value">฿{avg_price:,.0f}</div>
            </div>""", unsafe_allow_html=True)
        with m4:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">หมวดหมู่สูงสุด</div>
                <div class="metric-value" style="font-size:0.95rem">{top_cat.split(' ',1)[-1] if top_cat != '-' else '-'}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

        # ── FILTERS ───────────────────────────────────────────────────────
        with st.expander("🔍  ตัวกรองข้อมูล", expanded=True):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                search = st.text_input("🔎 ค้นหาชื่อ / ร้านค้า", placeholder="พิมพ์เพื่อค้นหา...")
            with fc2:
                all_cats = ["ทั้งหมด"] + sorted(df["category"].unique().tolist())
                cat_filter = st.multiselect("📂 หมวดหมู่", options=all_cats[1:], default=[])
            with fc3:
                date_range = st.date_input(
                    "📅 ช่วงวันที่",
                    value=(df["date"].min().date(), df["date"].max().date()),
                    min_value=df["date"].min().date(),
                    max_value=df["date"].max().date(),
                )

            fc4, fc5 = st.columns(2)
            with fc4:
                price_min, price_max = float(df["price"].min()), float(df["price"].max())
                if price_min < price_max:
                    price_range = st.slider(
                        "💰 ช่วงราคา (บาท)",
                        min_value=price_min,
                        max_value=price_max,
                        value=(price_min, price_max),
                        format="฿%.0f"
                    )
                else:
                    price_range = (price_min, price_max)
            with fc5:
                stores = ["ทั้งหมด"] + sorted(df["store"].dropna().unique().tolist())
                store_filter = st.selectbox("🏪 ร้านค้า", options=stores)

        # ── APPLY FILTERS ─────────────────────────────────────────────────
        filtered = df.copy()

        if search:
            mask = (
                filtered["name"].str.contains(search, case=False, na=False) |
                filtered["store"].str.contains(search, case=False, na=False) |
                filtered["brand"].str.contains(search, case=False, na=False)
            )
            filtered = filtered[mask]

        if cat_filter:
            filtered = filtered[filtered["category"].isin(cat_filter)]

        if len(date_range) == 2:
            start_d, end_d = date_range
            filtered = filtered[
                (filtered["date"].dt.date >= start_d) &
                (filtered["date"].dt.date <= end_d)
            ]

        filtered = filtered[
            (filtered["price"] >= price_range[0]) &
            (filtered["price"] <= price_range[1])
        ]

        if store_filter != "ทั้งหมด":
            filtered = filtered[filtered["store"] == store_filter]

        # ── SORT ──────────────────────────────────────────────────────────
        sc1, sc2, sc3 = st.columns([2, 1, 1])
        with sc1:
            st.markdown(f"<div style='color:#64748b; font-size:0.85rem; padding-top:8px'>แสดง <b style='color:#e2e8f0'>{len(filtered)}</b> จาก {len(df)} รายการ</div>", unsafe_allow_html=True)
        with sc2:
            sort_col = st.selectbox("เรียงตาม", ["date", "name", "price", "total", "category"], label_visibility="collapsed")
        with sc3:
            sort_asc = st.selectbox("ลำดับ", ["ใหม่→เก่า / มาก→น้อย", "เก่า→ใหม่ / น้อย→มาก"], label_visibility="collapsed")

        ascending = sort_asc == "เก่า→ใหม่ / น้อย→มาก"
        filtered = filtered.sort_values(sort_col, ascending=ascending)

        # ── DISPLAY TABLE ─────────────────────────────────────────────────
        display_df = filtered[[
            "date", "name", "brand", "store", "category",
            "price", "quantity", "total", "note"
        ]].copy()

        display_df.columns = [
            "วันที่", "ชื่ออุปกรณ์/วัสดุ", "ยี่ห้อ", "ร้านค้า", "หมวดหมู่",
            "ราคา (บาท)", "จำนวน", "รวม (บาท)", "หมายเหตุ"
        ]
        display_df["วันที่"] = display_df["วันที่"].dt.strftime("%d/%m/%Y")
        display_df["ราคา (บาท)"] = display_df["ราคา (บาท)"].apply(lambda x: f"฿{x:,.2f}")
        display_df["รวม (บาท)"] = display_df["รวม (บาท)"].apply(lambda x: f"฿{x:,.2f}")

        st.dataframe(
            display_df,
            use_container_width=True,
            height=480,
            hide_index=True,
        )

        # ── EXPORT ────────────────────────────────────────────────────────
        st.markdown("<div style='margin-top: 1rem'></div>", unsafe_allow_html=True)
        ex1, ex2 = st.columns(2)
        with ex1:
            csv = filtered.drop(columns=["id", "created_at", "receipt"], errors="ignore").to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                "⬇️  Export CSV",
                data=csv,
                file_name=f"expenses_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with ex2:
            if st.button("🗑️  ล้างตัวกรองทั้งหมด", use_container_width=True):
                st.rerun()

        # ── CHART ─────────────────────────────────────────────────────────
        if len(filtered) > 0:
            st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)
            st.markdown('<div class="section-header">📈 สรุปค่าใช้จ่ายตามหมวดหมู่</div>', unsafe_allow_html=True)
            cat_summary = (
                filtered.groupby("category")["total"]
                .sum()
                .reset_index()
                .rename(columns={"category": "หมวดหมู่", "total": "ยอดรวม (บาท)"})
                .sort_values("ยอดรวม (บาท)", ascending=False)
            )
            st.bar_chart(cat_summary.set_index("หมวดหมู่"), color="#7dd3fc", height=300)
