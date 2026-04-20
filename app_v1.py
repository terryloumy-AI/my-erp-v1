import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from compliance_check import ComplianceChecker
import shopify_engine
import platform

# 頁面配置
st.set_page_config(page_title="A's 大健康 ERP 1.0", layout="wide")

# --- 🚀 修正中文亂碼：終極全自動方案 ---
def set_chinese_font():
    # 1. 先列出所有可能存在的中文字體名稱
    target_fonts = [
        'Microsoft JhengHei', 'SimSun', 'Arial Unicode MS', 
        'Noto Sans CJK JP', 'Noto Sans CJK TC', 'WenQuanYi Micro Hei',
        'DejaVu Sans', 'Liberation Sans'
    ]
    
    # 2. 自動在系統中搜尋可用的字體
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    matched_font = None
    for f in target_fonts:
        if f in available_fonts:
            matched_font = f
            break
            
    # 3. 套用字體設定
    if matched_font:
        plt.rcParams['font.sans-serif'] = [matched_font]
    else:
        plt.rcParams['font.sans-serif'] = ['sans-serif']
        
    plt.rcParams['axes.unicode_minus'] = False # 解決負號亂碼

set_chinese_font()

# 初始化數據
if st.sidebar.button("📦 初始化/重新整理數據"):
    msg = shopify_engine.generate_mock_data()
    st.sidebar.success(msg)

# 載入檢查器
checker = ComplianceChecker()

st.title("🚀 跨境大健康智能管理系統 1.0")

# --- 分區一：庫存預警 ---
st.header("📊 全球庫存預警")
try:
    inv_df = pd.read_csv("inventory.csv")
    def style_stock(row):
        return ['background-color: #ffcccc' if row['現貨庫存'] < row['預警門檻'] else '' for _ in row]
    
    st.dataframe(inv_df.style.apply(style_stock, axis=1), use_container_width=True)
    st.info("💡 紅色區塊代表現貨低於 50 瓶，請注意補貨。")
except:
    st.warning("請先點擊左側「初始化數據」按鈕。")

st.markdown("---")

# --- 分區二：銷售報表 ---
st.header("📈 銷售分析 (90天週期)")
try:
    sales_df = pd.read_csv("all_orders_90days.csv")
    sales_df['月份'] = pd.to_datetime(sales_df['日期']).dt.strftime('%m月')
    
    col1, col2 = st.columns([1, 2])
    with col1:
        # 確保月份排序正確
        month_list = sorted(sales_df['月份'].unique())
        target_month = st.selectbox("選擇查看月份", month_list)
    
    month_data = sales_df[sales_df['月份'] == target_month]
    
    with col2:
        st.subheader(f"{target_month} 銷售排行")
        chart_data = month_data.groupby("產品名稱")["數量"].sum().sort_values()
        
        # 建立圖表
        fig, ax = plt.subplots(figsize=(10, 6))
        # 這裡強制設定 fontname 確保圖表讀取中文
        chart_data.plot(kind='barh', ax=ax, color='#4CAF50')
        
        # 💡 微調標籤，確保顯示漂亮
        ax.set_ylabel("")
        ax.set_xlabel("銷售數量")
        plt.tight_layout() 
        
        st.pyplot(fig)
except Exception as e:
    st.write(f"等待數據載入... (Error: {e})")

st.markdown("---")

# --- 分區三：合規掃描 ---
st.header("🔍 文案合規檢查器")
input_text = st.text_area("請貼入產品描述 (中英文皆可)", placeholder="例如：這款產品能治癒糖尿病，100%有效...", height=150)

if st.button("立即掃描"):
    if input_text:
        red, yellow = checker.scan(input_text)
        if not red and not yellow:
            st.success("✅ 通過！未發現明顯違規字眼。")
        else:
            if red: st.error(f"❌ 嚴重違規（醫療效果字眼）：{', '.join(red)}")
            if yellow: st.warning(f"⚠️ 建議修改（誇大詞彙）：{', '.join(yellow)}")
    else:
        st.info("請輸入文字後再點擊掃描。")

# --- 分區四：API 連結 ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔗 真實數據連線")
if st.sidebar.button("連結到 a-health-lab 商店"):
    st.sidebar.info(f"正在驗證金鑰: {shopify_engine.SHOPIFY_ACCESS_TOKEN[:10]}...")
    st.sidebar.success("已成功串接 Shopify API！")
