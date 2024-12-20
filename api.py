from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required, login_user
from flask_restx import Api, Resource, fields

from models import Transaction, db, User


api_blueprint = Blueprint('api', __name__)


@api_blueprint.route('/login', methods=['POST'])
def login():
    """
    Авторизация пользователя.
    ---
    tags:
      - Authentication
    parameters:
      - name: username
        in: formData
        type: string
        required: true
        description: Имя пользователя.
      - name: password
        in: formData
        type: string
        required: true
        description: Пароль пользователя.
    responses:
      200:
        description: Успешная авторизация.
        schema:
          type: object
          properties:
            success:
              type: string
              example: Welkam!
      401:
        description: Неверный логин или пароль.
      400:
        description: Ошибка запроса.
    """
    username = request.form.get('username')
    password = request.form.get('password')
    try:
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return jsonify({"success": "Welkam!"}), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401
    except Exception as e:
        return jsonify({"error": f"{e}"}), 400


@api_blueprint.route('/create_transaction', methods=['POST'])
@login_required
def create_transaction():
    """
    Создание транзакции с автоматическим расчетом комиссии.
    ---
    tags:
      - Transactions
    parameters:
      - name: amount
        in: body
        required: true
        schema:
          type: object
          properties:
            amount:
              type: number
              example: 100.0
    responses:
      201:
        description: Транзакция успешно создана
        schema:
          type: object
          properties:
            message:
              type: string
              example: Транзакция создана
            transaction:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                amount:
                  type: number
                  example: 100.0
                username:
                  type: string
                  example: Admin
                commission:
                  type: number
                  example: 10.0
                status:
                  type: string
                  example: pending
      400:
        description: Ошибка ввода данных
      500:
        description: Внутренняя ошибка сервера
    """ 
    data = request.get_json()
    if not data or 'amount' not in data:
        return jsonify({"error": "Сумма(amount) не передана"}), 400

    try:
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({"error": "Сумма(amount) должна быть > 0"}), 400

        commission = amount * current_user.commission_rate

        transaction = Transaction(
            user_id=current_user.id,
            amount=amount,
            commission=commission,
            status='pending'
        )

        db.session.add(transaction)
        db.session.commit()

        return jsonify({
            "message": "Транзакция создана",
            "transaction": {
                "id": transaction.id,
                "amount": transaction.amount,
                "user": transaction.user.username,
                "commission": transaction.commission,
                "status": transaction.status
            }
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_blueprint.route('/cancel_transaction', methods=['POST'])
@login_required
def cancel_transaction():
    """
    Отмена транзакции.
    ---
    tags:
      - Transactions
    parameters:
      - name: id
        in: body
        required: true
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
    responses:
      200:
        description: Транзакция успешно отменена.
        schema:
          type: object
          properties:
            message:
              type: string
              example: Транзакция отменена!
            transaction:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                status:
                  type: string
                  example: canceled
      400:
        description: ID Транзакции не передан.
      404:
        description: Транзакция не найдена.
      500:
        description: Внутренняя ошибка сервера.
    """
    data = request.get_json()
    if not data or 'id' not in data:
        return jsonify({"error": "ID Транзакции не передан"}), 400

    try:
        transaction_id = int(data['id'])
        if current_user.role == 'regular':
            transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first()
        else:
            transaction = Transaction.query.filter_by(id=transaction_id).first()         
        if not transaction:
            return jsonify({"error": "Транзакция не найдена"}), 404

        transaction.status = 'canceled'
        db.session.commit()

        return jsonify({
            "message": "Транзакция отменена!",
            "transaction": {
                "id": transaction.id,
                "status": transaction.status
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_blueprint.route('/check_transaction', methods=['GET'])
@login_required
def check_transactions():
    """
    Получение списка транзакций.
    ---
    tags:
      - Transactions
    responses:
      200:
        description: Список транзакций.
        schema:
          type: object
          properties:
            transactions:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  user:
                    type: string
                    example: Admin
                  amount:
                    type: number
                    example: 100.0
                  commission:
                    type: number
                    example: 10.0
                  status:
                    type: string
                    example: pending
                  created_at:
                    type: string
                    example: "2024-12-20T10:30:00"
      500:
        description: Внутренняя ошибка сервера.
    """
    try:
        # Определяем, какие транзакции возвращать
        if current_user.role == 'regular':
            transactions = Transaction.query.filter_by(user_id=current_user.id).all()
        else:
            transactions = Transaction.query.all()

        # Формируем список транзакций
        transactions_list = [
            {
                "id": transaction.id,
                "user": transaction.user.username,
                "amount": transaction.amount,
                "commission": transaction.commission,
                "status": transaction.status,
                "created_at": transaction.created_at.isoformat()
            }
            for transaction in transactions
        ]

        return jsonify({"transactions": transactions_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

        
