from flask_admin.contrib.sqla import ModelView, filters
from flask_login import current_user
from flask import redirect, url_for
from flask_admin import Admin, expose, base
from wtforms import SelectField
from datetime import datetime

from models import User, Transaction, db


CHOISE_STATUS = [
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('canceled', 'Canceled'),
            ('expired', 'Expired'),
        ]

CHOISE_ROLE = [
    ('admin', 'Admin'),
    ('regular', 'Regular'),
    ]

class DashboardView(base.BaseView):
    @expose('/')
    def index(self):
        # Получаем количество пользователей
        user_count = User.query.count()
        
        # Получаем количество транзакций
        transaction_count = Transaction.query.count()
        
        # Получаем сумму транзакций за текущий день
        today = datetime.today().date()
        daily_total = db.session.query(db.func.sum(Transaction.amount)).filter(db.func.date(Transaction.created_at) == today).scalar() or 0.0
        
        # Получаем последние транзакции
        last_transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(5).all()
        
        # Отображаем данные в шаблоне
        return self.render('admin/dashboard.html', user_count=user_count, transaction_count=transaction_count, 
                           daily_total=daily_total, last_transactions=last_transactions)


class BaseModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, username, **kwargs):
        return redirect(url_for('login'))


class UserAdmin(BaseModelView):
    column_list = ['username', 'role', 'balance', 'commission_rate', 'webhook_url']

    can_create = False
    can_edit = True
    can_delete = True
    
    form_excluded_columns = ['password_hash']
    
    form_overrides = {
        'role': SelectField
    }
    
    form_args = {
        'role': {
            'choices': CHOISE_ROLE
        }
    }
    
    # Фильтрация пользователей для обычных пользователей (REGULAR)
    def get_query(self):
        if current_user.role == 'admin':
            return super().get_query()  # Для администратора - все пользователи
        return super().get_query().filter(User.id == current_user.id)  # Для обычного пользователя - только свой

    # Для правильного отображения количества записей в таблице
    def get_count_query(self):
        if current_user.role == 'admin':
            return super().get_count_query()  # Для администратора - все пользователи
        return super().get_count_query().filter(User.id == current_user.id)  # Для обычного пользователя - только свой


class UserFilter(filters.BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(Transaction.user_id == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        # Получение списка пользователей, у которых есть транзакции
        users = view.session.query(User.id, User.username).join(Transaction).distinct().all()
        return [(user.id, user.username) for user in users]


class StatusFilter(filters.BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        return query.filter(Transaction.status == value)

    def operation(self):
        return 'equals'

    def get_options(self, view):
        # Опции статусов
        return CHOISE_STATUS


class TransactionAdmin(BaseModelView):
    column_list = ['created_at', 'user.username', 'amount', 'commission', 'status']
    form_columns = ['amount', 'status']
    form_excluded_columns = ['user_id']
    form_overrides = {
        'status': SelectField
    }
    column_filters = [
        UserFilter(Transaction.user_id, 'User'),
        StatusFilter(Transaction.status, 'Status'),
    ]
    column_labels = {
        'user.username': 'User',
        'status': 'Status'
    }
    form_args = {
        'status': {
            'choices': CHOISE_STATUS
        }
    }
    
    def on_model_change(self, form, model, is_created):
        if is_created:
            if current_user.is_authenticated:
                model.user_id = current_user.id
                model.commission = float(model.amount) * float(current_user.commission_rate)
            else:
                raise Exception("Пользователь не аутентифицирован. Невозможно установить user_id.")
        return super().on_model_change(form, model, is_created)
    
    # Фильтрация транзакций для обычных пользователей (REGULAR)
    def get_query(self):
        if current_user.role == 'admin':
            return super().get_query()  # Для администратора - все транзакции
        return super().get_query().filter(Transaction.user_id == current_user.id)  # Для обычного пользователя - только свои транзакции

    # Для правильного отображения количества записей в таблице
    def get_count_query(self):
        if current_user.role == 'admin':
            return super().get_count_query()  # Для администратора - все транзакции
        return super().get_count_query().filter(Transaction.user_id == current_user.id)  # Для обычного пользователя - только свои транзакции
    

admin = Admin(template_mode='bootstrap4', name='Админка')

def setup_admin(admin, db):
    admin.add_view(DashboardView(name='Dashboard', endpoint='dashboard'))
    admin.add_view(UserAdmin(User, db.session, name="Users", endpoint="admin_user", url="/admin/user"))
    admin.add_view(TransactionAdmin(Transaction, db.session, name="Transactions", endpoint="admin_transaction", url="/admin/transaction"))

