from flask import Blueprint, request, jsonify
from models import db, User, Transaction

api_blueprint = Blueprint('api', __name__, url_prefix='/api')

@api_blueprint.route('/create_transaction', methods=['POST'])
def create_transaction():
    data = request.get_json()
    user_id = data.get('user_id')
    amount = data.get('amount')
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    commission = amount * user.commission_rate
    transaction = Transaction(user=user, amount=amount, commission=commission)
    db.session.add(transaction)
    db.session.commit()
    return jsonify({'message': 'Transaction created', 'transaction_id': transaction.id})

@api_blueprint.route('/cancel_transaction', methods=['POST'])
def cancel_transaction():
    data = request.get_json()
    transaction_id = data.get('transaction_id')
    transaction = Transaction.query.get(transaction_id)
    if not transaction or transaction.status != 'pending':
        return jsonify({'error': 'Transaction not found or invalid status'}), 404
    transaction.status = 'canceled'
    db.session.commit()
    return jsonify({'message': 'Transaction canceled'})

@api_blueprint.route('/check_transaction', methods=['GET'])
def check_transaction():
    transaction_id = request.args.get('transaction_id')
    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404
    return jsonify({
        'transaction_id': transaction.id,
        'status': transaction.status.value,
        'amount': transaction.amount,
        'commission': transaction.commission
    })
