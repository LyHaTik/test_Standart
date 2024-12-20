from datetime import datetime, timedelta
import requests
import logging
from app import create_app
from celery import Celery

from models import db, Transaction, TaskSchedule


# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем Celery приложение
celery_app = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
)

celery_app.conf.beat_schedule = {
    'dynamic-scheduler': {
        'task': 'tasks.scheduler',
        'schedule': timedelta(seconds=1),
    },
}

celery_app.conf.timezone = 'UTC'


# Интеграция с Flask
def make_celery(app):
    celery_app.conf.update(app.config)
    TaskBase = celery_app.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app

app = create_app()
celery = make_celery(app)


@celery.task
def scheduler():
    """
    Планировщик задач. Проверяет расписания задач и запускает их.
    """
    with app.app_context():
        now = datetime.now()
        schedules = TaskSchedule.query.all()
        for schedule in schedules:
            if not schedule.last_run or (now - schedule.last_run).total_seconds() >= schedule.interval_seconds:
                try:
                    # Запуск Celery задачи
                    check_expired_transactions()
                    # Обновляем отметку времени
                    schedule.last_run = now
                    db.session.commit()
                    logger.info(f"Задача {schedule.task_name} выполнена успешно.")
                except Exception as e:
                    logger.error(f"Ошибка при запуске задачи {schedule.task_name}: {str(e)}")


def send_webhook(transaction):
    """
    Отправляет вебхук для транзакции.
    """
    if transaction.user and transaction.user.webhook_url:
        try:
            payload = {
                'user_id': transaction.user_id,
                'transaction_id': transaction.id,
                'status': transaction.status
            }
            response = requests.post(transaction.user.webhook_url, json=payload)
            response.raise_for_status()
            logger.info("Вебхук успешно отправлен для транзакции ID", transaction.id)
        except requests.RequestException as e:
            logger.error("Ошибка отправки вебхука для транзакции ID", transaction.id, str(e))


def check_expired_transactions():
    """
    Проверяет транзакции со статусом 'pending' и обновляет их на 'expired'.
    """
    with app.app_context():
        now = datetime.now()
        fifteen_minutes_ago = now - timedelta(minutes=15)

        logger.info("Запуск проверки истекших транзакций. Текущее время: %s", now)

        # Поиск всех транзакций со статусом 'pending', созданных более 15 минут назад
        try:
            expired_transactions = Transaction.query.filter(
                Transaction.status == 'pending',
                Transaction.created_at < fifteen_minutes_ago
            ).all()

            logger.info("Найдено истекших транзакций: %d", len(expired_transactions))

            for transaction in expired_transactions:
                transaction.status = 'expired'
                db.session.add(transaction)

                send_webhook(transaction)

            db.session.commit()
            logger.info("Обновлено транзакций: %d", len(expired_transactions))
        except Exception as e:
            logger.error(f"Ошибка при обработке транзакций: {str(e)}")
