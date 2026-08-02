from models.option import Option, OptionType
from models.black_scholes import BlackScholes
from models.greeks import Greeks


option = Option(
    option_type=OptionType.CALL,
    spot=100,
    strike=100,
    maturity=1,
    rate=0.05,
    volatility=0.2,
)

bs = BlackScholes(option)

greeks = Greeks(bs)

print(greeks.summary())