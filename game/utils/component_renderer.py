from django.template import Template, Context
from django.utils.html import format_html, mark_safe
from .condition_parser import ConditionParser

class ComponentRenderer:
    def __init__(self, context):
        self.context = context
        # 添加常用函数到上下文
        self.context['format'] = self.format_value
        self.context['safe'] = mark_safe
    
    def render(self, component):
        """渲染统一文本组件"""
        # 检查显示条件
        if not self.evaluate_condition(component.show_condition):
            return ''
        
        try:
            # 渲染内容模板
            tpl = Template(component.display_text)
            rendered_content = tpl.render(Context(self.context))
            print(tpl)
            # 添加事件绑定
            html = self.add_event_wrapper(rendered_content, component)
            print(html)
            # 添加自定义样式
            # if component.custom_css:
            #     css = component.custom_css.replace('#component-{id}', f'#component-{component.id}')
            #     html = format_html('<style>{}</style>{}', css, html)
            
            # # 添加自定义脚本
            # if component.custom_js:
            #     js = component.custom_js
            #     html += format_html(
            #         '<script data-component-id="{}">{}</script>',
            #         component.id, js
            #     )
            
            # 包裹容器
            return format_html(
                '<div id="component-{}" data-component-id="{}">{}</div>',
                component.id, component.id, html
            )
            
        except Exception as e:
            return format_html(
                '<div class="error">组件错误 (ID:{}): {}</div>',
                component.id, str(e)
            )
    
    def evaluate_condition(self, condition_str):
        """评估显示条件"""
        if not condition_str.strip():
            return True
        
        try:
            parser = ConditionParser(self.context)
            return parser.parse(condition_str)
        except Exception as e:
            print(f"条件解析错误: {str(e)}")
            return False
    
    def format_value(self, value, format_str):
        """格式化值（用于模板中）"""
        try:
            return format_str.format(value)
        except:
            return str(value)
    
    def add_event_wrapper(self, display_text, component):
        """为内容添加事件绑定"""
        if component.event == None:
            return display_text
        
        # 根据事件类型添加不同的包装
        # if component.event == 'move_page':
        #     return format_html(
        #         '<a href="/game/{}" class="event-link">{}</a>',
        #         component.event_target, display_text
        #     )

        if component.event.name == '返回首页':
            return format_html(
                '<a href="/index/" class="event-link">{}</a>', display_text
            )
        # elif component.event == 'go_url':
        #     return format_html(
        #         '<a href="{}" class="event-link">{}</a>',
        #         component.event_target, display_text
        #     )
        
        # else:
        #     # 其他事件类型添加数据属性
        #     return format_html(
        #         '<div class="event-trigger" data-event-type="{}" data-event-target="{}">{}</div>',
        #         component.event, component.event_target, display_text
        #     )