import requests
from bs4 import BeautifulSoup
import json
import sys

# 監視したい商品のSKU
sku_numbers = ["YOUR_SKU1", "YOUR_SKU2"]    # ex."1234"
# Line Notify Token
line_notify_token = 'YOUR_TOKEN'

# 在庫ファイル名をコマンドライン引数から読み取り
args = sys.argv
if len(args) != 2:
    print("引数が足りません")
    sys.exit()
stock_fn = args[1]

# 前回の在庫数をファイルから読み込み
try:
    with open(stock_fn, 'r') as f:
        stock_last = json.load(f)
except Exception as e:
    stock_last = {}
    
stock_now = {}
for sku in sku_numbers:
    # 商品サイトからHTTP GET
    url = 'https://www.switch-science.com/catalog/' + sku + '/'
    response = requests.get(url)
    
    # 在庫数を抽出
    soup = BeautifulSoup(response.text, "html.parser")
    t = soup.find_all("script", {"type": "application/ld+json"})
    json_dict = json.loads(t[0].text)
    name = json_dict["name"]
    stock = json_dict["offers"][0]["availability"]
    
    # 在庫0の場合"http://schema.org/OutOfStock"が入る
    if 'OutOfStock' in stock:
        stock = '0'
    
    stock_now[sku] = stock

    # 例外処理
    if not sku in stock_last:
        continue
    
    # 在庫数が変動していたら通知する
    notification_message = ''
    if stock_now[sku] != stock_last[sku]:     # 在庫数変動あり
        # 通知文作成
        if stock_now[sku] == '0':
            notification_message += (name + ' が売れ切れました')
        elif stock_now[sku] == '多数' or (stock_last[sku] != '多数' and (int(stock_now[sku]) > int(stock_last[sku]))):
            notification_message += (name + ' の在庫が補充されました')
        else:
            notification_message += (name + ' が売れました')
        notification_message += "\n現在の在庫数: " + stock_now[sku]
        print(notification_message)
    
        # Line Notifyで通知
        line_notify_api = 'https://notify-api.line.me/api/notify'
        headers = {'Authorization': f'Bearer {line_notify_token}'}
        data = {'message': f'message: {notification_message}'}
        requests.post(line_notify_api, headers = headers, data = data)

# 在庫数をファイルに保存
with open(stock_fn, 'w') as f:
    json.dump(stock_now, f, ensure_ascii=False, indent=2)


