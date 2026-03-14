"""
速率限制模組
使用 Flask-Limiter 提供 API 請求速率限制
"""
from functools import wraps
from datetime import datetime

# 簡易記憶體速率限制器（不依賴額外套件）
class SimpleRateLimiter:
    """簡單的記憶體速率限制器"""

    def __init__(self, max_requests=5, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {ip: [timestamp1, timestamp2, ...]}

    def _clean_old_requests(self, key):
        """清除過期的請求記錄"""
        now = datetime.now().timestamp()
        if key in self.requests:
            self.requests[key] = [
                ts for ts in self.requests[key]
                if now - ts < self.window_seconds
            ]

    def is_allowed(self, identifier):
        """檢查請求是否允許"""
        self._clean_old_requests(identifier)

        if identifier not in self.requests:
            self.requests[identifier] = []

        if len(self.requests[identifier]) >= self.max_requests:
            return False

        self.requests[identifier].append(datetime.now().timestamp())
        return True

    def get_remaining(self, identifier):
        """獲取剩餘請求次數"""
        self._clean_old_requests(identifier)
        remaining = self.max_requests - len(self.requests.get(identifier, []))
        return max(0, remaining)

# 全域速率限制器（提交表單：5次/分鐘）
submit_limiter = SimpleRateLimiter(max_requests=5, window_seconds=60)
# 全域速率限制器（管理頁面：10次/分鐘）
admin_limiter = SimpleRateLimiter(max_requests=10, window_seconds=60)

def rate_limit(limiter_class, identifier_func=None):
    """速率限制 decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request, jsonify, abort

            # 使用 IP 作為識別
            identifier = request.remote_addr

            if not limiter_class.is_allowed(identifier):
                abort(429, '請求過於頻繁，請稍後再試')

            return f(*args, **kwargs)
        return decorated_function
    return decorator
