from django.contrib import admin

# Register your models here.
from game.models import User, GamePage, PageComponent, GameEvent, Player, GameCity, GameMap, GameMapArea, Gang, GangMember, GangApplication, \
    Skill, PlayerSkill, GameBase, ChatMessage, GameNPC, Item, PlayerItem, GameMapNPC, GameMapItem, QuickSlot
 
# Register your models here.
admin.site.register([User, GamePage, PageComponent, GameEvent, Player, GameCity, GameMap, GameMapArea, Gang, GangMember, GangApplication, \
    Skill, PlayerSkill, GameBase, ChatMessage, GameNPC, Item, PlayerItem, GameMapNPC, GameMapItem, QuickSlot])