from __future__ import annotations

import csv
import copy
import io
import json
import math
import os
import re
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
STATE_FILE = DATA_DIR / "census.json"
RECORDS_PAGE_SIZE = 8
SUPABASE_BRANDS_TABLE = "census_brands"
SUPABASE_ITEMS_TABLE = "census_items"

def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --census-bg: #f7f8fa;
            --census-panel: #ffffff;
            --census-panel-soft: #fbfcfd;
            --census-line: #d9dee7;
            --census-line-strong: #c5ccd8;
            --census-ink: #172033;
            --census-muted: #667085;
            --census-accent: #e5484d;
            --census-accent-dark: #c92f36;
            --census-teal: #0f766e;
            --census-shadow: 0 12px 28px rgba(23, 32, 51, 0.08);
        }

        .stApp {
            background:
                linear-gradient(180deg, #ffffff 0%, var(--census-bg) 220px),
                var(--census-bg);
            color: var(--census-ink);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 2.25rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3 {
            color: var(--census-ink);
            letter-spacing: 0;
        }

        h1 {
            font-size: clamp(2rem, 3vw, 3rem);
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        h2, [data-testid="stHeadingWithActionElements"] h2 {
            font-size: 1.65rem;
            font-weight: 760;
            margin-top: 1.35rem;
            padding-top: 0.35rem;
        }

        h3 {
            font-size: 1.18rem;
            font-weight: 720;
        }

        [data-testid="stCaptionContainer"] {
            color: var(--census-muted);
        }

        [data-testid="stMarkdownContainer"] p {
            line-height: 1.65;
        }

        div[data-testid="stSegmentedControl"],
        div[data-testid="stRadio"] {
            margin: 1.15rem 0 1.35rem;
        }

        div[data-testid="stSegmentedControl"] [role="radiogroup"],
        div[data-testid="stRadio"] > div {
            gap: 0.45rem;
            padding: 0.35rem;
            width: fit-content;
            max-width: 100%;
            border: 1px solid var(--census-line);
            border-radius: 8px;
            background: var(--census-panel);
            box-shadow: 0 8px 20px rgba(23, 32, 51, 0.06);
        }

        div[data-testid="stSegmentedControl"] [role="radiogroup"] label,
        div[data-testid="stRadio"] label {
            min-height: 2.15rem;
            padding: 0.35rem 0.7rem;
            border-radius: 6px;
            color: var(--census-muted);
            transition: background 120ms ease, color 120ms ease;
        }

        div[data-testid="stSegmentedControl"] [role="radiogroup"] label:has(input:checked),
        div[data-testid="stRadio"] label:has(input:checked) {
            background: #fff1f1;
            color: var(--census-accent-dark);
            font-weight: 700;
        }

        div[data-testid="stForm"],
        div[data-testid="stExpander"],
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--census-line) !important;
            border-radius: 8px !important;
            background: var(--census-panel);
            box-shadow: var(--census-shadow);
        }

        div[data-testid="stForm"] {
            padding: 1.1rem 1.2rem 1.2rem;
        }

        div[data-testid="stExpander"] {
            overflow: hidden;
        }

        label[data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] p {
            color: #344054;
            font-size: 0.9rem;
            font-weight: 700;
            margin-bottom: 0.3rem;
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        textarea {
            border-color: var(--census-line-strong) !important;
            border-radius: 8px !important;
            background-color: var(--census-panel-soft) !important;
            box-shadow: inset 0 1px 0 rgba(23, 32, 51, 0.03);
            transition: border-color 120ms ease, box-shadow 120ms ease, background 120ms ease;
        }

        div[data-baseweb="input"]:focus-within > div,
        div[data-baseweb="select"]:focus-within > div,
        textarea:focus {
            border-color: var(--census-teal) !important;
            background-color: #ffffff !important;
            box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12) !important;
        }

        input,
        textarea,
        div[data-baseweb="select"] span {
            color: var(--census-ink) !important;
            font-size: 0.98rem !important;
        }

        div[data-testid="stButton"] button,
        div[data-testid="stFormSubmitButton"] button,
        div[data-testid="stDownloadButton"] button {
            min-height: 2.55rem;
            border-radius: 8px;
            border: 1px solid var(--census-line-strong);
            background: #ffffff;
            color: var(--census-ink);
            font-weight: 720;
            box-shadow: 0 4px 10px rgba(23, 32, 51, 0.06);
            transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease;
        }

        div[data-testid="stButton"] button:hover,
        div[data-testid="stFormSubmitButton"] button:hover,
        div[data-testid="stDownloadButton"] button:hover {
            border-color: var(--census-accent);
            color: var(--census-accent-dark);
            box-shadow: 0 8px 18px rgba(229, 72, 77, 0.14);
            transform: translateY(-1px);
        }

        div[data-testid="stButton"] button[kind="primary"],
        div[data-testid="stFormSubmitButton"] button[kind="primary"] {
            border-color: var(--census-accent);
            background: var(--census-accent);
            color: #ffffff;
        }

        div[data-testid="stButton"] button:disabled,
        div[data-testid="stFormSubmitButton"] button:disabled {
            transform: none;
            box-shadow: none;
            opacity: 0.62;
        }

        [data-testid="stAlert"] {
            border-radius: 8px;
            border: 1px solid var(--census-line);
            box-shadow: 0 6px 16px rgba(23, 32, 51, 0.05);
        }

        hr {
            margin: 1.4rem 0;
            border-color: var(--census-line);
        }

        pre,
        code {
            border-radius: 8px !important;
        }

        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: var(--census-shadow);
        }

        @media (max-width: 720px) {
            .block-container {
                padding: 0.85rem 1rem 3rem;
                padding-top: max(0.85rem, env(safe-area-inset-top));
            }

            h1 {
                font-size: 1.62rem;
                line-height: 1.18;
                margin-bottom: 0.05rem;
            }

            h2, [data-testid="stHeadingWithActionElements"] h2 {
                font-size: 1.28rem;
                margin-top: 0.85rem;
                padding-top: 0.15rem;
            }

            div[data-testid="stSegmentedControl"],
            div[data-testid="stRadio"] {
                margin: 0.75rem 0 0.95rem;
            }

            div[data-testid="stSegmentedControl"] [role="radiogroup"],
            div[data-testid="stRadio"] > div {
                width: 100%;
                gap: 0.25rem;
                padding: 0.25rem;
            }

            div[data-testid="stSegmentedControl"] [role="radiogroup"] label,
            div[data-testid="stRadio"] label {
                padding-inline: 0.45rem;
                min-height: 1.9rem;
            }

            div[data-testid="column"] {
                min-width: 100%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


DEVICE_TYPES = [
    "耳道式耳機",
    "耳罩式耳機",
    "DAC",
    "耳擴",
    "DAC/耳擴一體機",
    "DAP / 隨身播放器",
    "小尾巴",
]

GOOGLE_MODEL_SUGGESTION_PROMPT = """請幫我分析這批巴哈耳機普查型號資料，找出疑似應合併的型號寫法，作為人工整理資料時的參考。

請遵守以下規則：
1. 以同品牌為前提判斷，不同品牌即使型號字串相似，也不要直接視為同一型號。
2. 大小寫、空白、全形半形、符號差異、品牌名混入型號欄，可列為高信心。
3. 不要把不同世代、不同尾碼、不同版本直接合併。
4. 若相似但可能是不同正式型號，請列為低信心或需人工判斷。
5. 請提供建議 canonical_model，但最後由人工決定。

請用以下格式輸出：
一、高信心可合併
- 原始寫法：
- 建議合併為：
- 理由：

二、低信心疑似可合併
- 原始寫法：
- 建議合併為：
- 風險：

三、不可直接合併，需人工判斷
- 容易混淆的寫法：
- 為什麼不能直接合併：
"""

STARTER_BRAND_ROWS = [
    ("Audio-Technica", "鐵三角", ["ATH"]),
    ("Sennheiser", "聲海", ["森海", "聲海"]),
    ("SONY", "索尼", ["Sony"]),
    ("AKG", "", []),
    ("Beyerdynamic", "拜耳", ["拜亞"]),
    ("Grado Labs", "", ["Grado"]),
    ("FOSTEX", "", ["Fostex"]),
    ("Yamaha", "山葉", []),
    ("Meze Audio", "", ["Meze"]),
    ("HIFIMAN", "海菲曼", ["HiFiMAN"]),
    ("final", "", ["Final", "Final Audio"]),
    ("MOONDROP", "水月雨", ["Moondrop"]),
    ("Tangzu", "唐族", ["TANGZU"]),
    ("JVC", "杰偉世", ["Victor", "JVC Victor"]),
    ("Xenns", "", []),
    ("See Audio", "", []),
    ("FiiO", "飛傲", ["FIIO", "Fiio"]),
    ("TOPPING", "拓品", ["Topping"]),
    ("SMSL", "雙木三林", ["S.M.S.L"]),
    ("iFi audio", "", ["ifi", "iFi"]),
    ("Schiit Audio", "", ["Schiit"]),
    ("TEAC", "", ["Teac"]),
    ("LUXMAN", "", ["Luxman"]),
    ("Denafrips", "", []),
    ("Astell&Kern", "", ["AK", "A&K"]),
    ("Shanling", "山靈", []),
    ("iBasso Audio", "", ["iBasso"]),
    ("Cayin", "凱音", []),
    ("Hiby", "", ["HiBy"]),
    ("Luxury&Precision", "樂彼", ["L&P"]),
    ("FOCAL", "", ["Focal"]),
    ("Campfire Audio", "", ["Campfire"]),
    ("RME", "", []),
    ("Chord Electronics", "", ["Chord"]),
    ("STAX", "", ["Stax"]),
    ("Shure", "舒爾", []),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_id() -> str:
    return str(uuid.uuid4())


def brand_sort_key(brand: dict) -> tuple[str, str]:
    return (normalize(brand.get("englishName", "")), normalize(brand.get("chineseName", "")))


def next_brand_id(state: dict) -> str:
    max_index = 0
    for brand in state.get("brands", []):
        match = re.fullmatch(r"brand-(\d+)", str(brand.get("id", "")))
        if match:
            max_index = max(max_index, int(match.group(1)))
    return f"brand-{max_index + 1}"


def next_entry_id(state: dict) -> str:
    max_index = 0
    for entry in state.get("entries", []):
        match = re.fullmatch(r"entry-(\d+)", str(entry.get("id", "")))
        if match:
            max_index = max(max_index, int(match.group(1)))
    return f"entry-{max_index + 1}"


def next_item_id(state: dict) -> str:
    max_index = 0
    for entry in state.get("entries", []):
        for device in entry.get("devices", []):
            match = re.fullmatch(r"item-(\d+)", str(device.get("id", "")))
            if match:
                max_index = max(max_index, int(match.group(1)))
    for device in st.session_state.get("devices", []):
        match = re.fullmatch(r"item-(\d+)", str(device.get("id", "")))
        if match:
            max_index = max(max_index, int(match.group(1)))
    return f"item-{max_index + 1}"


def display_brand(brand: dict) -> str:
    chinese = brand.get("chineseName", "")
    return f"{brand.get('englishName', '')} {chinese}".strip()


def starter_brands() -> list[dict]:
    rows = sorted(STARTER_BRAND_ROWS, key=lambda row: row[0].lower())
    return [
        {
            "id": f"brand-{index + 1}",
            "englishName": english,
            "chineseName": chinese,
            "aliases": aliases,
            "status": "approved",
        }
        for index, (english, chinese, aliases) in enumerate(rows)
    ]


def normalize(value: str) -> str:
    return str(value or "").strip().lower()


def normalize_brand_key(value: str) -> str:
    return re.sub(r"[\s\-_.・．。&＋+]+", "", normalize(value))


def unique_values(values: list[str]) -> list[str]:
    seen = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.append(text)
    return seen


def merge_starter_brands(existing: list[dict]) -> list[dict]:
    by_name = {}
    for brand in existing:
        english = brand.get("englishName")
        if not english:
            continue
        by_name[normalize(english)] = {
            "id": brand.get("id") or create_id(),
            "englishName": english,
            "chineseName": brand.get("chineseName", ""),
            "aliases": brand.get("aliases", []) if isinstance(brand.get("aliases"), list) else [],
            "status": brand.get("status", "approved"),
            "createdAt": brand.get("createdAt", ""),
            "updatedAt": brand.get("updatedAt", ""),
        }

    for brand in starter_brands():
        key = normalize(brand["englishName"])
        if key not in by_name:
            by_name[key] = brand
            continue
        current = by_name[key]
        current["chineseName"] = current.get("chineseName") or brand.get("chineseName", "")
        current["aliases"] = unique_values(current.get("aliases", []) + brand.get("aliases", []))
        current["status"] = current.get("status") or "approved"
    return list(by_name.values())


def normalize_state(raw: dict | None) -> dict:
    raw = raw if isinstance(raw, dict) else {}
    entries = raw.get("entries", [])
    brands = raw.get("brands", [])
    return {
        "brands": merge_starter_brands(brands if isinstance(brands, list) else []),
        "entries": entries if isinstance(entries, list) else [],
    }


def secret_value(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name, "")).strip()


def supabase_settings() -> tuple[str, str]:
    url = secret_value("SUPABASE_URL")
    key = secret_value("SUPABASE_SERVICE_ROLE_KEY") or secret_value("SUPABASE_ANON_KEY")
    placeholders = ("請把你的", "貼在這裡")
    if any(text in url for text in placeholders) or any(text in key for text in placeholders):
        return "", ""
    return url, key


def supabase_enabled() -> bool:
    url, key = supabase_settings()
    return bool(url and key)


def set_storage_status(mode: str, ok: bool, message: str = "") -> None:
    st.session_state.storage_mode = mode
    st.session_state.storage_ok = ok
    st.session_state.storage_message = message


@st.cache_resource(show_spinner=False)
def supabase_client(url: str, key: str):
    from supabase import create_client

    return create_client(url, key)


def get_supabase_client():
    url, key = supabase_settings()
    if not url or not key:
        return None
    return supabase_client(url, key)


def brand_from_supabase(row: dict) -> dict:
    return {
        "id": row.get("id") or create_id(),
        "englishName": row.get("english_name", ""),
        "chineseName": row.get("chinese_name", ""),
        "aliases": row.get("aliases", []) if isinstance(row.get("aliases"), list) else [],
        "status": row.get("status", "approved"),
        "createdAt": row.get("created_at", ""),
        "updatedAt": row.get("updated_at", ""),
    }


def brand_to_supabase(brand: dict) -> dict:
    now = now_iso()
    return {
        "id": brand.get("id") or create_id(),
        "english_name": brand.get("englishName", ""),
        "chinese_name": brand.get("chineseName", ""),
        "aliases": brand.get("aliases", []) if isinstance(brand.get("aliases"), list) else [],
        "status": brand.get("status", "approved"),
        "created_at": brand.get("createdAt") or now,
        "updated_at": brand.get("updatedAt") or now,
    }


def device_to_supabase(entry: dict, device: dict) -> dict:
    now = now_iso()
    model = str(device.get("model", "")).strip()
    original_model = str(device.get("originalModel") or model).strip()
    canonical_model = str(device.get("canonicalModel") or model).strip()
    return {
        "id": device.get("id") or create_id(),
        "entry_id": entry.get("id") or entry.get("bahamutId") or create_id(),
        "bahamut_id": entry.get("bahamutId", ""),
        "category": device.get("type", ""),
        "brand_id": device.get("brandId") or None,
        "brand": device.get("brandName", ""),
        "canonical_brand": device.get("canonicalBrand") or device.get("brandName", ""),
        "model": original_model,
        "canonical_model": canonical_model,
        "item_note": device.get("note", ""),
        "user_note": entry.get("generalNote", ""),
        "status": device.get("status", "active"),
        "created_at": entry.get("createdAt") or now,
        "updated_at": entry.get("updatedAt") or now,
        "deleted_at": device.get("deletedAt"),
    }


def state_from_supabase(brands: list[dict], items: list[dict]) -> dict:
    grouped = {}
    for row in items:
        entry_id = row.get("entry_id") or row.get("bahamut_id") or create_id()
        entry = grouped.setdefault(
            entry_id,
            {
                "id": entry_id,
                "bahamutId": row.get("bahamut_id", ""),
                "generalNote": row.get("user_note", "") or "",
                "devices": [],
                "createdAt": row.get("created_at", ""),
                "updatedAt": row.get("updated_at", ""),
            },
        )
        entry["generalNote"] = entry.get("generalNote") or row.get("user_note", "") or ""
        if (row.get("created_at") or "") < (entry.get("createdAt") or row.get("created_at") or ""):
            entry["createdAt"] = row.get("created_at", "")
        if (row.get("updated_at") or "") > (entry.get("updatedAt") or ""):
            entry["updatedAt"] = row.get("updated_at", "")

        raw_model = row.get("model", "") or ""
        canonical_model = row.get("canonical_model") or raw_model
        device = {
            "id": row.get("id") or create_id(),
            "type": row.get("category", ""),
            "brandId": row.get("brand_id", ""),
            "brandName": row.get("canonical_brand") or row.get("brand", ""),
            "model": canonical_model,
            "note": row.get("item_note", "") or "",
            "status": row.get("status", "active"),
        }
        if raw_model and raw_model != canonical_model:
            device["originalModel"] = raw_model
            device["canonicalModel"] = canonical_model
        entry["devices"].append(device)

    return normalize_state(
        {
            "brands": [brand_from_supabase(row) for row in brands],
            "entries": list(grouped.values()),
        }
    )


def load_state_from_supabase() -> dict | None:
    client = get_supabase_client()
    if not client:
        return None
    brand_response = client.table(SUPABASE_BRANDS_TABLE).select("*").execute()
    item_response = (
        client.table(SUPABASE_ITEMS_TABLE)
        .select("*")
        .eq("status", "active")
        .order("created_at", desc=True)
        .execute()
    )
    return state_from_supabase(brand_response.data or [], item_response.data or [])


def save_state_to_supabase(state: dict) -> bool:
    client = get_supabase_client()
    if not client:
        return False

    brand_rows = [brand_to_supabase(brand) for brand in state.get("brands", [])]
    if brand_rows:
        client.table(SUPABASE_BRANDS_TABLE).upsert(brand_rows, on_conflict="id").execute()

    active_rows = []
    active_ids = set()
    for entry in state.get("entries", []):
        for device in entry.get("devices", []):
            row = device_to_supabase(entry, device)
            active_rows.append(row)
            active_ids.add(row["id"])
    if active_rows:
        client.table(SUPABASE_ITEMS_TABLE).upsert(active_rows, on_conflict="id").execute()
        verify_response = (
            client.table(SUPABASE_ITEMS_TABLE)
            .select("id")
            .in_("id", list(active_ids))
            .eq("status", "active")
            .execute()
        )
        saved_ids = {row.get("id") for row in (verify_response.data or []) if row.get("id")}
        missing_ids = active_ids - saved_ids
        if missing_ids:
            raise RuntimeError(f"Supabase 驗證失敗：{len(missing_ids)} 筆器材未出現在 census_items。")

    existing_response = client.table(SUPABASE_ITEMS_TABLE).select("id").eq("status", "active").execute()
    for row in existing_response.data or []:
        row_id = row.get("id")
        if row_id and row_id not in active_ids:
            client.table(SUPABASE_ITEMS_TABLE).update(
                {"status": "deleted", "deleted_at": now_iso(), "updated_at": now_iso()}
            ).eq("id", row_id).execute()

    return True


def load_state() -> dict:
    if "state" in st.session_state:
        return st.session_state.state
    if supabase_enabled():
        try:
            state = load_state_from_supabase()
            if state is not None:
                set_storage_status("Supabase", True)
                st.session_state.state = state
                return state
        except Exception as error:
            set_storage_status("本機 JSON fallback", False, str(error))
            st.warning(f"Supabase 載入失敗，暫時改用本機資料：{error}")
    if STATE_FILE.exists():
        try:
            state = normalize_state(json.loads(STATE_FILE.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            state = normalize_state({})
    else:
        state = normalize_state({})
    set_storage_status("本機 JSON fallback", True)
    st.session_state.state = state
    return state


def save_state(state: dict) -> bool:
    if supabase_enabled():
        try:
            if save_state_to_supabase(state):
                set_storage_status("Supabase", True)
                st.session_state.state = state
                return True
        except Exception as error:
            set_storage_status("Supabase", False, str(error))
            st.error(f"Supabase 儲存失敗，資料未寫入遠端：{error}")
            return False

    DATA_DIR.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    set_storage_status("本機 JSON fallback", True)
    st.session_state.state = state
    return True


def approved_brands(state: dict) -> list[dict]:
    brands = [brand for brand in state["brands"] if brand.get("status") == "approved"]
    return sorted(brands, key=brand_sort_key)


def pending_brands(state: dict) -> list[dict]:
    return [brand for brand in state["brands"] if brand.get("status") == "pending"]


def brand_initial(brand: dict) -> str:
    name = str(brand.get("englishName") or display_brand(brand) or "").strip()
    if not name:
        return "#"
    initial = name[0].upper()
    return initial if initial.isalpha() else "#"


def brand_matched_aliases(brand: dict, query: str) -> list[str]:
    needle = normalize(query)
    if not needle:
        return []
    return [
        alias
        for alias in brand.get("aliases", [])
        if needle in normalize(alias)
    ]


def brand_matches_query(brand: dict, query: str) -> bool:
    needle = normalize(query)
    if not needle:
        return True
    fields = [
        display_brand(brand),
        brand.get("englishName", ""),
        brand.get("chineseName", ""),
        *brand.get("aliases", []),
    ]
    return any(needle in normalize(field) for field in fields)


def render_approved_brand_directory(state: dict) -> None:
    st.markdown("#### 正式品牌清單")
    brands = approved_brands(state)
    if not brands:
        st.info("目前沒有正式品牌。")
        return

    search_col, initial_col = st.columns([3, 1])
    query = search_col.text_input("搜尋正式品牌", placeholder="輸入品牌英文、中文或 alias", key="approved_brand_search")
    initials = sorted({brand_initial(brand) for brand in brands})
    selected_initial = initial_col.selectbox("字母索引", ["全部"] + initials, key="approved_brand_initial")

    filtered = [
        brand
        for brand in brands
        if (selected_initial == "全部" or brand_initial(brand) == selected_initial)
        and brand_matches_query(brand, query)
    ]

    st.caption(f"顯示 {len(filtered)} / {len(brands)} 個正式品牌")
    if not filtered:
        st.info("找不到符合條件的正式品牌。")
        return

    rows = []
    for brand in filtered:
        aliases = brand.get("aliases", [])
        matched_aliases = brand_matched_aliases(brand, query)
        rows.append(
            {
                "品牌": display_brand(brand),
                "Alias": ", ".join(aliases),
                "命中 alias": ", ".join(matched_aliases) if matched_aliases else "",
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)


def find_brand(state: dict, query: str) -> dict | None:
    needle = normalize(query)
    brand_key = normalize_brand_key(query)
    for brand in state["brands"]:
        if brand.get("status") in ("rejected", "merged"):
            continue
        values = [
            brand.get("englishName", ""),
            brand.get("chineseName", ""),
            display_brand(brand),
            *brand.get("aliases", []),
        ]
        if any(normalize(value) == needle or normalize_brand_key(value) == brand_key for value in values):
            return brand
    return None


def create_pending_brand(state: dict, raw_name: str) -> dict:
    existing = find_brand(state, raw_name)
    if existing:
        return existing

    brand = {
        "id": next_brand_id(state),
        "englishName": raw_name,
        "chineseName": "",
        "aliases": [raw_name],
        "status": "pending",
        "createdAt": now_iso(),
        "updatedAt": now_iso(),
    }
    state["brands"].append(brand)
    return brand


def resolve_device_brands_for_submit(state: dict, devices: list[dict]) -> list[dict]:
    resolved = []
    for device in devices:
        next_device = dict(device)
        brand = brand_by_id(state, next_device.get("brandId", "")) or find_brand(
            state,
            next_device.get("brandName", ""),
        )
        if not brand:
            brand = create_pending_brand(state, next_device.get("brandName", ""))
        next_device["brandId"] = brand["id"]
        next_device["brandName"] = display_brand(brand)
        resolved.append(next_device)
    return resolved


def build_post(entry: dict) -> str:
    groups = defaultdict(list)
    for device in entry.get("devices", []):
        groups[device.get("type", "其他")].append(device)

    lines = ["2026 巴哈耳機普查", "", f"巴哈 ID：{entry.get('bahamutId', '')}", ""]
    for device_type in DEVICE_TYPES:
        devices = groups.get(device_type, [])
        if not devices:
            continue
        lines.append(f"{device_type}：")
        for device in devices:
            note = f"（{device.get('note')}）" if device.get("note") else ""
            lines.append(f"- {device.get('brandName', '')} {device.get('model', '')}{note}")
        lines.append("")

    if entry.get("generalNote"):
        lines.append("補充：")
        lines.append(entry["generalNote"])
        lines.append("")
    return "\n".join(lines).strip()


def flatten_devices(state: dict) -> list[dict]:
    rows = []
    for entry in state["entries"]:
        for device in entry.get("devices", []):
            rows.append(
                {
                    **device,
                    "bahamutId": entry.get("bahamutId", ""),
                    "createdAt": entry.get("createdAt", ""),
                    "updatedAt": entry.get("updatedAt", ""),
                }
            )
    return rows


def brand_by_id(state: dict, brand_id: str) -> dict | None:
    return next((brand for brand in state["brands"] if brand.get("id") == brand_id), None)


def is_approved_device(state: dict, device: dict) -> bool:
    brand = brand_by_id(state, device.get("brandId", ""))
    return not brand or brand.get("status") == "approved"


def merge_notes(left: str, right: str) -> str:
    return "\n".join(unique_values([*(left or "").split("\n"), right]))


def unique_devices(devices: list[dict]) -> list[dict]:
    by_key = {}
    for device in devices:
        key = "|".join(
            normalize(str(device.get(field, "")))
            for field in ("type", "brandName", "model", "note")
        )
        by_key.setdefault(key, dict(device))
    return list(by_key.values())


def record_groups(state: dict, query: str = "") -> list[dict]:
    groups = {}
    needle = normalize(query)
    for entry in state["entries"]:
        key = normalize(entry.get("bahamutId", ""))
        if not key or (needle and needle not in key):
            continue

        current = groups.setdefault(
            key,
            {
                "id": key,
                "bahamutId": entry.get("bahamutId", ""),
                "generalNote": entry.get("generalNote", ""),
                "devices": [],
                "createdAt": entry.get("createdAt") or entry.get("updatedAt", ""),
                "updatedAt": entry.get("updatedAt") or entry.get("createdAt", ""),
                "entryCount": 0,
            },
        )
        current["devices"].extend(entry.get("devices", []))
        current["generalNote"] = merge_notes(current.get("generalNote", ""), entry.get("generalNote", ""))
        current["entryCount"] += 1
        if (entry.get("createdAt") or entry.get("updatedAt", "")) > current.get("createdAt", ""):
            current["createdAt"] = entry.get("createdAt") or entry.get("updatedAt", "")
        if (entry.get("updatedAt") or entry.get("createdAt", "")) > current.get("updatedAt", ""):
            current["updatedAt"] = entry.get("updatedAt") or entry.get("createdAt", "")

    rows = [{**group, "devices": unique_devices(group["devices"])} for group in groups.values()]
    return sorted(rows, key=lambda item: item.get("createdAt") or item.get("updatedAt", ""), reverse=True)


def format_time(value: str) -> str:
    if not value:
        return "未記錄"
    return value.replace("T", " ").replace("+00:00", "").replace("Z", "")[:19]


def rank_rows(items: list[dict], key: str, limit: int | None = 10) -> list[tuple[str, int]]:
    counts = Counter(str(item.get(key, "")).strip() for item in items if item.get(key))
    return counts.most_common(limit)


def model_rank_rows(devices: list[dict], limit: int | None = None) -> list[tuple[str, int]]:
    counts = Counter(
        f"{device.get('brandName', '')} {device.get('model', '')}".strip()
        for device in devices
        if device.get("model")
    )
    return counts.most_common(limit)


def chart_rows(rows: list[tuple[str, int]]) -> list[dict]:
    return [{"label": label, "count": count} for label, count in rows]


def render_bar_chart(title: str, rows: list[tuple[str, int]], empty_text: str, height: int = 260) -> None:
    st.markdown(f"#### {title}")
    values = chart_rows(rows)
    if not values:
        st.info(empty_text)
        return
    max_count = max(row["count"] for row in values)
    x_axis = {"format": "d"}
    if max_count <= 30:
        x_axis["values"] = list(range(1, max_count + 1))
    st.vega_lite_chart(
        {
            "data": {"values": values},
            "mark": {"type": "bar", "cornerRadiusEnd": 3, "tooltip": True},
            "encoding": {
                "x": {
                    "field": "count",
                    "type": "quantitative",
                    "title": "數量",
                    "scale": {"domainMin": 0, "domainMax": max_count},
                    "axis": x_axis,
                },
                "y": {
                    "field": "label",
                    "type": "nominal",
                    "title": None,
                    "sort": "-x",
                },
                "tooltip": [
                    {"field": "label", "type": "nominal", "title": "項目"},
                    {"field": "count", "type": "quantitative", "title": "數量"},
                ],
            },
            "height": height,
        },
        use_container_width=True,
    )


def render_full_rank_table(
    title: str,
    rows: list[tuple[str, int]],
    empty_text: str,
    *,
    label_title: str = "項目",
    search_key: str,
    sort_key: str,
    scale_key: str,
    height: int = 560,
) -> None:
    st.markdown(f"#### {title}")
    if not rows:
        st.info(empty_text)
        return

    control_cols = st.columns([3, 1.4, 1.2])
    query = control_cols[0].text_input("搜尋", placeholder=f"輸入{label_title}關鍵字", key=search_key)
    sort_mode = control_cols[1].selectbox(
        "排序",
        ["數量高到低", f"{label_title} A-Z", f"{label_title} Z-A"],
        key=sort_key,
    )
    scale_mode = control_cols[2].segmented_control("刻度", ["線性", "對數"], key=scale_key)
    scale_mode = scale_mode or "線性"

    filtered = [(label, count) for label, count in rows if normalize(query) in normalize(label)]
    if sort_mode.endswith("A-Z"):
        filtered.sort(key=lambda row: normalize(row[0]))
    elif sort_mode.endswith("Z-A"):
        filtered.sort(key=lambda row: normalize(row[0]), reverse=True)
    else:
        filtered.sort(key=lambda row: (-row[1], normalize(row[0])))

    total_count = sum(count for _, count in rows)
    max_count = max((count for _, count in filtered), default=0)
    max_log = math.log10(max_count + 1) if max_count else 1
    table_rows = []
    for index, (label, count) in enumerate(filtered, start=1):
        if scale_mode == "對數":
            bar_value = (math.log10(count + 1) / max_log * 100) if max_count else 0
        else:
            bar_value = (count / max_count * 100) if max_count else 0
        table_rows.append(
            {
                "排名": index,
                label_title: label,
                "數量": count,
                "占比": (count / total_count * 100) if total_count else 0,
                "視覺比例": round(bar_value, 2),
            }
        )

    st.caption(f"顯示 {len(filtered)} / {len(rows)} 筆；占比以目前品項總數計算。")
    if not table_rows:
        st.info("找不到符合條件的資料。")
        return
    st.dataframe(
        table_rows,
        use_container_width=True,
        hide_index=True,
        height=height,
        column_config={
            "排名": st.column_config.NumberColumn(width="small", format="%d"),
            label_title: st.column_config.TextColumn(width="large"),
            "數量": st.column_config.NumberColumn(width="small", format="%d"),
            "占比": st.column_config.NumberColumn(width="small", format="%.2f%%"),
            "視覺比例": st.column_config.ProgressColumn(
                "視覺比例",
                min_value=0,
                max_value=100,
                format="%.1f%%",
                width="medium",
            ),
        },
    )


def normalize_model_key(value: str, brand_names: list[str] | None = None) -> str:
    text = normalize(value)
    for brand_name in brand_names or []:
        brand_key = normalize(brand_name)
        if brand_key and text.startswith(brand_key):
            text = text[len(brand_key) :].strip()
    return re.sub(r"[\s\-_/\\.・．。＋+]+", "", text)


def model_rows_for_brand(state: dict, brand: dict) -> list[dict]:
    rows = []
    brand_name = display_brand(brand)
    for device in flatten_devices(state):
        if device.get("brandId") == brand.get("id") or normalize(device.get("brandName")) == normalize(brand_name):
            model = str(device.get("model", "")).strip()
            if model:
                rows.append(device)
    return rows


def model_variant_groups(devices: list[dict], brand: dict) -> list[dict]:
    brand_names = [
        brand.get("englishName", ""),
        brand.get("chineseName", ""),
        display_brand(brand),
        *brand.get("aliases", []),
    ]
    groups = {}
    for device in devices:
        model = str(device.get("model", "")).strip()
        key = normalize_model_key(model, brand_names)
        if not key:
            continue
        group = groups.setdefault(
            key,
            {
                "key": key,
                "canonical": model,
                "models": Counter(),
                "types": Counter(),
                "users": set(),
            },
        )
        group["models"][model] += 1
        group["types"][device.get("type", "")] += 1
        if device.get("bahamutId"):
            group["users"].add(device["bahamutId"])

    rows = []
    for group in groups.values():
        if len(group["models"]) < 2:
            continue
        variants = group["models"].most_common()
        rows.append(
            {
                "key": group["key"],
                "canonical": variants[0][0],
                "variants": variants,
                "count": sum(group["models"].values()),
                "users": len(group["users"]),
                "types": ", ".join(name for name, _ in group["types"].most_common() if name),
            }
        )
    return sorted(rows, key=lambda item: (-item["count"], item["canonical"].lower()))


def model_frequency_rows(devices: list[dict]) -> list[tuple[str, int, int, str]]:
    rows = {}
    for device in devices:
        model = str(device.get("model", "")).strip()
        if not model:
            continue
        row = rows.setdefault(model, {"count": 0, "users": set(), "types": Counter()})
        row["count"] += 1
        if device.get("bahamutId"):
            row["users"].add(device["bahamutId"])
        row["types"][device.get("type", "")] += 1
    result = [
        (
            model,
            data["count"],
            len(data["users"]),
            ", ".join(name for name, _ in data["types"].most_common() if name),
        )
        for model, data in rows.items()
    ]
    return sorted(result, key=lambda row: (-row[1], row[0].lower()))


def build_model_ai_prompt(brand: dict, devices: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["品牌", "類型", "型號", "筆數", "使用者數"])
    for model, count, users, types in model_frequency_rows(devices):
        writer.writerow([display_brand(brand), types, model, count, users])
    return f"{GOOGLE_MODEL_SUGGESTION_PROMPT}\n\n品牌：{display_brand(brand)}\n\n資料：\n{output.getvalue()}"


def apply_model_merge(state: dict, brand: dict, variants: list[str], canonical_model: str) -> int:
    canonical = canonical_model.strip()
    if not canonical:
        return 0

    variant_set = {str(value or "").strip() for value in variants if str(value or "").strip()}
    if not variant_set:
        return 0

    brand_name = display_brand(brand)
    changed = 0
    now = now_iso()
    for entry in state["entries"]:
        entry_changed = False
        for device in entry.get("devices", []):
            same_brand = device.get("brandId") == brand.get("id") or normalize(device.get("brandName")) == normalize(brand_name)
            current_model = str(device.get("model", "")).strip()
            if not same_brand or current_model not in variant_set:
                continue
            if current_model != canonical and not device.get("originalModel"):
                device["originalModel"] = current_model
            device["model"] = canonical
            device["canonicalModel"] = canonical
            changed += 1
            entry_changed = True
        if entry_changed:
            entry["updatedAt"] = now

    for device in st.session_state.get("devices", []):
        same_brand = device.get("brandId") == brand.get("id") or normalize(device.get("brandName")) == normalize(brand_name)
        current_model = str(device.get("model", "")).strip()
        if same_brand and current_model in variant_set:
            if current_model != canonical and not device.get("originalModel"):
                device["originalModel"] = current_model
            device["model"] = canonical
            device["canonicalModel"] = canonical

    return changed


def snapshot_model_merge(state: dict, brand: dict, variants: list[str], canonical_model: str) -> dict | None:
    canonical = canonical_model.strip()
    variant_set = {str(value or "").strip() for value in variants if str(value or "").strip()}
    if not canonical or not variant_set:
        return None

    brand_name = display_brand(brand)
    records = []
    for entry in state["entries"]:
        for device in entry.get("devices", []):
            same_brand = device.get("brandId") == brand.get("id") or normalize(device.get("brandName")) == normalize(brand_name)
            current_model = str(device.get("model", "")).strip()
            if not same_brand or current_model not in variant_set:
                continue
            records.append(
                {
                    "entryId": entry.get("id"),
                    "entryUpdatedAt": entry.get("updatedAt"),
                    "deviceId": device.get("id"),
                    "model": device.get("model"),
                    "originalModel": device.get("originalModel"),
                    "hasOriginalModel": "originalModel" in device,
                    "canonicalModel": device.get("canonicalModel"),
                    "hasCanonicalModel": "canonicalModel" in device,
                }
            )

    if not records:
        return None

    return {
        "brand": display_brand(brand),
        "variants": sorted(variant_set),
        "canonicalModel": canonical,
        "records": records,
        "createdAt": now_iso(),
    }


def remember_model_merge(snapshot: dict | None) -> None:
    if not snapshot:
        return
    stack = st.session_state.setdefault("model_merge_undo_stack", [])
    stack.append(snapshot)
    if len(stack) > 10:
        del stack[:-10]


def restore_optional_field(target: dict, field: str, value, existed: bool) -> None:
    if existed:
        target[field] = value
    else:
        target.pop(field, None)


def undo_last_model_merge(state: dict) -> tuple[int, str]:
    stack = st.session_state.get("model_merge_undo_stack", [])
    if not stack:
        return 0, ""

    snapshot = stack.pop()
    restored = 0
    entries_by_id = {entry.get("id"): entry for entry in state["entries"]}
    for record in snapshot.get("records", []):
        entry = entries_by_id.get(record.get("entryId"))
        if not entry:
            continue
        device = next((item for item in entry.get("devices", []) if item.get("id") == record.get("deviceId")), None)
        if not device:
            continue
        device["model"] = record.get("model")
        restore_optional_field(device, "originalModel", record.get("originalModel"), record.get("hasOriginalModel", False))
        restore_optional_field(device, "canonicalModel", record.get("canonicalModel"), record.get("hasCanonicalModel", False))
        if record.get("entryUpdatedAt") is not None:
            entry["updatedAt"] = record.get("entryUpdatedAt")
        restored += 1

    return restored, snapshot.get("canonicalModel", "")


def google_api_key() -> str:
    try:
        secret_value = st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        secret_value = ""
    return str(secret_value or os.getenv("GOOGLE_API_KEY", "")).strip()


def google_api_key_status(api_key: str) -> tuple[bool, str]:
    if not api_key:
        return False, "尚未設定 GOOGLE_API_KEY。"
    if "請把你的" in api_key or "貼在這裡" in api_key:
        return False, "GOOGLE_API_KEY 仍是範例文字，請把引號內整段換成真正的 Google API key。"
    if not api_key.isascii():
        return False, "GOOGLE_API_KEY 含有非英文/數字符號字元，請確認沒有貼到中文說明或多餘文字。"
    if len(api_key) < 20:
        return False, "GOOGLE_API_KEY 看起來太短，請確認已貼上完整 key。"
    return True, "Google API key 已設定。"


def ask_google_for_model_suggestions(prompt: str, model_name: str, api_key: str) -> tuple[str, str]:
    key_ok, key_message = google_api_key_status(api_key)
    if not key_ok:
        return "", key_message

    try:
        from google import genai
    except ImportError:
        return "", "尚未安裝 google-genai。本機請先執行 python -m pip install -r requirements.txt，若剛安裝完成請重啟 Streamlit。"

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model_name, contents=prompt)
    except Exception as error:
        return "", f"Google API 呼叫失敗：{error}"
    return str(getattr(response, "text", "") or "").strip(), ""


def state_to_csv(state: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["巴哈ID", "建立時間", "更新時間", "類型", "品牌", "型號", "備註"])
    for device in flatten_devices(state):
        writer.writerow(
            [
                device.get("bahamutId", ""),
                device.get("createdAt", ""),
                device.get("updatedAt", ""),
                device.get("type", ""),
                device.get("brandName", ""),
                device.get("model", ""),
                device.get("note", ""),
            ]
        )
    return "\ufeff" + output.getvalue()


def ensure_session_defaults() -> None:
    st.session_state.setdefault("devices", [])
    st.session_state.setdefault("last_post", "")
    st.session_state.setdefault("editing_entry_id", None)
    st.session_state.setdefault("pending_edit_entry_id", None)
    st.session_state.setdefault("requested_page", None)
    st.session_state.setdefault("history_submitted_bahamut_id", "")
    st.session_state.setdefault("record_submitted_search", "")
    st.session_state.setdefault("records_page", 1)
    st.session_state.setdefault("expanded_record_id", None)
    st.session_state.setdefault("active_page", "填寫")


def render_form(state: dict) -> None:
    st.subheader("填寫資料")
    if st.session_state.pending_edit_entry_id:
        entry = next(
            (item for item in state["entries"] if item.get("id") == st.session_state.pending_edit_entry_id),
            None,
        )
        if entry:
            st.session_state.editing_entry_id = entry["id"]
            st.session_state.bahamut_id = entry.get("bahamutId", "")
            st.session_state.general_note = entry.get("generalNote", "")
            st.session_state.devices = [dict(device) for device in entry.get("devices", [])]
        st.session_state.pending_edit_entry_id = None

    if st.session_state.editing_entry_id:
        st.info("編輯模式：資料已載入，修改後送出會覆蓋原紀錄。")

    bahamut_id = st.text_input("巴哈 ID", key="bahamut_id")

    with st.form("device_form", clear_on_submit=True):
        cols = st.columns([1, 1, 1])
        device_type = cols[0].selectbox("設備類型", DEVICE_TYPES)
        brand_options = [display_brand(brand) for brand in approved_brands(state)]
        brand_name = cols[1].selectbox("品牌", [""] + brand_options, index=0)
        custom_brand = cols[1].text_input("清單沒有？新增待審品牌")
        cols[1].caption("直接輸入清單外品牌，送出整份問卷後會送到後台待確認。")
        brand_error_slot = cols[1].empty()
        model = cols[2].text_input("型號", placeholder="例如 HA-FW02、HD800S、K9 Pro")
        note = st.text_input("設備備註", placeholder="例如 改線、常用搭配、版本")
        submitted = st.form_submit_button("加入設備")

    if submitted:
        picked_brand = custom_brand.strip() or brand_name.strip()
        missing = []
        if not picked_brand:
            brand_error_slot.warning("請選擇品牌或輸入待審品牌")
            missing.append("請選擇品牌或輸入待審品牌")
        if not model.strip():
            missing.append("請填寫型號")
        if missing:
            global_missing = [item for item in missing if item != "請選擇品牌或輸入待審品牌"]
            if global_missing:
                st.warning("\n".join(f"- {item}" for item in global_missing))
        else:
            brand = find_brand(state, picked_brand)
            st.session_state.devices.append(
                {
                    "id": next_item_id(state),
                    "type": device_type,
                    "brandId": brand["id"] if brand else "",
                    "brandName": display_brand(brand) if brand else picked_brand,
                    "model": model.strip(),
                    "note": note.strip(),
                }
            )
            st.success("已加入設備。")

    st.markdown("#### 本次填寫的設備")
    if st.session_state.devices:
        for index, device in enumerate(st.session_state.devices):
            cols = st.columns([5, 1])
            cols[0].write(f"{device['type']}｜{device['brandName']} {device['model']} {device.get('note', '')}")
            if cols[1].button("移除", key=f"remove-device-{device['id']}"):
                st.session_state.devices.pop(index)
                st.rerun()
    else:
        st.info("尚未加入設備。")

    st.divider()
    general_note = st.text_area("補充備註", key="general_note")

    if st.button("送出並產生貼文", type="primary"):
        missing = []
        if not bahamut_id.strip():
            missing.append("請填寫巴哈 ID")
        if not st.session_state.devices:
            missing.append("請至少加入一項設備")
        if missing:
            st.warning("\n".join(f"- {item}" for item in missing))
            return

        previous_state = copy.deepcopy(state)
        now = now_iso()
        submitted_devices = resolve_device_brands_for_submit(state, st.session_state.devices)
        entry = {
            "id": st.session_state.editing_entry_id or next_entry_id(state),
            "bahamutId": bahamut_id.strip(),
            "generalNote": general_note.strip(),
            "devices": submitted_devices,
            "createdAt": now,
            "updatedAt": now,
        }

        existing_index = next(
            (index for index, item in enumerate(state["entries"]) if item.get("id") == entry["id"]),
            None,
        )
        if existing_index is None:
            state["entries"].append(entry)
        else:
            entry["createdAt"] = state["entries"][existing_index].get("createdAt", now)
            state["entries"][existing_index] = entry

        if save_state(state):
            st.session_state.last_post = build_post(entry)
            st.session_state.devices = []
            st.session_state.editing_entry_id = None
            st.success("已儲存，貼文已產生。")
        else:
            state.clear()
            state.update(previous_state)
            st.warning("遠端儲存未成功，這次送出沒有完成寫入。")

    if st.session_state.last_post:
        st.text_area("貼文內容", value=st.session_state.last_post, height=360)


def render_history(state: dict) -> None:
    st.subheader("查詢 / 編輯自己的紀錄")
    search_cols = st.columns([5, 1])
    bahamut_id = search_cols[0].text_input("輸入巴哈 ID 查詢", key="history_bahamut_id")
    if search_cols[1].button("查詢", key="history_search_button", type="primary"):
        st.session_state.history_submitted_bahamut_id = bahamut_id.strip()
    bahamut_id = st.session_state.history_submitted_bahamut_id
    if not bahamut_id.strip():
        return
    matches = [
        entry
        for entry in state["entries"]
        if normalize(entry.get("bahamutId")) == normalize(bahamut_id)
    ]
    matches.sort(key=lambda item: item.get("updatedAt", ""), reverse=True)
    if not matches:
        st.info("找不到這個 ID 的紀錄。")
        return
    if st.session_state.editing_entry_id:
        st.info("已載入編輯模式，請切到「填寫」頁繼續修改。")
        st.divider()
    for entry in matches:
        with st.expander(f"{entry.get('bahamutId')}｜{len(entry.get('devices', []))} 項設備｜{entry.get('updatedAt', '')}"):
            st.code(build_post(entry), language="text")
            cols = st.columns(2)
            if cols[0].button("載入編輯", key=f"edit-{entry['id']}"):
                st.session_state.pending_edit_entry_id = entry["id"]
                st.session_state.requested_page = "填寫"
                st.rerun()
            if cols[1].button("刪除", key=f"delete-{entry['id']}"):
                state["entries"] = [item for item in state["entries"] if item.get("id") != entry["id"]]
                save_state(state)
                st.rerun()


def render_record_detail(entry: dict) -> None:
    st.caption(f"{entry.get('bahamutId', '')}｜提交時間：{format_time(entry.get('createdAt') or entry.get('updatedAt', ''))}")
    st.write(f"設備數：{len(entry.get('devices', []))}")
    for device in entry.get("devices", []):
        note = f"（{device.get('note')}）" if device.get("note") else ""
        st.write(f"- {device.get('type', '')}｜{device.get('brandName', '')} {device.get('model', '')}{note}")
    if entry.get("generalNote"):
        st.divider()
        st.write(f"備註：{entry.get('generalNote')}")


def render_records(state: dict) -> None:
    st.subheader("紀錄")
    st.caption("依提交時間倒序查看所有回覆。")

    search_cols = st.columns([5, 1])
    query_input = search_cols[0].text_input("巴哈 ID 搜尋", key="record_search")
    if search_cols[1].button("查詢", key="record_search_button", type="primary"):
        st.session_state.record_submitted_search = query_input.strip()
        st.session_state.records_page = 1
        st.session_state.expanded_record_id = None
    query = st.session_state.record_submitted_search

    records = record_groups(state, query)
    total_pages = max(1, (len(records) + RECORDS_PAGE_SIZE - 1) // RECORDS_PAGE_SIZE)
    st.session_state.records_page = min(max(st.session_state.records_page, 1), total_pages)
    page = st.session_state.records_page
    start = (page - 1) * RECORDS_PAGE_SIZE
    page_records = records[start : start + RECORDS_PAGE_SIZE]

    if records:
        st.caption(f"共 {len(records)} 位使用者，第 {page} / {total_pages} 頁")
    elif query:
        st.info("找不到符合的巴哈 ID。")
    else:
        st.info("目前還沒有任何紀錄。")

    for entry in page_records:
        with st.container(border=True):
            cols = st.columns([3, 2, 1])
            cols[0].markdown(f"**{entry.get('bahamutId', '未填寫')}**")
            cols[0].caption(f"提交時間：{format_time(entry.get('createdAt') or entry.get('updatedAt', ''))}")
            cols[1].write(f"設備數：{len(entry.get('devices', []))}")
            is_expanded = st.session_state.expanded_record_id == entry["id"]
            label = "收合" if is_expanded else "查看"
            if cols[2].button(label, key=f"record-view-{entry['id']}"):
                st.session_state.expanded_record_id = None if is_expanded else entry["id"]
                st.rerun()
            if is_expanded:
                st.divider()
                render_record_detail(entry)

    if total_pages > 1:
        prev_col, page_col, next_col = st.columns([1, 2, 1])
        if prev_col.button("上一頁", disabled=page <= 1):
            st.session_state.records_page -= 1
            st.rerun()
        page_col.write(f"{page} / {total_pages}")
        if next_col.button("下一頁", disabled=page >= total_pages):
            st.session_state.records_page += 1
            st.rerun()


def render_stats(state: dict) -> None:
    st.subheader("統計")
    devices = flatten_devices(state)
    approved_devices = [device for device in devices if is_approved_device(state, device)]
    cols = st.columns(4)
    cols[0].metric("填寫紀錄", len(state["entries"]))
    cols[1].metric("設備總數", len(devices))
    cols[2].metric("正式品牌", len(approved_brands(state)))
    cols[3].metric("待確認品牌", len(pending_brands(state)))

    type_rows = rank_rows(devices, "type", None)
    type_options = [row[0] for row in type_rows]
    selected_type = "全部" if type_options else ""
    if type_options:
        selected_type = st.selectbox("品項類型", ["全部"] + type_options, key="stats_device_type")
    typed_approved_devices = [
        device
        for device in approved_devices
        if selected_type == "全部" or device.get("type") == selected_type
    ]
    brand_rows = rank_rows(typed_approved_devices, "brandName", None)
    model_rows = model_rank_rows(typed_approved_devices, None)
    brand_chart_rows = brand_rows[:20]
    model_chart_rows = model_rows[:20]
    selected_type_title = "" if selected_type == "全部" else selected_type

    st.markdown("### 成果視覺化")
    chart_left, chart_right = st.columns(2)
    with chart_left:
        render_bar_chart("類型分布", type_rows, "目前沒有可視覺化的設備類型。")
    with chart_right:
        chart_tab_brand, chart_tab_model = st.tabs(["Top 品牌", "Top 型號"])
        with chart_tab_brand:
            render_bar_chart(
                f"{selected_type_title} Top 品牌" if selected_type_title else "Top 品牌",
                brand_chart_rows,
                "目前沒有這個品項的正式品牌設備可視覺化。",
            )
        with chart_tab_model:
            render_bar_chart(
                f"{selected_type_title} Top 型號" if selected_type_title else "Top 型號",
                model_chart_rows,
                "目前沒有這個品項的正式型號設備可視覺化。",
            )

    st.divider()

    pending_rows = []
    for brand in pending_brands(state):
        count = sum(1 for device in devices if device.get("brandId") == brand.get("id"))
        pending_rows.append((display_brand(brand), count))
    pending_rows.sort(key=lambda row: (-row[1], row[0]))

    pending_col, summary_col = st.columns(2)
    pending_col.markdown("#### 待確認品牌")
    if pending_rows:
        pending_col.table(pending_rows)
    else:
        pending_col.info("目前沒有待確認品牌。")
    summary_col.markdown("#### 目前篩選")
    summary_col.write(f"品項類型：{selected_type}")
    summary_col.write(f"正式設備：{len(typed_approved_devices)}")
    summary_col.write(f"品牌數：{len(brand_rows)}")
    summary_col.write(f"型號數：{len(model_rows)}")

    st.markdown("### 完整排名")
    rank_type_tab, rank_brand_tab, rank_model_tab = st.tabs(["類型", "品牌", "型號"])
    with rank_type_tab:
        render_full_rank_table(
            "類型完整排名",
            type_rows,
            "目前沒有設備類型資料。",
            label_title="類型",
            search_key="stats-type-search",
            sort_key="stats-type-sort",
            scale_key="stats-type-scale",
            height=360,
        )
    with rank_brand_tab:
        render_full_rank_table(
            f"{selected_type_title} 品牌完整排名" if selected_type_title else "品牌完整排名",
            brand_rows,
            "目前沒有品牌排名資料。",
            label_title="品牌",
            search_key="stats-brand-search",
            sort_key="stats-brand-sort",
            scale_key="stats-brand-scale",
        )
    with rank_model_tab:
        render_full_rank_table(
            f"{selected_type_title} 型號完整排名" if selected_type_title else "型號完整排名",
            model_rows,
            "目前沒有型號排名資料。",
            label_title="型號",
            search_key="stats-model-search",
            sort_key="stats-model-sort",
            scale_key="stats-model-scale",
            height=640,
        )

    st.download_button("下載 CSV", state_to_csv(state), "bahamut-audio-census.csv", "text/csv")
    st.download_button(
        "下載 JSON",
        json.dumps(state, ensure_ascii=False, indent=2),
        "bahamut-audio-census.json",
        "application/json",
    )


def render_model_review(state: dict) -> None:
    if not st.session_state.get("admin_unlocked", False):
        prompt_admin_password()
        return

    st.subheader("型號人工對照")
    st.caption("此頁只做型號合併判斷草稿，不會寫入目前資料。Google AI 建議只作第一輪參考，最後仍由人工決定。")

    undo_stack = st.session_state.get("model_merge_undo_stack", [])
    undo_cols = st.columns([1, 3])
    if undo_cols[0].button("復原上一次型號合併", disabled=not undo_stack):
        restored, canonical = undo_last_model_merge(state)
        if restored:
            save_state(state)
            st.success(f"已復原上一筆型號合併：{canonical}，還原 {restored} 筆設備。")
            st.rerun()
        else:
            st.warning("沒有可復原的型號合併紀錄。")
    if undo_stack:
        last_snapshot = undo_stack[-1]
        undo_cols[1].caption(
            f"可復原：{last_snapshot.get('brand', '')}｜{', '.join(last_snapshot.get('variants', []))}"
            f" -> {last_snapshot.get('canonicalModel', '')}"
        )

    approved = approved_brands(state)
    if not approved:
        st.info("目前沒有正式品牌，請先完成品牌審核。")
        return

    brand_options = [display_brand(brand) for brand in approved]
    selected_label = st.selectbox("選擇正式品牌", brand_options, key="model-review-brand")
    brand = approved[brand_options.index(selected_label)]
    devices = model_rows_for_brand(state, brand)

    if not devices:
        st.info("這個品牌目前沒有可對照的型號資料。")
        return

    frequency_rows = model_frequency_rows(devices)
    variant_groups = model_variant_groups(devices, brand)

    cols = st.columns(4)
    cols[0].metric("型號寫法", len(frequency_rows))
    cols[1].metric("設備筆數", len(devices))
    cols[2].metric("疑似同型群組", len(variant_groups))
    cols[3].metric("填寫者數", len({device.get("bahamutId") for device in devices if device.get("bahamutId")}))

    st.markdown("#### 型號清單")
    st.dataframe(
        [
            {"型號": model, "筆數": count, "使用者數": users, "類型": types}
            for model, count, users, types in frequency_rows
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### 手動合併")
    model_options = [model for model, _, _, _ in frequency_rows]
    manual_variants = st.multiselect(
        "自行選擇要合併的型號寫法",
        model_options,
        key=f"manual-model-variants-{brand['id']}",
    )
    default_manual_canonical = manual_variants[0] if manual_variants else ""
    manual_canonical = st.text_input(
        "手動 canonical_model",
        value=default_manual_canonical,
        key=f"manual-model-canonical-{brand['id']}",
    )
    manual_note = st.text_area(
        "手動合併備註",
        placeholder="例如 AI 沒抓到，但我確認這幾個寫法是同一台。",
        key=f"manual-model-note-{brand['id']}",
    )
    manual_cols = st.columns([1, 1])
    if manual_cols[0].button(
        "產生手動合併草稿",
        disabled=len(manual_variants) < 2 or not manual_canonical.strip(),
        key=f"manual-model-draft-{brand['id']}",
    ):
        st.session_state.model_review_draft = "\n".join(
            [
                f"品牌：{display_brand(brand)}",
                f"原始寫法：{', '.join(manual_variants)}",
                "人工判定：手動合併",
                f"canonical_model：{manual_canonical.strip()}",
                f"備註：{manual_note.strip()}",
            ]
        )
    if manual_cols[1].button(
        "確認手動合併並套用",
        type="primary",
        disabled=len(manual_variants) < 2 or not manual_canonical.strip(),
        key=f"manual-model-apply-{brand['id']}",
    ):
        snapshot = snapshot_model_merge(state, brand, manual_variants, manual_canonical)
        changed = apply_model_merge(state, brand, manual_variants, manual_canonical)
        if changed:
            remember_model_merge(snapshot)
            st.session_state.model_review_draft = "\n".join(
                [
                    f"品牌：{display_brand(brand)}",
                    f"原始寫法：{', '.join(manual_variants)}",
                    "人工判定：手動合併",
                    f"canonical_model：{manual_canonical.strip()}",
                    f"備註：{manual_note.strip()}",
                ]
            )
            save_state(state)
            st.success(f"已套用手動合併，更新 {changed} 筆設備型號。")
            st.rerun()
        else:
            st.warning("沒有可更新的型號，請確認選取項目與 canonical_model。")

    st.markdown("#### 系統初步抓出的疑似同型")
    if not variant_groups:
        st.info("目前沒有只因大小寫、空白或符號差異而聚在一起的型號。")
    else:
        group_labels = [
            f"{group['canonical']}（{group['count']} 筆，{len(group['variants'])} 種寫法）"
            for group in variant_groups
        ]
        selected_group_label = st.selectbox("選擇要人工判斷的群組", group_labels, key="model-review-group")
        selected_group = variant_groups[group_labels.index(selected_group_label)]
        st.table([(model, count) for model, count in selected_group["variants"]])
        variant_models = [model for model, _ in selected_group["variants"]]

        with st.form("model-review-decision"):
            canonical = st.text_input("建議 canonical_model", selected_group["canonical"])
            decision = st.radio(
                "人工判定",
                ["先不處理", "合併", "改 canonical_model", "不可合併"],
                horizontal=True,
            )
            note = st.text_area("人工備註", placeholder="例如 HD800 與 HD800S 不合併；HD 800 S 可併到 HD800S")
            submitted = st.form_submit_button("產生本次草稿")
            applied = st.form_submit_button(
                "確認合併並套用",
                type="primary",
                disabled=decision not in ("合併", "改 canonical_model"),
            )

        if submitted or applied:
            variants = ", ".join(variant_models)
            st.session_state.model_review_draft = "\n".join(
                [
                    f"品牌：{display_brand(brand)}",
                    f"原始寫法：{variants}",
                    f"人工判定：{decision}",
                    f"canonical_model：{canonical.strip()}",
                    f"備註：{note.strip()}",
                ]
            )
        if applied:
            snapshot = snapshot_model_merge(state, brand, variant_models, canonical)
            changed = apply_model_merge(state, brand, variant_models, canonical)
            if changed:
                remember_model_merge(snapshot)
                save_state(state)
                st.success(f"已套用合併，更新 {changed} 筆設備型號。")
                st.rerun()
            else:
                st.warning("沒有可更新的型號，請確認 canonical_model 與原始寫法。")

    st.markdown("#### Google AI 第一輪建議")
    prompt = build_model_ai_prompt(brand, devices)
    with st.expander("查看送給 Google AI 的 Prompt"):
        st.text_area("Prompt", value=prompt, height=360, key=f"model-ai-prompt-preview-{brand['id']}")

    api_key = google_api_key()
    key_ok, key_message = google_api_key_status(api_key)
    model_name = st.selectbox("Google 模型", ["gemini-2.5-flash", "gemini-2.0-flash"], key="model-ai-name")
    if key_ok:
        st.caption(key_message)
    else:
        st.warning(f"{key_message} 你仍可先複製 Prompt 手動貼到 AI 工具。")
    if st.button("請 Google AI 產生型號合併建議", disabled=not key_ok):
        suggestion, error = ask_google_for_model_suggestions(prompt, model_name, api_key)
        if error:
            st.error(error)
        else:
            st.session_state.model_ai_suggestion = suggestion
            st.session_state["model-ai-suggestion-input"] = suggestion
            st.success("已產生 Google AI 建議。")

    suggestion_text = st.text_area(
        "Google AI 建議 / 手動貼上建議",
        height=300,
        key="model-ai-suggestion-input",
    )
    st.session_state.model_ai_suggestion = suggestion_text

    if st.session_state.get("model_review_draft"):
        st.markdown("#### 本次人工對照草稿")
        st.code(st.session_state.model_review_draft, language="text")


def render_brand_admin(state: dict) -> None:
    st.subheader("品牌管理")
    pending = pending_brands(state)
    st.markdown("#### 待確認品牌")
    if not pending:
        st.info("目前沒有待確認品牌。")
    for brand in pending:
        with st.expander(brand.get("englishName", "")):
            english = st.text_input("英文/原文名稱", brand.get("englishName", ""), key=f"pending-en-{brand['id']}")
            chinese = st.text_input("中文名稱", brand.get("chineseName", ""), key=f"pending-zh-{brand['id']}")
            aliases = st.text_input(
                "Alias",
                ", ".join(brand.get("aliases", [])),
                key=f"pending-aliases-{brand['id']}",
            )
            cols = st.columns(2)
            if cols[0].button("通過", key=f"approve-{brand['id']}"):
                brand["englishName"] = english.strip() or brand["englishName"]
                brand["chineseName"] = chinese.strip()
                brand["aliases"] = unique_values(aliases.split(","))
                brand["status"] = "approved"
                next_name = display_brand(brand)
                for entry in state["entries"]:
                    for device in entry.get("devices", []):
                        if device.get("brandId") == brand["id"]:
                            device["brandName"] = next_name
                save_state(state)
                st.rerun()
            if cols[1].button("拒絕", key=f"reject-{brand['id']}"):
                brand["status"] = "rejected"
                save_state(state)
                st.rerun()

    st.markdown("#### 新增正式品牌")
    with st.form("add_brand"):
        english = st.text_input("英文/原文名稱")
        chinese = st.text_input("中文名稱")
        aliases = st.text_input("Alias，用逗號分隔")
        if st.form_submit_button("新增品牌"):
            if not english.strip():
                st.warning("請填寫品牌名稱。")
            elif find_brand(state, english):
                st.warning("這個品牌已存在。")
            else:
                state["brands"].append(
                    {
                        "id": next_brand_id(state),
                        "englishName": english.strip(),
                        "chineseName": chinese.strip(),
                        "aliases": unique_values(aliases.split(",")),
                        "status": "approved",
                    }
                )
                save_state(state)
                st.success("已新增品牌。")

    render_approved_brand_directory(state)


def merge_pending_brand(state: dict, pending_brand: dict, target_brand: dict) -> None:
    target_brand["aliases"] = unique_values(
        [
            *target_brand.get("aliases", []),
            pending_brand.get("englishName", ""),
            pending_brand.get("chineseName", ""),
            *pending_brand.get("aliases", []),
        ]
    )
    for entry in state["entries"]:
        for device in entry.get("devices", []):
            if device.get("brandId") == pending_brand.get("id"):
                device["brandId"] = target_brand["id"]
                device["brandName"] = display_brand(target_brand)
    pending_brand["status"] = "merged"
    pending_brand["updatedAt"] = now_iso()


def render_brand_admin(state: dict) -> None:
    st.subheader("品牌管理")
    pending = sorted(
        pending_brands(state),
        key=lambda brand: brand.get("createdAt") or brand.get("updatedAt", ""),
        reverse=True,
    )
    st.markdown("#### 待審品牌")
    if not pending:
        st.info("目前沒有待審品牌。")

    approved = approved_brands(state)
    approved_options = ["審核為新品牌"] + [display_brand(brand) for brand in approved]

    for brand in pending:
        with st.expander(brand.get("englishName", "")):
            english = st.text_input("英文/原文名稱", brand.get("englishName", ""), key=f"pending-en-{brand['id']}")
            chinese = st.text_input("中文名稱", brand.get("chineseName", ""), key=f"pending-zh-{brand['id']}")
            aliases = st.text_input(
                "Alias",
                ", ".join(brand.get("aliases", [])),
                key=f"pending-aliases-{brand['id']}",
            )
            merge_choice = st.selectbox("合併到既有品牌", approved_options, key=f"pending-merge-{brand['id']}")
            cols = st.columns(2)
            if cols[0].button("通過", key=f"approve-{brand['id']}"):
                if merge_choice != "審核為新品牌":
                    target = approved[approved_options.index(merge_choice) - 1]
                    merge_pending_brand(state, brand, target)
                else:
                    brand["englishName"] = english.strip() or brand["englishName"]
                    brand["chineseName"] = chinese.strip()
                    brand["aliases"] = unique_values(aliases.split(","))
                    brand["status"] = "approved"
                    brand["updatedAt"] = now_iso()
                    next_name = display_brand(brand)
                    for entry in state["entries"]:
                        for device in entry.get("devices", []):
                            if device.get("brandId") == brand["id"]:
                                device["brandName"] = next_name
                save_state(state)
                st.rerun()
            if cols[1].button("拒絕", key=f"reject-{brand['id']}"):
                brand["status"] = "rejected"
                brand["updatedAt"] = now_iso()
                save_state(state)
                st.rerun()

    st.markdown("#### 新增正式品牌")
    with st.form("add_brand"):
        english = st.text_input("英文/原文名稱")
        chinese = st.text_input("中文名稱")
        aliases = st.text_input("Alias，用逗號分隔")
        if st.form_submit_button("新增品牌"):
            if not english.strip():
                st.warning("請填寫品牌名稱。")
            elif find_brand(state, english):
                st.warning("這個品牌已存在。")
            else:
                state["brands"].append(
                    {
                        "id": next_brand_id(state),
                        "englishName": english.strip(),
                        "chineseName": chinese.strip(),
                        "aliases": unique_values(aliases.split(",")),
                        "status": "approved",
                        "createdAt": now_iso(),
                        "updatedAt": now_iso(),
                    }
                )
                save_state(state)
                st.success("已新增品牌。")

    render_approved_brand_directory(state)


def render_admin(state: dict) -> None:
    st.subheader("後台")
    brand_tab, model_tab = st.tabs(["品牌管理", "型號合併"])
    with brand_tab:
        render_brand_admin(state)
    with model_tab:
        render_model_review(state)


def main() -> None:
    st.set_page_config(page_title="巴哈耳機普查", layout="wide")
    inject_styles()
    ensure_session_defaults()
    state = load_state()
    requested_page = st.session_state.pop("requested_page", None)
    if requested_page:
        st.session_state.active_page = requested_page

    st.title("巴哈耳機普查")
    st.caption("2026 Bahamut Audio Census")
    storage_mode = st.session_state.get("storage_mode", "本機 JSON fallback")
    st.caption(f"資料儲存：{storage_mode}")
    if st.session_state.get("storage_ok") is False and st.session_state.get("storage_message"):
        st.caption(f"最近錯誤：{st.session_state.get('storage_message')}")

    page_options = ["填寫", "查詢/編輯", "紀錄", "統計", "後台"]
    page = st.segmented_control(
        "目前頁面",
        page_options,
        key="active_page",
    )
    page = page or st.session_state.active_page
    if page == "填寫":
        render_form(state)
    elif page == "查詢/編輯":
        render_history(state)
    elif page == "紀錄":
        render_records(state)
    elif page == "統計":
        render_stats(state)
    elif page == "後台":
        render_admin(state)


ADMIN_PASSWORD = "Lastcoffee"
_render_admin_impl = render_admin


@st.dialog("請輸入管理員密碼")
def prompt_admin_password():
    st.write("請輸入管理員密碼")
    with st.form("admin_password_form", clear_on_submit=False):
        password = st.text_input("管理員密碼", type="password", key="admin_password_input")
        submitted = st.form_submit_button("確認")
        if submitted:
            if password == ADMIN_PASSWORD:
                st.session_state.admin_unlocked = True
                st.session_state.admin_password_error = False
                st.rerun()
            else:
                st.session_state.admin_password_error = True
                st.error("密碼輸入錯誤，無法訪問後台")


def render_admin(state):
    if not st.session_state.get("admin_unlocked", False):
        prompt_admin_password()
        return
    _render_admin_impl(state)


if __name__ == "__main__":
    main()
