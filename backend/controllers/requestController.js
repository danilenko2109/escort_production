const db = require("../src/database/db");

const ALLOWED_DURATIONS = ["1h", "2h", "3h"];

const submitBookingRequest = (req, res) => {
  const {
    profileCode,
    duration,
    bookingDate,
    bookingTime,
    clientName,
    clientPhone,
    extras,
    comment,
  } = req.body || {};

  if (!profileCode || !ALLOWED_DURATIONS.includes(duration)) {
    return res.status(400).json({ detail: "profileCode и duration (1h|2h|3h) обязательны" });
  }

  if (bookingDate && !/^\d{4}-\d{2}-\d{2}$/.test(String(bookingDate))) {
    return res.status(400).json({ detail: "Некорректная дата заявки" });
  }
  if (bookingTime && !/^\d{2}:\d{2}$/.test(String(bookingTime))) {
    return res.status(400).json({ detail: "Некорректное время заявки" });
  }
  if (clientName && String(clientName).trim().length < 2) {
    return res.status(400).json({ detail: "Имя должно быть не короче 2 символов" });
  }
  if (clientPhone && String(clientPhone).replace(/\D/g, "").length < 10) {
    return res.status(400).json({ detail: "Некорректный телефон" });
  }
  if (extras !== undefined && !Array.isArray(extras)) {
    return res.status(400).json({ detail: "extras должен быть массивом" });
  }
  if (comment && String(comment).length > 2000) {
    return res.status(400).json({ detail: "Комментарий слишком длинный" });
  }

  const bookingPhone = db.prepare("SELECT value FROM settings WHERE key = ?").get("booking_phone")?.value || "";

  return res.status(201).json({
    message: "Заявка принята",
    phone: bookingPhone || "+7 (900) 000-00-00",
  });
};

module.exports = { submitBookingRequest };