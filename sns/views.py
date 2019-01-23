from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib import messages

from .models import Message,Friend,Group,Good
from .forms import GroupCheckForm,GroupSelectForm,\
        SearchForm,FriendsForm,CreateGroupForm,PostForm

from django.db.models import Q
from django.contrib.auth.decorators import login_required

# indexのビュー関数
@login_required(login_url='/admin/login/')
def index(request):
    (public_user, public_group) = get_public()
    
    if request.method == 'POST':
        
        if request.POST['mode'] == '__check_form__':
            #フォームの作成
            searchform = SearchForm()
            checkform = GroupCheckForm(request.user, request.POST)
            #選択されたグループ名の取得
            glist = []
            #グループ名のループ
            for group in request.POST.getlist('groups'):
                glist.append(group)
            #チェックしたグループに所属するメッセージの取得
            messages = get_your_group_message(request.user, glist, None)
            
        if request.POST['made'] == '__search_form__':
            searchform = SearchForm(request.POST)
            checkform = GroupCheckForm(request.user)
            groups = Group.object.filter(owner=request.user)
            glist = [public_group]
            for group in groups:
                glist.append(group)
            messages = get_your_group_message(request.user, glist, \
                                              request.POST['search'])
            
        else:
            searchform = SearchForm()
            checkform = GroupCheckForm(request.user)
            groups = Group.object.filter(owner=request.user)
            glist = [public_group]
            for group in groups:
                glist.append(group)
            messages = get_your_group_message(request.user, glist, None)
            
        params = {
                'login_user':request.user,
                'contents':messages,
                'check_form':checkform,
                'search_form':searchform,
                }
            
        return render(request, 'sns/index.html', params)
     
#group編集画
    
@login_required(login_url='/admin/login/')
def groups(request):
    friends = Friend.objects.filter(owner=request.user)

    #POSTアクセス時    
    if request.method == 'POST': 
        if request.POST['mode'] == '__groups_form__':
            sel_group_name = request.POST['groups']
            sel_group = Group.objects.filter(owner=request.user) \
                        .filter(title=sel_group_name).first()        
            check_friends = Friend.objects.filter(owner=request.user) \
                                            .filter(group=sel_group)                                
            userlist = []
            for friend in check_friends:
                userlist.append(friend.user.username)       
            groupsform =GroupSelectForm(request.user, request.POST)
            friendsform = FriendsForm(request.user, \
                                      friends = friends, vals = userlist)
                                        
        if request.POST['mode'] == '__friends_form__':
            sel_group_name = request.POST['group']
            sel_group = Group.objects.filter(owner=request.user) \
                        .filter(title=sel_group_name).first()
            check_friend_names = request.POST.getlist('friends')
            check_users = User.objects.filter(username__in=check_friend_names)
            friends = Friend.objects.filter(owner = request.user) \
                        .filter(user__in=check_users)
            userlist = []
            for friend in friends:
                friend.group = sel_group
                friend.save()
                vlist.append(friend.user.username)
            message.success(request, ' チェックされたFriendを' + \
                            sel_group_name + ' に登録しました')                
            groupsform = GroupSelectForm(request.user, {'groups':sel_group})
            friendform = FriendsForm(request.user, \
                                     friends=friends, vals=userlist)
    
    #GETアクセス時
    else:
        groupsform = GroupSelectForm(request.user)
        friendform = FriendsForm(request.user, friends=friends, vals=[])
        sel_group_name = '-'
            
     createform = CreateGroupForm()
     params = {
             'login_user':request.user,
             'groups_form':groupsform,
             'friends_form':friendsform,
             'crete_form':createform,
             'group_name':sel_group_name,
             }

#Friendの追加処理     
@login_required(login_url='/admin/login/')
def add(request):
    friend_name = request.POST['friend']
    
        

     

def get_your_group_message(owner, glist, find):
    (public_user, public_group) = get_public()

    #ログインユーザーがチェックしたグループインスタンスを取得する
    check_groups = Group.objects.filter(Q(owner=owner) | Q(owner=public_user)) \
                                .filter(title__in=glist)
                                
    check_friends = Friend.objects.filter(groups__in=check_groups)
    check_users = []
    for friend in check_friends:
        check_users.append(friend.user)
    #選択したグループに所属するユーザーが保持するグループ              
    target_users_groups = Group.objects.filter(owener__in=check_users)
    #ここで得られるFriendインスタンスは、チェックしたグループに所属するユーザーが、
    #ログインユーザーをメンバーに持つグループを取得するためのもの
    target_friends = Friend.objects.filter(group__in=target_users_groups) \
                                    .filter(user=owner)

    # 表示したいユーザーが作成した、ログインユーザーが所属するグループ
    me_belong_groups = []
    for friend in target_friends:
        me_belong_groups.append(friend.group)
        
    if find==None:
        messages = Message.objects.filter(group__in=me_belong_groups)[:100]
    else:
        messages = Message.objects.filter(group__in=me_belong_groups) \
                                    .filter(content__contains=find)[:100]
    return messages
    
def get_public():
    public_user = User.objects.get(username='public')
    public_group = Group.objects.get(owner=public_user)
    return (public_user, public_group)



















