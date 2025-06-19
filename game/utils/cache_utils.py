# game/cache_utils.py
from django.core.cache import cache
from ..models import GameMapNPC

def invalidate_map_cache(map_id):
    """
    使地图缓存失效
    :param map_id: 地图ID
    """
    # keys = [
    #     f"map_context_{map_id}",
    #     f"adjacent_maps_{map_id}"
    # ]
    # cache.delete_many(keys)
    keys = [
        f"map_context_{map_id}",
        f"adjacent_maps_{map_id}",
        f"map_players_{map_id}",
        f"map_items_{map_id}",
        f"map_npcs_{map_id}"
    ]
    
    # 添加通配符键（如果使用Redis）
    wildcard_keys = [
        f"map_*_{map_id}",
        f"player_*_map_{map_id}"
    ]
    
    # 批量删除缓存
    cache.delete_many(keys)
    
    # 如果是Redis，删除通配符匹配的键
    if hasattr(cache, 'delete_pattern') and callable(cache.delete_pattern):
        for pattern in wildcard_keys:
            cache.delete_pattern(pattern)
    
    # 简单日志（可选）
    print(f"地图缓存已清除: map_id={map_id}")

def invalidate_npc_cache(npc_id):
    """
    使NPC相关缓存失效
    :param npc_id: NPC ID
    """
    # 查找所有包含此NPC的地图
    map_ids = GameMapNPC.objects.filter(
        npc_id=npc_id
    ).values_list('map_id', flat=True).distinct()
    
    for map_id in map_ids:
        invalidate_map_cache(map_id)

def invalidate_player_cache(player_id):
    """
    使玩家相关缓存失效
    :param player_id: 玩家ID
    """
    # 玩家移动时会清除地图缓存，这里主要处理玩家数据变更
    cache.delete(f"player_data_{player_id}")
