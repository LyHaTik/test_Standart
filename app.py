from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user
from flasgger import Swagger
from api import api_blueprint

from models import User, db
from admin import admin, setup_admin
from commands import admin_cli


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
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    # Инициализация Swagger
    Swagger(app)
    
    # Регистрация команд CLI
    app.cli.add_command(admin_cli)
    
    
    # Маршрут для webhookа
    @app.route('/webhook', methods=['POST'])
    def webhook():
        try:
            data = request.get_json()

            if not data or 'transaction_id' not in data or 'status' not in data:
                return jsonify({'error': 'Не верно переданы данные или отсутствуют!'}), 400

            # Обработка вебхука
            print(f"Получен вебхук: {data}")
            return jsonify({'message': 'Webhook доставлен!'}), 200
        except Exception as e:
            return jsonify({'error': 'Ошибка на сервере!'}), 500
    
    # Маршрут для логина
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            try:
                user = User.query.filter_by(username=username).first()
                if user and user.check_password(password):
                    login_user(user)
                    flash('Успешный вход', 'success')
                    return redirect(url_for('admin.index'))
                else:
                    flash('Не верный логин или пароль', 'danger')
            except Exception as e:
                flash(f"Ошибка: {e}", 'danger')
        return render_template('login.html')
    
    # Маршрут для регистрации
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if password != confirm_password:
                flash('Разные пароли!', 'danger')
                return redirect(url_for('register'))

            user = User.query.filter_by(username=username).first()
            if user:
                flash(f'Имя {username} уже существует', 'danger')
                return redirect(url_for('register'))

            try:
                new_user = User(username=username)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                flash('Успешная регистрация', 'success')
                return redirect(url_for('admin.index'))
            except Exception as e:
                flash(f"Ошибка: {e}", 'danger')
                db.session.rollback()

        return render_template('register.html')

    # Создание базы данных
    with app.app_context():
        db.create_all()
        setup_admin(admin, db)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
