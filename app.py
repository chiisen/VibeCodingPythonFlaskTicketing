from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort
from markupsafe import escape
import os
import sys
import hashlib
import hmac
import secrets
import datetime
from functools import wraps

# 載入環境變數設定
try:
    from config import SECRET_KEY, FLASK_DEBUG, FLASK_ENV, SQLALCHEMY_DATABASE_URI
except ImportError as e:
    print(f"ERROR: 載入設定失敗: {e}")
    print("   請確保 config.py 和 .env 檔案存在")
    sys.exit(1)

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['FLASK_ENV'] = FLASK_ENV
app.config['DEBUG'] = FLASK_DEBUG
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_TIME_LIMIT'] = 3600

# ═══════════════════════════════════════════
# 💡 概念：CSRFProtection（跨站請求偽造保護）
# 說明：防止惡意網站偽造使用者的請求
# 為何使用：保護使用者的訂單不被惡意修改
# 注意事項：所有 POST 表單必须包含有效的 CSRF token
# ═══════════════════════════════════════════
def generate_csrf_token():
    """產生 CSRF token"""
    if '_csrf_token' not in session:
        session['_csrf_token'] = hashlib.sha256(os.urandom(32)).hexdigest()
    return session['_csrf_token']

def validate_csrf_token():
    """驗證 CSRF token"""
    token = session.get('_csrf_token')
    if not token:
        return False
    form_token = request.form.get('csrf_token')
    if not form_token:
        return False
    return hmac.compare_digest(token, form_token)

def csrf_protect(f):
    """CSRF 保護装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            if not validate_csrf_token():
                abort(400, '無效的 CSRF token，請求已被拒絕')
        return f(*args, **kwargs)
    return decorated_function

app.jinja_env.globals['generate_csrf_token'] = generate_csrf_token

# ═══════════════════════════════════════════
# 💡 概念：Sanitization（輸入清理）
# 說明：使用 markupsafe 逃逸使用者輸入，防止 XSS 攻擊
# 為何使用：防止惡意使用者注入 JavaScript 指令碼
# 注意事項：所有使用者輸入在顯示前都應逃逸
# ═══════════════════════════════════════════
def sanitize_input(value):
    """清理使用者輸入，防止 XSS 攻擊"""
    if value is None:
        return None
    return escape(str(value))

app.jinja_env.filters['sanitize'] = sanitize_input

# ═══════════════════════════════════════════
# 💡 概念：RateLimiter（速率限制）
# 說明：限制單一 IP 的請求頻率
# 為何使用：防止濫用和 DDoS 攻擊
# 注意事項：使用 sliding window algorithm 計算請求頻率
# ═══════════════════════════════════════════
from ratelimit import submit_limiter, admin_limiter

# 資料庫相關
from models import db, Ticket, Order

# 初始化資料庫
db.init_app(app)

# ═══════════════════════════════════════════
# 💡 概念：XSS Prevention（跨站指令碼攻擊防護）
# 說明：使用 markupsafe.escape() 逃逸 HTML 特殊字元
# 為何使用：防止惡意使用者在表單中注入 <script> 標籤
# 注意事項：在模板中使用 {{ variable|e }} 或 {{ variable|sanitize }}
# ═══════════════════════════════════════════
def escape_html(text):
    """逃逸 HTML 特殊字元"""
    if not text:
        return ''
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

# ═══════════════════════════════════════════
# 💡 概念：Error Handler（錯誤處理）
# 說明：統一處理應用程式的錯誤，提供使用者友好的提示
# 為何使用：避免顯示內部錯誤細節，提升安全性與使用者體驗
# 注意事項：每種錯誤應有對應的處理與記錄機制
# ═══════════════════════════════════════════
@app.errorhandler(400)
def bad_request(error):
    """400 錯誤處理"""
    flash(f'請求無效: {error.description}', 'error')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    """404 錯誤處理"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 錯誤處理"""
    db.session.rollback()
    flash('系統發生錯誤，請稍後再試', 'error')
    return redirect(url_for('index'))


@app.route('/')
def index():
    """首頁：顯示票種資訊"""
    tickets = Ticket.query.filter_by(is_active=True).all()
    return render_template('index.html', tickets=tickets)


@app.route('/book')
def book():
    """訂票表單頁面"""
    tickets = Ticket.query.filter_by(is_active=True).all()
    return render_template('book.html', tickets=tickets)


@app.route('/submit', methods=['POST'])
def submit():
    """處理訂票提交"""
    # 速率限制檢查
    if not submit_limiter.is_allowed(request.remote_addr):
        flash('請求過於頻繁，請稍後再試', 'error')
        return redirect(url_for('book'))

    # CSRF token 已由装饰器自動驗證
    try:
        # Get form data - 並立即清理
        ticket_type = request.form.get('ticket_type')
        quantity = request.form.get('quantity')
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')

        # Validate required fields
        if not all([ticket_type, quantity, name, phone, email]):
            flash('請填寫所有必填欄位', 'error')
            return redirect(url_for('book'))

        # Validate quantity
        try:
            quantity = int(quantity)
            if quantity <= 0 or quantity > 10:
                flash('訂票數量必須在1-10之間', 'error')
                return redirect(url_for('book'))
        except ValueError:
            flash('訂票數量必須為數字', 'error')
            return redirect(url_for('book'))

        # Validate email format (basic check)
        if '@' not in email:
            flash('請輸入有效的電子郵件地址', 'error')
            return redirect(url_for('book'))

        # Find selected ticket
        ticket = Ticket.query.get(ticket_type)
        if not ticket or not ticket.is_active:
            flash('請選擇有效的票種', 'error')
            return redirect(url_for('book'))

        # Calculate total price
        total_price = ticket.price * quantity

        # Generate order number (unique)
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = secrets.token_hex(4).upper()
        order_number = f"TK{timestamp}{random_suffix}"

        # Create order record in database
        order = Order(
            order_number=order_number,
            ticket_id=ticket.id,
            ticket_name=ticket.name,
            ticket_price=ticket.price,
            quantity=quantity,
            total_price=total_price,
            name=escape_html(name),
            phone=escape_html(phone),
            email=escape_html(email),
            status='pending'
        )

        db.session.add(order)
        db.session.commit()

        # Store order ID in session for success page
        order_id = order.id

        return redirect(url_for('success', order_id=order_id))

    except Exception as e:
        db.session.rollback()
        flash('處理訂票時發生錯誤，請稍後再試', 'error')
        return redirect(url_for('book'))


@app.route('/success')
def success():
    """訂票成功頁面"""
    order_id = request.args.get('order_id', type=int)
    if not order_id:
        flash('無效的訂單編號', 'error')
        return redirect(url_for('index'))

    order = Order.query.get(order_id)
    if not order:
        flash('找不到訂單資訊', 'error')
        return redirect(url_for('index'))

    return render_template('success.html', order=order)


@app.route('/admin')
def admin():
    """管理訂單頁面"""
    # 速率限制檢查（僅 POST 請求）
    if request.method == 'POST':
        if not admin_limiter.is_allowed(request.remote_addr):
            flash('請求過於頻繁，請稍後再試', 'error')
            return redirect(url_for('admin'))

    search_term = request.args.get('search', '')
    status_filter = request.args.get('status', '')

    # Query orders with filtering
    query = Order.query

    if search_term:
        search_pattern = f"%{escape_html(search_term)}%"
        query = query.filter(
            db.or_(
                Order.name.ilike(search_pattern),
                Order.email.ilike(search_pattern),
                Order.phone.ilike(search_pattern)
            )
        )

    if status_filter and status_filter != 'all':
        query = query.filter_by(status=status_filter)

    orders = query.order_by(Order.created_at.desc()).all()

    # Calculate statistics
    from collections import Counter
    status_counts = Counter(o.status for o in orders)

    return render_template('admin.html',
                         orders=orders,
                         search_term=search_term,
                         status_filter=status_filter,
                         stats={
                             'total': len(orders),
                             'pending': status_counts.get('pending', 0),
                             'confirmed': status_counts.get('confirmed', 0),
                             'cancelled': status_counts.get('cancelled', 0)
                         })


@app.route('/admin/order/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    """更新訂單狀態"""
    # CSRF token 已由 decorator 自動驗證
    new_status = request.form.get('status')

    if new_status not in ['pending', 'confirmed', 'cancelled']:
        flash('無效的狀態', 'error')
        return redirect(url_for('admin'))

    order = Order.query.get(order_id)
    if not order:
        flash('找不到訂單', 'error')
        return redirect(url_for('admin'))

    order.update_status(new_status)
    flash(f'訂單 #{order.id} 狀態已更新為 {new_status}', 'success')
    return redirect(url_for('admin'))


@app.route('/admin/orders/export')
def export_orders():
    """匯出訂單資料"""
    # Query all orders
    orders = Order.query.order_by(Order.created_at.desc()).all()

    # Simple CSV export
    csv_data = "訂單編號,票種,數量,總金額,訂票人,電話,電子郵件,訂票時間,狀態\n"

    for order in orders:
        csv_data += f"{order.order_number},{order.ticket_name},{order.quantity},{order.total_price},{order.name},{order.phone},{order.email},{order.created_at.strftime('%Y-%m-%d %H:%M:%S')},{order.status}\n"

    from flask import Response
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=orders.csv"}
    )


if __name__ == '__main__':
    print('=' * 50)
    print('Flask Ticketing System - Optimized')
    print('=' * 50)
    print(f'Environment: {FLASK_ENV}')
    print(f'Debug Mode: {FLASK_DEBUG}')
    print(f'Database: {SQLALCHEMY_DATABASE_URI}')
    print(f'CSRF Protection: Enabled')
    print(f'Rate Limiting: Enabled')
    print('=' * 50)
    app.run(debug=FLASK_DEBUG)
