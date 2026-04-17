from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """Модель для хранения данных пользователя."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    avatar_bg = models.CharField(max_length=50, default='violet')
    level_name = models.CharField(max_length=120, default='Cipher Member')
    total_generated = models.PositiveIntegerField(default=0)
    total_decoded = models.PositiveIntegerField(default=0)
    total_downloaded = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.display_name or self.user.username


class Achievement(models.Model):
    """Модель для хранения данных об ачивках."""
    code = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=120)
    description = models.TextField()
    icon = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return self.title


class UserAchievement(models.Model):
    """Связка пользователь - ачивка."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')


class UserActivity(models.Model):
    """
    Модель для хранения данных об использовании пользователем функций,
    для хранения истории.
    """
    ACTION_CHOICES = [
        ('generate', 'Generate QR'),
        ('decode', 'Decode secret'),
        ('download', 'Download QR'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.action_type}'