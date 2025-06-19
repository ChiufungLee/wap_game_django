# wap_game/celery.py
import os
from celery import Celery

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wap_game.settings')

app = Celery('wap_game')

# 使用 Django 设置文件中的配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务
app.autodiscover_tasks(['game.utils.tasks'])

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')