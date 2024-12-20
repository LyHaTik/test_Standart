from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='regular', nullable=False)
    balance = db.Column(db.Float, default=0.0)
    commission_rate = db.Column(db.Float, default=0.03)
    webhook_url = db.Column(db.String(255), default='http://localhost:5000/webhook')
    
    # Поле для хранения хэша пароля
    password_hash = db.Column("password_hash", db.String(128), nullable=False)

    # Метод для установки пароля
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Метод для проверки пароля
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    # Атрибут is_active для Flask-Login
    @property
    def is_active(self):
        return True

    def __str__(self):
        return f'User({self.id}, {self.username}, {self.role})'


class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    commission = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending', nullable=False)
    user = db.relationship('User', backref='transactions')

    def __str__(self):
        return f'Transaction({self.id}, User: {self.user_id}, Amount: {self.amount}, Status: {self.status})'


class TaskSchedule(db.Model):
    __tablename__ = 'taskschedule'
    
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(255), unique=True, nullable=False)
    interval_seconds = db.Column(db.Integer, default=60)
    last_run = db.Column(db.DateTime, nullable=True)
    
    def __str__(self):
        return f"TaskSchedule {self.task_name}"
