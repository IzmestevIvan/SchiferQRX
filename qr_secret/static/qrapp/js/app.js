const textInput = document.getElementById("textInput");
const secretInput = document.getElementById("secretInput");
const generateBtn = document.getElementById("generateBtn");
const previewInner = document.getElementById("previewInner");
const previewMeta = document.getElementById("previewMeta");
const errorMessage = document.getElementById("errorMessage");

const downloadBtn = document.getElementById("downloadBtn");
const sendToDecodeBtn = document.getElementById("sendToDecodeBtn");

const decodeInput = document.getElementById("decodeInput");
const decodeBtn = document.getElementById("decodeBtn");
const decodeErrorMessage = document.getElementById("decodeErrorMessage");
const secretResult = document.getElementById("secretResult");
const decodePreview = document.getElementById("decodePreview");

const lifetimeToggle = document.getElementById("lifetimeToggle");
const lifetimeToggleLabel = document.getElementById("lifetimeToggleLabel");
const lifetimeControls = document.getElementById("lifetimeControls");
const lifetimeInput = document.getElementById("lifetimeInput");
const lifetimeHint = document.getElementById("lifetimeHint");
const presetChips = Array.from(document.querySelectorAll(".preset-chip"));

let currentQrDataUrl = null;
let currentQrBlob = null;

function syncLifetimeUi() {
  const hasLifetime = lifetimeToggle.checked;
  lifetimeControls.classList.toggle("is-hidden", !hasLifetime);
  lifetimeToggleLabel.textContent = hasLifetime ? "Есть срок" : "Бессрочный";

  if (!hasLifetime) {
    lifetimeInput.value = "";
    presetChips.forEach((chip) => chip.classList.remove("is-active"));
    lifetimeHint.textContent = "Код будет жить без ограничения по времени.";
    return;
  }

  if (!lifetimeInput.value) {
    lifetimeInput.value = "15";
  }

  updateLifetimeHint();
  syncPresetSelection();
}

function syncPresetSelection() {
  const value = lifetimeInput.value.trim();
  presetChips.forEach((chip) => {
    chip.classList.toggle("is-active", chip.dataset.minutes === value);
  });
}

function updateLifetimeHint() {
  if (!lifetimeToggle.checked) {
    lifetimeHint.textContent = "Код будет жить без ограничения по времени.";
    return;
  }

  const minutes = Number.parseInt(lifetimeInput.value, 10);
  if (!Number.isInteger(minutes) || minutes < 1) {
    lifetimeHint.textContent = "Минимальный срок жизни — 1 минута.";
    return;
  }

  lifetimeHint.textContent = `Скрытый слой будет доступен ${formatDuration(minutes)} с момента генерации.`;
}

function getLifetimeMinutes() {
  if (!lifetimeToggle.checked) {
    return null;
  }

  const minutes = Number.parseInt(lifetimeInput.value, 10);
  if (!Number.isInteger(minutes) || minutes < 1) {
    throw new Error("Минимальный срок жизни QR-кода — 1 минута.");
  }

  return minutes;
}

async function generateQr() {
  const publicText = textInput.value.trim();
  const secretText = secretInput.value.trim();
  errorMessage.textContent = "";
  if (!publicText) {
    errorMessage.textContent = "Пожалуйста, введите открытый текст.";
    return;
  }

  let lifetimeMinutes = null;
  try {
    lifetimeMinutes = getLifetimeMinutes();
  } catch (error) {
    errorMessage.textContent = error.message;
    return;
  }

  generateBtn.disabled = true;
  generateBtn.textContent = "Генерация...";

  try {
    const response = await fetch("/api/generate/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({
            public_text: publicText,
            secret_text: secretText,
            lifetime_minutes: lifetimeMinutes,
        }),
    });
    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.error || "Не удалось сгенерировать QR-код.");
    }
    currentQrDataUrl = data.qr_code;
    currentQrBlob = await dataUrlToBlob(data.qr_code);
    previewInner.innerHTML = `
      <div class="qr-stage">
        <img src="${data.qr_code}" alt="QR Code" class="qr-image">
      </div>
    `;
    renderPreviewMeta(data);
    downloadBtn.disabled = false;
    sendToDecodeBtn.disabled = false;
  } catch (error) {
    errorMessage.textContent = error.message;
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = "Сгенерировать QR";
  }
}

function renderPreviewMeta(data) {
  if (!data.has_lifetime || !data.expires_at) {
    previewMeta.innerHTML = `
      <div class="status-chip status-chip--infinite">Бессрочный QR-код</div>
    `;
    return;
  }

  const expiresAt = new Date(data.expires_at);
  previewMeta.innerHTML = `
    <div class="status-chip status-chip--timed">Живёт до ${formatDateTime(expiresAt)}</div>
  `;
}

async function decodeSecret() {
  decodeErrorMessage.textContent = "";
  secretResult.innerHTML = `<p class="secret-result__placeholder">Идёт извлечение скрытого текста...</p>`;

  const file = decodeInput.files[0];

  if (!file) {
    decodeErrorMessage.textContent = "Пожалуйста, выберите изображение.";
    secretResult.innerHTML = `<p class="secret-result__placeholder">Секретный текст появится здесь</p>`;
    return;
  }
  const formData = new FormData();
  formData.append("image", file);
  decodeBtn.disabled = true;
  decodeBtn.textContent = "Извлечение...";
  try {
    const response = await fetch("/api/decode/", {
        method: "POST",
        headers: {
            "X-CSRFToken": csrfToken,
        },
        body: formData,
    });
    const data = await response.json();
    if (!response.ok || !data.success) {
      if (data.expired) {
        throw new Error(`Срок жизни QR-кода истёк${data.expires_at ? ` (${formatDateTime(new Date(data.expires_at))})` : ""}.`);
      }
      throw new Error(data.error || "Не удалось извлечь секрет.");
    }

    const lifetimeBlock = data.expires_at
      ? `<p class="secret-result__meta">Доступен до ${formatDateTime(new Date(data.expires_at))}</p>`
      : `<p class="secret-result__meta">QR-код без ограничения по времени</p>`;

    secretResult.innerHTML = `
      <div class="secret-result__content">
        <p class="secret-result__label">Secret message</p>
        ${lifetimeBlock}
        <p class="secret-result__text">${escapeHtml(data.secret_text)}</p>
      </div>
    `;
  } catch (error) {
    decodeErrorMessage.textContent = error.message;
    secretResult.innerHTML = `<p class="secret-result__placeholder">Секретный текст появится здесь</p>`;
  } finally {
    decodeBtn.disabled = false;
    decodeBtn.textContent = "Извлечь секрет";
  }
}

async function downloadQr() {
  if (!currentQrDataUrl) return;

  const link = document.createElement("a");
  link.href = currentQrDataUrl;
  link.download = "schiferqrx-code.png";
  document.body.appendChild(link);
  link.click();
  link.remove();

  try {
    await fetch("/accounts/profile/track-download/", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
      },
    });
  } catch (error) {
    console.error("Не удалось сохранить download activity", error);
  }
}

async function sendQrToDecode() {
  if (!currentQrBlob || !currentQrDataUrl) return;

  const file = new File([currentQrBlob], "schiferqrx-code.png", { type: "image/png" });

  const dataTransfer = new DataTransfer();
  dataTransfer.items.add(file);
  decodeInput.files = dataTransfer.files;

  decodePreview.innerHTML = `
    <img src="${currentQrDataUrl}" alt="QR for decode" class="decode-preview__image">
  `;

  secretResult.innerHTML = `<p class="secret-result__placeholder">Секретный текст появится здесь</p>`;
  decodeErrorMessage.textContent = "";

  const decodeSection = document.querySelector(".decode-card");
  decodeSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function updateDecodePreviewFromFile() {
  const file = decodeInput.files[0];

  if (!file) {
    decodePreview.innerHTML = `
      <p class="decode-preview__placeholder">
        Сюда можно загрузить файл или перенести только что созданный QR
      </p>
    `;
    return;
  }

  const reader = new FileReader();
  reader.onload = (event) => {
    decodePreview.innerHTML = `
      <img src="${event.target.result}" alt="Uploaded QR" class="decode-preview__image">
    `;
  };
  reader.readAsDataURL(file);
}

async function dataUrlToBlob(dataUrl) {
  const response = await fetch(dataUrl);
  return await response.blob();
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDuration(totalMinutes) {
  if (totalMinutes < 60) {
    return `${totalMinutes} ${pluralize(totalMinutes, "минуту", "минуты", "минут")}`;
  }

  if (totalMinutes % 1440 === 0) {
    const days = totalMinutes / 1440;
    return `${days} ${pluralize(days, "день", "дня", "дней")}`;
  }

  if (totalMinutes % 60 === 0) {
    const hours = totalMinutes / 60;
    return `${hours} ${pluralize(hours, "час", "часа", "часов")}`;
  }

  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return `${hours} ${pluralize(hours, "час", "часа", "часов")} ${minutes} ${pluralize(minutes, "минута", "минуты", "минут")}`;
}

function pluralize(number, one, two, five) {
  const n = Math.abs(number) % 100;
  const n1 = n % 10;
  if (n > 10 && n < 20) return five;
  if (n1 > 1 && n1 < 5) return two;
  if (n1 === 1) return one;
  return five;
}

function formatDateTime(date) {
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

presetChips.forEach((chip) => {
  chip.addEventListener("click", () => {
    lifetimeInput.value = chip.dataset.minutes;
    syncPresetSelection();
    updateLifetimeHint();
  });
});

lifetimeToggle.addEventListener("change", syncLifetimeUi);
lifetimeInput.addEventListener("input", () => {
  syncPresetSelection();
  updateLifetimeHint();
});

generateBtn.addEventListener("click", generateQr);
decodeBtn.addEventListener("click", decodeSecret);
downloadBtn.addEventListener("click", downloadQr);
sendToDecodeBtn.addEventListener("click", sendQrToDecode);
decodeInput.addEventListener("change", updateDecodePreviewFromFile);

syncLifetimeUi();
