import requests
import streamlit as st

SHOPIFY_ACCESS_TOKEN = st.secrets["SHOPIFY_ACCESS_TOKEN"]
SHOP_URL = st.secrets["SHOP_URL"]
API_VERSION = "2024-04"

def get_full_data():
    """一次性抓取產品、庫存、真實成本及訂單資訊"""
    headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}
    
    try:
        # 1. 抓取產品與成本
        p_url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/products.json"
        p_res = requests.get(p_url, headers=headers, timeout=10)
        
        all_products = []
        if p_res.status_code == 200:
            for p in p_res.json().get('products', []):
                variant = p['variants'][0]
                inv_id = variant.get('inventory_item_id')
                price = float(variant.get('price', 0))
                
                # 精準抓取 $6.99 那個欄位
                cost = 0.0
                if inv_id:
                    c_url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/inventory_items/{inv_id}.json"
                    c_res = requests.get(c_url, headers=headers, timeout=5)
                    if c_res.status_code == 200:
                        cost_str = c_res.json().get('inventory_item', {}).get('cost')
                        cost = float(cost_str) if cost_str else 0.0
                
                all_products.append({
                    "產品名稱": p['title'],
                    "現貨庫存": variant.get('inventory_quantity', 0),
                    "售價": price,
                    "成本": cost,
                    "毛利": price - cost,
                    "毛利率": ((price - cost) / price * 100) if price > 0 else 0
                })

        # 2. 抓取訂單
        o_url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/orders.json?status=any"
        o_res = requests.get(o_url, headers=headers, timeout=10)
        all_orders = []
        if o_res.status_code == 200:
            for o in o_res.json().get('orders', []):
                all_orders.append({
                    "Order_ID": o.get('name'),
                    "Total_USD": float(o.get('total_price', 0)),
                    "Status": "Shipped" if o.get('fulfillment_status') == 'fulfilled' else "Pending"
                })
        
        return all_products, all_orders
    except:
        return None, None
