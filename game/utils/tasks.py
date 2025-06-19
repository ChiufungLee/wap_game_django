# tasks.py
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from ..models import Player
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

@shared_task
def update_offline_status():
    """更新玩家离线状态（每10分钟运行一次）"""
    """更新玩家离线状态（每10分钟运行一次）"""
    offline_threshold = timezone.now() - timedelta(minutes=10)
    
    try:
        # 获取需要标记为离线的玩家ID列表
        offline_player_ids = Player.objects.filter(
            is_online=True,  # 当前标记为在线
            last_active__lte=offline_threshold  # 最后活动时间超过10分钟
        ).values_list('id', flat=True)
        
        # 转换为列表，使查询独立
        offline_player_ids_list = list(offline_player_ids)
        
        if not offline_player_ids_list:
            logger.info("没有需要标记为离线的玩家")
            return "没有玩家需要标记为离线"
        
        # 批量更新数据库状态
        count = Player.objects.filter(
            id__in=offline_player_ids_list
        ).update(is_online=False)
        
        # 清除缓存状态
        for player_id in offline_player_ids_list:
            cache_key = f"player_status:{player_id}"
            cache.delete(cache_key)
        
        logger.info(f"标记了 {count} 名玩家为离线状态")
        return f"成功标记 {count} 名玩家离线"
    
    except Exception as e:
        logger.error(f"更新离线状态时出错: {str(e)}")
        return f"更新离线状态失败: {str(e)}"


@shared_task
def handle_long_offline_players():
    """处理长时间离线的玩家（每30分钟运行一次）"""
    # 检查30分钟未活动的玩家
    long_offline_threshold = timezone.now() - timedelta(minutes=30)
    
    # 获取长时间离线的玩家
    long_offline_players = Player.objects.filter(
        is_online=False,
        last_active__lte=long_offline_threshold
    )
    
    count = long_offline_players.count()
    
    # 示例：释放帮派资源
    for player in long_offline_players:
        # 这里可以添加您的特殊逻辑
        # 例如：player.release_gang_resources()
        pass
    
    logger.info(f"处理了 {count} 名长时间离线玩家")
    return f"处理了 {count} 名长时间离线玩家"