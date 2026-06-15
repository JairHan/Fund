SIDEBAR_CSS = """
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
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-actions) .favorite-manage-actions + div {
    margin-top: 0.2rem !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-actions) .favorite-manage-actions ~ [data-testid="stElementContainer"]:has(.stButton) {
    padding-bottom: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-actions) .favorite-manage-actions ~ [data-testid="stElementContainer"]:has(.stButton):last-child {
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
@media (prefers-color-scheme: dark) {
    [data-testid="stSidebar"] {
        background: #0b1118;
        border-right: 1px solid #1f2937;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(17, 24, 39, 0.88);
        border-color: #263244;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.35);
    }
    [data-testid="stSidebar"] .sidebar-section-title,
    [data-testid="stSidebar"] label {
        color: #e5e7eb;
    }
    [data-testid="stSidebar"] input {
        background: #0f172a;
        border-color: #334155;
        color: #f8fafc;
    }
    [data-testid="stSidebar"] [data-testid="stNumberInput"] button,
    [data-testid="stSidebar"] [data-testid="stNumberInput"] input {
        background: #0f172a;
        border-color: #334155;
        color: #f8fafc;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: #111827;
        border-color: #334155;
        color: #e5e7eb;
    }
    [data-testid="stSidebar"] .stButton > button *,
    [data-testid="stSidebar"] .stButton > button p {
        color: inherit;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #1f2937;
        border-color: #ff7a7a;
        color: #ff7a7a;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: #ff4b4b;
        border-color: #ff4b4b;
        color: #ffffff;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-actions) .stButton > button[kind="primary"] {
        background: rgba(255, 75, 75, 0.18);
        border-color: #ff4b4b;
        color: #ff8a8a;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-actions) .stButton > button[kind="primary"] *,
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:has(.favorite-actions) .stButton > button[kind="primary"] p {
        color: #ff8a8a;
    }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #94a3b8;
    }
    [data-testid="stSidebar"] [role="slider"] {
        color: #ff4b4b;
    }
}
</style>
"""
