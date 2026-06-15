import json
import os


DEFAULT_FUND_CODES = [
    "001811", "161725", "512690", "005827", "163406",
    "003095", "005911", "001838", "161022", "519670"
]


def normalize_fund_code(fund_code):
    code = str(fund_code).strip()
    if not code:
        return ""
    return code.zfill(6) if code.isdigit() and len(code) <= 6 else code


def read_json_file(file_path, fallback):
    if not os.path.exists(file_path):
        return fallback

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback


def write_json_file(file_path, data, indent=None):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
    except Exception:
        pass


def get_cached_fund_codes():
    codes = read_json_file("fund_codes_cache.json", DEFAULT_FUND_CODES)
    if codes and isinstance(codes, list):
        return codes
    return DEFAULT_FUND_CODES


def load_invest_amts():
    return read_json_file("invest_cache.json", {})


def save_invest_amts(data):
    write_json_file("invest_cache.json", data)


def load_favorite_funds():
    raw_funds = read_json_file("favorite_funds.json", [])
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
    write_json_file("favorite_funds.json", favorites, indent=2)


def add_favorite_fund(favorites, fund_code, fund_name=""):
    code = normalize_fund_code(fund_code)
    if not code:
        return False

    name = str(fund_name or "").strip()
    for favorite in favorites:
        if favorite["code"] == code:
            if name and not favorite.get("name"):
                favorite["name"] = name
                save_favorite_funds(favorites)
            return False

    favorites.append({"code": code, "name": name})
    save_favorite_funds(favorites)
    return True


def remove_favorite_fund(favorites, fund_code):
    code = normalize_fund_code(fund_code)
    updated_favorites = [
        favorite for favorite in favorites
        if favorite["code"] != code
    ]
    save_favorite_funds(updated_favorites)
    return updated_favorites


def move_favorite_to_top(favorites, fund_code):
    code = normalize_fund_code(fund_code)
    if not code:
        return favorites

    selected_favorite = None
    remaining_favorites = []
    for favorite in favorites:
        if favorite["code"] == code and selected_favorite is None:
            selected_favorite = favorite
        else:
            remaining_favorites.append(favorite)

    if selected_favorite is None:
        return favorites

    updated_favorites = [selected_favorite, *remaining_favorites]
    save_favorite_funds(updated_favorites)
    return updated_favorites
