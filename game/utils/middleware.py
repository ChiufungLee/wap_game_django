# middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from ..models import User, Player
from django.contrib import messages
from urllib.parse import urlencode
import logging
from .security_params import ParamSecurity
import time
logger = logging.getLogger(__name__)
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse

# class SessionRecoveryMiddleware(MiddlewareMixin):
#     """会话恢复和安全增强中间件"""
#     def process_request(self, request):

#         logger.debug(f"处理请求: {request.path}")
        
#         # 检查会话中是否有用户信息
#         if 'user_id' not in request.session:
#             # 尝试从持久化存储恢复会话
#             logger.debug("会话中没有user_id，尝试恢复")
#             self.try_recover_session(request)
            
#         # 验证会话有效性
#         if 'user_id' in request.session:
#             user_id = request.session['user_id']
#             try:
#                 # 验证用户是否存在且未被锁定
#                 user = User.objects.get(id=user_id)
#                 if not user.is_active:
#                     # 用户被锁定，强制登出
#                     return self.force_logout(request)
                    
#                 # 将会话绑定到请求对象
#                 request.user = user
#             except User.DoesNotExist:
#                 # 用户不存在，清除会话
#                 return self.force_logout(request)
                
#     def process_response(self, request, response):
#         # 添加安全头
#         response['X-Frame-Options'] = 'DENY'
#         response['X-Content-Type-Options'] = 'nosniff'
#         response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
#         return response
        
#     def try_recover_session(self, request):
#         """尝试恢复会话"""
#         # 方法1：从cookie中恢复
#         user_id = request.COOKIES.get('persistent_user_id')
#         token = request.COOKIES.get('persistent_token')
        
#         if user_id and token:
#             try:
#                 user = User.objects.get(id=user_id)
#                 # 验证持久化令牌（存储在用户模型中）

#                 # 检查用户是否被锁定
#                 if not user.is_active:
#                     logger.info(f"尝试恢复被锁定用户 {user.username} 的会话，拒绝")
#                     return False

#                 if user.params.get('persistent_token') == token:
#                     # 恢复会话
#                     request.session['user_id'] = user.id
#                     request.session['username'] = user.username
#                     request.session['user_admin'] = user.is_admin()

#             except User.DoesNotExist:
#                 pass
        
#         # 方法2：从本地存储恢复（单页应用）
#         if request.headers.get('X-Session-Recovery'):
#             try:
#                 data = json.loads(request.headers['X-Session-Recovery'])
#                 user_id = data.get('user_id')
#                 token = data.get('token')
                
#                 if user_id and token:
#                     user = User.objects.get(id=user_id)
#                     if user.params.get('local_token') == token:
#                         request.session['user_id'] = user.id
#                         request.session['username'] = user.username
#                         request.session['user_admin'] = user.is_admin()
#                         return True
#             except:
#                 pass
                
#         return False
        
#     def force_logout(self, request):
#         """强制登出并重定向"""
#         logger.warning("执行强制登出操作")
#         # 清除会话
#         request.session.flush()
        
#         # 清除持久化cookie
#         response = redirect(reverse('login'))
#         response.delete_cookie('persistent_user_id')
#         response.delete_cookie('persistent_token')
        
#         # 添加消息提示
#         print(type(request))

#         messages.warning(request, '会话已过期，请重新登录')
        
#         return response


# class CustomErrorHandler(MiddlewareMixin):
#     """自定义错误处理中间件"""
#     def process_exception(self, request, exception):
#         # 记录异常
#         logger.error(f"请求异常: {request.path}", exc_info=True)
        
#         # 检查会话是否可能丢失
#         if 'user_id' not in request.session:
#             # 尝试恢复会话
#             if SessionRecoveryMiddleware().try_recover_session(request):
#                 # 重试请求
#                 return None
        
#         # 特殊处理常见异常
#         if isinstance(exception, User.DoesNotExist) and 'user_id' in request.session:
#             # 用户不存在但会话存在 - 清除会话
#             request.session.flush()
#             return redirect(reverse('login') + '?error=session_expired')
        
#         # 返回友好错误页面
#         from django.http import HttpResponseServerError
#         return HttpResponseServerError(render_to_string('500.html', request=request))

# class SecureParamMiddleware(MiddlewareMixin):
#     def process_request(self, request):
#         secure_params = {}
#         # request.secure_params = {}
        
#         # 解密所有GET参数
#         for key in request.GET:
#             # 只处理加密参数（格式：xxx-xxx）
#             if '-' in key and len(key.split('-')) == 2:
#                 param_value = ParamSecurity.decode_param(key)
#                 print(param_value)
#                 if param_value:
#                     secure_params[param_value] = request.GET[key]
#             else:
#                 encrypted_value = request.GET[key]
#                 decoded = ParamSecurity.decode_param(encrypted_value)
#                 if decoded:
#                     secure_params[key] = decoded
#             print(secure_params)
#         request.secure_params = secure_params

class SecureParamMiddleware(MiddlewareMixin):
    ENCRYPTED_PARAMS = ['cmd', 'token', 'action']
    RENEW_THRESHOLD = 600  # 提前10分钟续期

    def process_request(self, request):
        request.secure_params = {}
        request.secure_data = {}
        sources = [request.GET, request.POST]
        
        for params_source in sources:
            for key in self.ENCRYPTED_PARAMS:
                if key in params_source:
                    value = params_source[key]
                    if self.is_encrypted_param(value):
                        # 尝试解密参数
                        decrypted = ParamSecurity.decode_param(value)
                        print(f"decrypted:{decrypted}")
                        if decrypted:
                            # 直接存储解密后的参数字典
                            request.secure_params[key] = {
                                'entity': decrypted['entity_type'],
                                'sub_action': decrypted['sub_action'],
                                'params': decrypted['params']  # 包含所有参数
                            }
                            request.secure_data[key] = decrypted   
                            # 自动续期主参数(cmd)
                            if key == 'cmd':
                                self.renew_param_if_needed(request, value)
                        else:
                            base_url = reverse('error')
                            query_string = urlencode({'error': '长时间未操作，请重新登录'})
                            return redirect(f'{base_url}?{query_string}')

                            
        
        return None

    def renew_param_if_needed(self, request, original_value):
        """检查并续期即将过期的参数"""
        # 计算剩余时间
        decrypted_data = request.secure_data.get('cmd')
        if not decrypted_data:
            return
            
        timestamp = int(decrypted_data.get('timestamp', 0))
        remaining = (timestamp + ParamSecurity.DEFAULT_MAX_AGE) - time.time()
        
        # 剩余时间不足阈值时自动续期
        if remaining < self.RENEW_THRESHOLD:
            # 生成新参数
            new_cmd = ParamSecurity.renew_param(original_value)
            if new_cmd:
                # 更新当前请求参数
                if request.method == "GET":
                    request.GET = request.GET.copy()
                    request.GET['cmd'] = new_cmd
                else:
                    request.POST = request.POST.copy()
                    request.POST['cmd'] = new_cmd
                
                # 重新解密新参数
                new_decrypted = ParamSecurity.decode_param(new_cmd)
                # if new_decrypted:
                #     parts = new_decrypted['value'].split(':', 2)
                #     if len(parts) == 3:
                #         request.secure_params['cmd'] = {
                #             'entity': parts[0],
                #             'sub_action': parts[1],
                #             'entity_id': parts[2]
                #         }
                request.secure_data['cmd'] = new_decrypted
                request.secure_params['cmd'] = {  # 添加上下文更新
                    'entity': new_decrypted['entity_type'],
                    'sub_action': new_decrypted['sub_action'],
                    'params': new_decrypted['params']
                }
    
    @staticmethod
    def is_encrypted_param(value):
        """判断是否为加密参数格式（简化版）"""
        return (
            isinstance(value, str) and 
            len(value) > 25 and  # unique_id(10) + '-' + signature(16)
            value.count('-') == 1
        )

class PlayerActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 处理请求前的逻辑
        response = self.get_response(request)
        # 处理请求后的逻辑
        
        # 检查用户是否已登录且有玩家角色
        user_id = request.session.get('user_id')
        # if user_id:

        if user_id and hasattr(request.user, 'players') and request.user.players.exists():
            # 获取当前玩家（假设用户只有一个玩家角色）
            player = request.user.players.first()
            # 更新玩家活动时间
            player.update_activity()
        
        return response

class RequestTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 记录请求开始时间
        start_time = time.perf_counter()
        
        # 执行视图处理请求
        response = self.get_response(request)
        
        # 计算请求处理耗时（毫秒）
        end_time = time.perf_counter()
        load_time = f"{(end_time - start_time) * 1000:.2f} ms"
        
        # 添加到响应头（调试用）
        response['X-Request-Time'] = load_time
        
        # 处理不同类型的响应
        if isinstance(response, TemplateResponse):
            # 对于模板响应，添加到上下文
            if not response.context_data:
                response.context_data = {}
            response.context_data['load_time'] = load_time
        elif hasattr(response, 'content') and 'text/html' in response.get('Content-Type', ''):
            # 对于普通HTML响应，注入到HTML中
            try:
                content = response.content.decode('utf-8')
                if '</body>' in content:
                    load_html = f'<p class="load_time" >耗时: {load_time}</p>'
                    content = content.replace('</body>', load_html + '</body>')
                    response.content = content.encode('utf-8')
            except UnicodeDecodeError:
                pass  # 忽略非文本响应
        
        return response


# 缓存命中率
class CacheStatsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.requests = 0
        self.cache_hits = 0
    
    def __call__(self, request):
        response = self.get_response(request)
        if 'chat' in request.path:
            self.requests += 1
            if hasattr(request, 'cache_hit') and request.cache_hit:
                self.cache_hits += 1
            
            # 每100次请求记录一次命中率
            if self.requests % 100 == 0:
                hit_rate = (self.cache_hits / self.requests) * 100
                logging.info(f"Chat cache hit rate: {hit_rate:.2f}%")
        return response

# class UpdateLastActiveMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response
    
#     def __call__(self, request):
#         response = self.get_response(request)

#         request.player = None
#         user_id = request.session.get('user_id')
#         if user_id:
#             try:
#                 # 获取当前玩家的最新对象
#                 # 这里假设一个用户只有一个角色，如果有多个需要额外处理
#                 player = Player.objects.get(user_id=user_id)
                
#                 # 将玩家对象附加到 request
#                 request.player = player
                
#                 # 更新活动状态（设置为在线）
#                 player.update_activity()
                
#             except Player.DoesNotExist:
#                 # 没有找到玩家角色
#                 pass
#         response = self.get_response(request)
#         return response





# class ParamRefreshMiddleware(MiddlewareMixin):
#     def process_response(self, request, response):
#         """检查参数失效情况并自动刷新"""
#         # 仅处理参数相关错误
#         if response.status_code != 500:
#             return response
            
#         # 检查是否是参数解密错误
#         if hasattr(request, 'secure_data') and any(
#             data.get('error') == 'used' for data in request.secure_data.values()
#         ):
#             # 获取当前URL和参数
#             current_url = request.build_absolute_uri()
#             parsed_url = urlparse(current_url)
#             query_params = parse_qs(parsed_url.query)
            
#             # 生成新参数替换失效参数
#             for param_name in list(query_params.keys()):
#                 if self.is_encrypted_param(query_params[param_name][0]):
#                     # 获取原始值（从session或上下文）
#                     if param_name == 'cmd' and request.session.get('user_id'):
#                         new_value = f"user:{request.session['user_id']}"
#                         new_param = ParamSecurity.generate_param(
#                             new_value, 
#                             action="user_session",
#                             expire=3600,
#                             one_time=False  # 可刷新参数
#                         )
#                         query_params[param_name] = [new_param]
            
#             # 重建URL
#             new_query = urlencode(query_params, doseq=True)
#             new_url = urlunparse((
#                 parsed_url.scheme,
#                 parsed_url.netloc,
#                 parsed_url.path,
#                 parsed_url.params,
#                 new_query,
#                 parsed_url.fragment
#             ))
            
#             # 307临时重定向保持请求方法
#             return HttpResponseRedirect(new_url, status=307)
            
#         return response

# class SecureParamMiddleware(MiddlewareMixin):
#     def process_request(self, request):
#         valid_params = {}  # 只存储有效参数
#         invalid_params = []  # 记录无效参数
        
#         # 解密所有GET参数
#         for key in request.GET:
#             value = request.GET[key]
            
#             # 处理加密参数名 (格式: token-signature)
#             if '-' in key and len(key.split('-')) == 2:
#                 decrypted_key = ParamSecurity.decode_param(key)
#                 if decrypted_key:
#                     # 使用解密后的参数名
#                     valid_params[decrypted_key] = value
#                 else:
#                     invalid_params.append(key)
            
#             # 处理加密的参数值
#             else:
#                 decrypted_value = ParamSecurity.decode_param(value)
#                 if decrypted_value:
#                     # 使用原始参数名和解密后的值
#                     valid_params[key] = decrypted_value
#                 else:
#                     invalid_params.append(key)
        
#         # 设置请求属性
#         request.secure_params = valid_params
#         request.invalid_params = invalid_params  # 记录无效参数
        
        # 调试日志
        # if invalid_params:
        #     logger.warning(
        #         f"发现无效参数: {invalid_params} "
        #         f"路径: {request.path}"
        #     )
        