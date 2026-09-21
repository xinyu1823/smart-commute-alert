import os
import requests

# 從環境變數讀取 Telegram 設定（受 GitHub Secrets 保護）
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 設定預設座標（以台北市為例：緯度 25.033, 經度 121.5654）
LAT = 25.033
LON = 121.5654


def fetch_weather_and_aqi():
    """串聯天氣與空氣品質 API 取得當日預報數據"""
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
        "&hourly=temperature_2m,precipitation_probability&forecast_days=1"
    )
    air_url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={LAT}&longitude={LON}"
        "&hourly=us_aqi&forecast_days=1"
    )

    try:
        # 取得天氣資料
        res_w = requests.get(weather_url, timeout=10)
        res_w.raise_for_status()
        w_data = res_w.json()
        hourly = w_data.get("hourly", {})
        temps = hourly.get("temperature_2m", [0])
        precips = hourly.get("precipitation_probability", [0])

        max_temp = max(temps) if temps else 0
        max_precip = max(precips) if precips else 0

        # 取得空氣品質資料
        res_a = requests.get(air_url, timeout=10)
        res_a.raise_for_status()
        a_data = res_a.json()
        aqi_hourly = a_data.get("hourly", {}).get("us_aqi", [0])

        max_aqi = max(aqi_hourly) if aqi_hourly else 0

        return max_temp, max_precip, max_aqi

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 錯誤發生: {http_err}")
        raise
    except Exception as err:
        print(f"發生其他錯誤: {err}")
        raise


def generate_advice(max_temp, max_precip, max_aqi):
    """依據多個條件產生可同時成立的通勤建議"""
    advice_list = []

    # 1. 降雨機率達 60% 時提醒攜帶雨傘
    if max_precip >= 60:
        advice_list.append("☔ 降雨機率達 60% 以上，出門記得攜帶雨傘！")

    # 2. 最高溫度達 33°C 時提醒防曬與補充水分
    if max_temp >= 33:
        advice_list.append("☀️ 最高氣溫達 33°C 以上，請注意防曬並多補充水分！")

    # 3. AQI 達 100 時提醒配戴口罩
    if max_aqi >= 100:
        advice_list.append("😷 空氣品質 AQI 達 100 以上，建議配戴口罩！")

    # 4. 所有條件正常時，顯示適合外出通勤
    if not advice_list:
        advice_list.append("✨ 天氣與空氣品質皆良好，非常適合外出通勤，祝您有個美好的一天！")

    message = (
        "🏙️ *【智慧通勤風險通知】*\n\n"
        f"🌡️ 最高溫度: {max_temp}°C\n"
        f"🌧️ 最高降雨機率: {max_precip}%\n"
        f"🌫️ 最高 AQI: {max_aqi}\n\n"
        "💡 *通勤建議：*\n"
        + "\n".join(advice_list)
    )
    return message


def send_telegram_message(message):
    """透過 Telegram Bot 發送通知訊息"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("錯誤：未設定 Telegram Bot Token 或 Chat ID 環境變數。")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    print("Telegram 通知發送成功！")


if __name__ == "__main__":
    print("正在取得天氣與空氣品質資料...")
    temp, precip, aqi = fetch_weather_and_aqi()
    print(f"取得資料 -> 溫度: {temp}°C, 降雨機率: {precip}%, AQI: {aqi}")

    message = generate_advice(temp, precip, aqi)
    send_telegram_message(message)
