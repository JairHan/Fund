import re

import requests


def fetch_sina_data(stocks_list):
    if not stocks_list:
        return []

    codes = [s["code"] for s in stocks_list]
    url = f"http://hq.sinajs.cn/list={','.join(codes)}"
    headers = {"Referer": "http://finance.sina.com.cn/"}

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.encoding = "gbk"
        text = response.text
        results = []

        for stock in stocks_list:
            code = stock["code"]
            match = re.search(f'var hq_str_{code}="(.*?)";', text)
            change = 0.0
            if match:
                data = match.group(1).split(",")
                if code.startswith("hk") and len(data) > 8:
                    change = float(data[8])
                elif len(data) > 3:
                    price, pre_close = float(data[3]), float(data[2])
                    change = (price - pre_close) / pre_close * 100 if pre_close > 0 else 0.0

            results.append({
                "名称": stock["name"],
                "代码": stock["code"],
                "持仓占比(%)": stock["weight"],
                "实时涨跌幅(%)": round(change, 2),
                "贡献度(%)": round(change * (stock["weight"] / 100), 4),
            })

        return results
    except Exception:
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

        tbody_match = re.search(r"<tbody>(.*?)</tbody>", text, re.S)
        latest_text = tbody_match.group(1) if tbody_match else text
        holdings = []
        rows = re.findall(r"<tr>(.*?)</tr>", latest_text, re.S)

        for row in rows:
            name_patt = re.findall(r"<a href=['\"][^'\"]*['\"]>([^<]+)</a>", row)
            weight_match = re.search(
                r"<td class=['\"]tor['\"]>(\d+\.\d+)%</td>", row)
            if len(name_patt) >= 2 and weight_match:
                stock_code = name_patt[0].strip()
                stock_name = name_patt[1].strip()
                weight = float(weight_match.group(1))
                market_code = stock_code
                if market_code.isdigit():
                    if len(market_code) == 5:
                        market_code = "hk" + market_code
                    elif market_code.startswith("6"):
                        market_code = "sh" + market_code
                    elif market_code.startswith("0") or market_code.startswith("3"):
                        market_code = "sz" + market_code
                holdings.append({"name": stock_name, "code": market_code, "weight": weight})

        return fund_name, holdings
    except Exception:
        return "", []


def fetch_real_nav(fund_code):
    url_history = "https://api.fund.eastmoney.com/f10/lsjz"
    headers = {
        "Referer": f"https://fundf10.eastmoney.com/jjjz_{fund_code}.html",
        "User-Agent": "Mozilla/5.0",
    }

    try:
        response = requests.get(
            url_history,
            params={"fundCode": fund_code, "pageIndex": 1, "pageSize": 2},
            headers=headers,
            timeout=3,
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
    except Exception:
        pass

    url_pc = f"http://fund.eastmoney.com/{fund_code}.html"
    try:
        response = requests.get(url_pc, timeout=3)
        response.encoding = "utf-8"
        text = response.text
        date_match = re.search(r"单位净值.*?\(\s*(?:</span>)?\s*([^)<]+)\)", text)
        data_match = re.search(
            r'单位净值.*?<dd class="dataNums">\s*<span[^>]*>([^<]+)</span>\s*<span[^>]*>([^<]+)</span>',
            text,
            re.S,
        )
        if date_match and data_match:
            display_chg = data_match.group(2).strip().replace("%", "")
            return date_match.group(1).strip(), data_match.group(1).strip(), display_chg, display_chg
    except Exception:
        pass

    return "", "-", "0", 0.0
