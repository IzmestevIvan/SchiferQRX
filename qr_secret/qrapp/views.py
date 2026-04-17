import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from PIL import Image

from .services.qr_generator import generate_qr_base64, extract_secret_from_image
from users.models import UserActivity


@login_required
@require_GET
def index(request):
    return render(request, "qrapp/index.html")


@login_required
@require_POST
def generate_qr(request):
    try:
        data = json.loads(request.body)
        public_text = data.get("public_text", "").strip()
        secret_text = data.get("secret_text", "").strip()
        lifetime_minutes = data.get("lifetime_minutes")

        if not public_text:
            return JsonResponse(
                {"success": False, "error": "Введите открытый текст для генерации QR-кода."},
                status=400
            )

        if lifetime_minutes in ("", None):
            lifetime_minutes = None
        else:
            try:
                lifetime_minutes = int(lifetime_minutes)
            except (TypeError, ValueError):
                return JsonResponse(
                    {"success": False, "error": "Срок жизни QR-кода должен быть целым числом минут."},
                    status=400
                )

            if lifetime_minutes < 1:
                return JsonResponse(
                    {"success": False, "error": "Минимальный срок жизни QR-кода — 1 минута."},
                    status=400
                )

            if lifetime_minutes > 43200:
                return JsonResponse(
                    {"success": False, "error": "Слишком большой срок жизни. Максимум — 43200 минут (30 дней)."},
                    status=400
                )

        qr_base64, expires_at = generate_qr_base64(public_text, secret_text, lifetime_minutes)

        profile = request.user.profile
        profile.total_generated += 1
        profile.save(update_fields=['total_generated'])

        UserActivity.objects.create(user=request.user, action_type='generate')

        return JsonResponse({
            "success": True,
            "qr_code": f"data:image/png;base64,{qr_base64}",
            "expires_at": expires_at,
            "has_lifetime": expires_at is not None,
        })

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Некорректный JSON."},
            status=400
        )
    except Exception as error:
        return JsonResponse(
            {"success": False, "error": str(error)},
            status=500
        )


@login_required
@require_POST
def decode_qr_secret(request):
    try:
        uploaded_file = request.FILES.get("image")

        if not uploaded_file:
            return JsonResponse(
                {"success": False, "error": "Загрузите изображение с QR-кодом."},
                status=400
            )

        image = Image.open(uploaded_file)
        payload = extract_secret_from_image(image)

        if payload.get("expired"):
            return JsonResponse(
                {
                    "success": False,
                    "error": "Срок жизни этого QR-кода уже истёк.",
                    "expired": True,
                    "expires_at": payload.get("expires_at"),
                },
                status=410
            )

        profile = request.user.profile
        profile.total_decoded += 1
        profile.save(update_fields=['total_decoded'])

        UserActivity.objects.create(user=request.user, action_type='decode')

        return JsonResponse({
            "success": True,
            "secret_text": payload.get("secret_text", ""),
            "expires_at": payload.get("expires_at"),
            "expired": False,
        })

    except ValueError as error:
        return JsonResponse(
            {"success": False, "error": str(error)},
            status=400
        )
    except Exception as error:
        return JsonResponse(
            {"success": False, "error": f"Ошибка обработки файла: {error}"},
            status=500
        )
