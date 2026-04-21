import requests
import streamlit as st

# 從 Secrets 讀取密鑰
SHOPIFY_ACCESS_TOKEN = st.secrets["SHOPIFY_ACCESS_TOKEN"]
SHOP_URL = st.secrets["SHOP_URL"]
API_VERSION = "2024-04"

def get_real_inventory():
    """抓取產品庫存"""
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
    """抓取訂單、計算利潤並解決圖表亂碼問題"""
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/orders.json?status=any"
    headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            orders = response.json().get('orders', [])
            if not orders: return None
                
            order_data = []
            for o in orders:
                # 這裡改用英文標籤，避免圖表出現方塊亂碼
                f_status = o.get('fulfillment_status')
                if f_status == 'fulfilled': status_label = "Shipped"
                elif f_status is None or f_status == 'null': status_label = "Pending"
                else: status_label = str(f_status).capitalize()

                order_data.append({
                    "Order_ID": o.get('name'),
                    "Date": o.get('created_at')[:10],
                    "Total_USD": float(o.get('total_price', 0)),
                    "Status": status_label,
                    "Profit_Est": float(o.get('total_price', 0)) * 0.4 
                })
            return order_data
        return None
    except: return None
