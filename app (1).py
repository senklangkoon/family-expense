import streamlit as st
import pandas as pd
from datetime import date, datetime
from pathlib import Path
from streamlit_gsheets import GSheetsConnection

# ─── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="บันทึกค่าใช้จ่ายครอบครัว",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

WORKSHEET = "Data"  # ชื่อแท็บใน Google Sheets
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# ลำดับคอลัมน์ A→J ตามที่กำหนด
COLUMNS = [
    "หมายเลขใบเสร็จ / ใบกำกับ",  # A
    "ชื่ออุปกรณ์ / วัสดุ",          # B
    "ยี่ห้อ",                       # C
    "ร้านค้า / แหล่งซื้อ",          # D
    "วันที่ซื้อ",                   # E
    "ราคาต่อหน่วย (บาท)",          # F
    "จำนวน",                       # G
    "ราคารวม",                     # H
    "หมวดหมู่วัสดุ",               # I
    "หมายเหตุ",                    # J
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

# ─── Google Sheets connection ──────────────────────────────────────────────────
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def load_data():
    """ดึงข้อมูลจาก Google Sheets แท็บ Data"""
    try:
        df = conn.read(worksheet=WORKSHEET, ttl=5)
        if df is None or df.empty:
            return pd.DataFrame(columns=COLUMNS)
        # ลบแถวว่าง
        df = df.dropna(how="all")
        # บังคับให้ทุกคอลัมน์ที่จำเป็นมีอยู่
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[COLUMNS]
    except Exception as e:
        st.error(f"⚠️ เชื่อมต่อ Google Sheets ไม่ได้: {e}")
        return pd.DataFrame(columns=COLUMNS)

def append_row(record: dict):
    """เพิ่มแถวใหม่ในแท็บ Data"""
    df_old = load_data()
    new_row = pd.DataFrame([{
        "หมายเลขใบเสร็จ / ใบกำกับ": record["receipt_no"],
        "ชื่ออุปกรณ์ / วัสดุ": record["name"],
        "ยี่ห้อ": record["brand"],
        "ร้านค้า / แหล่งซื้อ": record["store"],
        "วันที่ซื้อ": record["date"],
        "ราคาต่อหน่วย (บาท)": record["price"],
        "จำนวน": record["quantity"],
        "ราคารวม": record["total"],
        "หมวดหมู่วัสดุ": record["category"],
        "หมายเหตุ": record["note"],
    }])
    df_new = pd.concat([df_old, new_row], ignore_index=True)
    conn.update(worksheet=WORKSHEET, data=df_new)
    st.cache_data.clear()

def save_image(uploaded_file):
    if uploaded_file is None:
        return None
    path = UPLOAD_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(path)

def get_autofill(receipt_no: str):
    """ดึงข้อมูลล่าสุดของหมายเลขใบเสร็จเดียวกัน"""
    if not receipt_no or not receipt_no.strip():
        return None
    df = load_data()
    if df.empty:
        return None
    matches = df[df["หมายเลขใบเสร็จ / ใบกำกับ"].astype(str).str.strip() == receipt_no.strip()]
    if matches.empty:
        return None
    latest = matches.iloc[-1]
    try:
        price = float(latest["ราคาต่อหน่วย (บาท)"])
    except (ValueError, TypeError):
        price = 0.0
    return {
        "name": str(latest["ชื่ออุปกรณ์ / วัสดุ"]) if pd.notna(latest["ชื่ออุปกรณ์ / วัสดุ"]) else "",
        "brand": str(latest["ยี่ห้อ"]) if pd.notna(latest["ยี่ห้อ"]) else "",
        "price": price,
        "category": str(latest["หมวดหมู่วัสดุ"]) if pd.notna(latest["หมวดหมู่วัสดุ"]) else CATEGORIES[0],
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
    letter-spacing: -0.02em;
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
    letter-spacing: -0.02em;
}
.section-sub {
    font-size: 0.9rem;
    color: #64748b;
    font-weight: 400;
    margin-left: 10px;
}

.field-label {
    font-size: 1rem;
    font-weight: 600;
    color: #cbd5e1;
    letter-spacing: 0.01em;
    margin-bottom: 10px;
    margin-top: 4px;
}
.required { color: #f87171; margin-left: 3px; font-size: 1.1rem; }

.autofill-badge {
    display: inline-block;
    background: #14532d;
    border: 1px solid #16a34a;
    color: #4ade80;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 999px;
    margin-left: 10px;
    vertical-align: middle;
}

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
    transition: border-color 0.2s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: #7dd3fc !important;
    box-shadow: 0 0 0 3px rgba(125,211,252,0.1) !important;
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
    cursor: pointer !important;
    transition: all 0.2s !important;
    margin-top: 0.5rem !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(14,165,233,0.3) !important;
}

.stSuccess, .stError { border-radius: 10px !important; }

.stFileUploader > div {
    border: 2px dashed #2a3147 !important;
    border-radius: 10px !important;
    background: #0f1117 !important;
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
.metric-unit { font-size: 0.8rem; color: #64748b; margin-left: 4px; }

/* ── TOTAL preview (ราคารวม) ── */
.total-preview {
    background: #0f1117;
    border: 1px solid #2a3147;
    border-radius: 10px;
    padding: 18px 24px;
    margin: 1rem 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.total-label {
    color: #cbd5e1;
    font-size: 1.05rem;
    font-weight: 600;
}
.total-value {
    font-size: 2rem;
    font-weight: 800;
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: -0.02em;
}

.stDataFrame { border: 1px solid #2a3147 !important; border-radius: 12px !important; overflow: hidden !important; }

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
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.5rem !important; }

.stSelectbox [data-baseweb="select"] > div {
    background: #0f1117 !important;
    border-color: #2a3147 !important;
    color: #e2e8f0 !important;
}
.stMultiSelect [data-baseweb="select"] > div {
    background: #0f1117 !important;
    border-color: #2a3147 !important;
}

/* ── ราคา/จำนวน — ตัวเลขใหญ่แบบเครื่องคิดเลข ── */
input[aria-label="ราคา"],
input[aria-label="จำนวน"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.4rem !important;
    font-weight: 600 !important;
    text-align: right !important;
    padding: 14px 18px !important;
    color: #7dd3fc !important;
}
</style>

<script>
// บังคับให้เปิด numeric keypad บนมือถือ
(function() {
    const setNumeric = () => {
        document.querySelectorAll('input[aria-label="ราคา"], input[aria-label="จำนวน"]').forEach(el => {
            el.setAttribute('inputmode', 'decimal');
            el.setAttribute('pattern', '[0-9]*');
            el.setAttribute('autocomplete', 'off');
        });
    };
    setNumeric();
    new MutationObserver(setNumeric).observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)

# ─── NAV ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-nav">
  <div class="nav-brand">🏠 <span>Family</span>Expense</div>
</div>
""", unsafe_allow_html=True)

# ─── Session state init ────────────────────────────────────────────────────────
if "autofill" not in st.session_state:
    st.session_state.autofill = None
if "last_receipt_no" not in st.session_state:
    st.session_state.last_receipt_no = ""

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["➕  เพิ่มรายการ", "📊  ตารางรายจ่าย"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FORM
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">บันทึกรายจ่ายใหม่ <span class="section-sub">กรอกข้อมูลแล้วกด บันทึก</span></div>', unsafe_allow_html=True)

    # ── หมายเลขใบเสร็จ ────────────────────────────────────────────────────────
    st.markdown('<div class="field-label">หมายเลขใบเสร็จ / ใบกำกับ</div>', unsafe_allow_html=True)
    receipt_no_input = st.text_input(
        "หมายเลขใบเสร็จ",
        placeholder="เช่น INV-2025-001",
        label_visibility="collapsed",
        key="receipt_no_field",
    )

    # autofill เมื่อเลขใบเสร็จเปลี่ยน
    if receipt_no_input != st.session_state.last_receipt_no:
        st.session_state.last_receipt_no = receipt_no_input
        st.session_state.autofill = get_autofill(receipt_no_input)

    af = st.session_state.autofill
    if af:
        st.markdown(
            f'<div style="margin-bottom:0.75rem">'
            f'<span class="autofill-badge">✨ Autofill จากบันทึกก่อนหน้า</span>'
            f'<span style="color:#64748b; font-size:0.8rem; margin-left:8px;">'
            f'ชื่อ: <b style="color:#cbd5e1">{af["name"] or "-"}</b> · '
            f'ยี่ห้อ: <b style="color:#cbd5e1">{af["brand"] or "-"}</b> · '
            f'ราคา: <b style="color:#cbd5e1">฿{af["price"]:,.2f}</b> · '
            f'หมวด: <b style="color:#cbd5e1">{af["category"]}</b>'
            f'</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom:0.5rem'></div>", unsafe_allow_html=True)

    # ── ชื่อ + ยี่ห้อ ──────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="field-label">ชื่ออุปกรณ์ / วัสดุ <span class="required">*</span></div>', unsafe_allow_html=True)
        name_default = af["name"] if af else ""
        name = st.text_input("ชื่อ", value=name_default, placeholder="เช่น ปูนซีเมนต์, โต๊ะ, หลอดไฟ", label_visibility="collapsed", key="name_field")
    with col2:
        st.markdown('<div class="field-label">ยี่ห้อ</div>', unsafe_allow_html=True)
        brand_default = af["brand"] if af else ""
        brand = st.text_input("ยี่ห้อ", value=brand_default, placeholder="เช่น SCG, IKEA, Philips", label_visibility="collapsed", key="brand_field")

    # ── ร้านค้า + วันที่ ───────────────────────────────────────────────────────
    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="field-label">ร้านค้า / แหล่งซื้อ</div>', unsafe_allow_html=True)
        store = st.text_input("ร้านค้า", placeholder="เช่น HomePro, Lazada, ตลาดนัด", label_visibility="collapsed", key="store_field")
    with col4:
        st.markdown('<div class="field-label">วันที่ซื้อ <span class="required">*</span></div>', unsafe_allow_html=True)
        purchase_date = st.date_input(
            "วันที่", value=date.today(), label_visibility="collapsed",
            min_value=date(2000, 1, 1), max_value=date(2099, 12, 31),
            format="DD/MM/YYYY", key="date_field",
        )

    # ── ราคา + จำนวน (text_input → numeric keypad บนมือถือ) ───────────────────
    col5, col6 = st.columns(2)
    with col5:
        st.markdown('<div class="field-label">ราคาต่อหน่วย (บาท) <span class="required">*</span></div>', unsafe_allow_html=True)
        price_default = f"{float(af['price']):.2f}" if af else ""
        price_str = st.text_input(
            "ราคา", value=price_default, placeholder="0.00",
            label_visibility="collapsed", key="price_field",
        )
        try:
            price = float(price_str.replace(",", "").replace(" ", "")) if price_str.strip() else 0.0
        except ValueError:
            price = 0.0
            st.caption(":red[⚠️ กรุณากรอกตัวเลขเท่านั้น]")

    with col6:
        st.markdown('<div class="field-label">จำนวน <span class="required">*</span></div>', unsafe_allow_html=True)
        qty_str = st.text_input(
            "จำนวน", value="1", placeholder="1",
            label_visibility="collapsed", key="qty_field",
        )
        try:
            quantity = int(float(qty_str.replace(",", "").replace(" ", ""))) if qty_str.strip() else 1
            if quantity < 1:
                quantity = 1
        except ValueError:
            quantity = 1
            st.caption(":red[⚠️ กรุณากรอกตัวเลขเท่านั้น]")

    # ── ราคารวม real-time (เฉพาะคำว่า "ราคารวม" + ตัวเลขสีเขียวใหญ่) ─────────
    total_preview = price * quantity
    color = "#34d399" if total_preview > 0 else "#4a5568"
    st.markdown(f"""
    <div class="total-preview">
        <div class="total-label">ราคารวม</div>
        <div class="total-value" style="color:{color};">฿{total_preview:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── หมวดหมู่ ───────────────────────────────────────────────────────────────
    st.markdown('<div class="field-label">หมวดหมู่วัสดุ <span class="required">*</span></div>', unsafe_allow_html=True)
    cat_options = ["— เลือกหมวดหมู่ —"] + CATEGORIES
    cat_default_idx = 0
    if af and af["category"] in CATEGORIES:
        cat_default_idx = cat_options.index(af["category"])
    category = st.selectbox("หมวดหมู่", options=cat_options, index=cat_default_idx, label_visibility="collapsed", key="cat_field")

    # ── หมายเหตุ ───────────────────────────────────────────────────────────────
    st.markdown('<div class="field-label" style="margin-top:1rem">หมายเหตุ</div>', unsafe_allow_html=True)
    note = st.text_area("หมายเหตุ", placeholder="รายละเอียดเพิ่มเติม...", height=80, label_visibility="collapsed", key="note_field")

    # ── รูปใบเสร็จ ─────────────────────────────────────────────────────────────
    st.markdown('<div class="field-label" style="margin-top:1rem">รูปถ่ายใบเสร็จ</div>', unsafe_allow_html=True)
    receipt_img = st.file_uploader("รูปใบเสร็จ", type=["jpg", "jpeg", "png", "webp", "pdf"], label_visibility="collapsed", key="img_field")

    st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)
    submitted = st.button("💾  บันทึกรายการ", use_container_width=True, type="primary")

    if submitted:
        if not name.strip():
            st.error("⚠️ กรุณากรอกชื่ออุปกรณ์ / วัสดุ")
        elif category == "— เลือกหมวดหมู่ —":
            st.error("⚠️ กรุณาเลือกหมวดหมู่")
        elif price <= 0:
            st.error("⚠️ กรุณากรอกราคาต่อหน่วย")
        else:
            save_image(receipt_img)  # เก็บไฟล์ในเซิร์ฟเวอร์ (ชั่วคราว)
            record = {
                "receipt_no": receipt_no_input.strip(),
                "name": name.strip(),
                "brand": brand.strip(),
                "store": store.strip(),
                "date": str(purchase_date),
                "price": float(price),
                "quantity": int(quantity),
                "total": float(price) * int(quantity),
                "category": category,
                "note": note.strip(),
            }
            try:
                with st.spinner("กำลังบันทึกลง Google Sheets..."):
                    append_row(record)
                st.session_state.autofill = None
                st.session_state.last_receipt_no = ""
                st.success(f"✅ บันทึก **{name}** ลง Google Sheets เรียบร้อย! ยอดรวม ฿{price * quantity:,.2f}")
                st.balloons()
            except Exception as e:
                st.error(f"❌ บันทึกไม่สำเร็จ: {e}")

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
            <div style="font-size:0.85rem; color:#4a5568; margin-top:6px;">ไปที่แท็บ "เพิ่มรายการ" เพื่อเริ่มบันทึก</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # แปลง type
        df["ราคาต่อหน่วย (บาท)"] = pd.to_numeric(df["ราคาต่อหน่วย (บาท)"], errors="coerce").fillna(0)
        df["จำนวน"] = pd.to_numeric(df["จำนวน"], errors="coerce").fillna(0).astype(int)
        df["ราคารวม"] = pd.to_numeric(df["ราคารวม"], errors="coerce").fillna(0)
        df["วันที่ซื้อ"] = pd.to_datetime(df["วันที่ซื้อ"], errors="coerce")

        # ── METRICS ───────────────────────────────────────────────────────
        total_all = df["ราคารวม"].sum()
        total_items = len(df)
        avg_price = df["ราคาต่อหน่วย (บาท)"].mean()
        top_cat = df.groupby("หมวดหมู่วัสดุ")["ราคารวม"].sum().idxmax() if len(df) > 0 else "-"

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
                <div class="metric-label">ราคาเฉลี่ย/หน่วย</div>
                <div class="metric-value">฿{avg_price:,.0f}</div>
            </div>""", unsafe_allow_html=True)
        with m4:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">หมวดหมู่สูงสุด</div>
                <div class="metric-value" style="font-size:0.9rem">{str(top_cat).split(' ',1)[-1] if top_cat != '-' else '-'}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

        # ── FILTERS ───────────────────────────────────────────────────────
        with st.expander("🔍  ตัวกรองข้อมูล", expanded=True):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                search = st.text_input("🔎 ค้นหาชื่อ / ร้านค้า / เลขใบเสร็จ", placeholder="พิมพ์เพื่อค้นหา...")
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

        # ── APPLY FILTERS ─────────────────────────────────────────────────
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
            start_d, end_d = date_range
            filtered = filtered[
                (filtered["วันที่ซื้อ"].dt.date >= start_d) &
                (filtered["วันที่ซื้อ"].dt.date <= end_d)
            ]

        # ── DISPLAY ──────────────────────────────────────────────────────
        sc1, sc2 = st.columns([3, 1])
        with sc1:
            st.markdown(f"<div style='color:#64748b; font-size:0.85rem; padding-top:8px'>แสดง <b style='color:#e2e8f0'>{len(filtered)}</b> จาก {len(df)} รายการ</div>", unsafe_allow_html=True)
        with sc2:
            if st.button("🔄  รีเฟรชข้อมูล", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        display_df = filtered.copy()
        if "วันที่ซื้อ" in display_df.columns:
            display_df["วันที่ซื้อ"] = display_df["วันที่ซื้อ"].dt.strftime("%d/%m/%Y").fillna("")
        display_df["ราคาต่อหน่วย (บาท)"] = display_df["ราคาต่อหน่วย (บาท)"].apply(lambda x: f"฿{x:,.2f}")
        display_df["ราคารวม"] = display_df["ราคารวม"].apply(lambda x: f"฿{x:,.2f}")

        st.dataframe(display_df, use_container_width=True, height=480, hide_index=True)

        # ── EXPORT ────────────────────────────────────────────────────────
        st.markdown("<div style='margin-top: 1rem'></div>", unsafe_allow_html=True)
        csv = filtered.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "⬇️  Export CSV", data=csv,
            file_name=f"expenses_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv", use_container_width=True,
        )

        # ── CHART ─────────────────────────────────────────────────────────
        if len(filtered) > 0:
            st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)
            st.markdown('<div class="section-header">📈 สรุปค่าใช้จ่ายตามหมวดหมู่</div>', unsafe_allow_html=True)
            cat_summary = (
                filtered.groupby("หมวดหมู่วัสดุ")["ราคารวม"]
                .sum().reset_index()
                .rename(columns={"ราคารวม": "ยอดรวม (บาท)"})
                .sort_values("ยอดรวม (บาท)", ascending=False)
            )
            st.bar_chart(cat_summary.set_index("หมวดหมู่วัสดุ"), color="#7dd3fc", height=300)
