# Python Design Patterns — Part 2: Structural Patterns

> **Structural patterns** deal with how classes and objects are composed to form larger structures, keeping the system flexible and efficient.

---

## 1. Adapter

**What:** Converts the interface of a class into another interface that clients expect. Lets incompatible interfaces work together.

**When to use:**
- Integrating third-party libraries with different APIs
- Legacy system migration (wrapping old code behind a new interface)
- Switching payment providers, logging libraries, or ORMs
- Unifying data from different sources (APIs returning different shapes)

```python
from abc import ABC, abstractmethod


# Target interface your app expects
class PaymentProcessor(ABC):
    @abstractmethod
    def pay(self, amount: float, currency: str) -> dict:
        pass

    @abstractmethod
    def refund(self, transaction_id: str, amount: float) -> dict:
        pass


# Third-party SDK #1 — Stripe-like
class StripeSDK:
    def create_charge(self, amount_cents: int, cur: str) -> dict:
        return {"id": "ch_abc", "provider": "stripe", "charged": amount_cents, "currency": cur}

    def create_refund(self, charge_id: str, amount_cents: int) -> dict:
        return {"id": "re_xyz", "charge": charge_id, "refunded": amount_cents}


# Third-party SDK #2 — Razorpay-like
class RazorpaySDK:
    def initiate_payment(self, amount_paise: int, currency_code: str) -> dict:
        return {"payment_id": "pay_123", "provider": "razorpay", "amount": amount_paise}

    def initiate_refund(self, payment_id: str, amount_paise: int) -> dict:
        return {"refund_id": "rfnd_456", "payment_id": payment_id}


# Adapters — translate your interface to each SDK
class StripeAdapter(PaymentProcessor):
    def __init__(self, sdk: StripeSDK):
        self._sdk = sdk

    def pay(self, amount: float, currency: str) -> dict:
        return self._sdk.create_charge(int(amount * 100), currency)

    def refund(self, transaction_id: str, amount: float) -> dict:
        return self._sdk.create_refund(transaction_id, int(amount * 100))


class RazorpayAdapter(PaymentProcessor):
    def __init__(self, sdk: RazorpaySDK):
        self._sdk = sdk

    def pay(self, amount: float, currency: str) -> dict:
        return self._sdk.initiate_payment(int(amount * 100), currency)

    def refund(self, transaction_id: str, amount: float) -> dict:
        return self._sdk.initiate_refund(transaction_id, int(amount * 100))


# Usage — your app code doesn't care which provider
def checkout(processor: PaymentProcessor, amount: float):
    result = processor.pay(amount, "INR")
    print(f"Payment: {result}")
    return result


checkout(StripeAdapter(StripeSDK()), 499.99)
checkout(RazorpayAdapter(RazorpaySDK()), 499.99)
```

---

## 2. Decorator

**What:** Dynamically adds responsibilities to an object without modifying its class. Wraps objects in layers of behavior.

**When to use:**
- Adding logging, caching, or retry logic to services
- Middleware pipelines (Django, Flask)
- Stream compression / encryption layers
- Feature toggles / A-B testing wrappers
- Measuring execution time

### Class-Based Decorator

```python
from abc import ABC, abstractmethod
import time


class DataService(ABC):
    @abstractmethod
    def fetch(self, key: str) -> str:
        pass


class DatabaseService(DataService):
    def fetch(self, key: str) -> str:
        time.sleep(0.01)  # simulate DB latency
        return f"data_for_{key}"


class CachingDecorator(DataService):
    def __init__(self, wrapped: DataService):
        self._wrapped = wrapped
        self._cache: dict[str, str] = {}

    def fetch(self, key: str) -> str:
        if key not in self._cache:
            print(f"    [Cache MISS] {key}")
            self._cache[key] = self._wrapped.fetch(key)
        else:
            print(f"    [Cache HIT]  {key}")
        return self._cache[key]


class LoggingDecorator(DataService):
    def __init__(self, wrapped: DataService):
        self._wrapped = wrapped

    def fetch(self, key: str) -> str:
        print(f"    [Log] Fetching '{key}'...")
        start = time.time()
        result = self._wrapped.fetch(key)
        elapsed = (time.time() - start) * 1000
        print(f"    [Log] Done in {elapsed:.1f}ms")
        return result


class RetryDecorator(DataService):
    def __init__(self, wrapped: DataService, max_retries: int = 3):
        self._wrapped = wrapped
        self._max_retries = max_retries

    def fetch(self, key: str) -> str:
        for attempt in range(1, self._max_retries + 1):
            try:
                return self._wrapped.fetch(key)
            except Exception as e:
                print(f"    [Retry] Attempt {attempt} failed: {e}")
                if attempt == self._max_retries:
                    raise
        return ""


# Stack decorators like layers
service = LoggingDecorator(
    CachingDecorator(
        RetryDecorator(
            DatabaseService()
        )
    )
)

print("First call:")
print(f"  Result: {service.fetch('user:42')}")
print("Second call:")
print(f"  Result: {service.fetch('user:42')}")  # cache hit
```

### Python-Specific: Function Decorators

```python
import functools
import time


def retry(max_attempts: int = 3, delay: float = 0.5):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"  Attempt {attempt} failed: {e}")
                    if attempt == max_attempts:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator


def log_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"  Calling {func.__name__}({args}, {kwargs})")
        result = func(*args, **kwargs)
        print(f"  → {result}")
        return result
    return wrapper


def cache(func):
    memo = {}

    @functools.wraps(func)
    def wrapper(*args):
        if args not in memo:
            memo[args] = func(*args)
        return memo[args]
    return wrapper


@log_calls
@retry(max_attempts=2)
@cache
def fetch_user(user_id: int) -> dict:
    return {"id": user_id, "name": f"User {user_id}"}


fetch_user(42)
```

---

## 3. Facade

**What:** Provides a simplified interface to a complex subsystem. Hides internal complexity behind a clean API.

**When to use:**
- Wrapping complex libraries (video encoding, email sending)
- Simplifying multi-step processes (user onboarding, order checkout)
- API gateway or service aggregation layers
- SDK wrappers for internal microservices

```python
# ── Complex subsystems ──
class InventoryService:
    def check_stock(self, product_id: str) -> bool:
        print(f"    [Inventory] Checking stock for {product_id}")
        return True

    def reserve(self, product_id: str, qty: int):
        print(f"    [Inventory] Reserved {qty}x {product_id}")

    def release(self, product_id: str, qty: int):
        print(f"    [Inventory] Released {qty}x {product_id}")


class PaymentService:
    def authorize(self, user_id: str, amount: float) -> str:
        print(f"    [Payment] Authorized ${amount} for {user_id}")
        return "auth_abc123"

    def capture(self, auth_id: str) -> str:
        print(f"    [Payment] Captured {auth_id}")
        return "txn_xyz789"

    def void(self, auth_id: str):
        print(f"    [Payment] Voided {auth_id}")


class ShippingService:
    def estimate(self, address: str) -> dict:
        print(f"    [Shipping] Estimated for {address}")
        return {"days": 3, "cost": 5.99}

    def create_shipment(self, address: str, product_id: str) -> str:
        print(f"    [Shipping] Created shipment for {product_id}")
        return "SHIP-001"


class NotificationService:
    def send_email(self, user_id: str, subject: str, body: str):
        print(f"    [Email] To {user_id}: {subject}")

    def send_sms(self, phone: str, message: str):
        print(f"    [SMS] To {phone}: {message}")


# ── Facade ──
class OrderFacade:
    def __init__(self):
        self._inventory = InventoryService()
        self._payment = PaymentService()
        self._shipping = ShippingService()
        self._notifications = NotificationService()

    def place_order(
        self, user_id: str, product_id: str, qty: int,
        amount: float, address: str
    ) -> dict:
        # 1. Check stock
        if not self._inventory.check_stock(product_id):
            raise Exception(f"{product_id} is out of stock")

        # 2. Reserve inventory
        self._inventory.reserve(product_id, qty)

        # 3. Authorize payment
        auth_id = self._payment.authorize(user_id, amount)

        try:
            # 4. Capture payment
            txn_id = self._payment.capture(auth_id)

            # 5. Ship
            tracking = self._shipping.create_shipment(address, product_id)

            # 6. Notify
            self._notifications.send_email(
                user_id, "Order Confirmed", f"Tracking: {tracking}"
            )

            return {"txn_id": txn_id, "tracking": tracking, "status": "confirmed"}

        except Exception:
            # Rollback on failure
            self._payment.void(auth_id)
            self._inventory.release(product_id, qty)
            raise


# Usage — caller doesn't know about the 4 subsystems
order = OrderFacade()
result = order.place_order("u1", "SKU-42", 2, 59.98, "123 Main St, Mumbai")
print(f"\nOrder result: {result}")
```

---

## 4. Proxy

**What:** Provides a surrogate or placeholder for another object to control access to it.

**When to use:**
- Lazy loading (load expensive resources only when needed)
- Access control / authorization checks
- Rate limiting API calls
- Virtual proxies for large images or files
- Logging and monitoring wrappers

```python
from abc import ABC, abstractmethod
import time


class APIClient(ABC):
    @abstractmethod
    def request(self, endpoint: str) -> str:
        pass


class RealAPIClient(APIClient):
    def request(self, endpoint: str) -> str:
        return f"Response from {endpoint}"


class RateLimitingProxy(APIClient):
    def __init__(self, client: APIClient, max_per_second: int = 5):
        self._client = client
        self._max = max_per_second
        self._timestamps: list[float] = []

    def request(self, endpoint: str) -> str:
        now = time.time()
        # Remove timestamps older than 1 second
        self._timestamps = [t for t in self._timestamps if now - t < 1.0]

        if len(self._timestamps) >= self._max:
            wait = 1.0 - (now - self._timestamps[0])
            raise Exception(f"Rate limit exceeded. Retry in {wait:.2f}s")

        self._timestamps.append(now)
        return self._client.request(endpoint)


class AuthProxy(APIClient):
    def __init__(self, client: APIClient, allowed_roles: set[str]):
        self._client = client
        self._allowed = allowed_roles
        self._current_role: str | None = None

    def set_role(self, role: str):
        self._current_role = role

    def request(self, endpoint: str) -> str:
        if self._current_role not in self._allowed:
            raise PermissionError(
                f"Role '{self._current_role}' cannot access {endpoint}"
            )
        return self._client.request(endpoint)


class CachingProxy(APIClient):
    def __init__(self, client: APIClient, ttl_seconds: float = 60):
        self._client = client
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[str, float]] = {}

    def request(self, endpoint: str) -> str:
        now = time.time()
        if endpoint in self._cache:
            result, timestamp = self._cache[endpoint]
            if now - timestamp < self._ttl:
                print(f"    [Cache] Serving cached: {endpoint}")
                return result

        result = self._client.request(endpoint)
        self._cache[endpoint] = (result, now)
        return result


# Usage — stack proxies
api = AuthProxy(
    CachingProxy(
        RateLimitingProxy(RealAPIClient(), max_per_second=3),
        ttl_seconds=30,
    ),
    allowed_roles={"admin", "editor"},
)
api.set_role("admin")

print(api.request("/users"))
print(api.request("/users"))  # served from cache
```

---

## 5. Composite

**What:** Composes objects into tree structures to represent part-whole hierarchies. Clients treat individual objects and compositions uniformly.

**When to use:**
- File system representation (files and folders)
- UI component trees (nested layouts, menus)
- Organization hierarchies (departments → teams → people)
- Permission systems (role groups containing roles)
- Pricing rules (composite discounts)

```python
from abc import ABC, abstractmethod


class FileSystemItem(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_size(self) -> int:
        pass

    @abstractmethod
    def display(self, indent: int = 0) -> str:
        pass

    @abstractmethod
    def search(self, query: str) -> list[str]:
        pass


class File(FileSystemItem):
    def __init__(self, name: str, size: int):
        super().__init__(name)
        self._size = size

    def get_size(self) -> int:
        return self._size

    def display(self, indent: int = 0) -> str:
        return f"{'  ' * indent}📄 {self.name} ({self._size} KB)"

    def search(self, query: str) -> list[str]:
        if query.lower() in self.name.lower():
            return [self.name]
        return []


class Folder(FileSystemItem):
    def __init__(self, name: str):
        super().__init__(name)
        self.children: list[FileSystemItem] = []

    def add(self, *items: FileSystemItem) -> "Folder":
        self.children.extend(items)
        return self

    def get_size(self) -> int:
        return sum(child.get_size() for child in self.children)

    def display(self, indent: int = 0) -> str:
        lines = [f"{'  ' * indent}📁 {self.name} ({self.get_size()} KB)"]
        for child in self.children:
            lines.append(child.display(indent + 1))
        return "\n".join(lines)

    def search(self, query: str) -> list[str]:
        results = []
        if query.lower() in self.name.lower():
            results.append(self.name)
        for child in self.children:
            results.extend(child.search(query))
        return results


# Usage
root = Folder("project")
src = Folder("src")
src.add(
    File("index.py", 12),
    File("app.py", 8),
    File("models.py", 15),
)

tests = Folder("tests")
tests.add(
    File("test_app.py", 5),
    File("test_models.py", 7),
)

root.add(src, tests, File("README.md", 2), File("pyproject.toml", 1))

print(root.display())
print(f"\nTotal size: {root.get_size()} KB")
print(f"Search 'test': {root.search('test')}")
```

---

## 6. Bridge

**What:** Decouples an abstraction from its implementation so the two can vary independently.

**When to use:**
- Cross-platform rendering (same shape API, different renderers)
- Database drivers (same query interface, different DB engines)
- Message sending (same message API, different transports)
- Notification + channel combinations

```python
from abc import ABC, abstractmethod


# ── Implementation layer (how to send) ──
class MessageTransport(ABC):
    @abstractmethod
    def deliver(self, recipient: str, content: str) -> str:
        pass


class EmailTransport(MessageTransport):
    def deliver(self, recipient: str, content: str) -> str:
        return f"📧 Email to {recipient}: {content}"


class SMSTransport(MessageTransport):
    def deliver(self, recipient: str, content: str) -> str:
        return f"📱 SMS to {recipient}: {content[:160]}"


class SlackTransport(MessageTransport):
    def deliver(self, recipient: str, content: str) -> str:
        return f"💬 Slack to #{recipient}: {content}"


# ── Abstraction layer (what to send) ──
class Message(ABC):
    def __init__(self, transport: MessageTransport):
        self._transport = transport

    @abstractmethod
    def send(self, recipient: str) -> str:
        pass


class AlertMessage(Message):
    def __init__(self, transport: MessageTransport, severity: str, details: str):
        super().__init__(transport)
        self.severity = severity
        self.details = details

    def send(self, recipient: str) -> str:
        content = f"🚨 [{self.severity.upper()}] {self.details}"
        return self._transport.deliver(recipient, content)


class ReminderMessage(Message):
    def __init__(self, transport: MessageTransport, task: str, due: str):
        super().__init__(transport)
        self.task = task
        self.due = due

    def send(self, recipient: str) -> str:
        content = f"⏰ Reminder: '{self.task}' is due {self.due}"
        return self._transport.deliver(recipient, content)


class WelcomeMessage(Message):
    def __init__(self, transport: MessageTransport, user_name: str):
        super().__init__(transport)
        self.user_name = user_name

    def send(self, recipient: str) -> str:
        content = f"Welcome aboard, {self.user_name}! We're glad to have you."
        return self._transport.deliver(recipient, content)


# Usage — mix any message type with any transport
print(AlertMessage(EmailTransport(), "critical", "DB is down").send("ops@co.com"))
print(AlertMessage(SlackTransport(), "warning", "High CPU").send("alerts"))
print(ReminderMessage(SMSTransport(), "Deploy v2.1", "tomorrow").send("+91-9876543210"))
print(WelcomeMessage(EmailTransport(), "Priya").send("priya@co.com"))
```

---

## Quick Reference — When to Use Which Structural Pattern

| Pattern | Choose When... | Real-World Example |
|---|---|---|
| **Adapter** | Making incompatible interfaces work together | Switching payment / logging providers |
| **Decorator** | Adding behavior dynamically without changing the class | Caching, logging, retry middleware |
| **Facade** | Simplifying a complex multi-step subsystem | Order checkout, user onboarding |
| **Proxy** | Controlling access — auth, rate limiting, lazy loading | API gateways, image lazy-loaders |
| **Composite** | Tree structures where leaf and branch are treated the same | File systems, UI trees, org charts |
| **Bridge** | Abstraction and implementation should vary independently | Renderers, DB drivers, transports |
