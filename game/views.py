from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.cache import cache
from .models import *
from .utils.middleware import ParamSecurity
from .utils.cache_utils import *
from .utils.component_renderer import ComponentRenderer
from django.urls import reverse
import time
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import json
import random
from datetime import datetime, timedelta
from django.db import transaction
import ujson
from django.utils import timezone
import logging
logger = logging.getLogger(__name__)



# 缓存时间设置
MAP_CACHE_TIMEOUT = 60 * 15  # 15分钟缓存
MAX_ITEMS_DISPLAY = 10       # 最多显示物品数量
MAX_PLAYERS_DISPLAY = 20     # 最多显示玩家数量

# def get_default_map():
#     """获取默认地图"""
#     try:
#         return GameBase.objects.get(id=1).default_map
#     except GameBase.DoesNotExist:
#         return None


def get_default_map():
    """获取默认起始地图"""
    cache_key = "default_map_id"
    map_id = cache.get(cache_key)
    
    if not map_id:
        # 查找标记为起始点的地图
        default_map = GameMap.objects.filter(params__is_start=True).first()
        if default_map:
            map_id = default_map.id
            cache.set(cache_key, map_id, 24 * 3600)  # 缓存24小时
        else:
            # 如果没有设置，取第一个地图
            first_map = GameMap.objects.order_by('id').first()
            map_id = first_map.id if first_map else None
    
    return map_id

def generate_direction_links(exits, player_id):
    """生成方向链接的加密cmd"""
    links = {}
    for direction, info in exits.items():
        # 创建方向移动命令
        encrypted_cmd = ParamSecurity.generate_param(
            entity_type='map',
            sub_action='move',
            params={
                'direction': direction,
                'player_id': player_id
            },
            action='map'
        )
        links[direction] = encrypted_cmd
    print(links)
    return links

def get_player_skills(player_id):
    """获取玩家技能数据（带缓存）"""
    cache_key = f"player_skills:{player_id}"
    cached_skills = cache.get(cache_key)
    
    if cached_skills is not None:
        return cached_skills
    
    # 模拟从数据库获取玩家技能
    # 实际项目中应替换为真实数据库查询
    skill_list = PlayerSkill.objects.filter(player_id=player_id)
    skills = []
    for skill in skill_list:
        skills.append({
            'id':skill.skill.id,
            'name':skill.skill.name,
            'level': skill.current_level,
            'attack': skill.attack,
            'defense': skill.defense,
            'linghunli': skill.linghunli,
            'douqi': skill.douqi,
        })
    
    # 设置缓存（10分钟）
    cache.set(cache_key, skills, 600)
    return skills

def generate_loot(npc_id):
    """
    生成怪物掉落物品
    :return: 物品ID列表
    """
    # 优化查询：仅获取掉落概率>0的物品
    # 获取当前怪物的掉落配置
    cache_key = f"npc_drops_{npc_id}"
    drop_list = cache.get(cache_key)
    
    if drop_list is None:
        # 从数据库获取掉落配置
        drop_list = list(NPCDropList.objects.filter(
            npc_id=npc_id, 
            gailv__gt=0
        ).values('item_id', 'gailv',  'count'))
        
        # 缓存10分钟
        cache.set(cache_key, drop_list, 600)

    # drop_list = NPCDropList.objects.filter(
    #     npc_id=npc_id, 
    #     gailv__gt=0
    # ).select_related('item').only('item_id', 'gailv')
    
    loot = {}
    for drop in drop_list:
        # 根据概率决定是否掉落
        if random.randint(1, 100) <= drop['gailv']:
            # 随机决定掉落数量
            max_count = drop.get('max_count',1)
            quantity = random.randint(1, max_count)
            
            # 合并相同物品的数量
            item_id = drop['item_id']
            loot[item_id] = loot.get(item_id, 0) + quantity
    print(f"怪物 {npc_id} 掉落物品: {loot}")
    # print(loot)
    return loot


def get_player_combat_stats(player_id):
    """获取玩家战斗属性（基础+装备+技能），使用缓存优化"""
    key = f"player_combat_{player_id}"
    stats = cache.get(key)
    
    if not stats:
        player = Player.objects.get(id=player_id)
        # 基础属性
        stats = player.total_attributes()
        
        # 获取玩家技能（使用缓存函数）
        skills = get_player_skills(player_id)
        
        # 叠加技能属性
        for skill in skills:
            stats['min_attack'] += skill['attack']
            stats['max_attack'] += skill['attack']
            stats['min_defense'] += skill['defense']
            stats['max_defense'] += skill['defense']
            # 添加其他技能属性（如灵魂力、斗气等）
            stats['linghunli'] += skill.get('linghunli', 0)

        # 缓存30分钟
        cache.set(key, stats, 1800)
    
    return stats

def attack_monster(player_id, npc_id, skill_id=None):
    """
    核心攻击逻辑
    :param player_id: 玩家ID
    :param npc_id: 怪物ID
    :param skill_id: 可选技能ID
    :return: (是否击杀, 玩家伤害, 怪物伤害, 怪物剩余血量, 玩家剩余血量, 玩家是否死亡)
    """
    # 获取怪物和玩家信息
    monster = GameNPC.objects.only('hp', 'attack', 'defense', 'is_boss', 'exp_reward', 'gold_reward').get(id=npc_id)
    player_stats = get_player_combat_stats(player_id)
    player = Player.objects.get(id=player_id)  # 获取玩家对象
    
    # 应用技能效果
    skill_name = None
    if skill_id:
        skills = get_player_skills(player_id)
        selected_skill = next((s for s in skills if s['id'] == skill_id), None)
        
        if selected_skill:
            # 应用技能额外加成
            attack_bonus = selected_skill.get('skill_attack_bonus', 0)
            player_stats['min_attack'] += attack_bonus
            player_stats['max_attack'] += attack_bonus
            skill_name = selected_skill['name']
            
            # 消耗资源（如灵魂力）
            linghunli_cost = selected_skill.get('linghunli', 0)
            player_stats['linghunli'] -= linghunli_cost
            player.linghunli = max(0, player.linghunli - linghunli_cost)
    
    # 计算玩家攻击伤害
    player_attack = random.randint(player_stats['min_attack'], player_stats['max_attack'])
    defense = monster.defense
    player_damage = max(1, player_attack - defense)  # 至少造成1点伤害
    
    # 计算怪物反击伤害
    monster_attack = monster.attack
    player_defense = random.randint(player_stats['min_defense'], player_stats['max_defense'])
    monster_damage = max(1, monster_attack - player_defense)
    
    # 应用伤害到玩家
    player.current_hp = max(0, player.current_hp - monster_damage)
    
    # 检查玩家是否死亡
    player_died = player.current_hp <= 0
    
    # 处理玩家死亡
    if player_died:
        # 传送玩家到安全区（地图ID=1）
        player.map_id = 5
        
        # 恢复部分生命值（例如恢复50%最大生命值）
        recovered_hp = int(player.max_hp * 0.2)
        player.current_hp = recovered_hp
        
        # 设置死亡状态
        player_died = True
    else:
        # 如果玩家没有死亡，保存状态
        player.save()
    
    # 处理不同怪物类型（只有在玩家没有死亡时才继续攻击）
    is_killed = False
    new_hp = monster.hp  # 默认值
    
    if not player_died:
        if monster.is_boss:
            # BOSS共享血条
            new_hp = update_boss_hp(npc_id, player_damage)
            is_killed = (new_hp <= 0)
            
            if is_killed:
                # BOSS击杀处理
                reward_info = handle_kill_reward(player_id, monster)
                cache.delete(f"boss_hp_{npc_id}")  # 清除BOSS缓存
        else:
            # 普通怪物独立血条（临时缓存）
            hp_key = f"monster_{npc_id}_{player_id}"
            current_hp = cache.get_or_set(hp_key, monster.hp, 300)  # 5分钟缓存
            new_hp = max(0, current_hp - player_damage)
            is_killed = (new_hp <= 0)
            cache.set(hp_key, new_hp, 300)
            
            if is_killed:
                # 普通怪物击杀处理
                reward_info = handle_kill_reward(player_id, monster)
                print(reward_info)
                cache.delete(hp_key)
    
    # 如果玩家死亡，保存状态（包含传送和恢复后的状态）
    if player_died:
        player.save()
    
    return {
        'killed': is_killed,
        'player_damage': player_damage,
        'monster_damage': monster_damage,
        'remaining_hp': new_hp,
        'player_current_hp': player.current_hp,
        'skill_used': skill_name,
        'player_died': player_died,
        'reward_info': reward_info if is_killed else None
    }

def handle_kill_reward(player_id, monster):
    """处理击杀奖励并返回奖励信息"""
    player = Player.objects.get(id=player_id)
    
    # 基础奖励
    exp_reward = monster.exp_reward
    gold_reward = monster.gold_reward
    
    player.current_exp += exp_reward
    player.money += gold_reward
    
    # 物品掉落
    loot_items = generate_loot(monster.id)
    loot_info = []
    
    if loot_items:
        # 简化的背包添加逻辑
        # for item_id in loot_items:
        #     item = Item.objects.get(id=item_id)
        #     loot_info.append({
        #         'id': item.id,
        #         'name': item.name,
        #         'quantity': 1
        #     })
        #     player.add_to_bag(item_id)
            # 获取玩家当前位置
        player_location = player.map_id

                # 创建地图物品实例 - 每个物品只创建一个实例
        for item_id, quantity in loot_items.items():
            item = Item.objects.get(id=item_id)
            
            # 创建单个地图物品实例，数量为总数量
            GameMapItem.objects.create(
                item_id=item_id,
                map_id=player_location,
                count=quantity,  # 关键：这里设置总数量
                expire_time=timezone.now() + timedelta(minutes=30)
            )    
            loot_info.append({
                'id': item.id,
                'name': item.name,
                'quantity': quantity
            })
    player.save()
    
    # 返回奖励信息
    return {
        'exp': exp_reward,
        'gold': gold_reward,
        'loot': loot_info
    }

# 获取并缓存怪物掉落信息
def get_npc_info(npc_id):
    """
    获取NPC信息（带缓存）
    """
    cache_key = f"npc_{npc_id}_info"
    cached_info = cache.get(cache_key)
    
    if cached_info:
        return cached_info
    
    npc = GameNPC.objects.only(
        'name', 'npc_type', 'level', 'description', 
        'hp', 'attack', 'defense', 'exp_reward', 'gold_reward',
        'dialogue', 'shop_items', 'is_boss'
    ).get(id=npc_id)
    
    # 如果是怪物，获取掉落信息
    drop_info = None
    if npc.npc_type == 'monster':
        drop_info = get_npc_drop_info(npc_id)
    
    npc_info = {
        'id': npc.id,
        'name': npc.name,
        'type': npc.npc_type,
        'level': npc.level,
        'description': npc.description,
        'hp': npc.hp,
        'attack': npc.attack,
        'defense': npc.defense,
        'exp_reward': npc.exp_reward,
        'gold_reward': npc.gold_reward,
        'dialogue': npc.dialogue,
        'shop_items': npc.shop_items,
        'is_boss': npc.is_boss,
        'drop_info': drop_info
    }
    
    # 设置缓存（1小时）
    cache.set(cache_key, npc_info, 3600)
    return npc_info

def get_npc_drop_info(npc_id):
    """
    获取NPC掉落信息（带缓存）
    """
    cache_key = f"npc_drop_info_{npc_id}"
    cached_info = cache.get(cache_key)
    
    if cached_info:
        return cached_info
    
    # 获取最新版本的掉落配置
    drop_list = NPCDropList.objects.filter(
        npc_id=npc_id, 
        gailv__gt=0
    ).select_related('item').values(
        'item_id', 'gailv', 'count', 'item__name'
    )

    drop_info = []
    for drop in drop_list:
        drop_info.append({
            'item_id': drop['item_id'],
            'item_name': drop['item__name'],
            'gailv': drop['gailv'],
            'count': drop.get('count', 1),
            # 'item_params': ParamSecurity.generate_param(
            #     entity_type="item", 
            #     sub_action="detail_item", 
            #     params={'item_id':drop['item_id']}, 
            #     action="item"
            # ),
        })
    
    # 设置缓存（24小时）
    cache.set(cache_key, drop_info, 86400)
    return drop_info

def get_map_context(map_id, player_id=None):
    """
    获取地图上下文数据（带缓存）
    :param map_id: 地图ID
    :param player_id: 当前玩家ID（用于排除玩家自身）
    :return: 地图上下文字典
    """
    cache_key = f"map_context_{map_id}"
    context = cache.get(cache_key)
    
    if context:
        return context
    
    current_map = GameMap.objects.select_related(
        'north', 'south', 'east', 'west', 'city', 'city__area'
    ).only(
        'id', 'name', 'is_safe_zone', 'is_city',
        'north_id', 'south_id', 'east_id', 'west_id',
        'north__name', 'south__name', 'east__name', 'west__name',
        'city__name', 'city__area__name'
    ).get(id=map_id)
    
    # 获取城市和区域名称
    city_name = current_map.city.name if current_map.city else "未知城市"
    area_name = current_map.city.area.name if current_map.city and current_map.city.area else "未知区域"
    exits = {}
    direction_exits = []
    for direction in ['north', 'south', 'east', 'west']:
        adj_map = getattr(current_map, direction)
        if direction == 'north':
            direction = '北'
        elif direction == 'south':
            direction = '南'
        elif direction == 'east':
            direction = '东'
        elif direction == 'west':
            direction = '西'
        else:
            pass
        if adj_map:
            cmd_params = ParamSecurity.generate_param(entity_type="wap", sub_action="none", params={"map_id":adj_map.id}, action="wap")
            exits[direction] = {
                'id': adj_map.id,
                'name': adj_map.name,
                'cmd_params':cmd_params

            }
            
            direction_link = '<a href="/wap/?cmd={}">{}</a>'.format(cmd_params,adj_map.name)
            direction_exits.append(direction_link)


    npc_instances = GameMapNPC.objects.filter(
        map_id=map_id
    ).only('id', 'npc_id', 'count')
    # print(npc_instances)
    # 收集所有 NPC ID
    npc_ids = [instance.npc_id for instance in npc_instances]
    
    # 批量获取 NPC 对象
    npcs_objs = GameNPC.objects.filter(id__in=npc_ids).only(
        'id', 'name', 'npc_type', 'level', 'description'
    )
    npc_map = {npc.id: npc for npc in npcs_objs}

    npcs = []
    monsters = []
    for instance in npc_instances:
        npc = npc_map.get(instance.npc_id)
        if not npc:
            continue

        # 获取怪物的掉落信息（如果是怪物类型）
        # drop_info = None
        # if npc.npc_type == 'monster':
        #     drop_info = get_npc_drop_info(npc.id)
        
        cmd_params = ParamSecurity.generate_param(
            entity_type="gamenpc", 
            sub_action="detail_npc", 
            params={"npc_id":npc.id}, 
            action="gamenpc"
        )

        if npc.npc_type == 'monster':

            for i in range(instance.count):
                monsters.append({
                'id': npc.id,
                'name': npc.name,
                'type': npc.npc_type,
                # 'level': npc.level,
                # 'count': instance.count,
                'cmd_params': cmd_params,
                # 'hp': npc.hp,
                # 'level': npc.level,
                # 'attack': npc.attack,
                # 'defense': npc.defense,
                # 'exp_reward': npc.exp_reward,
                # 'gold_reward': npc.gold_reward,
                # 'drop_info': drop_info  
                
            })
        else:
            npcs.append({
                'id': npc.id,
                'name': npc.name,
                'type': npc.npc_type,
                # 'description': npc.description,
                # 'dialogue': npc.dialogue,
                'cmd_params': cmd_params
            })
    
    # 获取地图物品（排除已拾取和过期的）
    item_list = GameMapItem.objects.filter(
        map_id=map_id,
        expire_time__gt=timezone.now(),
        picked_by__isnull=True
    ).select_related('item').only(
        'id', 'item__id', 'item__name', 'count'
    )[:MAX_ITEMS_DISPLAY]
    
    items = []
    for item in item_list:
        cmd_params = ParamSecurity.generate_param(entity_type="item", sub_action="get_item", params={"map_item_id":item.id,"item_id":item.item.id}, action="item")
        items.append({
                'id': item.item.id,
                'name': item.item.name,
                'cmd_params': cmd_params,
                'count': item.count
            })
    # 获取地图玩家（排除自己）
    players_query = Player.objects.filter(map_id=map_id)
    if player_id:
        players_query = players_query.exclude(id=player_id)
    
    map_players = players_query.only(
        'id', 'name', 'level', 
    )[:MAX_PLAYERS_DISPLAY]
    players = []
    for player in map_players:
        if not player:
            continue
        print(player)
        cmd_params = ParamSecurity.generate_param(entity_type="player", sub_action="detail_player", params={"player_id":player.id}, action="player")
        players.append({
                'id': player.id,
                'name': player.name,
                'cmd_params': cmd_params,
                'level': player.level
            })
    
    # 构建上下文
    context = {
        'map': current_map,
        'exits': exits,
        'npcs': npcs,
        'monsters': monsters,
        'items': items,
        'players': players,
        'has_more_items': GameMapItem.objects.filter(
            map_id=map_id,
            expire_time__gt=timezone.now(),
            picked_by__isnull=True
        ).count() > MAX_ITEMS_DISPLAY
    }
    
    # 设置缓存
    cache.set(cache_key, context, MAP_CACHE_TIMEOUT)
    return context


def pick_item(player, map_item_id):
    """玩家拾取物品（修复版）"""
    print(player.map.id)
    print(map_item_id)
    print("见简介啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊")
    ## 判断是否被捡走
    try:
        with transaction.atomic():
            # 重新获取并锁定物品（防止并发修改）
            locked_item = GameMapItem.objects.select_for_update().get(
                id=map_item_id,
            )
            print(locked_item.map_id)
            print(player.map_id)
            # 验证物品是否在当前地图
            if locked_item.map_id != player.map.id:
                return False, "物品不在当前地图"

            # 检查物品是否已被拾取
            if locked_item.picked_by is not None:
                return False, "物品已被其他玩家捡走"
            
            # 检查物品是否过期
            if locked_item.expire_time and locked_item.expire_time < timezone.now():
                return False, "物品已过期"
            
            # 添加物品到背包
            success, message = PlayerItem.add_item(player, locked_item.item_id, count=1)
            if not success:
                return False, message
            
            # 标记物品为已拾取
            locked_item.picked_by = player.id
            locked_item.save(update_fields=['picked_by'])
            
            # 清除地图缓存
            invalidate_map_cache(player.map_id)
            
            return True, f"成功拾取 {locked_item.item.name}"
    
    except GameMapItem.DoesNotExist:
        return False, "物品不存在或已被移除"
    except Exception as e:
        logger.exception(f"拾取物品异常：{e}")
        return False, "拾取物品失败，请稍后再试"

def drop_item(player, player_item_id, item_id):
    """
    玩家丢弃物品
    :param player: 玩家对象
    :param item_instance_id: 地图物品实例ID
    """
    # 验证玩家是否拥有该物品
    if not PlayerItem.objects.filter(
        player=player,
        id=player_item_id
    ).exists():
        return False
    
    try:
    # 只包装核心操作在事务中
        with transaction.atomic():
            # 调用优化后的移除方法
            success = PlayerItem.remove_item(player, player_item_id, count=1)
            
            if not success:
                return False
            
            # 创建地图物品 - 使用延迟创建优化
            GameMapItem.objects.create(
                item_id=item_id,
                map_id=player.map.id,  # 直接使用ID避免额外查询
                expire_time=timezone.now() + timedelta(minutes=10)
            )
            
        # 事务外清除缓存
        invalidate_map_cache(player.map.id)
        return True
    except Exception as e:
        # 记录错误日志
        logger.error(f"丢弃物品失败: {e}")
        print("丢弃物品失败")
        return False

def generate_action_links(map_id, player_id, context):
    """生成动作链接的加密cmd"""
    links = {}
    
    # 物品拾取链接
    for item in context.get('items', []):
        encrypted_cmd = ParamSecurity.generate_param(
            entity_type="item",
            sub_action="pick",
            params={
                'item_id': item.id,
                'player_id': player_id,
                'map_id': map_id
            },
            action="item"
        )
        links[f'pick_item_{item.id}'] = encrypted_cmd
    
    # NPC交互链接
    for npc in context.get('npcs', []):
        encrypted_cmd = ParamSecurity.generate_param(
            entity_type="npc",
            sub_action="interact",
            params={
                'npc_id': npc['id'],
                'player_id': player_id,
                'map_id': map_id
            },
            action="npc"
        )
        links[f'interact_npc_{npc["id"]}'] = encrypted_cmd
    
    # 怪物攻击链接
    for monster in context.get('monsters', []):
        encrypted_cmd = ParamSecurity.generate_param(
            entity_type="monster",
            sub_action="attack",
            params={
                'monster_id': monster['id'],
                'player_id': player_id,
                'map_id': map_id
            },
            action="monster"
        )
        links[f'attack_{monster["id"]}'] = encrypted_cmd
    
    # 刷新链接
    encrypted_cmd = ParamSecurity.generate_param(
        entity_type="map",
        sub_action="refresh",
        params={
            'player_id': player_id,
            'map_id': map_id
        },
        action="map"
    )
    links['refresh'] = encrypted_cmd
    
    # 商城链接
    encrypted_cmd = ParamSecurity.generate_param(
        entity_type="shop",
        sub_action="open",
        params={
            'player_id': player_id
        },
        action="shop"
    )
    links['shop'] = encrypted_cmd
    
    # 任务链接
    encrypted_cmd = ParamSecurity.generate_param(
        entity_type="mission",
        sub_action="list",
        params={
            'player_id': player_id
        },
        action="mission"
    )
    links['mission'] = encrypted_cmd
    
    # 更多物品链接
    encrypted_cmd = ParamSecurity.generate_param(
        entity_type="item",
        sub_action="list_more",
        params={
            'player_id': player_id,
            'map_id': map_id
        },
        action="item"
    )
    links['show_more_items'] = encrypted_cmd
    
    # 玩家查看链接
    for player in context.get('players', []):
        encrypted_cmd = ParamSecurity.generate_param(
            entity_type="player",
            sub_action="detail_player",
            params={
                'player_id': player.id
            },
            action="player"
        )
        links[f'view_player_{player.id}'] = encrypted_cmd
    
    return links

        # 生成分页导航的加密参数
def generate_page_param(entity, type_value, page_num,):
    object_type = entity + '_type'
    list_object = 'list_' + entity
    page_params = {
        object_type: type_value,
        "page": page_num,
    }

    return ParamSecurity.generate_param(
        entity_type=entity,
        sub_action=list_object,
        params=page_params,
        action=entity
    )

def use_heal_item(player_item, player):
    """使用恢复类药品"""
    # item = player_item.item
    heal_amount = player_item.hp
    
    need_hp = player.max_hp - player.current_hp
    if need_hp == 0:
        return False, "生命值已满，无需使用"

    if need_hp < heal_amount:
        add_hp = need_hp
    else:
        add_hp = heal_amount

    # 更新玩家生命值
    updated = Player.objects.filter(
        id=player.id,
    ).update(
        current_hp=player.current_hp + add_hp
        )
    
    player_item.remove_item(player, player_item.id, count=1)
    # 消耗物品

    return True, f"成功恢复生命值{add_hp}点"


def equip_item(player, player_item_id):
    """玩家装备物品"""
    try:
        with transaction.atomic():
            # 获取并锁定物品（防止并发修改）
            player_item = PlayerItem.objects.select_for_update().get(
                id=player_item_id,
                player=player,
                is_equipped=False
            )
            print(player_item.item.category)
            # 验证是否为装备
            if player_item.category != 1:
                return False, "只能装备武器或防具"
            
            position = player_item.item.equipment_post
            
            # 检查槽位是否被占用
            existing_equipment = PlayerEquipment.objects.filter(
                player=player, 
                position=position
            ).first()
            
            # 如果槽位已有装备，先卸下
            if existing_equipment:
                _, msg = unequip_item(player, position)
                if not _:
                    return False, f"无法替换装备: {msg}"
            
            # 装备新物品
            PlayerEquipment.objects.create(
                player=player,
                position=position,
                item=player_item
            )
            player_item.is_equipped = True
            player_item.save(update_fields=['is_equipped'])
            cache.delete(f'player_attrs_{player.id}')
            cache.delete(f'player_combat_{player.id}')
            return True, f"成功装备 {player_item.item.name}"
    
    except PlayerItem.DoesNotExist:
        return False, "物品不存在或不属于你"
    except Exception as e:
        logger.exception(f"装备物品异常：{e}")
        return False, "装备失败，请稍后再试"

def unequip_item(player, position):
    """玩家卸下装备"""
    print(position)
    print("玩家卸下装备")
    try:
        with transaction.atomic():
            # 获取并锁定装备槽位
            equipment = PlayerEquipment.objects.select_for_update().get(
                player=player,
                position=position
            )
            player_item = equipment.item
            
            # 更新物品状态
            player_item.is_equipped = False
            player_item.save(update_fields=['is_equipped'])
            
            # 删除装备槽记录
            equipment.delete()
            cache.delete(f'player_attrs_{player.id}')
            cache.delete(f'player_combat_{player.id}')
            return True, f"成功卸下 {player_item.item.name}"
    
    except PlayerEquipment.DoesNotExist:
        return False, "该位置没有装备"
    except Exception as e:
        logger.exception(f"卸下装备异常：{e}")
        return False, "卸下装备失败，请稍后再试"

def get_equipped_lists(player):
    """获取玩家已装备的物品列表"""
    equipment = PlayerEquipment.objects.filter(
        player=player
    ).select_related('item', 'item__item').order_by('position')
    
    return [
        {
            'position': e.get_position_display(),
            'position_id': e.position,
            'item_id': e.item.id,
            'item_name': e.item.item.name,
            'attributes': {
                'hp': e.item.hp,
                'attack': e.item.attack,
                'defense': e.item.defense,
                'minjie': e.item.minjie,
                'linghunli': e.item.linghunli
            },
            'cmd_params': ParamSecurity.generate_param(
                entity_type='item',
                sub_action='detail_item',
                params = {'player_item_id':e.item_id,'player_id':player.id},
                action='item'
            ),
        } for e in equipment
    ]

def get_equipped_items(player_id):
    """获取已装备物品列表"""
    return PlayerEquipment.objects.filter(
        player_id=player_id
    ).select_related('item', 'item__item').order_by('position')

def index(request):
    
    try:
        secure_params = request.secure_params
        # npc_id = request.secure_params.get('pk_get_into')
    except:
        pass
    
    user_id = request.session.get("user_id")
    user = request.session["username"]
    user_admin = request.session.get("user_admin")
    has_player = True



    
    if request.method == "GET":
        player = Player.objects.filter(user=user_id).first()
        params = user_id
        print(player)
        if player:
            # 已创建角色，进入游戏场景
            has_player = True
            params = player.id
            request.session["player_id"] = player.id
            request.session["player_name"] = player.name
            request.session["player"] = player
            # cache.set('player', player, timeout=300)
        else:
            # 未创建角色，进入角色创建页面
            has_player = False
            params = user_id
        print(has_player)
        
        
        # generate_param('item', 'equip', item.id, action='game')
        return render(request, 'index.html', {
            "admin_encrypted_param": ParamSecurity.generate_param("admin", "none", user_id, action="admin"),
            "player_encrypted_param": ParamSecurity.generate_param("player", "create", user_id, action="player"),
            "wap_encrypted_param": ParamSecurity.generate_param(
                entity_type="wap", 
                sub_action="none", 
                # params=params, 
                params={
                    'params': params,
                },
                action="wap"
            ),
            "player":player,
            "user": user,
            
            'has_player': has_player,
        })


def player_handler(request, params, sub_action):
    # 处理玩家相关的操作
    # start_time = time.perf_counter()
    print(params)
    print("$$$$$$$$$")
    if sub_action == 'create':
        # 处理创建角色的逻辑
        

        param_data = request.secure_params.get('cmd')
        print(f"player param_data: {param_data}")
        if not param_data:
            return render_error(request, "参数错误")
        entity = param_data['entity']
        sub_action = param_data['sub_action']
        params = param_data['params']

        create_param = ParamSecurity.generate_param(
            entity_type='player',
            sub_action='create',
            params=params,
            action='player'
        )


        if request.method == 'POST':
            # 处理表单提交
            print("处理表单提交")
            player_name = request.POST.get('player_name').strip()
            gender = request.POST.get('gender').strip()
            signature = request.POST.get('signature').strip()
            print(f"player_name: {player_name}")

            ### 校验字段

            if player_name:
                # 创建新角色
                if Player.objects.filter(name=player_name).exists():
                    messages.error(request, "该用户名已被注册，请更换用户名后重试！")
                    return render(request, 'create_player.html', {'create_param': create_param})

                player = Player.objects.create(user_id=params, name=player_name,gender=gender,signature=signature, map=get_default_map())
                request.session["player"] = player
                request.session["player_id"] = player.id
                chat_msg = ChatMessage.objects.create(
                    type_id=1,  # 系统消息类型
                    message=' 欢迎 <a href="/wap/?cmd={}">{}</a> 加入游戏！',
                    sender=player.id,
                    sender_name=player.name,
                )
                
                
                return redirect(reverse('wap') + f'?cmd={ParamSecurity.generate_param("wap", "none", player.id, action="wap")}')
            else:
                # 返回错误信息
                return render(request, 'create_player.html', {
                    'error': '角色名称不能为空',
                    'params': params,
                    'sub_action': sub_action,
                    
                    'create_param': create_param
                })
        
        
        # 如果是GET请求，渲染创建角色页面
        return render(request, 'create_player.html', {
            'create_param': create_param,
            
            'op_action': 'create_player',
            'wap_encrypted_param': ParamSecurity.generate_param(
                entity_type='wap',
                sub_action='none',
                params=params,
                action='wap'
            ),
        })
    elif sub_action == 'detail_player':
        # 处理查看角色的逻辑

        player = Player.objects.get(id=params.get("player_id"))
        if player.gang:
            gang_encrypted_param = ParamSecurity.generate_param(
                entity_type='gang',
                sub_action='detail_gang',
                params={"gang_id":player.gang.id},
                action='gang'
            )
        else:
            gang_encrypted_param = ''

        status = "在线" if player.is_online else "离线"

        equip_list = get_equipped_lists(player)
        
        print(equip_list)
        return render(request, 'player_status.html', {
            'player': player,
            'op_action': 'detail_player',
            'equip_list': equip_list,
            'wap_encrypted_param': ParamSecurity.generate_param(
                entity_type='wap',
                sub_action='none',
                params = {'player_id':player.id},
                action='wap'
            ),
            'gang_encrypted_param': gang_encrypted_param,
            'status':status
        })
    else:
        pass


# Create your views here.

def game_page(request):

    # page = get_object_or_404(GamePage, name=page_name)

    secure_params = request.secure_params.get('cmd')
    
    if not secure_params:
        # return JsonResponse({'error': '非法参数'})
        return redirect(reverse('error') + '?error=非法参数')

    page = GamePage.objects.get(id=1)
    
    # 获取当前玩家
    player_id = request.session.get('user_id', 1)
    player = User.objects.get(id=player_id)
    
    
    # 创建渲染上下文
    context = {
        'player': player,
        # 'location': location,
        # 'npc': npc,
        # 'item': item,
        'request': request
    }
    
    # 创建渲染器
    renderer = ComponentRenderer(context)
    print(renderer)
    # 渲染所有组件
    components_html = []
    for component in page.components.all():
        components_html.append(renderer.render(component))
    
        # 添加页面级自定义CSS和JS
    page_css = f'<style>{page.custom_css}</style>' if page.custom_css else ''
    page_js = f'<script>{page.custom_js}</script>' if page.custom_js else ''
    print(components_html)
    return render(request, 'test.html', {
        'page': page,
        'components_html': components_html,
        'page_css': page_css,
        'page_js': page_js
    })


def wap(request):
    # start_time = time.perf_counter()

    param_data = request.secure_params.get('cmd')
    if not param_data:
        error_url = '/login/'
        return render_error(request, "你已长时间未操作，请重新登录！",{'error_url':error_url})
    print(f"post param_data: {param_data}")
    entity = param_data['entity']
    sub_action = param_data['sub_action']
    params = param_data.get('params')



    try:
        # 获取玩家ID而非整个对象
        player_id = request.session["player_id"]
        # 从数据库重新获取玩家对象
        player = Player.objects.get(id=player_id)
        print(player.total_attributes())
        
        if player.is_online == False:
            player.update_activity()
    except (KeyError, Player.DoesNotExist):
        messages.error(request, "你已长时间未操作，请重新登录！")
        return redirect(reverse('error'))
    
    # print(player.total_attributes())

    new_map_id = params.get("map_id")
    # # 记录旧地图ID
    old_map_id = player.map.id
    
    # # 验证新地图是否存在
    if new_map_id:
        # 确保地图ID有效
        try:
            new_map = GameMap.objects.get(id=new_map_id)
        except GameMap.DoesNotExist:
            new_map_id = old_map_id  # 无效则保持原地
    
    # 仅当位置变化时才更新
    if new_map_id and new_map_id != old_map_id:
        player.map_id = new_map_id
        # player.last_position_update = timezone.now()
        player.save(update_fields=['map_id'])
        
        # 清除相关缓存
        invalidate_map_cache(old_map_id)  # 清除旧地图缓存
        invalidate_map_cache(new_map_id)  # 清除新地图缓存
        invalidate_player_cache(player.id)  # 清除玩家缓存

    print("当前所在地图" + player.map.name)
    print("当前所在地图" + str(player.map.id))
    request.session["player"] = player
    # print("target_map:"+ str(new_map_id))
    print(entity)
    print(params)
    # context['direction_links'] = generate_direction_links(
    #     context['exits'], player.id
    # )
    context = get_map_context(player.map.id, player.id)
    # get_map = get_map_context(player.map.id, player.id)  
    context['direction_links'] = generate_direction_links(
        context['exits'], player.id
    )  

    # context['action_links'] = generate_action_links(
    #     map_id, player.id, context
    # )
    
    # action_links = generate_action_links(
    #     map_id, player.id, context
    # )

    test_items = GameMapItem.objects.filter(
        map_id=1,
        expire_time__gt=timezone.now(),
        picked_by__isnull=True
    ).select_related('item').only(
        'id', 'item__id', 'item__name', 'count'
    )[:MAX_ITEMS_DISPLAY]
    print(test_items)

    exits = context['exits']
    npcs = context.get('npcs', [])
    items = context['items']
    print(npcs)
    print("*****************************")
    players = context.get('players', [])
    monsters = context.get('monsters', [])
    print(items)





    if entity == 'wap' and sub_action == 'none':
        # 处理无操作的情况
        try:
            player_id = request.session["player_id"]
        except:
            messages.error(request, "会话过期，请重新登录")
            error_url = '/login/'
            return redirect(reverse('error'))
        print(f"player_id is " + str(player_id))
        player = Player.objects.filter(id=player_id).first()
    
        ### 聊天消息
        chatlists = ChatMessage.objects.filter(Q(type_id=1) | Q(type_id=2)).order_by('-created_at')[:4]
        chat_list = []
        for chat in chatlists:
            player_encrypted_param = ParamSecurity.generate_param(
                    entity_type='player',
                    sub_action='detail_player',
                    # params=chat.sender,
                    params = {
                        'player_id':chat.sender
                    },
                    action='player',
                    # one_time=True,
            )

            if chat.type_id == 1:
            # 系统消息类型，替换链接
            
                # player_encrypted_param = ParamSecurity.generate_param(
                #     entity_type='player',
                #     sub_action='view',
                #     params=chat.sender,
                #     action='player',
                #     # one_time=True,
                # )

                # chat_message = chat.message.format(
                #         player_encrypted_param, chat.sender_name, 
                # )
                chat_message = "[系统]" + chat.message.format(
                                player_encrypted_param, chat.sender_name, 
                        ) + "(" + chat.created_at.strftime('%Y-%m-%d %H:%M:%S') + ")<br>"        
                print(f"chat message: {chat.message}")
            elif chat.type_id == 2:


                chat_message = '[世界] <a href="/wap/?cmd=' + player_encrypted_param + '">' + chat.sender_name + '</a>:' + chat.message + "(" + chat.created_at.strftime('%Y-%m-%d %H:%M:%S') + ")<br>"
            # elif chat.type_id
            else:
                chat_message = ""
            print(chat_message)
            chat_list.append(chat_message)
        ### 地图
        # 获取当前地图  
        map = GameMap.objects.get(id=player.map.id)

        # 帮会

        # 
        # 
        return render(request, 'wap.html', {
            # 
            'chatlists': chatlists,
            'chat_list': chat_list,
            'player_encrypted_param': ParamSecurity.generate_param(
                entity_type='player',
                sub_action='detail_player',
                params = {'player_id':player.id},
                action='player'
            ),
            'wap_encrypted_param': ParamSecurity.generate_param(
                entity_type='wap',
                sub_action='none',
                params = {'player_id':player.id},
                action='wap'
            ),
            'exits': exits,
            'map': map,
            'npcs':npcs,
            'items':items,
            'map_players': players,
            'monsters': monsters,
            'player': player,
            'chat_encrypted_param': ParamSecurity.generate_param(entity_type='chat',sub_action='list_chat',params = {'chat_type':2},action='chat'),
            'gang_encrypted_param': ParamSecurity.generate_param(entity_type='gang',sub_action='list_gang',params = {'gang_type':1},action='gang'),
            'team_encrypted_param': ParamSecurity.generate_param(entity_type='team',sub_action='list_team',params = {'team_type':1},action='team'),
            'skill_encrypted_param': ParamSecurity.generate_param(entity_type='skill',sub_action='list_skill',params = {'skill_id':1},action='skill'),
            'item_encrypted_param': ParamSecurity.generate_param(entity_type='item',sub_action='list_item',params = {'item_type':1},action='item'),
        })
    elif entity == 'wap' and sub_action == 'move':
         return movemap_handler(request, params, sub_action)
    elif entity == 'player':
        # 处理主页面的情况
        return player_handler(request, params, sub_action)
    elif entity == 'chat':
        # 处理聊天页面
        return chat_handler(request, params, sub_action)
    elif entity == 'gang':
        # 处理聊天页面
        return gang_handler(request, params, sub_action)
    elif entity == 'team':
        # 处理聊天页面
        return team_handler(request, params, sub_action)
    elif entity == 'gamenpc':
        return gamenpc_handler(request, params, sub_action)
    elif entity == 'attack':
        return attack_handler(request, params, sub_action)
    elif entity == 'skill':
        return skill_handler(request, params, sub_action)
    elif entity == 'item':
        return item_handler(request, params, sub_action)
    else:

        
        
        messages.error(request, "未知操作")
        return render(request, 'error.html', )

def render_error(request, message, status=400):
    """安全渲染错误页面"""
    response = render(request, 'error.html', {
        'error_message': message,
        'status_code': status
    })
    response.status_code = status
    return response


def item_handler(request, params, sub_action):
    map_item_id = params.get("map_item_id")
    # print("item_id")
    player = request.session.get("player")
    
    if sub_action == "get_item":
        
        # item = Item.objects.get(id=item_id)
        # print(item)
        # result = pick_item(player,item=item)
        success, message = pick_item(player, map_item_id)
        if success:
            # messages.success(request, "成功获得物品" + item.name + "x1")
            messages.success(request, message)
        else:
            messages.error(request, message)
        wap_encrypted_param = ParamSecurity.generate_param(
            entity_type="wap", 
            sub_action="none", 
            params=params, 
            action="wap"
        )
        print("捡到了aaaaaaaaaaaaaaaaaa")
        wap_url = "/wap/?cmd=" + wap_encrypted_param
        return redirect(wap_url)
    elif sub_action == "list_item":


        item_type = params.get("item_type",1)

        page = int(params.get("page", 1))
        PAGE_SIZE = 10  # 每页消息数量

        # 基础查询
        base_query = PlayerItem.objects.filter(
            player_id=player.id,
            category=item_type
        ).select_related('item').only(
            'id', 'count', 'is_bound', 'is_equipped',
            'item__id', 'item__name', 'item__category'
        )

        
        # 计算分页
        total_count = base_query.count()
        total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE
        
        # 确保页码在有效范围内
        page = max(1, min(page, total_pages))
        
        # 获取当前页数据
        offset = (page - 1) * PAGE_SIZE
        item_lists = base_query.order_by('-id')[offset:offset + PAGE_SIZE]
        
        start_index = (page - 1) * PAGE_SIZE

        # 格式化消息
        item_list = []
        for i in item_lists:
            print(i.item.name)
            item_params = ParamSecurity.generate_param(
                entity_type='item',
                sub_action='detail_item',
                params = {'item_id':i.item_id,'player_id':player.id,'player_item_id':i.id},
                action='item'
            ),
            html_context = '<a href="/wap/?cmd={}">{}</a> x{}'.format(item_params[0],i.item.name,i.count)
            item_list.append(html_context)
        
    
        # 创建分页导航
        pagination = []
        if page > 1:
            shouye_params = generate_page_param(entity='item', type_value=item_type, page_num=1)
            shangyiye_params = generate_page_param(entity='item', type_value=item_type, page_num=(-1))
            pagination.append(f'<a href="/wap/?cmd={shouye_params}">首页</a>')
            pagination.append(f'<a href="/wap/?cmd={shangyiye_params}">上一页</a>')
        
        # 显示当前页和总页数
        pagination.append(f'第{page}/{total_pages}页')
        
        if page < total_pages:
            xiayiye_params = generate_page_param(entity='item', type_value=item_type, page_num=page+1)
            weiye_params = generate_page_param(entity='item', type_value=item_type, page_num=total_pages)
            pagination.append(f'<a href="/wap/?cmd={xiayiye_params}">下一页</a>')
            pagination.append(f'<a href="/wap/?cmd={weiye_params}">尾页</a>')

        return render(request, 'object_rank.html',{
            'item_list': item_list,
            'op_action': 'list_item',
            'wap_encrypted_param': ParamSecurity.generate_param(
                entity_type='wap',
                sub_action='none',
                params = {'player_id':player.id},
                action='wap'
            ),
            'pagination':" ".join(pagination),
            'start_index': start_index,
            'item_type': item_type,
            'zhuangbei_params': ParamSecurity.generate_param(
                entity_type='item',
                sub_action='list_item',
                params = {'item_type':1},
                action='item'
            ),
            'yaopin_params': ParamSecurity.generate_param(
                entity_type='item',
                sub_action='list_item',
                params = {'item_type':2},
                action='item'
            ),
            'wupin_params': ParamSecurity.generate_param(
                entity_type='item',
                sub_action='list_item',
                params = {'item_type':3},
                action='item'
            ),
            'qita_params': ParamSecurity.generate_param(
                entity_type='item',
                sub_action='list_item',
                params = {'item_type':6},
                action='item'
            ),
            'now_rongliang': player.get_bag_weight(),
            'max_rongliang': player.bag_capacity,
            'money': player.money
        })






    elif sub_action == "detail_item":
        item_id = params.get("item_id")
        player_id = params.get("player_id")
        player_item_id = params.get("player_item_id")
        action_link = ''
        print(item_id)
        print(player_id)
        print("#############detail########################")
        has_item = False
        if player_item_id:
            playeritem = PlayerItem.objects.filter(
                player_id=player_id,
                id=player_item_id  
            ).select_related('item').first()
            unequip_link = None
            equip_link = None
            if playeritem.category == 1:
                equip_params = ParamSecurity.generate_param(
                    entity_type='item',
                    sub_action='equip_item',
                    params = {'player_id':player.id,'player_item_id':playeritem.id,'item_id':playeritem.item_id},
                    action='item'
                ),
                chuandai_link = '<a href="/wap/?cmd={}">穿戴</a>'.format(equip_params[0])
                if playeritem.is_equipped == 1:
                    unequip_params = ParamSecurity.generate_param(
                        entity_type='item',
                        sub_action='unequip_item',
                        params = {'player_id':player.id, 'item_id':playeritem.item_id, 'position':playeritem.equipment_post},
                        action='item'
                    ),
                    unequip_link = '<a href="/wap/?cmd={}">卸下</a>'.format(unequip_params[0])
                

            elif playeritem.category == 2:
                use_params = ParamSecurity.generate_param(
                    entity_type='item',
                    sub_action='use_item',
                    params = {'player_id':player.id,'player_item_id':playeritem.id,'item_id':playeritem.item_id},
                    action='item'
                ),
                action_link = '<a href="/wap/?cmd={}">使用</a>'.format(use_params[0])
            has_item = True
            himself = True
            return render(request, 'gang_detail.html',{
                'playeritem': playeritem,
                'op_action': 'detail_item',
                'equip_link': equip_link,
                'unequip_link': unequip_link,
                'use_link':action_link,
                'himself': himself,
                'has_item': has_item,
                'wap_encrypted_param': ParamSecurity.generate_param(
                    entity_type='wap',
                    sub_action='none',
                    params = {'player_id':player.id},
                    action='wap'
                ),
                'drop_encrypted_param': ParamSecurity.generate_param(
                    entity_type='item',
                    sub_action='drop_item',
                    params = {'player_item_id':playeritem.id,'item_id':playeritem.item.id},
                    action='item'
                ),
            })
        else:
            item = Item.objects.filter(
                id=item_id  
            ).first()
            himself = False
            return render(request, 'gang_detail.html',{
                'item': item,
                'op_action': 'detail_item',
                'equip_link': None,
                'unequip_link': None,
                'use_link':None,
                'himself': himself,
                'has_item': has_item,
                'wap_encrypted_param': ParamSecurity.generate_param(
                    entity_type='wap',
                    sub_action='none',
                    params = {'player_id':player.id},
                    action='wap'
                ),
                'drop_encrypted_param': None,
            })



    elif sub_action == "equip_item":
        player_item_id = params.get("player_item_id")
        item_id = params.get("item_id")
        success, message = equip_item(player,player_item_id)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        wap_encrypted_param = ParamSecurity.generate_param(
            entity_type="item", 
            sub_action="detail_item", 
            params={'item_id':item_id,'player_item_id':player_item_id, 'player_id':player.id}, 
            action="item"
        )
        equip_list = get_equipped_lists(player)
        print(equip_list)
        wap_url = "/wap/?cmd=" + wap_encrypted_param
        return redirect(wap_url)

    elif sub_action == "use_item":
        player_item_id = params.get("player_item_id")
        item_id = params.get("item_id")
        # player_id = params.get("player_id")



        # 判断有没有物品
        player_item = PlayerItem.objects.filter(player=player,id=player_item_id).first()
        # if player_item is None:
            ## 没有物品
        success, message = use_heal_item(player_item, player)
        if player_item.count > 1:
            wap_encrypted_param = ParamSecurity.generate_param(
                entity_type="item", 
                sub_action="detail_item", 
                params={'item_id':item_id,'player_item_id':player_item_id, 'player_id':player.id}, 
                action="item"
            )
            messages.success(request, message)
        else:
            if success:
                messages.success(request, message)
                wap_encrypted_param = ParamSecurity.generate_param(
                    entity_type="item", 
                    sub_action="list_item", 
                    params={'item_type':1}, 
                    action="item"
                )  
            else:
                messages.success(request, message)
                wap_encrypted_param = ParamSecurity.generate_param(
                    entity_type="item", 
                    sub_action="detail_item", 
                    params={'item_id':item_id,'player_item_id':player_item_id, 'player_id':player.id}, 
                    action="item"
                )
        wap_url = "/wap/?cmd=" + wap_encrypted_param
        return redirect(wap_url)


    elif sub_action == "unequip_item":
        '''卸下装备'''
        position = params.get("position")
        player_item_id = params.get("player_item_id")
        item_id = params.get("item_id")

        print(item_id)
        success, message = unequip_item(player,position)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        wap_encrypted_param = ParamSecurity.generate_param(
            entity_type="item", 
            sub_action="detail_item", 
            params={'item_id':item_id,'player_id':player.id}, 
            action="item"
        )
        equip_list = get_equipped_lists(player)
        print(equip_list)
        wap_url = "/wap/?cmd=" + wap_encrypted_param
        return redirect(wap_url)

    elif sub_action == "drop_item":
        item_id = params.get("item_id")
        player_item_id = params.get("player_item_id")
        # item = Item.objects.get(id=item_id)
        drop_item(player,player_item_id=player_item_id,item_id=item_id)

        messages.success(request, "已丢弃物品")
        wap_encrypted_param = ParamSecurity.generate_param(
            entity_type="item", 
            sub_action="list_item", 
            params={'player_id':player.id}, 
            action="item"
        )
        print("捡到了aaaaaaaaaaaaaaaaaa")
        wap_url = "/wap/?cmd=" + wap_encrypted_param
        return redirect(wap_url)
    else:
        pass
    




def skill_handler(request, params, sub_action):

    player = request.session.get("player",[])
    if sub_action == "list_skill":
        skills = PlayerSkill.objects.filter(player=player)
        skill_list = []
        for skill in skills:
            skill_encrypted_param = ParamSecurity.generate_param(
                entity_type='skill',
                sub_action='detail_skill',
                params = {'skill_id':skill.skill.id},
                action='skill'
            )
            html_context = '<a href="/wap/?cmd={}">{}</a>'.format(skill_encrypted_param,skill.skill)
            # print(html_context)
            skill_list.append(html_context)
        # print(skills)
        return render(request, 'object_rank.html',{
            'skill_list':skill_list,
            'op_action': 'list_skill',
            'wap_encrypted_param': ParamSecurity.generate_param(
                entity_type='wap',
                sub_action='none',
                params = {'player_id':player.id},
                action='wap'
            ),
        })
    elif sub_action == 'detail_skill':
        skill_id = params.get("skill_id")
        print("skill id" + str(skill_id))
        skill = PlayerSkill.objects.filter(player=player,skill_id=skill_id).first()
        print(skill)
        return render(request, 'gang_detail.html',{
            'skill':skill,
            'op_action': 'detail_skill',
            'wap_encrypted_param': ParamSecurity.generate_param(
                entity_type='wap',
                sub_action='none',
                params = {'player_id':player.id},
                action='wap'
            ),
        })

def attack_handler(request, params, sub_action):
    
    npc = params.get("npc")
    print("***********npc*********")
    print(npc)
    npc_id = params.get("npc_id")
    player = request.session.get("player")
    player_id = player.id
    skill_id = params.get("skill_id")
    print("npc_id")
    print(npc_id)

    slots_data = QuickSlot.get_player_quick_slots(player.id)
    player_skills = get_player_skills(player.id)
    print(player_skills)

    for skill in player_skills:
        cmd_params = ParamSecurity.generate_param(
            entity_type="attack", 
            sub_action="attack_monster", 
            params={"skill_id":skill["id"],"npc_id":npc_id,"npc":npc,}, 
            action="attack"
            )
        skill['cmd_params'] = cmd_params


    if sub_action == "attack_monster":
        try:
            attack_result = attack_monster(player_id, npc_id, skill_id)

            # 更新session中的玩家状态
            request.session['player'] = Player.objects.get(id=player_id)
            
            # 如果是玩家死亡，重定向到安全区
            if attack_result['player_died']:
                messages.error(request, "你竟然被怪物击败了！已被传送到安全区。")
                
                # 生成安全区的加密参数
                safe_area_param = ParamSecurity.generate_param(
                    entity_type='wap',
                    sub_action='none',
                    params={'map_id': 1},
                    action='wap'
                )
                safe_area_url = f"/wap/?cmd={safe_area_param}"
                return redirect(safe_area_url)

            # 如果是击杀，获取奖励信息
            reward_info = None
            if attack_result['killed']:
                # reward_info = handle_kill_reward(player_id, GameNPC.objects.get(id=npc_id))
                reward_info = attack_result.get('reward_info')
            
            request.session['player'].current_hp = attack_result['player_current_hp']

            print("啥啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊")
            context = {
                'npc': npc,
                'op_action': 'attack_monster',
                'player': request.session['player'],  # 使用更新后的玩家状态
                'player_skills': player_skills,
                'status': 'success',
                'attack_result': attack_result,
                'reward_info': reward_info,
                'wap_encrypted_param': ParamSecurity.generate_param(
                    entity_type='wap',
                    sub_action='none',
                    params={'player_id': player.id},
                    action='wap'
                ),
            }

            return render(request, 'monster_attack.html',context)

        except Exception as e:

            messages.error(request, str(e))

            wap_encrypted_param = ParamSecurity.generate_param(
                entity_type="attack", 
                sub_action="attack_monster", 
                params={"skill_id":skill_id,"npc_id":npc_id,"npc":npc,}, 
                action="attack"
            )
            wap_url = "/wap/?cmd=" + wap_encrypted_param
            return redirect(wap_url)


    elif sub_action == "attack_boss":
        pass
    elif sub_action == "attack":

        return render(request, 'monster_attack.html',{
            'npc':npc,
            'op_action': 'attack_monster',
            'player':player,
            'player_skills': player_skills,
            'wap_encrypted_param': ParamSecurity.generate_param(
                    entity_type='wap',
                    sub_action='none',
                    params = {'player_id':player.id},
                    action='wap'
                ),
            
        })
    else:
        pass

def gamenpc_handler(request, params, sub_action):
    try:
        player = request.session["player"]
        # player.update_activity()
    except:
        messages.error(request, "你已长时间未操作，请重新登录！")
        return redirect(reverse('error'))

    # 获取当前地图上下文（从缓存中）
    # context = get_map_context(player.map.id, player.id)
    
    npc_id = params.get("npc_id")

    # 查找NPC
    # npc = next((n for n in context['npcs'] if n['id'] == npc_id), None)
    #     level = models.IntegerField(default=1, verbose_name="等级")   # 通用属性
    # # map = models.ForeignKey('GameMap', null=True, blank=True, on_delete=models.CASCADE, verbose_name="地图")  # 通用属性
    # # map_id = models.PositiveIntegerField(null=True, blank=True, db_index=True, verbose_name="地图")
    
    # # ---- 怪物专属字段 (nullable) ----
    # hp = models.IntegerField(null=True, blank=True, verbose_name="生命值")
    # attack = models.IntegerField(null=True, blank=True, verbose_name="攻击力")
    # defense = models.IntegerField(null=True, blank=True, verbose_name="防御力")
    # exp_reward = models.IntegerField(default=0, verbose_name="经验奖励")
    # gold_reward = models.IntegerField(default=0, verbose_name="金钱奖励")
    # drop_items = models.JSONField(null=True, blank=True, verbose_name="物品掉落")  # 掉落物品JSON
    # is_boss = models.BooleanField(default=False, verbose_name="是否BOSS") 
    # if not npc:
    #     # 如果缓存中没有，从数据库查询（很少发生）
    #     try:
    #         npc_obj = GameNPC.objects.get(id=npc_id)

    #         npc = {
    #             'id': npc_obj.id,
    #             'name': npc_obj.name,
    #             'type': npc_obj.npc_type,
    #             'description': npc_obj.description,
    #             'dialogue': npc_obj.dialogue,
    #             'hp': npc_obj.hp,
    #             'level': npc_obj.level,
    #             'attack': npc_obj.attack,
    #             'defense': npc_obj.defense,
    #             'exp_reward': npc_obj.exp_reward,
    #             'gold_reward': npc_obj.gold_reward,
                
    #         }
    #     except GameNPC.DoesNotExist:
    #         return redirect('game:map_view')
    # print(npc["name"])
    try:
        npc = get_npc_info(npc_id)

        drop_info = npc["drop_info"]
        if drop_info:
            for item in drop_info:
                full_params = {
                    'item_id': item['item_id'],
                    'player_id': player.id,
                    'player_item_id': None
                }
                print(f"item_id{item['item_id']}")
                print(f"item_id{player.id}")
                # 保留原始参数，添加玩家ID
                item['item_params'] = ParamSecurity.generate_param(
                    entity_type="item", 
                    sub_action="detail_item", 
                    params=full_params,
                    action="item"
                )

    except GameNPC.DoesNotExist:
        messages.error(request, "NPC 不存在！")
        return redirect('game:map_view')
    print(npc)

    print(drop_info)
    return render(request, 'player_status.html', {
        'npc':npc,
        'op_action': 'npc',
        'drop_info': drop_info,
        'wap_encrypted_param': ParamSecurity.generate_param(
            entity_type='wap',
            sub_action='none',
            params = {'player_id':player.id},
            action='wap'
        ),
        'attack_encrypted_param': ParamSecurity.generate_param(
            entity_type='attack',
            sub_action='attack',
            params = {'player_id':player.id,'npc_id':npc["id"],"npc":npc},
            action='attack'
        ),
        })

def movemap_handler(request, params, sub_action):
    """
    处理地图相关命令
    :param request: HTTP请求
    :param player: 当前玩家对象
    :return: 地图上下文
    """
    # param_data = request.GET.get('cmd', '').lower()
    player = request.session.get("player")
    # map_id = player.map.id
    # print(param_data)
    print("(((((((((())))))))))")
    # entity = param_data['entity']
    # sub_action = param_data['sub_action']
    # params = param_data['params']
    map_id = params.get("map_id")

    # 方向移动处理
    # if cmd in ['north', 'south', 'east', 'west']:
    if sub_action == "move":
        try:
            current_map = GameMap.objects.only(
                'north_id', 'south_id', 'east_id', 'west_id'
            ).get(id=player.map.id)
        except GameMap.DoesNotExist:
            return get_map_context(map_id, player.id)
        
        # 获取目标地图ID
        # next_map_id = getattr(current_map, f"id")
        next_map_id = map_id
        
        if next_map_id:
            # 更新玩家位置
            player.map.id = next_map_id
            player.save(update_fields=['map'])
            
            # 清除缓存
            invalidate_map_cache(map_id)  # 清除旧地图缓存
            invalidate_map_cache(next_map_id)  # 清除新地图缓存
            
            map_id = next_map_id
    
    
    # return get_map_context(map_id, player.id)
    get_map_context(map_id, player.id)
    # messages.success(request, "已丢弃物品")
    wap_encrypted_param = ParamSecurity.generate_param(
        entity_type="wap", 
        sub_action="none", 
        params={'player_id':player.id}, 
        action="wap"
    )
    wap_url = "/wap/?cmd=" + wap_encrypted_param
    return redirect(wap_url)


def team_handler(request, params, sub_action):

    param_data = request.secure_params.get('cmd')
    if not param_data:
        return render_error(request, "参数错误")
    entity = param_data['entity']
    sub_action = param_data['sub_action']
    params = param_data['params']

    create_param = ParamSecurity.generate_param(
        entity_type='team',
        sub_action='create_team',
        params=params,
        action='team'
    )
    wap_encrypted_param = ParamSecurity.generate_param(
        entity_type="wap", 
        sub_action="none", 
        params=params, 
        action="wap"
    )
    ## 判断是否已加入队伍
    player = request.session["player"]
    is_onteam = TeamMember.objects.filter(player=player).exists()


    if sub_action == 'create_team':


        
        

        return render(request, 'create_player.html', {
            'create_param': create_param,
            
            'op_action': 'create_team',
            "wap_encrypted_param": wap_encrypted_param,
            # 'create_param': create_param,
            # 'gang_list': gang_list,
            'comfirm_encrypted_param': ParamSecurity.generate_param(
                entity_type='team',
                sub_action='confirm_create_team',
                params=params,
                action='team',
            ),
        })

    elif sub_action == 'confirm_create_team':
            # gang_name = request.POST.get('team_name').strip()
            # gang_zongzhi = request.POST.get('gang_zongzhi').strip()
            # if is_onteam:
                # 创建新帮会
            player_name = player.name
            team_name = player_name + '的队伍'
            if Team.objects.filter(name=team_name).exists():
                messages.error(request, "该队伍名称已存在，请更换名称后重试！")

                
                
                return render(request, 'create_player.html', {
                    'create_param': create_param,
                    "wap_encrypted_param": wap_encrypted_param,
                    'op_action': 'create_team',
                    
                    })
            else:
                team = Team.objects.create(leader=player, name=team_name)
                TeamMember.objects.create(team=team, is_leader=True, player=player)
    

                
                
                # 如果是GET请求，渲染创建角色页面
                return render(request, 'gang_detail.html', {
                    # 'create_param': create_param,
                    
                    "wap_encrypted_param": wap_encrypted_param,
                    'team':team,
                    'op_action': 'detail_team',
                    'is_onteam': True,
                    "breakteam_encrypted_param": ParamSecurity.generate_param(
                        entity_type="team", 
                        sub_action="break_team", 
                        params=team.id, 
                        action="team"
                    )


                })
    elif sub_action == 'list_team':


        try:
            # 假设你有TeamMember模型
            print("假设你有TeamMember模型")
            team_member = TeamMember.objects.get(player_id=player.id)
            current_team = team_member.team.id
            # print("currteam" + str(current_team.id))
            is_onteam = True
        except TeamMember.DoesNotExist:
            is_onteam = False
            current_team = 1


        get_team_list = Team.objects.all()[:10]
        team_list = []
        for team in get_team_list:
            team_encrypted_param = ParamSecurity.generate_param(
                entity_type="team", 
                sub_action="detail_team", 
                params={'team_id':team.id}, 
                action="team"
            )
            jointeam_encrypted_param = ParamSecurity.generate_param(
                entity_type="team", 
                sub_action="join_team", 
                params={'team_id':team.id}, 
                action="team"
            )


            context = '<a href="/wap/?cmd={}">{}</a>（{}/{}） '.format(
                team_encrypted_param,
                team.name,
                team.member_count,
                team.max_size,
            )
            if is_onteam:
                join_link = '[<a>加入</a>]</p>'
            else:
                join_link = '[<a href="/wap/?cmd={}">加入</a>]</p>'.format(jointeam_encrypted_param)

            context += join_link
            
            team_list.append(context)
        print(team_list)

        
        
        return render(request, 'object_rank.html', {
            'create_param': create_param,
            
            'op_action': 'list_team',
            "wap_encrypted_param": wap_encrypted_param,
            'team_list': team_list,
            'is_onteam': is_onteam,
            'myteam_encrypted_param': ParamSecurity.generate_param(
                entity_type="team", 
                sub_action="detail_team", 
                params={'team_id':current_team}, 
                action="team"
            )

        })

    elif sub_action == 'detail_team':
        team_id = params.get("team_id")
        team = Team.objects.get(id=team_id)
        print(player)
        print(team.leader)
        if team.leader == player:
            print("=========")

        teamleader_encrypted_param = ParamSecurity.generate_param(
            entity_type="player", 
            sub_action="detail_player", 
            params={'player_id':team.leader.id}, 
            action="player"
        )

        is_onteam = TeamMember.objects.filter(team=team_id, player=player).exists()
        member_list = []
        if team.member_count > 1:
            get_member_list = team.get_all_members_info()
            
            for member in get_member_list:
                player_encrypted_param = ParamSecurity.generate_param(
                    entity_type="player", 
                    sub_action="detail_player", 
                    params={'player_id':member['id']}, 
                    action="player"
                )
                removeteam_encrypted_param = ParamSecurity.generate_param(
                    entity_type="team", 
                    sub_action="remove_team", 
                    params={'player_id':member["id"],'team_id':team.id}, 
                    action="team"
                )
                if team.leader == player: 
                    context = '<a href="/wap/?cmd={}">{}</a> [在线] <a href="/wap/?cmd={}">踢出</a>'.format(
                        player_encrypted_param,
                        member['name'],
                        removeteam_encrypted_param,
                    )
                else:
                    context = '<a href="/wap/?cmd={}">{}</a>[在线]'.format(
                        player_encrypted_param,
                        member["name"],
                    )
                member_list.append(context)
        else:
            pass

        print(member_list)
        print(is_onteam)
        
        
        return render(request, 'gang_detail.html', {
            # 'create_param': create_param,
            
            'op_action': 'detail_team',
            "wap_encrypted_param": wap_encrypted_param,
            # 'create_param': create_param,
            # 'gang_list': gang_list,
            'is_onteam': is_onteam,
            'team':team,
            'player':player,
            "breakteam_encrypted_param": ParamSecurity.generate_param(
                entity_type="team", 
                sub_action="break_team", 
                params={'team_id':team.id,'player_id':player.id}, 
                action="team"
            ),
            'member_list': member_list,
            'teamleader_encrypted_param': teamleader_encrypted_param
        })
    elif sub_action == 'break_team':
        team_id = params.get("team_id")
        player_id = params.get("player_id")
        if player_id == player.id:

            team = Team.objects.get(id=team_id)
            # player = request
            team.remove_member(player)
            messages.success(request,"退出队伍成功")
            is_onteam = False


        get_team_list = Team.objects.all()[:10]
        team_list = []
        for team in get_team_list:
            team_encrypted_param = ParamSecurity.generate_param(
                entity_type="team", 
                sub_action="detail_team", 
                params=team.id, 
                action="team"
            )
            jointeam_encrypted_param = ParamSecurity.generate_param(
                entity_type="team", 
                sub_action="join_team", 
                params=team.id, 
                action="team"
            )
            context = '<p><a href="/wap/?cmd={}">{}</a>（{}/{}） [<a href="/wap/?cmd={}">加入</a>]</p>'.format(
                team_encrypted_param,
                team.name,
                team.member_count,
                team.max_size,
                jointeam_encrypted_param
            )
            team_list.append(context)


        
        
        return redirect(reverse('wap') + f'?cmd={ParamSecurity.generate_param("team", "list_team", {}, action="team")}')


    elif sub_action == 'join_team':
        team_id = params.get("team_id")
        
        team = Team.objects.get(id=team_id)
        team.add_member(player)
        # player = request
        # team.remove_member(player)
        messages.success(request,"加入队伍成功")
        is_onteam = True
        
        

        return redirect(reverse('wap') + f'?cmd={ParamSecurity.generate_param("team", "list_team", {}, action="team")}')

    elif sub_action == 'remove_team':
        team_id = params.get("team_id")
        player_id = params.get("player_id")
        
        try:
            # 使用事务确保操作原子性
            with transaction.atomic():
                # 一次性获取所有必要对象并锁定记录
                team_member = TeamMember.objects.select_for_update().select_related(
                    'team', 'player'
                ).get(
                    team_id=team_id,
                    player_id=player_id
                )
                
                team = team_member.team
                player = team_member.player
                
                # 直接使用获取的team_member对象进行删除操作
                is_leader = team_member.is_leader
                team_member.delete()
                
                # 处理队长变更逻辑
                if is_leader:
                    # 使用更高效的查询查找新队长
                    new_leader_member = team.members.order_by('join_time').first()
                    if new_leader_member:
                        new_leader_member.is_leader = True
                        new_leader_member.save()
                        team.leader = new_leader_member.player
                        team.save()
                    else:
                        # 队伍为空，删除队伍
                        team.delete()
                        team = None
        
            messages.success(request, "已成功踢出队员")
        
        except TeamMember.DoesNotExist:
            messages.error(request, "玩家不在该队伍中")
            return redirect(reverse('wap') + '?cmd=team_list')
        
        # 处理重定向
        if team:  # 队伍仍然存在
            redirect_params = {'team_id': team.id}
        else:  # 队伍已删除
            redirect_params = {}  # 重定向到队伍列表页
        
        return redirect(
            reverse('wap') + 
            f'?cmd={ParamSecurity.generate_param("team", "detail_team", redirect_params, action="team")}'
        )


    else:

        return render(request, 'object_rank.html', {
            'create_param': create_param,
            
            'op_action': 'list_team',
            "wap_encrypted_param": wap_encrypted_param,
            # 'create_param': create_param,
            # 'gang_list': gang_list,
            'comfirm_encrypted_param': ParamSecurity.generate_param(
                entity_type='team',
                sub_action='confirm_create_team',
                params=params,
                action='team',
            ),
            'is_onteam': is_onteam
        })




def gang_handler(request, params, sub_action):
    # start_time = time.perf_counter()
    # params = param_data['params']
    create_param = ParamSecurity.generate_param(
        entity_type='gang',
        sub_action='create_gang',
        params=params,
        action='gang'
    )
    wap_encrypted_param = ParamSecurity.generate_param(
        entity_type="wap", 
        sub_action="none", 
        params=params, 
        action="wap"
    )
    ## 判断是否已加入帮会
    player = request.session["player"]
    # is_ongang = GangMember.objects.filter(player=player).exists()
    try:
        # 假设你有TeamMember模型
        gang_member = GangMember.objects.get(player=player.id)
        current_gang = gang_member.gang.id
        # print("currteam" + str(current_team.id))
        is_ongang = True
    except GangMember.DoesNotExist:
        is_ongang = False
        current_gang = 0


    if sub_action == 'create_gang':

        if request.method == 'POST':
            gang_name = request.POST.get('gang_name').strip()
            gang_zongzhi = request.POST.get('gang_zongzhi').strip()
            if gang_name:
                # 创建新帮会
                
                if Gang.objects.filter(name=gang_name).exists():
                    messages.error(request, "该名称宗门已存在，请更换名称后重试！")
                    return render(request, 'create_player.html', {'create_param': create_param})
                player = request.session["player"]
                gang = Gang.objects.create(leader=player, name=gang_name)
                GangMember.objects.create(gang=gang, position='bz',player=player)
                ChatMessage.objects.create(
                    type_id=1,  # 系统消息类型
                    message=" 一个新的宗门势力【" + gang.name +"】诞生了！",
                    sender_name=gang.name,
                )

                
                
                # 如果是GET请求，渲染创建角色页面
                return render(request, 'gang_detail.html', {
                    'create_param': create_param,
                    
                    "wap_encrypted_param": wap_encrypted_param,
                    'gang':gang
                })
            else:
                messages.error(request, "名称不能为空")
        
        
        # 如果是GET请求，渲染创建角色页面
        return render(request, 'create_player.html', {
            'create_param': create_param,
            
            'op_action': 'create_gang',
            "wap_encrypted_param": wap_encrypted_param,
        })
    elif sub_action == 'list_gang':



        get_gang_list = Gang.objects.all()[:10]
        gang_list = []
        if get_gang_list:
            for gang in get_gang_list:
                gang_encrypted_param = ParamSecurity.generate_param(
                    entity_type='gang',
                    sub_action='detail_gang',
                    params={'gang_id':gang.id},
                    action='gang',
                    # one_time=True,
                )
                per_gang = '<a href="/wap/?cmd={}">{}</a>'.format(gang_encrypted_param, gang.name)
                gang_list.append(per_gang)


        
            
            
            print(gang.id)
            # messages.error(request, "你还未加入任何宗门")
            return render(request, 'object_rank.html', {
                'create_param': create_param,
                
                'op_action': 'list_gang',
                "wap_encrypted_param": wap_encrypted_param,
                'gang_list': gang_list,
                'is_ongang': is_ongang,
                'mygang_encrypted_param': ParamSecurity.generate_param(
                    entity_type="gang", 
                    sub_action="detail_gang", 
                    params={'gang_id':current_gang}, 
                    action="gang"
                ),
                'record_apply_gang': ParamSecurity.generate_param(
                    entity_type='gang',
                    sub_action='record_apply_gang',
                    params={"gang_id":gang.id},
                    action='gang',
                    # one_time=True,
                ),
            })

    elif sub_action == 'detail_gang':
        player_id = request.session["player_id"]
        # gang = Gang.objects.filter(player=player_id)
        print(player_id)
        print(params)
        # membership = GangMember.objects.select_related('gang').get(id=params)
        gang = Gang.objects.get(id=params.get("gang_id"))

        member_list = []
        get_member_list = gang.get_all_members_info()
        for member in get_member_list:
            player_encrypted_param = ParamSecurity.generate_param(
                entity_type="player", 
                sub_action="detail_player", 
                params={'player_id':member['id']}, 
                action="player"
            )

            context = '<a href="/wap/?cmd={}">{}</a>、'.format(
                player_encrypted_param,
                member["name"],
            )
            if member["name"] == player.name:
                pass
            else:
                member_list.append(context)

        # try:
        has_apply = GangApplication.objects.filter(gang_id=gang.id,player_id=player_id,status='pending').first()
        #     print("aaaaaaaaaaaaaaaaa")
        if has_apply:
            has_apply_gang = True
        else:
            has_apply_gang = False
        # except:
        #     has_apply_gang = False
        print(has_apply_gang)
        
        
        return render(request, 'gang_detail.html', {
            'create_param': create_param,
            
            'op_action': 'detail_gang',
            "wap_encrypted_param": wap_encrypted_param,
            'has_apply_gang': has_apply_gang,
            'member_list': member_list,
            'player_encrypted_param': ParamSecurity.generate_param(
                entity_type='player',
                sub_action='detail_player',
                params={'player_id':gang.leader.id},
                action='player',
                # one_time=True,
            ),
            'gang': gang,
            'current_gang':current_gang,
            'apply_gang_params': ParamSecurity.generate_param(
                entity_type='gang',
                sub_action='apply_gang',
                params={"gang_id":gang.id},
                action='gang',
                # one_time=True,
            ),
            # 'curr_count':curr_count

        })
    elif sub_action == "apply_gang":
        ### 申请加入帮会
        param_data = request.secure_params.get('cmd')
        gang_id = params.get("gang_id")
        player = request.session["player"]

        gang = Gang.objects.get(id=gang_id)
        params = {"gang_id":gang_id}

        if GangApplication.objects.filter(player=player, gang=gang,status="pending").exists():
            messages.error(request, "你已提交申请，请耐心等候门主审批！")
            return redirect(reverse('wap')+f'?cmd={ParamSecurity.generate_param("gang", "detail_gang", params, action="gang")}')

        current_members = GangMember.objects.filter(gang_id=gang_id).count()
        if current_members >= gang.max_count:
            messages.error(request, f"该宗门已满人（{current_members}/{gang.max_count}），请选择其他宗门加入！")
            return redirect(reverse('wap')+f'?cmd={ParamSecurity.generate_param("gang", "detail_gang", params, action="gang")}')

        gang_apply = GangApplication.objects.create(player=player, gang=gang, status='pending')
        messages.success(request, "申请成功，请耐心等候门主审批")
        chat_message = "有人申请加入你的宗门啦，快去宗门页面看看是谁吧~"
        chat = ChatMessage.objects.create(type_id=3, message=chat_message,receiver=gang.leader.id)

        
        
        

        return redirect(reverse('wap')+f'?cmd={ParamSecurity.generate_param("gang", "detail_gang", params, action="gang")}')

    elif sub_action == "record_apply_gang":
        gang_id = params.get("gang_id")
        has_record = True
        player_id = request.session["player_id"]
        

        ## 判断是否帮主
        get_gang = Gang.objects.filter(leader_id=player_id).first()
        if get_gang:
            ### 帮主
            is_gangleader = True
            record_list = []
            ### 获取所有申请记录
            get_apply_record = GangApplication.objects.filter(gang_id=gang_id, status='pending')
            if get_apply_record:
                for record in get_apply_record:
                    apply_player_params = ParamSecurity.generate_param(
                        entity_type='player',
                        sub_action='detail_player',
                        params={'player_id':record.player.id},
                        action='player',
                    )
                    accept_apply_params = ParamSecurity.generate_param(
                        entity_type='gang',
                        sub_action='accept_apply',
                        params={'player_id':record.player.id,'gang_id':record.gang.id},
                        action='gang',
                    )
                    reject_apply_params = ParamSecurity.generate_param(
                        entity_type='gang',
                        sub_action='reject_apply',
                        params={'player_id':record.player.id,'gang_id':record.gang.id},
                        action='gang',
                    )
                    apply_record = '<a href="/wap/?cmd={}">{}</a> 申请加入宗门 <a href="/wap/?cmd={}">同意</a> | <a href="/wap/?cmd={}">拒绝</a>'.format(
                        apply_player_params,record.player,accept_apply_params,reject_apply_params
                    )
                    record_list.append(apply_record)
            else:
                has_record = False
            
            
            
            return render(request, 'gang_detail.html', {
                
                "wap_encrypted_param": wap_encrypted_param,
                'op_action': 'record_apply_gang',
                'record_list': record_list,
                'has_record':has_record,
                'is_gangleader': is_gangleader,
                # 'get_apply_record':get_apply_record,
                # 'get_record':get_record
            })

        else:
            is_gangleader = False
            get_apply_record = GangApplication.objects.filter(player_id=player_id, gang_id=gang_id, status='pending').first()

            if get_apply_record == None:
                ### 无申请记录
                has_record = False
                
                
                
                return render(request, 'gang_detail.html', {
                    
                    "wap_encrypted_param": wap_encrypted_param,
                    'op_action': 'record_apply_gang',
                    # 'record_list': record_list,
                    'has_record':has_record,
                    'is_gangleader': is_gangleader,
                    'get_apply_record':get_apply_record,
                })

            else:
                has_record = True
                record_id = get_apply_record.id

                
                
                return render(request, 'gang_detail.html', {
                    
                    "wap_encrypted_param": wap_encrypted_param,
                    'op_action': 'record_apply_gang',
                    # 'record_list': record_list,
                    'revoke_apply_record': ParamSecurity.generate_param(
                        entity_type='gang',
                        sub_action='revoke_apply_gang',
                        params={'record_id':record_id},
                        action='gang',
                        # one_time=True,
                    ),
                    'has_record':has_record,
                    'is_gangleader': is_gangleader,
                    'get_apply_record':get_apply_record,
                    # 'get_record':get_record
                })
             

    elif sub_action == "revoke_apply_gang":
        apply_record_id = params.get("record_id")

        # apply_record = GangApplication.objects.filter(player_id=player.id, id=apply_record_id,status='pending').update(status='revoked')
        # apply_record.status = 'revoked'
        # apply_record.save()
        apply_record = GangApplication.objects.filter(player_id=player.id, id=apply_record_id,status='pending')
        apply_record.delete()
        messages.success(request,'你已撤回加入宗门的申请，现在你可以加入其他宗门或创建自己的宗门')

        
        
        return redirect(reverse('wap') + f'?cmd={ParamSecurity.generate_param("gang", "list_gang", {}, action="gang")}')

    elif sub_action == "accept_apply":
        player_id = params.get("player_id")
        gang_id = params.get("gang_id")
        gangmember = GangMember.objects.create(gang_id=gang_id,player_id=player_id)

        apply_record = GangApplication.objects.filter(player_id=player_id,gang_id=gang_id,status="pending").update(status="accepted")
        banghui_message = '<a href="/wap/?cmd={}">欢迎 {} 加入本宗门~</a>'
        siliao_message = '你申请的宗门同意了你的加入'
        # chat_message = ChatMessage.objects.create(type_id=4,message=message,bangpai_id=gang_id)
        # chat_message = ChatMessage.objects.create(type_id=3,message=message)

        chat_messages = [
            ChatMessage(type_id=3, message=siliao_message, receiver=player_id),
            ChatMessage(type_id=4, message=banghui_message, bangpai_id=gang_id),
            
        ]

        # 批量创建消息
        created_messages = ChatMessage.objects.bulk_create(chat_messages)

        messages.success(request,"审批通过")
        params = ParamSecurity.generate_param("gang","record_apply_gang", {}, action="gang")
        return redirect(reverse('wap')+f'?cmd={params}')

    elif sub_action == "reject_apply":
        player_id = params.get("player_id")
        gang_id = params.get("gang_id")    
        apply_record = GangApplication.objects.filter(player_id=player_id,gang_id=gang_id,status="pending").update(status="rejected")
        messages.success(request,"已拒绝")
        message = '宗门<a href="/wap/?cmd={}">{}</a>拒绝了你的加入申请'
        chat_message = ChatMessage.objects.create(type_id=4,message=message,receiver=player_id)

        params = ParamSecurity.generate_param("gang","record_apply_gang", {}, action="gang")
        return redirect(reverse('wap')+f'?cmd={params}')

    else:
        pass



def chat_handler(request, params, sub_action):
    # 处理玩家相关的操作
    curr_player = request.session["player"]
    if sub_action == 'send_message':
        # 处理发送消息的逻辑

        chat_type = params.get("chat_type", 2)  # 默认是世界消息

        create_param = ParamSecurity.generate_param(
            entity_type='chat',
            sub_action='send_message',
            params={'chat_type': chat_type},
            action='chat'
        )


        if request.method == 'POST':
            # 处理表单提交
            print("处理表单提交")
            curr_player_id = request.session["player_id"]
            player_name = request.session["player_name"]
            message = request.POST.get('message_input').strip()
            # signature = request.POST.get('signature').strip()
            print(f"player_name: {player_name}")
            print(message)
            ### 校验字段

            chat_list = []
            if message:
                if len(message) > 100:
                    messages.error(request, "消息长度不能超过100个字符")
                    return redirect(reverse('wap') + f'?cmd={ParamSecurity.generate_param("chat", "list_chat", {"chat_type": chat_type}, action="chat")}')
                if chat_type == 2:
                    # 世界消息
                    chat = ChatMessage.objects.create(type_id=chat_type, sender=curr_player.id, sender_name=curr_player.name, message=message)
                elif chat_type == 3:
                    # 私聊消息
                    receiver_id = params.get("receiver_id")
                    if not receiver_id:
                        messages.error(request, "私聊消息需要指定接收者")
                        return redirect(reverse('wap') + f'?cmd={ParamSecurity.generate_param("chat", "list_chat", {"chat_type": chat_type}, action="chat")}')
                    chat = ChatMessage.objects.create(type_id=chat_type, sender=curr_player.id, sender_name=curr_player.name, message=message, receiver=receiver_id)
                elif chat_type == 4:
                    # 帮会消息
                    # bangpai_id = params.get("bangpai_id")
                    # 提前获取用户帮派和队伍信息
                    gang_member = GangMember.objects.filter(player_id=curr_player.id).first()
                    bangpai_id = gang_member.gang.id if gang_member else None

                    if bangpai_id is None:
                        messages.error(request, "帮会消息需要指定帮会ID")
                        return redirect(reverse('wap') + f'?cmd={ParamSecurity.generate_param("chat", "list_chat", {"chat_type": chat_type}, action="chat")}')
                    chat = ChatMessage.objects.create(type_id=chat_type, sender=curr_player.id, sender_name=curr_player.name, message=message, bangpai_id=bangpai_id)
                elif chat_type == 5:
                    # 队伍消息
                    team_member = TeamMember.objects.filter(player_id=curr_player.id).first()
                    duiwu_id = team_member.team.id if team_member else None
                    if duiwu_id is None:
                        messages.error(request, "队伍消息需要指定队伍ID")
                        return redirect(reverse('wap') + f'?cmd={ParamSecurity.generate_param("chat", "list_chat", {"chat_type": chat_type}, action="chat")}')
                    chat = ChatMessage.objects.create(type_id=chat_type, sender=curr_player.id, sender_name=curr_player.name, message=message, duiwu_id=duiwu_id)
                # chat = ChatMessage.objects.create(type_id=2, sender=curr_player_id,sender_name=player_name,message=message)
                else:
                    pass
                messages.success(request, "发送成功")     
            else:
                # 返回错误信息
                messages.error(request, "你什么都没输入呀")

            return redirect(reverse('wap') + f'?cmd={ParamSecurity.generate_param("chat", "list_chat", {"chat_type": chat_type}, action="chat")}')
        
        
    elif sub_action == 'list_chat':
        # 处理查看消息的逻辑
        print("viewsssssssssssssssssss")
        chat_type = params.get("chat_type")
        page = int(params.get("page", 1))
        chat_type = int(params.get("chat_type"))
        PAGE_SIZE = 10  # 每页消息数量

        # 基础查询
        base_query = ChatMessage.objects.all()

        # 根据聊天类型过滤
        if chat_type == 1:  # 系统消息
            base_query = base_query.filter(type_id=1)
        elif chat_type == 2:  # 世界消息
            base_query = base_query.filter(type_id=2)
        elif chat_type == 3:  # 私聊消息
            base_query = base_query.filter(type_id=3, receiver=curr_player.id)
        elif chat_type == 4:  # 帮派消息
            gang = GangMember.objects.filter(player_id=curr_player.id).first()
            if gang:
                base_query = base_query.filter(type_id=4, bangpai_id=gang.gang.id)

            else:
                base_query = base_query.none()
        elif chat_type == 5:  # 队伍消息
            team = TeamMember.objects.filter(player_id=curr_player.id).first()
            if team:
                base_query = base_query.filter(type_id=5, duiwu_id=team.team.id)
            else:
                base_query = base_query.none()
        
        # 计算分页
        total_count = base_query.count()
        total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE
        
        # 确保页码在有效范围内
        page = max(1, min(page, total_pages))
        
        # 获取当前页数据
        offset = (page - 1) * PAGE_SIZE
        chat_lists = base_query.order_by('-created_at')[offset:offset + PAGE_SIZE]
        
        # 格式化消息
        chat_list = []
        for chat in chat_lists:
            # 生成玩家详情加密参数
            player_encrypted_param = ""
            if chat.sender:
                player_encrypted_param = ParamSecurity.generate_param(
                    entity_type='player',
                    sub_action='detail_player',
                    params={"player_id": chat.sender},
                    action='player'
                )
            
            # 格式化消息内容
            if chat_type == 1:  # 系统消息
                if chat.sender_name:
                    content = "[系统]" + chat.message.format(
                        player_encrypted_param, chat.sender_name
                    )
                else:
                    content = "[系统]" + chat.message
            else:  # 其他消息
                sender_display = (
                    f'<a href="/wap/?cmd={player_encrypted_param}">{chat.sender_name}</a>'
                    if chat.sender_name else "未知"
                )
                content = f"[{chat.get_type_id_display()}]{sender_display}: {chat.message}"
            
            # 添加时间戳
            full_message = f"{content}({chat.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
            chat_list.append(full_message)
        


        # 创建分页导航
        pagination = []
        if page > 1:
            shouye_params = generate_page_param(entity='chat', type_value=chat_type, page_num=1)
            shangyiye_params = generate_page_param(entity='chat', type_value=chat_type, page_num=page-1)
            pagination.append(f'<a href="/wap/?cmd={shouye_params}">首页</a>')
            pagination.append(f'<a href="/wap/?cmd={shangyiye_params}">上一页</a>')
        
        # 显示当前页和总页数
        pagination.append(f'第{page}/{total_pages}页')
        
        if page < total_pages:
            xiayiye_params = generate_page_param(entity='chat', type_value=chat_type, page_num=page+1)
            weiye_params = generate_page_param(entity='chat', type_value=chat_type, page_num=total_pages)
            pagination.append(f'<a href="/wap/?cmd={xiayiye_params}">下一页</a>')
            pagination.append(f'<a href="/wap/?cmd={weiye_params}">尾页</a>')


        return render(request, 'chat.html', {
            # 'player': player,
            'pagination': " ".join(pagination),
            'wap_encrypted_param': ParamSecurity.generate_param(
                entity_type='wap',
                sub_action='none',
                params=params,
                action='wap'
            ),
            'chat_list': chat_list,
            'chat_type': chat_type,
            'create_param': ParamSecurity.generate_param(
                entity_type='chat',
                sub_action='send_message',
                params=params,
                action='chat'
            ),
            'shijie_params': ParamSecurity.generate_param(
                entity_type='chat',
                sub_action='list_chat',
                params={'chat_type':2},
                action='chat'
            ),
            'siliao_params': ParamSecurity.generate_param(
                entity_type='chat',
                sub_action='list_chat',
                params={'chat_type':3},
                action='wap'
            ),
            'bangpai_params': ParamSecurity.generate_param(
                entity_type='chat',
                sub_action='list_chat',
                params={'chat_type':4},
                action='chat'
            ),
            'xitong_params': ParamSecurity.generate_param(
                entity_type='chat',
                sub_action='list_chat',
                params={'chat_type':1},
                action='chat'
            ),
            'duiwu_params': ParamSecurity.generate_param(
                entity_type='chat',
                sub_action='list_chat',
                params={'chat_type':5},
                action='chat'
            ),
        })
    else:
        pass

def chat(request):
    return render(request, 'chat.html')

# 缓存最近消息的键名模板
def get_chat_cache_key(chat_type, identifier=None):
    """生成聊天缓存键"""
    if chat_type == 2:  # 世界聊天
        return f"world_chat:latest"
    elif chat_type == 3:  # 帮派聊天
        return f"guild_chat:{identifier}:latest"
    elif chat_type == 4:  # 队伍聊天
        return f"team_chat:{identifier}:latest"
    elif chat_type == 5:  # 私聊
        return f"private_chat:{identifier}:latest"
    return f"system_chat:latest"

@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """发送聊天消息"""
    try:
        data = json.loads(request.body)
        player_id = data.get('player_id')
        player_name = data.get('player_name')
        message_type = int(data.get('type_id'))
        message_content = data.get('message')[:256]  # 确保不超过长度限制
        
        # 验证基本参数
        if not all([player_id, player_name, message_type, message_content]):
            return JsonResponse({'status': 'error', 'message': '缺少必要参数'}, status=400)
        
        # 创建消息对象
        chat_data = {
            'type_id': message_type,
            'sender': player_id,
            'sender_name': player_name,
            'message': message_content,
            'created_at': datetime.now()
        }
        
        # 根据聊天类型设置额外参数
        if message_type == 3:  # 帮派聊天
            bangpai_id = data.get('bangpai_id')
            if not bangpai_id:
                return JsonResponse({'status': 'error', 'message': '缺少帮派ID'}, status=400)
            chat_data['bangpai_id'] = bangpai_id
        
        elif message_type == 4:  # 队伍聊天
            duiwu_id = data.get('duiwu_id')
            if not duiwu_id:
                return JsonResponse({'status': 'error', 'message': '缺少队伍ID'}, status=400)
            chat_data['duiwu_id'] = duiwu_id
        
        elif message_type == 5:  # 私聊
            receiver_id = data.get('receiver_id')
            if not receiver_id:
                return JsonResponse({'status': 'error', 'message': '缺少接收者ID'}, status=400)
            chat_data['receiver'] = receiver_id
        
        # 系统消息只能由特定接口发送
        if message_type == 1:
            return JsonResponse({'status': 'error', 'message': '玩家不能发送系统消息'}, status=403)
        
        # 创建消息并更新缓存
        with transaction.atomic():
            msg = ChatMessage.objects.create(**chat_data)
            
            # 更新缓存
            cache_key = get_chat_cache_key(
                message_type, 
                identifier=chat_data.get('bangpai_id') or 
                         chat_data.get('duiwu_id') or 
                         chat_data.get('receiver')
            )
            cached_messages = cache.get(cache_key, [])
            
            # 只保留最近20条消息在缓存中
            if len(cached_messages) >= 20:
                cached_messages.pop(0)
                
            cached_messages.append({
                'id': msg.id,
                'sender_name': player_name,
                'message': message_content,
                'time': msg.created_at.strftime('%H:%M')
            })
            cache.set(cache_key, cached_messages, timeout=300)  # 缓存5分钟
        
        return JsonResponse({'status': 'success', 'message_id': msg.id})
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@require_http_methods(["GET"])
def get_messages(request):
    """获取聊天消息"""
    try:
        player_id = request.GET.get('player_id')
        message_type = int(request.GET.get('type_id', 2))  # 默认为世界聊天
        last_message_id = int(request.GET.get('last_id', 0))
        
        # 根据聊天类型确定标识符
        identifier = None
        cache_key = None
        use_cache = True
        
        if message_type == 3:  # 帮派聊天
            identifier = request.GET.get('bangpai_id')
            if not identifier:
                return JsonResponse({'status': 'error', 'message': '缺少帮派ID'}, status=400)
            cache_key = get_chat_cache_key(message_type, identifier)
        
        elif message_type == 4:  # 队伍聊天
            identifier = request.GET.get('duiwu_id')
            if not identifier:
                return JsonResponse({'status': 'error', 'message': '缺少队伍ID'}, status=400)
            cache_key = get_chat_cache_key(message_type, identifier)
        
        elif message_type == 5:  # 私聊
            identifier = request.GET.get('other_player_id', player_id)  # 对方玩家ID
            if not identifier:
                return JsonResponse({'status': 'error', 'message': '缺少对方玩家ID'}, status=400)
            cache_key = get_chat_cache_key(message_type, identifier)
            # 私聊不缓存，因为消息量少且隐私性高
            use_cache = False
        
        else:  # 系统(1)和世界(2)聊天
            cache_key = get_chat_cache_key(message_type)
        
        # 尝试从缓存获取
        if use_cache:
            cached_messages = cache.get(cache_key)
            if cached_messages:
                return JsonResponse({
                    'status': 'success',
                    'messages': cached_messages,
                    'from_cache': True
                })
        
        # 数据库查询条件
        filters = Q(type_id=message_type)
        
        # 添加类型特定的过滤条件
        if message_type == 3:  # 帮派
            filters &= Q(bangpai_id=identifier)
        elif message_type == 4:  # 队伍
            filters &= Q(duiwu_id=identifier)
        elif message_type == 5:  # 私聊
            # 私聊需要双向过滤
            filters &= (
                (Q(sender=player_id) & Q(receiver=identifier)) |
                (Q(sender=identifier) & Q(receiver=player_id)
            ))
        
        # 获取消息（最多50条）
        messages = ChatMessage.objects.filter(filters)
        
        if last_message_id > 0:
            messages = messages.filter(id__gt=last_message_id)
        
        messages = messages.order_by('-id')[:50]
        
        # 格式化消息
        formatted_messages = []
        for msg in messages:
            # 系统消息特殊处理
            if message_type == 1:
                display_text = f"系统公告: {msg.message}"
            else:
                display_text = f"{msg.sender_name}: {msg.message}"
            
            formatted_messages.append({
                'id': msg.id,
                'text': display_text,
                'time': msg.created_at.strftime('%H:%M')
            })
        
        # 更新缓存（非私聊）
        if use_cache and formatted_messages:
            cache.set(cache_key, formatted_messages, timeout=300)
        
        return JsonResponse({
            'status': 'success',
            'messages': formatted_messages,
            'from_cache': False
        })
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)