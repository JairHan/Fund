import streamlit as st
import streamlit.components.v1 as components
import requests
import re
import pandas as pd
import random
import os
import json
import time

# 设置网页配置
st.set_page_config(page_title="基金净值实时估算器", layout="wide")
st.title("📈 基金净值实时估算工具")

# --- 核心函数库 (保持不变) ---


@st.cache_data
def get_cached_fund_codes():
    file_path = "fund_codes_cache.json"
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                codes = json.load(f)
                if codes and isinstance(codes, list):
                    return codes
        except:
            pass
    return ["001811", "161725", "512690", "005827", "163406", "003095", "005911", "001838", "161022", "519670"]


# 投资金额的本地缓存管理，避免每次刷新都丢失输入的金额数据
def load_invest_amts():
    if os.path.exists("invest_cache.json"):
        try:
            with open("invest_cache.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}


# 保存投资金额到本地缓存文件，确保用户输入的金额在页面刷新后仍然保留
def save_invest_amts(data):
    try:
        with open("invest_cache.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except:
        pass


def normalize_fund_code(fund_code):
    code = str(fund_code).strip()
    if not code:
        return ""
    return code.zfill(6) if code.isdigit() and len(code) <= 6 else code


def load_favorite_funds():
    file_path = "favorite_funds.json"
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_funds = json.load(f)
    except:
        return []

    favorites = []
    seen_codes = set()
    for item in raw_funds if isinstance(raw_funds, list) else []:
        if isinstance(item, dict):
            code = normalize_fund_code(item.get("code", ""))
            name = str(item.get("name", "")).strip()
        else:
            code = normalize_fund_code(item)
            name = ""

        if code and code not in seen_codes:
            favorites.append({"code": code, "name": name})
            seen_codes.add(code)
    return favorites


def save_favorite_funds(favorites):
    try:
        with open("favorite_funds.json", "w", encoding="utf-8") as f:
            json.dump(favorites, f, ensure_ascii=False, indent=2)
    except:
        pass


def add_favorite_fund(fund_code, fund_name=""):
    code = normalize_fund_code(fund_code)
    if not code:
        return False

    name = str(fund_name or "").strip()
    for favorite in st.session_state.favorite_funds:
        if favorite["code"] == code:
            if name and not favorite.get("name"):
                favorite["name"] = name
                save_favorite_funds(st.session_state.favorite_funds)
            return False

    st.session_state.favorite_funds.append({"code": code, "name": name})
    save_favorite_funds(st.session_state.favorite_funds)
    return True


def remove_favorite_fund(fund_code):
    code = normalize_fund_code(fund_code)
    st.session_state.favorite_funds = [
        favorite for favorite in st.session_state.favorite_funds
        if favorite["code"] != code
    ]
    save_favorite_funds(st.session_state.favorite_funds)


def switch_fund(fund_code):
    st.session_state.fund_code = normalize_fund_code(fund_code)
    st.session_state.top_10 = []
    st.session_state.fund_name = ""
    st.session_state.prev_profit = None
    st.session_state.prev_estimate = None


def fetch_sina_data(stocks_list):
    if not stocks_list:
        return []
    codes = [s["code"] for s in stocks_list]
    url = f"http://hq.sinajs.cn/list={','.join(codes)}"
    headers = {"Referer": "http://finance.sina.com.cn/"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.encoding = 'gbk'
        text = response.text
        results = []
        for stock in stocks_list:
            code = stock["code"]
            match = re.search(f'var hq_str_{code}="(.*?)";', text)
            change = 0.0
            if match:
                data = match.group(1).split(',')
                if code.startswith('hk') and len(data) > 8:
                    change = float(data[8])
                elif len(data) > 3:
                    price, pre_close = float(data[3]), float(data[2])
                    change = (price - pre_close) / pre_close * \
                        100 if pre_close > 0 else 0.0
            results.append({
                "名称": stock["name"], "代码": stock["code"], "持仓占比(%)": stock["weight"],
                "实时涨跌幅(%)": round(change, 2), "贡献度(%)": round(change * (stock["weight"] / 100), 4)
            })
        return results
    except:
        return []


def fetch_fund_holdings(fund_code):
    url = f"http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={fund_code}&topline=100&year=&month="
    headers = {"Referer": f"http://fundf10.eastmoney.com/ccmx_{fund_code}.html"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        text = response.text
        fund_name = ""
        name_match = re.search(
            r"<label class=['\"]left['\"]><a title=['\"]([^'\"]+)['\"]", text)
        if name_match:
            fund_name = name_match.group(1)
        tbody_match = re.search(r'<tbody>(.*?)</tbody>', text, re.S)
        latest_text = tbody_match.group(1) if tbody_match else text
        holdings = []
        rows = re.findall(r'<tr>(.*?)</tr>', latest_text, re.S)
        for row in rows:
            name_patt = re.findall(
                r"<a href=['\"][^'\"]*['\"]>([^<]+)</a>", row)
            weight_match = re.search(
                r"<td class=['\"]tor['\"]>(\d+\.\d+)%</td>", row)
            if len(name_patt) >= 2 and weight_match:
                stock_code, stock_name, weight = name_patt[0].strip(
                ), name_patt[1].strip(), float(weight_match.group(1))
                market_code = stock_code
                if market_code.isdigit():
                    if len(market_code) == 5:
                        market_code = "hk" + market_code
                    elif market_code.startswith("6"):
                        market_code = "sh" + market_code
                    elif market_code.startswith("0") or market_code.startswith("3"):
                        market_code = "sz" + market_code
                holdings.append(
                    {"name": stock_name, "code": market_code, "weight": weight})
        return fund_name, holdings
    except:
        return "", []


def fetch_real_nav(fund_code):
    url_history = "https://api.fund.eastmoney.com/f10/lsjz"
    headers = {
        "Referer": f"https://fundf10.eastmoney.com/jjjz_{fund_code}.html",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(
            url_history,
            params={"fundCode": fund_code, "pageIndex": 1, "pageSize": 2},
            headers=headers,
            timeout=3
        )
        data = response.json()
        rows = data.get("Data", {}).get("LSJZList", [])
        if rows:
            latest = rows[0]
            real_date = latest.get("FSRQ", "")
            real_nav = latest.get("DWJZ", "-")
            display_chg = str(latest.get("JZZZL", "0")).replace("%", "")
            calc_chg = display_chg
            if len(rows) >= 2:
                latest_nav = float(latest.get("DWJZ", 0))
                prev_nav = float(rows[1].get("DWJZ", 0))
                if prev_nav > 0:
                    calc_chg = (latest_nav - prev_nav) / prev_nav * 100
            return real_date, real_nav, display_chg, calc_chg
    except:
        pass

    url_pc = f"http://fund.eastmoney.com/{fund_code}.html"
    try:
        response = requests.get(url_pc, timeout=3)
        response.encoding = 'utf-8'
        text = response.text
        date_match = re.search(r'单位净值.*?\(\s*(?:</span>)?\s*([^)<]+)\)', text)
        data_match = re.search(
            r'单位净值.*?<dd class="dataNums">\s*<span[^>]*>([^<]+)</span>\s*<span[^>]*>([^<]+)</span>', text, re.S)
        if date_match and data_match:
            display_chg = data_match.group(2).strip().replace('%', '')
            return date_match.group(1).strip(), data_match.group(1).strip(), display_chg, display_chg
    except:
        pass
    return "", "-", "0", 0.0


def calc_profit_from_current_amount(current_amount, change_percent):
    # 支付宝展示的金额是含当天收益后的当前资产，收益需从当前金额反推。
    change_rate = change_percent / 100
    growth_factor = 1 + change_rate
    if growth_factor <= 0:
        return current_amount * change_rate
    return current_amount - (current_amount / growth_factor)


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

# --- 侧边栏参数控制 (静态部分) ---
with st.sidebar:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            background: #f3f6fb;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0.65rem;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid #dce4ee;
            border-radius: 14px;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }
        [data-testid="stSidebar"] .sidebar-section-title {
            display: flex;
            align-items: center;
            gap: 0.45rem;
            color: #172033;
            font-size: 1.05rem;
            font-weight: 800;
            line-height: 1.2;
            margin: 0 0 0.45rem;
        }
        [data-testid="stSidebar"] label {
            color: #344054;
            font-size: 0.86rem;
            font-weight: 600;
        }
        [data-testid="stSidebar"] input {
            border-radius: 10px;
            border-color: #e1e7ef;
        }
        [data-testid="stSidebar"] .stButton {
            margin-bottom: 0 !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.settings-actions) [data-testid="stElementContainer"]:has(.stButton) {
            margin: 0 !important;
            padding: 0 !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.settings-actions) [data-testid="stElementContainer"]:has(.stButton) + [data-testid="stElementContainer"]:has(.stButton) {
            margin-top: -0.44rem !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.settings-actions) .stButton > button {
            min-height: 2.05rem;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-actions) [data-testid="stVerticalBlock"] {
            gap: 0.45rem;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-actions) [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-scroll-area) {
            background: transparent;
            border: 0;
            box-shadow: none;
            padding: 0;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-actions) [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-scroll-area) [data-testid="stVerticalBlock"] {
            gap: 0.45rem;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-actions) [data-testid="stElementContainer"]:has(.stButton) {
            margin: 0 !important;
            padding: 0 0.18rem !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-actions) .stButton > button {
            min-height: 2.15rem;
            white-space: normal;
            word-break: break-word;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-actions) .stButton > button[kind="primary"] {
            background: #fff1f1;
            border-color: #ff4b4b;
            color: #d92d20;
            box-shadow: inset 0 0 0 1px rgba(255, 75, 75, 0.14);
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-actions) .stButton > button[kind="primary"] *,
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-actions) .stButton > button[kind="primary"] p {
            color: #d92d20;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-actions) .favorite-remove-action + div {
            margin-top: 0.2rem !important;
            padding-bottom: 0.72rem !important;
        }
        [data-testid="stSidebar"] .stButton > button {
            min-height: 2.15rem;
            border-radius: 999px;
            border-color: #d0d8e4;
            background: #ffffff;
            color: #1f2937;
            font-size: 0.875rem;
            font-weight: 600;
            padding-top: 0.25rem;
            padding-bottom: 0.25rem;
            line-height: 1.2;
        }
        [data-testid="stSidebar"] .stButton > button *,
        [data-testid="stSidebar"] .stButton > button p {
            font-size: 0.875rem;
            line-height: 1.2;
            font-weight: inherit;
            margin: 0;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            border-color: #ff7a7a;
            color: #d92d20;
            background: #fff8f8;
        }
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: #ff4b4b;
            border-color: #ff4b4b;
            color: #ffffff;
            font-weight: 700;
            box-shadow: 0 1px 2px rgba(255, 75, 75, 0.24);
        }
        [data-testid="stSidebar"] .stButton > button[kind="primary"] *,
        [data-testid="stSidebar"] .stButton > button[kind="primary"] p {
            color: #ffffff;
            font-weight: 700;
        }
        [data-testid="stSidebar"] .favorite-list {
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
            margin-top: 0.15rem;
            overflow: hidden;
            padding: 0.08rem 0.18rem 0.38rem;
            box-sizing: border-box;
        }
        [data-testid="stSidebar"] .favorite-item,
        [data-testid="stSidebar"] .favorite-remove {
            align-items: center;
            border: 1px solid #d0d8e4;
            border-radius: 999px;
            box-sizing: border-box;
            display: grid;
            font-size: 0.875rem;
            font-weight: 600;
            line-height: 1.15;
            min-height: 2.15rem;
            padding: 0.42rem 0.8rem 0.34rem;
            place-items: center;
            text-align: center;
            text-decoration: none !important;
            transition: all 0.16s ease;
            white-space: normal;
            word-break: break-word;
            width: calc(100% - 0.08rem);
        }
        [data-testid="stSidebar"] .favorite-item {
            background: #ffffff;
            color: #243044 !important;
            margin: 0 auto;
        }
        [data-testid="stSidebar"] .favorite-item:hover {
            background: #fff8f8;
            border-color: #ffb0b0;
            color: #d92d20 !important;
        }
        [data-testid="stSidebar"] .favorite-item.active {
            background: #fff1f1;
            border-color: #ff4b4b;
            color: #d92d20 !important;
            font-weight: 700;
            box-shadow: inset 0 0 0 1px rgba(255, 75, 75, 0.14);
        }
        [data-testid="stSidebar"] .favorite-remove {
            background: #ffffff;
            border-color: #ffc9c9;
            color: #d92d20 !important;
            margin: 0.2rem auto 0;
        }
        [data-testid="stSidebar"] .favorite-remove:hover {
            background: #fff1f1;
            border-color: #ff8a8a;
            color: #b42318 !important;
        }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            margin-top: -0.15rem;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="sidebar-section-title">⭐ 关注列表</div>',
                    unsafe_allow_html=True)
        if st.session_state.favorite_funds:
            current_in_favorites = False
            st.markdown('<div class="favorite-actions"></div>',
                        unsafe_allow_html=True)
            with st.container(height=245, border=False):
                st.markdown('<div class="favorite-scroll-area"></div>',
                            unsafe_allow_html=True)
                for favorite in st.session_state.favorite_funds:
                    code = favorite["code"]
                    label_name = favorite.get("name") or "未命名基金"
                    is_current = code == st.session_state.fund_code
                    current_in_favorites = current_in_favorites or is_current
                    if st.button(
                        f"{code} {label_name}",
                        key=f"favorite_open_{code}",
                        width="stretch",
                        type="primary" if is_current else "secondary"
                    ):
                        switch_fund(code)
                        st.rerun()

            if current_in_favorites:
                st.markdown('<div class="favorite-remove-action"></div>',
                            unsafe_allow_html=True)
                if st.button("🚫 从关注列表移除当前", key="favorite_remove_current", width="stretch"):
                    remove_favorite_fund(st.session_state.fund_code)
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
                add_favorite_fund(st.session_state.fund_code,
                                  st.session_state.fund_name)
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

        st.caption("开启后系统将自动更新实时行情，无需手动操作。")

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
@st.fragment(run_every=refresh_interval if auto_refresh else None)
def show_realtime_content():
    data_list = fetch_sina_data(st.session_state.top_10)

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
        current_time = time.strftime('%H:%M:%S')
        if 'trend_records' not in st.session_state:
            st.session_state.trend_records = {}

        # 换基金时初始化记录
        if st.session_state.fund_code not in st.session_state.trend_records:
            st.session_state.trend_records[st.session_state.fund_code] = []

        trend_list = st.session_state.trend_records[st.session_state.fund_code]
        # 只在有新的时间变动或者数值产生时追加，避免一秒内重复录入
        if not trend_list or trend_list[-1]['时间'] != current_time:
            trend_list.append({'时间': current_time, '估值(%)': final_estimate})
            # 保留最近的1000个点，防止随着时间推移数据过大拖慢性能
            if len(trend_list) > 1000:
                trend_list = trend_list[-1000:]
            st.session_state.trend_records[st.session_state.fund_code] = trend_list

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
            # 转换持仓排名为字符串形式以便更好地控制对齐
            df["持仓排名"] = df["持仓排名"].astype(str)

            st.dataframe(
                df.style.format(
                    {'持仓占比(%)': '{:.2f}', '实时涨跌幅(%)': '{:.2f}', '贡献度(%)': '{:.4f}'})
                .set_properties(subset=['持仓排名'], **{'text-align': 'left'})
                .map(lambda x: f"color: {'red' if x > 0 else 'green'}", subset=['实时涨跌幅(%)', '贡献度(%)']),
                width="stretch", hide_index=True
            )
            st.caption(f"最后更新时间: {current_time}")

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
        st.info("数据加载中或开盘时间内未获取到行情...")


# 执行局部刷新函数
show_realtime_content()
