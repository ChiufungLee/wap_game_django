from django.db import models
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.db.models import F, Sum
import logging
logger = logging.getLogger(__name__)
# from .utils.cache_utils import invalidate_map_cache, invalidate_npc_cache, invalidate_player_cache

# Create your models here.
class User(models.Model):
    # 用户类型选项 - 添加明确选项
    USER_TYPE_CHOICES = (
        (0, '管理员'),
        (1, '普通用户'),
        (2, 'VIP用户'),  # 预留扩展
    )
    STATUS_CHOICES = (
        (0, '正常'),
        (1, '禁用'),
        (2, '待验证'),
    )
    username = models.CharField(max_length=32, unique=True, verbose_name="用户名")
    password = models.CharField(max_length=128, verbose_name="密码")
    # 联系信息
    email = models.EmailField(max_length=64, null=True, blank=True, verbose_name="邮箱")
    phone = models.CharField(max_length=32, null=True, blank=True, verbose_name="手机号")
    # 用户类型 - 使用SmallInteger节省空间
    user_type = models.PositiveSmallIntegerField(
        choices=USER_TYPE_CHOICES, 
        default=1, 
        verbose_name="用户类型"
    )
    # 状态标记（0=正常，1=禁用，2=待验证）
    status = models.PositiveSmallIntegerField(
        default=0, 
        verbose_name="用户状态",
        choices=STATUS_CHOICES
    )
    security_code = models.CharField(max_length=8, verbose_name="安全码")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="注册时间")
    # 登录信息
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="最近登录IP")
    last_login_at = models.DateTimeField(null=True, blank=True, verbose_name="最近登录时间")
    failed_attempts = models.PositiveSmallIntegerField(default=0, verbose_name="登录失败次数")
    # 扩展属性
    params = models.JSONField(default=dict, verbose_name="扩展属性")

    class Meta:
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['last_login_ip']), 
        ]
        db_table = 'game_user'
        verbose_name = '游戏用户'

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    def lock_account(self):
        """锁定账户"""
        self.status = 1
        self.save(update_fields=['status'])
    
    def unlock_account(self):
        """解锁账户"""
        self.status = 0
        self.save(update_fields=['status'])
    
    def reset_login_attempts(self):
        """重置登录尝试次数"""
        self.status = 0
        self.failed_attempts = 0
        self.save(update_fields=['status', 'failed_attempts'])
    
    def increment_login_attempts(self):
        """增加登录尝试次数并检查是否锁定"""
        self.failed_attempts += 1
        if self.failed_attempts >= 10:  # 10次失败后锁定
            self.status = 1
            update_fields = ['status', 'failed_attempts']
        else:
            update_fields = ['failed_attempts']
        
        self.save(update_fields=update_fields)
    
    def update_last_login_info(self, ip_address):
        """更新最后登录信息"""
        self.last_login_at = timezone.now()
        self.last_login_ip = ip_address
        self.reset_login_attempts()  # 登录成功后重置失败次数
        self.save(update_fields=['last_login_at', 'last_login_ip', 'failed_attempts'])
    
    def is_admin(self):
        """检查是否是管理员"""
        if self.user_type == 0:
            return True
        else:
            return False
    
    def is_active(self):
        """检查账户是否可用"""
        return self.status == 0

# 页面模板
class GamePage(models.Model):
    name = models.CharField(max_length=64, unique=True, verbose_name="页面名称")
    description = models.TextField(blank=True, default='', verbose_name="页面描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    custom_css = models.TextField(blank=True, default='')
    custom_js = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = "游戏页面"
        verbose_name_plural = "游戏页面"
    
    def __str__(self):
        return self.name

    def get_next_position(self):
        """获取下一个可用位置"""
        last_component = self.components.order_by('-position').first()
        return last_component.position + 1 if last_component else 1
    
    def reorder_components(self):
        """重新排序当前页面的所有组件"""
        components = self.components.order_by('position')
        position = 1
        updates = []
        
        for component in components:
            if component.position != position:
                component.position = position
                updates.append(component)
            position += 1
        
        if updates:
            with transaction.atomic():
                PageComponent.objects.bulk_update(updates, ['position'])


# 页面组件
class PageComponent(models.Model):
    COMPONENT_TYPES = (
        ('text', '文本'),
        ('function', '操作'),
        ('input', '输入框'),
        ('link', '链接'),
    )
    
    display_text = models.TextField(blank=True, default='', verbose_name="显示内容")
    show_condition = models.TextField(blank=True, default='', verbose_name="显示条件")
    position = models.PositiveIntegerField(default=0, verbose_name="组件位置")
    component_type = models.CharField(max_length=128, choices=COMPONENT_TYPES, default='text', verbose_name="组件类型")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    # target_function = models.CharField(max_length=256, default='', verbose_name="目标参数")
    page = models.ForeignKey(
        'GamePage', 
        on_delete=models.CASCADE, 
        related_name='components', 
        verbose_name="所属页面"
    )    
    event = models.ForeignKey(
        'GameEvent', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        verbose_name="关联事件"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['page']),
            models.Index(fields=['event']), 
        ]
        verbose_name = "页面组件"
        verbose_name_plural = "页面组件"

    
    def __str__(self):
        return f"{self.get_component_type_display()}: {self.display_text[:20]}"

    def clean(self):
        """验证位置值"""
        if self.position < 0:
            raise ValidationError("位置不能为负数")
    
    def save(self, *args, **kwargs):
        """保存组件"""
        is_new = not self.pk
        
        # 新组件默认排在最后
        if is_new and self.position == 0:
            self.position = self.page.get_next_position()
        
        super().save(*args, **kwargs)
        
        # 保存后重新排序页面组件
        self.page.reorder_components()
    
    def delete(self, *args, **kwargs):
        """删除组件"""
        page = self.page
        super().delete(*args, **kwargs)
        # 删除后重新排序
        page.reorder_components()

# 游戏事件
class GameEvent(models.Model):
    EVENT_CATEGORIES = (
        ('player', '玩家操作'),
        ('item', '物品操作'),
        ('skill', '技能操作'),
        ('navigation', '导航操作'),
        ('system', '系统功能'),
    )
    
    name = models.CharField(max_length=128, unique=True, verbose_name="事件名称")
    description = models.TextField(blank=True, default='', verbose_name="事件描述")
    category = models.CharField(max_length=20, choices=EVENT_CATEGORIES, blank=True, null=True,default='player', verbose_name="事件类别")
    
    # 预定义函数选择
    FUNCTION_CHOICES = (
        ('player_heal', '治疗玩家'),
        ('player_add_gold', '添加金币'),
        ('player_teleport', '传送玩家'),
        ('item_add', '添加物品'),
        ('item_remove', '移除物品'),
        ('skill_learn', '学习技能'),
        ('navigate_page', '跳转页面'),
        ('system_save', '保存游戏'),
    )
    
    function_name = models.CharField(
        max_length=50,
        blank=True, 
        null=True,
        choices=FUNCTION_CHOICES,
        verbose_name="功能函数"
    )
    
    # 函数参数
    function_params = models.JSONField(
        blank=True, 
        null=True,
        verbose_name="函数参数"
    )
    
    # 状态机配置 (JSON格式)
    state_machine_config = models.JSONField(
        blank=True, 
        null=True,
        verbose_name="状态机配置"
    )
    
    # 结果处理
    success_message = models.TextField(blank=True, default='', verbose_name="成功消息")
    failure_message = models.TextField(blank=True, default='', verbose_name="失败消息")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    
    class Meta:
        verbose_name = "游戏事件"
        verbose_name_plural = "游戏事件"
        ordering = ['name']
        indexes = [
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.name

class GameObject:
    def __init__(self, obj):
        self.__dict__['obj'] = obj

    def __unicode__(self):
        return self.obj

    # def __getattribute__(self, item):
    # return self.obj.__getattribute__(item)
    def __repr__(self):
        return self.obj.__repr__()

    def __getattr__(self, item):
        if item == '__getattribute__':
            val = self.__getattribute__
        elif item == '__getattr__':
            val = self.__getattr__
        if item.startswith('__'):
            val = self.__getattribute__(item)
        if item in self.obj.__class__.__dict__:
            val = self.obj.__getattribute__(item)
        elif item in self.obj.__dict__:
            val = self.obj.__getattribute__(item)
        else:
            val = self.obj.get(item)
        # if item == u'name':
        # if not val or str(val) == u'0':
        # val = u'无名氏{}'.format(game_get(self.obj, 'id', 0))
        # t_val = str(game_get(self.obj, u'chenghao', u''))
        # if t_val and str(t_val) != u'0':
        # val = t_val + str(val)
        # if not val and item != 'message':
        #    return 0
        # elif str(val).isdigit():
        #    return int(val)
        # else:
        #     return val
        if not val and item != 'message':
            return 0
        elif str(val).replace(".", '').isdigit():
            if str(val).count(".") == 0:
                return int(val)
            elif str(val).count(".") == 1:
                val = float(val)
                return round(val,3)
            else:
                return val
        else:
            return val

class Player(models.Model):
    GENDER_CHOICES = (
        ('M', '男'),
        ('F', '女'),
        ('O', '其他'),
    )

    # 基础信息
    avatar = models.URLField('头像URL', blank=True, null=True)
    name = models.CharField('名称', max_length=50, unique=True)
    gender = models.CharField('性别', max_length=1, choices=GENDER_CHOICES)
    signature = models.CharField('个性签名', max_length=100, blank=True, default='')
    marriage = models.OneToOneField(
        'self', 
        verbose_name='婚姻关系',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='spouse_of'
    )
    
    # 核心属性
    level = models.PositiveIntegerField('等级', default=1, )
    current_exp = models.PositiveBigIntegerField('当前经验', default=0)
    max_exp = models.PositiveBigIntegerField('最大经验', default=0)
    current_hp = models.PositiveIntegerField('当前生命', default=100)
    max_hp = models.PositiveIntegerField('最大生命', default=100)
    min_attack = models.PositiveIntegerField('最小攻击', default=10)
    max_attack = models.PositiveIntegerField('最大攻击', default=20)
    min_defense = models.PositiveIntegerField('最小防御', default=5)
    max_defense = models.PositiveIntegerField('最大防御', default=10)
    agility = models.PositiveIntegerField('敏捷', default=10)
    linghunli = models.PositiveIntegerField('灵魂力', default=0)
    reputation = models.IntegerField('声望', default=0)
    douqi = models.IntegerField('斗气', default=1000)
    user = models.ForeignKey(
        'User', 
        null=True, blank=True, 
        verbose_name='关联用户', 
        on_delete=models.CASCADE, 
        related_name='players'
    )
    map = models.ForeignKey(
        'GameMap', 
        verbose_name='所在地图', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    gang = models.ForeignKey(
        'Gang', 
        verbose_name='所在帮派', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    # combat_power = models.PositiveIntegerField('综合战力', default=0)
    # offline_at = models.DateTimeField('离线时间', null=True, blank=True)
    
    last_active = models.DateTimeField('最后活动时间', auto_now=True)
    is_online = models.BooleanField('是否在线', default=True)
    # 动态扩展字段
    params = models.JSONField('动态属性', default=dict, blank=True)
    bag_capacity = models.IntegerField(default=100, verbose_name="背包容量")
    money = models.PositiveIntegerField('货币', default=0)
    big_money = models.PositiveIntegerField('金钱', default=0)
    # 元数据
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    
    class Meta:
        verbose_name = '玩家'
        verbose_name_plural = '玩家管理'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['level']),
            models.Index(fields=['last_active']),
        ]
    
   # 离线阈值（秒）
    SHORT_OFFLINE_THRESHOLD = 600  # 10分钟
    LONG_OFFLINE_THRESHOLD = 1800  # 30分钟
    MAX_LEVEL = 5

    def __str__(self):
        return f"{self.name}"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 缓存当前等级的经验值
        self.max_exp = self.calculate_max_exp(self.level)

    def calculate_max_exp(self, level):
        """计算指定等级所需的最大经验值（使用缓存优化）"""
        # 公式: (level +1)*(level +1)*(level +11)+200
        return (level + 10) ** 2 * (level + 25) + 200

    def update_attributes(self):
        """根据当前等级更新玩家属性"""
        # 线性增长公式示例（可根据游戏平衡性调整）
        self.max_hp = 100 + (self.level - 1) * 50
        self.min_attack = 10 + (self.level - 1) * 5
        self.max_attack = 20 + (self.level - 1) * 10
        self.min_defense = 5 + (self.level - 1) * 3
        self.max_defense = 10 + (self.level - 1) * 5
        self.douqi = 500 + (self.level - 1) * 50
        # 升级时恢复满生命值
        self.current_hp = self.max_hp
        
        # 更新最大经验缓存
        self.max_exp = self.calculate_max_exp(self.level)

    def gain_exp(self, exp):
        """增加玩家经验并触发升级检查（性能优化版）"""
        self.current_exp += exp
        
        # 预计算升级所需总经验（减少重复计算）
        required_exp = self.max_exp - self.current_exp
        
        # 批量升级处理（避免多次保存）
        while self.current_exp >= self.max_exp and self.level < self.MAX_LEVEL:
            # 保存剩余经验
            self.current_exp -= self.max_exp
            
            # 执行升级
            self.level += 1
            self.update_attributes()  # 更新属性
            
            # 计算下一级所需经验
            required_exp = self.calculate_max_exp(self.level)
        
        # 设置最终最大经验值
        self.max_exp = self.max_exp
        
        # 只保存一次数据库
        self.save(update_fields=[
            'level', 'current_exp', 'max_exp',
            'current_hp', 'max_hp',
            'min_attack', 'max_attack',
            'min_defense', 'max_defense',
            'last_active'
        ])
        
        return self.level

    def save(self, *args, **kwargs):
        """重写save方法确保初始经验值正确"""
        if not self.pk or self.max_exp == 0:
            self.max_exp = self.calculate_max_exp(self.level)
        super().save(*args, **kwargs)

    def get_bag_weight(self):
        """高效计算背包当前负重"""
        return self.inventory.aggregate(
            total_weight=models.Sum(
                models.F('item__weight') * models.F('count'),
                output_field=models.IntegerField()
            )
        )['total_weight'] or 0
    
    @property
    def bag_space_available(self):
        """可用背包空间"""
        return self.bag_capacity - self.get_bag_weight()

    def update_activity(self):
        """更新玩家活动时间并标记为在线"""
        self.last_active = timezone.now()
        self.is_online = True
        self.save(update_fields=['last_active', 'is_online'])
        
        # 更新缓存
        cache_key = f"player_online_{self.id}"
        cache.set(cache_key, True, 600)  # 缓存10分钟
        
        # # 触发在线事件
        # self._trigger_online_event()
    
    def check_offline_status(self):
        """检查玩家是否应该被标记为离线"""
        if not self.is_online:
            return False  # 已经是离线状态
        
        now = timezone.now()
        inactive_seconds = (now - self.last_active).total_seconds()
        
        if inactive_seconds >= self.LONG_OFFLINE_THRESHOLD:
            # 30分钟未活动，标记为离线
            self._set_offline(now)
            return True
        # elif inactive_seconds >= self.SHORT_OFFLINE_THRESHOLD:
        #     # 10分钟未活动，标记为离线
        #     self._set_offline(now)
        #     return True
        
        return False
    
    def move_to_map(self, map_id):
        """移动玩家到指定地图"""
        old_map_id = self.map_id
        self.map_id = map_id
        self.save(update_fields=['current_map'])
        
        # 清除地图缓存
        from .utils.cache_utils import invalidate_map_cache
        if old_map_id:
            invalidate_map_cache(old_map_id)
        invalidate_map_cache(map_id)

    def _set_offline(self, offline_time):
        """设置玩家为离线状态并处理离线事件"""
        self.is_online = False
        self.offline_at = offline_time
        self.save(update_fields=['is_online', 'offline_at'])
        
        # 更新缓存
        cache_key = f"player_online_{self.id}"
        cache.delete(cache_key)
        
        # # 触发离线事件
        # self._trigger_offline_event()
        
        logger.info(f"玩家 {self.name} (ID: {self.id}) 已离线")


    def total_attributes(self):
        """计算玩家总属性（基础属性+装备属性）"""
        # 基础属性
        attributes = {
            'max_hp': self.max_hp,
            'min_attack': self.min_attack,
            'max_attack': self.max_attack,
            'min_defense': self.min_defense,
            'max_defense': self.max_defense,
            'agility': self.agility,
            'linghunli': self.linghunli
        }
        
        # 累加装备属性
        for equipment in self.equipments.select_related('item'):
            attributes['max_hp'] += equipment.item.hp or 0
            attributes['min_attack'] += equipment.item.attack or 0
            attributes['max_attack'] += equipment.item.attack or 0
            attributes['min_defense'] += equipment.item.defense or 0
            attributes['max_defense'] += equipment.item.defense or 0
            attributes['agility'] += equipment.item.minjie or 0
            attributes['linghunli'] += equipment.item.linghunli or 0
        
        return attributes
    
    @property
    def status_display(self):
        """返回在线/离线状态文本"""
        return "在线" if self.is_online else "离线"
    
    # def update_activity(self):
    #     """更新玩家活动状态（设置为在线）"""
    #     # 如果当前是离线状态，则清除离线标记
    #     if not self.is_online:
    #         self.offline_at = None
    #         self.save(update_fields=['offline_at'])
    
    # def mark_offline(self):
    #     """标记玩家为离线状态"""
    #     if self.is_online:
    #         self.offline_at = timezone.now()
    #         self.save(update_fields=['offline_at'])
    
    @property
    def offline_duration(self):
        """计算离线持续时间（分钟）"""
        if not self.is_online:
            return int((timezone.now() - self.offline_at).total_seconds() / 60)
        return 0

    # 动态计算升级所需经验
    @property
    def next_level_exp(self):
        return 100 * (self.level ** 2)  # 升级公式：100 * 等级²
    
    @property
    def combat_power(self):
        """动态计算综合战力"""
        # 示例公式：攻击、防御、敏捷加权平均 + 等级加成
        attack_avg = (self.min_attack + self.max_attack) / 2
        defense_avg = (self.min_defense + self.max_defense) / 2
        return int(attack_avg * 1.5 + defense_avg * 1.2 + self.agility * 0.8 + self.linghunli * 1.6 + self.level * 10)


    @property
    def rank_title(self):
        """根据等级计算称号（如：一星斗者、七星斗圣）"""
        # 称号体系配置
        RANK_NAMES = ["斗之气", "斗者", "斗师", "大斗师","斗灵", "斗王", "斗皇", "斗宗", "斗尊", "半圣", "斗圣", "半帝", "斗帝"]
        STAR_NAMES = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "巅峰"]
        
        # 计算阶段和星级
        rank_index = (self.level) // 10
        star_level = self.level % 10  # 10级时显示10星（特殊处理）
        
        # 处理称号边界情况
        if rank_index >= len(RANK_NAMES):
            # 超过最高称号时使用最终称号
            plus_count = rank_index - len(RANK_NAMES) + 1
            rank_name = f"{RANK_NAMES[-1]}{'+' * plus_count}"
            
            # 整十级显示巅峰
            if star_level == 0:
                return f"{rank_name}巅峰"

            # 非整十级显示星级
            star_name = STAR_NAMES[star_level] if star_level < len(STAR_NAMES) else "十"
            return f"{star_name}星{rank_name}"
        # 处理正常称号
        rank_name = RANK_NAMES[rank_index]
        
        # 整十级显示为【xx巅峰】
        if star_level == 0:
            return f"{rank_name}巅峰"
        
        # 非整十级显示为【n星xx】
        star_name = STAR_NAMES[star_level-1] if star_level < len(STAR_NAMES) else "十"
        return f"{star_name}星{rank_name}"

    @property
    def rank_info(self):
        """返回称号的详细信息（用于API或前端展示）"""
        return {
            "title": self.rank_title,
            "level": self.level,
            "next_level_exp": self.next_level_exp,
            "progress_percentage": min(100, int(self.current_exp / self.next_level_exp * 100))
        }



# class GongFa(models.Model):
#     ELEMENT_CHOICES = [
#         ('fire', '火系'),
#         ('water', '水系'),
#         # 其他元素...
#     ]
#     name = models.CharField('功法名称', max_length=50, unique=True)
#     description = models.TextField('功法描述', blank=True)
#     level_requirement = models.PositiveIntegerField('等级要求', default=1)
#     cultivation_coef = models.FloatField('修炼系数', default=1.0)
#     element = models.CharField('属性', max_length=20, choices=ELEMENT_CHOICES, default='')
    
#     def __str__(self):
#         return self.name

#总伤害：(({u.lvl}*({r.100}+20)+{m.lvl}*8+({m.hurt_mod}*({m.lvl}+18)/6)+{u.gj}*8)-({r.o.lvl}+10)*8-{o.fy}*3)

class Skill(models.Model):
    """游戏技能表"""
    
    name = models.CharField('技能名称', max_length=50, unique=True)
    description = models.TextField('技能描述', blank=True, help_text="基础技能描述")
    level = models.PositiveSmallIntegerField('基础等级', default=1)
    battle_description = models.TextField(
        '战斗描述', 
        blank=True,
        help_text="战斗中使用时的描述文本，可使用{player}、{target}等占位符"
    )

    class Meta:
        verbose_name = '核心技能'
        verbose_name_plural = '核心技能'

    def __str__(self):
        return self.name

    # 实例方法定义成长规则
    def calculate_effect(self, level, effect_type):
        """计算指定等级的效果值"""
        base_value = self.get_base_effect(effect_type)
        
        # 不同效果类型使用不同成长规则
        growth_rules = {
            'attack': lambda l: base_value * (1.5 ** (l - 1)),  # 攻击指数成长
            'defense': lambda l: base_value * (1.2 ** (l - 1)), # 防御较慢成长
            'soul_cost': lambda l: base_value * (1.1 ** (l - 1)), # 消耗缓慢增加
            'vigor_cost': lambda l: base_value * (1.1 ** (l - 1))  # 消耗缓慢增加
        }
        
        # 获取特定技能的成长规则（可选）
        if self.name == "特殊技能":
            growth_rules['attack'] = lambda l: base_value * (2 ** (l - 1))
        
        return int(growth_rules.get(effect_type, lambda l: base_value)(level))


class PlayerSkill(models.Model):
    """玩家技能掌握表"""
    player = models.ForeignKey(
        'Player',
        verbose_name='玩家',
        on_delete=models.CASCADE,
        related_name='skills'
    )
    skill = models.ForeignKey(
        'Skill',
        verbose_name='关联技能',
        on_delete=models.CASCADE,
        related_name='playerskills'
    )

     # 当前等级和修炼值
    current_level = models.PositiveSmallIntegerField('当前等级', default=1)
    current_xp = models.PositiveIntegerField('当前经验值', default=0)
    max_xp = models.PositiveIntegerField('最大经验值', default=0)
    
    # 当前效果
    attack = models.SmallIntegerField('攻击加成', default=20)
    defense = models.SmallIntegerField('防御加成', default=5)
    linghunli = models.SmallIntegerField('灵魂力消耗', default=2)
    douqi = models.SmallIntegerField('斗气消耗', default=5)


    class Meta:
        verbose_name = '玩家技能'
        verbose_name_plural = '玩家技能'
        indexes = [
            models.Index(fields=['player', 'current_level']),
            models.Index(fields=['attack', 'defense']),
        ]

    def __str__(self):
        return f"{self.skill.name}"

    def save(self, *args, **kwargs):
        """创建时初始化效果值"""
        if not self.pk:  # 新建记录时初始化
            self.attack = self.skill.calculate_effect(1, 'attack')
            self.defense = self.skill.calculate_effect(1, 'defense')
            self.linghunli = self.skill.calculate_effect(1, 'linghunli')
            self.douqi = self.skill.calculate_effect(1, 'douqi')
        super().save(*args, **kwargs)
    
    @property
    def rank_display(self):
        """显示阶位名称"""
        rank_map = {
            1: "黄阶初级",
            2: "黄阶中级",
            3: "黄阶高级",
            4: "玄阶初级",
            5: "玄阶中级",
            6: "玄阶高级",
            7: "地阶初级",
            8: "地阶中级",
            9: "地阶高级",
            10: "天阶初级",
            11: "天阶中级",
            12: "天阶高级"
        }
        return rank_map.get(self.current_level, f"Lv.{self.current_level}")
    
    def add_xp(self, amount):
        """添加经验值并检查升级"""
        self.current_xp += amount
        self.save()  # 保存经验值
        
        # 检查是否可升级
        while self.can_upgrade:
            self.upgrade()
    
    @property
    def can_upgrade(self):
        """检查是否可以升级"""
        return (
            self.current_level < self.skill.max_level and 
            self.current_xp >= self.required_xp
        )
    
    def upgrade(self):
        """执行升级操作"""
        if not self.can_upgrade:
            return False
        
        # 扣除所需经验
        self.current_xp -= self.required_xp
        self.current_level += 1
        
        # 使用技能计算方法更新效果值
        self.attack = self.skill.calculate_effect(self.current_level, 'attack')
        self.defense = self.skill.calculate_effect(self.current_level, 'defense')
        self.linghunli = self.skill.calculate_effect(self.current_level, 'linghunli')
        self.douqi = self.skill.calculate_effect(self.current_level, 'douqi')
        
        self.save()
        return True


    @property
    def total_attributes(self):
        """实时计算玩家总属性（基础属性+装备属性）"""
        cache_key = f'player_attrs_{self.id}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        base_attrs = {
            'max_hp': self.max_hp,
            'min_attack': self.min_attack,
            'max_attack': self.max_attack,
            'min_defense': self.min_defense,
            'max_defense': self.max_defense,
            'agility': self.agility,
            'linghunli': self.linghunli
        }
        
        # 聚合所有装备属性
        equipment_attrs = self.equipments.aggregate(
            hp=Sum('item__hp'),
            attack=Sum('item__attack'),
            defense=Sum('item__defense'),
            minjie=Sum('item__minjie'),
            linghunli=Sum('item__linghunli')
        )
        
        # 合并属性
        attributes = {
            'max_hp': base_attrs['max_hp'] + (equipment_attrs['hp'] or 0),
            'min_attack': base_attrs['min_attack'] + (equipment_attrs['attack'] or 0),
            'max_attack': base_attrs['max_attack'] + (equipment_attrs['attack'] or 0),
            'min_defense': base_attrs['min_defense'] + (equipment_attrs['defense'] or 0),
            'max_defense': base_attrs['max_defense'] + (equipment_attrs['defense'] or 0),
            'agility': base_attrs['agility'] + (equipment_attrs['minjie'] or 0),
            'linghunli': base_attrs['linghunli'] + (equipment_attrs['linghunli'] or 0),
        }
        cache.set(cache_key, attributes, timeout=60)
        return attributes


class QuickSlot(models.Model):
    """极简高性能快捷键模型"""
    player_id = models.BigIntegerField(verbose_name='玩家ID', db_index=True)
    slot_index = models.PositiveSmallIntegerField(verbose_name='快捷键位置')
    skill_id = models.BigIntegerField(null=True, blank=True, verbose_name='技能ID')
    item_id = models.BigIntegerField(null=True, blank=True, verbose_name='物品ID')
    
    class Meta:
        verbose_name = '玩家快捷键'
        verbose_name_plural = '玩家快捷键'
        unique_together = [('player_id', 'slot_index')]
        indexes = [
            models.Index(fields=['player_id']),
        ]
        ordering = ['player_id', 'slot_index']

    def __str__(self):
        return f"玩家{self.player_id}的快捷键{self.slot_index}"
    
    @classmethod
    def get_player_quick_slots(cls, player_id):
        """获取玩家快捷键数据，使用缓存优化"""
        cache_key = f"quick_slots:{player_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        # 从数据库获取数据
        slots = list(cls.objects.filter(player_id=player_id).values(
            'slot_index', 'skill_id', 'item_id'
        ))
        
        # 设置缓存（5分钟）
        cache.set(cache_key, slots, 300)
        return slots
    
    @classmethod
    def update_slot(cls, player_id, slot_index, skill_id=None, item_id=None):
        """更新或创建快捷键"""
        # 更新数据库
        obj, created = cls.objects.update_or_create(
            player_id=player_id,
            slot_index=slot_index,
            defaults={
                'skill_id': skill_id,
                'item_id': item_id
            }
        )
        
        # 清除缓存
        cache_key = f"quick_slots:{player_id}"
        cache.delete(cache_key)
        
        return obj

# 帮派模型
class Gang(models.Model):
    name = models.CharField('帮派名称', max_length=50, unique=True)
    description = models.TextField('描述', blank=True)
    reputation = models.PositiveIntegerField('帮派声望', default=0)
    money = models.PositiveIntegerField('帮派资金', default=0)
    level = models.PositiveIntegerField('帮派等级', default=1)
    current_count = models.PositiveIntegerField(default=1, verbose_name="当前人数")  
    max_count = models.PositiveIntegerField(default=50, verbose_name="人数上限")  
    max_exp = models.PositiveIntegerField(default=10000, verbose_name="经验上限")  
    exp = models.PositiveIntegerField(default=0, verbose_name="当前经验")  
    location = models.CharField('所在地', max_length=100, blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    params = models.JSONField('扩展属性', default=dict, blank=True)
    icon = models.URLField('图标URL', blank=True, null=True)
    leader = models.ForeignKey(
        'Player',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leading_gang',
        verbose_name='帮主'
    )
    class Meta:
        verbose_name = '帮派'
        verbose_name_plural = '帮派管理'
    

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        """当前帮会人数"""
        return self.gang_members.count()

    def get_all_members_info(self):
        """获取帮派所有成员的详细信息（按贡献值降序排序）"""
        members = self.gang_members.all().select_related('player').order_by('-contribution', 'join_date')
        
        return [{
            'id': member.player.id,
            'name': member.player.name,
            'level': member.player.level,
            'position': member.get_position_display(),
            'contribution': member.contribution,
            'join_date': member.join_date.strftime("%Y-%m-%d %H:%M:%S")
        } for member in members]

    # 添加升级逻辑
    def level_up(self):
        if self.exp >= self.max_exp:
            self.level += 1
            self.exp -= self.max_exp
            self.max_exp = self.level * 10000  # 升级后经验上限增加
            self.max_count += 10  # 升级后人数上限增加
            self.save()
            return True
        return False

class GangMember(models.Model):  # 修正拼写
    POSITION_CHOICES = (
        ("bz", "帮主"),
        ("fb", "副帮主"),
        ("zl", "长老"),
        ("hf", "护法"),
        ("cy", "成员"),
    )
    
    player = models.ForeignKey('Player', on_delete=models.CASCADE, related_name='player')
    gang = models.ForeignKey('Gang', on_delete=models.CASCADE, related_name='gang_members')
    join_date = models.DateTimeField('加入时间', auto_now_add=True)
    position = models.CharField('职位', max_length=20, choices=POSITION_CHOICES, default='cy')
    contribution = models.PositiveIntegerField('贡献值', default=0)  # 新增贡献值字段
    
    class Meta:
        verbose_name = '帮派成员'
        verbose_name_plural = '帮派成员'
        unique_together = ('player', 'gang')
    
    def __str__(self):
        return f"{self.player.name}-{self.gang.name}({self.position})"

    def get_all_members_info(self):
        """获取帮派所有成员的详细信息（按贡献值降序排序）"""
        members = self.members.all().select_related('player').order_by('-contribution', 'join_date')
        
        return [{
            'id': member.player.id,
            'name': member.player.name,
            'level': member.player.level,
            'position': member.get_position_display(),
            'contribution': member.contribution,
            'join_date': member.join_date.strftime("%Y-%m-%d %H:%M:%S")
        } for member in members]


class GangApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', '审核中'),
        ('accepted', '已通过'),
        ('rejected', '已拒绝'),
        ('revoked', '已撤回'),
    )
    
    player = models.ForeignKey('Player', on_delete=models.CASCADE, related_name='gang_applications')
    gang = models.ForeignKey('Gang', on_delete=models.CASCADE, related_name='applications')
    applied_time = models.DateTimeField('申请时间', auto_now_add=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        verbose_name = '帮派申请'
        verbose_name_plural = '帮派申请'
        # unique_together = ('player', 'gang')  # 防止重复申请
        
    def __str__(self):
        return f"{self.player}->{self.gang}({self.status})"

# 队伍模型
class Team(models.Model):
    """队伍模型"""
    name = models.CharField('队伍名称', max_length=50, blank=True, null=True)
    leader = models.ForeignKey(
        'Player',
        verbose_name='队长',
        on_delete=models.SET_NULL,
        null=True,
        related_name='leading_teams'
    )
    max_size = models.PositiveSmallIntegerField('最大人数', default=5)
    need_approval = models.BooleanField('是否需要审批', default=False)
    
    class Meta:
        verbose_name = '队伍'
        verbose_name_plural = '队伍管理'
    
    def __str__(self):
        return self.name or f"队伍-{self.id}"
    
    @property
    def member_count(self):
        """当前队伍人数"""
        return self.members.count()
    
    def can_join(self):
        """检查是否可以加入队伍"""
        return self.member_count < self.max_size
    
    def add_member(self, player_id):
        """添加成员到队伍"""
        if not self.can_join():
            raise ValidationError("队伍已满")
            
        if TeamMember.objects.filter(player_id=player_id).exists():
            raise ValidationError("玩家已在其他队伍中")
            
        with transaction.atomic():
            member = TeamMember.objects.create(
                player_id=player_id,
                team=self,
                is_leader=(self.member_count == 0)  # 第一个成员成为队长
            )
            
            if member.is_leader:
                self.leader = player
                self.save()
                
            return member
    
    def get_all_members_info(self):
        """获取队伍所有成员的详细信息"""
        members = self.members.filter(is_leader=False).select_related('player').order_by('-is_leader', 'join_time')
        
        return [{
            'id': member.player.id,
            'name': member.player.name,
            'level': member.player.level,
            'is_leader': member.is_leader,
            'join_time': member.join_time,
            # 添加其他需要的字段...
        } for member in members]
    
    def remove_member(self, player_id):
        """从队伍移除成员"""
        member = self.members.filter(player_id=player_id).first()
        logger.info(f"尝试从队伍 {self.id} 移除玩家 {player_id}")
        if not member:
            raise ValidationError("玩家不在此队伍中")
            
        with transaction.atomic():
            is_leader = member.is_leader
            member.delete()
            
            # 如果移除的是队长，需要重新选举
            if is_leader and self.members.exists():
                new_leader = self.members.order_by('join_time').first()
                new_leader.is_leader = True
                new_leader.save()
                self.leader = new_leader.player
                self.save()
            elif not self.members.exists():
                # 队伍空了，删除队伍
                self.delete()


class TeamMember(models.Model):
    """队伍成员模型"""
    
    player = models.ForeignKey(
        'Player', 
        verbose_name='玩家', 
        on_delete=models.CASCADE,
        related_name='team_memberships'
    )
    team = models.ForeignKey(
        'Team', 
        verbose_name='队伍', 
        on_delete=models.CASCADE,
        related_name='members'
    )
    join_time = models.DateTimeField('加入时间', auto_now_add=True)
    # role = models.CharField('角色', max_length=20, choices=ROLE_CHOICES, blank=True, null=True)
    is_leader = models.BooleanField('是否队长', default=False)
    
    class Meta:
        verbose_name = '队伍成员'
        verbose_name_plural = '队伍成员'
        unique_together = ('player', 'team')
    
    def __str__(self):
        return f"{self.player.name} - {self.team}"

        
class ChatMessage(models.Model):
    # 类型说明：1-系统 2-世界 3-帮派 4-组队 5-私聊
    MESSAGE_TYPES = (
        (1, '系统'),
        (2, '世界'),
        (3, '私聊'),
        (4, '帮派'),
        (5, '组队'),
        
    )
    type_id = models.PositiveSmallIntegerField(verbose_name="类型", choices=MESSAGE_TYPES, db_index=True)
    sender = models.PositiveSmallIntegerField(verbose_name="发送者ID", null=True, blank=True, db_index=True)
    sender_name = models.CharField(verbose_name='发送人名称', max_length=50, null=True, blank=True)
    message = models.CharField(max_length=256, verbose_name="消息内容", null=True, blank=True)
    receiver = models.PositiveSmallIntegerField(verbose_name="接受者", null=True, blank=True, db_index=True)
    bangpai_id = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    duiwu_id = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


    class Meta:
        indexes = [
            models.Index(fields=['type_id', '-created_at']),
            models.Index(fields=['bangpai_id', '-created_at']),
            models.Index(fields=['sender', 'receiver', '-created_at']),
        ]
        verbose_name = '聊天消息'

    def __str__(self):
        return f"[{self.get_type_id_display()}]:{self.message}"





# class Gift(Item):
#     """礼物模型（继承自物品）"""
#     GIFT_TYPES = (
#         ('common', '普通礼物'),
#         ('special', '特殊礼物'),
#         ('event', '活动礼物'),
#     )
    
#     gift_type = models.CharField('礼物类型', max_length=20, choices=GIFT_TYPES)
#     effect_duration = models.PositiveIntegerField('效果持续时间(小时)', default=0)
    
#     class Meta:
#         verbose_name = '礼物'
#         verbose_name_plural = '礼物管理'


# class Pet(models.Model):
#     """宠物模型"""
#     name = models.CharField('名称', max_length=50)
#     owner = models.ForeignKey(
#         Player, 
#         verbose_name='主人', 
#         on_delete=models.CASCADE,
#         related_name='pets'
#     )
#     level = models.PositiveIntegerField('等级', default=1)
#     attack_bonus = models.PositiveIntegerField('攻击加成', default=0)
#     defense_bonus = models.PositiveIntegerField('防御加成', default=0)
#     hp_bonus = models.PositiveIntegerField('生命加成', default=0)
#     skills = JSONField('技能', default=list, blank=True)
#     is_active = models.BooleanField('是否激活', default=True)
    
#     class Meta:
#         verbose_name = '宠物'
#         verbose_name_plural = '宠物管理'
    
#     def __str__(self):
#         return f"{self.name} (Lv.{self.level})"


# class Mount(models.Model):
#     """坐骑模型"""
#     name = models.CharField('名称', max_length=50)
#     owner = models.ForeignKey(
#         Player, 
#         verbose_name='主人', 
#         on_delete=models.CASCADE,
#         related_name='mounts'
#     )
#     speed = models.PositiveIntegerField('速度', default=100)
#     stamina = models.PositiveIntegerField('耐力', default=100)
#     max_stamina = models.PositiveIntegerField('最大耐力', default=100)
#     agility_bonus = models.PositiveIntegerField('敏捷加成', default=0)
#     is_active = models.BooleanField('是否激活', default=True)
    
#     class Meta:
#         verbose_name = '坐骑'
#         verbose_name_plural = '坐骑管理'
    
#     def __str__(self):
#         return self.name


# class GiftLog(models.Model):
#     """礼物赠送记录"""
#     sender = models.ForeignKey(
#         Player, 
#         verbose_name='赠送者', 
#         on_delete=models.CASCADE,
#         related_name='sent_gifts'
#     )
#     receiver = models.ForeignKey(
#         Player, 
#         verbose_name='接收者', 
#         on_delete=models.CASCADE,
#         related_name='received_gifts'
#     )
#     gift = models.ForeignKey(
#         Gift, 
#         verbose_name='礼物', 
#         on_delete=models.CASCADE
#     )
#     message = models.CharField('留言', max_length=200, blank=True)
#     sent_at = models.DateTimeField('赠送时间', auto_now_add=True)
#     is_received = models.BooleanField('是否已接收', default=False)
    
#     class Meta:
#         verbose_name = '礼物记录'
#         verbose_name_plural = '礼物记录'
#         ordering = ['-sent_at']
    
#     def __str__(self):
#         return f"{self.sender} → {self.receiver}: {self.gift}"



class GameMapArea(models.Model):
    """地图区域"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True, default='')
    area_type = models.PositiveSmallIntegerField(default=0, verbose_name="区域类型",
        help_text="0=普通区域, 1=特殊区域, 2=隐藏区域"
    )

    class Meta:
        indexes = [
            models.Index(fields=['area_type']),
        ]
        verbose_name = '地图区域'

    def __str__(self):
        return self.name

class GameCity(models.Model):
    """城市模型"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True, default='')
    area = models.ForeignKey(
        'GameMapArea',
        related_name='cities',
        on_delete=models.CASCADE,
        verbose_name="所属区域"
    )
    
    class Meta:
        verbose_name = '游戏城市'
    
    def __str__(self):
        return f"{self.name} ({self.area.name})"

class GameMap(models.Model):
    """游戏地图模型"""
    name = models.CharField(max_length=100)
    desc = models.TextField(default='', blank=True)
    city = models.ForeignKey(
        'GameCity',
        null=True,
        blank=True,
        related_name='locations',
        on_delete=models.SET_NULL,
        verbose_name="所属城市"
    )
    # 方向连接
    north = models.ForeignKey(
        'self', null=True, blank=True, 
        related_name='south_link', 
        on_delete=models.SET_NULL,
        verbose_name="北向连接"
    )
    south = models.ForeignKey(
        'self', null=True, blank=True, 
        related_name='north_link', 
        on_delete=models.SET_NULL,
        verbose_name="南向连接"
    )
    east = models.ForeignKey(
        'self', null=True, blank=True, 
        related_name='west_link', 
        on_delete=models.SET_NULL,
        verbose_name="东向连接"
    )
    west = models.ForeignKey(
        'self', null=True, blank=True, 
        related_name='east_link', 
        on_delete=models.SET_NULL,
        verbose_name="西向连接"
    )
    
    # 游戏属性
    is_city = models.BooleanField(default=False, verbose_name="是否城内")
    is_safe_zone = models.BooleanField(default=False, verbose_name="安全区")
    refresh_time = models.IntegerField(
        default=300, 
        verbose_name="刷新时间(秒)",
        help_text="NPC和物品的刷新间隔"
    )
    
    # 动态属性
    params = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="扩展属性",
        help_text="存储动态变化的游戏数据"
    )
    
    class Meta:
        # 添加索引提高查询效率
        indexes = [
            models.Index(fields=['is_safe_zone']),
            models.Index(fields=['is_city']),
        ]
        verbose_name = '游戏地图'
    
    def __str__(self):
        # return f"{self.name} ({self.city.name if self.city else '无城市'})"
        return f"{self.name}(ID:{self.id})"
    
    def get_adjacent_maps(self):
        """获取所有相邻地图"""
        return {
            'north': self.north,
            'south': self.south,
            'east': self.east,
            'west': self.west
        }
    
    def save(self, *args, **kwargs):
        """重写save方法，确保双向连接一致性"""
        super().save(*args, **kwargs)
        
        # 确保北向南连接一致性
        if self.north and self.north.south != self:
            self.north.south = self
            self.north.save()
            
        # 确保南向北连接一致性
        if self.south and self.south.north != self:
            self.south.north = self
            self.south.save()
            
        # 确保东向西连接一致性
        if self.east and self.east.west != self:
            self.east.west = self
            self.east.save()
            
        # 确保西向东连接一致性
        if self.west and self.west.east != self:
            self.west.east = self
            self.west.save() 

        super().save(*args, **kwargs)
        # 清除自身和相邻地图的缓存
        from .utils.cache_utils import invalidate_map_cache
        invalidate_map_cache(self.id)
        for direction in ['north', 'south', 'east', 'west']:
            adj_map = getattr(self, direction)
            if adj_map:
                invalidate_map_cache(adj_map.id)

    def get_direction_to(self, target_map):
        """获取到目标地图的方向"""
        if self.north == target_map:
            return 'north'
        elif self.south == target_map:
            return 'south'
        elif self.east == target_map:
            return 'east'
        elif self.west == target_map:
            return 'west'
        return None

    def get_adjacent_map_ids(self):
        """获取相邻地图ID（缓存优化）"""
        cache_key = f"adjacent_maps_{self.id}"
        adjacent_ids = cache.get(cache_key)
        
        if adjacent_ids is None:
            adjacent_ids = {
                'north': self.north_id,
                'south': self.south_id,
                'east': self.east_id,
                'west': self.west_id
            }
            cache.set(cache_key, adjacent_ids, MAP_CACHE_TIMEOUT)
        
        return adjacent_ids


class GameNPC(models.Model):
    NPC_TYPES = (
        ('npc', 'NPC'),
        ('monster', '怪物'),
        ('quest', '任务NPC'),
        ('shop', '商店NPC'),
        # 可扩展其他类型
    )
    npc_type = models.CharField(max_length=20, choices=NPC_TYPES, verbose_name="类型")
    name = models.CharField(max_length=100, verbose_name="名称")  # 通用属性
    description = models.TextField(default='', verbose_name="描述")          # 通用属性
    level = models.IntegerField(default=1, verbose_name="等级")   # 通用属性
    # map = models.ForeignKey('GameMap', null=True, blank=True, on_delete=models.CASCADE, verbose_name="地图")  # 通用属性
    # map_id = models.PositiveIntegerField(null=True, blank=True, db_index=True, verbose_name="地图")
    
    # ---- 怪物专属字段 (nullable) ----
    hp = models.IntegerField(null=True, blank=True, verbose_name="生命值")
    attack = models.IntegerField(null=True, blank=True, verbose_name="攻击力")
    defense = models.IntegerField(null=True, blank=True, verbose_name="防御力")
    exp_reward = models.IntegerField(default=0, verbose_name="经验奖励")
    gold_reward = models.IntegerField(default=0, verbose_name="金钱奖励")
    drop_items = models.JSONField(null=True, blank=True, verbose_name="物品掉落")  # 掉落物品JSON
    is_boss = models.BooleanField(default=False, verbose_name="是否BOSS") 
    
    # ---- NPC专属字段 (nullable) ----
    dialogue = models.TextField(null=True, blank=True, verbose_name="对话文本")    # 对话文本
    shop_items = models.JSONField(null=True, blank=True, verbose_name="出售物品" )  # 商店物品
    show_conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text="满足条件才显示的JSON配置",
        verbose_name="显示条件"
    )

    class Meta:
        indexes = [
            models.Index(fields=['npc_type']),  # 组合索引
        ]
        verbose_name = '游戏NPC'
        verbose_name_plural = '游戏NPC管理'

    def __str__(self):
        return f"{self.name}(ID:{self.id})"

    def save(self, *args, **kwargs):
        """重写save方法，清除相关缓存"""
        # 保存前记录旧值（用于位置变化时清除旧地图缓存）
        from .utils.cache_utils import invalidate_map_cache,invalidate_npc_cache
        old_map_id = None
        if self.pk:
            old_instance = GameNPC.objects.filter(pk=self.pk).first()
            if old_instance:
                old_map_id = old_instance.map_id
        
        super().save(*args, **kwargs)
        
        # 清除NPC自身缓存
        invalidate_npc_cache(self.id)
        
        # 清除相关地图缓存
        # if self.map_id:
        #     self.invalidate_map_cache(self.map_id)
        
        # 如果位置变化，清除旧地图缓存
        # if old_map_id and old_map_id != self.map_id:
        #     self.invalidate_map_cache(old_map_id)

class NPCDropList(models.Model):
    npc = models.ForeignKey(
        'GameNPC', 
        on_delete=models.CASCADE, 
        related_name='droplist',
        verbose_name="NPC"
    )
    item = models.ForeignKey(
        'Item', 
        on_delete=models.CASCADE, 
        related_name='npcdrop',
        verbose_name="掉落物品"
    )
    gailv = models.IntegerField(default=50, verbose_name='掉落概率')
    count = models.IntegerField(default=1, verbose_name='掉落数量')

    class Meta:
        verbose_name = 'NPC掉落设置'
    
    def __str__(self):
        return f"{self.npc.name}({self.item.name})"

    def save(self, *args, **kwargs):
        """保存时清除相关缓存"""
        super().save(*args, **kwargs)
        # 清除怪物掉落缓存
        cache.delete(f"npc_drop_info_{self.npc_id}")
        cache.delete(f"npc:{self.npc_id}:info")
    
    def delete(self, *args, **kwargs):
        """删除时清除相关缓存"""
        npc_id = self.npc_id
        super().delete(*args, **kwargs)
        cache.delete(f"npc_drop_info_{npc_id}")
        cache.delete(f"npc:{npc_id}:info")


class GameMapNPCManager(models.Manager):
    def for_map(self, map_id):
        """获取指定地图的NPC"""
        return self.filter(map_id=map_id).select_related('npc').only(
            'id', 'count', 'npc__name', 'npc__npc_type', 'npc__level'
        )

class GameMapNPC(models.Model):
    """地图放置NPC"""

    npc_id = models.PositiveIntegerField(db_index=True)
    map_id = models.PositiveIntegerField(blank=True, null=True, db_index=True)
    count = models.IntegerField(default=1, verbose_name="数量")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="生成时间")
    # refresh_time = models.IntegerField(default=300, verbose_name="刷新时间")
    next_refresh_time = models.IntegerField(default=3600, verbose_name="下次刷新时间")
    
    objects = GameMapNPCManager()
    
    class Meta:
        indexes = [
            models.Index(fields=['map_id']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = '地图NPC'

    def __str__(self):
        return f"map-{self.map_id}/npc-{self.npc_id}"

    def save(self, *args, **kwargs):
        """重写save方法，清除地图缓存"""
        super().save(*args, **kwargs)
        from .utils.cache_utils import invalidate_map_cache,invalidate_npc_cache
        # invalidate_map_cache(self.map_id)
        # invalidate_npc_cache(self.npc_id)
        if self.map_id:
            # invalidate_map_cache(self.map_id)
            keys = [
                f"map_context_{self.map_id}",
                f"adjacent_maps_{self.map_id}"
            ]
            cache.delete_many(keys)



class GameMapItemManager(models.Manager):
    def active_for_map(self, map_id):
        """获取地图上的有效物品"""
        return self.filter(
            map_id=map_id,
            expire_time__gt=timezone.now(),
            picked_by__isnull=True
        ).select_related('item').only(
            'id', 'item__name', 'count'
        )
    
    def create_item(self, map_id, item_id, count, expire_minutes=30):
        """创建地图物品"""
        expire_time = timezone.now() + datetime.timedelta(minutes=expire_minutes)
        return self.create(
            map_id=map_id,
            item_id=item_id,
            count=count,
            expire_time=expire_time
        )

class Item(models.Model):
    """
    游戏物品表 - 单表设计所有物品类型
    """
    # 基础属性（所有物品共享）
    item_type = (
        (1, '装备'),
        (2, '药品'),
        (3, '物品'),
        (4, '宝石'),
        (5, '时装'),
        (6, '其他'),
    )
    name = models.CharField(max_length=50, db_index=True, verbose_name="名称")  # 名称添加索引
    description = models.TextField(default='', blank=True, null=True, verbose_name="描述")  # 描述
    category = models.PositiveSmallIntegerField(default=3, choices=item_type, db_index=True, verbose_name="分类")  # 类别添加索引
    level = models.IntegerField(default=1, verbose_name="等级")
    weight = models.IntegerField(default=1, verbose_name="负重")  # 负重
    price = models.IntegerField(default=100, verbose_name="价格")
    jiaoyi = models.BooleanField(default=True, verbose_name="可交易")  # 是否可交易
    zengsong = models.BooleanField(default=True, verbose_name="可赠送")  # 是否可赠送
    duidie  = models.BooleanField(default=False, verbose_name="可堆叠")  # 是否可堆叠
    
    # 基础属性（装备和药品共享，但含义不同）
    attack = models.IntegerField(default=0, verbose_name="攻击")       # 攻击加成（装备）/造成伤害（药品）
    defense = models.IntegerField(default=0, verbose_name="防御")      # 防御加成
    minjie = models.IntegerField(default=0, verbose_name="敏捷")      # 敏捷加成
    linghunli = models.IntegerField(default=0, verbose_name="灵魂力")   # 灵魂力加成
    hp = models.IntegerField(default=0, verbose_name="生命")         # 生命加成（装备）/回复量（药品）
    
    zhuangbei_position = (
        (1, '武器'),
        (2, '头盔'),
        (3, '衣服'),
        (4, '裤子'),
        (5, '腰带'),
        (6, '鞋子'),
        (7, '饰品'),
        (8, '戒指'),
        (9, '项链'),
    )

    # 装备特有属性
    equipment_post = models.PositiveSmallIntegerField(default=1, blank=True, null=True, choices=zhuangbei_position, verbose_name="装备位置")
    set_id = models.IntegerField(default=0, db_index=True, verbose_name="套装ID")  # 套装ID（0表示非套装）
    set_bonus = models.JSONField(default=dict, blank=True, verbose_name="套装加成")  # 套装加成属性
    # 示例set_bonus: {"attack": 10, "defense": 5, "set_count": 2}

    RANK_CHOICES = (
        (1, '一品'),
        (2, '二品'),
        (3, '三品'),
        (4, '四品'),
        (5, '五品'),
        (6, '六品'),
        (7, '七品'),
        (8, '八品'),
        (9, '九品'),
    )
    rank = models.IntegerField(default=1, choices=RANK_CHOICES, db_index=True, verbose_name="品阶")

    max_naijiu = models.IntegerField(default=0, blank=True, null=True, verbose_name="最大耐久")  # 最大耐久
    is_kaikong = models.BooleanField(default=False, verbose_name="是否可开孔")  # 是否开孔
    max_kaikong = models.IntegerField(default=0, blank=True, null=True, verbose_name="最大开孔数量")  # 最大开孔数量
    max_qianghua = models.IntegerField(default=10, verbose_name="最大强化等级") #最大强化等级
    # 动态属性
    attrs = models.JSONField(default=dict, blank=True, verbose_name="动态属性")
    # 示例存储内容：
    # 武器: {"critical_rate": 0.1, "attack_speed": 1.2}
    # 宝石: {"element_type": "fire", "element_power": 15}
    

    class Meta:
        db_table = 'game_items'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['equipment_post']),  # 装备类型索引
        ]
        verbose_name="游戏物品"
    
    def __str__(self):
        # return f"{self.get_category_display()}:{self.name}"
        return f"{self.name}(ID:{self.id})"

    def is_equipment(self):
        """判断是否为装备"""
        return self.category == 'EQUIPMENT'
    
    def get_base_attributes(self):
        """获取基础属性字典"""
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'level': self.level,
            'weight': self.weight,
            'price': self.price,
            'jiaoyi': self.jiaoyi,
            'zengsong': self.zengsong,
        }
    
    def get_all_attributes(self):
        """获取物品所有属性（基础+扩展）"""
        attrs = self.get_base_attributes()
        
        # 添加数值属性
        attrs.update({
            'attack': self.attack,
            'defense': self.defense,
            'minjie': self.minjie,
            'linghunli': self.linghunli,
            'hp': self.hp,
        })
        
        # 添加装备特有属性
        if self.is_equipment():
            attrs.update({
                'equipment_post': self.equipment_post,
                'max_naijiu': self.max_naijiu,
                'is_kaikong': self.is_kaikong,
                'kaikong_count': self.kaikong_count,
            })
        
        # 添加动态属性
        attrs.update(self.extra_attributes)
        
        return attrs

    def save(self, *args, **kwargs):
        """重写save方法，清除地图缓存"""
        super().save(*args, **kwargs)
        # from .utils.cache_utils import invalidate_map_cache
        # invalidate_map_cache(self.map_id)
    
    def delete(self, *args, **kwargs):
        """重写delete方法，清除地图缓存"""
        map_id = self.map_id
        super().delete(*args, **kwargs)
        # from .utils.cache_utils import invalidate_map_cache
        # invalidate_map_cache(map_id)




class GameMapItem(models.Model):
    ### 地图物品 ###
    item = models.ForeignKey(
        'Item', 
        on_delete=models.CASCADE, 
        related_name='map_item',
        verbose_name="物品"
    )
    map_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="所在地图", db_index=True)
    count = models.IntegerField(default=1, verbose_name="数量")
    picked_by = models.PositiveIntegerField(null=True, blank=True, verbose_name="拾取者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="生成时间")
    expire_time = models.DateTimeField(null=True, blank=True, verbose_name="消失时间")
    
    class Meta:
        indexes = [
            models.Index(fields=['map_id']),
            models.Index(fields=['expire_time']),
        ]
        verbose_name = '地图物品实例'

    def __str__(self):
        return f"{self.item.name}(m-{self.map_id})" 

    def save(self, *args, **kwargs):
        """保存时清除相关地图缓存"""
        # 保存前记录旧地图ID（用于位置变化时清除旧地图缓存）
        old_map_id = None
        if self.pk:
            old_map = GameMapItem.objects.filter(pk=self.pk).values('map_id').first()
            old_map_id = old_map['map_id'] if old_map else None
        
        super().save(*args, **kwargs)
        
        # 清除新地图缓存
        if self.map_id:
            from .utils.cache_utils import invalidate_map_cache
            invalidate_map_cache(self.map_id)
            
            keys = [
                f"map_context_{self.map_id}",
                f"adjacent_maps_{self.map_id}"
            ]
            cache.delete_many(keys)
        
        # 如果位置变化，清除旧地图缓存
        if old_map_id and old_map_id != self.map_id:
            # invalidate_map_cache(old_map_id)
            keys = [
                f"map_context_{old_map_id}",
                f"adjacent_maps_{old_map_id}"
            ]
            cache.delete_many(keys)
    
    def delete(self, *args, **kwargs):
        """删除时清除相关地图缓存"""
        map_id = self.map_id
        super().delete(*args, **kwargs)
        from .utils.cache_utils import invalidate_map_cache
        if map_id:
            invalidate_map_cache(map_id)


class PlayerItem(models.Model):
    """玩家拥有的物品"""
    player = models.ForeignKey(
        'Player', 
        on_delete=models.CASCADE, 
        related_name='inventory',
        db_index=True  # 按玩家ID快速查询
    )
    item = models.ForeignKey(
        'Item',  # 关联基础物品定义
        on_delete=models.CASCADE,
        db_index=True  # 按物品类型快速查询
    )
    category = models.PositiveSmallIntegerField(
        default=3, 
        choices=Item.item_type, 
        db_index=True,  
        verbose_name="物品类型"
    )
    equipment_post = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="装备位置")
    count = models.IntegerField(default=1)  # 数量（堆叠物品）
    is_bound = models.BooleanField(default=False)  # 是否已绑定
    is_equipped = models.BooleanField(default=False, db_index=True) # 是否已装备
    # 属性（装备和药品共享，但含义不同）
    hp = models.IntegerField(default=0, verbose_name="生命")         # 生命加成（装备）/回复量（药品）
    attack = models.IntegerField(default=0, verbose_name="攻击")       # 攻击加成（装备）/造成伤害（药品）
    defense = models.IntegerField(default=0, verbose_name="防御")      # 防御加成
    minjie = models.IntegerField(default=0, verbose_name="敏捷")      # 敏捷加成
    linghunli = models.IntegerField(default=0, verbose_name="灵魂力")   # 灵魂力加成


    naijiu = models.IntegerField(default=100, null=True, blank=True)  # 当前耐久
    max_naijiu = models.IntegerField(default=100, null=True, blank=True)  # 最大耐久
    qianghua_level = models.IntegerField(default=0)  # 强化等级
    kaikong_count = models.IntegerField(default=0, blank=True, null=True, verbose_name="开孔数量")  # 开孔数量
    baoshi = models.JSONField(default=list, blank=True)  # 镶嵌的宝石ID列表
    # 药品特有属性（若为药品）

    expiration_time = models.DateTimeField(null=True, blank=True)  # 过期时间
    attrs = models.JSONField(default=dict, blank=True)  # 动态属性

    class Meta:
        db_table = 'game_player_item'
        indexes = [
            models.Index(fields=['player', 'is_equipped']),  # 快速玩家物品
            models.Index(fields=['item', 'is_bound']),
            models.Index(fields=['player', 'category']),
        ]
        verbose_name="玩家物品"

    def __str__(self):
        return f"{self.player.name}的 {self.item.name}"

    def use(self, target=None):
        """使用物品逻辑"""
        if self.item.category == 'CONSUMABLE':
            # 处理消耗品逻辑
            return self._use_consumable(target)
        elif self.item.category == 'EQUIPMENT':
            # 处理装备逻辑
            return self._equip(target)
        else:
            return False, "无法使用该物品类型"

    @property
    def item_weight(self):
        """计算单个物品的总重量（考虑数量和强化）"""
        base_weight = self.item.weight
        # 示例：强化可能增加重量
        weight_multiplier = 1.0 + (self.qianghua_level * 0.05)
        return base_weight * weight_multiplier * self.count

    @classmethod
    def get_player_total_weight(cls, player):
        """计算玩家当前背包总重量"""
        # 使用数据库聚合函数优化计算
        from django.db.models import Sum
        
        total_weight = cls.objects.filter(
            player=player,
            is_equipped=False  # 只计算背包中的物品
        ).annotate(
            item_total_weight=Sum('item__weight') * Sum('count')
        ).values_list('item_total_weight', flat=True).first()
        
        return total_weight or 0

    @classmethod
    def add_item(cls, player, item_id, count=1, is_bound=False, **kwargs):
        """添加物品到背包（同步基础字段）"""
        from django.db import transaction
        
        try:
            with transaction.atomic():
                # 获取物品基础信息（带锁）
                item = Item.objects.select_for_update().get(id=item_id)
                
                # 先检查负重限制
                if not cls.can_add_item(player, item, count):
                    return False, "背包负重已满"
                
                # 尝试堆叠已有物品（仅处理可堆叠物品）
                if item.duidie:
                    existing_item = cls.objects.filter(
                        player=player,
                        item=item,
                        is_equipped=False,
                        is_bound=is_bound,
                        # 确保堆叠物品属性一致
                        hp=item.hp,
                        attack=item.attack,
                        defense=item.defense,
                        minjie=item.minjie,
                        linghunli=item.linghunli
                    ).select_for_update().first()
                    
                    if existing_item:
                        # 计算实际可堆叠数量
                        available_space = player.bag_capacity - existing_item.count
                        stack_amount = min(count, available_space)
                        
                        # 更新堆叠
                        existing_item.count += stack_amount
                        existing_item.save(update_fields=['count'])
                        
                        # 如果有剩余物品，递归添加
                        remaining = count - stack_amount
                        if remaining > 0:
                            return cls.add_item(player, item_id, remaining, **kwargs)
                        
                        return True, "物品已堆叠"
                
                # 创建新物品并同步基础字段
                new_item = cls(
                    player=player,
                    item=item,
                    count=count,
                    is_equipped=False,
                    is_bound=is_bound,
                    # 同步基础属性
                    category=item.category,
                    equipment_post=item.equipment_post,
                    hp=item.hp,
                    attack=item.attack,
                    defense=item.defense,
                    minjie=item.minjie,
                    linghunli=item.linghunli,
                    # 初始化装备相关属性
                    naijiu=item.max_naijiu,  # 耐久初始化为最大值
                    max_naijiu=item.max_naijiu,
                    qianghua_level=0,  # 强化等级初始为0
                    kaikong_count=0,  # 开孔数量初始为0
                    # 传递额外参数
                    **kwargs
                )
                
                # 设置特殊字段
                if item.category == 1:  # 装备
                    # 耐久度处理
                    if item.max_naijiu:
                        new_item.naijiu = item.max_naijiu
                elif item.category == 2:  # 药品
                    # 设置过期时间（如果有）
                    if 'expiration_time' not in kwargs:
                        # 默认药品有效期30天
                        new_item.expiration_time = timezone.now() + timedelta(days=30)
                
                new_item.save()
                return True, "物品已添加到背包"
        
        except Item.DoesNotExist:
            return False, "物品不存在"
        except Exception as e:
            logger.error(f"添加物品失败: {e}")
            return False, "添加物品失败，请稍后再试"

    @classmethod
    def remove_item(cls, player, player_item_id, count=1):
        """高性能移除物品实现"""
        
        with transaction.atomic():
            # 步骤1: 验证总量是否足够 (避免无效操作)
            total_count = cls.objects.filter(
                player=player,
                id=player_item_id
            ).aggregate(total=models.Sum('count'))['total'] or 0
            
            if total_count < count:
                return False
            
            # 步骤2: 批量获取并锁定相关记录
            items_to_process = list(cls.objects.filter(
                player=player,
                id=player_item_id
            ).select_for_update())
            
            # 步骤3: 内存中计算处理方案
            to_delete = []
            to_update = []
            remaining = count
            
            for instance in items_to_process:
                if instance.count <= remaining:
                    # 标记整个实例删除
                    to_delete.append(instance.id)
                    remaining -= instance.count
                else:
                    # 标记部分减少
                    instance.count -= remaining
                    to_update.append(instance)
                    remaining = 0
                    break  # 提前终止循环
                
                if remaining == 0:
                    break
            
            # 步骤4: 批量执行数据库操作
            if to_delete:
                cls.objects.filter(id__in=to_delete).delete()
            
            if to_update:
                # 批量更新减少数量
                cls.objects.bulk_update(to_update, ['count'])
            
            return True
    
    @classmethod
    def can_add_item(cls, player, item, count):
        """检查是否可以添加物品（考虑负重）"""
        # 计算物品总负重
        item_weight = item.weight * count
        
        # 获取玩家当前负重
        current_burden = PlayerItem.objects.filter(
            player=player,
            is_equipped=False
        ).aggregate(
            total_weight=models.Sum(models.F('item__weight') * models.F('count'))
        )['total_weight'] or 0
        
        # 计算新总负重
        new_burden = current_burden + item_weight
        
        # 检查是否超过背包容量
        return new_burden <= player.bag_capacity

    # def calculate_equipment_attributes(self):
    #     """计算装备的实际属性（含强化、套装等加成）"""
    #     if not self.is_equipped or not self.item.is_equipment():
    #         return {}
            
    #     # 基础属性
    #     attrs = {
    #         'attack': self.item.attack,
    #         'defense': self.item.defense,
    #         'minjie': self.item.minjie,
    #         'linghunli': self.item.linghunli,
    #         'hp': self.item.hp,
    #     }
        
    #     # # 强化加成
    #     # enhance_bonus = self.item.get_enhance_bonus(self.qianghua_level)
    #     # for attr, value in enhance_bonus.items():
    #     #     attrs[attr] = attrs.get(attr, 0) + value
            
    #     # 宝石加成
    #     for gem in self.get_socketed_gems():
    #         gem_attrs = gem.get_attributes()
    #         for attr, value in gem_attrs.items():
    #             attrs[attr] = attrs.get(attr, 0) + value
                
    #     # 套装加成（在Player类中统一处理）
        
    #     return attrs
    
    # def update_cached_attributes(self):
    #     """更新缓存的装备属性"""
    #     self.cached_attributes = self.calculate_equipment_attributes()
    #     self.last_updated_stats = timezone.now()
    #     self.save(update_fields=['cached_attributes', 'last_updated_stats'])

    # def equip(self, player):
    #     """穿戴装备"""
    #     from django.db import transaction
        
    #     with transaction.atomic():
    #         # 检查是否为装备
    #         if not self.item.is_equipment():
    #             return False, "该物品不是装备"
                
    #         # 检查是否已装备
    #         if self.is_equipped:
    #             return False, "该装备已穿戴"
                
    #         # 检查装备位置是否已被占用
    #         if self.item.equipment_type:
    #             existing_equipment = ItemInstance.objects.filter(
    #                 player=player,
    #                 is_equipped=True,
    #                 equip_position=self.item.equipment_type
    #             ).first()
                
    #             if existing_equipment:
    #                 # 先卸下已有装备
    #                 existing_equipment.unequip(player)
            
    #         # 穿戴装备
    #         self.is_equipped = True
    #         self.equip_position = self.item.equipment_type
    #         self.position = -1  # 从背包移除
    #         self.update_cached_attributes()  # 更新属性缓存
    #         self.save()
            
    #         # 刷新玩家属性缓存
    #         player.refresh_equipment_bonus()
            
    #         return True, f"已装备 {self.item.name}"
    
    # def unequip(self, player):
    #     """卸下装备"""
    #     from django.db import transaction
        
    #     with transaction.atomic():
    #         # 检查是否已装备
    #         if not self.is_equipped:
    #             return False, "该装备未穿戴"
                
    #         # 检查背包空间
    #         if not ItemInstance.can_add_item(player, self.item, 1):
    #             return False, "背包空间不足"
                
    #         # 卸下装备
    #         self.is_equipped = False
    #         self.equip_position = None
    #         self.position = ItemInstance._find_empty_position(player)  # 放入背包
    #         self.update_cached_attributes()  # 更新属性缓存（变为0）
    #         self.save()
            
    #         # 刷新玩家属性缓存
    #         player.refresh_equipment_bonus()
            
    #         return True, f"已卸下 {self.item.name}"

class PlayerEquipment(models.Model):
    """玩家穿在身上的装备"""
    player = models.ForeignKey(
        'Player', 
        on_delete=models.CASCADE,
        related_name='equipments',
        db_index=True
    )
    position = models.PositiveSmallIntegerField(
        default=1, 
        choices=Item.zhuangbei_position,
        db_index=True
    )
    item = models.ForeignKey(
        'PlayerItem', 
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='equipped_in'
    )
    
    # 套装加成属性
    hp = models.IntegerField(default=0, verbose_name="生命")         # 生命加成（装备）
    attack = models.IntegerField(default=0, verbose_name="攻击")       # 攻击加成（装备）
    defense = models.IntegerField(default=0, verbose_name="防御")      # 防御加成
    minjie = models.IntegerField(default=0, verbose_name="敏捷")      # 敏捷加成
    linghunli = models.IntegerField(default=0, verbose_name="灵魂力")   # 灵魂力加成

    class Meta:
        db_table = 'game_player_equipment'
        unique_together = (('player', 'position'),)  # 每个槽位唯一
        indexes = [
            models.Index(fields=['player', 'position']),
        ]
        verbose_name = '玩家装备'
        verbose_name_plural = '玩家装备'
        
    def __str__(self):
        return f"{self.player.name}'s {self.get_slot_display()}"

    
    # def is_expired(self):
    #     """检查物品是否过期"""
    #     if self.is_expired:
    #         return True
    #     if self.expire_time and timezone.now() > self.expire_time:
    #         self.is_expired = True
    #         self.save(update_fields=['is_expired'])
    #         return True
    #     return False

# class GameMapItem(models.Model):
#     """地图放置物品"""
#     id = models.AutoField(primary_key=True)
#     map_id = models.CharField(max_length=20, default=0, db_index=True)  # 归属地图
#     npc_id = models.CharField(max_length=20, default=0, db_index=True)  # 归属NPC
#     item_id = models.CharField(max_length=20, default=0, db_index=True)  # 放置物品
#     item_code = models.TextField(default=0)  # 物品数量

class HeCheng(models.Model):
    """合成"""
    item = models.OneToOneField(
        Item,
        on_delete=models.CASCADE,
        help_text="图纸物品",
        null=True,
        blank=True,
        related_name='hecheng'
    )
    required_materials = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="所需材料",
        help_text="所需材料: {'item_id1':5, 'item_id2':3}"
    )
    success_rate = models.PositiveSmallIntegerField(
        default=80,
        help_text="成功率%"
    )
    result_item = models.ForeignKey(
        'Item',
        on_delete=models.CASCADE,
        related_name='blueprints',
        help_text="产出的装备"
    )
    forger = models.ForeignKey(
        'User', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='forging_records',
        verbose_name="锻造师"
    )

    
    def __str__(self):
        return f"{self.item.name} 图纸"


class GameBase(models.Model):
    """游戏基础属性表"""
    STATUS_CHOICES = [
        ('kfz', '开发中'),
        ('whz', '维护中'),
        ('nc', '内测种'),
        ('gc', '公测中'),
        ('zs', '正式上线'),
        ('other', '其他'),
    ]

    name = models.CharField(max_length=100, verbose_name="游戏名称")
    description = models.TextField(blank=True, null=True, verbose_name="游戏介绍")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='kfz',
        verbose_name="游戏状态"
    )
    version = models.CharField(max_length=20, default="0.1.0", verbose_name="游戏版本")
    updated_at = models.DateTimeField(auto_now_add=True, verbose_name="更新时间")

    # 游戏默认设置
    huobi = models.CharField(max_length=50, default="金币", verbose_name="默认货币")
    default_map = models.ForeignKey(
        'GameMap',  # 假设已存在GameMap模型
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='start_map',
        verbose_name="默认地图入口"
    )
    
    # 玩家初始设置
    default_skill = models.ForeignKey(
        'Skill',  # 假设已存在Skill模型
        blank=True,
        related_name='default_skill',
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="人物初始技能"
    )

    
    # 游戏配置参数
    config_params = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="游戏配置参数",
    )
    
    class Meta:
        verbose_name = '游戏基础属性'
        verbose_name_plural = '游戏基础属性'

    def __str__(self):
        return f"{self.name} (v{self.version})"


class Task(models.Model):
    """优化后的任务模型"""
    FUNCTIONAL_TYPE = (  # 功能类型
        (1, '对话任务'),
        (2, '杀怪任务'),
        (3, '寻物任务'),
    )
    THEME_TYPE = (
        (1, '主线任务'),
        (2, '日常任务'),
        (3, '副本任务'),
    )
    # 基础信息
    name = models.CharField(verbose_name="任务名称", max_length=200, db_index=True)
    description = models.TextField(verbose_name="任务描述", blank=True)
    theme = models.PositiveSmallIntegerField(
        choices=THEME_TYPE,
        db_index=True,
        verbose_name="任务主题"
    )
    function_type = models.PositiveSmallIntegerField(
        choices=FUNCTIONAL_TYPE,
        db_index=True,
        verbose_name="任务类型"
    )
    
    # 任务配置
    is_droppable = models.BooleanField(verbose_name="可放弃", default=True)
    trigger_conditions = models.JSONField(
        verbose_name="触发条件", 
        default=dict,
        help_text="JSON格式的条件配置"
    )

    # 任务链关系
    prev_task_id = models.PositiveIntegerField(  # 范围扩大
        blank=True,
        null=True,
        verbose_name="前置任务ID",
        db_index=True  # 增加索引
    )
    
    # NPC关联
    accept_npc = models.ForeignKey(
        'GameNPC',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='available_tasks',
        verbose_name="接取NPC"
    )
    
    submit_npc = models.ForeignKey(
        'GameNPC',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submit_tasks',
        verbose_name="提交NPC"
    )
    map = models.ForeignKey(
        'GameMap',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="任务地图"
    )
    
    # 对话内容
    accept_dialog = models.TextField("接受对话", blank=True)
    progress_dialog = models.TextField("进度对话", blank=True)
    completion_dialog = models.TextField("完成对话", blank=True)
    
    # 奖励
    rewards = models.JSONField(
        verbose_name="任务奖励", 
        default={
            'money': 10,
            'exp': 10,
            # 'item': {
            #     'item_id': 1,
            #     'count': 1,
            # }
        },
        help_text="JSON格式的奖励配置"
    )
    

    class Meta:
        verbose_name = "游戏任务"
        verbose_name_plural = "任务"
        indexes = [
            models.Index(fields=['theme', 'function_type']),
            models.Index(fields=['accept_npc', 'submit_npc']),
        ]

    def __str__(self):
        return self.name


class TaskItem(models.Model):
    """任务目标表"""
    TARGET_TYPE = (
        (1, '对话'),
        (2, '怪物'),
        (3, '物品'),
    )
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='targets')
    target_type = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="目标类型", choices=TARGET_TYPE)
    target_id = models.PositiveIntegerField(null=True,blank=True, verbose_name="目标ID")  # 物品ID/怪物ID/NPC ID
    amount = models.IntegerField(default=1, verbose_name="数量")
    
    class Meta:
        verbose_name = "任务目标表"
        verbose_name_plural = "任务目标表"

    def __str__(self):
        return self.task.name

class PlayerTaskProcess(models.Model):
    """玩家任务进度表"""
    player_task = models.ForeignKey('PlayerTask', on_delete=models.CASCADE, related_name='progresses')
    target_type = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="目标类型", choices=TaskItem.TARGET_TYPE)
    target_id = models.PositiveIntegerField(null=True,blank=True, verbose_name="目标ID")
    current_count = models.IntegerField(default=0, verbose_name="当前数量")  # 当前进度

    # item_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="收集物品")
    # item_count = models.IntegerField(default=0, verbose_name="已有数量")
    # monster_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="击杀怪物")
    # monster_count = models.IntegerField(default=0, verbose_name="击杀数量")
    
    class Meta:
        verbose_name = "玩家任务进度表"
        verbose_name_plural = "玩家任务进度表"

class PlayerTask(models.Model):
    """玩家任务状态表"""
    # 任务状态选择
    TASK_STATUS = (
        (0, '未开始'),
        (1, '进行中'),
        (2, '已完成'),
        (3, '已放弃'),
        
    )
    
    player = models.ForeignKey('Player', on_delete=models.CASCADE, related_name='player_tasks', verbose_name="玩家", db_index=True)
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='player_tasks', verbose_name="任务", db_index=True)
    status = models.PositiveSmallIntegerField( choices=TASK_STATUS, default=1, verbose_name="任务状态", db_index=True)
    
    # 任务时间
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="开始时间", db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间", db_index=True)
    
    class Meta:
        verbose_name = "玩家任务表"
 

class SellGoods(models.Model):
    SHOP_TYPES = (
        (1, 'NPC商店'),
        (2, '游戏商城'),
        (3, '帮会商店'),
    )
    
    CURRENCY_TYPES = (
        (1, '铜币'),
        (2, '金币'),
        (3, '帮派资金'),
    )
    
    shop_type = models.PositiveSmallIntegerField(
        choices=SHOP_TYPES, 
        db_index=True, 
        verbose_name="商店类型",
        default=1
    )
    npc = models.ForeignKey(
        'GameNPC', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        db_index=True,
        verbose_name="关联NPC"
    )
    item = models.ForeignKey(
        'Item', 
        on_delete=models.CASCADE, 
        db_index=True,
        verbose_name="物品"
    )
    price = models.PositiveIntegerField(verbose_name="价格")
    currency_type = models.PositiveSmallIntegerField(
        choices=CURRENCY_TYPES, 
        default=1,
        verbose_name="货币类型"
    )
    
    class Meta:
        verbose_name = '游戏商店'
        indexes = [
            # 组合索引优化查询性能
            models.Index(fields=['shop_type', 'npc']),
            models.Index(fields=['shop_type', 'item']),
        ]

    def __str__(self):
        return f"{self.item.name}({self.get_shop_type_display()})"

    def save(self, *args, **kwargs):
        """重写save方法，清除缓存"""
        super().save(*args, **kwargs)
        from .utils.cacheutils import CacheManager
        CacheManager.invalidate_shop_cache(self.shop_type)
