import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine
import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 1. 系統配置與 PDF 字體修復 ---
DB_FILE = "risk_words.txt"

def get_chinese_font():
    # 解決 PDF 顯示黑塊問題：優先搜索系統中文字體
    paths = [
        "C:/Windows/Fonts/msjh.ttc",    # Windows 微軟正黑
        "C:/Windows/Fonts/simhei.ttf",  # Windows 黑體
        "/System/Library/Fonts/STHeiti Light.ttc", # macOS
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc" # Linux
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont('ChineseFont', p))
                return 'ChineseFont'
            except: continue
    return 'Helvetica'

CHINESE_FONT = get_chinese_font()

def load_risk_words():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return ["治癒", "療效", "根治", "副作用"]

def save_risk_words(words):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        for w in words: f.write(f"{w}\n")

# --- 2. 登入邏輯 ---
st.set_page_config(page_title="跨境大健康 ERP V2.2.7", layout="wide")

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.title("🔒 跨境大健康 ERP 系統")
    pwd = st.text_input("請輸入授權密碼", type="password")
    if st.button("登入"):
        if pwd == "your_password": # ⚠️ 請在此修改密碼
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("❌ 密碼錯誤")
else:
    # --- 3. 數據加載與處理 ---
    try:
        products, orders, sales_stats = shopify_engine.get_full_data()
        df_p = pd.DataFrame(products)
        df_o = pd.DataFrame(orders)
        
        # 庫存欄位識別與預警設定
        stock_col = "現貨庫存" if "現貨庫存" in df_p.columns else ("現有庫存" if "現有庫存" in df_p.columns else "庫存")
        df_p["預警數量"] = 50 
        
        # 銷售彙總數據準備
        summary_data = []
        for p_name, qty in sales_stats.items():
            price = df_p[df_p["產品名稱"] == p_name]["售價"].iloc[0] if p_name in df_p["產品名稱"].values else 0
            summary_data.append({"產品名稱": p_name, "銷售數量": qty, "銷售總額": qty * price})
        df_summary = pd.DataFrame(summary_data).sort_values("銷售數量", ascending=False)

        # 物流數據準備 (確保不只有金額)
        log_fields = ["Order_Number", "name", "Fulfillment_Status", "fulfillment_status", "Financial_Status", "Total_USD"]
        valid_log_fields = [c for c in log_fields if c in df_o.columns]
        df_logistics = df_o[valid_log_fields] if len(valid_log_fields) > 0 else df_o

    except Exception as e:
        st.error(f"數據加載失敗: {e}"); st.stop()

    # --- 4. 側邊欄 ---
    with st.sidebar:
        st.title("👤 管理中心")
        if st.button("🔄 同步 Shopify 數據"):
            st.cache_data.clear(); st.rerun()
        if st.button("🚪 安全登出"):
            st.session_state["password_correct"] = False; st.rerun()
        st.info("版本: V 2.2.7 (Excel 數據補完版)")

    # --- 5. 分頁功能 ---
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    # --- Tab 1: 庫存管理 (純淨版：無成本售價) ---
    with tab1:
        st.header("📦 庫存實時監控")
        
        c_i1, c_i2, _ = st.columns([1, 1, 3])
        with c_i1:
            inv_xl = io.BytesIO()
            with pd.ExcelWriter(inv_xl, engine='xlsxwriter') as wr:
                # 庫存 Excel 僅匯出 名稱、庫存、預警數
                df_p[["產品名稱", stock_col, "預警數量"]].to_excel(wr, index=False, sheet_name='庫存清單')
            st.download_button("📊 匯出庫存 Excel", data=inv_xl.getvalue(), file_name='Inventory_Report.xlsx')
        
        with c_i2:
            inv_pdf = io.BytesIO()
            c = canvas.Canvas(inv_pdf, pagesize=A4); c.setFont(CHINESE_FONT, 16)
            c.drawString(100, 800, "庫存管理報告 (Inventory)"); c.save()
            st.download_button("📄 匯出庫存 PDF", data=inv_pdf.getvalue(), file_name='Inventory_Report.pdf')

        st.divider()
        # 缺貨提醒
        low_stock = df_p[df_p[stock_col] < df_p["預警數量"]]
        if not low_stock.empty:
            st.error(f"⚠️ 以下產品低於預警數量 (50)：")
            st.dataframe(low_stock[["產品名稱", stock_col, "預警數量"]], use_container_width=True)
        
        st.subheader("📋 實時庫存清單 (僅展示庫存數據)")
        # 頁面顯示隱藏成本與售價
        st.dataframe(df_p[["產品名稱", stock_col, "預警數量"]], use_container_width=True)

    # --- Tab 2: 營運看板 (Excel 三合一匯出) ---
    with tab2:
        st.header("💰 營運與銷售分析")
        
        # A. 核心指標
        m1, m2, m3, m4 = st.columns(4)
        total_rev = df_o['Total_USD'].sum() if 'Total_USD' in df_o.columns else 0
        total_profit = sum(sales_stats.get(p['產品名稱'], 0) * p['毛利'] for p in products)
        m1.metric("總銷售額", f"${total_rev:,.2f}")
        m2.metric("總真實利潤", f"${total_profit:,.2f}")
        m3.metric("訂單總數", len(df_o))
        m4.metric("平均毛利率", f"{(df_p['毛利率'].mean()):.1f}%")

        # B. 營運數據匯出中心
        st.write("### 📥 營運數據全表導出")
        c_o1, c_o2, _ = st.columns([1, 1, 3])
        
        with c_o1:
            op_xl = io.BytesIO()
            with pd.ExcelWriter(op_xl, engine='xlsxwriter') as writer:
                # 匯出要求的 3 個 Sheet
                df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].to_excel(writer, index=False, sheet_name='產品財務獲利明細')
                df_summary.to_excel(writer, index=False, sheet_name='產品銷售情況彙總')
                df_logistics.to_excel(writer, index=False, sheet_name='訂單即時物流狀態')
            st.download_button("📊 匯出營運全表 Excel", data=op_xl.getvalue(), file_name='Full_Operation_Report.xlsx')

        with c_o2:
            op_pdf = io.BytesIO()
            c = canvas.Canvas(op_pdf, pagesize=A4); c.setFont(CHINESE_FONT, 16)
            c.drawString(100, 800, f"營運綜合分析報告 - 總銷售: ${total_rev:,.2f}"); c.save()
            st.download_button("📄 匯出營運 PDF", data=op_pdf.getvalue(), file_name='Full_Operation_Report.pdf')

        st.divider()
        # C. 財務表格
        st.subheader("💵 產品財務獲利明細")
        st.dataframe(df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].style.format({"售價":"${:.2f}","成本":"${:.2f}","毛利率":"{:.1f}%"}), use_container_width=True)

        # D. 銷售情況彙總
        st.subheader("📋 產品銷售情況彙總")
        st.dataframe(df_summary.style.format({"銷售總額": "${:.2f}"}), use_container_width=True)

        # E. 圖表
        st.subheader("📊 產品銷售數量分布圖")
        fig, ax = plt.subplots(figsize=(10, 3.5))
        if not df_summary.empty:
            ax.bar(df_summary["產品名稱"], df_summary["銷售數量"], color='#3498db')
            plt.xticks(rotation=30, fontsize=8); plt.tight_layout()
            st.pyplot(fig)

        st.divider()
        # F. 物流表格 (確保展示正確欄位)
        st.subheader("🚚 訂單即時物流狀態")
        st.dataframe(df_logistics, use_container_width=True)

    # --- Tab 3: 文案合規 ---
    with tab3:
        st.header("🔍 文案檢測系統")
        cl, cr = st.columns([2, 1])
        with cr:
            st.subheader("🛡️ 字庫管理")
            current = load_risk_words()
            edited = st.text_area("編輯禁語清單", value="\n".join(current), height=300)
            if st.button("💾 儲存並更新"):
                save_risk_words([w.strip() for w in edited.split("\n") if w.strip()])
                st.success("字庫已更新"); st.rerun()
        with cl:
            st.subheader("📝 文案掃描")
            input_text = st.text_area("請貼入文案內容...", height=200)
            if st.button("🚀 開始檢測"):
                risks = load_risk_words()
                found = [w for w in risks if w in input_text]
                if found: st.error(f"❌ 發現禁語：{', '.join(found)}")
                else: st.success("✅ 檢測通過")
