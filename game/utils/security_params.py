# security_params.py
from django.conf import settings
from django.core.cache import cache
import hmac
import time
import secrets
from django.utils.deprecation import MiddlewareMixin
import ujson
import base64

# security_params.py
class ParamSecurity:
    DEFAULT_MAX_AGE = 1800  # 30分钟统一有效期

    @staticmethod
    def _encode_data(data_dict):
        """将字典编码为URL安全的base64字符串"""
        json_str = ujson.dumps(data_dict)
        return base64.urlsafe_b64encode(json_str.encode()).decode().rstrip('=')

    @staticmethod
    def _decode_data(encoded_str):
        """将base64字符串解码为字典"""
        # 补齐可能缺失的等号
        padding = 4 - (len(encoded_str) % 4)
        encoded_str += '=' * padding
        
        try:
            json_str = base64.urlsafe_b64decode(encoded_str).decode()
            return ujson.loads(json_str)
        except (ValueError, TypeError, ujson.JSONDecodeError):
            return None

    @staticmethod
    def generate_param(entity_type, sub_action, params=None, action=""):
        """生成加密参数 - 使用统一有效期"""
        """
        生成加密参数 - 支持多参数和字典
        :param entity_type: 实体类型（如'player'）
        :param sub_action: 子操作（如'view'）
        :param params: 参数字典（如{'id': 123, 'name': 'test'}）
        :param action: 主操作类型（可选）
        :return: 加密参数字符串
        """

        timestamp = int(time.time())
        # 构建参数字典
        param_dict = {
            'entity_type': entity_type,
            'sub_action': sub_action,
            'params': params or {},  # 默认为空字典
            'timestamp': timestamp
        }
        
        # 生成唯一ID
        unique_id = secrets.token_urlsafe(8).replace('-', '').replace('_', '')[:10]
        
        # 编码参数字典
        encoded_params = ParamSecurity._encode_data(param_dict)
        
        # 生成签名数据
        data = f"{action}:{encoded_params}|{unique_id}"
        # value = f"{entity_type}:{sub_action}:{entity_id}"
        # unique_id = secrets.token_urlsafe(8).replace('-', '').replace('_', '')[:10]
        
        # timestamp = str(int(time.time()))
        # data = f"{action}:{value}|{timestamp}|{unique_id}"
        signature = hmac.new(
            key=settings.SECRET_KEY.encode(),
            msg=data.encode(),
            digestmod='sha256'
        ).hexdigest()[:16]
        
        # 缓存键包含签名确保唯一性
        cache_key = f"secure_param:{signature}"
        
        # 存储到缓存（有效期 = max_age + 5分钟缓冲）
        cache.set(cache_key, {
            'action': action,
            # 'value': value,
            'param_dict': param_dict,  # 存储原始字典
            'timestamp': timestamp,
        }, timeout=ParamSecurity.DEFAULT_MAX_AGE + 300)
        
        return f"{unique_id}-{signature}"

    @staticmethod
    def decode_param(encrypted_param, expected_action=None):
        """解密参数 - 使用统一有效期"""
        if not encrypted_param or not isinstance(encrypted_param, str):
            return None
            
        parts = encrypted_param.split('-', 1)
        if len(parts) != 2:
            return None
            
        unique_id, signature = parts
        
        # 直接从签名获取缓存
        cache_key = f"secure_param:{signature}"
        data = cache.get(cache_key)
        
        if not data:
            return None
            
        # 验证时效性（30分钟）
        try:
            timestamp_val = int(data['timestamp'])
            if time.time() - timestamp_val > ParamSecurity.DEFAULT_MAX_AGE:
                return None
        except (TypeError, ValueError):
            return None
            
        # 验证签名
        # check_data = f"{data['action']}:{data['value']}|{data['timestamp']}|{unique_id}"
        # expected_signature = hmac.new(
        #     key=settings.SECRET_KEY.encode(),
        #     msg=check_data.encode(),
        #     digestmod='sha256'
        # ).hexdigest()[:16]
        # 验证签名
        # 重新生成签名数据进行比较
        encoded_params = ParamSecurity._encode_data(data['param_dict'])
        check_data = f"{data['action']}:{encoded_params}|{unique_id}"
        expected_signature = hmac.new(
            key=settings.SECRET_KEY.encode(),
            msg=check_data.encode(),
            digestmod='sha256'
        ).hexdigest()[:16]


        if not hmac.compare_digest(signature, expected_signature):
            return None
            
        # 验证操作类型（如果指定）
        if expected_action and data['action'] != expected_action:
            return None

        # 返回完整的参数字典
        return {
            'entity_type': data['param_dict']['entity_type'],
            'sub_action': data['param_dict']['sub_action'],
            'params': data['param_dict']['params'],
            'action': data['action']
        }
        
        # 返回解密数据（不再标记已使用）
        return data


    @staticmethod
    def renew_param(encrypted_param):
        """续期参数 - 生成新参数代替续期"""
        # 解密原参数
        data = ParamSecurity.decode_param(encrypted_param)
        if not data:
            return None
        
        # 提取参数组成部分
        # value_parts = data['value'].split(':')
        # if len(value_parts) != 3:
        #     return None
        parts = encrypted_param.split('-', 1)
        if len(parts) != 2:
            return None
                
                
        # 生成全新的参数（自动续期）
        return ParamSecurity.generate_param(
            # entity_type=value_parts[0],
            # sub_action=value_parts[1],
            # entity_id=value_parts[2],
            # action=data.get('action', "")
            entity_type=data['entity_type'],
            sub_action=data['sub_action'],
            params=data['params'],
            action=data.get('action', "")
        )