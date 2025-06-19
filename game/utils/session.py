# utils/session.py
from django.http import JsonResponse

def session_health_check(request):
    """会话健康检查API"""
    response = {
        'session_active': False,
        'user_id': None,
        'username': None
    }
    
    # 检查标准会话
    if 'user_id' in request.session:
        response.update({
            'session_active': True,
            'user_id': request.session['user_id'],
            'username': request.session['username'],
            'session_type': 'standard'
        })
    # 检查持久化会话
    elif 'persistent_user_id' in request.COOKIES and 'persistent_token' in request.COOKIES:
        response['session_type'] = 'persistent'
        # 这里可以添加验证逻辑
    
    return JsonResponse(response)
