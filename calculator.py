def calc_profit_from_current_amount(current_amount, change_percent):
    # 支付宝展示的金额是含当天收益后的当前资产，收益需从当前金额反推。
    change_rate = change_percent / 100
    growth_factor = 1 + change_rate
    if growth_factor <= 0:
        return current_amount * change_rate
    return current_amount - (current_amount / growth_factor)
