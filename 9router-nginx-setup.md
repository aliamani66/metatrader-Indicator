# راه‌اندازی Nginx برای 9router

## نصب Nginx روی Ubuntu

```bash
# نصب nginx
sudo apt update
sudo apt install -y nginx

# بررسی نصب
nginx -v

# شروع سرویس
sudo systemctl start nginx
sudo systemctl enable nginx

# بررسی وضعیت
sudo systemctl status nginx
```

## تنظیم Nginx برای 9router

### ایجاد فایل کانفیگ

```bash
sudo nano /etc/nginx/sites-available/9router
```

### محتوای فایل (HTTP ساده):

```nginx
server {
    listen 80;
    listen [::]:80;
    
    # اگر دامنه دارید، uncomment کنید:
    # server_name your-domain.com;
    
    # اگر دامنه ندارید، این خط رو نگه دارید:
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:20128;
        proxy_http_version 1.1;
        
        # Headers مهم
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (اگر لازمه)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering off;
    }
}
```

### فعال‌سازی کانفیگ

```bash
# ایجاد symlink
sudo ln -s /etc/nginx/sites-available/9router /etc/nginx/sites-enabled/

# حذف کانفیگ default (اختیاری)
sudo rm /etc/nginx/sites-enabled/default

# تست کانفیگ
sudo nginx -t

# اگر "syntax is ok" گفت، reload کنید
sudo systemctl reload nginx
```

## تست

```bash
# از روی سرور
curl http://localhost/

# از لپ‌تاپ (مرورگر)
http://YOUR_SERVER_IP/
```

---

## نسخه با پورت سفارشی (مثلاً 8080)

اگر نمیخواید از پورت 80 استفاده کنید:

```nginx
server {
    listen 8080;
    listen [::]:8080;
    
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:20128;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

بعد باز کردن پورت در فایروال:
```bash
sudo ufw allow 8080/tcp
```

دسترسی:
```
http://YOUR_SERVER_IP:8080/
```

---

## نسخه با HTTPS (با Let's Encrypt)

اگر دامنه دارید و میخواید HTTPS داشته باشید:

### نصب Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### دریافت گواهی SSL

```bash
# جایگزین کردن your-domain.com با دامنه واقعی
sudo certbot --nginx -d your-domain.com
```

Certbot خودش کانفیگ nginx رو به HTTPS تبدیل میکنه!

### تمدید خودکار

```bash
# تست تمدید
sudo certbot renew --dry-run

# Certbot خودش cron job میسازه برای تمدید خودکار
```

### کانفیگ نهایی با HTTPS (Certbot خودش این رو میسازه):

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:20128;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## محدود کردن دسترسی به IP خاص (امنیتی)

اگر فقط میخواید از IP لپ‌تاپ خودتون دسترسی داشته باشید:

```nginx
server {
    listen 80;
    server_name _;
    
    # فقط این IP ها اجازه دارند
    allow YOUR_LAPTOP_IP;
    deny all;
    
    location / {
        proxy_pass http://127.0.0.1:20128;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## دستورات مفید Nginx

```bash
# شروع
sudo systemctl start nginx

# توقف
sudo systemctl stop nginx

# ریستارت (قطع کامل)
sudo systemctl restart nginx

# Reload (بدون قطع - بهتره)
sudo systemctl reload nginx

# وضعیت
sudo systemctl status nginx

# تست کانفیگ
sudo nginx -t

# مشاهده error log
sudo tail -f /var/log/nginx/error.log

# مشاهده access log
sudo tail -f /var/log/nginx/access.log
```

---

## عیب‌یابی

### مشکل: 502 Bad Gateway

```bash
# بررسی که 9router در حال اجرا است
ps aux | grep 9router

# بررسی که روی پورت 20128 گوش میده
netstat -tulpn | grep 20128

# بررسی لاگ nginx
sudo tail -f /var/log/nginx/error.log
```

### مشکل: Permission Denied

```bash
# SELinux را غیرفعال کنید (اگر CentOS/RHEL استفاده میکنید)
sudo setsebool -P httpd_can_network_connect 1
```

### مشکل: نمیتونم به پورت 80 دسترسی داشته باشم

```bash
# باز کردن در فایروال
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```

---

## Basic Authentication (امنیت اضافی)

اگر میخواید یوزر و پسورد هم داشته باشید:

```bash
# نصب ابزار
sudo apt install apache2-utils

# ساخت فایل password
sudo htpasswd -c /etc/nginx/.htpasswd admin

# اضافه کردن یوزر دیگه
sudo htpasswd /etc/nginx/.htpasswd user2
```

در کانفیگ nginx اضافه کنید:

```nginx
server {
    listen 80;
    server_name _;
    
    location / {
        auth_basic "Restricted Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        proxy_pass http://127.0.0.1:20128;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## خلاصه مراحل نصب سریع

```bash
# 1. نصب nginx
sudo apt update && sudo apt install -y nginx

# 2. ساخت کانفیگ
sudo nano /etc/nginx/sites-available/9router

# 3. کپی کردن یکی از کانفیگ های بالا

# 4. فعال‌سازی
sudo ln -s /etc/nginx/sites-available/9router /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# 5. تست
sudo nginx -t

# 6. reload
sudo systemctl reload nginx

# 7. باز کردن فایروال
sudo ufw allow 80/tcp

# 8. تست
curl http://YOUR_SERVER_IP/
```

---

موفق باشید! 🎉
