# Python Design Patterns — Part 3: Behavioral Patterns

> **Behavioral patterns** deal with communication between objects, defining how they interact and distribute responsibility.

---

## 1. Observer

**What:** Defines a one-to-many dependency where when one object changes state, all its dependents are notified automatically.

**When to use:**
- Event-driven systems (GUI events, WebSocket messages)
- Pub/sub messaging (chat rooms, notification feeds)
- State management (reactive stores)
- Stock price tickers, live dashboards
- Form validation (field changes trigger validators)

```python
from typing import Callable, Any


class EventEmitter:
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = {}

    def on(self, event: str, callback: Callable) -> Callable:
        """Register a listener. Returns the callback for easy unsubscription."""
        self._listeners.setdefault(event, []).append(callback)
        return callback

    def off(self, event: str, callback: Callable):
        if event in self._listeners:
            self._listeners[event].remove(callback)

    def emit(self, event: str, data: Any = None):
        for callback in self._listeners.get(event, []):
            callback(data)

    def once(self, event: str, callback: Callable):
        """Listen for an event only once."""
        def wrapper(data):
            callback(data)
            self.off(event, wrapper)
        self.on(event, wrapper)


# Usage — an e-commerce store
class ProductStore(EventEmitter):
    def __init__(self):
        super().__init__()
        self._products: dict[str, dict] = {}

    def add_product(self, product_id: str, name: str, price: float):
        self._products[product_id] = {"name": name, "price": price, "stock": 0}
        self.emit("product_added", self._products[product_id])

    def update_stock(self, product_id: str, quantity: int):
        product = self._products[product_id]
        old_stock = product["stock"]
        product["stock"] = quantity
        self.emit("stock_changed", {
            "product": product["name"],
            "old": old_stock,
            "new": quantity,
        })
        if old_stock == 0 and quantity > 0:
            self.emit("back_in_stock", product)

    def update_price(self, product_id: str, new_price: float):
        product = self._products[product_id]
        old_price = product["price"]
        product["price"] = new_price
        self.emit("price_changed", {
            "product": product["name"],
            "old_price": old_price,
            "new_price": new_price,
        })


store = ProductStore()

# Different subscribers care about different events
store.on("product_added", lambda d: print(f"  [Catalog] New product: {d['name']}"))
store.on("stock_changed", lambda d: print(f"  [Warehouse] {d['product']}: {d['old']} → {d['new']}"))
store.on("back_in_stock", lambda d: print(f"  [Email] Notify waitlist: {d['name']} is back!"))
store.on("price_changed", lambda d: print(f"  [Analytics] Price change: {d['product']} ${d['old_price']} → ${d['new_price']}"))

store.add_product("p1", "Wireless Mouse", 29.99)
store.update_stock("p1", 50)
store.update_price("p1", 24.99)
store.update_stock("p1", 0)
store.update_stock("p1", 10)  # triggers back_in_stock
```

---

## 2. Strategy

**What:** Defines a family of algorithms, encapsulates each one, and makes them interchangeable at runtime.

**When to use:**
- Sorting / filtering with different algorithms
- Pricing strategies (flat rate, tiered, usage-based)
- Authentication methods (JWT, OAuth, API key)
- Compression algorithms (gzip, brotli, zstd)
- Validation rules that change by context

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


class PricingStrategy(ABC):
    @abstractmethod
    def calculate(self, base_price: float, quantity: int) -> float:
        pass

    @abstractmethod
    def description(self) -> str:
        pass


class FlatPricing(PricingStrategy):
    def calculate(self, base_price: float, quantity: int) -> float:
        return base_price * quantity

    def description(self) -> str:
        return "Flat rate — no discounts"


class TieredPricing(PricingStrategy):
    """10% off for 10+, 20% off for 50+, 30% off for 100+"""
    def calculate(self, base_price: float, quantity: int) -> float:
        if quantity >= 100:
            discount = 0.70
        elif quantity >= 50:
            discount = 0.80
        elif quantity >= 10:
            discount = 0.90
        else:
            discount = 1.0
        return base_price * quantity * discount

    def description(self) -> str:
        return "Tiered: 10% off (10+), 20% off (50+), 30% off (100+)"


class SubscriptionPricing(PricingStrategy):
    def __init__(self, monthly_fee: float):
        self._fee = monthly_fee

    def calculate(self, base_price: float, quantity: int) -> float:
        return self._fee

    def description(self) -> str:
        return f"Flat monthly: ${self._fee}"


class BuyOneGetOneFree(PricingStrategy):
    def calculate(self, base_price: float, quantity: int) -> float:
        paid_items = (quantity + 1) // 2  # pay for half, rounded up
        return base_price * paid_items

    def description(self) -> str:
        return "Buy one get one free"


@dataclass
class CartItem:
    name: str
    base_price: float
    quantity: int


class ShoppingCart:
    def __init__(self, strategy: PricingStrategy):
        self._strategy = strategy
        self._items: list[CartItem] = []

    def set_strategy(self, strategy: PricingStrategy):
        self._strategy = strategy

    def add_item(self, name: str, price: float, qty: int):
        self._items.append(CartItem(name, price, qty))

    def checkout(self) -> float:
        total = 0.0
        print(f"  Strategy: {self._strategy.description()}")
        for item in self._items:
            cost = self._strategy.calculate(item.base_price, item.quantity)
            print(f"    {item.name} x{item.quantity} = ${cost:.2f}")
            total += cost
        print(f"  Total: ${total:.2f}\n")
        return total


# Usage
cart = ShoppingCart(FlatPricing())
cart.add_item("Widget", 10.0, 25)
cart.add_item("Gadget", 5.0, 8)
cart.checkout()

cart.set_strategy(TieredPricing())
cart.checkout()

cart.set_strategy(BuyOneGetOneFree())
cart.checkout()
```

---

## 3. Command

**What:** Encapsulates a request as an object, allowing you to parameterize, queue, log, and undo operations.

**When to use:**
- Undo/redo functionality (text editors, drawing apps)
- Task queues and job schedulers
- Macro recording and playback
- Transaction systems (execute, rollback)
- Remote procedure calls

```python
from abc import ABC, abstractmethod
from collections import deque


class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass

    @abstractmethod
    def description(self) -> str:
        pass


class TextEditor:
    def __init__(self):
        self.content = ""

    def __repr__(self):
        return f'"{self.content}"'


class InsertTextCommand(Command):
    def __init__(self, editor: TextEditor, text: str, position: int):
        self._editor = editor
        self._text = text
        self._position = position

    def execute(self):
        c = self._editor.content
        self._editor.content = c[:self._position] + self._text + c[self._position:]

    def undo(self):
        c = self._editor.content
        self._editor.content = c[:self._position] + c[self._position + len(self._text):]

    def description(self) -> str:
        return f"Insert '{self._text}' at {self._position}"


class DeleteTextCommand(Command):
    def __init__(self, editor: TextEditor, position: int, length: int):
        self._editor = editor
        self._position = position
        self._length = length
        self._deleted = ""

    def execute(self):
        c = self._editor.content
        self._deleted = c[self._position:self._position + self._length]
        self._editor.content = c[:self._position] + c[self._position + self._length:]

    def undo(self):
        c = self._editor.content
        self._editor.content = c[:self._position] + self._deleted + c[self._position:]

    def description(self) -> str:
        return f"Delete {self._length} chars at {self._position}"


class ReplaceTextCommand(Command):
    def __init__(self, editor: TextEditor, old_text: str, new_text: str):
        self._editor = editor
        self._old = old_text
        self._new = new_text

    def execute(self):
        self._editor.content = self._editor.content.replace(self._old, self._new, 1)

    def undo(self):
        self._editor.content = self._editor.content.replace(self._new, self._old, 1)

    def description(self) -> str:
        return f"Replace '{self._old}' → '{self._new}'"


class CommandHistory:
    def __init__(self):
        self._undo_stack: list[Command] = []
        self._redo_stack: list[Command] = []

    def execute(self, command: Command):
        command.execute()
        self._undo_stack.append(command)
        self._redo_stack.clear()

    def undo(self) -> str:
        if not self._undo_stack:
            return "Nothing to undo"
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
        return f"Undid: {cmd.description()}"

    def redo(self) -> str:
        if not self._redo_stack:
            return "Nothing to redo"
        cmd = self._redo_stack.pop()
        cmd.execute()
        self._undo_stack.append(cmd)
        return f"Redid: {cmd.description()}"


# Usage
editor = TextEditor()
history = CommandHistory()

history.execute(InsertTextCommand(editor, "Hello World", 0))
print(f"After insert: {editor}")

history.execute(InsertTextCommand(editor, ", Beautiful", 5))
print(f"After insert: {editor}")

history.execute(ReplaceTextCommand(editor, "World", "Python"))
print(f"After replace: {editor}")

print(history.undo())
print(f"After undo: {editor}")

print(history.redo())
print(f"After redo: {editor}")

print(history.undo())
print(history.undo())
print(f"After 2x undo: {editor}")
```

---

## 4. State

**What:** Allows an object to change its behavior when its internal state changes. The object appears to change its class.

**When to use:**
- Order lifecycle (draft → submitted → paid → shipped → delivered)
- Media players (playing, paused, stopped)
- UI components (loading, error, success states)
- Game character states (idle, walking, attacking, dead)
- Document workflow (draft → review → approved → published)

```python
from abc import ABC, abstractmethod


class OrderState(ABC):
    @abstractmethod
    def proceed(self, order: "Order") -> str:
        pass

    @abstractmethod
    def cancel(self, order: "Order") -> str:
        pass

    @abstractmethod
    def status(self) -> str:
        pass

    @abstractmethod
    def allowed_actions(self) -> list[str]:
        pass


class DraftState(OrderState):
    def proceed(self, order):
        order._state = PaidState()
        return "Payment received. Order is now paid."

    def cancel(self, order):
        order._state = CancelledState()
        return "Draft order cancelled."

    def status(self): return "DRAFT"
    def allowed_actions(self): return ["proceed (pay)", "cancel"]


class PaidState(OrderState):
    def proceed(self, order):
        order._state = ShippedState()
        return "Order shipped!"

    def cancel(self, order):
        order._state = CancelledState()
        return "Paid order cancelled. Refund initiated."

    def status(self): return "PAID"
    def allowed_actions(self): return ["proceed (ship)", "cancel (refund)"]


class ShippedState(OrderState):
    def proceed(self, order):
        order._state = DeliveredState()
        return "Order delivered successfully!"

    def cancel(self, order):
        return "Cannot cancel — already shipped. Please initiate a return."

    def status(self): return "SHIPPED"
    def allowed_actions(self): return ["proceed (deliver)"]


class DeliveredState(OrderState):
    def proceed(self, order):
        return "Order complete. No further action."

    def cancel(self, order):
        return "Cannot cancel — already delivered. Please initiate a return."

    def status(self): return "DELIVERED"
    def allowed_actions(self): return ["(none — terminal state)"]


class CancelledState(OrderState):
    def proceed(self, order):
        return "Cannot proceed — order is cancelled."

    def cancel(self, order):
        return "Already cancelled."

    def status(self): return "CANCELLED"
    def allowed_actions(self): return ["(none — terminal state)"]


class Order:
    def __init__(self, order_id: str):
        self.order_id = order_id
        self._state: OrderState = DraftState()
        self._history: list[str] = [f"Created as {self._state.status()}"]

    def proceed(self) -> str:
        old = self._state.status()
        result = self._state.proceed(self)
        if self._state.status() != old:
            self._history.append(f"{old} → {self._state.status()}")
        return result

    def cancel(self) -> str:
        old = self._state.status()
        result = self._state.cancel(self)
        if self._state.status() != old:
            self._history.append(f"{old} → {self._state.status()}")
        return result

    @property
    def status(self) -> str:
        return self._state.status()

    @property
    def actions(self) -> list[str]:
        return self._state.allowed_actions()

    @property
    def history(self) -> list[str]:
        return self._history


# Usage
order = Order("ORD-001")
print(f"[{order.status}] Actions: {order.actions}")

print(order.proceed())
print(f"[{order.status}] Actions: {order.actions}")

print(order.proceed())
print(f"[{order.status}] {order.cancel()}")  # can't cancel shipped

print(order.proceed())
print(f"[{order.status}]")

print(f"\nHistory: {order.history}")
```

---

## 5. Chain of Responsibility

**What:** Passes a request along a chain of handlers. Each handler decides to process it or pass it to the next handler.

**When to use:**
- Middleware pipelines (Django, Flask, FastAPI)
- Logging with severity levels (debug → info → warn → error)
- Approval workflows (manager → director → VP)
- Input validation chains
- Support ticket escalation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExpenseRequest:
    employee: str
    amount: float
    category: str
    description: str


class ApprovalHandler(ABC):
    def __init__(self):
        self._next: ApprovalHandler | None = None

    def set_next(self, handler: "ApprovalHandler") -> "ApprovalHandler":
        self._next = handler
        return handler

    @abstractmethod
    def handle(self, request: ExpenseRequest) -> str:
        pass

    def pass_to_next(self, request: ExpenseRequest) -> str:
        if self._next:
            return self._next.handle(request)
        return f"❌ No one approved ${request.amount:.0f} from {request.employee}"


class AutoApproval(ApprovalHandler):
    """Auto-approve expenses under $100"""
    def handle(self, request: ExpenseRequest) -> str:
        if request.amount < 100:
            return f"✅ [Auto] Approved ${request.amount:.0f} — {request.description}"
        return self.pass_to_next(request)


class ManagerApproval(ApprovalHandler):
    """Managers approve up to $1,000"""
    def handle(self, request: ExpenseRequest) -> str:
        if request.amount < 1000:
            return f"✅ [Manager] Approved ${request.amount:.0f} — {request.description}"
        print(f"    [Manager] ${request.amount:.0f} exceeds my limit, escalating...")
        return self.pass_to_next(request)


class DirectorApproval(ApprovalHandler):
    """Directors approve up to $10,000"""
    def handle(self, request: ExpenseRequest) -> str:
        if request.amount < 10000:
            return f"✅ [Director] Approved ${request.amount:.0f} — {request.description}"
        print(f"    [Director] ${request.amount:.0f} exceeds my limit, escalating...")
        return self.pass_to_next(request)


class VPApproval(ApprovalHandler):
    """VP approves up to $50,000"""
    def handle(self, request: ExpenseRequest) -> str:
        if request.amount < 50000:
            return f"✅ [VP] Approved ${request.amount:.0f} — {request.description}"
        return f"❌ [VP] Denied ${request.amount:.0f} — needs board approval"


# Build the chain
chain = AutoApproval()
chain.set_next(ManagerApproval()) \
     .set_next(DirectorApproval()) \
     .set_next(VPApproval())

# Usage
requests = [
    ExpenseRequest("Alice", 50, "supplies", "Notebooks"),
    ExpenseRequest("Bob", 500, "software", "IDE license"),
    ExpenseRequest("Charlie", 5000, "equipment", "New monitors"),
    ExpenseRequest("Diana", 25000, "travel", "Conference trip"),
    ExpenseRequest("Eve", 80000, "hiring", "Recruitment agency"),
]

for req in requests:
    print(chain.handle(req))
```

---

## 6. Template Method

**What:** Defines the skeleton of an algorithm in a base class and lets subclasses override specific steps without changing the algorithm's structure.

**When to use:**
- Data processing pipelines (extract → transform → load)
- Report generation (fetch data → format → render → export)
- Testing frameworks (setup → test → teardown)
- Build systems (compile → link → package)
- Game loops (input → update → render)

```python
from abc import ABC, abstractmethod
import time


class DataPipeline(ABC):
    """Template: the pipeline steps are fixed, but each step is customizable."""

    def run(self, source: str) -> dict:
        print(f"Pipeline: {self.__class__.__name__}")
        start = time.time()

        raw = self.extract(source)
        validated = self.validate(raw)
        transformed = self.transform(validated)
        result = self.load(transformed)
        self.notify(result)

        elapsed = (time.time() - start) * 1000
        print(f"  Completed in {elapsed:.0f}ms\n")
        return result

    @abstractmethod
    def extract(self, source: str) -> list[dict]:
        pass

    def validate(self, data: list[dict]) -> list[dict]:
        """Optional hook — subclasses can override for validation."""
        return data

    @abstractmethod
    def transform(self, data: list[dict]) -> list[dict]:
        pass

    @abstractmethod
    def load(self, data: list[dict]) -> dict:
        pass

    def notify(self, result: dict):
        """Optional hook — default notification."""
        print(f"  ✅ Done: {result}")


class CSVToDatabase(DataPipeline):
    def extract(self, source: str) -> list[dict]:
        print(f"  📥 Reading CSV from {source}")
        return [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]

    def validate(self, data: list[dict]) -> list[dict]:
        print(f"  🔍 Validating {len(data)} rows")
        return [row for row in data if row.get("name")]

    def transform(self, data: list[dict]) -> list[dict]:
        print("  🔄 Uppercasing names, casting age to int")
        return [{"name": r["name"].upper(), "age": int(r["age"])} for r in data]

    def load(self, data: list[dict]) -> dict:
        print(f"  💾 Inserted {len(data)} rows into database")
        return {"rows_inserted": len(data), "destination": "postgres"}


class APIToS3(DataPipeline):
    def extract(self, source: str) -> list[dict]:
        print(f"  📥 Fetching from API: {source}")
        return [{"id": 1, "value": 42}, {"id": 2, "value": 99}]

    def transform(self, data: list[dict]) -> list[dict]:
        print("  🔄 Enriching records")
        return [{**r, "enriched": True, "processed_at": "2025-01-01"} for r in data]

    def load(self, data: list[dict]) -> dict:
        print(f"  ☁️  Uploaded {len(data)} records to S3")
        return {"records_uploaded": len(data), "destination": "s3://bucket/data/"}

    def notify(self, result: dict):
        print(f"  📢 [Slack] S3 upload complete: {result}")


# Usage
CSVToDatabase().run("data/users.csv")
APIToS3().run("https://api.example.com/metrics")
```

---

## 7. Iterator

**What:** Provides a way to access elements of a collection sequentially without exposing the underlying representation.

**When to use:**
- Custom collection traversal (trees, graphs, linked lists)
- Paginated API results
- Lazy evaluation of large datasets
- Database cursor abstraction
- Streaming file processing (line by line)

```python
from typing import Iterator


class PaginatedAPI:
    """Iterates over paginated API responses transparently."""

    def __init__(self, base_url: str, page_size: int = 10):
        self.base_url = base_url
        self.page_size = page_size

    def __iter__(self) -> Iterator[dict]:
        page = 1
        while True:
            items = self._fetch_page(page)
            if not items:
                break
            yield from items
            page += 1

    def _fetch_page(self, page: int) -> list[dict]:
        """Simulated API call — replace with real requests."""
        all_data = [{"id": i, "name": f"Item {i}"} for i in range(1, 48)]
        start = (page - 1) * self.page_size
        return all_data[start:start + self.page_size]


# Usage — consumer doesn't know about pagination
api = PaginatedAPI("https://api.example.com/items", page_size=10)

print("All items:")
for item in api:
    print(f"  {item['id']:>3}: {item['name']}")

print(f"\nFirst 5 items: {[item['name'] for _, item in zip(range(5), api)]}")
```

### Fibonacci Iterator (lazy infinite sequence)

```python
class Fibonacci:
    def __init__(self, limit: int | None = None):
        self._limit = limit

    def __iter__(self):
        a, b = 0, 1
        count = 0
        while self._limit is None or count < self._limit:
            yield a
            a, b = b, a + b
            count += 1


# First 10 Fibonacci numbers
print(list(Fibonacci(limit=10)))

# Fibonacci numbers under 1000
for n in Fibonacci():
    if n >= 1000:
        break
    print(n, end=" ")
```

---

## 8. Mediator

**What:** Defines an object that encapsulates how a set of objects interact. Promotes loose coupling by preventing objects from referring to each other directly.

**When to use:**
- Chat rooms (users communicate through a central server)
- Air traffic control (planes communicate through tower)
- Form validation (fields interact through a form controller)
- Microservice orchestration
- Event bus / message broker

```python
from datetime import datetime


class ChatRoom:
    """Mediator — all communication goes through the room."""

    def __init__(self, name: str):
        self.name = name
        self._users: dict[str, "ChatUser"] = {}
        self._message_log: list[dict] = []

    def join(self, user: "ChatUser"):
        self._users[user.name] = user
        user.room = self
        self._broadcast(f"{user.name} joined #{self.name}", sender=None)

    def leave(self, user: "ChatUser"):
        if user.name in self._users:
            del self._users[user.name]
            user.room = None
            self._broadcast(f"{user.name} left #{self.name}", sender=None)

    def send(self, message: str, sender: "ChatUser", to: str | None = None):
        entry = {
            "from": sender.name,
            "to": to or "all",
            "message": message,
            "time": datetime.now().strftime("%H:%M"),
        }
        self._message_log.append(entry)

        if to:
            if to in self._users:
                self._users[to].receive(message, sender.name, private=True)
            else:
                sender.receive(f"User '{to}' not found in #{self.name}", "System")
        else:
            self._broadcast(message, sender)

    def _broadcast(self, message: str, sender: "ChatUser | None"):
        sender_name = sender.name if sender else "System"
        for name, user in self._users.items():
            if user != sender:
                user.receive(message, sender_name)

    @property
    def online_users(self) -> list[str]:
        return list(self._users.keys())


class ChatUser:
    def __init__(self, name: str):
        self.name = name
        self.room: ChatRoom | None = None
        self.inbox: list[str] = []

    def send(self, message: str, to: str | None = None):
        if self.room:
            self.room.send(message, self, to)

    def receive(self, message: str, from_user: str, private: bool = False):
        prefix = "[DM]" if private else ""
        formatted = f"  [{self.name}] {prefix} {from_user}: {message}"
        self.inbox.append(formatted)
        print(formatted)


# Usage
room = ChatRoom("general")

alice = ChatUser("Alice")
bob = ChatUser("Bob")
charlie = ChatUser("Charlie")

room.join(alice)
room.join(bob)
room.join(charlie)

alice.send("Hey everyone! 👋")
bob.send("Hi Alice!", to="Alice")   # private DM
charlie.send("Welcome back, Alice!")

print(f"\nOnline: {room.online_users}")

room.leave(bob)
alice.send("Where did Bob go?")
```

---

## Quick Reference — When to Use Which Behavioral Pattern

| Pattern | Choose When... | Real-World Example |
|---|---|---|
| **Observer** | One change should notify many dependents | Event systems, live dashboards, Redux |
| **Strategy** | Algorithm needs to be swappable at runtime | Pricing tiers, auth methods, sorting |
| **Command** | Need to queue, undo, or log operations | Text editors, task queues, transactions |
| **State** | Object behavior changes with its internal state | Order lifecycle, media player, game AI |
| **Chain of Responsibility** | Request handled by one of many possible handlers | Middleware, support escalation, logging |
| **Template Method** | Fixed algorithm skeleton, customizable steps | ETL pipelines, report generators |
| **Iterator** | Sequential access without exposing internals | Paginated APIs, lazy streams, cursors |
| **Mediator** | Many objects interact but shouldn't know each other | Chat rooms, form validation, ATC |

---

## Master Decision Guide — All 19 Patterns (Python)

| Situation | Pattern | Category |
|---|---|---|
| Need exactly one global instance | Singleton | Creational |
| Object type decided at runtime | Factory Method | Creational |
| Families of related objects | Abstract Factory | Creational |
| Complex object, many optional parts | Builder | Creational |
| Cloning cheaper than constructing | Prototype | Creational |
| Incompatible interfaces | Adapter | Structural |
| Add behavior without modifying class | Decorator | Structural |
| Simplify a complex subsystem | Facade | Structural |
| Control access (auth, rate limit, lazy) | Proxy | Structural |
| Part-whole tree hierarchies | Composite | Structural |
| Abstraction and impl vary independently | Bridge | Structural |
| Notify many dependents of a change | Observer | Behavioral |
| Swap algorithms at runtime | Strategy | Behavioral |
| Queue, undo, or log operations | Command | Behavioral |
| Behavior changes with internal state | State | Behavioral |
| Pass request through a handler chain | Chain of Responsibility | Behavioral |
| Fixed algorithm, customizable steps | Template Method | Behavioral |
| Traverse a collection transparently | Iterator | Behavioral |
| Centralize complex interactions | Mediator | Behavioral |
