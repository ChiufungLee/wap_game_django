# game/refresh.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from .models import GameMap, GameMapNPC, GameMapItem, MapConfig
from .cache_utils import invalidate_map_cache
import random

class Command(BaseCommand):
    help = '刷新游戏地图内容（NPC和物品）'
    
    def handle(self, *args, **options):
        self.stdout.write("开始刷新游戏地图内容...")
        
        # 1. 清理过期物品
        expired_items = GameMapItem.objects.filter(
            expire_time__lte=timezone.now()
        )
        expired_count = expired_items.count()
        expired_items.delete()
        self.stdout.write(f"清理过期物品: {expired_count}个")
        
        # 2. 刷新NPC
        refreshed_maps = set()
        for map_id in MapConfig.objects.values_list('map_id', flat=True).distinct():
            self.refresh_map_npcs(map_id)
            refreshed_maps.add(map_id)
            self.stdout.write(f"刷新地图 {map_id} 的NPC")
        
        # 3. 刷新物品
        for map_id in refreshed_maps:
            self.refresh_map_items(map_id)
            self.stdout.write(f"刷新地图 {map_id} 的物品")
        
        self.stdout.write("地图内容刷新完成！")
    
    def refresh_map_npcs(self, map_id):
        """刷新指定地图的NPC"""
        # 删除现有NPC（除了永久NPC）
        GameMapNPC.objects.filter(
            map_id=map_id,
            npc__is_permanent=False
        ).delete()
        
        # 从配置生成新NPC
        config = MapConfig.objects.get(map_id=map_id)
        for npc_config in config.npcs:
            if random.random() <= npc_config['spawn_chance']:
                count = random.randint(npc_config['min_count'], npc_config['max_count'])
                GameMapNPC.objects.create(
                    map_id=map_id,
                    npc_id=npc_config['npc_id'],
                    count=count
                )
        
        # 清除地图缓存
        invalidate_map_cache(map_id)
    
    def refresh_map_items(self, map_id):
        """刷新指定地图的物品"""
        config = MapConfig.objects.get(map_id=map_id)
        for item_config in config.items:
            if random.random() <= item_config['spawn_chance']:
                count = random.randint(item_config['min_count'], item_config['max_count'])
                GameMapItem.objects.create_item(
                    map_id=map_id,
                    item_id=item_config['item_id'],
                    count=count,
                    expire_minutes=item_config['expire_minutes']
                )