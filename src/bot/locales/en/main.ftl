# Welcome messages
welcome = 👋 Welcome to Lingooru!
welcome-choose-lang = Choose your interface language:
welcome-choose-pair = Which language are you learning?

# Language names
lang-ru = 🇷🇺 Русский
lang-en = 🇬🇧 English
lang-ko = 🇰🇷 한국어

# Language pairs
pair-en-ru = 🇬🇧 English → 🇷🇺 Russian
pair-ko-ru = 🇰🇷 Korean → 🇷🇺 Russian

# Main menu
menu-title = 🎓 Lingooru
menu-subtitle = Your language learning assistant
menu-stats = 📊 Learned: { $learned } of { $total } words
menu-stats-by-lang = { $flag }: { $learned }/{ $total }
menu-streak = 🔥 Streak: { $days } days

# Buttons
btn-learn = 📚 Learn
btn-review = 🔄 Review
btn-stats = 📊 Statistics
btn-settings = ⚙️ Settings
btn-menu = 📋 Menu
btn-lang = 🌐 Language
btn-pair = 📖 Pair
btn-back = ⬅️ Back
btn-add-words-menu = ➕ Add Words

# Settings
settings-title = ⚙️ Settings
settings-lang = 🌐 Interface language: { $lang }
settings-pair = 📖 Learning: { $pair }
settings-saved = ✅ Settings saved!

# Learning
learn-no-words = 📚 Your vocabulary is empty.
    Add words by sending them as text, or choose from ready-made lists!

learn-no-words-for-pair = 📚 You don't have any words to learn for your current language pair.
    Add words by sending them as text, or choose from ready-made lists!

learn-choose-lang = 📚 Choose a language to learn:

learn-card = 📚 Learning ({ $position }/{ $total })

    🔊 { $word }{ $phonetic }

    <tg-spoiler>{ $translation }</tg-spoiler>{ $example }

learn-session-complete = ✅ Session complete!
    You learned { $count } words.

learn-session-ended = Session ended!

# Words
word-added = ✅ Word added!

    🔊 { $word }{ $phonetic }

    { $translation }

word-already-exists = ⚠️ This word is already in your vocabulary.

word-not-found-enter-translation = 📝 Word "{ $word }" not found in dictionary.
    Enter the translation manually:

word-add-prompt = 📝 Send a word you want to add:

word-add-error = ❌ Failed to add word. Please try again.

word-removed = ✅ Word removed from vocabulary.

# Vocabulary
vocab-title = 📖 My Vocabulary ({ $total } words)

vocab-empty = 📖 Your vocabulary is empty.
    Add your first word by sending it as text!

# Word lists
lists-title = 📋 Choose a thematic list:

lists-empty = 📋 No word lists available for this language yet.

list-preview-words = Words in list: { $count }

list-and-more = and { $count } more...

list-not-found = List not found.

list-added = ✅ List "{ $list_name }" added!

    Words added: { $added }
    Skipped (already exists): { $skipped }

# Additional buttons
btn-know = ✅ Know
btn-hard = 🤔 Hard
btn-forgot = ❌ Forgot
btn-skip = ⏭️ Skip
btn-add-more = ➕ More
btn-add-words = ➕ Add
btn-word-lists = 📋 Lists
btn-my-vocab = 📖 Vocab
btn-learn-again = 🔄 Again
btn-add-list = ➕ Add list
btn-more-lists = 📋 Other lists
btn-list-added = ✅ Added

list-already-added = This list has already been added.

# Language selection
btn-mix = Mix

# Audio
btn-play-audio = 🔊 Listen
audio-loading = ⏳ Loading audio...
audio-not-available = ❌ Audio not available for this word
audio-error = ❌ Playback error

# Misc
coming-soon = 🚧 Coming soon!

# Review (SM-2)
review-start = 🔄 Review

    📊 Words due today: { $count }

review-no-words-due = ✅ Great! No reviews due today.
    Come back later or learn new words!

review-question = 🔄 Review ({ $position }/{ $total })

    Translate:

    { $translation }

review-answer = 🔄 Review ({ $position }/{ $total })

    🔊 { $word }{ $phonetic }{ $example }

    How well did you remember?

review-complete = ✅ Review complete!

    📊 Results:
    • Reviewed: { $count } words
    • Average rating: { $avg_rating }
    • Time: { $time } min

review-session-ended = Session ended!

# Review buttons
btn-begin-review = ▶️ Begin Review
btn-show-answer = 👀 Show Answer
btn-review-again = 🔄 Again

# Voice/Pronunciation
btn-pronunciation = 🎤 Pronunciation

voice-no-words = 🎤 You don't have any learned words for pronunciation practice yet.
    Learn some words first!

voice-prompt = 🎤 Pronunciation ({ $position }/{ $total })

    Pronounce:
    🔊 { $word }{ $phonetic }

    💡 Send a voice message

voice-processing = ⏳ Processing...

voice-result = 🎤 Result

    You said: "{ $transcribed }"
    Expected: { $expected }

    { $rating } { $rating_num }/5

    💡 { $feedback }

voice-complete = ✅ Practice complete!

    📊 Results:
    • Words: { $count }
    • Average rating: { $avg_rating }
    • Time: { $time } min

voice-error = ❌ Failed to process voice message. Please try again.

voice-session-ended = Practice ended!

# Voice buttons
btn-voice-retry = 🔄 Retry
btn-voice-next = ➡️ Next
btn-voice-again = 🎤 Again
