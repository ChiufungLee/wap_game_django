def chat_handler(request, params, sub_action):
    # 处理玩家相关的操作
    curr_player = request.session["player"]
    if sub_action == 'send_message':
        # 处理发送消息的逻辑

        chat_type = params.get("chat_type", 2)  # 默认是世界消息

        create_param = ParamSecurity.generate_param(
            entity_type='chat',
            sub_action='send_message',
            params={'chat_type': chat_type},
            action='chat'
        )


        if request.method == 'POST':
            # 处理表单提交
            print("处理表单提交")
            curr_player_id = request.session["player_id"]
            player_name = request.session["player_name"]
            message = request.POST.get('message_input').strip()
            # signature = request.POST.get('signature').strip()
            print(f"player_name: {player_name}")
            print(message)
            ### 校验字段

            chat_list = []
            if message:
                if len(message) > 100:
                    messages.error(request, "消息长度不能超过100个字符")
                    return redirect(reverse('wap') + f'?cmd={ParamSecurity.generate_param("chat", "list_chat", {"chat_type": chat_type}, action="chat")}')
                if chat_type == 2:
                    # 世界消息
                    chat = ChatMessage.objects.create(type_id=chat_type, sender=curr_player.id, sender_name=curr_player.name, message=message)
                elif chat_type == 3:
                    # 私聊消息
                    receiver_id = params.get("receiver_id")
                    if not receiver_id:
                        messages.error(request, "私聊消息需要指定接收者")
                        return redirect(reverse('wap') + f'?cmd={ParamSecurity.generate_param("chat", "list_chat", {"chat_type": chat_type}, action="chat")}')
                    chat = ChatMessage.objects.create(type_id=chat_type, sender=curr_player.id, sender_name=curr_player.name, message=message, receiver=receiver_id)
                elif chat_type == 4:
                    # 帮会消息
                    # bangpai_id = params.get("bangpai_id")
                    # 提前获取用户帮派和队伍信息
                    gang_member = GangMember.objects.filter(player_id=curr_player.id).first()
                    bangpai_id = gang_member.gang.id if gang_member else None

                    if bangpai_id is None:
                        messages.error(request, "帮会消息需要指定帮会ID")
                        return redirect(reverse('wap') + f'?cmd={ParamSecurity.generate_param("chat", "list_chat", {"chat_type": chat_type}, action="chat")}')
                    chat = ChatMessage.objects.create(type_id=chat_type, sender=curr_player.id, sender_name=curr_player.name, message=message, bangpai_id=bangpai_id)
                elif chat_type == 5:
                    # 队伍消息
                    team_member = TeamMember.objects.filter(player_id=curr_player.id).first()
                    duiwu_id = team_member.team.id if team_member else None
                    if duiwu_id is None:
                        messages.error(request, "队伍消息需要指定队伍ID")
                        return redirect(reverse('wap') + f'?cmd={ParamSecurity.generate_param("chat", "list_chat", {"chat_type": chat_type}, action="chat")}')
                    chat = ChatMessage.objects.create(type_id=chat_type, sender=curr_player.id, sender_name=curr_player.name, message=message, duiwu_id=duiwu_id)
                # chat = ChatMessage.objects.create(type_id=2, sender=curr_player_id,sender_name=player_name,message=message)
                else:
                    pass
                messages.success(request, "发送成功")     

                cache_keys = []
                if chat_type == 4:  # 帮派消息
                    cache_keys.append(f"chat_4_bangpai_{bangpai_id}")
                elif chat_type == 5:  # 队伍消息
                    cache_keys.append(f"chat_5_duiwu_{duiwu_id}")
                else:
                    cache_keys.append(f"chat_{chat_type}")
                print(f"cache_keys: {cache_keys}")
                # 清除所有相关分页缓存
                for key in cache_keys:
                    cache.delete_pattern(f"player_*_chat_{chat_type}_page_*")
                    cache.delete(key)


            else:
                # 返回错误信息
                messages.error(request, "你什么都没输入呀")

            return redirect(reverse('wap') + f'?cmd={ParamSecurity.generate_param("chat", "list_chat", {"chat_type": chat_type}, action="chat")}')
        
        
    elif sub_action == 'list_chat':
        # 处理查看消息的逻辑
        chat_type = params.get("chat_type")
        page = int(params.get("page", 1))
        chat_type = int(params.get("chat_type"))
        PAGE_SIZE = 10  # 每页消息数量

        cache_key = f"player_{curr_player.id}_chat_{chat_type}_page_{page}"
        
        # 尝试从缓存获取数据
        cached_data = cache.get(cache_key)
        if cached_data:
            # 如果缓存命中，直接返回缓存数据
            return render(request, 'chat.html', json.loads(cached_data))

        # 提前获取用户帮派和队伍信息
        gang_member = cache.get(f"player_{curr_player.id}_gang")
        if not gang_member:
            gang_member = GangMember.objects.filter(player_id=curr_player.id).first()
            cache.set(f"player_{curr_player.id}_gang", gang_member, 300)  # 缓存5分钟
            
        team_member = cache.get(f"player_{curr_player.id}_team")
        if not team_member:
            team_member = TeamMember.objects.filter(player_id=curr_player.id).first()
            cache.set(f"player_{curr_player.id}_team", team_member, 300)  # 缓存5分钟
        
        # 存储帮派ID和队伍ID
        bangpai_id = gang_member.gang.id if gang_member else None
        duiwu_id = team_member.team.id if team_member else None
        
        # 生成缓存键时考虑帮派和队伍ID
        cache_key = f"chat_{chat_type}"
        if bangpai_id:
            cache_key += f"_bangpai_{bangpai_id}"
        if duiwu_id:
            cache_key += f"_duiwu_{duiwu_id}"



        # 尝试获取整个聊天记录的缓存
        all_chats = cache.get(cache_key)
        if not all_chats:

            # 基础查询
            base_query = ChatMessage.objects.all()

            # 根据聊天类型过滤
            if chat_type == 1:  # 系统消息
                base_query = base_query.filter(type_id=1)
            elif chat_type == 2:  # 世界消息
                base_query = base_query.filter(type_id=2)
            elif chat_type == 3:  # 私聊消息
                base_query = base_query.filter(type_id=3, receiver=curr_player.id)
            elif chat_type == 4:  # 帮派消息
                # gang = GangMember.objects.filter(player_id=curr_player.id).first()
                if bangpai_id:
                    base_query = base_query.filter(type_id=4, bangpai_id=bangpai_id)
                else:
                    base_query = base_query.none()
            elif chat_type == 5:  # 队伍消息
                # team = TeamMember.objects.filter(player_id=curr_player.id).first()
                if duiwu_id:
                    base_query = base_query.filter(type_id=5, duiwu_id=duiwu_id)
                else:
                    base_query = base_query.none()
            
            # 获取并缓存整个聊天记录
            all_chats = list(base_query.order_by('-created_at').values(
                'id', 'type_id', 'sender', 'sender_name', 'message', 'created_at'
            ))
            # 缓存1分钟 - 聊天系统更新频繁，不宜缓存太久
            cache.set(cache_key, all_chats, 600)

        # 使用分页器处理分页
        paginator = Paginator(all_chats, PAGE_SIZE)
        try:
            chat_page = paginator.page(page)
        except:
            chat_page = paginator.page(1)


        # # 计算分页
        # total_count = base_query.count()
        # total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE
        
        # # 确保页码在有效范围内
        # page = max(1, min(page, total_pages))
        
        # # 获取当前页数据
        # offset = (page - 1) * PAGE_SIZE
        # chat_lists = base_query.order_by('-created_at')[offset:offset + PAGE_SIZE]
        
        # 格式化消息
        chat_list = []
        for chat in chat_page.object_list:
            # 生成玩家详情加密参数
            player_encrypted_param = ""
            if chat['sender']:
                player_encrypted_param = ParamSecurity.generate_param(
                    entity_type='player',
                    sub_action='detail_player',
                    params={"player_id": chat['sender']},
                    action='player'
                )
            
            # 格式化消息内容
            if chat_type == 1:  # 系统消息
                if chat['sender_name']:
                    content = "[系统]" + chat['message'].format(
                        player_encrypted_param, chat['sender_name']
                    )
                else:
                    content = "[系统]" + chat.message
            else:  # 其他消息
                sender_display = (
                    f'<a href="/wap/?cmd={player_encrypted_param}">{chat["sender_name"]}</a>'
                    if chat['sender_name'] else "未知"
                )
                # content = f"[{chat.get_type_id_display()}]{sender_display}: {chat.message}"
                content = f"[{dict(ChatMessage.MESSAGE_TYPES).get(chat['type_id'])}{sender_display}: {chat['message']}"
            
            # 添加时间戳
            # full_message = f"{content}({chat.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
            # chat_list.append(full_message)
            # 添加时间戳
            created_at = chat['created_at']
            if isinstance(created_at, str):
                # 如果缓存中存储的是字符串时间
                dt_str = created_at
            else:
                # 如果是datetime对象
                dt_str = created_at.strftime('%Y-%m-%d %H:%M:%S')

            full_message = f"{content}({dt_str})"
            chat_list.append(full_message)
        
        # 生成分页导航的加密参数
        def generate_page_param(page_num):
            page_params = {
                "chat_type": chat_type,
                "page": page_num,
            }
  
            return ParamSecurity.generate_param(
                entity_type='chat',
                sub_action='list_chat',
                params=page_params,
                action='wap'
            )

        # 创建分页导航
        # pagination = []
        # if page > 1:
        #     pagination.append(f'<a href="/wap/?cmd={generate_page_param(1)}">首页</a>')
        #     pagination.append(f'<a href="/wap/?cmd={generate_page_param(page-1)}">上一页</a>')
        
        # # 显示当前页和总页数
        # pagination.append(f'第{page}/{total_pages}页')
        
        # if page < total_pages:
        #     pagination.append(f'<a href="/wap/?cmd={generate_page_param(page+1)}">下一页</a>')
        #     pagination.append(f'<a href="/wap/?cmd={generate_page_param(total_pages)}">尾页</a>')
        # 创建分页导航
        pagination = []
        if chat_page.has_previous():
            pagination.append(f'<a href="/wap/?cmd={generate_page_param(1)}">首页</a>')
            pagination.append(f'<a href="/wap/?cmd={generate_page_param(chat_page.previous_page_number())}">上一页</a>')
        
        # 显示当前页和总页数
        pagination.append(f'第{page}/{paginator.num_pages}页')
        
        if chat_page.has_next():
            pagination.append(f'<a href="/wap/?cmd={generate_page_param(chat_page.next_page_number())}">下一页</a>')
            pagination.append(f'<a href="/wap/?cmd={generate_page_param(paginator.num_pages)}">尾页</a>')

        response_data = {
            'pagination': " ".join(pagination),
            'wap_encrypted_param': ParamSecurity.generate_param(
                entity_type='wap',
                sub_action='none',
                params=params,
                action='wap'
            ),
            'chat_list': chat_list,
            'chat_type': chat_type,
            'create_param': ParamSecurity.generate_param(
                entity_type='chat',
                sub_action='send_message',
                params=params,
                action='chat'
            ),
            'shijie_params': ParamSecurity.generate_param(
                entity_type='chat',
                sub_action='list_chat',
                params={'chat_type':2},
                action='wap'
            ),
            'siliao_params': ParamSecurity.generate_param(
                entity_type='chat',
                sub_action='list_chat',
                params={'chat_type':3},
                action='wap'
            ),
            'bangpai_params': ParamSecurity.generate_param(
                entity_type='chat',
                sub_action='list_chat',
                params={'chat_type':4},
                action='wap'
            ),
            'xitong_params': ParamSecurity.generate_param(
                entity_type='chat',
                sub_action='list_chat',
                params={'chat_type':1},
                action='wap'
            ),
            'duiwu_params': ParamSecurity.generate_param(
                entity_type='chat',
                sub_action='list_chat',
                params={'chat_type':5},
                action='wap'
            ),
        }

        # 缓存整个响应（不包括玩家特定信息）
        cache.set(cache_key + f"_page_{page}", json.dumps(response_data), 30)  # 缓存30秒

        return render(request, 'chat.html', response_data)
    else:
        pass