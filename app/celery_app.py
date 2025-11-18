try:
    from celery import Celery
except ImportError:
    Celery = None

celery_app = None


def make_celery(app):
    global celery_app

    if Celery is None:
        print("⚠ Celery chưa cài, background task sẽ chạy sync.")
        celery_app = None
        return None

    celery = Celery(
        app.import_name,
        broker=app.config.get("CELERY_BROKER_URL"),
        backend=app.config.get("CELERY_RESULT_BACKEND"),
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask
    celery_app = celery
    return celery
