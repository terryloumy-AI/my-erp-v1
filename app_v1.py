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

# --- 1. 字體與配置 (解決 PDF 黑塊) ---
def get_chinese_font():
    paths = ["C:/Windows/Fonts/msjh.ttc", "C:/Windows/Fonts/simhei.ttf", "/System/Library/Fonts/STHeiti Light.ttc", "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"]
    for p in paths:
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont('ChineseFont', p))
                return 'ChineseFont'
            except: continue
    return 'Helvetica'

CHINESE_FONT = get_chinese_font()

# --- 2. 登入邏輯 ---
st.set_page_config(page_title="跨境大健康 ERP V2.3.0", layout="wide")

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.title("🔒 跨境大健康 ERP 系統")
    pwd = st.text_input("輸入授權密碼", type="password")
    if st.button("登入"):
        if pwd == "your_password": # ⚠️ 請在此修改密碼
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("密碼錯誤")
else:
    # --- 3. 數據核心 (嚴格準備導出對象) ---
    try:
        products, orders, sales_stats = shopify_engine.get_full_data()
        df_p = pd.DataFrame(products)
        df_o = pd.DataFrame(orders)
        
        # 庫存定義
        stock_col = "現貨庫存" if "現貨庫存" in df_p.columns else ("現有庫存" if "現有庫存" in df_p.columns else "庫存")
        df_p["預警數量"] = 50 
        
        # 數據 A：營運看板 - 銷售情況彙總
        sum_list = []
        for p_name, qty in sales_stats.items():
            price = df_p[df_p["產品名稱"] == p_name]["售價"].iloc[0] if p_name in df_p["產品名稱"].values else 0
            sum_list.append({"產品名稱": p_name, "銷售數量": qty, "銷售總額": qty * price})
        df_summary = pd.DataFrame(sum_list).sort_values("銷售數量", ascending=False)

        # 數據 B：營運看板 - 物流數據 (還原物流屬性，不只有金額)
        log_fields = ["Order_Number", "name", "Fulfillment_Status", "fulfillment_status", "Financial_Status", "Total_USD"]
        valid_cols = [c for c in log_fields if c in df_o.columns]
        df_logistics_final = df_o[valid_cols].copy() if valid_cols else df_o.copy()

    except Exception as e:
        st.error(f"同步失敗: {e}"); st.stop()

    # --- 4. 左邊欄 (修正：回歸！) ---
    with st.sidebar:
        st.title("👤 管理員中心")
        if st.button("🔄 同步 Shopify 數據"):
            st.cache_data.clear(); st.rerun()
        st.divider()
        if st.button("🚪 安全登出"):
            st.session_state["password_correct"] = False; st.rerun()
        st.info("版本: V 2.3.0 (穩定整合版)")

    # --- 5. 分頁 ---
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    # --- Tab 1: 庫存管理 (隱藏成本與售價) ---
    with tab1:
        st.header("📦 庫存管理中心")
        c1, c2, _ = st.columns([1, 1, 3])
        with c1:
            inv_xl = io.BytesIO()
            with pd.ExcelWriter(inv_xl, engine='xlsxwriter') as wr:
                df_p[["產品名稱", stock_col, "預警數量"]].to_excel(wr, index=False, sheet_name='Inventory')
            st.download_button("📊 匯出庫存 Excel", data=inv_xl.getvalue(), file_name='Inventory_Report.xlsx')
        with c2:
            inv_pdf = io.BytesIO()
            c = canvas.Canvas(inv_pdf, pagesize=A4); c.setFont(CHINESE_FONT, 16); c.drawString(100, 800, "庫存清單"); c.save()
            st.download_button("📄 匯出庫存 PDF", data=inv_pdf.getvalue(), file_name='Inventory_Report.pdf')

        st.divider()
        st.subheader("📋 實時庫存清單 (僅展示現貨與預警)")
        st.dataframe(df_p[["產品名稱", stock_col, "預警數量"]], use_container_width=True)

    # --- Tab 2: 營運看板 ---
    with tab2:
        st.header("💰 營運分析看板")
        
        m1, m2, m3, m4 = st.columns(4)
        total_rev = df_o['Total_USD'].sum() if 'Total_USD' in df_o.columns else 0
        total_profit = sum(sales_stats.get(p['產品名稱'], 0) * p['毛利'] for p in products)
        m1.metric("總銷售額", f"${total_rev:,.2f}")
        m2.metric("總利潤", f"${total_profit:,.2f}")
        m3.metric("訂單數", len(df_o))
        m4.metric("平均毛利", f"{(df_p['毛利率'].mean()):.1f}%")

        # 📥 營運 Excel 導出 (修復：手動確保三個 Sheet)
        st.write("### 📥 數據導出中心")
        co1, co2, _ = st.columns([1, 1, 3])
        with co1:
            op_xl = io.BytesIO()
            with pd.ExcelWriter(op_xl, engine='xlsxwriter') as writer:
                # 這裡強制導出您要求的三個數據集
                df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].to_excel(writer, index=False, sheet_name='產品財務獲利明細')
                df_summary.to_excel(writer, index=False, sheet_name='產品銷售情況彙總')
                df_logistics_final.to_excel(writer, index=False, sheet_name='訂單即時物流狀態')
            st.download_button("📊 匯出營運 Excel (全表)", data=op_xl.getvalue(), file_name='Operations_Report.xlsx')
        
        with co2:
            op_pdf = io.BytesIO()
            c = canvas.Canvas(op_pdf, pagesize=A4); c.setFont(CHINESE_FONT, 16); c.drawString(100, 800, "營運報告"); c.save()
            st.download_button("📄 匯出營運 PDF", data=op_pdf.getvalue(), file_name='Operations_Report.pdf')

        st.divider()
        st.subheader("💵 產品財務獲利明細")
        st.dataframe(df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].style.format({"售價":"${:.2f}","成本":"${:.2f}"}), use_container_width=True)

        st.subheader("📋 產品銷售情況彙總")
        st.dataframe(df_summary.style.format({"銷售總額": "${:.2f}"}), use_container_width=True)

        st.subheader("📊 產品銷售數量分布")
        fig, ax = plt.subplots(figsize=(10, 3.5))
        if not df_summary.empty:
            ax.bar(df_summary["產品名稱"], df_summary["銷售數量"], color='#3498db')
            plt.xticks(rotation=30, fontsize=8); plt.tight_layout()
            st.pyplot(fig)

        st.divider()
        # 物流表格回歸：確保顯示的是 df_logistics_final
        st.subheader("🚚 訂單即時物流狀態")
        st.dataframe(df_logistics_final, use_container_width=True)

    # --- Tab 3: 文案合規 ---
    with tab3:
        st.header("🔍 文案合規檢測")
        cl, cr = st.columns([2, 1])
        with cr:
            st.subheader("🛡️ 字庫管理")
            if os.path.exists("risk_words.txt"):
                with open("risk_words.txt", "r", encoding="utf-8") as f: words = f.read()
            else: words = "治癒\n療效\n根治"
            edited = st.text_area("編輯禁語 (每行一個)", value=words, height=300)
            if st.button("💾 儲存字庫"):
                with open("risk_words.txt", "w", encoding="utf-8") as f: f.write(edited)
                st.success("已儲存"); st.rerun()
        with cl:
            st.subheader("📝 內容掃描")
            text = st.text_area("在此輸入文案...", height=200)
            if st.button("🚀 開始檢測"):
                risk_list = [w.strip() for w in edited.split("\n") if w.strip()]
                found = [w for w in risk_list if w in text]
                if found: st.error(f"❌ 發現禁語：{', '.join(found)}")
                else: st.success("✅ 文案合規")
