from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.core.cache import cache
from .models import User, GameBase, Player
import re
import time
import random
from io import BytesIO
import base64
from captcha.image import ImageCaptcha
from django.utils import timezone
import secrets
from .utils.middleware import ParamSecurity
from django.contrib import messages

import logging
logger = logging.getLogger(__name__)

# Create your views here.
# from .utils.session_recovery import SessionRecoveryMiddleware


def register(request):
    # 获取客户端IP
    ip_address = get_client_ip(request)
    
    # ===== 安全防护层 1: 基础频率限制 =====
    if is_ip_blocked(ip_address):
        return HttpResponseForbidden("操作过于频繁，请稍后再试")
    
    # ===== 安全防护层 2: 注册间隔限制 =====
    if request.method == "POST":
        last_reg_time = cache.get(f'last_reg:{ip_address}', 0)
        current_time = time.time()
        if current_time - last_reg_time < 5:  # 5秒内不允许重复注册
            return render(request, 'register.html', {
                'message': '操作过于频繁，请等待5秒后再试',
                'captcha_image': generate_image_captcha(ip_address)  # 生成新验证码
            })
    
    if request.method == "GET":
        # 生成并存储验证码（实际应用应使用图形验证码）
        # captcha = generate_simple_captcha()
        # cache.set(f'captcha:{ip_address}', captcha[1], timeout=300)  # 5分钟有效期
        captcha_image = generate_image_captcha(ip_address)
        # print(captcha_image)
        return render(request, "register.html", {
            'captcha_image': captcha_image,
            'ip_address': ip_address
        })
    else:
        # ===== 安全防护层 3: 请求参数获取与基础验证 =====
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        re_password = request.POST.get('re_password', '').strip()
        security_code = request.POST.get('security_code', '').strip()
        # captcha_answer = request.POST.get('captcha', '').strip()
        captcha_answer = request.POST.get('captcha', '').strip().lower()  # 转为小写
        
        # 验证码检查
        if not validate_captcha(captcha_answer, ip_address):
            return render(request, 'register.html', {
                'message': '验证码错误',
                # 'captcha_question': generate_simple_captcha()[0],
                'captcha_image': generate_image_captcha(ip_address),  # 生成新验证码
                'username': username,
                'security_code': security_code
            })
        
        # 基本字段验证
        error_context = validate_registration_fields(username, password, re_password, security_code)
        if error_context:
            return render(request, 'register.html', {
                **error_context,
                # 'captcha_question': generate_simple_captcha()[0],
                'captcha_image': generate_image_captcha(ip_address),  # 生成新验证码
                'username': username,
                'security_code': security_code
            })
        
        # ===== 安全防护层 5: 用户名唯一性检查 =====
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {
                'message': '该用户已注册',
                # 'captcha_question': generate_simple_captcha()[0],
                'captcha_image': generate_image_captcha(ip_address),  # 生成新验证码
                'username': username,
                'security_code': security_code
            })
        
        # ===== 安全防护层 6: IP注册频率限制 =====
        if not check_ip_registration_limit(ip_address):
            record_security_alert(ip_address, "高频注册尝试")
            return render(request, 'register.html', {
                'message': '注册请求过于频繁',
                # 'captcha_question': generate_simple_captcha()[0]
                'captcha_image': generate_image_captcha(ip_address),  # 生成新验证码
            })
        
        # ===== 创建用户 =====
        try:
            user = User.objects.create(
                username=username,
                password=password,  
                security_code=security_code,
                # user_type=1,  # 普通用户
                last_login_ip=ip_address,
                # last_login_at=timezone.now(),
            )
            
            messages.success(request, '注册成功！请登录')
            return redirect('login')
        except Exception as e:
            return render(request, 'register.html', {
                'message': f'注册失败: {str(e)}',
                # 'captcha_question': generate_simple_captcha()[0]
                'captcha_image': generate_image_captcha(ip_address)  # 生成新验证码
            })

# ===== 安全工具函数 =====
def get_client_ip(request):
    """获取客户端真实IP"""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def is_ip_blocked(ip):
    """检查IP是否被临时封禁"""
    return cache.get(f'ip_block:{ip}', False)

def generate_image_captcha(ip):
    """生成图形验证码并返回base64编码的图片"""
    # 生成4位随机字符（排除易混淆字符）
    chars = ''.join(random.choices('123456789', k=4))
    
    # 创建验证码图片
    image = ImageCaptcha(width=200, height=80)
    image_data = image.generate(chars)
    
    # 存储验证码答案（转为小写）
    cache.set(f'captcha:{ip}', chars.lower(), timeout=300)  # 5分钟有效期
    
    # 将图片转换为base64
    buffer = BytesIO()
    image_data.seek(0)
    buffer.write(image_data.read())
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}"

def validate_captcha(user_input, ip):
    """验证用户输入的验证码"""
    correct_answer = cache.get(f'captcha:{ip}')
    if not correct_answer:
        return False
    return user_input == correct_answer

def validate_registration_fields(username, password, re_password, security_code):
    """验证注册字段有效性"""
    # 检查必填字段
    if not all([username, password, re_password, security_code]):
        return {'message': '所有字段必须填写'}
    
    # 用户名长度和格式
    if len(username) < 6 or len(username) > 24:
        return {'message': '用户名长度需在6-24个字符之间'}
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return {'message': '用户名只能包含字母、数字和下划线'}
    
    # 密码长度
    if len(password) < 6 or len(password) > 24:
        return {'message': '密码长度需在6-24个字符之间'}
    
    # 密码一致性
    if password != re_password:
        return {'message': '两次输入的密码不一致'}
    
    # 安全码格式
    if len(security_code) != 6 or not security_code.isdigit():
        return {'message': '安全码必须是6位数字'}
    
    return None

def check_ip_registration_limit(ip):
    """检查IP注册频率限制"""
    # 获取当前小时注册次数
    current_hour = timezone.now().strftime('%Y-%m-%d-%H')
    reg_count_key = f'reg_count:{ip}:{current_hour}'
    
    # 获取并增加计数
    reg_count = cache.get(reg_count_key, 0) + 1
    cache.set(reg_count_key, reg_count, timeout=3600)  # 1小时过期
    
    # 每小时最多允许5次注册
    return reg_count <= 5



        

# def register(request):
#     if request.method == "GET":
#         return render(request,"register.html",{})
#     else:
#         username = request.POST.get('username').trip()
#         # vcode = request.POST.get('vcode')
#         password = request.POST.get('password')
        
#         # 判断用户名和密码是否符合要求
#         if not (6 <= len(email) <= 24) or not (6 <= len(password) <= 24):
#             context = {'error': '用户名和密码长度必须在6-24之间'}
#             return render(request, 'register.html', context) 
#         try:
#             # latest_vcode = VerificationCode.objects.filter(email=email).latest('created_at')
#             # 进行验证码比较
#             # if vcode == latest_vcode.code:
#             if User.objects.filter(email=email).exists():
#                 messages.success(request, '该邮箱已使用！')
#                 return redirect('/register/')
#             else:
#                 user = User.objects.create(username=email, email=email, password=password)
#                 user_log = UserLog.objects.create(userid=user.id,log="账号注册成功！")
#                 return HttpResponse('注册成功！ <a href="/login/">前往登录</a>')
#             # else:
#             #     error_message = '验证码错误，请重新输入!'
#             #     return render(request, 'register.html', locals())
#         except VerificationCode.DoesNotExist:
#             error_message = '未找到验证码，请重新获取!'
#             return render(request, 'register.html', locals())

def login(request):
    game = GameBase.objects.first()
    if request.method == "GET":
        
        return render(request,"login.html", {
            'game': game,
        })
    else:

        ip_address = get_client_ip(request)
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)

            # 检查用户是否被锁定
            if not user.is_active:
                return render(request, "login.html", {
                    'error_message': '用户已被锁定，请联系管理员'
                })
            if user.password == password:
                # 登录成功
                request.session['user_id'] = user.id
                request.session['username'] = user.username
                request.session['user_admin'] = user.is_admin()
                
                # 更新登录信息
                user.update_last_login_info(ip_address)
                
                # 创建持久化会话令牌
                response = redirect('/index')
            

                # 添加持久化cookie（可选）
                if request.POST.get('remember_me'):
                    # 生成唯一令牌
                    token = secrets.token_urlsafe(32)
                    
                    # 存储在用户模型中
                    user.params['persistent_token'] = token
                    user.save(update_fields=['params'])
                    
                    # 设置长期有效cookie
                    response.set_cookie(
                        'persistent_user_id', 
                        str(user.id),
                        max_age=1209600,  # 2周
                        httponly=True,
                        secure=True
                    )
                    response.set_cookie(
                        'persistent_token',
                        token,
                        max_age=1209600,
                        httponly=True,
                        secure=True
                    )
                    print("********")
                return response
            else:
                # 密码错误
                messages.error(request, '密码错误，请重新登录！')
                return render(request, "login.html",{'game': game})
        except User.DoesNotExist:
            # 用户不存在
            messages.error(request, '用户不存在，请先注册！')
            return render(request, "login.html", {'game': game})

def logout(request):
    # 清除用户登录状态
    request.session.flush()
    # 这里可以根据需要进行其他操作，例如重定向到登录页面或其他页面
    # SessionRecoveryMiddleware.force_logout(request)
        # 创建中间件实例
    # middleware = SessionRecoveryMiddleware()
    
    # 执行登出操作并返回响应
    # return middleware.perform_logout(request)
    return redirect('/login/')



def game_error(request):
    # message = message
    error_message = request.GET.get('error', '未知错误，请重新登录')
    return render(request, 'game_error.html', {'error_message':error_message})
    # return render(request, 'error.html', {})

def admin_views(request):
    """
    管理员视图入口
    """
    # 直接从中间件获取解密数据
    cmd_data = request.secure_data.get('cmd')
    get_cmd_data = request.secure_params.get('cmd')
    print("cmd_data")
    print(get_cmd_data)
    if not cmd_data:

        return render_error(request, "非法访问：缺少安全参数", status=403)
    
    # 验证操作类型
    if cmd_data['action'] != "admin":
        return render_error(request, "非法操作类型", status=403)


    # 解析并验证用户ID
    try:

        decrypted_user_id = cmd_data['value'].split(':')[-1]

        if len(decrypted_user_id) > 1:
            token_time = int(decrypted_user_id[1])
            if time.time() - token_time > 300:  # 10分钟有效期
                # logger.warning("Expired admin token used")
                return render_error(request, "令牌已过期", status=403)
    
    except (KeyError, ValueError, IndexError, TypeError):
        # logger.exception("Invalid admin token format")
        return render_error(request, "参数格式错误", status=400)


    
    return render(request, 'admin/wap_admin.html', {})

    # return render(request, 'admin/wap_admin.html', {})

def reset_password(request):
    secure_params = request.secure_params.get('cmd')
    
    if not secure_params:
        # return JsonResponse({'error': '非法参数'})
        return redirect(reverse('game_error') + '?error=非法参数')
    print(secure_params)

    return render(request, 'admin/wap_admin.html', {})

def navigate_page(request):
    pass

