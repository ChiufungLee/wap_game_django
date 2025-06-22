# combat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from ..models import GameNPC

class CombatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.npc_id = self.scope['url_route']['kwargs']['npc_id']
        self.room_group_name = f'combat_{self.npc_id}'

        # 加入战斗房间组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # 发送初始状态
        is_boss, current_hp = await self.get_npc_status()
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'npc_id': self.npc_id,
            'is_boss': is_boss,
            'current_hp': current_hp
        }))

    async def disconnect(self, close_code):
        # 离开房间组
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # 接收来自WebSocket的消息
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'get_status':
            is_boss, current_hp = await self.get_npc_status()
            await self.send(text_data=json.dumps({
                'type': 'status_update',
                'npc_id': self.npc_id,
                'is_boss': is_boss,
                'current_hp': current_hp
            }))

    # 处理战斗事件
    async def combat_event(self, event):
        # 向WebSocket发送战斗事件
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_npc_status(self):
        """获取NPC状态（是否BOSS，当前HP）"""
        try:
            npc = GameNPC.objects.only('is_boss').get(id=self.npc_id)
            if npc.is_boss:
                current_hp = cache.get(f"boss_hp_{self.npc_id}", npc.hp)
            else:
                current_hp = npc.hp  # 普通怪物不共享HP，返回基础HP
            return npc.is_boss, current_hp
        except GameNPC.DoesNotExist:
            return False, 0