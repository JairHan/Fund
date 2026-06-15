# 基金净值实时估算工具

一个基于 Streamlit 的基金净值实时估算页面。输入基金代码后，程序会从天天基金/东方财富获取基金持仓和净值数据，并结合新浪实时行情估算当日涨跌、收益金额和实时走势。

## 功能

- 输入基金代码查看基金名称、持仓和净值信息
- 估算当日基金涨跌幅和今日收益
- 按支付宝口径计算最新实际收益
- 支持关注基金列表，方便快速切换常看基金
- 支持将常看基金置顶，调整关注列表展示顺序
- 支持本地保存持仓金额和关注基金
- 支持自动刷新和实时估值走势

## 本地运行

建议使用 Python 3.10 或更新版本。

```bash
pip install streamlit requests pandas altair
streamlit run index.py
```

启动后访问：

```text
http://localhost:8501
```

## 项目结构

- `index.py`：Streamlit 页面、交互和状态管理
- `data_fetch.py`：东方财富、天天基金、新浪行情数据获取
- `storage.py`：本地 JSON 缓存读写、基金代码规范化、关注基金管理
- `calculator.py`：收益金额等核心计算
- `market.py`：A 股交易时间判断和刷新状态
- `styles.py`：侧边栏样式和深色模式适配

## 本地数据文件

应用会在运行目录下生成一些本地缓存文件：

- `invest_cache.json`：各基金持仓金额和净值日期
- `favorite_funds.json`：关注基金列表
- `watchlist_cache.json`：旧版关注列表缓存
- `fund_codes_cache.json`：随机基金代码缓存

这些文件属于个人本地数据，默认不提交到 Git。

## 部署提示

如果部署到宝塔面板或 Nginx 反向代理后页面长时间停在加载骨架屏，请优先检查：

- 服务器访问东方财富、天天基金、新浪行情接口是否很慢
- Streamlit 的 WebSocket 反向代理是否配置正确
- 自动刷新频率是否过低，导致服务器频繁请求外部行情接口

Nginx 反向代理 Streamlit 时通常需要支持 WebSocket：

```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
proxy_set_header Host $host;
```

## 说明

页面展示的估算值仅用于个人参考，不构成投资建议。外部行情和基金数据来自第三方网站，可能存在延迟、限流或接口变更。
