from src.notify.taskapp.app import create_celery_app

app = create_celery_app()

if __name__ == "__main__":
    app.start()
