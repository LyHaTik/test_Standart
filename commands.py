from flask.cli import AppGroup
from models import db, User

admin_cli = AppGroup('admin')

@admin_cli.command('create-admin')
def create_admin():
    username = input('Введите username: ')
    password = input('Введите пароль: ')
    role = 'admin'
    
    admin_user = User(username=username, role=role, balance=0, commission_rate=0)
    admin_user.set_password(password)
    db.session.add(admin_user)
    db.session.commit()
    print(f'Admin name: {username}\npassword: {password} создан.')
