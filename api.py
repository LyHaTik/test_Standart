from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from models import Transaction, db

api_blueprint = Blueprint('api', __name__)

@api_blueprint.route('/create_transaction', methods=['POST'])
@login_required
def create_transaction():
    """
    Создание транзакции с автоматическим расчетом комиссии.
    JSON:
    {
        "id": (необязательно),
        "amount": 100.0
    }
    """
    data = request.get_json()
    if not data or 'amount' not in data:
        return jsonify({"error": "Amount is required"}), 400

    try:
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than 0"}), 400

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
            "message": "Transaction created successfully",
            "transaction": {
                "id": transaction.id,
                "amount": transaction.amount,
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
    JSON:
    {
        "id": 1
    }
    """
    data = request.get_json()
    if not data or 'id' not in data:
        return jsonify({"error": "Transaction ID is required"}), 400

    try:
        transaction_id = int(data['id'])
        transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first()

        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404

        if transaction.status != 'pending':
            return jsonify({"error": "Only pending transactions can be canceled"}), 400

        transaction.status = 'canceled'
        db.session.commit()

        return jsonify({
            "message": "Transaction canceled successfully",
            "transaction": {
                "id": transaction.id,
                "status": transaction.status
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_blueprint.route('/check_transaction', methods=['POST'])
@login_required
def check_transaction():
    """
    Проверка транзакции.
    JSON:
    {
        "id": 1
    }
    """
    data = request.get_json()
    if not data or 'id' not in data:
        return jsonify({"error": "Transaction ID is required"}), 400

    try:
        transaction_id = int(data['id'])
        transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first()

        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404

        return jsonify({
            "transaction": {
                "id": transaction.id,
                "amount": transaction.amount,
                "commission": transaction.commission,
                "status": transaction.status,
                "created_at": transaction.created_at
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
