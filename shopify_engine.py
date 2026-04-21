import requests
import streamlit as st

# 從 Secrets 讀取密鑰
SHOPIFY_ACCESS_TOKEN = st.secrets["SHOPIFY_ACCESS_TOKEN"]
SHOP_URL = st.secrets["SHOP_URL"]
API_VERSION = "2024-01"

def get_real_inventory():
    """抓取產品庫存 (保持原功能)"""
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/products.json"
    headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            products = response.json().get('products', [])
            return [{"產品名稱": p['title'], "現貨庫存": p['variants'][0].get('inventory_quantity', 0), "預警門檻": 50} for p in products]
        return None
    except: return None

def get_orders_and_profit():
    """抓取訂單、計算毛利與物流狀態"""
    # 抓取最近 50 筆訂單
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/orders.json?status=any&limit=50"
    headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            orders = response.json().get('orders', [])
            order_data = []
            for o in orders:
                # 物流狀態轉換為中文
                f_status = o.get('fulfillment_status')
                if f_status == 'fulfilled': status_cn = "🟢 已發貨"
                elif f_status is None: status_cn = "🟡 待處理"
                else: status_cn = f"🔵 {f_status}"

                order_data.append({
                    "訂單編號": o.get('name'),
                    "日期": o.get('created_at')[:10],
                    "客戶": o.get('customer', {}).get('first_name', '訪客'),
                    "總金額": float(o.get('total_price', 0)),
                    "物流狀態": status_cn,
                    "商品數量": len(o.get('line_items', [])),
                    # 簡易毛利計算：假設平均毛利率為 40% (未來可對接真實成本)
                    "預估毛利": float(o.get('total_price', 0)) * 0.4 
                })
            return order_data
        return None
    except: return None
