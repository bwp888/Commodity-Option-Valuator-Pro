from models.option import (
    Option,
    OptionType,
    OptionDirection,
)

from models.black_scholes import BlackScholes


def create_call_option():

    return Option(
        symbol="TEST-CALL",
        option_type=OptionType.CALL,
        direction=OptionDirection.LONG,
        spot=100,
        strike=100,
        maturity=1.0,
        rate=0.05,
        volatility=0.2,
    )


def test_black_scholes_create():

    option = create_call_option()

    bs = BlackScholes(option)

    assert bs.option == option



def test_black_scholes_price_positive():

    option = create_call_option()

    bs = BlackScholes(option)

    assert bs.price > 0



def test_black_scholes_price_type():

    option = create_call_option()

    bs = BlackScholes(option)

    assert isinstance(bs.price, float)