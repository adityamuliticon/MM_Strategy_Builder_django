# Python Design Patterns — Part 1: Creational Patterns

> **Creational patterns** deal with object creation mechanisms, providing flexible ways to create objects while hiding the creation logic.

---

## 1. Singleton

**What:** Ensures a class has only one instance and provides a global access point to it.

**When to use:**
- Database connection pools
- Logger instances
- Configuration / settings managers
- Caching layers
- Thread pools

```python
class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connection = None
        return cls._instance

    def connect(self, connection_string: str):
        if self._connection is None:
            self._connection = f"Connected to {connection_string}"
        return self._connection


# Usage
db1 = DatabaseConnection()
db2 = DatabaseConnection()
print(db1 is db2)  # True — same instance

db1.connect("postgres://localhost/mydb")
print(db2.connect("ignored"))  # Returns existing connection
```

### Thread-Safe Singleton (production use)

```python
import threading


class AppConfig:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # double-checked locking
                    cls._instance = super().__new__(cls)
                    cls._instance._settings = {}
        return cls._instance

    def set(self, key: str, value):
        self._settings[key] = value

    def get(self, key: str, default=None):
        return self._settings.get(key, default)
```

---

## 2. Factory Method

**What:** Defines an interface for creating objects but lets subclasses or a factory decide which class to instantiate.

**When to use:**
- When the exact type of object isn't known until runtime
- Payment processing (Stripe, PayPal, Razorpay)
- Notification systems (Email, SMS, Push)
- Document export (PDF, DOCX, CSV)
- Database drivers (MySQL, PostgreSQL, SQLite)

```python
from abc import ABC, abstractmethod


class Notification(ABC):
    @abstractmethod
    def send(self, message: str) -> str:
        pass


class EmailNotification(Notification):
    def send(self, message: str) -> str:
        return f"📧 Email sent: {message}"


class SMSNotification(Notification):
    def send(self, message: str) -> str:
        return f"📱 SMS sent: {message}"


class PushNotification(Notification):
    def send(self, message: str) -> str:
        return f"🔔 Push notification: {message}"


class SlackNotification(Notification):
    def send(self, message: str) -> str:
        return f"💬 Slack message: {message}"


class NotificationFactory:
    _registry: dict[str, type[Notification]] = {
        "email": EmailNotification,
        "sms": SMSNotification,
        "push": PushNotification,
        "slack": SlackNotification,
    }

    @classmethod
    def register(cls, channel: str, notification_cls: type[Notification]):
        """Allow registering new notification types at runtime."""
        cls._registry[channel] = notification_cls

    @classmethod
    def create(cls, channel: str) -> Notification:
        if channel not in cls._registry:
            raise ValueError(f"Unknown channel: {channel}. Available: {list(cls._registry)}")
        return cls._registry[channel]()


# Usage
notification = NotificationFactory.create("email")
print(notification.send("Hello!"))

# Send to multiple channels
for channel in ["email", "slack", "push"]:
    n = NotificationFactory.create(channel)
    print(n.send("Server is back online"))
```

---

## 3. Abstract Factory

**What:** Provides an interface for creating families of related objects without specifying their concrete classes.

**When to use:**
- Cross-platform UI toolkits (Windows vs macOS vs Linux widgets)
- Database abstraction layers (MySQL vs PostgreSQL families)
- Theming systems (light theme vs dark theme component sets)
- Game development (different enemy/weapon/powerup sets per level)

```python
from abc import ABC, abstractmethod


# ── Abstract products ──
class Button(ABC):
    @abstractmethod
    def render(self) -> str:
        pass

class TextField(ABC):
    @abstractmethod
    def render(self) -> str:
        pass

class Checkbox(ABC):
    @abstractmethod
    def render(self) -> str:
        pass


# ── Material theme products ──
class MaterialButton(Button):
    def render(self) -> str:
        return "<MaterialButton elevated />"

class MaterialTextField(TextField):
    def render(self) -> str:
        return "<MaterialTextField outlined />"

class MaterialCheckbox(Checkbox):
    def render(self) -> str:
        return "<MaterialCheckbox ripple />"


# ── iOS theme products ──
class IOSButton(Button):
    def render(self) -> str:
        return "<IOSButton rounded />"

class IOSTextField(TextField):
    def render(self) -> str:
        return "<IOSTextField borderless />"

class IOSCheckbox(Checkbox):
    def render(self) -> str:
        return "<IOSToggle switch />"


# ── Abstract factory ──
class UIFactory(ABC):
    @abstractmethod
    def create_button(self) -> Button:
        pass

    @abstractmethod
    def create_text_field(self) -> TextField:
        pass

    @abstractmethod
    def create_checkbox(self) -> Checkbox:
        pass


class MaterialFactory(UIFactory):
    def create_button(self) -> Button:
        return MaterialButton()

    def create_text_field(self) -> TextField:
        return MaterialTextField()

    def create_checkbox(self) -> Checkbox:
        return MaterialCheckbox()


class IOSFactory(UIFactory):
    def create_button(self) -> Button:
        return IOSButton()

    def create_text_field(self) -> TextField:
        return IOSTextField()

    def create_checkbox(self) -> Checkbox:
        return IOSCheckbox()


# ── Usage ──
def build_login_form(factory: UIFactory) -> list[str]:
    return [
        factory.create_text_field().render(),
        factory.create_text_field().render(),
        factory.create_checkbox().render(),
        factory.create_button().render(),
    ]


# Switch entire UI theme by changing one factory
import platform

factory = MaterialFactory() if platform.system() == "Linux" else IOSFactory()
form = build_login_form(factory)
for widget in form:
    print(f"  {widget}")
```

---

## 4. Builder

**What:** Separates the construction of a complex object from its representation, allowing the same construction process to create different representations.

**When to use:**
- Building complex configuration objects (HTTP requests, queries)
- Constructing objects with many optional parameters
- Creating test data / fixtures
- Email or report builders
- ORM query builders

```python
from dataclasses import dataclass, field


@dataclass
class HttpRequest:
    method: str = "GET"
    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, str] = field(default_factory=dict)
    body: str | None = None
    timeout: int = 30
    retries: int = 0


class HttpRequestBuilder:
    def __init__(self):
        self._request = HttpRequest()

    def method(self, method: str) -> "HttpRequestBuilder":
        self._request.method = method.upper()
        return self

    def url(self, url: str) -> "HttpRequestBuilder":
        self._request.url = url
        return self

    def header(self, key: str, value: str) -> "HttpRequestBuilder":
        self._request.headers[key] = value
        return self

    def query(self, key: str, value: str) -> "HttpRequestBuilder":
        self._request.query_params[key] = value
        return self

    def body(self, body: str) -> "HttpRequestBuilder":
        self._request.body = body
        return self

    def timeout(self, seconds: int) -> "HttpRequestBuilder":
        self._request.timeout = seconds
        return self

    def retries(self, count: int) -> "HttpRequestBuilder":
        self._request.retries = count
        return self

    def build(self) -> HttpRequest:
        if not self._request.url:
            raise ValueError("URL is required")
        return self._request


# Usage — fluent chaining
request = (
    HttpRequestBuilder()
    .method("POST")
    .url("https://api.example.com/users")
    .header("Content-Type", "application/json")
    .header("Authorization", "Bearer token123")
    .query("version", "2")
    .body('{"name": "Alice", "role": "admin"}')
    .timeout(10)
    .retries(3)
    .build()
)

print(request)
```

### Director Pattern (predefined build sequences)

```python
class RequestDirector:
    """Predefined build recipes for common request types."""

    @staticmethod
    def authenticated_get(url: str, token: str) -> HttpRequest:
        return (
            HttpRequestBuilder()
            .method("GET")
            .url(url)
            .header("Authorization", f"Bearer {token}")
            .timeout(15)
            .retries(2)
            .build()
        )

    @staticmethod
    def json_post(url: str, body: str) -> HttpRequest:
        return (
            HttpRequestBuilder()
            .method("POST")
            .url(url)
            .header("Content-Type", "application/json")
            .header("Accept", "application/json")
            .body(body)
            .timeout(30)
            .build()
        )


# Usage
req = RequestDirector.authenticated_get("https://api.example.com/me", "abc123")
```

---

## 5. Prototype

**What:** Creates new objects by cloning an existing object (the prototype) instead of constructing from scratch.

**When to use:**
- When object creation is expensive (DB queries, API calls to populate)
- Game objects (cloning enemy templates with slight variations)
- Document templates (clone a base config, tweak fields)
- Undo/redo systems (snapshot and clone state)
- Caching pre-configured objects

```python
import copy
from dataclasses import dataclass, field


@dataclass
class ServerConfig:
    host: str
    port: int
    ssl: bool
    database: dict = field(default_factory=dict)
    features: list[str] = field(default_factory=list)
    options: dict = field(default_factory=dict)

    def clone(self) -> "ServerConfig":
        """Deep copy so nested dicts/lists are independent."""
        return copy.deepcopy(self)


# Base template — expensive to build in real life
base_config = ServerConfig(
    host="0.0.0.0",
    port=8080,
    ssl=True,
    database={"engine": "postgres", "pool_size": 20, "timeout": 30},
    features=["auth", "rate_limiting", "cors"],
    options={"log_level": "info", "max_body_size": "10mb"},
)

# Dev: clone and tweak
dev = base_config.clone()
dev.host = "localhost"
dev.ssl = False
dev.database["pool_size"] = 5
dev.options["log_level"] = "debug"
dev.features.append("hot_reload")

# Staging: clone and tweak
staging = base_config.clone()
staging.port = 9090
staging.database["pool_size"] = 10

# Production: clone base as-is, just change host
prod = base_config.clone()
prod.host = "prod.example.com"

print(f"Dev:     {dev.host}:{dev.port} ssl={dev.ssl} pool={dev.database['pool_size']}")
print(f"Staging: {staging.host}:{staging.port} ssl={staging.ssl} pool={staging.database['pool_size']}")
print(f"Prod:    {prod.host}:{prod.port} ssl={prod.ssl} pool={prod.database['pool_size']}")
```

### Prototype Registry

```python
class ConfigRegistry:
    """Store named prototypes and clone them on demand."""

    def __init__(self):
        self._prototypes: dict[str, ServerConfig] = {}

    def register(self, name: str, config: ServerConfig):
        self._prototypes[name] = config

    def create(self, name: str) -> ServerConfig:
        if name not in self._prototypes:
            raise KeyError(f"No prototype named '{name}'")
        return self._prototypes[name].clone()


registry = ConfigRegistry()
registry.register("base", base_config)
registry.register("dev", dev)

new_dev = registry.create("dev")
new_dev.port = 3000  # independent copy
```

---

## Quick Reference — When to Use Which Creational Pattern

| Pattern | Choose When... | Real-World Example |
|---|---|---|
| **Singleton** | Exactly one instance needed globally | Logger, DB pool, app config |
| **Factory Method** | Object type decided at runtime | Payment gateways, notifications |
| **Abstract Factory** | Families of related objects vary together | Cross-platform UI, theming |
| **Builder** | Complex object with many optional parts | HTTP clients, query builders, test data |
| **Prototype** | Cloning is cheaper than constructing | Game entities, config templates |
