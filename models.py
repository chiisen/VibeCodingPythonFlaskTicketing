"""
資料庫模型模組
定義應用程式的資料表結構
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 初始化 SQLAlchemy
db = SQLAlchemy()

# ═══════════════════════════════════════════
# 💡 概念：SQLAlchemy ORM（物件關係對映）
# 說明：使用 Python 類別定義資料表，無需直接寫 SQL
# 為何使用：簡化資料庫操作，避免 SQL Injection
# 注意事項：修改模型後需重新執行資料庫遷移
# ═══════════════════════════════════════════

class Ticket(db.Model):
    """票種模型"""
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='票種名稱')
    price = db.Column(db.Integer, nullable=False, comment='票價')
    description = db.Column(db.Text, comment='描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否啟用')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='建立時間')

    def __repr__(self):
        return f'<Ticket {self.name}>'

    def to_dict(self):
        """轉換為字典"""
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'description': self.description,
            'is_active': self.is_active
        }


class Order(db.Model):
    """訂單模型"""
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, comment='訂單編號')

    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False, comment='票種 ID')
    ticket_name = db.Column(db.String(100), nullable=False, comment='票種名稱')
    ticket_price = db.Column(db.Integer, nullable=False, comment='票價')

    quantity = db.Column(db.Integer, nullable=False, default=1, comment='購買數量')
    total_price = db.Column(db.Integer, nullable=False, comment='總金額')

    # 訂票人資訊
    name = db.Column(db.String(100), nullable=False, comment='訂票人姓名')
    phone = db.Column(db.String(50), nullable=False, comment='電話')
    email = db.Column(db.String(200), nullable=False, comment='電子郵件')

    # 狀態: pending, confirmed, cancelled
    status = db.Column(db.String(20), default='pending', comment='訂單狀態')

    created_at = db.Column(db.DateTime, default=datetime.now, comment='訂單時間')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新時間')

    # 關聯
    ticket = db.relationship('Ticket', backref=db.backref('orders', lazy=True))

    def __repr__(self):
        return f'<Order {self.order_number}>'

    def to_dict(self):
        """轉換為字典"""
        return {
            'id': self.id,
            'order_number': self.order_number,
            'ticket_id': self.ticket_id,
            'ticket_name': self.ticket_name,
            'ticket_price': self.ticket_price,
            'quantity': self.quantity,
            'total_price': self.total_price,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def update_status(self, new_status):
        """更新訂單狀態"""
        valid_statuses = ['pending', 'confirmed', 'cancelled']
        if new_status not in valid_statuses:
            raise ValueError(f'無效的狀態: {new_status}')
        self.status = new_status
        db.session.commit()
