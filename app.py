import os
from flask import Flask, render_template_string, request, redirect, session
import sqlite3
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

DB = "orders.db"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

menu = {
    "پیتزا": {"price": 250000, "image": "/static/images/pizza.jpg"},
    "همبرگر": {"price": 180000, "image": "/static/images/burger.jpg"},
    "نوشابه": {"price": 30000, "image": "/static/images/soda.jpg"},
    "ساندویچ": {"price": 120000, "image": "/static/images/sandwich.jpg"},
    "سیب زمینی": {"price": 80000, "image": "/static/images/fries.webp"}
}

def connect():
    return sqlite3.connect(DB)

def init_db():
    con = connect()
    con.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT,
        phone TEXT,
        address TEXT,
        items TEXT,
        total INTEGER,
        status TEXT DEFAULT 'در انتظار'
    )
    """)
    con.commit()
    con.close()

page = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>رستوران افشین</title>
<style>
* {box-sizing:border-box}
body {margin:0;background:#101010;font-family:tahoma,sans-serif;color:#f5f5f5}
header {background:#191919;color:white;text-align:center;padding:25px}
header h1 {color:#e8bd62;margin:5px}
.container {max-width:850px;margin:auto;padding:15px}
.grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:15px}
.card {background:#1c1c1c;border:1px solid #80652e;border-radius:15px;overflow:hidden;box-shadow:0 3px 12px #ddd}
.card img {width:100%;height:145px;object-fit:cover}
.details {padding:14px}
.price {color:#e8bd62;font-weight:bold}
button {background:#b8862b;color:white;border:0;border-radius:8px;padding:11px 16px;cursor:pointer}
input {width:100%;padding:12px;margin:7px 0;border:1px solid #ccc;border-radius:8px}
.panel {background:#1c1c1c;color:#f5f5f5;border:1px solid #80652e;padding:18px;margin:18px 0;border-radius:14px}
a {color:#e8bd62}
</style>
</head>
<body>
<header>
<h1>🍕 رستوران نمونه افشین</h1>
<p>طعم خوب، سفارش آسان</p>
</header>
<section style="max-width:950px;margin:22px auto 0;padding:30px 18px;text-align:center;background:linear-gradient(135deg,#2a2112,#090909);border:1px solid #b8862b;border-radius:18px"><h2 style="color:#e8bd62;font-size:25px">🍽️ طعم خاص، تجربه‌ای به‌یادماندنی</h2><p style="color:#eee">غذای تازه و خوشمزه، فقط با چند کلیک سفارش بده</p><a href="#menu" style="display:inline-block;background:#b8862b;color:#111;padding:11px 22px;border-radius:9px;text-decoration:none">مشاهده منو</a></section>
<div class="container">
<h2>منوی غذا</h2>
<div class="grid">
{% for name,item in menu.items() %}
<div class="card">
<img src="{{item.image}}" alt="{{name}}">
<div class="details">
<h3>{{name}}</h3>
<p class="price">{{"{:,}".format(item.price)}} تومان</p>
<form method="post" action="/add/{{name}}">
<button>افزودن به سبد خرید</button>
</form>
</div>
</div>
{% endfor %}
</div>

<div class="panel">
<h2>🛒 سبد خرید</h2>
{% for name,count in cart.items() %}
<p>{{name}} × {{count}}</p>
{% endfor %}
<h3>مبلغ کل: {{"{:,}".format(total)}} تومان</h3>
{% if cart %}
<form method="post" action="/checkout">
<input name="customer" placeholder="نام و نام خانوادگی" required>
<input name="phone" placeholder="شماره موبایل" required>
<input name="address" placeholder="آدرس تحویل" required>
<button>ثبت نهایی سفارش</button>
</form>
{% else %}
<p>سبد خرید خالی است.</p>
{% endif %}
</div>
<p style="text-align:center"><a href="/admin">ورود مدیریت رستوران</a></p>
</div>
</body>
</html>
"""

@app.route("/")
def home():
    cart = session.get("cart", {})
    total = sum(menu[n]["price"] * c for n, c in cart.items())
    return render_template_string(page, menu=menu, cart=cart, total=total)

@app.route("/add/<name>", methods=["POST"])
def add(name):
    if name in menu:
        cart = session.get("cart", {})
        cart[name] = cart.get(name, 0) + 1
        session["cart"] = cart
    return redirect("/")

@app.route("/checkout", methods=["POST"])
def checkout():
    cart = session.get("cart", {})
    if not cart:
        return redirect("/")
    customer = request.form.get("customer", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    if not customer or not phone or not address:
        return "لطفاً همه اطلاعات را وارد کنید."
    total = sum(menu[n]["price"] * c for n, c in cart.items())
    con = connect()
    con.execute(
        "INSERT INTO orders(customer,phone,address,items,total) VALUES(?,?,?,?,?)",
        (customer, phone, address, json.dumps(cart, ensure_ascii=False), total)
    )
    con.commit()
    con.close()
    session["cart"] = {}
    return "<h2 dir='rtl'>سفارش با موفقیت ثبت و ذخیره شد ✅</h2><a href='/'>بازگشت به منو</a>"

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
        else:
            return "رمز اشتباه است. <a href='/admin'>تلاش دوباره</a>"
    if not session.get("admin"):
        return """
        <html lang="fa" dir="rtl"><meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <body style="font-family:tahoma;padding:25px">
        <h2>ورود مدیر رستوران</h2>
        <form method="post">
        <input type="password" name="password" placeholder="رمز مدیریت" required>
        <button>ورود</button>
        </form></body></html>
        """
    con = connect()
    rows = con.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    con.close()
    return render_template_string("""
    <html lang="fa" dir="rtl"><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <body style="font-family:tahoma;background:#101010;color:#f5f5f5;padding:15px">
    <h1>پنل مدیریت رستوران</h1>
    <a href="/" style="display:block;background:#d6ad55;color:#111;text-align:center;padding:15px;margin:15px 0;border-radius:12px;text-decoration:none;font-weight:bold;font-size:18px">🍔 مشاهده منوی مشتری</a>
    <h3>تعداد سفارش‌ها: {{rows|length}}</h3>
<h3 style="color:#d6ad55">سفارش‌های در انتظار: {{rows|selectattr(6, "equalto", "در انتظار")|list|length}}</h3>
<h3 style="color:#55cc88">مجموع فروش: {{ "{:,}".format(rows|rejectattr(6, "equalto", "لغو شده")|sum(attribute=5)) }} تومان</h3>
    {% for o in rows %}
    <div style="background:#1c1c1c;color:#f5f5f5;border:1px solid #80652e;padding:15px;margin:12px 0;border-radius:12px">
    <h3>سفارش شماره {{o[0]}}</h3>
    <p>مشتری: {{o[1]}}</p>
    <p>شماره: {{o[2]}}</p>
    <p>آدرس: {{o[3]}}</p>
    <p>غذاها: {{o[4]}}</p>
    <h3>مبلغ: {{ "{:,}".format(o[5]) }} تومان</h3>
    <p>وضعیت:
    <span style="display:inline-block;padding:7px 12px;border-radius:8px;font-weight:bold;background:{% if o[6] == 'در انتظار' %}#665018{% elif o[6] == 'در حال آماده‌سازی' %}#174b70{% elif o[6] == 'ارسال شده' %}#563477{% elif o[6] == 'تحویل داده شده' %}#176b3a{% else %}#8b2525{% endif %};color:white">{{o[6]}}</span>
    </p>
    <form method="post" action="/status/{{o[0]}}">
    <select name="status">
    {% for s in ["در انتظار","در حال آماده‌سازی","ارسال شده","تحویل داده شده","لغو شده"] %}
    <option value="{{s}}" {% if s == o[6] %}selected{% endif %}>{{s}}</option>
    {% endfor %}
    </select>
    <button>تغییر وضعیت</button>
    </form>
    </div>
    {% endfor %}
    <a href="/logout">خروج از مدیریت</a>
    </body></html>
    """, rows=rows)

@app.route("/status/<int:order_id>", methods=["POST"])
def status(order_id):
    if not session.get("admin"):
        return redirect("/admin")
    allowed = ["در انتظار","در حال آماده‌سازی","ارسال شده","تحویل داده شده","لغو شده"]
    value = request.form.get("status")
    if value in allowed:
        con = connect()
        con.execute("UPDATE orders SET status=? WHERE id=?", (value, order_id))
        con.commit()
        con.close()
    return redirect("/admin")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin")

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
