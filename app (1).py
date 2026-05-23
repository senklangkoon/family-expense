import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date, datetime
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="บันทึกค่าใช้จ่ายครอบครัว",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

COLUMNS = [
    "หมายเลขใบเสร็จ / ใบกำกับ",
    "ชื่ออุปกรณ์ / วัสดุ",
    "ยี่ห้อ",
    "ร้านค้า / แหล่งซื้อ",
    "วันที่ซื้อ",
    "ราคาต่อหน่วย (บาท)",
    "จำนวน",
    "ราคารวม",
    "หมวดหมู่วัสดุ",
    "หมายเหตุ",
]

CATEGORIES = [
    "🏗️ งานโครงสร้าง",
    "🎨 งานตกแต่ง",
    "🔧 งานซ่อม",
    "🛠️ เครื่องมือช่าง",
    "🪑 เฟอร์นิเจอร์",
    "🖌️ สี",
    "👷 ค่าแรงงาน",
]

# ─── Google Sheets ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_gsheet_connection():
    try:
        # ใช้ Secrets จาก Streamlit Cloud
        credentials_dict = st.secrets["gsheets"]
        creds = Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        sheet_url = st.secrets["gsheets"]["spreadsheet"]
        sheet_id = sheet_url.split("/d/")[1].split("/")[0]
        workbook = client.open_by_key(sheet_id)
        return workbook
    except Exception as e:
        st.error(f"⚠️ เชื่อมต่อ Google Sheets ไม่ได้: {e}")
        return None

@st.cache_data(ttl=10)
def load_data():
    try:
        workbook = get_gsheet_connection()
        if not workbook:
            return pd.DataFrame(columns=COLUMNS)
        worksheet = workbook.worksheet("Data")
        data = worksheet.get_all_records()
        if not data:
            return pd.DataFrame(columns=COLUMNS)
        df = pd.DataFrame(data)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[COLUMNS]
    except Exception as e:
        st.error(f"⚠️ ดึงข้อมูลไม่ได้: {e}")
        return pd.DataFrame(columns=COLUMNS)

def append_rows(records: list):
    try:
        workbook = get_gsheet_connection()
        if not workbook:
            st.error("⚠️ เชื่อมต่อ Google Sheets ไม่ได้")
            return False
        worksheet = workbook.worksheet("Data")
        for r in records:
            row_data = [
                r["receipt_no"],
                r["name"],
                r["brand"],
                r["store"],
                r["date"],
                r["price"],
                r["quantity"],
                r["total"],
                r["category"],
                r["note"],
            ]
            worksheet.append_row(row_data)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"⚠️ บันทึกไม่สำเร็จ: {e}")
        return False

def save_image(uploaded_file):
    if uploaded_file is None:
        return None
    path = UPLOAD_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(path)

def get_invoice_autofill(receipt_no: str):
    if not receipt_no or not receipt_no.strip():
        return None
    df = load_data()
    if df.empty:
        return None
    matches = df[df["หมายเลขใบเสร็จ / ใบกำกับ"].astype(str).str.strip() == receipt_no.strip()]
    if matches.empty:
        return None
    first = matches.iloc[0]
    items = []
    for _, row in matches.iterrows():
        try:
            price = float(row["ราคาต่อหน่วย (บาท)"])
        except (ValueError, TypeError):
            price = 0.0
        try:
            qty = int(float(row["จำนวน"]))
        except (ValueError, TypeError):
            qty = 1
        items.append({
            "ชื่ออุปกรณ์ / วัสดุ": str(row["ชื่ออุปกรณ์ / วัสดุ"]) if pd.notna(row["ชื่ออุปกรณ์ / วัสดุ"]) else "",
            "ยี่ห้อ":              str(row["ยี่ห้อ"])              if pd.notna(row["ยี่ห้อ"]) else "",
            "หมวดหมู่":            str(row["หมวดหมู่วัสดุ"])       if pd.notna(row["หมวดหมู่วัสดุ"]) else CATEGORIES[0],
            "ราคา/หน่วย":          price,
            "จำนวน":               qty,
        })
    return {
        "store": str(first["ร้านค้า / แหล่งซื้อ"]) if pd.notna(first["ร้านค้า / แหล่งซื้อ"]) else "",
        "note":  str(first["หมายเหตุ"])             if pd.notna(first["หมายเหตุ"]) else "",
        "items": items,
    }

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

header[data-testid="stHeader"] { display: none !important; }
.stDeployButton { display: none !important; }

.top-nav {
    display: flex;
    align-items: center;
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
    display: flex;
    align-items: center;
    gap: 8px;
}
.nav-brand span { color: #e2e8f0; }

.section-header {
    font-size: 1.6rem;
    font-weight: 700;
    color: #f1f5f9;
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid #2a3147;
}
.section-sub {
    font-size: 0.9rem;
    color: #64748b;
    font-weight: 400;
    margin-left: 10px;
}

.sub-header {
    font-size: 1.15rem;
    font-weight: 700;
    color: #cbd5e1;
    margin: 1.5rem 0 1rem 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.sub-header .badge {
    background: #1e3a5f;
    color: #7dd3fc;
    font-size: 0.75rem;
    padding: 3px 10px;
    border-radius: 999px;
    font-weight: 600;
}

.field-label {
    font-size: 1rem;
    font-weight: 600;
    color: #cbd5e1;
    margin-bottom: 10px;
    margin-top: 4px;
}
.required { color: #f87171; margin-left: 3px; font-size: 1.1rem; }

.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stTextArea textarea,
.stDateInput > div > div > input {
    background: #0f1117 !important;
    border: 1px solid #2a3147 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'IBM Plex Sans Thai', sans-serif !important;
    font-size: 1rem !important;
    padding: 12px 16px !important;
}

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
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(14,165,233,0.3) !important;
}

.stFileUploader > div {
    border: 2px dashed #2a3147 !important;
    border-radius: 10px !important;
    background: #0f1117 !important;
}

.grand-total {
    background: #0f1117;
    border: 2px solid #16a34a;
    border-radius: 12px;
    padding: 20px 28px;
    margin: 1.5rem 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 24px rgba(22,163,74,0.1);
}
.grand-total-label {
    color: #f1f5f9;
    font-size: 1.2rem;
    font-weight: 700;
}
.grand-total-value {
    color: #34d399;
    font-size: 2.2rem;
    font-weight: 800;
    font-family: 'IBM Plex Mono', monospace;
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
}
.metric-unit { font-size: 0.8rem; color: #64748b; margin-left: 4px; }

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
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 8px 24px !important;
}
.stTabs [aria-selected="true"] {
    background: #1e2535 !important;
    color: #7dd3fc !important;
}

.stSelectbox [data-baseweb="select"] > div {
    background: #0f1117 !important;
    border-color: #2a3147 !important;
}

.stDataFrame {
    border: 1px solid #2a3147 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}
</style>
""", unsafe_allow_html=True)

# ─── NAV ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-nav">
  <div class="nav-brand">🏠 <span>Family</span>Expense</div>
</div>
""", unsafe_allow_html=True)

# ─── Session state ─────────────────────────────────────────────────────────────
if "last_receipt_no" not in st.session_state:
    st.session_state.last_receipt_no = ""

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["➕  เพิ่มใบเสร็จ", "📊  ตารางรายจ่าย"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — INVOICE FORM
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">บันทึกใบเสร็จใหม่ <span class="section-sub">กรอกข้อมูลใบเสร็จ + รายการสินค้า</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="sub-header">📄 ข้อมูลใบเสร็จ <span class="badge">ส่วนกลาง</span></div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown('<div class="field-label">หมายเลขใบเสร็จ / ใบกำกับ <span class="required">*</span></div>', unsafe_allow_html=True)
        receipt_no = st.text_input("เลขใบเสร็จ", placeholder="เช่น INV-2025-001", label_visibility="collapsed", key="receipt_no_field")
    with col_b:
        st.markdown('<div class="field-label">วันที่ซื้อ <span class="required">*</span></div>', unsafe_allow_html=True)
        purchase_date = st.date_input(
            "วันที่", value=date.today(), label_visibility="collapsed",
            min_value=date(2000, 1, 1), max_value=date(2099, 12, 31),
            format="DD/MM/YYYY", key="date_field",
        )

    # autofill check
    if receipt_no != st.session_state.last_receipt_no:
        st.session_state.last_receipt_no = receipt_no
        inv = get_invoice_autofill(receipt_no)
        if inv:
            st.session_state["store_field"] = inv["store"]
            st.session_state["note_field"] = inv["note"]
            st.success(f"✨ โหลดข้อมูลใบเสร็จเดิม **{receipt_no}** ({len(inv['items'])} รายการ)")

    col_c, col_d = st.columns([1, 1])
    with col_c:
        st.markdown('<div class="field-label">ร้านค้า / แหล่งซื้อ</div>', unsafe_allow_html=True)
        store = st.text_input("ร้านค้า", placeholder="เช่น HomePro, Lazada, ตลาดนัด", label_visibility="collapsed", key="store_field")
    with col_d:
        st.markdown('<div class="field-label">รูปถ่ายใบเสร็จ</div>', unsafe_allow_html=True)
        receipt_img = st.file_uploader("รูปใบเสร็จ", type=["jpg", "jpeg", "png", "webp", "pdf"], label_visibility="collapsed", key="img_field")

    st.markdown('<div class="field-label" style="margin-top:0.75rem">หมายเหตุ</div>', unsafe_allow_html=True)
    note = st.text_area("หมายเหตุ", placeholder="รายละเอียดเพิ่มเติม...", height=70, label_visibility="collapsed", key="note_field")

    # ─── รายการสินค้า (data editor) ────────────────────────────────────────
    st.markdown(f'<div class="sub-header" style="margin-top:2rem">🛒 รายการสินค้า</div>', unsafe_allow_html=True)

    default_df = pd.DataFrame([{
        "ชื่ออุปกรณ์ / วัสดุ": "",
        "ยี่ห้อ": "",
        "หมวดหมู่": CATEGORIES[0],
        "ราคา/หน่วย": 0.0,
        "จำนวน": 1,
        "ราคารวม": 0.0,
    }])

    inv = None
    if receipt_no != st.session_state.last_receipt_no:
        st.session_state.last_receipt_no = receipt_no
        inv = get_invoice_autofill(receipt_no)

    if inv and len(inv["items"]) > 0:
        items_df = pd.DataFrame(inv["items"])
        items_df["ราคารวม"] = items_df["ราคา/หน่วย"] * items_df["จำนวน"]
    else:
        items_df = default_df.copy()

    edited_df = st.data_editor(
        items_df,
        num_rows="dynamic",
        column_config={
            "ชื่ออุปกรณ์ / วัสดุ": st.column_config.TextColumn(width="large"),
            "ยี่ห้อ": st.column_config.TextColumn(width="medium"),
            "หมวดหมู่": st.column_config.SelectboxColumn(width="medium", options=CATEGORIES),
            "ราคา/หน่วย": st.column_config.NumberColumn(width="small", format="%.2f"),
            "จำนวน": st.column_config.NumberColumn(width="small", format="%d"),
            "ราคารวม": st.column_config.NumberColumn(width="small", format="%.2f", disabled=True),
        },
        hide_index=False,
        key="items_editor",
    )

    edited_df["ราคารวม"] = edited_df["ราคา/หน่วย"] * edited_df["จำนวน"]

    grand_total = edited_df["ราคารวม"].sum()
    gt_color = "#34d399" if grand_total > 0 else "#4a5568"
    st.markdown(f"""
    <div class="grand-total" style="border-color:{gt_color};">
        <div class="grand-total-label">ราคารวมทั้งสิ้น</div>
        <div class="grand-total-value" style="color:{gt_color}">฿{grand_total:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

    # ─── ปุ่มบันทึก ─────────────────────────────────────────────────────
    if st.button("💾  บันทึกใบเสร็จ", use_container_width=True, type="primary"):
        errors = []
        if not receipt_no.strip():
            errors.append("กรอกหมายเลขใบเสร็จ")

        valid_items = []
        for idx, row in edited_df.iterrows():
            if not str(row["ชื่ออุปกรณ์ / วัสดุ"]).strip() and row["ราคา/หน่วย"] == 0 and row["จำนวน"] == 0:
                continue
            if not str(row["ชื่ออุปกรณ์ / วัสดุ"]).strip():
                errors.append(f"แถว {idx+1}: กรอกชื่อสินค้า")
                continue
            if row["หมวดหมู่"] not in CATEGORIES:
                errors.append(f"แถว {idx+1}: เลือกหมวดหมู่")
                continue
            if row["ราคา/หน่วย"] <= 0:
                errors.append(f"แถว {idx+1}: กรอกราคา")
                continue
            if row["จำนวน"] <= 0:
                errors.append(f"แถว {idx+1}: กรอกจำนวน")
                continue

            valid_items.append({
                "receipt_no": receipt_no.strip(),
                "name":       str(row["ชื่ออุปกรณ์ / วัสดุ"]).strip(),
                "brand":      str(row["ยี่ห้อ"]).strip(),
                "store":      store.strip(),
                "date":       str(purchase_date),
                "price":      float(row["ราคา/หน่วย"]),
                "quantity":   int(row["จำนวน"]),
                "total":      float(row["ราคารวม"]),
                "category":   row["หมวดหมู่"],
                "note":       note.strip(),
            })

        if not valid_items:
            errors.append("ต้องมีรายการสินค้าอย่างน้อย 1 รายการ")

        if errors:
            for e in errors:
                st.error(f"⚠️ {e}")
        else:
            save_image(receipt_img)
            if append_rows(valid_items):
                st.success(f"✅ บันทึกใบเสร็จ **{receipt_no}** ({len(valid_items)} รายการ) ยอดรวม ฿{grand_total:,.2f}")
                st.balloons()
                st.session_state.last_receipt_no = ""

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TABLE
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    df = load_data()

    if df.empty:
        st.markdown("""
        <div style="text-align:center; padding:60px 20px;">
            <div style="font-size:3rem; margin-bottom:12px;">📭</div>
            <div style="font-size:1.1rem; font-weight:600; color:#64748b;">ยังไม่มีรายการ</div>
            <div style="font-size:0.85rem; color:#4a5568; margin-top:6px;">ไปที่แท็บ "เพิ่มใบเสร็จ" เพื่อเริ่มบันทึก</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        df["ราคาต่อหน่วย (บาท)"] = pd.to_numeric(df["ราคาต่อหน่วย (บาท)"], errors="coerce").fillna(0)
        df["จำนวน"] = pd.to_numeric(df["จำนวน"], errors="coerce").fillna(0).astype(int)
        df["ราคารวม"] = pd.to_numeric(df["ราคารวม"], errors="coerce").fillna(0)
        df["วันที่ซื้อ"] = pd.to_datetime(df["วันที่ซื้อ"], errors="coerce")

        total_all = df["ราคารวม"].sum()
        total_items = len(df)
        total_invoices = df["หมายเลขใบเสร็จ / ใบกำกับ"].nunique()
        top_cat = df.groupby("หมวดหมู่วัสดุ")["ราคารวม"].sum().idxmax() if len(df) > 0 else "-"

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">ยอดรวมทั้งหมด</div>
                <div class="metric-value">฿{total_all:,.0f}</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">จำนวนใบเสร็จ</div>
                <div class="metric-value">{total_invoices}<span class="metric-unit">ใบ</span></div>
            </div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">จำนวนรายการ</div>
                <div class="metric-value">{total_items}<span class="metric-unit">รายการ</span></div>
            </div>""", unsafe_allow_html=True)
        with m4:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">หมวดสูงสุด</div>
                <div class="metric-value" style="font-size:0.9rem">{str(top_cat).split(' ',1)[-1] if top_cat != '-' else '-'}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

        with st.expander("🔍  ตัวกรองข้อมูล", expanded=True):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                search = st.text_input("🔎 ค้นหา ชื่อ/ร้าน/เลขใบเสร็จ", placeholder="พิมพ์เพื่อค้นหา...")
            with fc2:
                all_cats = sorted([c for c in df["หมวดหมู่วัสดุ"].dropna().unique() if c])
                cat_filter = st.multiselect("📂 หมวดหมู่", options=all_cats, default=[])
            with fc3:
                valid_dates = df["วันที่ซื้อ"].dropna()
                if not valid_dates.empty:
                    date_range = st.date_input(
                        "📅 ช่วงวันที่",
                        value=(valid_dates.min().date(), valid_dates.max().date()),
                        min_value=valid_dates.min().date(),
                        max_value=valid_dates.max().date(),
                    )
                else:
                    date_range = ()

        filtered = df.copy()
        if search:
            mask = (
                filtered["ชื่ออุปกรณ์ / วัสดุ"].astype(str).str.contains(search, case=False, na=False) |
                filtered["ร้านค้า / แหล่งซื้อ"].astype(str).str.contains(search, case=False, na=False) |
                filtered["ยี่ห้อ"].astype(str).str.contains(search, case=False, na=False) |
                filtered["หมายเลขใบเสร็จ / ใบกำกับ"].astype(str).str.contains(search, case=False, na=False)
            )
            filtered = filtered[mask]
        if cat_filter:
            filtered = filtered[filtered["หมวดหมู่วัสดุ"].isin(cat_filter)]
        if isinstance(date_range, tuple) and len(date_range) == 2:
            s, e = date_range
            filtered = filtered[(filtered["วันที่ซื้อ"].dt.date >= s) & (filtered["วันที่ซื้อ"].dt.date <= e)]

        sc1, sc2 = st.columns([3, 1])
        with sc1:
            st.markdown(f"<div style='color:#64748b; font-size:0.85rem; padding-top:8px'>แสดง <b style='color:#e2e8f0'>{len(filtered)}</b> จาก {len(df)} รายการ</div>", unsafe_allow_html=True)
        with sc2:
            if st.button("🔄  รีเฟรช", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        display_df = filtered.copy()
        if "วันที่ซื้อ" in display_df.columns:
            display_df["วันที่ซื้อ"] = display_df["วันที่ซื้อ"].dt.strftime("%d/%m/%Y").fillna("")
        display_df["ราคาต่อหน่วย (บาท)"] = display_df["ราคาต่อหน่วย (บาท)"].apply(lambda x: f"฿{x:,.2f}")
        display_df["ราคารวม"] = display_df["ราคารวม"].apply(lambda x: f"฿{x:,.2f}")

        st.dataframe(display_df, use_container_width=True, height=480, hide_index=True)

        csv = filtered.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("⬇️  Export CSV", data=csv,
                           file_name=f"expenses_{datetime.now().strftime('%Y%m%d')}.csv",
                           mime="text/csv", use_container_width=True)

        if len(filtered) > 0:
            st.markdown('<div class="section-header" style="margin-top:2rem">📈 สรุปตามหมวดหมู่</div>', unsafe_allow_html=True)
            cat_summary = (
                filtered.groupby("หมวดหมู่วัสดุ")["ราคารวม"]
                .sum().reset_index()
                .rename(columns={"ราคารวม": "ยอดรวม (บาท)"})
                .sort_values("ยอดรวม (บาท)", ascending=False)
            )
            st.bar_chart(cat_summary.set_index("หมวดหมู่วัสดุ"), color="#7dd3fc", height=300)
