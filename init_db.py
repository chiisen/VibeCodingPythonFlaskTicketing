#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫初始化腳本
建立資料表並預設填入票種資料
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 設定輸出編碼
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from app import app
from models import db, Ticket

def init_database():
    """初始化資料庫"""
    print("開始初始化資料庫...")

    with app.app_context():
        # 建立所有資料表
        db.create_all()
        print("[OK] 資料表建立完成")

        # 檢查是否已有票種資料
        if Ticket.query.first() is None:
            print("[INFO] 開始插入預設票種資料...")

            default_tickets = [
                Ticket(name='一般票', price=100, description='標準票種，適用於一般觀眾'),
                Ticket(name='學生票', price=80, description='需出示學生證，限學生購買'),
                Ticket(name='VIP票', price=200, description='VIP專區座位，包含精美禮品'),
                Ticket(name='團體票', price=90, description='10人以上團體優惠票種'),
            ]

            for ticket in default_tickets:
                db.session.add(ticket)

            db.session.commit()
            print("[OK] 預設票種資料已插入")
        else:
            print("[INFO] 票種資料已存在，跳過插入")

        # 顯示票種列表
        print("\n目前票種資料：")
        for ticket in Ticket.query.all():
            print(f"   - {ticket.name}: NT${ticket.price} (ID: {ticket.id})")

        print("\n[OK] 資料庫初始化完成！")

if __name__ == '__main__':
    init_database()
