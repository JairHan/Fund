import streamlit as st
import pandas as pd
import random

from calculator import calc_profit_from_current_amount
from data_fetch import fetch_fund_holdings, fetch_real_nav, fetch_sina_data
from market import get_market_clock
from storage import (
    add_favorite_fund,
    get_cached_fund_codes,
    load_favorite_funds,
    load_invest_amts,
    move_favorite_to_top,
    normalize_fund_code,
    remove_favorite_fund,
    save_favorite_funds,
    save_invest_amts,
)
from styles import SIDEBAR_CSS

# 设置网页配置
st.set_page_config(page_title="基金净值实时估算器", layout="wide")
st.title("📈 基金净值实时估算工具")

def switch_fund(fund_code):
    st.session_state.fund_code = normalize_fund_code(fund_code)
    st.session_state.top_10 = []
    st.session_state.fund_name = ""
    st.session_state.prev_profit = None
    st.session_state.prev_estimate = None


# --- 状态管理 ---
if 'invest_amts' not in st.session_state:
    st.session_state.invest_amts = load_invest_amts()
if 'fund_code' not in st.session_state:
    st.session_state.fund_code = "001811"
if 'fund_name' not in st.session_state:
    st.session_state.fund_name = ""
if 'top_10' not in st.session_state:
    st.session_state.top_10 = []
if 'prev_profit' not in st.session_state:
    st.session_state.prev_profit = None
if 'prev_estimate' not in st.session_state:
    st.session_state.prev_estimate = None
if 'favorite_funds' not in st.session_state:
    st.session_state.favorite_funds = load_favorite_funds()
market_clock = get_market_clock()

# --- 侧边栏参数控制 (静态部分) ---
with st.sidebar:
    st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="sidebar-section-title">⭐ 关注列表</div>',
                    unsafe_allow_html=True)
        if st.session_state.favorite_funds:
            current_in_favorites = False
            current_favorite_index = None
            st.markdown('<div class="favorite-actions"></div>',
                        unsafe_allow_html=True)
            with st.container(height=245, border=False):
                st.markdown('<div class="favorite-scroll-area"></div>',
                            unsafe_allow_html=True)
                for index, favorite in enumerate(st.session_state.favorite_funds):
                    code = favorite["code"]
                    label_name = favorite.get("name") or "未命名基金"
                    is_current = code == st.session_state.fund_code
                    current_in_favorites = current_in_favorites or is_current
                    if is_current:
                        current_favorite_index = index
                    if st.button(
                        f"{code} {label_name}",
                        key=f"favorite_open_{code}",
                        width="stretch",
                        type="primary" if is_current else "secondary"
                    ):
                        switch_fund(code)
                        st.rerun()

            if current_in_favorites:
                st.markdown('<div class="favorite-manage-actions"></div>',
                            unsafe_allow_html=True)
                if current_favorite_index is not None and current_favorite_index > 0:
                    if st.button("⬆️ 置顶当前", key="favorite_pin_current", width="stretch"):
                        st.session_state.favorite_funds = move_favorite_to_top(
                            st.session_state.favorite_funds,
                            st.session_state.fund_code
                        )
                        st.rerun()

                if st.button("🚫 从关注列表移除当前", key="favorite_remove_current", width="stretch"):
                    st.session_state.favorite_funds = remove_favorite_fund(
                        st.session_state.favorite_funds,
                        st.session_state.fund_code
                    )
                    st.rerun()
        else:
            st.caption("暂无关注基金，可在参数设置中加入当前基金。")

    with st.container(border=True):
        st.markdown('<div class="sidebar-section-title">⚙️ 参数设置</div>',
                    unsafe_allow_html=True)
        fund_code_input = st.text_input(
            "基金代码", value=st.session_state.fund_code, max_chars=6)

        st.markdown('<div class="settings-actions"></div>',
                    unsafe_allow_html=True)
        with st.container():
            if st.button("🎲 换一只基金", width="stretch"):
                random_code = random.choice(get_cached_fund_codes())
                switch_fund(random_code)
                st.rerun()

            if st.button("⭐ 加入关注", width="stretch"):
                add_favorite_fund(
                    st.session_state.favorite_funds,
                    st.session_state.fund_code,
                    st.session_state.fund_name
                )
                st.rerun()

            if st.button("🔄 从天天基金获取持仓", type="primary", width="stretch"):
                st.session_state.fund_name, st.session_state.top_10 = fetch_fund_holdings(
                    st.session_state.fund_code)
                for favorite in st.session_state.favorite_funds:
                    if favorite["code"] == st.session_state.fund_code and st.session_state.fund_name:
                        favorite["name"] = st.session_state.fund_name
                        save_favorite_funds(st.session_state.favorite_funds)
                        break

        if fund_code_input and fund_code_input != st.session_state.fund_code:
            switch_fund(fund_code_input)

        rem_change = st.number_input("剩余仓位预估涨跌 (%)", value=0.0, step=0.1)

    with st.container(border=True):
        st.markdown('<div class="sidebar-section-title">💰 收益试算</div>',
                    unsafe_allow_html=True)
    # 获取当前基金的缓存金额，默认10000
        fund_cache = st.session_state.invest_amts.get(
            st.session_state.fund_code)
        if isinstance(fund_cache, dict):
            current_invest_amt_val = float(fund_cache.get("amount", 10000.0))
            last_date_val = fund_cache.get("last_date", "")
        else:
            current_invest_amt_val = float(
                fund_cache) if fund_cache is not None else 10000.0
            last_date_val = ""

        # 核心修改：使用原生组件，移除闪烁的 HTML 输入框
        invest_amt = st.number_input(
            "输入持仓总金额 (元)", value=current_invest_amt_val, step=1000.0)

        # 当金额发生变化时，保存并写入本地缓存文件
        if invest_amt != current_invest_amt_val:
            st.session_state.invest_amts[st.session_state.fund_code] = {
                "name": st.session_state.fund_name,
                "amount": invest_amt,
                "last_date": last_date_val
            }
            save_invest_amts(st.session_state.invest_amts)
            # 更新目前传递到下方的变量
            current_invest_amt_val = invest_amt

    with st.container(border=True):
        st.markdown('<div class="sidebar-section-title">⏱️ 刷新设置</div>',
                    unsafe_allow_html=True)
        auto_refresh = st.toggle("开启自动刷新", value=True)

        if auto_refresh:
            refresh_interval = st.slider(
                "刷新频率 (秒)", min_value=1.0, max_value=60.0, value=2.0, step=1.0)
        else:
            refresh_interval = 2.0

        auto_refresh_active = auto_refresh and market_clock["is_trading"]
        st.caption(
            f"当前状态: {market_clock['status']}｜{market_clock['detail']}")
        st.caption(f"上海时间: {market_clock['time_text']}")

# --- 主界面显示 ---
if not st.session_state.fund_name and st.session_state.fund_code:
    st.session_state.fund_name, st.session_state.top_10 = fetch_fund_holdings(
        st.session_state.fund_code)

if st.session_state.fund_name:
    st.subheader(
        f"🎯 {st.session_state.fund_name} ({st.session_state.fund_code})")
else:
    st.caption("实时穿透估算中...")

# --- 局部刷新片段 (核心修改) ---
# run_every 参数会由 Streamlit 引擎控制自动刷新频率，不会报错且不会导致焦点丢失


# 通过 run_every 参数实现自动刷新，避免使用 st.experimental_rerun() 导致的焦点丢失问题
@st.fragment(run_every=refresh_interval if auto_refresh_active else None)
def show_realtime_content():
    update_clock = get_market_clock()
    fund_code = st.session_state.fund_code
    if 'last_realtime_data' not in st.session_state:
        st.session_state.last_realtime_data = {}
    if 'last_realtime_update_at' not in st.session_state:
        st.session_state.last_realtime_update_at = {}

    cached_data_list = st.session_state.last_realtime_data.get(fund_code)
    should_fetch_realtime = (
        update_clock["is_trading"] or
        not cached_data_list or
        not auto_refresh
    )
    if should_fetch_realtime:
        data_list = fetch_sina_data(st.session_state.top_10)
        if data_list:
            st.session_state.last_realtime_data[fund_code] = data_list
            st.session_state.last_realtime_update_at[fund_code] = update_clock["time_text"]
    else:
        data_list = cached_data_list

    if data_list:
        df = pd.DataFrame(data_list)
        top_total_weight = df["持仓占比(%)"].sum()
        top_contribution = df["贡献度(%)"].sum()
        rem_weight = 100.0 - top_total_weight
        rem_contribution = rem_change * (rem_weight / 100)
        final_estimate = top_contribution + rem_contribution

        # 实时收益卡片样式
        profit = invest_amt * (final_estimate / 100)
        color = "#ff4b4b" if profit > 0 else "#09ab3b"
        symbol = "📈 +" if profit > 0 else "📉 "

        # 检查数值变化决定是否闪烁
        flash_css = ""
        prev_profit = st.session_state.prev_profit
        if prev_profit is not None and abs(profit - prev_profit) > 0.001:
            if profit > prev_profit:
                flash_css = "animation: flash-red-bg 2.5s ease-out;"
            else:
                flash_css = "animation: flash-green-bg 2.5s ease-out;"

        st.session_state.prev_profit = profit
        st.session_state.prev_estimate = final_estimate

        real_date, real_nav, real_chg, real_chg_for_calc = fetch_real_nav(
            st.session_state.fund_code)

        try:
            real_chg_float = float(real_chg)
        except:
            real_chg_float = 0.0
        try:
            real_chg_calc_float = float(real_chg_for_calc)
        except:
            real_chg_calc_float = real_chg_float

        # --- 自动复利滚动本金逻辑 ---
        if real_date and real_date != "-":
            # 读取当前这只基金缓存中的记录状态
            fund_c = st.session_state.invest_amts.get(
                st.session_state.fund_code)
            if isinstance(fund_c, dict):
                saved_date = fund_c.get("last_date", "")
                saved_amt = float(fund_c.get("amount", 10000.0))
            else:
                saved_date = ""
                saved_amt = float(fund_c) if fund_c is not None else 10000.0

            if not saved_date:
                # 第一次获取到真实净值日期，绑定为初始基准，不做本金增加
                st.session_state.invest_amts[st.session_state.fund_code] = {
                    "name": st.session_state.fund_name,
                    "amount": invest_amt,
                    "last_date": real_date
                }
                save_invest_amts(st.session_state.invest_amts)
            elif saved_date != real_date:
                # 发现最新净值日期变更新了，执行复利计算：本金 = 本金 + 昨天的实际收益
                new_amt = round(saved_amt * (1 + real_chg_calc_float / 100), 2)
                st.session_state.invest_amts[st.session_state.fund_code] = {
                    "name": st.session_state.fund_name,
                    "amount": new_amt,
                    "last_date": real_date
                }
                save_invest_amts(st.session_state.invest_amts)
                st.rerun()  # 通知主界面重新渲染，刷新左侧输入框数值

        yesterday_profit = calc_profit_from_current_amount(
            invest_amt, real_chg_calc_float)
        y_color = "#ff4b4b" if yesterday_profit > 0 else (
            "#09ab3b" if yesterday_profit < 0 else "gray")
        y_symbol = "📈 +" if yesterday_profit > 0 else (
            "📉 " if yesterday_profit < 0 else "")

        # --- 记录实时走势数据 ---
        current_time = update_clock["now"].strftime('%H:%M:%S')
        update_time_text = st.session_state.last_realtime_update_at.get(
            fund_code, update_clock["time_text"])
        if 'trend_records' not in st.session_state:
            st.session_state.trend_records = {}

        # 换基金时初始化记录
        if st.session_state.fund_code not in st.session_state.trend_records:
            st.session_state.trend_records[st.session_state.fund_code] = []

        trend_list = [
            row for row in st.session_state.trend_records[fund_code]
            if isinstance(row, dict) and "时间" in row and "估值(%)" in row
        ]
        should_record_point = (
            not trend_list or
            (should_fetch_realtime and trend_list[-1].get('时间') != current_time)
        )

        # 只在有新的时间变动或者数值产生时追加，避免一秒内重复录入
        if should_record_point:
            trend_list.append({'时间': current_time, '估值(%)': final_estimate})
            # 保留最近的1000个点，防止随着时间推移数据过大拖慢性能
            if len(trend_list) > 1000:
                trend_list = trend_list[-1000:]
        st.session_state.trend_records[fund_code] = trend_list

        df_trend = pd.DataFrame(trend_list).set_index('时间')

        # --- 开启左右两侧分栏显示 ---
        left_col, right_col = st.columns([1.4, 1], gap="medium")

        with left_col:
            # 使用 Markdown 渲染收益显示区，解决闪烁问题，加入数值变动时的颜色背景闪烁提示
            st.markdown(f"""
                <style>
                @keyframes flash-red-bg {{ 0% {{ background-color: rgba(255, 75, 75, 0.4); }} 100% {{ background-color: rgba(128,128,128,0.05); }} }}
                @keyframes flash-green-bg {{ 0% {{ background-color: rgba(9, 171, 59, 0.4); }} 100% {{ background-color: rgba(128,128,128,0.05); }} }}
                .profit-card {{
                    background: rgba(128,128,128,0.05);
                    padding: 20px;
                    border-radius: 12px;
                    border-left: 6px solid {color};
                    margin-bottom: 20px;
                    transition: background-color 0.5s;
                    {flash_css}
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .profit-section {{
                    flex: 1;
                }}
                .divider {{
                    width: 1px;
                    background-color: rgba(128,128,128,0.2);
                    height: 80px;
                    margin: 0 30px;
                }}
                </style>
                <div class="profit-card">
                    <div class="profit-section">
                        <div style="font-size: 14px; color: gray;">今日估算收益</div>
                        <div style="font-size: 36px; font-weight: bold; color: {color}; margin: 5px 0;">¥ {abs(profit):.2f}</div>
                        <div style="font-size: 16px; color: {color}; font-weight: 600;">{symbol}{profit:.2f} 元 (当日估值 {final_estimate:.2f}%)</div>
                    </div>
                    <div class="divider"></div>
                    <div class="profit-section">
                        <div style="font-size: 14px; color: gray;">最新实际收益 ({real_date})</div>
                        <div style="font-size: 36px; font-weight: bold; color: {y_color}; margin: 5px 0;">¥ {abs(yesterday_profit):.2f}</div>
                        <div style="font-size: 16px; color: {y_color}; font-weight: 600;">{y_symbol}{yesterday_profit:.2f} 元 (净值涨跌 {real_chg_float:.2f}%)</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            c1.metric("估算总涨跌", f"{final_estimate:.2f}%",
                      delta=f"{final_estimate:.2f}%")
            c2.metric(f"共{len(df)}只股票/覆盖仓位", f"{top_total_weight:.2f}%")
            c3.metric(f"最新净值({real_date})", real_nav, delta=f"{real_chg}%")

            st.subheader("详细持仓变动")
            # 添加持仓排名列
            df.insert(0, "持仓排名", range(1, len(df) + 1))

            st.dataframe(
                df.style.format(
                    {'持仓占比(%)': '{:.2f}', '实时涨跌幅(%)': '{:.2f}', '贡献度(%)': '{:.4f}'})
                .set_properties(subset=['持仓排名'], **{'text-align': 'left'})
                .map(lambda x: f"color: {'red' if x > 0 else 'green'}", subset=['实时涨跌幅(%)', '贡献度(%)']),
                width="stretch",
                hide_index=True,
                column_config={
                    "持仓排名": st.column_config.NumberColumn(
                        "持仓排名", format="%d")
                }
            )
            refresh_status = "运行中" if auto_refresh and update_clock["is_trading"] else "已暂停"
            st.caption(
                f"行情更新时间: {update_time_text}｜自动刷新: {refresh_status}｜市场状态: {update_clock['status']}")

        with right_col:
            st.subheader("📈 实时估值走势")

            import altair as alt
            # 将索引重置以便 Altair 正确解析时间和估值
            df_trend_alt = df_trend.reset_index()
            line_color = "#ff4b4b" if final_estimate > 0 else "#09ab3b"

            # 使用 Altair 自定义图表设置 Y 轴小数点保留2位数字，并且不从 0 开始
            chart = alt.Chart(df_trend_alt).mark_line(color=line_color).encode(
                x=alt.X('时间', title='', axis=alt.Axis(labelOverlap=True)),
                y=alt.Y('估值(%)', title='', scale=alt.Scale(
                    zero=False), axis=alt.Axis(format='.2f'))
            ).interactive()

            st.altair_chart(chart, width="stretch")

            st.caption(
                f"说明: 走势只记录您当前打开网页并开启刷新期间 ({df_trend.index[0]} 起) 的走向，切换基金或关闭重新打开都会重置。")

    else:
        pause_text = "" if auto_refresh and update_clock["is_trading"] else f" 当前市场状态: {update_clock['status']}，自动刷新已暂停。"
        st.info(f"数据加载中或开盘时间内未获取到行情...{pause_text}")


# 执行局部刷新函数
show_realtime_content()
