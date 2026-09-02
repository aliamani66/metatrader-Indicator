import os
import sys
import csv
from collections import defaultdict

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

MT5_FILES_DIR = r"c:\Users\USER\AppData\Roaming\MetaQuotes\Terminal\3F2C3A2F8B221C9D88E569F2FD1D3E97\MQL5\Files"
DEFAULT_CSV = os.path.join(MT5_FILES_DIR, "flagpro_trades_export.csv")
if not os.path.exists(DEFAULT_CSV):
    DEFAULT_CSV = os.path.join(MT5_FILES_DIR, "flag_trades_export.csv")

def analyze_and_rank_dashboard(csv_path=DEFAULT_CSV):
    if not os.path.exists(csv_path):
        print(f"فایل یافت نشد: {csv_path}")
        return

    rows = []
    with open(csv_path, mode='r', encoding='utf-8-sig', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    total_boxes = len(rows)
    if total_boxes == 0:
        print("هیچ داده‌ای در فایل موجود نیست.")
        return

    entered = [r for r in rows if r.get('Outcome') != 'Pending']
    closed = [r for r in entered if r.get('IsClosed') == 'True']
    in_trade = [r for r in entered if r.get('IsClosed') != 'True']

    print("=" * 105)
    print("🏆 داشبورد تحلیلی و رتبه‌بندی استراتژی‌های پرچم (FlagPro Intelligence Dashboard)")
    print("=" * 105)
    print(f"📌 کل ستاپ‌های استخراج‌شده: {total_boxes} | موقعیت‌های فعال‌شده: {len(entered)} ({len(entered)/total_boxes*100:.1f}%) | در حال معامله: {len(in_trade)}")
    print(f"🎯 تعداد کل معاملات خاتمه‌یافته (Closed Trades): {len(closed)}")
    print("-" * 105)

    if not closed:
        print("معامله بسته‌شده‌ای برای محاسبه آمار وجود ندارد.")
        return

    # آمار کلی
    tp1_all = sum(1 for r in closed if int(r.get('HitTargetRatio', 0)) >= 1)
    tp2_all = sum(1 for r in closed if int(r.get('HitTargetRatio', 0)) >= 2)
    tp3_all = sum(1 for r in closed if int(r.get('HitTargetRatio', 0)) >= 3)
    tp4_all = sum(1 for r in closed if int(r.get('HitTargetRatio', 0)) >= 4)
    sl_all  = sum(1 for r in closed if int(r.get('HitTargetRatio', 0)) == 0)

    print("📈 [میانگین کل حساب در تمام الگوها]:")
    print(f"   • وین‌ریت تارگت ۱ (۱:۱): {tp1_all:3d}/{len(closed)} ({tp1_all/len(closed)*100:5.1f}%)")
    print(f"   • وین‌ریت تارگت ۲ (۱:۲): {tp2_all:3d}/{len(closed)} ({tp2_all/len(closed)*100:5.1f}%)")
    print(f"   • وین‌ریت تارگت ۳ (۱:۳): {tp3_all:3d}/{len(closed)} ({tp3_all/len(closed)*100:5.1f}%)")
    print(f"   • وین‌ریت تارگت ۴ (۱:۴): {tp4_all:3d}/{len(closed)} ({tp4_all/len(closed)*100:5.1f}%)")
    print(f"   • برخورد به حد ضرر (SL): {sl_all:3d}/{len(closed)} ({sl_all/len(closed)*100:5.1f}%)")
    print("=" * 105)

    # تجمیع بر اساس نقش گره
    role_dict = defaultdict(lambda: {'total': 0, 'tp1': 0, 'tp2': 0, 'tp3': 0, 'tp4': 0, 'sl': 0})
    for r in closed:
        role = r.get('Role', 'Flag')
        role_dict[role]['total'] += 1
        hr = int(r.get('HitTargetRatio', 0))
        if hr >= 1: role_dict[role]['tp1'] += 1
        if hr >= 2: role_dict[role]['tp2'] += 1
        if hr >= 3: role_dict[role]['tp3'] += 1
        if hr >= 4: role_dict[role]['tp4'] += 1
        if hr == 0: role_dict[role]['sl'] += 1

    ranking = []
    for role, s in role_dict.items():
        n = s['total']
        w1 = s['tp1'] / n * 100
        w2 = s['tp2'] / n * 100
        w3 = s['tp3'] / n * 100
        w4 = s['tp4'] / n * 100
        sl_p = s['sl'] / n * 100
        # نمره ترکیبی کیفیت استراتژی: وزن‌دهی به وین‌ریت ریوارد ۱ و ۲ + جریمه نمونه‌های خیلی کوچک
        quality_score = (w1 * 0.4 + w2 * 0.4 + w3 * 0.2) * (1.0 if n >= 5 else (n / 5.0))
        ranking.append({
            'role': role,
            'total': n,
            'w1': w1, 'w2': w2, 'w3': w3, 'w4': w4,
            'sl_p': sl_p,
            'score': quality_score
        })

    # سورت ۱: بر اساس بیشترین نرخ برد (Win Rate TP1)
    sorted_by_winrate = sorted(ranking, key=lambda x: (x['w1'], x['w2'], x['total']), reverse=True)

    print("\n🥇 [جدول رتبه‌بندی بر اساس بیشترین نرخ برد (Sorted by Win Rate TP 1:1)]:")
    print(f"{'رتبه':<5} | {'نوع گره / استراتژی':<36} | {'تعداد':<6} | {'وین‌ریت ۱:۱':<11} | {'وین‌ریت ۱:۲':<11} | {'وین‌ریت ۱:۳':<11} | {'نرخ استاپ':<9}")
    print("-" * 105)

    medals = ["🥇", "🥈", "🥉"]
    for idx, item in enumerate(sorted_by_winrate, 1):
        m = medals[idx-1] if idx <= 3 else f"#{idx:<2}"
        print(f"{m:<5} | {item['role']:<36} | {item['total']:4d}   | {item['w1']:5.1f}%     | {item['w2']:5.1f}%     | {item['w3']:5.1f}%     | {item['sl_p']:5.1f}%")

    # سورت ۲: بر اساس بهترین استراتژی جامع (امتیاز کیفیت و ریوارد بالا با حجم نمونه قابل اتکا)
    sorted_by_best = sorted(ranking, key=lambda x: x['score'], reverse=True)

    print("\n\n⭐ [جدول رتبه‌بندی بر اساس بهترین استراتژی جامع (Best Overall Strategy Score)]:")
    print(f"{'رتبه':<5} | {'نوع گره / استراتژی':<36} | {'تعداد':<6} | {'امتیاز کیفیت':<12} | {'وین‌ریت ۱:۱':<11} | {'وین‌ریت ۱:۲':<11} | {'وضعیت':<10}")
    print("-" * 105)

    for idx, item in enumerate(sorted_by_best, 1):
        m = medals[idx-1] if idx <= 3 else f"#{idx:<2}"
        verdict = "عالی (A+)" if item['score'] >= 35 else ("خوب (B)" if item['score'] >= 20 else "متوسط (C)")
        if item['total'] < 5: verdict += " *"
        print(f"{m:<5} | {item['role']:<36} | {item['total']:4d}   | {item['score']:5.1f}        | {item['w1']:5.1f}%     | {item['w2']:5.1f}%     | {verdict:<10}")

    print("\n* نکته: علامت ستاره (*) نشان‌دهنده تعداد نمونه زیر ۵ معامله است که نیاز به دیتای بیشتر دارد.")
    print("=" * 105)

if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    analyze_and_rank_dashboard(csv_file)
