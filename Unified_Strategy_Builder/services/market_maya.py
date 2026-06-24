"""USB Market Maya client — thin adapter over the shared marketmaya package."""

from marketmaya import MarketMaya
from config import Config

market_maya = MarketMaya(
    module="USB",
    save_url=Config.CREATE_STRATEGY_URL,
)
