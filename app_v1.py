import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine
import io
import os
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 1. 系統字體配置 ---
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

# --- 2. 動態日期邏輯 (讓 2026 的測試數據永遠變為當前日期) ---
def make_dates_dynamic(df):
    if df.empty: return df
    
    # 假設 Shopify 訂單日期欄位為 'created_at' 或 'processed_at'
    date_col = 'created_at' if 'created_at' in df.columns else ('processed_at' if 'processed_at' in df.columns else None)
    
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col])
        # 找出數據中的最大日期
        latest_data_date = df[date_col].max()
        # 計算與今天日期的差距
        time_offset = datetime.now() - latest_data_date
        # 將所有日期整體推移到現在
        df[date_col] = df[date_col] + time_offset
        # 轉換回易讀字串格式
        df['顯示日期'] = df[date_col].dt.strftime('%Y-%m-%d %H:%M')
    return df

# --- 3. 登入系統 ---
st.set_page_config(page_title="跨境大健康 ERP V2.3.1", layout="wide")

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.title("🔒 跨境大健康 ERP 系統")
    pwd = st.text_input("輸入授權密碼", type="password")
    if st.button("登入"):
        if pwd == "123456": # ⚠️ 密碼請自行修改
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("密碼錯誤")
else:
    # --- 4. 數據核心 ---
    try:
        products, orders, sales_stats = shopify_engine.get_full_data()
        df_p = pd.DataFrame(products)
        df_o = pd.DataFrame(orders)
        
        # 執行日期動態化
        df_o = make_dates_dynamic(df_o)
        
        # 庫存定義與預警
        stock_col = "現貨庫存" if "現貨庫存" in df_p.columns else ("現有庫存" if "現有庫存" in df_p.columns else "庫存")
        df_p["預警數量"] = 50 
        
        # A. 營運匯總數據
        sum_list = []
        for p_name, qty in sales_stats.items():
            price = df_p[df_p["產品名稱"] == p_name]["售價"].iloc[0] if p_name in df_p["產品名稱"].values else 0
            sum_list.append({"產品名稱": p_name, "銷售數量": qty, "銷售總額": qty * price})
        df_summary = pd.DataFrame(sum_list).sort_values("銷售數量", ascending=False)

        # B. 物流數據 (修正：回歸物流欄位，不只是金額)
        log_fields = ["Order_Number", "name", "Fulfillment_Status", "fulfillment_status", "Financial_Status", "Total_USD", "顯示日期"]
        valid_log_cols = [c for c in log_fields if c in df_o.columns]
        df_logistics_final = df_o[valid_log_cols].copy()

    except Exception as e:
        st.error(f"數據讀取失敗: {e}"); st.stop()

    # --- 5. 左邊欄 (確保存在) ---
    with st.sidebar:
        st.title("👤 系統管理")
        if st.button("🔄 同步數據"):
            st.cache_data.clear(); st.rerun()
        st.divider()
        if st.button("🚪 安全登出"):
            st.session_state["password_correct"] = False; st.rerun()
        st.info("版本: V 2.3.1 (動態演示版)")

    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    # --- Tab 1: 庫存管理 (隱藏成本售價) ---
    with tab1:
        st.header("📦 庫存即時監控")
        c1, c2, _ = st.columns([1, 1, 3])
        with c1:
            inv_xl = io.BytesIO()
            with pd.ExcelWriter(inv_xl, engine='xlsxwriter') as wr:
                df_p[["產品名稱", stock_col, "預警數量"]].to_excel(wr, index=False, sheet_name='庫存清單')
            st.download_button("📊 匯出庫存 Excel", data=inv_xl.getvalue(), file_name='Inventory_Report.xlsx')
        
        st.divider()
        st.subheader("📋 實時庫存清單 (無價格敏感數據)")
        st.dataframe(df_p[["產品名稱", stock_col, "預警數量"]], use_container_width=True)

    # --- Tab 2: 營運看板 (Excel 三合一匯出) ---
    with tab2:
        st.header("💰 營運分析看板")
        
        m1, m2, m3, m4 = st.columns(4)
        total_rev = df_o['Total_USD'].sum() if 'Total_USD' in df_o.columns else 0
        total_profit = sum(sales_stats.get(p['產品名稱'], 0) * p['毛利'] for p in products)
        m1.metric("總銷售額", f"${total_rev:,.2f}")
        m2.metric("總利潤", f"${total_profit:,.2f}")
        m3.metric("訂單數", len(df_o))
        m4.metric("平均毛利", f"{(df_p['毛利率'].mean()):.1f}%")

        st.write("### 📥 數據導出中心")
        co1, co2, _ = st.columns([1, 1, 3])
        with co1:
            op_xl = io.BytesIO()
            with pd.ExcelWriter(op_xl, engine='xlsxwriter') as writer:
                # 這裡強制導出 3 個 Sheet
                df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].to_excel(writer, index=False, sheet_name='產品財務獲利明細')
                df_summary.to_excel(writer, index=False, sheet_name='產品銷售情況彙總')
                df_logistics_final.to_excel(writer, index=False, sheet_name='訂單即時物流狀態')
            st.download_button("📊 匯出營運全表 Excel", data=op_xl.getvalue(), file_name='Full_Report.xlsx')

        st.divider()
        st.subheader("💵 產品財務獲利明細")
        st.dataframe(df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].style.format({"售價":"${:.2f}","成本":"${:.2f}"}), use_container_width=True)

        st.subheader("📋 產品銷售情況彙總")
        st.dataframe(df_summary.style.format({"銷售總額": "${:.2f}"}), use_container_width=True)

        st.subheader("🚚 訂單即時物流狀態 (含動態日期)")
        st.dataframe(df_logistics_final, use_container_width=True)

    # --- Tab 3: 文案合規 ---
    with tab3:
        st.header("🔍 文案檢測")
        input_text = st.text_area("貼入文案內容...", height=200)
        if st.button("🚀 開始檢測"):
            # 簡化檢測邏輯
            risks = ["治癒", "療效", "根治", "副作用"]
            found = [w for w in risks if w in input_text]
            if found: st.error(f"❌ 發現禁語：{', '.join(found)}")
            else: st.success("✅ 檢測通過")
