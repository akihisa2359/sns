from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import authenticate

from .models import Message,Friend,Group,Good
from .forms import GroupCheckForm,GroupSelectForm,\
        SearchForm,FriendsForm,CreateGroupForm,PostForm, SignUpForm

from django.db.models import Q
from django.contrib.auth.decorators import login_required

# indexのビュー関数
@login_required(login_url='/sns/login/')
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
            
        if request.POST['mode'] == '__search_form__':
            searchform = SearchForm(request.POST)
            checkform = GroupCheckForm(request.user)
            groups = Group.objects.filter(owner=request.user)
            glist = [public_group]
            for group in groups:
                glist.append(group)
            messages = get_your_group_message(request.user, glist, \
                                              request.POST['search'])
            
    else:
        searchform = SearchForm()
        checkform = GroupCheckForm(request.user)
        groups = Group.objects.filter(owner=request.user)
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
@login_required(login_url='/sns/login/')
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
            # 選択したGroupが　'-'出会った場合の処理
            if sel_group == None:
                messages.info(request, ' Groupを選択してください。')
                return redirect(to='/sns/groups')
            check_friend_names = request.POST.getlist('friends')
            check_users = User.objects.filter(username__in=check_friend_names)
            friends = Friend.objects.filter(owner = request.user) \
                        .filter(user__in=check_users)
            userlist = []
            for friend in friends:
                friend.group = sel_group
                friend.save()
                userlist.append(friend.user.username)
            messages.success(request, ' チェックされたFriendを' + \
                            sel_group_name + ' に登録しました')                
            groupsform = GroupSelectForm(request.user, {'groups':sel_group})
            friendsform = FriendsForm(request.user, \
                                     friends=friends, vals=userlist)
    
    #GETアクセス時
    else:
        groupsform = GroupSelectForm(request.user)
        friendsform = FriendsForm(request.user, friends=friends, vals=[])
        sel_group_name = '-'
            
    createform = CreateGroupForm()
    params = {
            'login_user':request.user,
            'groups_form':groupsform,
            'friends_form':friendsform,
            'create_form':createform,
            'group_name':sel_group_name,
            }
    return render(request, 'sns/groups.html', params)

#Friendの追加処理     
@login_required(login_url='/sns/login/')
def add(request):
    add_name = request.GET['name']
    add_user = User.objects.get(username=add_name)
    #自身をaddしようとした場合の処理
    if add_user == request.user:
        messages.info(request, "自分自身をFriendに追加することはできません。")
        return redirect(to='/sns')
    #既にFriendである場合の処理
    friend_num = Friend.objects.filter(owner=request.user) \
                                .filter(user=add_user).count()
    # friend_numが1であれば、既に登録されているということ
    if friend_num > 0:
        messages.info(request, add_user.username + \
                      ' はすでに追加されています。')
        return redirect(to='/sns')
    (public_user, public_group) = get_public()
    #Friendの登録処理
    friend_obj = Friend()
    friend_obj.owner = request.user
    friend_obj.user = add_user
    friend_obj.group = public_group
    friend_obj.save()
    messages.success(request, add_user.username + ' を追加しました! \
                     groupページに移動して、追加したFriendをメンバーに設定してください。')
    return redirect(to='/sns')
#Groupの作成処理
@login_required(login_url='/sns/login/')
def creategroup(request):
    group_name = request.POST['group_name']
    group_num = Group.objects.filter(owner=request.user) \
                            .filter(title=group_name).count()
    if group_num > 0:
        messages.info(request, group_name + ' はすでに存在します。')
        return redirect(to='/sns/groups')
    #Groupの登録
    group_obj = Group()
    group_obj.owner = request.user
    group_obj.title = group_name
    group_obj.save()
    messages.info(request, '新しいグループを追加しました。')
    return redirect(to='/sns/groups')
     
#メッセージのポスト処理
@login_required(login_url='/sns/login/')
def post(request):
    if request.method == 'POST':
        content = request.POST['content']
        group_name = request.POST['groups']
        group_obj = Group.objects.filter(owner=request.user) \
                                .filter(title=group_name).first()                       
        if group_obj == None:
            (pub_user, group_obj) = get_public()
        msg = Message()
        msg.owner = request.user
        msg.group = group_obj
        msg.content = content
        msg.save()
        messages.success(request, '新しいメッセージを投稿しました。')
        return redirect(to='/sns')
    #GETアクセス時
    else:
        postform = PostForm(request.user)
    
    params = {
            'login_user':request.user,
            'form':postform,
            }
    return render(request, 'sns/post.html', params)
        
@login_required(login_url='/sns/login/')
def share(request, share_id):
    share_message = Message.objects.get(id=share_id)
    
    if request.method == 'POST':
        group_name = request.POST['groups']
        content = request.POST['content']
        group = Group.objects.filter(owner=request.user) \
                            .filter(title=group_name).first()
        if group == None:
            (pub_user, group) = get_public()
        message = Message()
        message.owner = request.user
        message.group = group
        message.content = content
        message.share_id = share_message.id
        message.save()
        share_message.share_count += 1
        share_message.save()
        messages.success(request, 'メッセージをシェアしました。')
        return redirect(to='/sns')
    
    form = PostForm(request.user)
    params = {
            'login_user':request.user,
            'form':form,
            'share':share_message,
            }
    return render(request, 'sns/share.html', params)
    
@login_required(login_url='/sns/login/')
def good(request, good_id):
    
    good_message = Message.objects.get(id=good_id)
    is_good = Good.objects.filter(owner=request.user) \
                        .filter(message=good_message).count()
    if is_good > 0:
        messages.success(request, '既にメッセージにはGoodしています。')
        return redirect(to='/sns')
    
    good_message.good_count += 1
    good_message.save()
    
    good = Good()
    good.owner = request.user
    good.message =  good_message
    good.save()
    
    messages.success(request, 'メッセージにGoodしました。')
    return redirect(to='/sns')

def get_your_group_message(owner, glist, find):
    (public_user, public_group) = get_public()

    #ログインユーザーがチェックしたグループインスタンスを取得する
    check_groups = Group.objects.filter(Q(owner=owner) | Q(owner=public_user)) \
                                .filter(title__in=glist)
                                
    check_friends = Friend.objects.filter(group__in=check_groups)
    check_users = []
    for friend in check_friends:
        check_users.append(friend.user)
    #選択したグループに所属するユーザーが保持するグループ              
    target_users_groups = Group.objects.filter(owner__in=check_users)
    #ここで得られるFriendインスタンスは、チェックしたグループに所属するユーザーが、
    #ログインユーザーをメンバーに持つグループを取得するためのもの
    target_friends = Friend.objects.filter(group__in=target_users_groups) \
                                    .filter(user=owner)

    # 表示したいユーザーが作成した、ログインユーザーが所属するグループ
    me_belong_groups = []
    for friend in target_friends:
        me_belong_groups.append(friend.group)
        
    if find==None:
        messages = Message.objects.filter(Q(group__in=me_belong_groups) \
                                    |Q(group__in=check_groups))[:100]
    else:
        messages = Message.objects.filter(Q(group__in=me_belong_groups) \
                                          |Q(group__in=check_groups)) \
                                            .filter(content__contains=find)[:100]
    return messages
    
def get_public():
    public_user = User.objects.get(username='public')
    public_group = Group.objects.get(owner=public_user)
    return (public_user, public_group)

#ユーザー登録処理
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(to='/sns')
    else:
        form = SignUpForm()
    return render(request, 'sns/signup.html', {'form':form})

#ログイン処理
def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect(to='/sns')
        else:
            messages.info(request, 'ユーザー名/パスワードが正しくありません。')

    return render(request, 'sns/login.html')













