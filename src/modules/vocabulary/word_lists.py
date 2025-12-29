from dataclasses import dataclass

from src.modules.vocabulary.models import Language


@dataclass
class WordListItem:
    """A word with its translation and optional example."""

    text: str
    translation: str
    example: str | None = None


@dataclass
class ThematicWordList:
    """A thematic word list with localized names."""

    id: str
    name_ru: str
    name_en: str
    name_ko: str
    source_language: Language
    words: list[WordListItem]

    def get_name(self, lang: str) -> str:
        """Get localized name."""
        names = {
            "ru": self.name_ru,
            "en": self.name_en,
            "ko": self.name_ko,
        }
        return names.get(lang, self.name_en)


# Predefined word lists
WORD_LISTS: list[ThematicWordList] = [
    # English -> Russian lists
    ThematicWordList(
        id="food",
        name_ru="🍎 Еда и напитки",
        name_en="🍎 Food and Drinks",
        name_ko="🍎 음식과 음료",
        source_language=Language.EN,
        words=[
            WordListItem("apple", "яблоко", "An apple a day keeps the doctor away."),
            WordListItem("bread", "хлеб", "I need to buy some bread."),
            WordListItem("water", "вода", "Drink more water every day."),
            WordListItem("milk", "молоко", "The milk is fresh."),
            WordListItem("coffee", "кофе", "I love morning coffee."),
            WordListItem("tea", "чай", "Would you like some tea?"),
            WordListItem("cheese", "сыр", "This cheese is delicious."),
            WordListItem("egg", "яйцо", "I had eggs for breakfast."),
            WordListItem("meat", "мясо", "The meat is well cooked."),
            WordListItem("fish", "рыба", "Fresh fish from the market."),
        ],
    ),
    ThematicWordList(
        id="family",
        name_ru="👨‍👩‍👧 Семья",
        name_en="👨‍👩‍👧 Family",
        name_ko="👨‍👩‍👧 가족",
        source_language=Language.EN,
        words=[
            WordListItem("mother", "мама", "My mother is a teacher."),
            WordListItem("father", "папа", "My father works hard."),
            WordListItem("sister", "сестра", "I have one sister."),
            WordListItem("brother", "брат", "My brother is older than me."),
            WordListItem("grandmother", "бабушка", "My grandmother makes the best cookies."),
            WordListItem("grandfather", "дедушка", "My grandfather tells great stories."),
            WordListItem("son", "сын", "He is their only son."),
            WordListItem("daughter", "дочь", "She is a wonderful daughter."),
            WordListItem("husband", "муж", "Her husband is a doctor."),
            WordListItem("wife", "жена", "His wife works in IT."),
        ],
    ),
    ThematicWordList(
        id="colors",
        name_ru="🎨 Цвета",
        name_en="🎨 Colors",
        name_ko="🎨 색깔",
        source_language=Language.EN,
        words=[
            WordListItem("red", "красный", "The apple is red."),
            WordListItem("blue", "синий", "The sky is blue."),
            WordListItem("green", "зелёный", "The grass is green."),
            WordListItem("yellow", "жёлтый", "The sun is yellow."),
            WordListItem("white", "белый", "Snow is white."),
            WordListItem("black", "чёрный", "My cat is black."),
            WordListItem("orange", "оранжевый", "Oranges are orange."),
            WordListItem("pink", "розовый", "She likes pink flowers."),
            WordListItem("purple", "фиолетовый", "Grapes can be purple."),
            WordListItem("brown", "коричневый", "The tree trunk is brown."),
        ],
    ),
    ThematicWordList(
        id="animals",
        name_ru="🐾 Животные",
        name_en="🐾 Animals",
        name_ko="🐾 동물",
        source_language=Language.EN,
        words=[
            WordListItem("dog", "собака", "The dog is running."),
            WordListItem("cat", "кошка", "The cat is sleeping."),
            WordListItem("bird", "птица", "A bird is singing."),
            WordListItem("horse", "лошадь", "The horse is fast."),
            WordListItem("cow", "корова", "The cow gives milk."),
            WordListItem("sheep", "овца", "Sheep are on the field."),
            WordListItem("pig", "свинья", "The pig is pink."),
            WordListItem("rabbit", "кролик", "The rabbit eats carrots."),
            WordListItem("bear", "медведь", "Bears live in the forest."),
            WordListItem("lion", "лев", "The lion is the king of animals."),
        ],
    ),
    ThematicWordList(
        id="numbers",
        name_ru="🔢 Числа",
        name_en="🔢 Numbers",
        name_ko="🔢 숫자",
        source_language=Language.EN,
        words=[
            WordListItem("one", "один", "I have one apple."),
            WordListItem("two", "два", "There are two books."),
            WordListItem("three", "три", "Three birds are flying."),
            WordListItem("four", "четыре", "The table has four legs."),
            WordListItem("five", "пять", "I have five fingers."),
            WordListItem("ten", "десять", "Count to ten."),
            WordListItem("hundred", "сто", "A hundred people came."),
            WordListItem("thousand", "тысяча", "A thousand stars in the sky."),
            WordListItem("first", "первый", "I was first in line."),
            WordListItem("second", "второй", "She finished second."),
        ],
    ),
    ThematicWordList(
        id="body",
        name_ru="🫀 Части тела",
        name_en="🫀 Body Parts",
        name_ko="🫀 신체 부위",
        source_language=Language.EN,
        words=[
            WordListItem("head", "голова", "My head hurts."),
            WordListItem("hand", "рука", "Wash your hands."),
            WordListItem("leg", "нога", "I hurt my leg."),
            WordListItem("eye", "глаз", "She has blue eyes."),
            WordListItem("ear", "ухо", "I can hear with my ears."),  # noqa: RUF001
            WordListItem("nose", "нос", "My nose is cold."),
            WordListItem("mouth", "рот", "Open your mouth."),
            WordListItem("heart", "сердце", "The heart pumps blood."),
            WordListItem("finger", "палец", "I cut my finger."),
            WordListItem("foot", "стопа", "My foot is tired."),
        ],
    ),
    # Korean -> Russian lists
    ThematicWordList(
        id="food_ko",
        name_ru="🍎 Еда и напитки",
        name_en="🍎 Food and Drinks",
        name_ko="🍎 음식과 음료",
        source_language=Language.KO,
        words=[
            WordListItem("사과", "яблоко", "사과를 먹고 싶어요."),
            WordListItem("빵", "хлеб", "빵을 좀 사야 해요."),
            WordListItem("물", "вода", "물을 많이 마셔요."),
            WordListItem("우유", "молоко", "우유가 신선해요."),
            WordListItem("커피", "кофе", "아침 커피를 좋아해요."),
            WordListItem("차", "чай", "차 한 잔 드실래요?"),
            WordListItem("치즈", "сыр", "이 치즈 맛있어요."),
            WordListItem("계란", "яйцо", "아침에 계란을 먹었어요."),
            WordListItem("고기", "мясо", "고기가 잘 익었어요."),
            WordListItem("생선", "рыба", "시장에서 신선한 생선이에요."),
        ],
    ),
    ThematicWordList(
        id="family_ko",
        name_ru="👨‍👩‍👧 Семья",
        name_en="👨‍👩‍👧 Family",
        name_ko="👨‍👩‍👧 가족",
        source_language=Language.KO,
        words=[
            WordListItem("어머니", "мама", "어머니는 선생님이에요."),
            WordListItem("아버지", "папа", "아버지는 열심히 일해요."),
            WordListItem("언니", "старшая сестра", "저는 언니가 한 명 있어요."),
            WordListItem("오빠", "старший брат", "오빠는 저보다 나이가 많아요."),
            WordListItem("할머니", "бабушка", "할머니가 제일 맛있는 과자를 만들어요."),
            WordListItem("할아버지", "дедушка", "할아버지는 재미있는 이야기를 해요."),
            WordListItem("아들", "сын", "그는 외아들이에요."),
            WordListItem("딸", "дочь", "그녀는 훌륭한 딸이에요."),
            WordListItem("남편", "муж", "그녀의 남편은 의사예요."),
            WordListItem("아내", "жена", "그의 아내는 IT에서 일해요."),
        ],
    ),
    ThematicWordList(
        id="colors_ko",
        name_ru="🎨 Цвета",
        name_en="🎨 Colors",
        name_ko="🎨 색깔",
        source_language=Language.KO,
        words=[
            WordListItem("빨간색", "красный", "사과가 빨간색이에요."),
            WordListItem("파란색", "синий", "하늘이 파란색이에요."),
            WordListItem("초록색", "зелёный", "잔디가 초록색이에요."),
            WordListItem("노란색", "жёлтый", "해가 노란색이에요."),
            WordListItem("하얀색", "белый", "눈이 하얀색이에요."),
            WordListItem("검은색", "чёрный", "제 고양이는 검은색이에요."),
            WordListItem("주황색", "оранжевый", "오렌지는 주황색이에요."),
            WordListItem("분홍색", "розовый", "그녀는 분홍색 꽃을 좋아해요."),
            WordListItem("보라색", "фиолетовый", "포도가 보라색일 수 있어요."),
            WordListItem("갈색", "коричневый", "나무 줄기가 갈색이에요."),
        ],
    ),
    ThematicWordList(
        id="animals_ko",
        name_ru="🐾 Животные",
        name_en="🐾 Animals",
        name_ko="🐾 동물",
        source_language=Language.KO,
        words=[
            WordListItem("개", "собака", "개가 달리고 있어요."),
            WordListItem("고양이", "кошка", "고양이가 자고 있어요."),
            WordListItem("새", "птица", "새가 노래하고 있어요."),
            WordListItem("말", "лошадь", "말이 빨라요."),
            WordListItem("소", "корова", "소가 우유를 줘요."),
            WordListItem("양", "овца", "양이 들판에 있어요."),
            WordListItem("돼지", "свинья", "돼지가 분홍색이에요."),
            WordListItem("토끼", "кролик", "토끼가 당근을 먹어요."),
            WordListItem("곰", "медведь", "곰이 숲에 살아요."),
            WordListItem("사자", "лев", "사자는 동물의 왕이에요."),
        ],
    ),
    ThematicWordList(
        id="numbers_ko",
        name_ru="🔢 Числа",
        name_en="🔢 Numbers",
        name_ko="🔢 숫자",
        source_language=Language.KO,
        words=[
            WordListItem("하나", "один", "사과가 하나 있어요."),
            WordListItem("둘", "два", "책이 두 권 있어요."),
            WordListItem("셋", "три", "새 세 마리가 날고 있어요."),
            WordListItem("넷", "четыре", "테이블에 다리가 네 개 있어요."),
            WordListItem("다섯", "пять", "손가락이 다섯 개 있어요."),
            WordListItem("열", "десять", "열까지 세어보세요."),
            WordListItem("백", "сто", "백 명이 왔어요."),
            WordListItem("천", "тысяча", "하늘에 별이 천 개 있어요."),
            WordListItem("첫 번째", "первый", "저는 줄에서 첫 번째였어요."),
            WordListItem("두 번째", "второй", "그녀는 두 번째로 끝냈어요."),
        ],
    ),
    ThematicWordList(
        id="body_ko",
        name_ru="🫀 Части тела",
        name_en="🫀 Body Parts",
        name_ko="🫀 신체 부위",
        source_language=Language.KO,
        words=[
            WordListItem("머리", "голова", "머리가 아파요."),
            WordListItem("손", "рука", "손을 씻으세요."),
            WordListItem("다리", "нога", "다리를 다쳤어요."),
            WordListItem("눈", "глаз", "그녀는 파란 눈을 가지고 있어요."),
            WordListItem("귀", "ухо", "귀로 들을 수 있어요."),  # noqa: RUF001
            WordListItem("코", "нос", "코가 차가워요."),
            WordListItem("입", "рот", "입을 벌리세요."),
            WordListItem("심장", "сердце", "심장이 피를 펌프해요."),
            WordListItem("손가락", "палец", "손가락을 베었어요."),
            WordListItem("발", "стопа", "발이 피곤해요."),
        ],
    ),
]


def get_word_list_by_id(list_id: str) -> ThematicWordList | None:
    """Get a word list by its ID."""
    return next((wl for wl in WORD_LISTS if wl.id == list_id), None)


def get_all_word_lists() -> list[ThematicWordList]:
    """Get all available word lists."""
    return WORD_LISTS


def get_word_lists_by_language(language: Language) -> list[ThematicWordList]:
    """Get word lists filtered by source language."""
    return [wl for wl in WORD_LISTS if wl.source_language == language]
