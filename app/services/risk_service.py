MAX_ORDER_VALUE = 50000


def evaluate_risk(price, quantity, order_value):
    if price * quantity > MAX_ORDER_VALUE:
        return (False, "MAX_ORDER_VALUE_EXCEEDED")
    elif (price * quantity) != order_value:
        return (False, "PRICE_MISMATCH_ERROR")

    return (True, None)
