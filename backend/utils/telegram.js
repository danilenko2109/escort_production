const TELEGRAM_API_URL = 'https://api.telegram.org';

const escapeHtml = (value) => String(value ?? '')
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;');

const formatDateTime = () => new Date().toLocaleString('ru-RU', { hour12: false });

const parseChatIds = () => {
  const rawChatIds = String(process.env.TELEGRAM_CHAT_ID || '').trim();
  if (!rawChatIds) {
    return [];
  }

  return rawChatIds
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean);
};

const validateConfig = () => {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  if (!token) {
    throw new Error('TELEGRAM_BOT_TOKEN не задан');
  }

  const tokenLooksValid = /^\d+:[\w-]{20,}$/.test(token);
  if (!tokenLooksValid) {
    throw new Error('TELEGRAM_BOT_TOKEN имеет некорректный формат');
  }

  const chatIds = parseChatIds();
  if (!chatIds.length) {
    throw new Error('TELEGRAM_CHAT_ID не задан');
  }

  const hasInvalidChatIds = chatIds.some((id) => !/^-?\d+$/.test(id));
  if (hasInvalidChatIds) {
    throw new Error('TELEGRAM_CHAT_ID должен содержать число или список чисел через запятую');
  }

  return { token, chatIds };
};

const callTelegram = async (token, method, payload) => {
  const response = await fetch(`${TELEGRAM_API_URL}/bot${token}/${method}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.ok === false) {
    const detail = data?.description || response.statusText || 'Unknown Telegram API error';
    throw new Error(`Telegram API error: ${response.status} ${detail}`);
  }

  return data;
};

const sendTelegramMessage = async (text, options = {}) => {
  const { token, chatIds } = validateConfig();

  const payloadBase = {
    text,
    parse_mode: 'HTML',
    disable_web_page_preview: true,
    disable_notification: Boolean(options.disableNotification),
  };

  await Promise.all(
    chatIds.map((chatId) =>
      callTelegram(token, 'sendMessage', {
        ...payloadBase,
        chat_id: chatId,
        ...(options.replyMarkup ? { reply_markup: options.replyMarkup } : {}),
      })
    )
  );

  return true;
};

const formatContactTelegramMessage = ({ name, email, phone, message }) => {
  const safeEmail = email ? escapeHtml(email) : 'не указан';

  return [
    '📩 <b>Новая заявка из формы связи</b>',
    '',
    `👤 <b>Имя:</b> ${escapeHtml(name)}`,
    `📞 <b>Телефон:</b> ${escapeHtml(phone)}`,
    `✉️ <b>Email:</b> ${safeEmail}`,
    `💬 <b>Сообщение:</b> ${escapeHtml(message)}`,
    `🕒 <b>Дата/время:</b> ${escapeHtml(formatDateTime())}`,
  ].join('\n');
};

const formatBookingTelegramMessage = ({
  profileCode,
  duration,
  bookingDate,
  bookingTime,
  clientName,
  clientPhone,
  extras,
  comment,
}) => {
  const extrasText = Array.isArray(extras) && extras.length
    ? extras.map((item) => escapeHtml(item)).join(', ')
    : 'нет';

  return [
    '🔥 <b>Новая заявка на анкету</b>',
    '',
    `🆔 <b>Код анкеты:</b> ${escapeHtml(profileCode)}`,
    `⏳ <b>Длительность:</b> ${escapeHtml(duration)}`,
    `📅 <b>Дата:</b> ${escapeHtml(bookingDate || 'не указана')}`,
    `⏰ <b>Время:</b> ${escapeHtml(bookingTime || 'не указано')}`,
    `👤 <b>Имя клиента:</b> ${escapeHtml(clientName || 'не указано')}`,
    `📞 <b>Телефон:</b> ${escapeHtml(clientPhone || 'не указан')}`,
    `✨ <b>Доп. услуги:</b> ${extrasText}`,
    `📝 <b>Комментарий:</b> ${escapeHtml(comment || 'нет')}`,
    `🕒 <b>Создано:</b> ${escapeHtml(formatDateTime())}`,
  ].join('\n');
};

module.exports = {
  sendTelegramMessage,
  formatContactTelegramMessage,
  formatBookingTelegramMessage,
};
