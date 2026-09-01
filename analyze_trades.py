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
DEFAULT_CSV = os.path.join(MT5_FILES_DIR, "flag_trades_export.csv")

def analyze_trades(csv_path=DEFAULT_CSV):
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        print("Please refresh the MT5 chart once so the indicator writes the file.")
        return

    rows = []
    with open(csv_path, mode='r', encoding='utf-8-sig', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    total_boxes = len(rows)
    if total_boxes == 0:
        print("No trade data in CSV file.")
        return

    print("=" * 85)
    print("گزارش جامع تحلیلی و آماری معاملات (بر اساس دیتای ۲ روز گذشته متاتریدر ۵)")
    print("=" * 85)
    print(f"کل باکس‌های ثبت‌شده در ۲ روز گذشته: {total_boxes}")

    tested = [r for r in rows if r.get('Result') != 'PENDING']
    pending = [r for r in rows if r.get('Result') == 'PENDING']

    total_tested = len(tested)
    print(f"موقعیت‌های فعال و تست‌شده در گذشته (Tested Trades): {total_tested}")
    print(f"موقعیت‌های معلق لایو (Pending Setups): {len(pending)}")
    print("-" * 85)

    if total_tested == 0:
        print("هنوز معامله تست‌شده‌ای در این بازه لمس نشده است.")
        return

    # آمار کلی
    win_tp1 = sum(1 for r in tested if int(r.get('HitTP', 0)) >= 1)
    win_tp2 = sum(1 for r in tested if int(r.get('HitTP', 0)) >= 2)
    win_tp3 = sum(1 for r in tested if int(r.get('HitTP', 0)) >= 3)
    win_tp4 = sum(1 for r in tested if int(r.get('HitTP', 0)) >= 4)
    losses  = sum(1 for r in tested if r.get('Result') == 'LOSS')
    running = sum(1 for r in tested if r.get('Result') == 'OPEN')

    print("[نرخ موفقیت کلی بر اساس نسبت‌های ریسک به ریوارد]:")
    print(f"   تارگت TP 1:1 : {win_tp1:4d} برد | وین‌ریت: {win_tp1/total_tested*100:6.2f}%")
    print(f"   تارگت TP 1:2 : {win_tp2:4d} برد | وین‌ریت: {win_tp2/total_tested*100:6.2f}%")
    print(f"   تارگت TP 1:3 : {win_tp3:4d} برد | وین‌ریت: {win_tp3/total_tested*100:6.2f}%")
    print(f"   تارگت TP 1:4 : {win_tp4:4d} برد | وین‌ریت: {win_tp4/total_tested*100:6.2f}%")
    print(f"   استاپ کامل (Loss) : {losses:4d} باخت | نرخ باخت: {losses/total_tested*100:6.2f}%")
    print(f"   در حال اجرا (Open): {running:4d} مورد")
    print("-" * 85)

    # تفکیک بر اساس نقش باکس
    print("[تفکیک عملکرد بر اساس نوع و نقش باکس]:")
    by_role = defaultdict(list)
    for r in tested:
        by_role[r.get('Role', 'Flag')].append(r)

    for role, r_list in sorted(by_role.items()):
        n = len(r_list)
        w1 = sum(1 for r in r_list if int(r.get('HitTP', 0)) >= 1)
        w2 = sum(1 for r in r_list if int(r.get('HitTP', 0)) >= 2)
        w3 = sum(1 for r in r_list if int(r.get('HitTP', 0)) >= 3)
        w4 = sum(1 for r in r_list if int(r.get('HitTP', 0)) >= 4)
        loss = sum(1 for r in r_list if r.get('Result') == 'LOSS')

        print(f"\nنقش: {role:14s} (تعداد: {n:3d})")
        print(f"   • TP 1:1: {w1:3d} ({w1/n*100:5.1f}%) | TP 1:2: {w2:3d} ({w2/n*100:5.1f}%) | TP 1:3: {w3:3d} ({w3/n*100:5.1f}%) | TP 1:4: {w4:3d} ({w4/n*100:5.1f}%) | Loss: {loss:3d} ({loss/n*100:5.1f}%)")

    print("-" * 85)

    # تفکیک بر اساس تایم‌فریم
    print("[تفکیک عملکرد بر اساس تایم‌فریم]:")
    by_tf = defaultdict(list)
    for r in tested:
        by_tf[r.get('Timeframe', '')].append(r)

    for tf, r_list in sorted(by_tf.items()):
        n = len(r_list)
        w1 = sum(1 for r in r_list if int(r.get('HitTP', 0)) >= 1)
        w2 = sum(1 for r in r_list if int(r.get('HitTP', 0)) >= 2)
        w3 = sum(1 for r in r_list if int(r.get('HitTP', 0)) >= 3)
        w4 = sum(1 for r in r_list if int(r.get('HitTP', 0)) >= 4)
        loss = sum(1 for r in r_list if r.get('Result') == 'LOSS')

        print(f"\nتایم‌فریم: {tf:6s} (تعداد: {n:3d})")
        print(f"   • TP 1:1: {w1:3d} ({w1/n*100:5.1f}%) | TP 1:2: {w2:3d} ({w2/n*100:5.1f}%) | TP 1:3: {w3:3d} ({w3/n*100:5.1f}%) | TP 1:4: {w4:3d} ({w4/n*100:5.1f}%) | Loss: {loss:3d} ({loss/n*100:5.1f}%)")

    print("=" * 85)

if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    analyze_trades(csv_file)
