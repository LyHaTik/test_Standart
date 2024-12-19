from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from enum import Enum
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()

class UserRole(Enum):
    ADMIN = 'admin'
    REGULAR = 'regular'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.REGULAR, nullable=False)
    balance = db.Column(db.Float, default=0.0)
    commission_rate = db.Column(db.Float, default=0.02)  # 2% комиссия
    webhook_url = db.Column(db.String(255))
    
    # Поле для хранения хэша пароля
    _password_hash = db.Column("password_hash", db.String(128), nullable=False)

    # Метод для установки пароля
    def set_password(self, password):
        self._password_hash = generate_password_hash(password)

    # Метод для проверки пароля
    def check_password(self, password):
        return check_password_hash(self._password_hash, password)
    
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    # Атрибут is_active для Flask-Login
    @property
    def is_active(self):
        return True  # Или добавьте свою логику активации пользователя

    def __str__(self):
        return f'User({self.id}, {self.username}, {self.role.value})'


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    commission = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending', nullable=False)  # Используем строки
    user = db.relationship('User', backref='transactions')

    def __str__(self):
        return f'Transaction({self.id}, User: {self.user_id}, Amount: {self.amount}, Status: {self.status})'
