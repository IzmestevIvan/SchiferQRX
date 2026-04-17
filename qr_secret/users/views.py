from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import RegisterForm
from .models import UserActivity


def register_view(request):
    """View-функция для регистрации пользователя."""
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})


@login_required
def profile_view(request):
    """View-функция для профиля."""
    user = request.user
    profile = user.profile
    achievements = user.user_achievements.select_related(
        'achievement').order_by('-unlocked_at')[:6]
    recent_activities = user.activities.order_by('-created_at')[:8]
    activity_counts = (
        user.activities.values('action_type')
        .annotate(total=Count('id'))
        .order_by()
    )
    chart_data = {
        'generate': 0,
        'decode': 0,
        'download': 0,
    }
    for item in activity_counts:
        chart_data[item['action_type']] = item['total']
    context = {
        'user': user,
        'profile': profile,
        'achievements': achievements,
        'recent_activities': recent_activities,
        'achievement_count': user.user_achievements.count(),
        'chart_generate': chart_data['generate'],
        'chart_decode': chart_data['decode'],
        'chart_download': chart_data['download'],
    }
    return render(request, 'users/profile.html', context)


@login_required
@require_POST
def track_download_view(request):
    profile = request.user.profile
    profile.total_downloaded += 1
    profile.save(update_fields=['total_downloaded'])
    UserActivity.objects.create(user=request.user, action_type='download')
    return JsonResponse({'success': True})