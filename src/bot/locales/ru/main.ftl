# Welcome messages
welcome = 👋 Добро пожаловать в Lingooru!
welcome-choose-lang = Выбери язык интерфейса:
welcome-choose-pair = Какой язык изучаешь?

# Language names
lang-ru = 🇷🇺 Русский
lang-en = 🇬🇧 English
lang-ko = 🇰🇷 한국어

# Language pairs
pair-en-ru = 🇬🇧 Английский → 🇷🇺 Русский
pair-ko-ru = 🇰🇷 Корейский → 🇷🇺 Русский

# Main menu
menu-title = 🎓 Lingooru
menu-subtitle = Твой помощник в изучении языков
menu-stats = 📊 Выучено: { $learned } из { $total } слов
menu-stats-by-lang = { $flag }: { $learned }/{ $total }
menu-streak = 🔥 Streak: { $days } дней

# Buttons
btn-learn = 📚 Учить
btn-review = 🔄 Повторять
btn-stats = 📊 Статистика
btn-settings = ⚙️ Настройки
btn-menu = 📋 Меню
btn-lang = 🌐 Язык
btn-pair = 📖 Пара
btn-back = ⬅️ Назад
btn-add-words-menu = ➕ Добавить слова

# Settings
settings-title = ⚙️ Настройки
settings-lang = 🌐 Язык интерфейса: { $lang }
settings-pair = 📖 Изучаю: { $pair }
settings-saved = ✅ Настройки сохранены!

# Learning
learn-no-words = 📚 В твоём словаре пока нет слов для изучения.
    Добавь слова, отправив их текстом, или выбери из готовых списков!

learn-no-words-for-pair = 📚 В текущей языковой паре нет слов для изучения.
    Добавь слова, отправив их текстом, или выбери из готовых списков!

learn-choose-lang = 📚 Выбери язык для изучения:

learn-card = 📚 Изучение ({ $position }/{ $total })

    🔊 { $word }{ $phonetic }

    <tg-spoiler>{ $translation }</tg-spoiler>{ $example }

learn-session-complete = ✅ Сессия завершена!
    Ты изучил { $count } слов.

learn-session-ended = Сессия завершена!

# Words
word-added = ✅ Слово добавлено!

    🔊 { $word }{ $phonetic }

    { $translation }

word-already-exists = ⚠️ Это слово уже есть в твоём словаре.

word-not-found-enter-translation = 📝 Слово "{ $word }" не найдено в словаре.
    Введи перевод вручную:

word-add-prompt = 📝 Отправь слово, которое хочешь добавить:

word-add-error = ❌ Не удалось добавить слово. Попробуй ещё раз.

word-removed = ✅ Слово удалено из словаря.

# Vocabulary
vocab-title = 📖 Мой словарь ({ $total } слов)

vocab-empty = 📖 Твой словарь пока пуст.
    Добавь первое слово, отправив его текстом!

# Word lists
lists-title = 📋 Выбери тематический список:

lists-empty = 📋 Для этого языка пока нет готовых списков.

list-preview-words = Слов в списке: { $count }

list-and-more = ещё { $count }...

list-not-found = Список не найден.

list-added = ✅ Список "{ $list_name }" добавлен!

    Добавлено слов: { $added }
    Пропущено (уже есть): { $skipped }

# Additional buttons
btn-know = ✅ Знаю
btn-hard = 🤔 Сложно
btn-forgot = ❌ Забыл
btn-skip = ⏭️ Пропустить
btn-add-more = ➕ Ещё
btn-add-words = ➕ Добавить
btn-word-lists = 📋 Списки
btn-my-vocab = 📖 Словарь
btn-learn-again = 🔄 Ещё раз
btn-add-list = ➕ Добавить список
btn-more-lists = 📋 Другие списки
btn-list-added = ✅ Добавлено

list-already-added = Этот список уже добавлен.

# Language selection
btn-mix = Микс

# Audio
btn-play-audio = 🔊 Прослушать
audio-loading = ⏳ Загружаю аудио...
audio-not-available = ❌ Аудио недоступно для этого слова
audio-error = ❌ Ошибка воспроизведения

# Misc
coming-soon = 🚧 Скоро будет доступно!

# Review (SM-2)
review-start = 🔄 Повторение

    📊 Слов на сегодня: { $count }

review-no-words-due = ✅ Отлично! На сегодня повторений нет.
    Возвращайся позже или учи новые слова!

review-question = 🔄 Повторение ({ $position }/{ $total })

    Переведи:

    { $translation }

review-answer = 🔄 Повторение ({ $position }/{ $total })

    🔊 { $word }{ $phonetic }{ $example }

    Как хорошо вспомнил?

review-complete = ✅ Повторение завершено!

    📊 Результаты:
    • Повторено: { $count } слов
    • Средняя оценка: { $avg_rating }
    • Время: { $time } мин

review-session-ended = Сессия завершена!

# Review buttons
btn-begin-review = ▶️ Начать повторение
btn-show-answer = 👀 Показать ответ
btn-review-again = 🔄 Ещё раз

# Voice/Pronunciation
btn-pronunciation = 🎤 Произношение

voice-no-words = 🎤 В твоём словаре пока нет выученных слов для практики произношения.
    Сначала выучи несколько слов!

voice-prompt = 🎤 Произношение ({ $position }/{ $total })

    Произнеси:
    🔊 { $word }{ $phonetic }

    💡 Отправь голосовое сообщение

voice-processing = ⏳ Обрабатываю...

voice-result = 🎤 Результат

    Ты сказал: "{ $transcribed }"
    Правильно: { $expected }

    { $rating } { $rating_num }/5

    💡 { $feedback }

voice-complete = ✅ Практика завершена!

    📊 Результаты:
    • Слов: { $count }
    • Средняя оценка: { $avg_rating }
    • Время: { $time } мин

voice-error = ❌ Не удалось обработать голосовое сообщение. Попробуй ещё раз.

voice-session-ended = Практика завершена!

# Voice buttons
btn-voice-retry = 🔄 Ещё раз
btn-voice-next = ➡️ Далее
btn-voice-again = 🎤 Снова

# Teaching - Role Selection
btn-teaching = 👨‍🏫 Учитель/Ученик
teaching-role-title = 👤 Выбери роль
teaching-role-desc = Ты можешь быть учителем или учеником (или обоими!)

# Teaching - Buttons
btn-become-teacher = 👨‍🏫 Стать учителем
btn-dashboard = 👨‍🏫 Панель учителя
btn-my-teacher = 👨‍🎓 Мой учитель
btn-join-teacher = 👨‍🎓 Присоединиться к учителю
btn-students = 👥 Ученики
btn-assignments = 📝 Задания
btn-invite = ➕ Пригласить
btn-remove-student = ❌ Удалить ученика
btn-regenerate = 🔄 Новый код
btn-leave-teacher = 🚪 Отключиться
btn-my-assignments = 📝 Мои задания
btn-new-assignment = ➕ Новое задание
btn-confirm = ✅ Да
btn-cancel = ❌ Отмена

# Teaching - Invite
teaching-invite-title = 📨 Пригласи ученика
teaching-invite-code = Код приглашения:
    <code>{ $code }</code>
teaching-invite-link = Или ссылка:
    { $link }
teaching-regenerated = ✅ Код обновлён!

# Teaching - Dashboard
teaching-dashboard-title = 👨‍🏫 Панель учителя
teaching-dashboard-stats = 👥 Учеников: { $students }
    📝 Активных заданий: { $assignments }

# Teaching - Students
teaching-students-title = 👥 Мои ученики
teaching-student-item = 👤 { $name }
    📊 { $words } слов • 🔥 { $streak } дней
teaching-no-students = У тебя пока нет учеников.
    Пригласи первого!
teaching-remove-confirm = ⚠️ Удалить этого ученика?
teaching-removed = ✅ Ученик удалён.

# Teaching - Student Panel
teaching-panel-title = 👨‍🎓 Мой учитель
teaching-panel-teacher = 👨‍🏫 { $name }
teaching-no-teacher = У тебя пока нет учителя.
    Введи код приглашения, чтобы присоединиться.
teaching-leave-confirm = ⚠️ Отключиться от учителя?
teaching-left = ✅ Ты отключился от учителя.

# Teaching - Join
teaching-join-prompt = 📝 Введи код приглашения:
teaching-join-success = ✅ Ты присоединился к учителю { $name }!
teaching-join-invalid = ❌ Неверный код приглашения.
teaching-join-self = ❌ Нельзя присоединиться к себе.
teaching-join-already = ❌ У тебя уже есть этот учитель.

# Assignments
assign-list-title = 📝 Задания
assign-no-assignments = 📝 У тебя пока нет заданий.
assign-pending-title = 📝 Мои задания
assign-no-pending = ✅ У тебя нет активных заданий.
assign-select-type = Выбери тип задания:
assign-select-method = Как создать задание?
assign-select-difficulty = Выбери сложность:
assign-enter-topic = 📝 Введи тему для задания:
assign-generating = ⏳ Генерирую задание...
assign-created = ✅ Задание "{ $title }" создано!
assign-view-title = 📝 { $title }
assign-type = Тип
assign-status = Статус
assign-pronounce = 🎤 Произнеси слова:
assign-answer = 📝 Ответь на вопросы (каждый ответ с новой строки):
assign-score = 📊 Оценка
assign-submitted = ✅ Ответ отправлен!
assign-submission-title = 📝 Ответ ученика
assign-ai-feedback = 🤖 AI:
assign-ai-score = Оценка AI
assign-grade = Оценка учителя
assign-select-grade = Выбери оценку:
assign-graded = ✅ Оценка { $grade }/5 выставлена!
assign-result-title = 📊 Результат задания

# Assignment types
type-text = Текст
type-multiple_choice = Тест
type-voice = Голос

# Assignment statuses
status-published = Ожидает
status-submitted = На проверке
status-graded = Проверено

# Assignment buttons
btn-type-text = 📝 Текстовый ответ
btn-type-mc = ❓ Тест с вариантами
btn-type-voice = 🎤 Голосовой ответ
btn-method-ai = 🤖 Сгенерировать AI
btn-method-manual = ✏️ Создать вручную
btn-easy = Легко
btn-medium = Средне
btn-hard = Сложно
btn-view-submission = 👀 Смотреть ответ
btn-start-assignment = ▶️ Начать
btn-view-result = 📊 Результат
btn-grade = 📝 Оценить

# Errors
error-invalid-data = ❌ Неверные данные
error-not-found = ❌ Не найдено
error-empty-topic = ❌ Тема не может быть пустой
error-empty-answer = ❌ Ответ не может быть пустым
error-generation-failed = ❌ Не удалось сгенерировать задание
error-no-questions = ❌ В задании нет вопросов
error-not-your-assignment = ❌ Это не твоё задание
error-no-submission = ❌ Ответ не найден
success = ✅ Успешно!
unknown-user = Пользователь
