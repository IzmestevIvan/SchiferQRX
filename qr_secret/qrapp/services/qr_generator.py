import base64
import json
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Optional

import qrcode
from PIL import Image


LENGTH_PREFIX_SIZE = 8


def text_to_bits(text: str) -> str:
    return ''.join(format(byte, '08b') for byte in text.encode('utf-8'))


def bits_to_text(bits: str) -> str:
    chars = []
    for index in range(0, len(bits), 8):
        byte = bits[index:index + 8]
        if len(byte) == 8:
            chars.append(chr(int(byte, 2)))
    return ''.join(chars)


def build_secret_payload(secret_text: str = "", expires_at: Optional[str] = None) -> str:
    payload = {
        "v": 1,
        "secret_text": secret_text,
        "expires_at": expires_at,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def parse_secret_payload(raw_text: str) -> dict:
    try:
        payload = json.loads(raw_text)
        if isinstance(payload, dict):
            return {
                "secret_text": payload.get("secret_text", "") or "",
                "expires_at": payload.get("expires_at"),
            }
    except (json.JSONDecodeError, TypeError):
        pass

    return {
        "secret_text": raw_text,
        "expires_at": None,
    }


def calculate_expires_at(lifetime_minutes: Optional[int] = None) -> str:
    if lifetime_minutes is None:
        return None

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=lifetime_minutes)
    return expires_at.isoformat()


def is_expired(expires_at: Optional[str] = None) -> bool:
    if not expires_at:
        return False

    try:
        expires_dt = datetime.fromisoformat(expires_at)
    except ValueError:
        return False

    if expires_dt.tzinfo is None:
        expires_dt = expires_dt.replace(tzinfo=timezone.utc)

    return datetime.now(timezone.utc) >= expires_dt


def embed_secret_in_image(img: Image.Image, secret_text: str) -> Image.Image:
    img = img.convert("RGB")
    pixels = img.load()
    width, height = img.size

    encoded_secret = base64.b64encode(secret_text.encode("utf-8")).decode("utf-8")
    payload = f"{len(encoded_secret):0{LENGTH_PREFIX_SIZE}d}{encoded_secret}"
    bits = text_to_bits(payload)

    capacity = width * height * 3
    if len(bits) > capacity:
        raise ValueError("Секретный текст слишком длинный для этого QR-кода.")

    bit_index = 0

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]

            if bit_index < len(bits):
                r = (r & ~1) | int(bits[bit_index])
                bit_index += 1

            if bit_index < len(bits):
                g = (g & ~1) | int(bits[bit_index])
                bit_index += 1

            if bit_index < len(bits):
                b = (b & ~1) | int(bits[bit_index])
                bit_index += 1

            pixels[x, y] = (r, g, b)

            if bit_index >= len(bits):
                return img

    return img


def extract_secret_from_image(img: Image.Image) -> dict:
    img = img.convert("RGB")
    pixels = img.load()
    width, height = img.size

    bits = []

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            bits.append(str(r & 1))
            bits.append(str(g & 1))
            bits.append(str(b & 1))

    bit_string = ''.join(bits)

    prefix_bits_length = LENGTH_PREFIX_SIZE * 8
    prefix_bits = bit_string[:prefix_bits_length]
    prefix_text = bits_to_text(prefix_bits)

    if not prefix_text.isdigit():
        raise ValueError("Секретный слой не найден или изображение повреждено.")

    secret_length = int(prefix_text)
    secret_bits_length = secret_length * 8

    start = prefix_bits_length
    end = start + secret_bits_length

    secret_bits = bit_string[start:end]
    encoded_secret = bits_to_text(secret_bits)

    if len(encoded_secret) != secret_length:
        raise ValueError("Не удалось корректно извлечь секретный текст.")

    try:
        decoded_secret = base64.b64decode(encoded_secret.encode("utf-8")).decode("utf-8")
    except Exception:
        raise ValueError("Секретный слой найден, но не удалось его расшифровать.")

    payload = parse_secret_payload(decoded_secret)
    payload["expired"] = is_expired(payload.get("expires_at"))
    return payload


def generate_qr_base64(
        public_text: str, secret_text: str = "", 
        lifetime_minutes: Optional[int] = None
    ) -> tuple[str, Optional[str]]:
    qr = qrcode.QRCode(
        version=4,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(public_text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    expires_at = calculate_expires_at(lifetime_minutes)
    payload_text = build_secret_payload(secret_text.strip(), expires_at)

    if secret_text.strip() or expires_at:
        img = embed_secret_in_image(img, payload_text)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
    return image_base64, expires_at
