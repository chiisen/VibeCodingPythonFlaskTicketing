from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key

# Sample ticket data
TICKETS = [
    {
        'id': 1,
        'name': '一般票',
        'price': 100,
        'description': '標準票種，適用於一般觀眾'
    },
    {
        'id': 2,
        'name': '學生票',
        'price': 80,
        'description': '需出示學生證，限學生購買'
    },
    {
        'id': 3,
        'name': 'VIP票',
        'price': 200,
        'description': 'VIP專區座位，包含精美禮品'
    },
    {
        'id': 4,
        'name': '團體票',
        'price': 90,
        'description': '10人以上團體優惠票種'
    }
]

# Store orders in memory (in production, use a database)
orders = []

@app.route('/')
def index():
    """首頁：顯示票種資訊"""
    return render_template('index.html', tickets=TICKETS)

@app.route('/book')
def book():
    """訂票表單頁面"""
    return render_template('book.html', tickets=TICKETS)

@app.route('/submit', methods=['POST'])
def submit():
    """處理訂票提交"""
    try:
        # Get form data
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
        ticket = next((t for t in TICKETS if str(t['id']) == ticket_type), None)
        if not ticket:
            flash('請選擇有效的票種', 'error')
            return redirect(url_for('book'))

        # Calculate total price
        total_price = ticket['price'] * quantity

        # Create order
        order = {
            'id': len(orders) + 1,
            'ticket_type': ticket['name'],
            'ticket_price': ticket['price'],
            'quantity': quantity,
            'total_price': total_price,
            'name': name,
            'phone': phone,
            'email': email,
            'order_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'pending'  # pending, confirmed, cancelled
        }

        orders.append(order)

        # Store order in session for success page
        order_id = order['id']

        return redirect(url_for('success', order_id=order_id))

    except Exception as e:
        flash('處理訂票時發生錯誤，請稍後再試', 'error')
        return redirect(url_for('book'))

@app.route('/success')
def success():
    """訂票成功頁面"""
    order_id = request.args.get('order_id', type=int)
    if not order_id:
        flash('無效的訂單編號', 'error')
        return redirect(url_for('index'))

    order = next((o for o in orders if o['id'] == order_id), None)
    if not order:
        flash('找不到訂單資訊', 'error')
        return redirect(url_for('index'))

    return render_template('success.html', order=order)

@app.route('/admin')
def admin():
    """管理訂單頁面"""
    search_term = request.args.get('search', '')
    status_filter = request.args.get('status', '')

    # Filter orders based on search term and status
    filtered_orders = orders

    if search_term:
        filtered_orders = [
            order for order in filtered_orders
            if search_term.lower() in order['name'].lower() or
               search_term.lower() in order['email'].lower() or
               search_term.lower() in order['phone'].lower()
        ]

    if status_filter and status_filter != 'all':
        filtered_orders = [
            order for order in filtered_orders
            if order['status'] == status_filter
        ]

    return render_template('admin.html', orders=filtered_orders, search_term=search_term, status_filter=status_filter)

@app.route('/admin/order/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    """更新訂單狀態"""
    new_status = request.form.get('status')

    if new_status not in ['pending', 'confirmed', 'cancelled']:
        flash('無效的狀態', 'error')
        return redirect(url_for('admin'))

    order = next((o for o in orders if o['id'] == order_id), None)
    if not order:
        flash('找不到訂單', 'error')
        return redirect(url_for('admin'))

    order['status'] = new_status
    flash(f'訂單 #{order_id} 狀態已更新為 {new_status}', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/orders/export')
def export_orders():
    """匯出訂單資料"""
    # Simple CSV export
    csv_data = "訂單編號,票種,數量,總金額,訂票人,電話,電子郵件,訂票時間,狀態\n"

    for order in orders:
        csv_data += f"{order['id']},{order['ticket_type']},{order['quantity']},{order['total_price']},{order['name']},{order['phone']},{order['email']},{order['order_time']},{order['status']}\n"

    from flask import Response
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=orders.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True)
