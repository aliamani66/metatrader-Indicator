import os
import sys
import csv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

MT5_FILES_DIR = r"c:\Users\USER\AppData\Roaming\MetaQuotes\Terminal\3F2C3A2F8B221C9D88E569F2FD1D3E97\MQL5\Files"
CSV_PATH = os.path.join(MT5_FILES_DIR, "flag_trades_export.csv")
HTML_OUT = os.path.join(MT5_FILES_DIR, "s_rs_visual_report.html")

def generate_report():
    if not os.path.exists(CSV_PATH):
        print("CSV file not found.")
        return

    s_rs_trades = []
    with open(CSV_PATH, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'S-RS' in row.get('Role', ''):
                s_rs_trades.append(row)

    html_cards = ""
    for idx, t in enumerate(s_rs_trades):
        is_buy = t['Direction'] == 'BUY'
        dir_badge = f'<span style="background:{"#00e676" if is_buy else "#ff1744"};color:#000;padding:4px 10px;border-radius:6px;font-weight:bold;">{"BUY" if is_buy else "SELL"}</span>'
        
        res = t['Result']
        res_color = "#00e676" if "WIN" in res else ("#ff5252" if "LOSS" in res else "#ffd600")
        res_badge = f'<span style="background:{res_color};color:#000;padding:4px 12px;border-radius:6px;font-weight:bold;">{res}</span>'

        entry_p = float(t['EntryPrice'])
        sl_p = float(t['SLPrice'])
        tp1_p = float(t['TP1'])
        tp2_p = float(t['TP2'])
        tp3_p = float(t['TP3'])
        tp4_p = float(t['TP4'])
        top_p = float(t['TopPrice'])
        bot_p = float(t['BottomPrice'])
        risk_pips = float(t['RiskPips'])
        hit_tp = int(t['HitTP'])

        # Create Visual SVG Price Level Diagram
        min_p = min(sl_p, tp4_p, bot_p) - (risk_pips * 0.0001 * 0.3)
        max_p = max(sl_p, tp4_p, top_p) + (risk_pips * 0.0001 * 0.3)
        p_range = max_p - min_p if max_p > min_p else 1.0

        def to_y(price):
            return int(220 - ((price - min_p) / p_range * 180))

        y_top = to_y(top_p)
        y_bot = to_y(bot_p)
        y_entry = to_y(entry_p)
        y_sl = to_y(sl_p)
        y_tp1 = to_y(tp1_p)
        y_tp2 = to_y(tp2_p)
        y_tp3 = to_y(tp3_p)
        y_tp4 = to_y(tp4_p)

        svg = f'''
        <svg width="100%" height="240" viewBox="0 0 500 240" style="background:#11141a;border-radius:10px;margin-top:12px;">
            <!-- Box Zone -->
            <rect x="50" y="{min(y_top, y_bot)}" width="140" height="{max(abs(y_top - y_bot), 6)}" fill="rgba(255,140,0,0.25)" stroke="#ff8c00" stroke-width="2" stroke-dasharray="4,2" rx="4"/>
            <text x="55" y="{min(y_top, y_bot) - 6}" fill="#ff8c00" font-size="11" font-weight="bold">S-RS Zone [{top_p:.5f} - {bot_p:.5f}]</text>

            <!-- Stop Loss Line -->
            <line x1="190" y1="{y_sl}" x2="470" y2="{y_sl}" stroke="#ff5252" stroke-width="2" stroke-dasharray="5,3"/>
            <text x="400" y="{y_sl - 4}" fill="#ff5252" font-size="11" font-weight="bold">SL: {sl_p:.5f}</text>

            <!-- Entry Line -->
            <line x1="190" y1="{y_entry}" x2="470" y2="{y_entry}" stroke="#ffffff" stroke-width="2.5"/>
            <text x="200" y="{y_entry - 5}" fill="#ffffff" font-size="12" font-weight="bold">ENTRY: {entry_p:.5f}</text>

            <!-- TP Lines -->
            <line x1="190" y1="{y_tp1}" x2="470" y2="{y_tp1}" stroke="{"#00e676" if hit_tp>=1 else "#555"}" stroke-width="{2 if hit_tp>=1 else 1}" stroke-dasharray="3,3"/>
            <text x="400" y="{y_tp1 - 4}" fill="{"#00e676" if hit_tp>=1 else "#888"}" font-size="11">TP 1:1: {tp1_p:.5f}</text>

            <line x1="190" y1="{y_tp2}" x2="470" y2="{y_tp2}" stroke="{"#00e676" if hit_tp>=2 else "#555"}" stroke-width="{2 if hit_tp>=2 else 1}" stroke-dasharray="3,3"/>
            <text x="400" y="{y_tp2 - 4}" fill="{"#00e676" if hit_tp>=2 else "#888"}" font-size="11">TP 1:2: {tp2_p:.5f}</text>

            <line x1="190" y1="{y_tp3}" x2="470" y2="{y_tp3}" stroke="{"#00e676" if hit_tp>=3 else "#555"}" stroke-width="{2 if hit_tp>=3 else 1}" stroke-dasharray="3,3"/>
            <text x="400" y="{y_tp3 - 4}" fill="{"#00e676" if hit_tp>=3 else "#888"}" font-size="11">TP 1:3: {tp3_p:.5f}</text>

            <line x1="190" y1="{y_tp4}" x2="470" y2="{y_tp4}" stroke="{"#00e676" if hit_tp>=4 else "#555"}" stroke-width="{2 if hit_tp>=4 else 1}" stroke-dasharray="3,3"/>
            <text x="400" y="{y_tp4 - 4}" fill="{"#00e676" if hit_tp>=4 else "#888"}" font-size="11">TP 1:4: {tp4_p:.5f}</text>
        </svg>
        '''

        card = f'''
        <div style="background:#1a1f2c;border:1px solid #2d3748;border-radius:12px;padding:18px;margin-bottom:20px;box-shadow:0 4px 12px rgba(0,0,0,0.4);">
            <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #2d3748;padding-bottom:12px;">
                <div>
                    <span style="font-size:16px;font-weight:bold;color:#ff8c00;">معامله شماره {idx+1}: {t["Role"]} [{t["Timeframe"]}]</span>
                    <span style="color:#a0aec0;font-size:12px;margin-right:12px;">زمان شروع: {t["StartTime"]}</span>
                </div>
                <div>
                    {dir_badge}
                    {res_badge}
                </div>
            </div>
            
            <div style="display:grid;grid-template-columns:repeat(4, 1fr);gap:12px;margin-top:14px;font-size:13px;">
                <div style="background:#11141a;padding:10px;border-radius:8px;">
                    <span style="color:#a0aec0;">نقطه ورود (Entry):</span><br>
                    <b style="color:#fff;font-size:15px;">{entry_p:.5f}</b><br>
                    <span style="color:#718096;font-size:11px;">زمان: {t["EntryTime"]}</span>
                </div>
                <div style="background:#11141a;padding:10px;border-radius:8px;">
                    <span style="color:#a0aec0;">حد ضرر (SL):</span><br>
                    <b style="color:#ff5252;font-size:15px;">{sl_p:.5f}</b><br>
                    <span style="color:#718096;font-size:11px;">ریسک: {risk_pips} پیپ</span>
                </div>
                <div style="background:#11141a;padding:10px;border-radius:8px;">
                    <span style="color:#a0aec0;">تارگت‌ها:</span><br>
                    <span style="color:#00e676;">TP 1:1: {tp1_p:.5f}</span> | <span style="color:#00e676;">TP 1:2: {tp2_p:.5f}</span><br>
                    <span style="color:#00e676;">TP 1:3: {tp3_p:.5f}</span> | <span style="color:#00e676;">TP 1:4: {tp4_p:.5f}</span>
                </div>
                <div style="background:#11141a;padding:10px;border-radius:8px;">
                    <span style="color:#a0aec0;">وضعیت خروج:</span><br>
                    <b style="color:{res_color};font-size:15px;">{res}</b><br>
                    <span style="color:#718096;font-size:11px;">زمان خروج: {t["ExitTime"]}</span>
                </div>
            </div>

            {svg}
        </div>
        '''
        html_cards += card

    full_html = f'''
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <meta charset="utf-8">
        <title>گزارش تصویری معاملات S-RS</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #0b0e14; color: #e2e8f0; margin: 0; padding: 25px; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #ff8c00, #ff4500); padding: 20px; border-radius: 12px; color: #fff; margin-bottom: 25px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin:0;font-size:24px;">📊 گزارش تصویری و بصری معاملات S-RS (سواپ فلگ‌های واکنش)</h1>
                <p style="margin:6px 0 0 0;font-size:14px;opacity:0.9;">استخراج‌شده از دیتای واقعی ۲ روز گذشته متاتریدر ۵</p>
            </div>
            {html_cards}
        </div>
    </body>
    </html>
    '''

    with open(HTML_OUT, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f"Report generated at: {HTML_OUT}")

if __name__ == "__main__":
    generate_report()
