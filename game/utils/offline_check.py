from django.utils import timezone
from .models import Player
from datetime import timedelta

def update_player_offline_status():
    """更新玩家离线状态"""
    # 检查10分钟未活动的玩家
    offline_threshold = timezone.now() - timedelta(minutes=10)
    
    # 批量更新需要标记为离线的玩家
    players_to_update = Player.objects.filter(
        offline_at__isnull=True,
        last_active__lte=offline_threshold
    )
    
    for player in players_to_update:
        player.offline_at = player.last_active + timedelta(minutes=10)
        player.save()