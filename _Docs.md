# 📚 UniEvent Analytics

> Aplikace pro správu a analytiku univerzitních akcí v prostředí Digital Humanities.

Technické zadání a implementační plán pro platformu **UniEvent Analytics** v rámci Digital Humanities.

---

## ✨ Klíčové rysy

- 🎯 **Role-based přístup** - Admin, Teacher, Ambasador, Viewer
- 📋 **Správa akcí** - Vytváření, úprava, šablony, archivace
- ⏳ **FIFO registrace** - Automatický posun z waitlistu při uvolnění místa
- 📊 **Reporty a analytika** - PDF reporty s grafy a metrikami
- 🔍 **Pokročilé vyhledávání** - Filtry, razení, fulltext
- 📱 **Responzivní design** - Funguje na mobilu i desktopu
- ⚡ **Interaktivní UI** - Loading stavy, feedback na akce, real-time feedback

---

## ✅ Potvrzená rozhodnutí týmu

- **Princip přihlašování** - Platí FIFO, tedy "kdo dřív přijde, ten dřív mele"
- **Naplnění kapacity** - Po dosažení kapacity se další přihlášení řadí automaticky do pořadníku náhradníků
- **Uvolnění místa** - Při odhlášení registrovaného účastníka systém automaticky posune prvního náhradníka do stavu `registered`
- **Vizuální směr** - Aplikace se má držet spíše jednotného vizuálu univerzity než zcela autonomního designu

---

## 🛠 Stack technologií

| Komponenta | Technologie |
|:--|:--|
| **Backend** | Django 4.x |
| **Databáze** | SQLite 3 |
| **Frontend** | HTML5, CSS3, JavaScript (vanilla + AJAX) |
| **Analytika** | Pandas |
| **Grafy** | Chart.js |
| **Formát dat** | DD.MM.YYYY HH:mm (lokální čas pro ČR) |

---

## �️ Orientace v kódu pro vývojáře

### Hlavní složky a soubory

```
unievent_analytics/
├── config/                      # Django project settings
│   ├── settings.py              # Nastavení DB, aplikací, ALLOWED_HOSTS
│   ├── urls.py                  # Globální routy (/healthz, /admin, /events/)
│   └── wsgi.py                  # WSGI application pro produkci
│
├── events/                      # Hlavní aplikace
│   ├── models.py               # Datové modely (Teacher, Event, Registration, EventTemplate)
│   ├── views.py                # Business logika a renderování (přihlášení, filtry, bootstrap dat)
│   ├── forms.py                # Django formuláře (EventCreateForm s validacemi)
│   ├── urls.py                 # Routy aplikace (/events/, /events/<id>/, atd.)
│   ├── admin.py                # Django admin registrace modelů
│   └── migrations/             # Migrace databáze (0001_initial, 0002, 0003, ...)
│
├── templates/                  # HTML šablony
│   ├── base.html               # Hlavní šablona (navigace, layout, messages)
│   ├── events/
│   │   ├── login.html          # Role selection (Admin/Teacher/Ambasador/Viewer)
│   │   ├── dashboard.html      # Přehled akcí a registrací
│   │   ├── event_list.html     # Tabulka akcí s filtry (hledání, učitel, místo)
│   │   ├── event_detail.html   # Detail jedné akce + tlačítka Upravit/Smazat
│   │   └── event_create.html   # Formulář pro novou nebo editovanou akci
│
├── static/                     # Statické soubory
│   ├── css/app.css             # CSS styly (theme, layout, responsive)
│   └── js/app.js               # JavaScript (loading overlay)
│
├── manage.py                   # Django CLI
├── db.sqlite3                  # SQLite databáze (lokální dev)
└── requirements.txt            # Python závislosti
```

### Kde hledat co

| **Úkol** | **Soubor** | **Funkce/Model** |
|:--|:--|:--|
| Přihlášení a role | `events/views.py` | `role_login()` |
| Bootstrap demo dat | `events/views.py` | `_bootstrap_demo_events()` |
| Filtrování akcí | `events/views.py` | `event_list()` |
| Vytváření akce | `events/views.py` | `event_create()` |
| Validace formuláře | `events/forms.py` | `EventCreateForm` |
| Datové modely | `events/models.py` | `Event`, `Teacher`, `Registration` |
| Tabulka akcí | `templates/events/event_list.html` | - |
| Detail akce | `templates/events/event_detail.html` | - |
| CSS styly | `static/css/app.css` | - |

### Key koncept: Role-based logika

Role se ukládají v session:
- `request.session['selected_role']` – aktuální role (admin/teacher/ambassador/viewer)
- `request.session['actor_identity']` – jméno přihlášené osoby (pro ownership akcí)

Funkce `_can_manage_event(role, actor_identity, event)` v `views.py` určuje, kdo může upravit/smazat akci.

---

## �📊 Datový model

```
Teachers
├── id (PK)
├── name
└── department

Events
├── id (PK)
├── title
├── date
├── location
├── capacity
├── teacher_id (FK)
└── filling_strategy (FIFO)

Registrations
├── id (PK)
├── event_id (FK)
├── user_id_hashed
├── timestamp
└── status (registered | waitlist | cancelled)

EventTemplates
├── id (PK)
├── title
├── location
├── capacity
├── difficulty
├── teacher_id (optional)
├── is_archived
└── created_by_role
```

---

## 👥 Role a oprávnění

| Role | Akce | Čtení |
|:--|:--|:--|
| **Admin** 🔑 | Všechny operace | Vše |
| **Teacher** 👨‍🏫 | Vytvářet/upravit akce, šablony, vidět reporty | Vlastní a cizí data |
| **Ambasador** 👨‍🎓 | Registrace, zrušení registrace, pomoc na akcích | Vlastní data, základy akcí |
| **Viewer** 👁️ | Žádné | Základní info o akcích (název, místo, čas) |

> **Waitlist viditelnost**: Ambasador vidí své pořadí, Teacher a Admin vidí všechny

---

## 🎯 Přihlášení v MVP

```
┌──────────────────────────────────┐
│   UniEvent Analytics - Login     │
├──────────────────────────────────┤
│                                  │
│  Vyberte si roli:               │
│                                  │
│  [ Admin ]  [ Teacher ]         │
│  [ Ambasador ]  [ Viewer ]      │
│                                  │
│  (bez SSO a externích služeb)   │
└──────────────────────────────────┘
```

---

## 🎪 Správa akcí a šablon

### Životní cyklus akce

```
Vytvoření → Editace → Publikace → Registrace → Uzavření
   ↓                      ↓
  Ze šablony          Archivace
```

### Šablony akcí – Operace v MVP

- ✅ **Vytvořit** - Nová šablona s předvyplněnými poli
- ✅ **Upravit** - Změna jakéhokoli pole (nemá vliv na již vytvořené akce)
- ✅ **Duplikovat** - Zkopírovat existující šablonu
- ✅ **Archivovat** - Skrytí z běžných seznamů, zachování pro audit trail
- ✅ **Obnovit** - Vrácení archivované šablony do aktivního stavu

> ⚠️ **Smazání není v MVP** – Archivujeme kvůli referenční integritě a audit trail

---

## 🔐 FIFO Filling Strategy

```
Kapacita: 20

Registrace #1: REGISTERED ✅
Registrace #2: REGISTERED ✅
...
Registrace #20: REGISTERED ✅
Registrace #21: WAITLIST ⏳
Registrace #22: WAITLIST ⏳

Pokud se osoba #5 zruší:
  → Kapacita se uvolní
  → Osoba z WAITLIST[#1] se automaticky přesune do REGISTERED
```

---

## 🔍 Vyhledávání a filtry

### MVP vyhledávacího enginu

- 🔎 Fulltext podle názvu akce
- 👨‍🏫 Filtr podle učitele
- 📍 Filtr podle místa
- 📅 Filtr podle data (od-do)
- 🎯 Filtr podle obtížnosti (1-5)
- 📊 Výchozí řazení: podle data vzestupně

---

## 📋 Validace dat v MVP

```
✓ Zakázat vytváření akcí do minulosti
✓ Zakázat nulovou nebo zápornou kapacitu
✓ Povinná pole: title, location, date, capacity, difficulty
✓ Zakázat duplicitní akce (stejný čas + místo)
✓ Povolit více akcí v jeden den na stejném místě
  → ALE pouze pokud se casově nepřekrývají
```

---

## 📊 Dashboardy

### Ambasador Dashboard 👨‍🎓

```
┌──────────────────────────────────────┐
│ Ahoj, [Jméno]! 👋                   │
├──────────────────────────────────────┤
│                                      │
│ 🎯 Moje nejbližší akce (3):         │
│   • Kurz A - 12.05.2026 10:00      │
│   • Kurz B - 14.05.2026 14:00      │
│   • Kurz C - 19.05.2026 16:00      │
│                                      │
│ ⏳ Moje waitlist pozice (1):        │
│   • Kurz X - pozice #3              │
│                                      │
│ 📋 Historie registrací - [VÍCE]    │
│                                      │
│ ⚙️ Nastavení | 🚪 Odhlásit se      │
└──────────────────────────────────────┘
```

### Teacher/Admin Dashboard 👨‍🏫

```
Skupiny funkcí:
┌─────────────┐ ┌─────────────┐ ┌──────────┐
│   Akce      │ │ Registrace  │ │ Reporty  │
│             │ │             │ │          │
│ • Nová      │ │ • Přehled   │ │ • Export │
│ • Upravit   │ │ • Waitlist  │ │ • PDF    │
│ • Archiv    │ │ • Zrušit    │ │ • Grafy  │
└─────────────┘ └─────────────┘ └──────────┘

┌─────────────┐ ┌──────────────┐
│  Šablony    │ │   Správa     │
│             │ │              │
│ • Nová      │ │ • Uživatelé  │
│ • Duplik.   │ │ • Nastavení  │
│ • Archiv    │ │ • Export     │
└─────────────┘ └──────────────┘
```

> 💡 **Poznámka**: Nastavení Ambasadora bude v MVP přítomné vizuálně; nefunkční položky budou zašedlé

---

## 📈 Reporty a analytika

### Metriky reportu učitele
 (fáze 3)

- 📊 Počet akcí za zvolené obdobobsazená místa
- 📋 Počty registrací: registered / waitlist / cancelled
- 📅 Rozložení akcí podle měsíce
- 📆 Rozložení akcí podle dne v týdnu

### PDF Export

```
┌─────────────────────────────────┐
│  Report: Mgr. Jan Novotný      │
│  Období: 01.05.2026 - 31.05.26 │
├─────────────────────────────────┤
│                                 │
│  Souhrnná tabulka metrik:      │
│  • Akcí: 12                    │
│  • Průměrná obtížnost: 3.2    │
│  • Kapacita: 240               │
│  • Obsazeno: 185 (77%)        │
│                                 │
│  Tabulka akcí:                 │
│  ┌─────────────────────────┐   │
│  │ Název | Datum | Místo   │   │
│  │ ... (10 akcí)           │   │
│  └─────────────────────────┘   │
│                                 │
│  [GRAFY: Měsíc + Den v týdnu]  │
│                                 │
│  Strana 1/2                     │
└─────────────────────────────────┘
```

> Max. 2 stránky, pouze pro jednoho zvoleného učitele

---

## ⚡ Interaktivita a UI Feedback

### Uživatelské zpětné vazby v MVP

- ⏳ **Loading stavy** - Spinner při načítání akcí, registraci, exportu
- ✅ **Success notify** - Zelené hlášení "Akce uložena" / "Registrace potvrzena"
- ⚠️ **Error messages** - Červené upozornění na chyby (validace, duplikáty)
- 🔄 **Real-time updates** - Zobrazení obsazenosti v přehledu akcí
- 🎨 **Hover efekty** - Tlačítka a karty se reagují na najetí myši
- 📱 **Touch-friendly** - Větší cílové plochy na mobilu (min. 44x44px)
- 🎭 **Disabled stavy** - Zašednutá tlačítka pro nefunkční akce v MVP

---

## 🎨 UI Design – Jednotný vizuál FF UPCE

### Barvy

> Směr rozhraní je navázán na jednotný vizuální styl univerzity; vlastní odchylky jsou přípustné jen tam, kde zlepší použitelnost aplikace.

- 🟠 **Primární**: Oranžová (#E86D00, #FF6B1A)
- ⚪ **Sekundární**: Bílá
- 🔘 **Akcentní**: Tmavá šedá pro text (#333, #555)

### Layout

```
┌────────────────────────────────────┐
│  Logo  │  Navigace                  │
│        │  AKCE | REPORT | ŠABLONY  │
├────────────────────────────────────┤
│                                    │
│  [Obsah stránky]                  │
│  - Hero section / Dashboard       │
│  - Card-based layout              │
│  - Responsive: 1/2/3 sloupce      │
│                                    │
├────────────────────────────────────┤
│ Footer s odkazy a informacemi     │
└────────────────────────────────────┘
```

### Responsive design

- 📱 **Mobil** (< 640px): Hamburger menu, 1 sloupec
- 📊 **Tablet** (640-1024px): 2 sloupce
- 🖥️ **Desktop** (> 1024px): 3 sloupce, plný layout

---

## 📋 TODO – Implementační plán

### Fáze 1: Jádro a databáze 🏗️

- [ ] Inicializace Django projektu a SQLite schéma
- [ ] Modely: `Teachers`, `Events`, `Registrations`, `EventTemplates`
- [ ] Jednoduché přihlášení (role selection bez SSO)
- [ ] Skript na import testovacích dat
- [ ] Anonymizace – odloženo do fáze 2

### Fáze 2: Webové rozhraní a vyhledávání 🎨

- [ ] Vyhledávací engine s filtry
- [ ] Formulář pro vytváření akcí
- [ ] Šablony akcí (CRUD)
- [ ] Detail akce + registrace
- [ ] FIFO filling strategy
- [ ] Automatický posun z waitlistu
- [ ] Responzivní UI (mobile-first)
- [ ] Loading stavy a UI feedback
- [ ] Dashboard podle role

### Fáze 3: Analytika a reporty 📊

- [ ] Logika reportů učitele
- [ ] Grafy (měsíc, den v týdnu)
- [ ] PDF export
- [ ] Limity na 2 stránky

### Fáze 4: Backlog 📌

- [ ] **[Kritický]** Není možné se registrovat – ambasador nemá UI ani logiku pro registraci na akci
- [ ] Viewer vidí kolonky „Aktivní registrace" a „Waitlist" – tyto sloupce by měl vidět až od role Ambasador výš
- [ ] SSO integrace
- [ ] Predikce obtížnosti
- [ ] Rozšířená autentizace

---

## 🆚 Stav specifikace

| Součást | Stav |
|:--|:--|
| Datový model | ✅ Hotovo |
| Role a oprávnění | ✅ Hotovo |
| Šablony akcí | ✅ Hotovo |
| Vyhledávání | ✅ Hotovo |
| Reporty | ✅ Hotovo |
| UI design | ✅ Hotovo (inspirace FF UPCE) |
| Interaktivita | ✅ Specifikováno |
| Validace | ✅ Specifikováno |
