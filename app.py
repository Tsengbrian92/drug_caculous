from flask import Flask, request, render_template, jsonify
import requests
from bs4 import BeautifulSoup
import math

app = Flask(__name__)

def fetch_exchange_rate():
    """
    從台灣銀行官網爬取最新的日圓賣出即期匯率
    """
    url = 'https://rate.bot.com.tw/xrt?Lang=zh-TW'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        rows = soup.find('table', {'title': '牌告匯率'}).find('tbody').find_all('tr')
        for row in rows:
            currency = row.find('div', {'class': 'visible-phone'}).text.strip()
            if "日圓" in currency:
                sell_rate = row.find_all('td')[4].text.strip()
                return math.ceil(float(sell_rate) * 100) / 100  # 無條件進位到小數點第2位

        return None

    except requests.RequestException:
        return None

def calculate_price(currency_type, price, weight, exchange_rate):
    """
    計算最終售價
    """
    price = float(price)
    weight = float(weight)

    if currency_type == "twd":
        final_price = (price * 0.96 + weight * 0.3) * 1.2
    elif currency_type == "jpy":
        final_price = (price * exchange_rate + weight * 0.3) * 1.2
    else:
        return None

    return round(final_price)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/calculate", methods=["POST"])
def calculate():
    currency_type = request.form.get("currency_type")
    price = request.form.get("price")
    weight = request.form.get("weight")

    if not price or not weight or not price.isdigit() or not weight.isdigit():
        return jsonify({"error": "請輸入有效的價格和重量"}), 400

    exchange_rate = fetch_exchange_rate()
    if not exchange_rate:
        return jsonify({"error": "無法取得日圓匯率"}), 500

    final_price = calculate_price(currency_type, price, weight, exchange_rate)
    if final_price is None:
        return jsonify({"error": "計算錯誤"}), 400

    shopee_price = round(final_price * 1.15)

    return jsonify({
        "final_price": final_price,
        "shopee_price": shopee_price,
        "exchange_rate": exchange_rate
    })

if __name__ == "__main__":
    app.run(debug=True)
