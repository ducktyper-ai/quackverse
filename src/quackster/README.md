# 🧙 Quackster

**Quackster** is the dedicated teaching and gamification module of the QuackVerse. It powers interactive learning features across DuckTyper, including XP, badges, quests, and NPCs. If `quackcore` is the infrastructure, **Quackster is the teacher.**

---

## 🧠 Purpose

Quackster centralizes all learning logic so that:
- QuackCore stays clean and infrastructure-focused
- Teaching logic remains modular and upgradeable
- All gamification, feedback, and tutorial progress systems are handled in one place

---

## 📦 Folder Structure

```
src/quackster/
├── __init__.py
├── academy/              # Course, assignment, grading logic
├── core/                 # XP, badges, quests, certificates
├── github/               # GitHub grading + assignment submission
├── npc/                  # Dialogue systems and NPC logic
├── plugins.py            # DuckTyper plugin registration
└── README.md
```

---

## 🧩 Key Components

### 🎓 `academy/`
Logic for managing structured learning:
- Courses and tutorials
- Assignments with metadata
- Grading and feedback APIs

### 🪙 `core/`
The heart of the gamification system:
- XP and leveling
- Badges and quests
- Certificate generation

### 🐙 `github/`
Handles GitHub-based submission and evaluation:
- Pull request parsing
- Repo feedback
- Instructor automation

### 🧠 `npc/`
Interactive learning assistant logic:
- Dialogue scripting with Jinja2 templates
- Memory and progress tracking
- Persona & quest logic (Quackster the duck!)

---

## 🔌 Plugin Registration

Quackster is discoverable by DuckTyper via plugins:

```python
from quackcore.integrations.core import register_plugin

@register_plugin("teaching")
def register_teaching():
    return TeachingEngine()
```

---

## 🛠 Example Usage in DuckTyper

```python
from quackster.core.xp import award_xp
award_xp(user_id=\"duck123\", amount=50)
```

Trigger NPC dialogue from a CLI command:
```python
from quackster.npc.dialogue.registry import get_greeting
print(get_greeting(\"morning\"))
```

---

## 🧪 Testing

All tests now live under `tests/quackster/`, organized by submodule (e.g. `test_academy`, `test_npc`, etc.). GitHub mocking is handled by `quackcore.testing.github`.

---

## 🧭 Design Principles

- No teaching logic in `quackcore` — it all lives here
- Teaching is **optional and modular** — tools can ignore it if not used
- Gamification is easy to extend and version

---

## 🔮 Future Directions

- Integration with a user dashboard for live stats
- AI-powered NPCs with memory across sessions
- Dynamic quests and boss battles for advanced tutorials 🐉

---

🧙 Built for devs who learn like adventurers.  
Let Quackster guide the way. 🦆✨