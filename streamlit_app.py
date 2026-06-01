from __future__ import annotations

import csv
import io
import json
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
STATE_FILE = DATA_DIR / "census.json"

DEVICE_TYPES = [
    "耳道式耳機",
    "耳罩式耳機",
    "平板耳機",
    "DAC",
    "耳擴",
    "DAC/耳擴一體機",
    "DAP / 隨身播放器",
    "小尾巴",
    "線材",
    "其他",
]

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


def load_state() -> dict:
    if "state" in st.session_state:
        return st.session_state.state
    if STATE_FILE.exists():
        try:
            state = normalize_state(json.loads(STATE_FILE.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            state = normalize_state({})
    else:
        state = normalize_state({})
    st.session_state.state = state
    return state


def save_state(state: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    st.session_state.state = state


def approved_brands(state: dict) -> list[dict]:
    return [brand for brand in state["brands"] if brand.get("status") == "approved"]


def pending_brands(state: dict) -> list[dict]:
    return [brand for brand in state["brands"] if brand.get("status") == "pending"]


def find_brand(state: dict, query: str) -> dict | None:
    needle = normalize(query)
    for brand in state["brands"]:
        if brand.get("status") == "rejected":
            continue
        values = [
            brand.get("englishName", ""),
            brand.get("chineseName", ""),
            display_brand(brand),
            *brand.get("aliases", []),
        ]
        if any(normalize(value) == needle for value in values):
            return brand
    return None


def create_pending_brand(state: dict, raw_name: str) -> dict:
    brand = {
        "id": create_id(),
        "englishName": raw_name,
        "chineseName": "",
        "aliases": [raw_name],
        "status": "pending",
    }
    state["brands"].append(brand)
    return brand


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


def rank_rows(items: list[dict], key: str, limit: int = 10) -> list[tuple[str, int]]:
    counts = Counter(str(item.get(key, "")).strip() for item in items if item.get(key))
    return counts.most_common(limit)


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

    with st.form("device_form", clear_on_submit=True):
        cols = st.columns([1, 1, 1])
        device_type = cols[0].selectbox("設備類型", DEVICE_TYPES)
        brand_options = [display_brand(brand) for brand in approved_brands(state)]
        brand_name = cols[1].selectbox("品牌", [""] + brand_options, index=0)
        custom_brand = cols[1].text_input("清單沒有？輸入新品牌")
        model = cols[2].text_input("型號", placeholder="例如 HA-FW02、HD800S、K9 Pro")
        note = st.text_input("設備備註", placeholder="例如 改線、常用搭配、版本")
        submitted = st.form_submit_button("加入設備")

    if submitted:
        picked_brand = custom_brand.strip() or brand_name.strip()
        if not picked_brand or not model.strip():
            st.warning("請填寫品牌與型號。")
        else:
            brand = find_brand(state, picked_brand) or create_pending_brand(state, picked_brand)
            st.session_state.devices.append(
                {
                    "id": create_id(),
                    "type": device_type,
                    "brandId": brand["id"],
                    "brandName": display_brand(brand),
                    "model": model.strip(),
                    "note": note.strip(),
                }
            )
            save_state(state)
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
    bahamut_id = st.text_input("巴哈 ID", key="bahamut_id")
    general_note = st.text_area("補充備註", key="general_note")

    if st.button("送出並產生貼文", type="primary"):
        if not bahamut_id.strip():
            st.warning("請填寫巴哈 ID。")
            return
        if not st.session_state.devices:
            st.warning("請至少加入一項設備。")
            return

        now = now_iso()
        entry = {
            "id": st.session_state.editing_entry_id or create_id(),
            "bahamutId": bahamut_id.strip(),
            "generalNote": general_note.strip(),
            "devices": [dict(device) for device in st.session_state.devices],
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

        save_state(state)
        st.session_state.last_post = build_post(entry)
        st.session_state.devices = []
        st.session_state.editing_entry_id = None
        st.success("已儲存，貼文已產生。")

    if st.session_state.last_post:
        st.text_area("貼文內容", value=st.session_state.last_post, height=360)


def render_history(state: dict) -> None:
    st.subheader("查詢 / 編輯自己的紀錄")
    bahamut_id = st.text_input("輸入巴哈 ID 查詢", key="history_bahamut_id")
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
    for entry in matches:
        with st.expander(f"{entry.get('bahamutId')}｜{len(entry.get('devices', []))} 項設備｜{entry.get('updatedAt', '')}"):
            st.code(build_post(entry), language="text")
            cols = st.columns(2)
            if cols[0].button("載入編輯", key=f"edit-{entry['id']}"):
                st.session_state.pending_edit_entry_id = entry["id"]
                st.rerun()
            if cols[1].button("刪除", key=f"delete-{entry['id']}"):
                state["entries"] = [item for item in state["entries"] if item.get("id") != entry["id"]]
                save_state(state)
                st.rerun()


def render_stats(state: dict) -> None:
    st.subheader("統計")
    devices = flatten_devices(state)
    cols = st.columns(4)
    cols[0].metric("填寫紀錄", len(state["entries"]))
    cols[1].metric("設備總數", len(devices))
    cols[2].metric("正式品牌", len(approved_brands(state)))
    cols[3].metric("待確認品牌", len(pending_brands(state)))

    left, right = st.columns(2)
    left.markdown("#### 類型排名")
    left.table(rank_rows(devices, "type"))
    right.markdown("#### 品牌排名")
    right.table(rank_rows(devices, "brandName"))

    st.markdown("#### 型號排名")
    model_rows = Counter(
        f"{device.get('brandName', '')} {device.get('model', '')}".strip()
        for device in devices
        if device.get("model")
    ).most_common(10)
    st.table(model_rows)

    st.download_button("下載 CSV", state_to_csv(state), "bahamut-audio-census.csv", "text/csv")
    st.download_button(
        "下載 JSON",
        json.dumps(state, ensure_ascii=False, indent=2),
        "bahamut-audio-census.json",
        "application/json",
    )


def render_admin(state: dict) -> None:
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
                        "id": create_id(),
                        "englishName": english.strip(),
                        "chineseName": chinese.strip(),
                        "aliases": unique_values(aliases.split(",")),
                        "status": "approved",
                    }
                )
                save_state(state)
                st.success("已新增品牌。")

    st.markdown("#### 正式品牌清單")
    st.table([(display_brand(brand), ", ".join(brand.get("aliases", []))) for brand in approved_brands(state)])


def main() -> None:
    st.set_page_config(page_title="巴哈耳機普查", layout="wide")
    ensure_session_defaults()
    state = load_state()

    st.title("巴哈耳機普查")
    st.caption("2026 Bahamut Audio Census")

    tabs = st.tabs(["填寫", "查詢/編輯", "統計", "後台"])
    with tabs[0]:
        render_form(state)
    with tabs[1]:
        render_history(state)
    with tabs[2]:
        render_stats(state)
    with tabs[3]:
        render_admin(state)


if __name__ == "__main__":
    main()
