# UTextEditor

## 1. Призначення

**UTextEditor** — це локальний графічний текстовий редактор для desktop, візуально та функціонально схожий на **GEdit**, але з інтегрованим локальним AI-помічником на базі **Ollama + Gemma 4 12B**.

Основні можливості AI:

1. перевірка правопису та базових граматичних помилок;
2. виправлення помилок за запитом;
3. передбачення продовження тексту;
4. відображення передбаченого тексту **inline ("ghost text")**;
5. застосування передбачення клавішею **Tab**;
6. повністю локальна обробка тексту через Ollama без передачі тексту до зовнішніх сервісів.

---

# 2. Цілі MVP

MVP повинен забезпечувати:

* створення нового документа;
* відкриття текстового файлу;
* редагування тексту;
* збереження файлу;
* роботу з кількома відкритими файлами через вкладки;
* undo/redo;
* copy/paste/cut;
* пошук та заміну;
* інтеграцію з локальним Ollama;
* перевірку правопису;
* inline-підказки наступного тексту;
* застосування підказки клавішею `Tab`;
* роботу UI без зависання під час звернення до AI.

---

# 3. Платформа

Цільова платформа MVP:

* Linux
* macOS

Windows бажано підтримати архітектурно, але вона не є обов'язковою для першого релізу.

Редактор має бути **нативним desktop application**, а не web application.

---

# 4. Рекомендований технологічний стек

Рекомендований стек:

* **Python 3.12+**
* **PySide6 / Qt 6** — GUI
* **Ollama** — локальний AI runtime
* HTTP API Ollama — взаємодія з моделлю
* `QThread`, `QThreadPool` або `QtConcurrent` — асинхронна AI-обробка
* Git — version control
* pytest — unit tests

Для текстового редактора бажано використовувати Qt text editing component, наприклад `QPlainTextEdit` або `QTextEdit`.

Для MVP перевага надається `QPlainTextEdit`, оскільки редактор орієнтований насамперед на plain text.

---

# 5. Загальна архітектура

```text
┌───────────────────────────────┐
│           UTextEditor         │
│                               │
│  ┌─────────┐  ┌─────────────┐ │
│  │   Menu  │  │  Toolbar    │ │
│  └─────────┘  └─────────────┘ │
│                               │
│  ┌───────────────────────────┐│
│  │        Tab Manager        ││
│  │                           ││
│  │ ┌─────────────┐           ││
│  │ │ Text Editor │           ││
│  │ │             │           ││
│  │ │ text text...│           ││
│  │ │             │           ││
│  │ └─────────────┘           ││
│  └───────────────────────────┘│
│                               │
│  ┌───────────────────────────┐│
│  │ AI / status information   ││
│  └───────────────────────────┘│
└───────────────┬───────────────┘
                │
                │ HTTP
                ▼
       ┌───────────────────┐
       │      Ollama       │
       │ localhost:11434   │
       │                   │
       │  gemma4:12b       │
       └───────────────────┘
```

AI integration повинна бути винесена в окремий сервісний шар, щоб GUI не залежав безпосередньо від Ollama API.

Рекомендована структура:

```text
UTextEditor/
├── app/
│   ├── main.py
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── editor_widget.py
│   │   ├── tab_widget.py
│   │   └── ...
│   │
│   ├── ai/
│   │   ├── ollama_client.py
│   │   ├── completion_service.py
│   │   ├── spellcheck_service.py
│   │   └── prompts.py
│   │
│   ├── document/
│   │   ├── document.py
│   │   ├── file_manager.py
│   │   └── encoding.py
│   │
│   └── settings/
│       └── settings.py
│
├── tests/
├── requirements.txt
├── README.md
└── pyproject.toml
```

---

# 6. Основне вікно

Інтерфейс має нагадувати GEdit:

```text
┌───────────────────────────────────────────────────────┐
│ File  Edit  Search  View  AI  Help                    │
├───────────────────────────────────────────────────────┤
│ New Open Save | Undo Redo | Find Replace               │
├───────────────────────────────────────────────────────┤
│ file1.txt   │ file2.txt   │ +                          │
├───────────────────────────────────────────────────────┤
│                                                       │
│ Hello world.                                          │
│ This is my text...                                    │
│                                                       │
│ The predicted text is shown here...                  │
│                                                       │
│                                                       │
├───────────────────────────────────────────────────────┤
│ UTF-8     LF     Ln 12, Col 8       AI: Connected     │
└───────────────────────────────────────────────────────┘
```

---

# 7. Робота з файлами

Редактор повинен підтримувати:

### New

Створення нового документа.

### Open

Відкриття текстового файлу.

### Save

Збереження поточного документа.

### Save As

Збереження документа під новим ім'ям.

### Close

Закриття поточного документа.

### Multiple tabs

Кожен відкритий документ працює в окремій вкладці.

Назва вкладки повинна відображати:

```text
example.txt
```

Для незбережених змін:

```text
example.txt *
```

---

# 8. Робота з текстом

Потрібна стандартна функціональність:

* введення тексту;
* виділення;
* copy;
* cut;
* paste;
* undo;
* redo;
* select all;
* delete;
* navigation;
* keyboard shortcuts.

Стандартні комбінації:

```text
Ctrl/Cmd + N
Ctrl/Cmd + O
Ctrl/Cmd + S
Ctrl/Cmd + Shift + S

Ctrl/Cmd + Z
Ctrl/Cmd + Shift + Z

Ctrl/Cmd + C
Ctrl/Cmd + X
Ctrl/Cmd + V
Ctrl/Cmd + A

Ctrl/Cmd + F
Ctrl/Cmd + H
```

---

# 9. AI інтеграція

## 9.1 Ollama

За замовчуванням редактор використовує:

```text
Provider: Ollama
Host: http://localhost:11434
Model: gemma4:12b
```

Модель повинна бути конфігурованою через Settings.

Наприклад:

```text
Ollama host:
http://localhost:11434

Model:
gemma4:12b
```

Перед початком роботи редактор повинен перевірити доступність Ollama.

Стани:

```text
AI: Connected
AI: Connecting...
AI: Offline
AI: Error
```

---

# 10. AI completion

AI completion — це основна AI-функція редактора.

Після введення тексту редактор через коротку затримку повинен запросити Ollama для прогнозування можливого продовження.

Наприклад, користувач пише:

```text
Today I want to
```

AI може запропонувати:

```text
write a short description of my project.
```

У редакторі це має виглядати як:

```text
Today I want to write a short description of my project.
            └──────────────────────────────────────────┘
                        ghost text
```

Ghost text не є частиною основного документа до моменту підтвердження.

---

# 11. Inline suggestion

AI-передбачення повинно:

* відображатися безпосередньо в позиції курсора;
* мати візуально відмінний стиль від основного тексту;
* не змінювати документ;
* автоматично зникати при зміні тексту;
* автоматично оновлюватися після нового введення.

Suggestion повинна бути прив'язана до конкретної позиції курсора.

---

# 12. Застосування suggestion

Основний спосіб підтвердження:

```text
Tab
```

Після натискання `Tab`:

```text
ghost text
     ↓
real text
```

Suggestion додається до документа, а курсор переміщується в кінець вставленого тексту.

---

# 13. Скасування suggestion

Suggestion повинна автоматично зникати при:

* натисканні будь-якої клавіші, яка змінює текст;
* переміщенні курсора;
* зміні виділення;
* переході на іншу вкладку;
* натисканні Escape.

`Esc` повинен явно означати:

```text
Cancel suggestion
```

---

# 14. Асинхронна генерація

AI-запити **ніколи не повинні блокувати GUI thread**.

Наприклад:

```text
User types
    ↓
300–800 ms debounce
    ↓
start AI request
    ↓
GUI remains responsive
    ↓
AI response
    ↓
validate response
    ↓
display suggestion
```

Якщо користувач продовжив друкувати до завершення AI-запиту, старий запит повинен бути скасований або його результат повинен бути проігнорований.

Кожен AI request повинен мати revision/version identifier документа.

Приклад:

```text
Document revision = 154

request revision = 154

document changes

Document revision = 155

response for revision 154 arrives
        ↓
discard response
```

Це запобігає появі застарілих підказок.

---

# 15. Контекст для completion

AI повинен отримувати достатньо контексту для коректного продовження.

Мінімально:

* текст навколо курсора;
* поточний абзац;
* кілька попередніх речень;
* бажано частину поточного документа.

Необхідно уникати надсилання всього документа при кожному натисканні клавіші, якщо це не потрібно.

Бажано використовувати контекстне вікно:

```text
previous context
+
current paragraph
+
text before cursor
+
cursor
+
optional text after cursor
```

---

# 16. Prompt для completion

Промпт повинен змушувати модель генерувати **тільки продовження тексту**, без пояснень.

Приклад логіки:

```text
You are an inline text completion engine.

Continue the user's text naturally.

Rules:
- Generate only the continuation.
- Do not repeat existing text.
- Do not add explanations.
- Do not use markdown unless the user is writing markdown.
- Preserve the language of the document.
- Keep the continuation concise.
- Prefer 1-2 sentences.
```

Контекст документа передається окремо.

---

# 17. Кількість тексту в suggestion

Для MVP suggestion повинна бути короткою.

Рекомендований діапазон:

```text
5–100 tokens
```

Оптимально починати з невеликих пропозицій і не генерувати великі абзаци.

---

# 18. Spell checking

Редактор повинен автоматично перевіряти текст на орфографічні та базові граматичні помилки.

Помилки повинні бути візуально позначені.

Наприклад:

```text
This sentense contains a mistake.
     ~~~~~~~
```

Для помилки AI повинен повертати структуровану інформацію:

```json
{
  "start": 5,
  "end": 12,
  "replacement": "sentence",
  "type": "spelling",
  "explanation": "..."
}
```

GUI не повинен намагатися розбирати довільний текстовий response моделі.

AI повинен відповідати у визначеному JSON-форматі.

---

# 19. Виправлення помилки

Користувач повинен мати можливість:

* побачити помилку;
* побачити запропоноване виправлення;
* застосувати виправлення;
* проігнорувати його.

Мінімальна UX:

```text
right click
    ↓
Replace "sentense" with "sentence"
Ignore
```

---

# 20. Режими AI

В меню `AI`:

```text
AI
├── Enable AI
├── Check Spelling
├── Generate Completion
├── Accept Suggestion
├── Reject Suggestion
└── Settings
```

Також бажано мати кнопку:

```text
AI: ON
```

у status bar.

---

# 21. Мови

AI повинен працювати щонайменше з:

* English
* Ukrainian

Мова може визначатися автоматично.

Користувач також може вибрати мову вручну:

```text
Language:
Auto
English
Ukrainian
```

У майбутньому можна додати інші мови без зміни архітектури AI layer.

---

# 22. Налаштування

Settings повинні містити:

### AI

```text
Enable AI
Ollama host
Model
Completion enabled
Spell checking enabled
```

### Completion

```text
Debounce delay
Maximum suggestion length
Context size
Temperature
```

### Editor

```text
Font
Font size
Tab width
Show line numbers
Word wrap
Dark mode
```

---

# 23. Помилки AI

При недоступному Ollama редактор **не повинен падати**.

Наприклад:

```text
Ollama is not available.

AI features are disabled.
```

Редактор при цьому продовжує працювати як звичайний текстовий редактор.

Помилки повинні відображатися у status bar або notification area.

---

# 24. Продуктивність

Основні вимоги:

* GUI не блокується під час AI-запитів;
* введення тексту має залишатися плавним;
* completion не повинен запускатися на кожне натискання клавіші окремим запитом;
* AI-запити повинні використовувати debounce;
* застарілі AI responses повинні відкидатися;
* великі документи не повинні повністю передаватися моделі при кожній зміні.

---

# 25. AI Service interface

GUI не повинен напряму викликати Ollama.

Повинен існувати abstraction layer:

```python
class AIProvider(Protocol):

    async def complete(
        self,
        context: str,
        language: str,
    ) -> str:
        ...

    async def check_spelling(
        self,
        text: str,
        language: str,
    ) -> list[Suggestion]:
        ...
```

Реалізація:

```python
class OllamaProvider(AIProvider):
    ...
```

Це дозволить у майбутньому додати:

```text
OpenAIProvider
AnthropicProvider
LMStudioProvider
LocalModelProvider
```

без зміни GUI.

---

# 26. Completion Service

Completion service відповідає за:

1. отримання cursor position;
2. формування контексту;
3. debounce;
4. запуск AI request;
5. cancellation / invalidation;
6. перевірку response;
7. передачу suggestion UI.

Приблизний flow:

```text
Editor changed
      ↓
CompletionService
      ↓
Debounce
      ↓
Build Context
      ↓
OllamaProvider
      ↓
Gemma 4 12B
      ↓
Completion Result
      ↓
Validate
      ↓
Editor.showSuggestion()
```

---

# 27. Spellcheck Service

Окремий сервіс:

```text
Editor text
    ↓
SpellcheckService
    ↓
OllamaProvider
    ↓
Gemma 4 12B
    ↓
Structured JSON
    ↓
Validation
    ↓
Highlight errors
```

Spellcheck не повинен викликатися на кожну клавішу.

Можливі тригери:

* пауза після введення;
* завершення речення;
* зміна абзацу;
* ручна команда `Check Spelling`.

---

# 28. Безпека та приватність

Усі AI-запити виконуються локально.

За замовчуванням:

```text
UTextEditor
      ↓
localhost
      ↓
Ollama
```

Редактор не повинен передавати текст документа в Internet.

У MVP не потрібна авторизація або cloud backend.

---

# 29. Логи

AI errors повинні логуватися.

Наприклад:

```text
logs/utexteditor.log
```

Лог повинен містити:

* timestamp;
* operation;
* provider;
* model;
* duration;
* error;
* request id.

За замовчуванням повний текст документа не повинен записуватися в лог.

---

# 30. Тестування

Необхідні unit tests для:

* file manager;
* document state;
* dirty state;
* tab management;
* prompt generation;
* context generation;
* JSON parsing;
* spellcheck result validation;
* completion result validation;
* stale response handling.

Integration tests:

```text
UTextEditor
    ↓
mock Ollama
    ↓
completion
```

В Ollama-independent tests реальний AI не повинен використовуватися.

---

# 31. MVP acceptance criteria

Проєкт вважається готовим до MVP, коли:

### Editor

* можна створити документ;
* можна відкрити файл;
* можна редагувати файл;
* можна зберегти файл;
* працюють вкладки;
* працює undo/redo;
* працює пошук.

### Ollama

При запущеному:

```text
ollama serve
```

і встановленій:

```text
gemma4:12b
```

модель повинна бути доступною UTextEditor.

### Completion

Для тексту:

```text
The weather today is
```

AI може повернути приблизне продовження:

```text
sunny and warm.
```

Це продовження відображається як ghost text.

Натискання:

```text
Tab
```

перетворює його на реальний текст.

### Spellcheck

Текст з помилкою:

```text
This is teh test.
```

повинен бути ідентифікований, а користувачу повинно бути запропоновано:

```text
the
```

### Responsiveness

Під час генерації AI GUI залишається працездатним.

---

# 32. Майбутній розвиток

Після MVP можна додати:

* AI rewrite;
* Translate;
* Summarize;
* Explain selected text;
* AI chat sidebar;
* code syntax highlighting;
* Markdown preview;
* multiple completion candidates;
* completion через streaming;
* custom system prompt;
* project-specific AI context;
* document-aware suggestions;
* autocomplete для програмного коду;
* plugins;
* Windows support.

---

# 33. Основний принцип UX

UTextEditor повинен залишатися **звичайним текстовим редактором навіть без AI**.

AI має бути допоміжною функцією, а не перехоплювати керування редактором.

Користувач повинен завжди мати можливість:

```text
type → ignore AI → continue writing
```

а AI повинен працювати максимально ненав'язливо.

---

# 34. Definition of Done

Перший реліз UTextEditor повинен запускатися як desktop application і дозволяти користувачу:

```text
1. Open editor
2. Create/open text file
3. Write text
4. Receive inline AI completion
5. Accept completion with Tab
6. See spelling errors
7. Apply corrections
8. Save document
```

При цьому AI працює локально через:

```text
Ollama
└── gemma4:12b
```

і відмова/недоступність AI не повинна впливати на базову роботу текстового редактора.
