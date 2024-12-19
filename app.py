from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user

from models import User, db
from admin import admin, setup_admin


login_manager = LoginManager()

login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    admin.init_app(app)

    # Регистрация модулей
    from api import api_blueprint
    app.register_blueprint(api_blueprint)
    
    # Регистрация команд CLI
    from commands import admin_cli
    app.cli.add_command(admin_cli)
    
    # Маршрут для логина
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            print(user)
            if user and user.check_password(password):  # Предполагается, что у модели User есть метод check_password
                print('ПРОШЛА!!!!')
                login_user(user)
                flash('Login successful', 'success')
                return redirect(url_for('admin.index'))  # Перенаправление в админку
            else:
                flash('Invalid username or password', 'danger')

        return render_template('login.html')  # Убедитесь, что шаблон login.html существует
    
    # Маршрут для регистрации
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            # Проверка, что пароли совпадают
            if password != confirm_password:
                flash('Passwords do not match', 'danger')
                return redirect(url_for('register'))

            # Проверка, что пользователь с таким именем не существует
            user = User.query.filter_by(username=username).first()
            if user:
                flash('Username already exists', 'danger')
                return redirect(url_for('register'))

            # Создание нового пользователя
            new_user = User(username=username)
            new_user.set_password(password)  # Убедитесь, что у вас есть метод set_password в модели User
            db.session.add(new_user)
            db.session.commit()

            # Вход в систему после регистрации
            login_user(new_user)
            flash('Registration successful', 'success')
            return redirect(url_for('admin.index'))  # Перенаправление в админку или на другую страницу
        
        return render_template('register.html')

    # Создание базы данных
    with app.app_context():
        db.create_all()
        setup_admin(admin, db)

    return app



if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
