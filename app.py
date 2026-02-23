import json
import math
from pathlib import Path
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(page_title="日本株 25日移動平均線乖離率", layout="wide")
st.title("日本株 25日移動平均線乖離率ダッシュボード")

# ──────────────────────────────────────────
# 銘柄マスター（日経225 + TOPIX500 主要銘柄 約200銘柄）
# ──────────────────────────────────────────
STOCK_LIST: dict[str, str] = {
    # ── 建設 ──
    "1721": "コムシスHD",
    "1801": "大成建設",
    "1802": "大林組",
    "1803": "清水建設",
    "1808": "長谷工コーポレーション",
    "1812": "鹿島建設",
    "1925": "大和ハウス工業",
    "1928": "積水ハウス",
    # ── 食料品 ──
    "1332": "ニッスイ",
    "1333": "マルハニチロ",
    "2002": "日清製粉G本社",
    "2201": "森永製菓",
    "2269": "明治HD",
    "2282": "日本ハム",
    "2501": "サッポロHD",
    "2502": "アサヒグループHD",
    "2503": "キリンHD",
    "2531": "宝HD",
    "2593": "伊藤園",
    "2801": "キッコーマン",
    "2802": "味の素",
    "2871": "ニチレイ",
    "2897": "日清食品HD",
    "2914": "JT",
    # ── 繊維 ──
    "3101": "東洋紡",
    "3402": "東レ",
    "3407": "旭化成",
    # ── パルプ・紙 ──
    "3861": "王子HD",
    "3863": "日本製紙",
    # ── 化学 ──
    "3436": "SUMCO",
    "4004": "レゾナック・HD",
    "4005": "住友化学",
    "4021": "日産化学",
    "4042": "東ソー",
    "4043": "トクヤマ",
    "4061": "デンカ",
    "4063": "信越化学工業",
    "4151": "協和キリン",
    "4183": "三井化学",
    "4188": "三菱ケミカルG",
    "4208": "UBE",
    "4452": "花王",
    "4631": "DIC",
    # ── 医薬品 ──
    "4502": "武田薬品工業",
    "4503": "アステラス製薬",
    "4506": "住友ファーマ",
    "4507": "塩野義製薬",
    "4519": "中外製薬",
    "4523": "エーザイ",
    "4543": "テルモ",
    "4568": "第一三共",
    "4578": "大塚HD",
    # ── 石油・石炭 ──
    "1605": "INPEX",
    "5020": "ENEOSホールディングス",
    # ── ゴム ──
    "5101": "横浜ゴム",
    "5108": "ブリヂストン",
    # ── ガラス・土石 ──
    "5201": "AGC",
    "5214": "日本電気硝子",
    "5232": "住友大阪セメント",
    "5233": "太平洋セメント",
    "5332": "TOTO",
    "5333": "日本ガイシ",
    # ── 鉄鋼 ──
    "5301": "東海カーボン",
    "5401": "日本製鉄",
    "5406": "神戸製鋼所",
    "5411": "JFEHD",
    # ── 非鉄金属 ──
    "5713": "住友金属鉱山",
    "5714": "DOWAホールディングス",
    "5802": "住友電気工業",
    "5803": "フジクラ",
    # ── 金属製品 ──
    "5901": "東洋製罐グループHD",
    # ── 機械 ──
    "6103": "オークマ",
    "6113": "アマダ",
    "6146": "ディスコ",
    "6201": "豊田自動織機",
    "6273": "SMC",
    "6301": "コマツ",
    "6302": "住友重機械工業",
    "6326": "クボタ",
    "6361": "荏原製作所",
    "6367": "ダイキン工業",
    "6412": "平和",
    "6460": "セガサミーHD",
    "6471": "日本精工",
    "6472": "NTN",
    "6473": "ジェイテクト",
    "6479": "ミネベアミツミ",
    "6586": "マキタ",
    # ── 電気機器 ──
    "6501": "日立製作所",
    "6503": "三菱電機",
    "6504": "富士電機",
    "6506": "安川電機",
    "6526": "ソシオネクスト",
    "6532": "ベイカレントコンサルティング",
    "6594": "ニデック",
    "6645": "オムロン",
    "6674": "GSユアサ",
    "6701": "NEC",
    "6702": "富士通",
    "6723": "ルネサスエレクトロニクス",
    "6724": "セイコーエプソン",
    "6752": "パナソニックHD",
    "6753": "シャープ",
    "6758": "ソニーグループ",
    "6762": "TDK",
    "6770": "アルプスアルパイン",
    "6857": "アドバンテスト",
    "6861": "キーエンス",
    "6869": "シスメックス",
    "6902": "デンソー",
    "6920": "レーザーテック",
    "6925": "ウシオ電機",
    "6952": "カシオ計算機",
    "6954": "ファナック",
    "6963": "ローム",
    "6971": "京セラ",
    "6976": "太陽誘電",
    "6981": "村田製作所",
    "6988": "日東電工",
    # ── 輸送機器・重工 ──
    "7003": "三井E&SHD",
    "7004": "日立造船",
    "7011": "三菱重工業",
    "7012": "川崎重工業",
    "7013": "IHI",
    "7201": "日産自動車",
    "7202": "いすゞ自動車",
    "7203": "トヨタ自動車",
    "7205": "日野自動車",
    "7211": "三菱自動車",
    "7261": "マツダ",
    "7267": "ホンダ",
    "7269": "スズキ",
    "7270": "SUBARU",
    "7272": "ヤマハ発動機",
    # ── 精密機器 ──
    "7309": "シマノ",
    "7731": "ニコン",
    "7733": "オリンパス",
    "7735": "SCREENホールディングス",
    "7741": "HOYA",
    "7751": "キヤノン",
    "7762": "シチズン時計",
    # ── その他製品 ──
    "4661": "オリエンタルランド",
    "7832": "バンダイナムコHD",
    "7911": "TOPPANホールディングス",
    "7912": "大日本印刷",
    "7951": "ヤマハ",
    "7974": "任天堂",
    # ── 電気・ガス ──
    "9501": "東京電力HD",
    "9502": "中部電力",
    "9503": "関西電力",
    "9531": "東京ガス",
    "9532": "大阪ガス",
    # ── 陸運 ──
    "9001": "東武鉄道",
    "9005": "東急",
    "9007": "小田急電鉄",
    "9008": "京王電鉄",
    "9009": "京成電鉄",
    "9020": "東日本旅客鉄道",
    "9021": "西日本旅客鉄道",
    "9022": "東海旅客鉄道",
    "9064": "ヤマトHD",
    "9065": "山九",
    # ── 海運 ──
    "9101": "日本郵船",
    "9104": "商船三井",
    "9107": "川崎汽船",
    # ── 空運 ──
    "9201": "日本航空",
    "9202": "ANAHD",
    # ── 情報・通信 ──
    "2413": "エムスリー",
    "3659": "ネクソン",
    "4307": "野村総合研究所",
    "4324": "電通グループ",
    "4689": "LINEヤフー",
    "4704": "トレンドマイクロ",
    "4751": "サイバーエージェント",
    "4755": "楽天グループ",
    "6098": "リクルートHD",
    "9432": "NTT",
    "9433": "KDDI",
    "9434": "ソフトバンク",
    "9613": "NTTデータグループ",
    "9984": "ソフトバンクグループ",
    # ── 卸売 ──
    "2768": "双日",
    "8001": "伊藤忠商事",
    "8002": "丸紅",
    "8015": "豊田通商",
    "8031": "三井物産",
    "8053": "住友商事",
    "8058": "三菱商事",
    # ── 小売 ──
    "3382": "セブン&アイHD",
    "8267": "イオン",
    "9983": "ファーストリテイリング",
    # ── 銀行 ──
    "8306": "三菱UFJフィナンシャルG",
    "8308": "りそなHD",
    "8309": "三井住友トラストHD",
    "8316": "三井住友フィナンシャルG",
    "8354": "ふくおかFG",
    "8355": "静岡銀行",
    "8411": "みずほフィナンシャルG",
    # ── 証券 ──
    "8473": "SBIホールディングス",
    "8601": "大和証券グループ本社",
    "8604": "野村HD",
    "8697": "日本取引所グループ",
    # ── 保険 ──
    "8630": "SOMPOホールディングス",
    "8725": "MS&ADインシュアランスG",
    "8750": "第一生命HD",
    "8766": "東京海上HD",
    "8795": "T&DホールディングS",
    # ── その他金融 ──
    "8591": "オリックス",
    # ── 不動産 ──
    "3003": "ヒューリック",
    "8801": "三井不動産",
    "8802": "三菱地所",
    "8830": "住友不動産",
    # ── サービス ──
    "2432": "DeNA",
    "3289": "東急不動産HD",
    "4901": "富士フイルムHD",
    "6178": "日本郵政",
    "9602": "東宝",
    "9735": "セコム",
    "9766": "コナミグループ",
    # ── 新興・グロース ──
    "3697": "SHIFT",
    "4385": "メルカリ",
}

# ──────────────────────────────────────────
# セクター別しきい値
# ──────────────────────────────────────────
SECTOR_THRESHOLDS: dict[str, float] = {
    "IT・新興 (-15%)": -15.0,
    "一般 (-10%)": -10.0,
    "鉄鋼・銀行・安定 (-5%)": -5.0,
}

# スキャン1バッチあたりの銘柄数
_SCAN_BATCH_SIZE = 50

# ──────────────────────────────────────────
# ユーティリティ（サイドバーより前に定義が必要）
# ──────────────────────────────────────────

def parse_codes(text: str) -> list[str]:
    codes = []
    for part in text.replace(",", "\n").splitlines():
        code = part.strip()
        if code:
            codes.append(code)
    return list(dict.fromkeys(codes))


def ticker_symbol(code: str) -> str:
    return code if code.endswith(".T") else f"{code}.T"


# ──────────────────────────────────────────
# ウォッチリスト永続化
# ──────────────────────────────────────────

_WATCHLIST_FILE = Path(__file__).parent / "watchlist.json"
_PRESET_OPTIONS = ["カスタム", "ウォッチリスト", "保有銘柄"]
_PRESET_KEYS = {"ウォッチリスト": "watchlist", "保有銘柄": "holdings"}


def _default_presets() -> dict[str, list[str]]:
    return {
        "watchlist": ["7203", "6758", "9984"],
        "holdings": ["8306", "8316", "8411"],
    }


def load_watchlist() -> dict[str, list[str]]:
    """JSON ファイルからプリセットを読み込む。失敗時はデフォルト値を返す。"""
    defaults = _default_presets()
    try:
        if _WATCHLIST_FILE.exists():
            data = json.loads(_WATCHLIST_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                merged = {**defaults}
                for k in ("watchlist", "holdings"):
                    if k in data and isinstance(data[k], list):
                        merged[k] = [str(c) for c in data[k]]
                return merged
    except Exception:
        pass
    return defaults


def save_watchlist(presets: dict[str, list[str]]) -> None:
    """プリセットを JSON ファイルに保存する。"""
    try:
        _WATCHLIST_FILE.write_text(
            json.dumps(presets, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


# ──────────────────────────────────────────
# セッション状態の初期化（サイドバー前）
# ──────────────────────────────────────────

if "wl_presets" not in st.session_state:
    st.session_state.wl_presets = load_watchlist()

if "codes_input" not in st.session_state:
    st.session_state.codes_input = "\n".join(
        st.session_state.wl_presets.get("watchlist", ["7203", "6758", "9984"])
    )


def _on_preset_change() -> None:
    """プリセット切り替え時に銘柄コード入力欄を更新する。"""
    preset = st.session_state.get("preset_radio", "カスタム")
    if preset == "カスタム":
        return
    key = _PRESET_KEYS.get(preset)
    if key:
        codes = st.session_state.wl_presets.get(key, [])
        st.session_state.codes_input = "\n".join(codes)


def _save_preset() -> None:
    """現在の銘柄コードを選択中のプリセットに保存する。"""
    preset = st.session_state.get("preset_radio", "カスタム")
    if preset == "カスタム":
        return
    key = _PRESET_KEYS.get(preset)
    if key:
        codes = parse_codes(st.session_state.get("codes_input", ""))
        st.session_state.wl_presets[key] = codes
        save_watchlist(st.session_state.wl_presets)
        st.session_state["_save_toast"] = preset


# ──────────────────────────────────────────
# サイドバー
# ──────────────────────────────────────────
with st.sidebar:
    st.header("銘柄設定")

    # ── [ウォッチリスト] プリセット選択 ──
    st.caption("プリセット")
    st.radio(
        "プリセット",
        options=_PRESET_OPTIONS,
        key="preset_radio",
        on_change=_on_preset_change,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.divider()

    sector_label = st.selectbox(
        "セクター（ハイライトしきい値）",
        options=list(SECTOR_THRESHOLDS.keys()),
        index=1,
        help="選択したセクターのしきい値で乖離率ハイライトの基準を変えます",
    )

    raw_codes = st.text_area(
        "銘柄コード（複数の場合は改行またはカンマ区切り）",
        key="codes_input",
        height=150,
    )

    # ── [ウォッチリスト] プリセット保存ボタン ──
    _active_preset = st.session_state.get("preset_radio", "カスタム")
    if _active_preset != "カスタム":
        st.button(
            f"💾 {_active_preset}に保存",
            on_click=_save_preset,
            use_container_width=True,
            help="現在の銘柄コードをプリセットに保存します（ブラウザを閉じても保持）",
        )
        # 保存完了トースト（on_click の次のレンダリングで表示）
        if st.session_state.pop("_save_toast", None):
            st.success(f"「{_active_preset}」を保存しました！", icon="💾")

    fetch_btn = st.button("データ取得", type="primary", use_container_width=True)


# ──────────────────────────────────────────
# ヘルパー関数（parse_codes / ticker_symbol はサイドバー前に定義済み）
# ──────────────────────────────────────────

def fetch_data(code: str) -> pd.DataFrame | None:
    symbol = ticker_symbol(code)
    end = datetime.today()
    start = end - timedelta(days=180)
    try:
        df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        # Close は必須、Volume は欠損があっても保持
        cols = [c for c in ["Close", "Volume"] if c in df.columns]
        df = df[cols].dropna(subset=["Close"])
        df["MA25"] = df["Close"].rolling(window=25).mean()
        if "Volume" in df.columns:
            df["VolumeMA20"] = df["Volume"].rolling(window=20).mean()
        return df
    except Exception:
        return None


def calc_deviation(df: pd.DataFrame) -> float | None:
    if df is None or df["MA25"].dropna().empty:
        return None
    latest_close = df["Close"].iloc[-1]
    latest_ma25 = df["MA25"].iloc[-1]
    return (latest_close - latest_ma25) / latest_ma25 * 100


def calc_volume_ratio(df: pd.DataFrame) -> float | None:
    """当日出来高 ÷ 過去20日平均出来高を返す。データ不足時は None。"""
    if df is None or "Volume" not in df.columns or "VolumeMA20" not in df.columns:
        return None
    vol = df["Volume"].dropna()
    vma20 = df["VolumeMA20"].dropna()
    if vol.empty or vma20.empty:
        return None
    latest_vol = float(vol.iloc[-1])
    latest_vma20 = float(vma20.iloc[-1])
    if pd.isna(latest_vma20) or latest_vma20 == 0:
        return None
    return latest_vol / latest_vma20


def calc_day_change(df: pd.DataFrame) -> float | None:
    if df is None:
        return None
    closes = df["Close"].dropna()
    if len(closes) < 2:
        return None
    return float((closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2] * 100)


def fetch_nikkei_change() -> float | None:
    try:
        df = yf.download("^N225", period="5d", progress=False, auto_adjust=True)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        closes = df["Close"].dropna()
        if len(closes) < 2:
            return None
        return float((closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2] * 100)
    except Exception:
        return None


def show_market_condition(nikkei_change: float | None) -> None:
    st.subheader("地合い")
    if nikkei_change is None:
        st.warning("日経平均の取得に失敗しました")
        return
    sign = "+" if nikkei_change >= 0 else ""
    change_str = f"{sign}{nikkei_change:.2f}%"
    if nikkei_change <= -2.0:
        st.error(f"⚠️ パニック相場　日経平均: {change_str}")
    elif nikkei_change <= -1.0:
        st.warning(f"⚡ 注意相場　日経平均: {change_str}")
    else:
        st.success(f"✅ 通常相場　日経平均: {change_str}")


def build_chart(df: pd.DataFrame, code: str) -> go.Figure:
    cutoff = datetime.today() - timedelta(days=90)
    df_3m = df[df.index >= cutoff]

    has_volume = (
        "Volume" in df_3m.columns
        and "VolumeMA20" in df_3m.columns
        and df_3m["Volume"].notna().any()
    )

    if has_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            row_heights=[0.68, 0.32],
            vertical_spacing=0.04,
        )
        # ─ 株価チャート（上段）─
        fig.add_trace(go.Scatter(
            x=df_3m.index, y=df_3m["Close"],
            mode="lines", name="株価",
            line=dict(color="#2196F3", width=1.5),
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df_3m.index, y=df_3m["MA25"],
            mode="lines", name="25日MA",
            line=dict(color="#FF9800", width=2, dash="dot"),
        ), row=1, col=1)

        # ─ 出来高バー（下段）: 急増日は赤、通常は水色 ─
        vols = df_3m["Volume"].fillna(0)
        vma20s = df_3m["VolumeMA20"].fillna(0)
        bar_colors = [
            "#F44336" if (m > 0 and v >= m * 2) else "#90CAF9"
            for v, m in zip(vols, vma20s)
        ]
        fig.add_trace(go.Bar(
            x=df_3m.index, y=vols,
            name="出来高",
            marker_color=bar_colors,
            showlegend=True,
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=df_3m.index, y=df_3m["VolumeMA20"],
            mode="lines", name="出来高20日MA",
            line=dict(color="#FF9800", width=1.5, dash="dash"),
        ), row=2, col=1)

        fig.update_layout(
            title=f"{ticker_symbol(code)} — 過去3ヶ月チャート",
            yaxis_title="株価 (円)",
            yaxis2_title="出来高",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=520, margin=dict(l=0, r=0, t=40, b=0),
            hovermode="x unified",
            bargap=0.1,
        )
        fig.update_xaxes(title_text="日付", row=2, col=1)
    else:
        # 出来高データなし: 既存の単一チャート
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_3m.index, y=df_3m["Close"],
            mode="lines", name="株価",
            line=dict(color="#2196F3", width=1.5),
        ))
        fig.add_trace(go.Scatter(
            x=df_3m.index, y=df_3m["MA25"],
            mode="lines", name="25日MA",
            line=dict(color="#FF9800", width=2, dash="dot"),
        ))
        fig.update_layout(
            title=f"{ticker_symbol(code)} — 過去3ヶ月チャート",
            xaxis_title="日付", yaxis_title="株価 (円)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=400, margin=dict(l=0, r=0, t=40, b=0),
            hovermode="x unified",
        )
    return fig


def scan_all_stocks(
    threshold: float,
    progress_bar,
    status_text,
) -> pd.DataFrame:
    """全銘柄をバッチ取得して乖離率ランキングを返す"""
    codes = list(STOCK_LIST.keys())
    symbols = [ticker_symbol(c) for c in codes]
    results: list[dict] = []

    end = datetime.today()
    start = end - timedelta(days=180)
    total = len(symbols)
    total_batches = math.ceil(total / _SCAN_BATCH_SIZE)

    for batch_idx in range(total_batches):
        i = batch_idx * _SCAN_BATCH_SIZE
        batch_syms = symbols[i : i + _SCAN_BATCH_SIZE]
        batch_codes = codes[i : i + _SCAN_BATCH_SIZE]

        done = min(i + _SCAN_BATCH_SIZE, total)
        status_text.text(f"スキャン中… {done}/{total} 銘柄")

        try:
            raw = yf.download(
                batch_syms,
                start=start,
                end=end,
                auto_adjust=True,
                progress=False,
            )
            if raw.empty:
                progress_bar.progress((batch_idx + 1) / total_batches)
                continue

            # Close / Volume 列を取り出す
            # yfinance 0.2.x マルチティッカー: MultiIndex columns (field, ticker)
            # 単一ティッカー: フラット columns
            def _extract_field(raw_df: pd.DataFrame, field: str, syms: list[str]) -> dict[str, pd.Series]:
                if field not in raw_df.columns and not isinstance(raw_df.columns, pd.MultiIndex):
                    return {}
                try:
                    block = raw_df[field]
                except KeyError:
                    return {}
                if isinstance(block, pd.Series):
                    return {syms[0]: block}
                return {s: block[s] for s in syms if s in block.columns}

            closes_map = _extract_field(raw, "Close", batch_syms)
            volumes_map = _extract_field(raw, "Volume", batch_syms)

            for sym, code in zip(batch_syms, batch_codes):
                if sym not in closes_map:
                    continue
                try:
                    closes = closes_map[sym].dropna()
                    if len(closes) < 26:
                        continue
                    ma25 = float(closes.rolling(25).mean().iloc[-1])
                    latest = float(closes.iloc[-1])
                    if pd.isna(ma25) or pd.isna(latest):
                        continue
                    dev = (latest - ma25) / ma25 * 100

                    # [出来高異常検知] 出来高比率を計算
                    vol_ratio: float | None = None
                    if sym in volumes_map:
                        vols = volumes_map[sym].dropna()
                        if len(vols) >= 21:
                            vma20 = float(vols.rolling(20).mean().iloc[-1])
                            today_vol = float(vols.iloc[-1])
                            if vma20 > 0:
                                vol_ratio = today_vol / vma20

                    results.append({
                        "コード": sym,
                        "銘柄名": STOCK_LIST.get(code, code),
                        "現在株価 (円)": latest,
                        "25日MA (円)": ma25,
                        "乖離率 (%)": dev,
                        "出来高比率": vol_ratio,
                    })
                except Exception:
                    continue

        except Exception:
            pass

        progress_bar.progress((batch_idx + 1) / total_batches)

    status_text.empty()

    if not results:
        return pd.DataFrame()

    result_df = (
        pd.DataFrame(results)
        .sort_values("乖離率 (%)")
        .reset_index(drop=True)
    )
    result_df.insert(0, "順位", range(1, len(result_df) + 1))
    return result_df


def show_scan_results(df: pd.DataFrame, threshold: float) -> None:
    """スキャン結果テーブルを表示（上位20 + 残り折りたたみ）"""
    if df.empty:
        st.warning("スキャン結果を取得できませんでした。しばらくしてから再試行してください。")
        return

    st.success(f"スキャン完了: {len(df)} 銘柄取得")

    _VOL_SURGE_THRESHOLD = 2.0

    def highlight_scan_row(row):
        dev = row.get("乖離率 (%)", None)
        vol = row.get("出来高比率", None)
        dev_hit = isinstance(dev, float) and dev <= threshold
        vol_hit = isinstance(vol, float) and vol >= _VOL_SURGE_THRESHOLD
        if dev_hit and vol_hit:
            # 乖離率しきい値以下 かつ 出来高急増 → 特強調（アンバー）
            return ["background-color: #FF6F00; color: #FFFFFF; font-weight: bold"] * len(row)
        if dev_hit:
            # 乖離率しきい値以下のみ → 赤
            return ["background-color: #FFCDD2; color: #B71C1C; font-weight: bold"] * len(row)
        return [""] * len(row)

    def fmt_vol_ratio(x) -> str:
        if not isinstance(x, float):
            return "—"
        badge = "🔥 " if x >= _VOL_SURGE_THRESHOLD else ""
        return f"{badge}{x:.2f}x"

    def styled_table(df_part: pd.DataFrame):
        fmt: dict = {
            "現在株価 (円)": "{:,.0f}",
            "25日MA (円)": "{:,.2f}",
            "乖離率 (%)": lambda x: f"{x:+.2f}%" if isinstance(x, float) else "—",
        }
        if "出来高比率" in df_part.columns:
            fmt["出来高比率"] = fmt_vol_ratio
        return df_part.style.apply(highlight_scan_row, axis=1).format(fmt)

    top_n = 20
    top_df = df.head(top_n)
    rest_df = df.iloc[top_n:]

    st.subheader(f"乖離率ランキング — 上位 {top_n} 銘柄")
    st.dataframe(styled_table(top_df), use_container_width=True, hide_index=True)

    if not rest_df.empty:
        with st.expander(f"残り {len(rest_df)} 銘柄を表示"):
            st.dataframe(styled_table(rest_df), use_container_width=True, hide_index=True)

    st.caption(
        f"※ セクター: **{sector_label}** — "
        f"乖離率 {threshold:.0f}% 以下は赤、"
        f"さらに出来高比率 {_VOL_SURGE_THRESHOLD:.0f}x 以上はアンバーで強調表示。"
    )


# ──────────────────────────────────────────
# メイン — タブ構造
# ──────────────────────────────────────────
tab1, tab2 = st.tabs(["📊 個別チャート", "🔍 銘柄スキャナー"])

# ════════════════════════════════
# Tab 1: 個別チャート（既存機能）
# ════════════════════════════════
with tab1:
    if fetch_btn:
        codes = parse_codes(raw_codes)
        if not codes:
            st.warning("銘柄コードを入力してください。")
            st.stop()

        DEVIATION_THRESHOLD = SECTOR_THRESHOLDS[sector_label]

        summary_rows = []
        chart_data: dict[str, tuple[pd.DataFrame, float, float | None, float | None]] = {}

        with st.spinner("データ取得中..."):
            nikkei_change = fetch_nikkei_change()

            for code in codes:
                df = fetch_data(code)
                dev = calc_deviation(df)
                day_change = calc_day_change(df)
                vol_ratio = calc_volume_ratio(df)  # [出来高異常検知]

                if df is not None and dev is not None:
                    latest_close = float(df["Close"].iloc[-1])
                    latest_ma25 = float(df["MA25"].iloc[-1])
                    summary_rows.append({
                        "コード": ticker_symbol(code),
                        "現在株価 (円)": f"{latest_close:,.0f}",
                        "25日MA (円)": f"{latest_ma25:,.0f}",
                        "乖離率 (%)": dev,
                    })
                    chart_data[code] = (df, dev, day_change, vol_ratio)
                else:
                    summary_rows.append({
                        "コード": ticker_symbol(code),
                        "現在株価 (円)": "取得失敗",
                        "25日MA (円)": "—",
                        "乖離率 (%)": None,
                    })

        # 地合い表示
        show_market_condition(nikkei_change)
        st.divider()

        # サマリーテーブル
        st.subheader("乖離率サマリー")

        def highlight_row(row):
            dev = row["乖離率 (%)"]
            if isinstance(dev, float) and dev <= DEVIATION_THRESHOLD:
                return ["background-color: #FFCDD2; color: #B71C1C; font-weight: bold"] * len(row)
            return [""] * len(row)

        summary_df = pd.DataFrame(summary_rows)
        styled = (
            summary_df.style
            .apply(highlight_row, axis=1)
            .format({"乖離率 (%)": lambda x: f"{x:+.2f}%" if isinstance(x, float) else "—"})
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)
        st.caption(
            f"※ セクター: **{sector_label}** — 乖離率が {DEVIATION_THRESHOLD:.0f}% 以下の銘柄を赤くハイライトします。"
        )

        # 個別チャート
        st.subheader("個別チャート（過去3ヶ月）")
        nikkei_declining = nikkei_change is not None and nikkei_change <= -1.0

        for code, (df, dev, day_change, vol_ratio) in chart_data.items():
            vol_surge = vol_ratio is not None and vol_ratio >= 2.0
            # エキスパンダーヘッダーにバッジを付与
            header_badges = ""
            if vol_surge:
                header_badges += "  🔥"
            if nikkei_declining and day_change is not None and day_change < 0:
                header_badges += "  📌"
            with st.expander(
                f"{ticker_symbol(code)}　乖離率: {dev:+.2f}%{header_badges}",
                expanded=True,
            ):
                col_left, col_right = st.columns([3, 1])
                with col_left:
                    if dev <= DEVIATION_THRESHOLD:
                        st.error(f"乖離率 {dev:+.2f}% — 25日MAを {abs(dev):.2f}% 下回っています")
                    else:
                        st.info(f"乖離率 {dev:+.2f}%")
                with col_right:
                    # [出来高異常検知] 急増バッジ
                    if vol_surge:
                        ratio_str = f"{vol_ratio:.2f}x" if vol_ratio is not None else ""
                        st.error(f"🔥 出来高急増\n({ratio_str})")
                    if nikkei_declining and day_change is not None and day_change < 0:
                        st.warning("📌 連れ安の可能性あり")
                st.plotly_chart(build_chart(df, code), use_container_width=True)

    else:
        st.info("左のサイドバーに銘柄コードを入力して「データ取得」を押してください。")

# ════════════════════════════════
# Tab 2: 銘柄スキャナー（新機能）
# ════════════════════════════════
with tab2:
    DEVIATION_THRESHOLD = SECTOR_THRESHOLDS[sector_label]

    st.subheader("🔍 銘柄スキャナー")

    col_info1, col_info2, col_btn = st.columns([2, 2, 1])
    with col_info1:
        st.metric("対象銘柄数", f"{len(STOCK_LIST)} 銘柄")
    with col_info2:
        st.metric("ハイライトしきい値", f"{DEVIATION_THRESHOLD:.0f}%（{sector_label}）")
    with col_btn:
        scan_btn = st.button(
            "🚀 スキャン開始",
            type="primary",
            use_container_width=True,
            help="全銘柄の25日乖離率を一括取得します（30〜60秒程度かかります）",
        )

    st.divider()

    if scan_btn:
        # セッション状態をリセットしてスキャン実行
        st.session_state.scan_results = None
        st.session_state.scan_threshold = DEVIATION_THRESHOLD

        progress_bar = st.progress(0)
        status_text = st.empty()

        with st.spinner("スキャン中... しばらくお待ちください"):
            st.session_state.scan_results = scan_all_stocks(
                DEVIATION_THRESHOLD, progress_bar, status_text
            )

        progress_bar.empty()

    # キャッシュされた結果を表示
    if st.session_state.get("scan_results") is not None:
        cached_threshold = st.session_state.get("scan_threshold", DEVIATION_THRESHOLD)
        if cached_threshold != DEVIATION_THRESHOLD:
            st.info(
                f"表示中の結果はしきい値 **{cached_threshold:.0f}%** でスキャンしたものです。"
                "セクターを変更した場合は再スキャンしてください。"
            )
        show_scan_results(st.session_state.scan_results, cached_threshold)
    else:
        st.info("「スキャン開始」を押すと全銘柄の乖離率ランキングを表示します。")
