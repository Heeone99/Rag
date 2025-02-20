from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.sessions.backends.db import SessionStore
import json
from .models import User

@csrf_exempt
def signup(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({"error": "아이디와 비밀번호를 입력해주세요."}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({"error": "이미 존재하는 사용자입니다."}, status=400)

            hashed_password = make_password(password)
            User.objects.create(username=username, password=hashed_password)

            return JsonResponse({"message": "회원가입 성공"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({"error": "아이디와 비밀번호를 입력해주세요."}, status=400)

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return JsonResponse({"error": "존재하지 않는 사용자입니다."}, status=401)

            if check_password(password, user.password):
                session = SessionStore()
                session['user_id'] = user.id
                session.create()
                return JsonResponse({"message": "로그인 성공", "session_id": session.session_key}, status=200)
            else:
                return JsonResponse({"error": "비밀번호가 잘못되었습니다."}, status=401)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
