from models.option import Option, OptionType, OptionDirection
from models.black_scholes import BlackScholes


def test_option_create():

    option = Option(
        option_type=OptionType.CALL,
        direction=OptionDirection.LONG,
        spot=100,
        strike=100,
        maturity=1.0,
        rate=0.05,
        volatility=0.2,
    )

    assert option.spot == 100
    assert option.strike == 100
    assert option.is_call is True



def test_black_scholes_price():

    option = Option(
        option_type=OptionType.CALL,
        direction=OptionDirection.LONG,
        spot=100,
        strike=100,
        maturity=1.0,
        rate=0.05,
        volatility=0.2,
    )

    bs = BlackScholes(option)

    price = bs.price

    assert price > 0



def test_option_dict():

    option = Option(
        symbol="TEST-CALL",
        option_type=OptionType.CALL,
        direction=OptionDirection.LONG,
        spot=100,
        strike=100,
        maturity=1.0,
        rate=0.05,
        volatility=0.2,
    )

    data = option.to_dict()

    assert data["symbol"] == "TEST-CALL"
    assert data["spot"] == 100
    assert data["strike"] == 100