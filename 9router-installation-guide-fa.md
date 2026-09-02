# راهنمای نصب و راه‌اندازی 9router روی سرور خارجی

## 🎯 درباره 9router

9router یک gateway هوشمند برای AI است که به شما امکان می‌دهد به 40+ ارائه‌دهنده AI و 100+ مدل متصل شوید. این ابزار به طور خودکار بین مدل‌های رایگان و ارزان سوییچ می‌کند و 20-40% توکن شما را با فشرده‌سازی RTK ذخیره می‌کند.

**منابع:**
- [GitHub Repository](https://github.com/decolua/9router)
- [راهنمای نصب x-cmd](https://www.x-cmd.com/install/9router/)

---

## 📋 پیش‌نیازها

1. **سرور لینوکس** (پیشنهاد: Ubuntu 24)
   - حداقل: 2 کور CPU، 4GB RAM
   - سیستم عامل: Ubuntu 24 یا بالاتر
   - دسترسی SSH به سرور
   - **مهم**: سرور باید خارج از ایران باشد (سنگاپور، ژاپن، آمریکا و...)

2. **دسترسی‌های لازم**
   - دسترسی root یا sudo
   - پورت 20128 باید باز باشد

---

## 🚀 مرحله 1: نصب Docker روی Ubuntu 24

ابتدا به سرور خود متصل شوید:

```bash
ssh root@YOUR_SERVER_IP
```

سپس Docker را نصب کنید:

```bash
# به‌روزرسانی سیستم
sudo apt update

# نصب پیش‌نیازها
sudo apt install -y ca-certificates curl gnupg

# ایجاد دایرکتوری برای کلیدهای Docker
sudo install -m 0755 -d /etc/apt/keyrings

# افزودن کلید GPG رسمی Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# تنظیم دسترسی‌ها
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# افزودن repository Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# به‌روزرسانی لیست پکیج‌ها
sudo apt update

# نصب Docker و اجزای مرتبط
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# تست نصب Docker
sudo docker run hello-world
```

اگر پیغام "Hello from Docker!" را دیدید، نصب موفقیت‌آمیز بوده است! ✅

---

## 🔧 مرحله 2: اجرای 9router با Docker

### گزینه 1: با رمز عبور سفارشی (پیشنهادی)

```bash
sudo docker run -d \
  --name 9router \
  --restart=unless-stopped \
  -p 20128:20128 \
  -v "$HOME/.9router:/app/data" \
  -e DATA_DIR=/app/data \
  -e JWT_SECRET='YOUR-SUPER-LONG-RANDOM-STRING-HERE-CHANGE-ME-12345678' \
  -e INITIAL_PASSWORD='YOUR-STRONG-PASSWORD-HERE' \
  -e HOSTNAME=0.0.0.0 \
  -e REQUIRE_API_KEY=true \
  decolua/9router:latest
```

**مهم:** حتماً مقادیر زیر را تغییر دهید:
- `JWT_SECRET`: یک رشته طولانی و تصادفی (حداقل 32 کاراکتر)
- `INITIAL_PASSWORD`: رمز عبور قوی خودتان

### گزینه 2: با رمز عبور پیش‌فرض (برای تست)

```bash
sudo docker run -d \
  --name 9router \
  --restart=unless-stopped \
  -p 20128:20128 \
  -v "$HOME/.9router:/app/data" \
  -e DATA_DIR=/app/data \
  -e JWT_SECRET='9router-prod-jwt-2026-05-30-x8FvK2mQp7Nz4LdRc1TwUa6Hy9Sb3JeM' \
  -e INITIAL_PASSWORD='123456' \
  -e HOSTNAME=0.0.0.0 \
  -e REQUIRE_API_KEY=true \
  decolua/9router:latest
```

### بررسی وضعیت اجرا

```bash
# بررسی container در حال اجرا
sudo docker ps

# مشاهده لاگ‌ها
sudo docker logs 9router

# بررسی وضعیت
sudo docker logs -f 9router
```

---

## 🌐 مرحله 3: باز کردن پورت در فایروال

اگر از UFW استفاده می‌کنید:

```bash
sudo ufw allow 20128/tcp
sudo ufw reload
sudo ufw status
```

اگر از iptables استفاده می‌کنید:

```bash
sudo iptables -A INPUT -p tcp --dport 20128 -j ACCEPT
sudo iptables-save
```

**نکته**: اگر سرور شما در کلود است (AWS, Azure, GCP, Alibaba Cloud و...)، باید در پنل کنترل Security Group یا Firewall Rules هم پورت 20128 را باز کنید.

---

## 💻 مرحله 4: دسترسی از لپ‌تاپ

### روش 1: دسترسی مستقیم (اگر IP عمومی دارید)

در مرورگر خود روی لپ‌تاپ وارد کنید:

```
http://YOUR_SERVER_IP:20128
```

برای مثال:
```
http://123.45.67.89:20128
```

### روش 2: SSH Tunnel (امن‌تر)

اگر می‌خواهید به صورت امن دسترسی داشته باشید:

```bash
# روی لپ‌تاپ خود اجرا کنید (Windows PowerShell یا CMD)
ssh -L 20128:localhost:20128 root@YOUR_SERVER_IP
```

سپس در مرورگر وارد کنید:
```
http://localhost:20128
```

---

## 🔑 مرحله 5: ورود و تنظیمات اولیه

1. **ورود به داشبورد**
   - آدرس: `http://YOUR_SERVER_IP:20128`
   - رمز عبور: همان که در `INITIAL_PASSWORD` تنظیم کردید

2. **افزودن Provider (مثلاً Codex)**
   - کلیک روی `Providers`
   - پیدا کردن `Codex`
   - کلیک روی `Add Connection`
   - وارد کردن اطلاعات حساب GPT خود
   - تایید شماره موبایل
   - Authorization

3. **ساخت API Key**
   - رفتن به بخش `API Keys`
   - کلیک روی `Create New Key`
   - کپی کردن کلید (فقط یک بار نمایش داده می‌شود!)

---

## 📡 مرحله 6: استفاده در لپ‌تاپ خود

### اطلاعات اتصال

```
Base URL: http://YOUR_SERVER_IP:20128/v1
API Key: [کلیدی که ساختید]
```

### مثال‌های استفاده

#### در Claude Code, Cursor, VSCode و...

```json
{
  "apiEndpoint": "http://YOUR_SERVER_IP:20128/v1",
  "apiKey": "YOUR_API_KEY_HERE"
}
```

#### مدل‌های موجود (مثال)

برای Codex:
- `cx/gpt-5.5`
- `cx/gpt-4`

برای سایر providerها، می‌توانید در داشبورد بخش Models لیست کامل را ببینید.

#### تست با curl (در PowerShell یا CMD)

```bash
curl -X POST http://YOUR_SERVER_IP:20128/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer YOUR_API_KEY" ^
  -d "{\"model\": \"cx/gpt-5.5\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}]}"
```

---

## 🛠️ دستورات مفید Docker

```bash
# توقف 9router
sudo docker stop 9router

# شروع مجدد
sudo docker start 9router

# راه‌اندازی مجدد
sudo docker restart 9router

# حذف container (داده‌ها حفظ می‌شوند)
sudo docker rm -f 9router

# مشاهده لاگ‌های زنده
sudo docker logs -f 9router

# مشاهده 100 خط آخر لاگ
sudo docker logs --tail 100 9router

# به‌روزرسانی به آخرین نسخه
sudo docker pull decolua/9router:latest
sudo docker stop 9router
sudo docker rm 9router
# سپس دستور docker run را دوباره اجرا کنید
```

---

## 🔒 نکات امنیتی

1. **حتماً رمز عبور قوی استفاده کنید**
2. **JWT_SECRET را تصادفی و طولانی انتخاب کنید**
3. **در صورت امکان از HTTPS استفاده کنید** (با nginx + Let's Encrypt)
4. **فقط IP های مورد نیاز را به پورت 20128 دسترسی بدهید**
5. **به صورت منظم backup از دایرکتوری `~/.9router` بگیرید**

---

## 📊 نظارت و عیب‌یابی

### بررسی وضعیت سلامت

```bash
# بررسی اینکه سرویس در حال اجرا است
curl http://localhost:20128/

# بررسی استفاده از منابع
sudo docker stats 9router
```

### مشکلات رایج

1. **نمی‌توانم به داشبورد وصل شوم**
   - بررسی کنید container در حال اجرا است: `sudo docker ps`
   - بررسی فایروال: `sudo ufw status`
   - بررسی لاگ‌ها: `sudo docker logs 9router`

2. **پیغام خطای Authentication**
   - مطمئن شوید `INITIAL_PASSWORD` را درست وارد کرده‌اید
   - لاگ‌ها را بررسی کنید

3. **مدل‌ها کار نمی‌کنند**
   - مطمئن شوید provider را درست تنظیم کرده‌اید
   - اعتبار سنجی حساب را تکمیل کرده‌اید

---

## 🌟 ویژگی‌های پیشرفته

### Fallback خودکار

9router به صورت خودکار بین مدل‌ها سوییچ می‌کند:
1. Subscription (مدل‌های پولی شما)
2. Cheap (مدل‌های ارزان)
3. Free (مدل‌های رایگان)

### Token Compression (RTK)

فشرده‌سازی خودکار context تا 40% کاهش هزینه!

### Usage Tracking

رهگیری دقیق مصرف در داشبورد

---

## 📚 منابع اضافی

- [مستندات رسمی 9router](https://github.com/decolua/9router)
- [آموزش نصب با Railway](https://railway.com/deploy/9router-v3)
- [توضیحات معماری](https://github.com/decolua/9router/blob/master/docs/ARCHITECTURE.md)

---

## 💡 نکات نهایی

1. **Backup منظم**: فایل‌های config در `~/.9router` ذخیره می‌شوند
2. **به‌روزرسانی**: هر چند وقت یکبار image جدید را pull کنید
3. **Monitoring**: لاگ‌ها را به صورت دوره‌ای چک کنید
4. **Cost Optimization**: از fallback استفاده کنید تا هزینه کمتری داشته باشید

---

**موفق باشید! 🎉**

در صورت بروز مشکل، لاگ‌ها را با `sudo docker logs 9router` بررسی کنید.
