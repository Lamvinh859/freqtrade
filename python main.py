import os
import time
import requests
import schedule
from tradingview_ta import TA_Handler, Interval

# Lấy thông tin cấu hình từ biến môi trường trên Render
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(message):
    """Hàm gửi tin nhắn đến Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Lỗi: Chưa cấu hình TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Lỗi gửi Telegram: {response.text}")
    except Exception as e:
        print(f"Lỗi kết nối Telegram: {e}")

def analyze_asset(symbol, exchange, screener, name):
    """Hàm lấy dữ liệu phân tích kỹ thuật từ TradingView"""
    try:
        handler = TA_Handler(
            symbol=symbol,
            exchange=exchange,
            screener=screener,
            interval=Interval.INTERVAL_1_HOUR
        )
        analysis = handler.get_analysis()
        summary = analysis.summary
        indicators = analysis.indicators
        
        # Lấy các chỉ số cần thiết
        price = indicators.get("close", "N/A")
        rsi = indicators.get("RSI", "N/A")
        recommendation = summary.get("RECOMMENDATION", "NEUTRAL")
        
        # Chuyển đổi khuyến nghị sang tiếng Việt cho dễ đọc
        rec_map = {
            "STRONG_BUY": "🟢 MUA MẠNH",
            "BUY": "🟢 MUA",
            "NEUTRAL": "⚪ TRUNG LẬP",
            "SELL": "🔴 BÁN",
            "STRONG_SELL": "🔴 BÁN MẠNH"
        }
        rec_vn = rec_map.get(recommendation, recommendation)
        
        # Định dạng thông báo gửi về Telegram
        msg = (
            f"📊 **BÁO CÁO KỸ THUẬT - {name}**\n"
            f"───────────────────\n"
            f"💰 **Giá hiện tại:** `{price}`\n"
            f"📈 **Chỉ số RSI (1H):** `{rsi}`\n"
            f"🔮 **Nhận định:** *{rec_vn}*\n"
            f"───────────────────\n"
            f"⏱️ Khung thời gian: `1 Giờ`"
        )
        return msg
    except Exception as e:
        return f"⚠️ Không thể lấy dữ liệu cho {name}: {str(e)}"

def job():
    """Hàm thực hiện quét thị trường và gửi báo cáo"""
    print("Đang quét dữ liệu thị trường...")
    
    # 1. Phân tích Vàng (XAUUSD trên sàn OANDA)
    gold_msg = analyze_asset(
        symbol="XAUUSD",
        exchange="OANDA",
        screener="forex",
        name="VÀNG (XAUUSD)"
    )
    send_telegram(gold_msg)
    
    time.sleep(3) # Nghỉ 3 giây tránh bị nghẽn request
    
    # 2. Phân tích Dầu WTI (USOIL trên sàn TVC)
    oil_msg = analyze_asset(
        symbol="USOIL",
        exchange="TVC",
        screener="cfd",
        name="DẦU WTI (USOIL)"
    )
    send_telegram(oil_msg)

if __name__ == "__main__":
    print("Bot Telegram Phân Tích Vàng & Dầu đã khởi động!")
    
    # Gửi tin nhắn thông báo bot đã chạy thành công khi khởi động
    startup_msg = "🚀 *Bot Phân Tích Kỹ Thuật (Vàng & Dầu)* đã khởi động và hoạt động 24/7 thành công!"
    send_telegram(startup_msg)
    
    # Chạy ngay lần đầu khi khởi động bot
    job()
    
    # Lên lịch chạy định kỳ mỗi 1 tiếng/lần (bạn có thể đổi thành schedule.every(30).minutes nếu muốn quét mỗi 30 phút)
    schedule.every(1).hours.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
