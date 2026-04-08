const db = require("../src/database/db");

const {
  sendTelegramMessage,
  formatContactTelegramMessage,
} = require('../utils/telegram');

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

  const telegramText = formatContactTelegramMessage({
    name: String(name).trim(),
    phone: String(phone).trim(),
    email: String(email || '').trim(),
    message: String(message).trim(),
  });

  let telegramDelivered = true;
  try {
    await sendTelegramMessage(telegramText);
  } catch (error) {
    telegramDelivered = false;
    console.error("Telegram send failed:", error.message);
  }

  return res.status(201).json({
    message: "Message sent successfully",
    id: String(result.lastInsertRowid),
    telegramDelivered,
  });
};

module.exports = { submitContact };
