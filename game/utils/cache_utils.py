# game/cache_utils.py
from django.core.cache import cache, caches
from ..models import GameMapNPC, Player, GameNPC

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

    cache_keys = [
        f"npc_{self.id}_info",
        f"npc_drop_info_{self.id}",
        f"boss_hp_{self.id}"  # 如果是BOSS，清除血条缓存
    ]
    cache.delete_many(cache_keys)

    for map_id in map_ids:
        invalidate_map_cache(map_id)

def invalidate_player_cache(player_id):
    """
    使玩家相关缓存失效
    :param player_id: 玩家ID
    """
    # 玩家移动时会清除地图缓存，这里主要处理玩家数据变更
    cache.delete(f"player_data_{player_id}")
    cache.delete(f"player_combat_{player_id}")
    cache.delete(f"player_skills:{player_id}")

cache = caches['combat']

# def get_player_combat_stats(player_id):
#     """获取玩家战斗属性（基础+装备+技能），使用缓存优化"""
#     key = f"player_combat_{player_id}"
#     stats = cache.get(key)
    
#     if not stats:
#         player = Player.objects.get(id=player_id)
#         # 基础属性
#         stats = player.total_attributes()
        
#         # 叠加技能属性
#         for skill in player.skills.select_related('skill').only('attack', 'defense'):
#             stats['min_attack'] += skill.attack
#             stats['max_attack'] += skill.attack
#             stats['min_defense'] += skill.defense
#             stats['max_defense'] += skill.defense
        
#         # 缓存30分钟
#         cache.set(key, stats, 1800)
    
#     return stats

# def invalidate_player_cache(player_id):
#     """玩家属性变更时清除缓存"""
#     cache.delete(f"player_combat_{player_id}")

def get_boss_hp(npc_id):
    """获取BOSS当前血量（共享血条）"""
    return cache.get_or_set(
        f"boss_hp_{npc_id}", 
        lambda: GameNPC.objects.get(id=npc_id).hp,
        600  # 10分钟过期
    )

def update_boss_hp(npc_id, damage):
    """原子更新BOSS血量"""
    with cache.lock(f"boss_lock_{npc_id}"):
        current_hp = cache.get(f"boss_hp_{npc_id}", 0)
        new_hp = max(0, current_hp - damage)
        cache.set(f"boss_hp_{npc_id}", new_hp, 600)
        return new_hp




def invalidate_npc_cache(npc_id):
    """清除NPC相关缓存"""
    keys = [
        f"npc_{npc_id}_info",
        f"npc_drop_info_{npc_id}",
        f"boss_hp_{npc_id}"
    ]
    cache.delete_many(keys)