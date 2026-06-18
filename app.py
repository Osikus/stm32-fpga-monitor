import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI



# =========================================================
# 配置
# =========================================================

CSV_FILE = "data.csv"

# 偏离历史均值超过判为异常
DEFAULT_TEMP_THRESHOLD = 1.0

# 页面刷新只负责更新实时数据，不会自动调用 DeepSeek
PAGE_REFRESH_SECONDS = 5

# DeepSeek 模型
DEEPSEEK_MODEL = "deepseek-v4-flash"


load_dotenv()

DEEPSEEK_API_KEY = os.getenv(
    "DEEPSEEK_API_KEY",
    ""
).strip()

if not DEEPSEEK_API_KEY:
    try:
        DEEPSEEK_API_KEY = st.secrets[
            "DEEPSEEK_API_KEY"
        ]
    except Exception:
        DEEPSEEK_API_KEY = ""




st.set_page_config(
    page_title="环境温湿度智能监测系统",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# CSS 页面样式
# =========================================================

st.markdown(
    """
    <style>
    /* 整体背景 */
    .stApp {
        background-color: #eeeeee;
    }

    .block-container {
    max-width: 1320px;
    padding-top: 45px;
    padding-bottom: 45px;
    }

    /* 隐藏 Streamlit 默认元素 */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background-color: transparent;
    }

    .main-title {
    color: #202124;
    font-size: 2.25rem;
    font-weight: 800;
    line-height: 1.35;
    padding-top: 8px;
    padding-bottom: 4px;
    margin: 0 0 4px 0;
    overflow: visible;
}

    .main-subtitle {
        color: #777777;
        font-size: 0.95rem;
        margin-bottom: 26px;
    }

    /* 分区标题 */
    .section-title {
        color: #292929;
        font-size: 1.35rem;
        font-weight: 750;
        margin-top: 10px;
        margin-bottom: 14px;
    }

    /* 四个实时数据卡片 */
    .metric-card {
        height: 172px;
        box-sizing: border-box;
        background-color: #ffffff;
        border: 1px solid #dedede;
        border-radius: 16px;
        padding: 23px 25px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.035);

        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .metric-name {
        color: #777777;
        font-size: 0.95rem;
        font-weight: 500;
    }

    .metric-value {
        color: #202938;
        font-size: 2rem;
        font-weight: 750;
        line-height: 1.15;
    }

    .metric-note {
        color: #929292;
        font-size: 0.8rem;
        line-height: 1.4;
    }

    .status-normal {
        color: #168342;
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.15;
    }

    .status-abnormal {
        color: #c62828;
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.15;
    }

    .status-learning {
        color: #b56b00;
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.15;
    }

    /* 通用白色面板 */
    .panel-header {
        background-color: #ffffff;
        border: 1px solid #dedede;
        border-bottom: none;
        border-radius: 16px 16px 0 0;
        padding: 22px 25px 10px 25px;
        margin-top: 12px;
    }

    .panel-title {
        color: #292929;
        font-size: 1.28rem;
        font-weight: 750;
    }

    .panel-description {
        color: #858585;
        font-size: 0.85rem;
        margin-top: 5px;
    }

    /* AI 状态标签 */
    .ai-connected {
        display: inline-block;
        background-color: #edf7f0;
        color: #257044;
        border: 1px solid #d7eadc;
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 0.82rem;
        margin-bottom: 8px;
    }

    .ai-disconnected {
        display: inline-block;
        background-color: #f6f1e8;
        color: #8b641c;
        border: 1px solid #eadfc9;
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 0.82rem;
        margin-bottom: 8px;
    }

    /* AI 内容区域 */
    .ai-placeholder {
        background-color: #ffffff;
        border: 1px solid #dedede;
        border-radius: 14px;
        padding: 28px;
        color: #888888;
        line-height: 1.8;
        min-height: 95px;
    }

    /* 按钮 */
    .stButton > button {
        border-radius: 10px;
        border: 1px solid #cfcfcf;
        background-color: #ffffff;
        color: #333333;
        min-height: 43px;
        font-weight: 600;
    }

    .stButton > button:hover {
        border-color: #777777;
        color: #111111;
        background-color: #fafafa;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 9px;
        padding-left: 18px;
        padding-right: 18px;
    }

    /* 图表及表格 */
    [data-testid="stDataFrame"] {
        background-color: #ffffff;
        border: 1px solid #dedede;
        border-radius: 13px;
        overflow: hidden;
    }

    [data-testid="stArrowVegaLiteChart"],
    [data-testid="stPlotlyChart"] {
        background-color: #ffffff;
        border: 1px solid #dedede;
        border-radius: 13px;
        padding: 10px;
    }

    /* 输入控件 */
    [data-baseweb="select"] > div,
    [data-baseweb="input"] {
        background-color: #ffffff;
        border-radius: 9px;
    }

    /* 让四列顶部完全对齐 */
    [data-testid="stHorizontalBlock"] {
        align-items: stretch;
    }

    /* 减小某些 Streamlit 默认间距 */
    div[data-testid="stVerticalBlock"] {
        gap: 0.8rem;
    }
    
    
    .stApp,
    .stApp p,
    .stApp span,
    .stApp div,
 .stApp label,
 .stApp li {
    color: #262626;
 }

 /* 普通 Markdown 标题和正文 */
 [data-testid="stMarkdownContainer"] {
    color: #262626 !important;
 }

 [data-testid="stMarkdownContainer"] p,
 [data-testid="stMarkdownContainer"] li,
 [data-testid="stMarkdownContainer"] strong,
 [data-testid="stMarkdownContainer"] h1,
 [data-testid="stMarkdownContainer"] h2,
 [data-testid="stMarkdownContainer"] h3,
 [data-testid="stMarkdownContainer"] h4 {
    color: #262626 !important;
 }

 /* Streamlit 控件上方的标签 */
 [data-testid="stWidgetLabel"] p,
 [data-testid="stWidgetLabel"] label {
    color: #444444 !important;
 }

 /* 下拉选择框 */
 div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    color: #262626 !important;
    border-color: #bdbdbd !important;
 }

 div[data-baseweb="select"] span {
    color: #262626 !important;
 }

 /* 下拉框打开后的菜单 */
 div[data-baseweb="popover"],
 div[data-baseweb="menu"] {
    background-color: #ffffff !important;
 }

 div[data-baseweb="menu"] li,
 div[role="option"] {
    color: #262626 !important;
    background-color: #ffffff !important;
 }

 div[role="option"]:hover {
    background-color: #f1f1f1 !important;
 }

 /* 文本输入框 */
 input {
    background-color: #ffffff !important;
    color: #262626 !important;
    -webkit-text-fill-color: #262626 !important;
 }

 input::placeholder {
    color: #999999 !important;
    -webkit-text-fill-color: #999999 !important;
 }

 /* Caption 小字 */
 [data-testid="stCaptionContainer"],
 [data-testid="stCaptionContainer"] p {
    color: #777777 !important;
 }

 /* AI 分析结果 */
 .ai-result {
    background-color: #ffffff;
    color: #262626 !important;
    border: 1px solid #dedede;
    border-radius: 14px;
    padding: 22px 26px;
    line-height: 1.8;
 }

 .ai-result h1,
 .ai-result h2,
 .ai-result h3,
 .ai-result h4,
 .ai-result p,
 .ai-result li,
 .ai-result strong {
    color: #262626 !important;
 }

 /* 下载按钮等次要按钮 */
 .stDownloadButton > button {
    background-color: #ffffff !important;
    color: #333333 !important;
    border: 1px solid #cfcfcf !important;
 }




    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 数据处理函数
# =========================================================

def find_column(
    columns: list[str],
    candidates: list[str]
) -> str | None:
    """自动识别 CSV 中的列名。"""

    normalized = {
        str(column).strip().lower(): column
        for column in columns
    }

    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]

    return None


@st.cache_data(ttl=1)
def load_data(csv_file: str) -> pd.DataFrame:
    """读取并清理 CSV 数据。"""

    df = pd.read_csv(csv_file)

    df.columns = [
        str(column).strip().lower()
        for column in df.columns
    ]

    time_col = find_column(
        list(df.columns),
        ["time", "datetime", "timestamp", "date"]
    )

    temp_col = find_column(
        list(df.columns),
        ["temp", "temperature"]
    )

    humi_col = find_column(
        list(df.columns),
        ["humi", "humidity"]
    )

    light_col = find_column(
        list(df.columns),
        ["light", "lux", "illumination"]
    )

    if temp_col is None:
        raise ValueError(
            f"找不到温度列，当前列名为：{list(df.columns)}"
        )

    if humi_col is None:
        raise ValueError(
            f"找不到湿度列，当前列名为：{list(df.columns)}"
        )
    
    if light_col is None:
        raise ValueError(
            f"找不到光照列，当前列名为：{list(df.columns)}"
        )

    rename_map = {
        temp_col: "temperature",
        humi_col: "humidity",
        light_col: "light",
    }

    if time_col is not None:
        rename_map[time_col] = "time"

    df = df.rename(columns=rename_map)

    df["temperature"] = pd.to_numeric(
        df["temperature"],
        errors="coerce"
    )

    df["humidity"] = pd.to_numeric(
        df["humidity"],
        errors="coerce"
    )

    df["light"] = pd.to_numeric(
        df["light"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["temperature", "humidity","light"]
    ).copy()

    if "time" in df.columns:
        df["time"] = pd.to_datetime(
            df["time"],
            errors="coerce"
        )
    else:
        df["time"] = pd.date_range(
            end=datetime.now(),
            periods=len(df),
            freq="s"
        )

    df = df.dropna(subset=["time"])
    df = df.sort_values("time")
    df = df.reset_index(drop=True)

    return df


def calculate_monitoring(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    根据此前历史数据计算动态均值和异常状态。

    当前数据不参与自身的历史均值计算，
    防止异常值把判断基准同时拉高或拉低。
    """

    result = df.copy()

    result["historical_mean"] = (
        result["temperature"]
        .expanding()
        .mean()
        .shift(1)
    )

    result["temperature_deviation"] = (
        result["temperature"]
        - result["historical_mean"]
    )

    def judge(row: pd.Series) -> str:
        if pd.isna(row["historical_mean"]):
            return "学习中"

        if abs(row["temperature_deviation"]) > TEMP_THRESHOLD:
            return "异常"

        return "正常"

    result["status"] = result.apply(
        judge,
        axis=1
    )

    # 至少积累 5 条数据后再进行判断
    if len(result) < 5:
        result["status"] = "学习中"

    return result


# =========================================================
# DeepSeek
# =========================================================

def call_deepseek(
    latest: pd.Series,
    recent_df: pd.DataFrame
) -> str:
    """仅在用户点击按钮后调用 DeepSeek。"""

    if not DEEPSEEK_API_KEY:
        raise RuntimeError(
            "尚未配置 DEEPSEEK_API_KEY。"
            "请检查项目目录中的 .env 文件。"
        )

    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
    )

    historical_mean = latest["historical_mean"]
    deviation = latest["temperature_deviation"]

    if pd.isna(historical_mean):
        mean_text = "数据不足，仍处于学习阶段"
        deviation_text = "暂不可计算"
    else:
        mean_text = f"{historical_mean:.2f}℃"
        deviation_text = f"{deviation:+.2f}℃"

    recent_count = len(recent_df)

    prompt = f"""
请分析以下环境温湿度监测数据。

当前数据：
- 当前温度：{latest["temperature"]:.2f}℃
- 当前湿度：{latest["humidity"]:.2f}%
- 当前光照：{latest["light"]:.2f} lx
- 历史温度均值：{mean_text}
- 当前温度偏差：{deviation_text}
- 当前异常阈值：±{TEMP_THRESHOLD:.1f}℃
- 本地算法状态：{latest["status"]}

最近 {recent_count} 条数据统计：
- 平均温度：{recent_df["temperature"].mean():.2f}℃
- 最低温度：{recent_df["temperature"].min():.2f}℃
- 最高温度：{recent_df["temperature"].max():.2f}℃
- 平均湿度：{recent_df["humidity"].mean():.2f}%
- 最低湿度：{recent_df["humidity"].min():.2f}%
- 最高湿度：{recent_df["humidity"].max():.2f}%
- 平均光照：{recent_df["light"].mean():.2f} lx
- 最低光照：{recent_df["light"].min():.2f} lx
- 最高光照：{recent_df["light"].max():.2f} lx

本地异常规则：
当前温度偏离此前历史均值超过 ±{TEMP_THRESHOLD:.1f}℃ 时判定为异常。

请严格按照下面的格式输出：

### 监测结论
用一句话说明当前环境是否正常。

### 数据分析
分析温度偏差、湿度状态、光照情况和最近数据变化，
控制在两到三句话。

### 处理建议
给出两到三条简短、具体的建议，使用编号列表。

要求：
- 使用中文；
- 温度偏离历史均值超过 ±{TEMP_THRESHOLD:.1f}℃ 时才触发本地异常规则；
- 光照目前没有设定固定异常阈值，只能结合最近数据范围描述变化；
- 不要因为光照高低直接判定异常；
- 不要虚构没有提供的数据；
- 总长度不超过 220 字。
"""

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是环境温湿度智能监测助手。"
                    "你需要根据传感器数据和本地异常规则，"
                    "输出简洁、客观、格式清楚的环境分析。"
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        max_tokens=400,
        stream=False,
    )

    result = response.choices[0].message.content

    if not result:
        raise RuntimeError("DeepSeek 没有返回有效内容。")

    return result.strip()


# =========================================================
# UI 辅助函数
# =========================================================

def metric_card(
    title: str,
    value: str,
    note: str,
    value_class: str = "metric-value"
) -> None:
    """生成统一尺寸的实时数据卡片。"""

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-name">{title}</div>
            <div class="{value_class}">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 页面刷新
# =========================================================



# =========================================================
# 页面标题
# =========================================================

st.markdown(
    '<div class="main-title">环境温湿度智能监测系统</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="main-subtitle">
        实时采集 · 历史均值学习 · 异常检测 · DeepSeek 辅助分析
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.get("ai_running", False):
    st_autorefresh(
        interval=PAGE_REFRESH_SECONDS * 1000,
        key="data_refresh",
    )
# =========================================================
# 加载数据
# =========================================================

if not os.path.exists(CSV_FILE):
    st.error(
        "没有找到 data.csv。"
        "请先运行 serial_reader.py 采集数据。"
    )
    st.stop()

try:
    df = load_data(CSV_FILE)
except Exception as exc:
    st.error(f"读取 data.csv 失败：{exc}")
    st.stop()

if df.empty:
    st.warning("data.csv 中还没有有效数据。")
    st.stop()

TEMP_THRESHOLD = st.number_input(
    "温度异常阈值（℃）",
    min_value=0.1,
    max_value=10.0,
    value=DEFAULT_TEMP_THRESHOLD,
    step=0.1,
    format="%.1f",
)

df = calculate_monitoring(df)

latest = df.iloc[-1]
recent_df = df.tail(30).copy()

status = str(latest["status"])

historical_mean = latest["historical_mean"]

if pd.isna(historical_mean):
    historical_mean_text = "学习中"
else:
    historical_mean_text = f"{historical_mean:.2f} ℃"

if status == "正常":
    status_class = "status-normal"
elif status == "异常":
    status_class = "status-abnormal"
else:
    status_class = "status-learning"


# =========================================================
# 实时监测
# =========================================================

st.markdown(
    '<div class="section-title">实时监测</div>',
    unsafe_allow_html=True,
)

if st.button(
    "刷新实时数据",
    key="refresh_data_button"
):
    st.cache_data.clear()
    st.rerun()

col1, col2, col3, col4, col5 = st.columns(
    5,
    gap="medium"
)

with col1:
    metric_card(
        title="当前温度",
        value=f"{latest['temperature']:.2f} ℃",
        note=(
            "更新时间："
            + latest["time"].strftime("%H:%M:%S")
        ),
    )

with col2:
    metric_card(
        title="当前湿度",
        value=f"{latest['humidity']:.2f} %",
        note="AHT20 实时采集",
    )

with col3:
    metric_card(
        title="当前光照",
        value=f"{latest['light']:.2f} lx",
        note="BH1750 实时采集",
    )

with col4:
    metric_card(
        title="历史温度均值",
        value=historical_mean_text,
        note="基于此前历史温度动态计算",
    )

with col5:
    metric_card(
        title="监测状态",
        value=status,
        note=(
            f"异常阈值：历史均值 ±"
            f"{TEMP_THRESHOLD:.1f}℃"
        ),
        value_class=status_class,
    )


# =========================================================
# DeepSeek AI 手动分析
# =========================================================

# =========================================================
# DeepSeek AI 手动分析
# =========================================================

st.markdown(
    '<div class="section-title">DeepSeek AI 分析</div>',
    unsafe_allow_html=True,
)

# 先初始化状态，避免页面重跑后结果消失
if "ai_result" not in st.session_state:
    st.session_state["ai_result"] = ""

if "ai_error" not in st.session_state:
    st.session_state["ai_error"] = ""

if "ai_time" not in st.session_state:
    st.session_state["ai_time"] = None


ai_left, ai_right = st.columns(
    [5, 1.25],
    gap="medium",
)

with ai_left:
    if DEEPSEEK_API_KEY:
        st.markdown(
            """
            <span class="ai-connected">
                AI 接口已连接 · 点击按钮后分析
            </span>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <span class="ai-disconnected">
                尚未配置 API Key
            </span>
            """,
            unsafe_allow_html=True,
        )

    st.caption(
        "DeepSeek 将读取当前状态及最近 30 条数据统计，"
        "不会读取或上传整个 CSV 文件。"
    )

with ai_right:
    analyze_button = st.button(
        "开始 AI 分析",
        key="deepseek_analyze_button",
        use_container_width=True,
        type="primary",
    )


# 点击后调用 DeepSeek
if analyze_button:
    st.session_state["ai_error"] = ""
    st.session_state["ai_running"] = True

    if not DEEPSEEK_API_KEY:
        st.session_state["ai_error"] = (
            "没有检测到 API Key。请检查 .env 文件中的 "
            "DEEPSEEK_API_KEY。"
        )
        st.session_state["ai_running"] = False
        st.rerun()

    else:
        try:
            with st.spinner(
                "DeepSeek 正在分析监测数据，请稍候……"
            ):
                result = call_deepseek(
                    latest=latest,
                    recent_df=recent_df,
                )

            st.session_state["ai_result"] = result
            st.session_state["ai_time"] = datetime.now()
            st.session_state["ai_error"] = ""

        except Exception as exc:
            st.session_state["ai_result"] = ""
            st.session_state["ai_error"] = (
                f"{type(exc).__name__}: {exc}"
            )

        finally:
            st.session_state["ai_running"] = False

        st.rerun()


# 显示错误
if st.session_state["ai_error"]:
    st.error(
        "DeepSeek 调用失败：\n\n"
        + st.session_state["ai_error"]
    )


# 显示 AI 结果
if st.session_state["ai_result"]:
    st.markdown(
        st.session_state["ai_result"]
    )

    if st.session_state["ai_time"] is not None:
        st.caption(
            "本次分析时间："
            + st.session_state["ai_time"].strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

else:
    st.markdown(
        """
        <div class="ai-placeholder">
            尚未进行 AI 分析。点击右侧“开始 AI 分析”，
            DeepSeek 将结合当前温湿度、本地异常状态和最近数据趋势，
            给出监测结论与处理建议。
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "DeepSeek 将读取当前状态及最近 30 条数据统计，"
        "不会读取或上传整个 CSV 文件。"
    )






if st.session_state.get("ai_error"):
    st.error(
        "DeepSeek 调用失败："
        + st.session_state["ai_error"]
    )





# =========================================================
# 数据趋势
# =========================================================

st.markdown(
    '<div class="section-title">最近数据趋势</div>',
    unsafe_allow_html=True,
)

temp_tab, humi_tab , light_tab = st.tabs(
    ["温度趋势", "湿度趋势","光照趋势"]
)

with temp_tab:
    temp_chart = recent_df[
        [
            "time",
            "temperature",
            "historical_mean",
        ]
    ].copy()

    temp_chart = temp_chart.set_index("time")

    temp_chart = temp_chart.rename(
        columns={
            "temperature": "实时温度",
            "historical_mean": "历史均值",
        }
    )

    st.line_chart(
        temp_chart,
        height=330,
        use_container_width=True,
    )

with humi_tab:
    humi_chart = recent_df[
        [
            "time",
            "humidity",
        ]
    ].copy()

    humi_chart = humi_chart.set_index("time")

    humi_chart = humi_chart.rename(
        columns={
            "humidity": "实时湿度",
        }
    )

    st.line_chart(
        humi_chart,
        height=330,
        use_container_width=True,
    )

with light_tab:
    light_chart = recent_df[
        [
            "time",
            "light",
        ]
    ].copy()

    light_chart = light_chart.set_index("time")

    light_chart = light_chart.rename(
        columns={
            "light": "实时光照",
        }
    )

    st.line_chart(
        light_chart,
        height=330,
        use_container_width=True,
    )
# =========================================================
# 历史数据查询
# =========================================================

st.markdown(
    '<div class="section-title">历史数据查询</div>',
    unsafe_allow_html=True,
)

filter1, filter2, filter3 = st.columns(
    [1.2, 1.2, 1.3],
    gap="medium"
)

with filter1:
    query_range = st.selectbox(
        "查询范围",
        [
            "最近 20 条",
            "最近 50 条",
            "全部数据",
            "仅查看异常数据",
        ],
    )

with filter2:
    status_filter = st.selectbox(
        "监测状态",
        [
            "全部状态",
            "正常",
            "异常",
            "学习中",
        ],
    )

with filter3:
    time_keyword = st.text_input(
        "时间查询",
        placeholder="例如：16:05 或 2026-06-05",
    )


query_df = df.copy()

if query_range == "最近 20 条":
    query_df = query_df.tail(20)

elif query_range == "最近 50 条":
    query_df = query_df.tail(50)

elif query_range == "仅查看异常数据":
    query_df = query_df[
        query_df["status"] == "异常"
    ]


if status_filter != "全部状态":
    query_df = query_df[
        query_df["status"] == status_filter
    ]


if time_keyword:
    formatted_time = query_df["time"].dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    query_df = query_df[
        formatted_time.str.contains(
            time_keyword,
            case=False,
            na=False,
        )
    ]


display_df = query_df[
    [
        "time",
        "temperature",
        "humidity",
        "light",
        "historical_mean",
        "temperature_deviation",
        "status",
    ]
].copy()


display_df["time"] = display_df["time"].dt.strftime(
    "%Y-%m-%d %H:%M:%S"
)

display_df["temperature"] = (
    display_df["temperature"].round(2)
)

display_df["humidity"] = (
    display_df["humidity"].round(2)
)

display_df["light"] = (
    display_df["light"].round(2)
)

display_df["historical_mean"] = (
    display_df["historical_mean"].round(2)
)

display_df["temperature_deviation"] = (
    display_df["temperature_deviation"].round(2)
)


display_df = display_df.rename(
    columns={
        "time": "采集时间",
        "temperature": "温度/℃",
        "humidity": "湿度/%",
        "light": "光照/lx",
        "historical_mean": "历史均值/℃",
        "temperature_deviation": "温度偏差/℃",
        "status": "监测状态",
    }
)


st.dataframe(
    display_df.iloc[::-1],
    use_container_width=True,
    hide_index=True,
    height=390,
)


csv_download = display_df.to_csv(
    index=False
).encode("utf-8-sig")


st.download_button(
    label="导出当前查询结果",
    data=csv_download,
    file_name="monitor_query_result.csv",
    mime="text/csv",
)


st.caption(
    f"共读取 {len(df)} 条历史记录 · "
    f"页面每 {PAGE_REFRESH_SECONDS} 秒更新实时数据 · "
    f"DeepSeek 仅在点击按钮后调用"
)