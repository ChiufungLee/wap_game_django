import random
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q, F, Prefetch
from ..models import GameNPC, Task, TaskItem, PlayerTask, Item, NPCDropList, SellGoods

class CacheManager:
    @staticmethod
    def get_npc_info(npc_id):
        """
        获取NPC信息（带缓存）
        包含怪物掉落信息
        """
        cache_key = f"npc:{npc_id}:info"
        cached_info = cache.get(cache_key)
        
        if cached_info:
            return cached_info
        
        # try:
        #     # 创建Prefetch对象来优化查询
        #     droplist_prefetch = Prefetch(
        #         'droplist',
        #         queryset=NPCDropList.objects.select_related('item')
        #     )
            
        #     npc = GameNPC.objects.select_related('map').prefetch_related(
        #         droplist_prefetch
        #     ).get(id=npc_id)
        # except GameNPC.DoesNotExist:
        #     return None


        # 从数据库获取NPC信息
        try:
            npc = GameNPC.objects.only(
                'name', 'npc_type', 'level', 'description', 
                'hp', 'attack', 'defense', 'exp_reward', 'gold_reward',
                'dialogue', 'shop_items', 'is_boss',
            ).get(id=npc_id)
        except GameNPC.DoesNotExist:
            return None
        
        drop_info =None
        if npc.npc_type == 'monster':
            drop_info = CacheManager.get_npc_drop_info(npc_id)

        # 构建NPC信息字典
        npc_info = {
            'id': npc.id,
            'name': npc.name,
            'npc_type': npc.npc_type,
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
            'drop_info': drop_info,
        }
        
        # 如果是怪物，获取掉落信息
        # if npc.npc_type == 'monster':
        #     npc_info['drop_info'] = get_npc_drop_info(npc_id)
        # # 如果是怪物，获取掉落信息
        # if npc.npc_type == 'monster' and hasattr(npc, 'droplist'):
        #     drop_info = {
        #         'gold': 0,
        #         'exp': 0,
        #         'items': []
        #     }
            
        #     # 处理每个掉落项
        #     for drop in npc.droplist.all():
        #         # 金币掉落
        #         if drop.item.item_type == 'currency' and drop.item.name == "金币":
        #             drop_info['gold'] += drop.count
        #         # 经验掉落
        #         elif drop.item.item_type == 'currency' and drop.item.name == "经验":
        #             drop_info['exp'] += drop.count
        #         # 普通物品掉落
        #         else:
        #             drop_info['items'].append({
        #                 'item_id': drop.item.id,
        #                 'item_name': drop.item.name,
        #                 'drop_rate': min(1.0, max(0.0, drop.gailv / 100.0)),
        #                 'count': drop.count
        #             })
            
        #     npc_info['drop_info'] = drop_info

        # 设置缓存
        cache.set(cache_key, npc_info, settings.CACHE_TTL['NPC_INFO'])
        return npc_info

    @staticmethod
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

    @staticmethod
    def parse_drop_info(drop_items):
        """解析掉落信息"""
        if not isinstance(drop_items, dict):
            return None
            
        validated_drops = []
        for item in drop_items.get('items', []):
            if 'item_id' in item and 'drop_rate' in item:
                validated_drops.append({
                    'item_id': item['item_id'],
                    'drop_rate': min(1.0, max(0.0, item['drop_rate'])),
                    'min_count': max(1, item.get('min_count', 1)),
                    'max_count': max(1, item.get('max_count', 1))
                })
        
        return {
            'gold_min': max(0, drop_items.get('gold_min', 0)),
            'gold_max': max(0, drop_items.get('gold_max', 0)),
            'exp_min': max(0, drop_items.get('exp_min', 0)),
            'exp_max': max(0, drop_items.get('exp_max', 0)),
            'items': validated_drops
        }

    @staticmethod
    def get_or_set(key, callback, ttl_key='DEFAULT'):
        """通用缓存获取方法"""
        ttl = settings.CACHE_TTL.get(ttl_key, 60)
        result = cache.get(key)
        if result is None:
            print(f"缓存未命中，执行回调: {key}")
            result = callback()
            if result is not None:
                cache.set(key, result, timeout=ttl)
        print(f"从缓存获取: {key}")
        return result

    @staticmethod
    def get_task_config(task_id):
        """获取任务配置（带缓存）"""
        def fetch_task():
            task = Task.objects.filter(id=task_id).first()
            if not task:
                return None

            if task.function_type == 1:  # 3=对话任务类型
                return {
                    'id': task.id,
                    'name': task.name,
                    'description': task.description,
                    'theme': task.theme,
                    'function_type': task.function_type,
                    'accept_npc_id': task.accept_npc_id,
                    'submit_npc_id': task.submit_npc_id,
                    'rewards': task.rewards,
                    # 'targets': targets,
                    'accept_dialog': task.accept_dialog,
                    'progress_dialog': task.progress_dialog,
                    'completion_dialog': task.completion_dialog,
                    'map': task.map,
                    'is_dropable': task.is_droppable,
                    'trigger_conditions': task.trigger_conditions,
                    'prev_task_id': task.prev_task_id,
                    
                    'targets': [{
                        'target_type': 3,
                        'target_id': task.submit_npc_id,  # 使用提交NPC
                        'amount': 1,
                        'is_virtual': True  # 标记虚拟目标
                    }]
                }

            targets = list(TaskItem.objects.filter(task=task).values(
                'target_type', 'target_id', 'amount'
            ))

            print(f"获取任务配置目标{targets}")
            print(f"查询目标，条件: task_id={task_id}，结果: {len(targets)}个")
            
            return {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'theme': task.theme,
                'function_type': task.function_type,
                'accept_npc_id': task.accept_npc_id,
                'submit_npc_id': task.submit_npc_id,
                'rewards': task.rewards,
                'targets': targets,
                'accept_dialog': task.accept_dialog,
                'progress_dialog': task.progress_dialog,
                'completion_dialog': task.completion_dialog,
                'map': task.map,
                'is_dropable': task.is_droppable,
                'trigger_conditions': task.trigger_conditions,
                'prev_task_id': task.prev_task_id,

            }
        
        return CacheManager.get_or_set(
            f"task:{task_id}:config",
            fetch_task,
            'TASK_CONFIG'
        )

    @staticmethod
    def get_player_tasks(player_id):
        """获取玩家任务状态（带缓存）"""
        def fetch_tasks():
            return list(PlayerTask.objects.filter(
                player_id=player_id,
                # status=1  # 进行中任务
            ).values('id', 'task_id', 'status', 'started_at'))
        
        return CacheManager.get_or_set(
            f"player:{player_id}:tasks",
            fetch_tasks,
            'PLAYER_TASKS'
        )

    @staticmethod
    def get_target_name(target_type, target_id):
        """获取目标名称（带缓存）"""
        def fetch_name():
            if target_type == 1:  # 物品
                item = Item.objects.filter(id=target_id).values('name').first()
                return item['name'] if item else f"物品#{target_id}"
            elif target_type == 2:  # 怪物
                npc = GameNPC.objects.filter(
                    id=target_id, 
                    npc_type='monster'
                ).values('name').first()
                return npc['name'] if npc else f"怪物#{target_id}"
            elif target_type == 3:  # NPC
                npc = GameNPC.objects.filter(
                    id=target_id, 
                    npc_type='npc'
                ).values('name').first()
                return npc['name'] if npc else f"NPC#{target_id}"
            return f"目标#{target_id}"
        
        return CacheManager.get_or_set(
            f"target:{target_type}:{target_id}:name",
            fetch_name,
            'TARGET_NAMES'
        )

    @staticmethod
    def invalidate_npc_info(npc_id):
        """清除NPC信息缓存"""
        cache.delete(f"npc:{npc_id}:info")
    
    @staticmethod
    def invalidate_player_tasks(player_id):
        """清除玩家任务缓存"""
        cache.delete(f"player:{player_id}:tasks")
    
    @staticmethod
    def invalidate_task_config(task_id):
        """清除任务配置缓存"""
        cache.delete(f"task:{task_id}:config")
    
    @staticmethod
    def batch_get_npc_info(npc_ids):
        """批量获取NPC信息（高效版）"""
        # 构建缓存键列表
        cache_keys = [f"npc:{npc_id}:info" for npc_id in npc_ids]
        
        # 批量从缓存获取
        cached_results = cache.get_many(cache_keys)
        
        # 找出未缓存的NPC ID
        uncached_ids = []
        results = {}
        
        for i, npc_id in enumerate(npc_ids):
            key = cache_keys[i]
            if key in cached_results:
                results[npc_id] = cached_results[key]
            else:
                uncached_ids.append(npc_id)
        
        # 从数据库获取未缓存的NPC信息
        if uncached_ids:
            npcs = GameNPC.objects.filter(id__in=uncached_ids).only(
                'name', 'npc_type', 'level', 'description', 
                'hp', 'attack', 'defense', 'exp_reward', 'gold_reward',
                'dialogue', 'shop_items', 'is_boss', 'drop_items'
            )
            
            # 处理并缓存结果
            to_cache = {}
            for npc in npcs:
                npc_info = {
                    'id': npc.id,
                    'name': npc.name,
                    'npc_type': npc.npc_type,
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
                    'drop_info': None
                }
                
                if npc.npc_type == 'monster' and npc.drop_items:
                    npc_info['drop_info'] = CacheManager.parse_drop_info(npc.drop_items)
                
                results[npc.id] = npc_info
                to_cache[f"npc:{npc.id}:info"] = npc_info
            
            # 批量设置缓存
            cache.set_many(to_cache, settings.CACHE_TTL['NPC_INFO'])
        
        # 按原始顺序返回结果
        return [results.get(npc_id) for npc_id in npc_ids]

    @staticmethod
    def get_mall_goods(shop_type):
        """获取商城商品列表（带缓存）"""
        cache_key = f'shop_{shop_type}_goods'
        goods = cache.get(cache_key)
        if not goods:
            goods = list(
                SellGoods.objects
                .filter(shop_type=shop_type)
                .select_related('item')
                .only('item_id', 'price', 'currency_type', 'item__name', 'item__description')
                .values(
                    'id',
                    'item_id',
                    'item__name',
                    'item__description',
                    'price',
                    'currency_type'
                )
            )
            cache.set(cache_key, goods, timeout=300)
        return goods