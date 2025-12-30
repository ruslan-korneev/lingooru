# Welcome messages
welcome = 👋 Lingooru에 오신 것을 환영합니다!
welcome-choose-lang = 인터페이스 언어를 선택하세요:
welcome-choose-pair = 어떤 언어를 공부하고 계세요?

# Language names
lang-ru = 🇷🇺 Русский
lang-en = 🇬🇧 English
lang-ko = 🇰🇷 한국어

# Language pairs
pair-en-ru = 🇬🇧 영어 → 🇷🇺 러시아어
pair-ko-ru = 🇰🇷 한국어 → 🇷🇺 러시아어

# Main menu
menu-title = 🎓 Lingooru
menu-subtitle = 언어 학습 도우미
menu-stats = 📊 학습 완료: { $total }개 중 { $learned }개
menu-stats-by-lang = { $flag }: { $learned }/{ $total }
menu-streak = 🔥 연속: { $days }일

# Buttons
btn-learn = 📚 학습
btn-review = 🔄 복습
btn-stats = 📊 통계
btn-settings = ⚙️ 설정
btn-menu = 📋 메뉴
btn-lang = 🌐 언어
btn-pair = 📖 페어
btn-back = ⬅️ 뒤로
btn-add-words-menu = ➕ 단어 추가

# Settings
settings-title = ⚙️ 설정
settings-lang = 🌐 인터페이스 언어: { $lang }
settings-pair = 📖 학습 중: { $pair }
settings-saved = ✅ 설정이 저장되었습니다!

# Learning
learn-no-words = 📚 단어장이 비어 있습니다.
    텍스트로 단어를 보내거나 준비된 목록에서 선택하세요!

learn-no-words-for-pair = 📚 현재 언어 페어에 학습할 단어가 없습니다.
    텍스트로 단어를 보내거나 준비된 목록에서 선택하세요!

learn-choose-lang = 📚 학습할 언어를 선택하세요:

learn-card = 📚 학습 ({ $position }/{ $total })

    🔊 { $word }{ $phonetic }

    <tg-spoiler>{ $translation }</tg-spoiler>{ $example }

learn-session-complete = ✅ 세션 완료!
    { $count }개의 단어를 학습했습니다.

learn-session-ended = 세션 종료!

# Words
word-added = ✅ 단어가 추가되었습니다!

    🔊 { $word }{ $phonetic }

    { $translation }

word-already-exists = ⚠️ 이 단어는 이미 단어장에 있습니다.

word-not-found-enter-translation = 📝 "{ $word }" 단어를 사전에서 찾을 수 없습니다.
    번역을 직접 입력하세요:

word-add-prompt = 📝 추가할 단어를 보내세요:

word-add-error = ❌ 단어 추가 실패. 다시 시도해 주세요.

word-removed = ✅ 단어가 단어장에서 삭제되었습니다.

# Vocabulary
vocab-title = 📖 내 단어장 ({ $total }개 단어)

vocab-empty = 📖 단어장이 비어 있습니다.
    텍스트로 첫 번째 단어를 추가하세요!

# Word lists
lists-title = 📋 주제별 목록을 선택하세요:

lists-empty = 📋 이 언어에 대한 단어 목록이 아직 없습니다.

list-preview-words = 목록의 단어 수: { $count }

list-and-more = 그리고 { $count }개 더...

list-not-found = 목록을 찾을 수 없습니다.

list-added = ✅ "{ $list_name }" 목록이 추가되었습니다!

    추가된 단어: { $added }
    건너뛴 (이미 존재): { $skipped }

# Additional buttons
btn-know = ✅ 알아요
btn-hard = 🤔 어려워요
btn-forgot = ❌ 모르겠어요
btn-skip = ⏭️ 건너뛰기
btn-add-more = ➕ 더
btn-add-words = ➕ 추가
btn-word-lists = 📋 목록
btn-my-vocab = 📖 단어장
btn-learn-again = 🔄 다시
btn-add-list = ➕ 목록 추가
btn-more-lists = 📋 다른 목록
btn-list-added = ✅ 추가됨

list-already-added = 이 목록은 이미 추가되었습니다.

# Language selection
btn-mix = 혼합

# Audio
btn-play-audio = 🔊 듣기
audio-loading = ⏳ 오디오 로딩 중...
audio-not-available = ❌ 이 단어의 오디오를 사용할 수 없습니다
audio-error = ❌ 재생 오류

# Misc
coming-soon = 🚧 곧 출시 예정!

# Review (SM-2)
review-start = 🔄 복습

    📊 오늘 복습할 단어: { $count }개

review-no-words-due = ✅ 훌륭해요! 오늘 복습할 단어가 없습니다.
    나중에 다시 오거나 새 단어를 학습하세요!

review-question = 🔄 복습 ({ $position }/{ $total })

    번역하세요:

    { $translation }

review-answer = 🔄 복습 ({ $position }/{ $total })

    🔊 { $word }{ $phonetic }{ $example }

    얼마나 잘 기억하셨나요?

review-complete = ✅ 복습 완료!

    📊 결과:
    • 복습한 단어: { $count }개
    • 평균 평점: { $avg_rating }
    • 시간: { $time }분

review-session-ended = 세션 종료!

# Review buttons
btn-begin-review = ▶️ 복습 시작
btn-show-answer = 👀 정답 보기
btn-review-again = 🔄 다시

# Voice/Pronunciation
btn-pronunciation = 🎤 발음

voice-no-words = 🎤 발음 연습을 위한 학습 완료된 단어가 없습니다.
    먼저 단어를 학습하세요!

voice-prompt = 🎤 발음 ({ $position }/{ $total })

    발음하세요:
    🔊 { $word }{ $phonetic }

    💡 음성 메시지를 보내세요

voice-processing = ⏳ 처리 중...

voice-result = 🎤 결과

    당신이 말한 것: "{ $transcribed }"
    올바른 발음: { $expected }

    { $rating } { $rating_num }/5

    💡 { $feedback }

voice-complete = ✅ 연습 완료!

    📊 결과:
    • 단어: { $count }개
    • 평균 평점: { $avg_rating }
    • 시간: { $time }분

voice-error = ❌ 음성 메시지 처리 실패. 다시 시도해 주세요.

voice-session-ended = 연습 종료!

# Voice buttons
btn-voice-retry = 🔄 다시
btn-voice-next = ➡️ 다음
btn-voice-again = 🎤 다시

# Teaching - Role Selection
btn-teaching = 👨‍🏫 선생님/학생
teaching-role-title = 👤 역할을 선택하세요
teaching-role-desc = 선생님이나 학생이 될 수 있습니다 (둘 다도 가능!)

# Teaching - Buttons
btn-become-teacher = 👨‍🏫 선생님 되기
btn-dashboard = 👨‍🏫 선생님 대시보드
btn-my-teacher = 👨‍🎓 내 선생님
btn-join-teacher = 👨‍🎓 선생님 참여
btn-students = 👥 학생들
btn-assignments = 📝 과제
btn-invite = ➕ 초대
btn-remove-student = ❌ 학생 제거
btn-regenerate = 🔄 새 코드
btn-leave-teacher = 🚪 나가기
btn-my-assignments = 📝 내 과제
btn-new-assignment = ➕ 새 과제
btn-confirm = ✅ 예
btn-cancel = ❌ 취소

# Teaching - Invite
teaching-invite-title = 📨 학생 초대
teaching-invite-code = 초대 코드:
    <code>{ $code }</code>
teaching-invite-link = 또는 링크:
    { $link }
teaching-regenerated = ✅ 코드가 재생성되었습니다!

# Teaching - Dashboard
teaching-dashboard-title = 👨‍🏫 선생님 대시보드
teaching-dashboard-stats = 👥 학생: { $students }명
    📝 활성 과제: { $assignments }개

# Teaching - Students
teaching-students-title = 👥 내 학생들
teaching-student-item = 👤 { $name }
    📊 { $words }개 단어 • 🔥 { $streak }일
teaching-no-students = 아직 학생이 없습니다.
    첫 번째 학생을 초대하세요!
teaching-remove-confirm = ⚠️ 이 학생을 제거하시겠습니까?
teaching-removed = ✅ 학생이 제거되었습니다.

# Teaching - Student Panel
teaching-panel-title = 👨‍🎓 내 선생님
teaching-panel-teacher = 👨‍🏫 { $name }
teaching-no-teacher = 아직 선생님이 없습니다.
    초대 코드를 입력하여 참여하세요.
teaching-leave-confirm = ⚠️ 이 선생님을 나가시겠습니까?
teaching-left = ✅ 선생님을 나갔습니다.

# Teaching - Join
teaching-join-prompt = 📝 초대 코드를 입력하세요:
teaching-join-success = ✅ { $name } 선생님에게 참여했습니다!
teaching-join-invalid = ❌ 잘못된 초대 코드입니다.
teaching-join-self = ❌ 자신에게 참여할 수 없습니다.
teaching-join-already = ❌ 이미 이 선생님에게 연결되어 있습니다.

# Errors
error-invalid-data = ❌ 잘못된 데이터
error-not-found = ❌ 찾을 수 없음
unknown-user = 사용자
