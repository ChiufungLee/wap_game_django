import re
import operator

class ConditionParser:
    """简单的条件表达式解析器"""
    OPERATORS = {
        '>': operator.gt,
        '<': operator.lt,
        '>=': operator.ge,
        '<=': operator.le,
        '==': operator.eq,
        '!=': operator.ne,
        'in': lambda a, b: a in b,
        'not in': lambda a, b: a not in b
    }
    
    def __init__(self, context):
        self.context = context
    
    def get_value(self, expression):
        """获取表达式的值，支持变量和字面量"""
        # 如果是数字
        if expression.replace('.', '', 1).isdigit():
            return float(expression) if '.' in expression else int(expression)
        
        # 如果是布尔值
        if expression.lower() in ['true', 'false']:
            return expression.lower() == 'true'
        
        # 如果是字符串（用引号包裹）
        if expression.startswith('"') and expression.endswith('"'):
            return expression[1:-1]
        if expression.startswith("'") and expression.endswith("'"):
            return expression[1:-1]
        
        # 变量访问（支持点号分隔）
        parts = expression.split('.')
        current = self.context
        
        for part in parts:
            if part in current:
                current = current[part] if isinstance(current, dict) else getattr(current, part)
            else:
                raise ValueError(f"未找到变量: {expression}")
        
        return current
    
    def parse(self, condition_str):
        """解析条件表达式"""
        if not condition_str.strip():
            return True  # 空条件视为真
        
        # 支持括号表达式
        if '(' in condition_str and ')' in condition_str:
            return self.evaluate_parentheses(condition_str)
        
        # 匹配操作符
        for op_pattern in ['>=', '<=', '!=', '==', ' not in ', ' in ', '>', '<']:
            if op_pattern in condition_str:
                parts = condition_str.split(op_pattern, 1)
                left = parts[0].strip()
                right = parts[1].strip()
                
                left_val = self.get_value(left)
                right_val = self.get_value(right)
                
                op_func = self.OPERATORS[op_pattern.strip()]
                return op_func(left_val, right_val)
        
        # 没有操作符，直接判断表达式是否为真
        return bool(self.get_value(condition_str))
    
    def evaluate_parentheses(self, expr):
        """计算括号表达式"""
        # 提取括号内的表达式
        inner_expr = re.search(r'\((.*?)\)', expr).group(1)
        inner_result = self.parse(inner_expr)
        
        # 检查括号前的操作符（如 not）
        prefix = expr.split('(', 1)[0].strip()
        if prefix == 'not':
            return not inner_result
        
        return inner_result