const db = require("../src/database/db");

const sendTelegramMessage = async (text) => {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;
  if (!token || !chatId) return false;

  const response = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      parse_mode: "HTML",
      disable_web_page_preview: true,
    }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Telegram API error: ${response.status} ${detail}`);
  }

  return true;
};

const submitContact = async (req, res) => {
  const { name, email, phone, message } = req.body || {};
  if (!name || !phone || !message) {
    return res.status(400).json({ detail: "name, phone, message обязательны" });
  }
  if (String(name).trim().length < 2) {
    return res.status(400).json({ detail: "Имя должно быть не короче 2 символов" });
  }
  if (String(phone).replace(/\D/g, "").length < 10) {
    return res.status(400).json({ detail: "Некорректный телефон" });
  }
  if (email && !/^\S+@\S+\.\S+$/.test(String(email))) {
    return res.status(400).json({ detail: "Некорректный email" });
  }
  if (String(message).trim().length < 3) {
    return res.status(400).json({ detail: "Сообщение слишком короткое" });
  }

  const now = new Date().toISOString();
  const result = db
    .prepare(
      "INSERT INTO contact_messages (name, email, phone, message, created_at) VALUES (?, ?, ?, ?, ?)"
    )
    .run(name, email || "", phone, message, now);

  const telegramText = [
    "<b>Новая заявка из формы связи</b>",
    "",
    `<b>Имя:</b> ${String(name).trim()}`,
    `<b>Телефон:</b> ${String(phone).trim()}`,
    `<b>Email:</b> ${String(email || "не указан").trim()}`,
    `<b>Сообщение:</b> ${String(message).trim()}`,
    `<b>Дата/время:</b> ${new Date().toLocaleString("ru-RU")}`,
  ].join("\n");

  try {
    await sendTelegramMessage(telegramText);
  } catch (error) {
    console.error("Telegram send failed:", error.message);
  }

  return res.status(201).json({ message: "Message sent successfully", id: String(result.lastInsertRowid) });
};

module.exports = { submitContact };