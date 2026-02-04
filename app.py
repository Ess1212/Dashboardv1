# =============================================================================
# SECTION 1 — Application Bootstrap & Runtime Guards
# (NEW VERSION • Single-Page Dashboard • Enterprise-Safe • Streamlit)
# =============================================================================
# PURPOSE:
# - Initialize the application runtime safely
# - Declare ALL imports used anywhere in the app
# - Enforce strict architecture rules:
#     ✅ Single file only (app.py)
#     ✅ Python minimum version
#     ✅ SQLite availability
#     ✅ Streamlit session_state existence
# - Configure logging (rerun-safe)
# - Configure Streamlit page settings (ONLY UI allowed here)
#
# ABSOLUTE RULES (SECTION 1):
# ❌ NO database connections
# ❌ NO SQL execution
# ❌ NO file writing
# ❌ NO st.session_state mutation
# ❌ NO UI rendering (EXCEPT st.set_page_config)
#
# OUTPUT GUARANTEE:
# ✅ This section can run ALONE
# ✅ Later sections will not fail due to missing imports
# =============================================================================

from __future__ import annotations

# =============================================================================
# 1.1 — Standard Library Imports (Full Coverage)
# =============================================================================
import os
import sys
import io
import re
import gc
import json
import math
import time
import uuid
import copy
import hashlib
import logging
import warnings
import traceback
import contextlib
import tempfile
import sqlite3
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import (
    Any,
    Dict,
    List,
    Tuple,
    Optional,
    Callable,
    Iterable,
    Union,
    Literal,
)

# =============================================================================
# 1.2 — Third-Party Core Imports
# =============================================================================
import streamlit as st
import pandas as pd
import numpy as np

# Plotting engine (used later, not here)
import plotly.graph_objects as go

# =============================================================================
# 1.3 — Optional Libraries (Fail Gracefully)
# =============================================================================
AVAILABLE_REPORTLAB: bool = False
AVAILABLE_OPENPYXL: bool = False
AVAILABLE_XLSXWRITER: bool = False
AVAILABLE_KALEIDO: bool = False
AVAILABLE_MATPLOTLIB: bool = False

REPORTLAB_IMPORT_ERROR: Optional[str] = None
OPENPYXL_IMPORT_ERROR: Optional[str] = None
XLSXWRITER_IMPORT_ERROR: Optional[str] = None
KALEIDO_IMPORT_ERROR: Optional[str] = None
MATPLOTLIB_IMPORT_ERROR: Optional[str] = None

# ---- PDF (ReportLab) ----
try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
    )
    from reportlab.lib.styles import getSampleStyleSheet

    AVAILABLE_REPORTLAB = True
except Exception as exc:
    AVAILABLE_REPORTLAB = False
    REPORTLAB_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"

# ---- Excel engines ----
try:
    import openpyxl  # noqa: F401
    AVAILABLE_OPENPYXL = True
except Exception as exc:
    AVAILABLE_OPENPYXL = False
    OPENPYXL_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"

try:
    import xlsxwriter  # noqa: F401
    AVAILABLE_XLSXWRITER = True
except Exception as exc:
    AVAILABLE_XLSXWRITER = False
    XLSXWRITER_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"

# ---- Plotly image export ----
try:
    import kaleido  # noqa: F401
    AVAILABLE_KALEIDO = True
except Exception as exc:
    AVAILABLE_KALEIDO = False
    KALEIDO_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"

# ---- Matplotlib fallback ----
try:
    import matplotlib.pyplot as plt  # noqa: F401
    AVAILABLE_MATPLOTLIB = True
except Exception as exc:
    AVAILABLE_MATPLOTLIB = False
    MATPLOTLIB_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"

# =============================================================================
# 1.4 — Warning Policy (Quiet but Safe)
# =============================================================================
warnings.simplefilter("ignore", category=FutureWarning)
warnings.simplefilter("ignore", category=UserWarning)

# =============================================================================
# 1.5 — Logging System (Streamlit Rerun-Safe)
# =============================================================================
def _configure_logging_once() -> logging.Logger:
    """
    Configure a single application logger that is safe under Streamlit reruns.
    """
    logger_name = "SWG_ONEPAGE_DASHBOARD"
    logger = logging.getLogger(logger_name)

    if getattr(logger, "_configured", False):
        return logger

    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger._configured = True  # type: ignore[attr-defined]
    return logger


LOGGER = _configure_logging_once()

# =============================================================================
# 1.6 — Streamlit Page Configuration (ONLY UI ALLOWED HERE)
# =============================================================================
st.set_page_config(
    page_title="SWG Power Dispatch Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# 1.7 — Immutable Application Identity
# =============================================================================
APP_NAME: str = "SWG Power Dispatch Dashboard"
APP_VERSION: str = "4.0.0"
APP_BUILD_TAG: str = "ONE_PAGE_REDESIGN"

APP_DOMAIN: str = "Energy Dispatch Logging"
APP_RUNTIME: str = "LOCAL_SQLITE_ONLY"
APP_ARCHITECTURE: str = "SINGLE_FILE_STREAMLIT"

COMPANY_NAME: str = "SchneiTech Group"
COMPANY_SHORT: str = "STG"

BOOT_TIME_UTC: str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# =============================================================================
# 1.8 — HARD ARCHITECTURE GUARDS (FAIL FAST)
# =============================================================================
def _guard_single_file_name() -> None:
    """
    Enforce that the application is running from 'app.py'.
    """
    try:
        fname = os.path.basename(__file__)
    except Exception:
        LOGGER.warning("⚠️ __file__ unavailable; cannot strictly enforce filename.")
        return

    if fname.lower() != "app.py":
        raise RuntimeError(
            "❌ ARCHITECTURE VIOLATION\n"
            "This application MUST be executed from a single file named 'app.py'.\n"
            f"Detected filename: {fname}"
        )


def _guard_python_version(min_major: int = 3, min_minor: int = 9) -> None:
    """
    Enforce minimum Python version.
    """
    if sys.version_info < (min_major, min_minor):
        raise RuntimeError(
            "❌ PYTHON VERSION TOO LOW\n"
            f"Required: Python {min_major}.{min_minor}+\n"
            f"Detected: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )


def _guard_sqlite_available() -> None:
    """
    Ensure sqlite3 is available.
    """
    try:
        _ = sqlite3.sqlite_version
    except Exception as exc:
        raise RuntimeError(
            "❌ SQLITE NOT AVAILABLE\n"
            f"Error: {type(exc).__name__}: {exc}"
        )


def _guard_streamlit_session_state() -> None:
    """
    Ensure Streamlit session_state exists.
    """
    if not hasattr(st, "session_state"):
        raise RuntimeError("❌ Streamlit session_state is not available.")


# Execute guards immediately
_guard_single_file_name()
_guard_python_version()
_guard_sqlite_available()
_guard_streamlit_session_state()

# =============================================================================
# 1.9 — Database Identity Declaration (NO CONNECTION HERE)
# =============================================================================
DB_FILENAME: str = "SWG_DATA.db"
DB_ENGINE: str = "sqlite"
DB_SINGLE_FILE_ONLY: bool = True

if DB_FILENAME != "SWG_DATA.db":
    raise RuntimeError("❌ DB filename must be exactly 'SWG_DATA.db'")

# =============================================================================
# 1.10 — Canonical DateTime Rules (Global Contract)
# =============================================================================
DT_STORAGE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
DATE_STORAGE_FORMAT: str = "%Y-%m-%d"
TIME_STORAGE_FORMAT: str = "%H:%M:%S"

DEFAULT_TIMEZONE_LABEL: str = "Asia/Phnom_Penh"

# =============================================================================
# 1.11 — SWG Identity Constants
# =============================================================================
SWG_IDS: Tuple[str, ...] = ("SWG1", "SWG2", "SWG3")

# =============================================================================
# 1.12 — PURE Helper Utilities (Allowed in Section 1)
# =============================================================================
def deep_copy(obj: Any) -> Any:
    """Pure deep copy helper."""
    return copy.deepcopy(obj)


def safe_local_now() -> datetime:
    """Return local server datetime."""
    return datetime.now()


def safe_utc_now() -> datetime:
    """Return UTC datetime."""
    return datetime.utcnow()


def is_nan_like(value: Any) -> bool:
    """Detect NaN / NaT / None safely."""
    try:
        if value is None:
            return True
        if isinstance(value, float) and math.isnan(value):
            return True
        return bool(pd.isna(value))
    except Exception:
        return False


def normalize_to_none(value: Any) -> Any:
    """Convert NaN-like values to None."""
    return None if is_nan_like(value) else value


def stringify_datetime(dt_any: Any) -> Optional[str]:
    """
    Convert datetime-like input to canonical DB datetime string.
    """
    try:
        parsed = pd.to_datetime(dt_any, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.to_pydatetime().strftime(DT_STORAGE_FORMAT)
    except Exception:
        return None


def stable_hash_text(text: Any) -> str:
    """Stable SHA-256 hash of any text-like input."""
    s = str(text)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

# =============================================================================
# 1.13 — Debug Environment Snapshot (Read-Only)
# =============================================================================
def debug_env_snapshot() -> Dict[str, Any]:
    """
    Return environment diagnostics.
    """
    return {
        "app": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "build": APP_BUILD_TAG,
        },
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "sqlite_version": sqlite3.sqlite_version,
        "boot_utc": BOOT_TIME_UTC,
        "optional_libs": {
            "reportlab": AVAILABLE_REPORTLAB,
            "openpyxl": AVAILABLE_OPENPYXL,
            "xlsxwriter": AVAILABLE_XLSXWRITER,
            "kaleido": AVAILABLE_KALEIDO,
            "matplotlib": AVAILABLE_MATPLOTLIB,
        },
    }


# =============================================================================
# 1.14 — Forbidden Operation Guards (Fail Loud)
# =============================================================================
class SectionGuardError(RuntimeError):
    """Raised when forbidden operations are attempted in Section 1."""


def forbidden_in_section_1(operation: str) -> None:
    raise SectionGuardError(
        "❌ SECTION 1 VIOLATION\n"
        f"Operation '{operation}' is NOT allowed in Section 1.\n"
        "Move this logic to Section 3+."
    )


# Stub functions (will be overridden later)
def get_db_connection(*args, **kwargs):
    forbidden_in_section_1("get_db_connection")


def execute_sql(*args, **kwargs):
    forbidden_in_section_1("execute_sql")


def fetch_one(*args, **kwargs):
    forbidden_in_section_1("fetch_one")


def fetch_all(*args, **kwargs):
    forbidden_in_section_1("fetch_all")


# =============================================================================
# 1.15 — Final Assertions (Fail Early)
# =============================================================================
assert isinstance(LOGGER, logging.Logger)
assert DB_FILENAME == "SWG_DATA.db"
assert DT_STORAGE_FORMAT == "%Y-%m-%d %H:%M:%S"
assert len(SWG_IDS) == 3

LOGGER.info("✅ SECTION 1 loaded successfully — runtime is SAFE.")

# =============================================================================
# END SECTION 1
# =============================================================================

# =============================================================================
# SECTION 2 — Global Constants & Business Contracts
# (NEW VERSION • One-Page Dashboard • Enterprise Rules Layer)
# =============================================================================
# PURPOSE:
# - Define ALL constants used across the application
# - Centralize business rules, limits, formats, and contracts
# - Prevent logic drift between UI, DB, and text generation
# - Act as the SINGLE SOURCE OF TRUTH for:
#     ✅ SWG identity
#     ✅ Numeric validation limits
#     ✅ Datetime formats
#     ✅ Merge behavior
#     ✅ Session key registry
#     ✅ UI workflow scope (single page)
#
# HARD RULES (SECTION 2):
# ❌ NO database access
# ❌ NO SQL execution
# ❌ NO UI rendering
# ❌ NO st.session_state mutation
#
# GUARANTEE:
# ✅ Safe to import immediately after SECTION 1
# =============================================================================

# =============================================================================
# 2.1 — Feature Scope Flags (New Version = One Page Only)
# =============================================================================
# These flags define what this version SUPPORTS.
# Anything disabled here MUST NOT be implemented later.

FEATURE_ENABLE_ANALYTICS: bool = False
FEATURE_ENABLE_CHARTS: bool = False
FEATURE_ENABLE_EXPORTS: bool = False
FEATURE_ENABLE_MULTI_PAGE: bool = False

FEATURE_ENABLE_INPUT: bool = True
FEATURE_ENABLE_PREVIEW: bool = True
FEATURE_ENABLE_TEXT_EDIT: bool = True
FEATURE_ENABLE_COPY_TEXT: bool = True

# =============================================================================
# 2.2 — Mandatory Merge Mode Contract (CRITICAL)
# =============================================================================
# 🚨 DO NOT CHANGE THIS 🚨
# This contract guarantees:
# - No wide-table row misalignment
# - No SWG overwrite bugs
# - No NULL gap corruption

MERGE_MODE: Literal["FILL_NULL_QUEUE"] = "FILL_NULL_QUEUE"

ALLOWED_MERGE_MODES: Tuple[str, ...] = ("FILL_NULL_QUEUE",)

if MERGE_MODE not in ALLOWED_MERGE_MODES:
    raise RuntimeError(
        "❌ INVALID MERGE MODE\n"
        f"Detected: {MERGE_MODE}\n"
        f"Allowed: {ALLOWED_MERGE_MODES}"
    )

# =============================================================================
# 2.3 — TODAY-ONLY Data Policy
# =============================================================================
# This dashboard is for LIVE dispatch logging only.
# Historical data:
# - Read-only
# - Never overwritten
# - Never edited

TODAY_ONLY_ENFORCED: bool = True

TODAY_DATE_FORMAT: str = DATE_STORAGE_FORMAT  # from Section 1

# =============================================================================
# 2.4 — Numeric Input Validation Rules
# =============================================================================
# All operator inputs MUST follow these limits.
# UI + Repository must enforce the same values.

# ---- Active Power (MW) ----
LIMIT_ACTIVE_MIN: float = -150.0
LIMIT_ACTIVE_MAX: float = 150.0

# ---- Reactive Power (Mvar) ----
LIMIT_REACTIVE_MIN: float = -150.0
LIMIT_REACTIVE_MAX: float = 150.0

# ---- State of Charge (%) ----
LIMIT_SOC_MIN: float = 0.0
LIMIT_SOC_MAX: float = 100.0

# ---- Numeric formatting ----
NUMERIC_ALLOW_FLOAT: bool = True
NUMERIC_MAX_DECIMALS: int = 2

# =============================================================================
# 2.5 — Datetime Display & Storage Rules
# =============================================================================
# Storage format MUST match DB contract exactly
# Display format may differ but should remain consistent

DISPLAY_DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"
DISPLAY_TIME_FORMAT: str = "%H:%M"

# Used in log text generation
LOG_TIME_FORMAT: str = "%Y-%m-%d %H:%M"

# =============================================================================
# 2.6 — Database Table Naming Contract
# =============================================================================
# Yearly table pattern:
#   SWG_YYYY  (example: SWG_2026)

YEAR_TABLE_PREFIX: str = "SWG_"
YEAR_TABLE_REGEX: str = r"^SWG_\d{4}$"

# Primary key (internal use only)
DB_PRIMARY_KEY_COL: str = "__id"

# =============================================================================
# 2.7 — Wide Table Schema Contract (Authoritative)
# =============================================================================
# The DB MUST contain EXACTLY these columns (plus PK)

SWG_WIDE_COLS: Tuple[str, ...] = (
    "SWG1_DateTime", "SWG1_Active", "SWG1_Reactive", "SWG1_SOC",
    "SWG2_DateTime", "SWG2_Active", "SWG2_Reactive", "SWG2_SOC",
    "SWG3_DateTime", "SWG3_Active", "SWG3_Reactive", "SWG3_SOC",
)

SWG_WIDE_COLS_WITH_PK: Tuple[str, ...] = (DB_PRIMARY_KEY_COL,) + SWG_WIDE_COLS

# Per-SWG column mapping
SWG_COLS_BY_ID: Dict[str, Tuple[str, str, str, str]] = {
    "SWG1": ("SWG1_DateTime", "SWG1_Active", "SWG1_Reactive", "SWG1_SOC"),
    "SWG2": ("SWG2_DateTime", "SWG2_Active", "SWG2_Reactive", "SWG2_SOC"),
    "SWG3": ("SWG3_DateTime", "SWG3_Active", "SWG3_Reactive", "SWG3_SOC"),
}

# =============================================================================
# 2.8 — Dispatch Log Text Contract
# =============================================================================
# This defines EXACT formatting rules for copyable text

LOG_EVENT_DEFAULT: str = "CHARGE_Q"

LOG_LINE_SWG_TEMPLATE: str = (
    "{SWG}|P_MW={P}|SOC_PCT={SOC}|Q_MVAR={Q}"
)

LOG_HEADER_TIME_PREFIX: str = "TIME="
LOG_HEADER_EVENT_PREFIX: str = "EVENT="

# =============================================================================
# 2.9 — Session State Key Registry (CRITICAL)
# =============================================================================
# All session_state keys MUST be declared here.
# No section may invent new keys.

# ---- Core workflow ----
SSK_PAGE_READY: str = "page_ready"
SSK_LAST_ACTION: str = "last_action"

# ---- Input buffers ----
SSK_INPUT_DATETIME: str = "input_datetime"

SSK_INPUT_SWG1_ACTIVE: str = "input_swg1_active"
SSK_INPUT_SWG1_REACTIVE: str = "input_swg1_reactive"
SSK_INPUT_SWG1_SOC: str = "input_swg1_soc"

SSK_INPUT_SWG2_ACTIVE: str = "input_swg2_active"
SSK_INPUT_SWG2_REACTIVE: str = "input_swg2_reactive"
SSK_INPUT_SWG2_SOC: str = "input_swg2_soc"

SSK_INPUT_SWG3_ACTIVE: str = "input_swg3_active"
SSK_INPUT_SWG3_REACTIVE: str = "input_swg3_reactive"
SSK_INPUT_SWG3_SOC: str = "input_swg3_soc"

# ---- Preview ----
SSK_PREVIEW_DF: str = "preview_df"

# ---- Message text ----
SSK_GENERATED_TEXT: str = "generated_text"
SSK_EDITED_TEXT: str = "edited_text"

# =============================================================================
# 2.10 — UI Button Identifiers (Stable Keys)
# =============================================================================
BTN_ADD_SWG1: str = "btn_add_swg1"
BTN_ADD_SWG2: str = "btn_add_swg2"
BTN_ADD_SWG3: str = "btn_add_swg3"

BTN_APPLY_EDIT: str = "btn_apply_edit"
BTN_COPY_TEXT: str = "btn_copy_text"

# =============================================================================
# 2.11 — Refresh & Deduplication Policy
# =============================================================================
# Protect against accidental duplicate inserts caused by reruns

DEDUP_ENABLE: bool = True
DEDUP_HASH_WINDOW: int = 20

# =============================================================================
# 2.12 — Developer & Debug Flags
# =============================================================================
DEBUG_MODE: bool = False
DEBUG_SHOW_DB_STATUS: bool = False
DEBUG_SHOW_SESSION_STATE: bool = False

# =============================================================================
# 2.13 — Validation Helpers (PURE)
# =============================================================================
def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_numeric_limits() -> None:
    _assert(LIMIT_ACTIVE_MIN < LIMIT_ACTIVE_MAX, "Active power limits invalid")
    _assert(LIMIT_REACTIVE_MIN < LIMIT_REACTIVE_MAX, "Reactive power limits invalid")
    _assert(LIMIT_SOC_MIN >= 0 and LIMIT_SOC_MAX <= 100, "SOC limits invalid")


def validate_schema_contract() -> None:
    _assert(len(SWG_WIDE_COLS) == 12, "Wide schema must have exactly 12 columns")
    for swg in SWG_IDS:
        _assert(swg in SWG_COLS_BY_ID, f"Missing schema mapping for {swg}")


def validate_session_keys() -> None:
    keys = [
        SSK_PAGE_READY,
        SSK_LAST_ACTION,
        SSK_INPUT_DATETIME,
        SSK_INPUT_SWG1_ACTIVE, SSK_INPUT_SWG1_REACTIVE, SSK_INPUT_SWG1_SOC,
        SSK_INPUT_SWG2_ACTIVE, SSK_INPUT_SWG2_REACTIVE, SSK_INPUT_SWG2_SOC,
        SSK_INPUT_SWG3_ACTIVE, SSK_INPUT_SWG3_REACTIVE, SSK_INPUT_SWG3_SOC,
        SSK_PREVIEW_DF,
        SSK_GENERATED_TEXT,
        SSK_EDITED_TEXT,
    ]
    _assert(len(keys) == len(set(keys)), "Duplicate session_state keys detected")


# =============================================================================
# 2.14 — Execute Validations (Fail Fast)
# =============================================================================
validate_numeric_limits()
validate_schema_contract()
validate_session_keys()

LOGGER.info("✅ SECTION 2 loaded successfully — contracts validated.")

# =============================================================================
# END SECTION 2
# =============================================================================

# =============================================================================
# SECTION 3 — Database Engine (SQLite)
# (NEW VERSION • Mission-Critical • Rerun-Safe • Zero UI • Zero Schema)
# =============================================================================
# PURPOSE:
# - Prepare and verify the SQLite database engine
# - Guarantee DB file existence and write access
# - Provide SAFE connection factory for all future sections
# - Apply required PRAGMA settings (WAL, busy timeout, FK)
# - Perform integrity & smoke tests
#
# HARD RULES (SECTION 3):
# ❌ NO UI rendering
# ❌ NO st.session_state mutation
# ❌ NO table creation
# ❌ NO data insertion
#
# GUARANTEE AFTER THIS SECTION:
# ✅ SWG_DATA.db exists
# ✅ SQLite engine is stable
# ✅ Connections are safe under Streamlit reruns
# =============================================================================

# =============================================================================
# 3.1 — Database Path Resolver (Single Source of Truth)
# =============================================================================
def resolve_db_path() -> str:
    """
    Resolve absolute path to the SQLite database file.

    Strategy:
    - Use current working directory (Streamlit project root)
    - Enforce exact DB filename from Section 1
    - Return normalized absolute path
    """
    base_dir = os.getcwd()
    db_path = os.path.join(base_dir, DB_FILENAME)
    return os.path.abspath(db_path)


# =============================================================================
# 3.2 — Filesystem Safety Guards
# =============================================================================
def _ensure_parent_dir_writable(file_path: str) -> None:
    """
    Ensure the directory containing the DB file is writable.
    """
    parent_dir = os.path.dirname(file_path)

    if not parent_dir:
        raise RuntimeError(
            "❌ DB PATH ERROR\n"
            "Parent directory could not be resolved."
        )

    if not os.path.exists(parent_dir):
        raise RuntimeError(
            "❌ DB PATH ERROR\n"
            f"Directory does not exist: {parent_dir}"
        )

    if not os.access(parent_dir, os.W_OK):
        raise RuntimeError(
            "❌ DB PERMISSION ERROR\n"
            f"Directory is not writable: {parent_dir}"
        )


def ensure_db_file_exists(db_path: str) -> None:
    """
    Ensure the SQLite database file exists.
    If missing, create it safely (no schema, no tables).
    """
    _ensure_parent_dir_writable(db_path)

    if os.path.exists(db_path):
        if not os.path.isfile(db_path):
            raise RuntimeError(
                "❌ DB FILE ERROR\n"
                f"Path exists but is not a file: {db_path}"
            )
        return

    try:
        conn = sqlite3.connect(db_path)
        conn.close()
        LOGGER.info(f"✅ SQLite database created: {db_path}")
    except Exception as exc:
        raise RuntimeError(
            "❌ FAILED TO CREATE SQLITE DATABASE FILE\n"
            f"Path: {db_path}\n"
            f"Error: {type(exc).__name__}: {exc}"
        )


# =============================================================================
# 3.3 — SQLite PRAGMA Configuration
# =============================================================================
def _apply_sqlite_pragmas(conn: sqlite3.Connection) -> None:
    """
    Apply mandatory PRAGMA settings for stability & concurrency.
    """
    try:
        cur = conn.cursor()

        # Prevent "database is locked"
        cur.execute("PRAGMA busy_timeout = 4000;")

        # Enable foreign keys (safe even if unused)
        cur.execute("PRAGMA foreign_keys = ON;")

        # WAL mode for concurrent reads/writes
        cur.execute("PRAGMA journal_mode = WAL;")

        # Balanced durability
        cur.execute("PRAGMA synchronous = NORMAL;")

        # Performance improvements
        cur.execute("PRAGMA temp_store = MEMORY;")
        cur.execute("PRAGMA cache_size = -64000;")  # ~64MB

        conn.commit()
    except Exception as exc:
        raise RuntimeError(
            "❌ SQLITE PRAGMA CONFIGURATION FAILED\n"
            f"Error: {type(exc).__name__}: {exc}"
        )


# =============================================================================
# 3.4 — Connection Factory (Authoritative)
# =============================================================================
def get_db_connection(*, read_only: bool = False) -> sqlite3.Connection:
    """
    Create and return a configured SQLite connection.

    Guarantees:
    - DB file exists
    - Row factory enabled (dict-like)
    - PRAGMAs applied on every connection
    - Safe for Streamlit reruns

    IMPORTANT:
    - Caller MUST close the connection
    """
    db_path = resolve_db_path()
    ensure_db_file_exists(db_path)

    try:
        if read_only:
            # Best-effort read-only mode
            uri = f"file:{db_path}?mode=ro"
            conn = sqlite3.connect(uri, uri=True, timeout=4)
        else:
            conn = sqlite3.connect(db_path, timeout=4)

        conn.row_factory = sqlite3.Row
        _apply_sqlite_pragmas(conn)
        return conn

    except sqlite3.OperationalError as exc:
        raise RuntimeError(
            "❌ SQLITE OPERATIONAL ERROR\n"
            f"DB Path: {db_path}\n"
            f"Read Only: {read_only}\n"
            f"Error: {type(exc).__name__}: {exc}"
        )
    except Exception as exc:
        raise RuntimeError(
            "❌ FAILED TO OPEN SQLITE CONNECTION\n"
            f"DB Path: {db_path}\n"
            f"Read Only: {read_only}\n"
            f"Error: {type(exc).__name__}: {exc}"
        )


# =============================================================================
# 3.5 — Context Manager for Safe Usage
# =============================================================================
@contextlib.contextmanager
def db_session(*, read_only: bool = False) -> Iterable[sqlite3.Connection]:
    """
    Context manager that guarantees DB connection closure.
    """
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = get_db_connection(read_only=read_only)
        yield conn
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            LOGGER.warning("⚠️ Failed to close SQLite connection cleanly.")


# =============================================================================
# 3.6 — Database Integrity Check
# =============================================================================
def db_integrity_check() -> Dict[str, Any]:
    """
    Run SQLite integrity_check safely.
    """
    result: Dict[str, Any] = {
        "db_path": resolve_db_path(),
        "ok": False,
        "integrity": None,
        "journal_mode": None,
        "foreign_keys": None,
        "error": None,
    }

    try:
        with db_session(read_only=False) as conn:
            cur = conn.cursor()

            cur.execute("PRAGMA journal_mode;")
            result["journal_mode"] = cur.fetchone()[0]

            cur.execute("PRAGMA foreign_keys;")
            result["foreign_keys"] = cur.fetchone()[0]

            cur.execute("PRAGMA integrity_check;")
            integrity = cur.fetchone()[0]
            result["integrity"] = integrity
            result["ok"] = (integrity == "ok")

    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["ok"] = False

    return result


# =============================================================================
# 3.7 — Read/Write Smoke Test (TEMP TABLE ONLY)
# =============================================================================
def db_smoke_test() -> Dict[str, Any]:
    """
    Perform a TEMP table write/read test.
    Does NOT affect real schema or data.
    """
    out: Dict[str, Any] = {
        "ok": False,
        "error": None,
        "steps": [],
    }

    try:
        with db_session(read_only=False) as conn:
            cur = conn.cursor()

            out["steps"].append("create_temp")
            cur.execute("CREATE TEMP TABLE __healthcheck (x INTEGER);")

            out["steps"].append("insert_temp")
            cur.execute("INSERT INTO __healthcheck (x) VALUES (1);")

            out["steps"].append("select_temp")
            cur.execute("SELECT x FROM __healthcheck;")
            row = cur.fetchone()

            if not row or int(row[0]) != 1:
                raise RuntimeError("Temp table validation failed")

            out["ok"] = True

    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
        out["ok"] = False

    return out


# =============================================================================
# 3.8 — Boot-Time Verification (FAIL FAST)
# =============================================================================
def verify_database_engine_or_raise() -> None:
    """
    Verify database engine readiness.

    MUST PASS before schema or UI is allowed.
    """
    db_path = resolve_db_path()
    ensure_db_file_exists(db_path)

    integrity = db_integrity_check()
    if not integrity["ok"]:
        raise RuntimeError(
            "❌ SQLITE INTEGRITY CHECK FAILED\n"
            f"DB: {integrity['db_path']}\n"
            f"Integrity: {integrity['integrity']}\n"
            f"Error: {integrity['error']}"
        )

    smoke = db_smoke_test()
    if not smoke["ok"]:
        raise RuntimeError(
            "❌ SQLITE SMOKE TEST FAILED\n"
            f"Steps: {smoke['steps']}\n"
            f"Error: {smoke['error']}"
        )

    LOGGER.info("✅ SQLite engine verified and ready.")


# =============================================================================
# 3.9 — Execute Verification Immediately
# =============================================================================
verify_database_engine_or_raise()

# =============================================================================
# END SECTION 3
# =============================================================================

# =============================================================================
# SECTION 4 — Yearly Table Resolver & Date Rules
# (NEW VERSION • Time Authority • ZERO SQL • ZERO UI)
# =============================================================================
# PURPOSE:
# - Resolve which yearly table (SWG_YYYY) must be used
# - Enforce TODAY-ONLY data safety rules
# - Provide canonical datetime conversion utilities
# - Prevent year-routing bugs and historical data corruption
#
# HARD RULES (SECTION 4):
# ❌ NO database access
# ❌ NO SQL execution
# ❌ NO UI rendering
# ❌ NO st.session_state mutation
#
# GUARANTEE:
# ✅ All repositories use the SAME year logic
# ✅ No accidental writes to wrong year
# =============================================================================

# =============================================================================
# 4.1 — Internal Strict Type Helpers
# =============================================================================
def _is_date_like(obj: Any) -> bool:
    """
    Return True if object behaves like a date or datetime.
    PURE FUNCTION.
    """
    return isinstance(obj, (datetime, date, pd.Timestamp))


def _to_datetime_strict(dt_any: Any) -> datetime:
    """
    Convert supported input into datetime strictly.

    Accepted:
    - datetime
    - date (converted to midnight)
    - pandas.Timestamp
    - string parseable by pandas.to_datetime

    Raises:
    - ValueError on invalid input
    """
    if isinstance(dt_any, datetime):
        return dt_any

    if isinstance(dt_any, pd.Timestamp):
        if dt_any.tzinfo is not None:
            dt_any = dt_any.tz_convert(None)
        return dt_any.to_pydatetime()

    if isinstance(dt_any, date):
        return datetime(dt_any.year, dt_any.month, dt_any.day, 0, 0, 0)

    try:
        parsed = pd.to_datetime(dt_any, errors="raise")
        if isinstance(parsed, pd.Timestamp):
            if parsed.tzinfo is not None:
                parsed = parsed.tz_convert(None)
            return parsed.to_pydatetime()
        raise ValueError("Unsupported datetime input")
    except Exception as exc:
        raise ValueError(
            "❌ INVALID DATETIME INPUT\n"
            f"Value: {repr(dt_any)}\n"
            f"Error: {type(exc).__name__}: {exc}"
        )


# =============================================================================
# 4.2 — Year Extraction (Single Authority)
# =============================================================================
def extract_year(dt_any: Any) -> int:
    """
    Extract 4-digit year from datetime-like input.
    PURE FUNCTION.
    """
    dt = _to_datetime_strict(dt_any)
    year = int(dt.year)

    if year < 2000 or year > 2100:
        raise ValueError(
            "❌ YEAR OUT OF SUPPORTED RANGE\n"
            f"Year: {year}\n"
            "Supported range: 2000 → 2100"
        )
    return year


# =============================================================================
# 4.3 — Yearly Table Name Builder
# =============================================================================
def build_year_table_name(year: int) -> str:
    """
    Build yearly table name using strict contract: SWG_YYYY
    PURE FUNCTION.
    """
    if not isinstance(year, int):
        raise TypeError(f"Year must be int, got {type(year).__name__}")
    if year < 2000 or year > 2100:
        raise ValueError(f"Year out of supported range: {year}")
    return f"{YEAR_TABLE_PREFIX}{year}"


def resolve_yearly_table_name(dt_any: Optional[Any] = None) -> str:
    """
    Resolve yearly table name based on datetime reference.

    Rules:
    - dt_any is None → use server local now
    - Otherwise extract year strictly
    """
    if dt_any is None:
        dt_any = safe_local_now()
    year = extract_year(dt_any)
    return build_year_table_name(year)


def resolve_current_year_table_name() -> str:
    """
    Resolve yearly table name for CURRENT local year.
    PURE FUNCTION.
    """
    return resolve_yearly_table_name(safe_local_now())


# =============================================================================
# 4.4 — Table Name Validation (Injection Safe)
# =============================================================================
def is_valid_year_table_name(table_name: str) -> bool:
    """
    Validate table name matches ^SWG_\\d{4}$
    PURE FUNCTION.
    """
    if not isinstance(table_name, str):
        return False
    return re.match(YEAR_TABLE_REGEX, table_name.strip()) is not None


def assert_valid_year_table_name(table_name: str) -> None:
    """
    Raise error if table name violates contract.
    """
    if not is_valid_year_table_name(table_name):
        raise ValueError(
            "❌ INVALID YEAR TABLE NAME\n"
            f"Value: {repr(table_name)}\n"
            f"Expected pattern: {YEAR_TABLE_REGEX}"
        )


# =============================================================================
# 4.5 — TODAY-ONLY Boundary Helpers
# =============================================================================
def get_today_date() -> date:
    """
    Return today's LOCAL date (server authority).
    PURE FUNCTION.
    """
    return safe_local_now().date()


def to_date_str(d: Any) -> str:
    """
    Convert date/datetime into YYYY-MM-DD string.
    PURE FUNCTION.
    """
    dt = _to_datetime_strict(d)
    return dt.strftime(DATE_STORAGE_FORMAT)


def is_today_datetime(dt_any: Any) -> bool:
    """
    Return True if datetime belongs to today.
    PURE FUNCTION.
    """
    dt = _to_datetime_strict(dt_any)
    return dt.date() == get_today_date()


def assert_today_only(dt_any: Any, *, context: str = "operation") -> None:
    """
    Enforce TODAY-ONLY policy.

    Raises RuntimeError if datetime is not today.
    """
    if not TODAY_ONLY_ENFORCED:
        return

    if not is_today_datetime(dt_any):
        raise RuntimeError(
            "❌ TODAY-ONLY POLICY VIOLATION\n"
            f"Context: {context}\n"
            f"Target datetime: {repr(dt_any)}\n"
            f"Today date: {get_today_date().strftime(DATE_STORAGE_FORMAT)}"
        )


# =============================================================================
# 4.6 — Canonical Datetime Builders
# =============================================================================
def now_db_timestamp() -> str:
    """
    Return current local datetime in canonical DB format.
    """
    return safe_local_now().strftime(DT_STORAGE_FORMAT)


def ensure_db_datetime_format(dt_str: str) -> str:
    """
    Validate datetime string matches DB storage format EXACTLY.
    """
    if not isinstance(dt_str, str):
        raise TypeError("Datetime value must be a string")

    try:
        parsed = datetime.strptime(dt_str, DT_STORAGE_FORMAT)
        if parsed.strftime(DT_STORAGE_FORMAT) != dt_str:
            raise ValueError("Round-trip mismatch")
        return dt_str
    except Exception as exc:
        raise ValueError(
            "❌ INVALID DB DATETIME FORMAT\n"
            f"Expected: {DT_STORAGE_FORMAT}\n"
            f"Value: {repr(dt_str)}\n"
            f"Error: {type(exc).__name__}: {exc}"
        )


# =============================================================================
# 4.7 — Date Range Utilities (Read-Only Use)
# =============================================================================
def get_today_range_strings() -> Tuple[str, str]:
    """
    Return start and end datetime strings for today.
    Useful for preview queries later.
    PURE FUNCTION.
    """
    today = get_today_date()
    start = datetime(today.year, today.month, today.day, 0, 0, 0)
    end = datetime(today.year, today.month, today.day, 23, 59, 59)
    return (
        start.strftime(DT_STORAGE_FORMAT),
        end.strftime(DT_STORAGE_FORMAT),
    )


# =============================================================================
# 4.8 — Defensive Self-Test (NO SQL)
# =============================================================================
def _section_4_self_test() -> None:
    """
    Validate core logic of Section 4.
    PURE TEST (no DB, no UI).
    """
    # Year extraction
    assert extract_year("2026-01-30 12:00:00") == 2026

    # Table name build
    assert build_year_table_name(2026) == "SWG_2026"

    # Validation
    assert is_valid_year_table_name("SWG_2026")
    try:
        assert_valid_year_table_name("BAD_TABLE")
        raise RuntimeError("Validation should have failed")
    except ValueError:
        pass

    # Today logic
    now = safe_local_now()
    assert is_today_datetime(now)

    # Datetime format
    ts = now_db_timestamp()
    ensure_db_datetime_format(ts)

_section_4_self_test()

LOGGER.info("✅ SECTION 4 loaded successfully — time & table routing locked.")

# =============================================================================
# END SECTION 4
# =============================================================================

# =============================================================================
# SECTION 5 — Database Schema (Wide Table)
# (NEW VERSION • Schema Authority • Auto-Create • Zero Drift)
# =============================================================================
# PURPOSE:
# - Define the EXACT yearly wide-table schema (SWG_YYYY)
# - Auto-create the table if missing (idempotent)
# - Validate schema strictly on every run
# - Prevent silent schema drift or column mismatch
#
# SCHEMA CONTRACT (ABSOLUTE):
#   Table name: SWG_YYYY
#   Primary key: __id INTEGER PRIMARY KEY AUTOINCREMENT
#
#   SWG1_DateTime  TEXT
#   SWG1_Active    REAL
#   SWG1_Reactive  REAL
#   SWG1_SOC       REAL
#
#   SWG2_DateTime  TEXT
#   SWG2_Active    REAL
#   SWG2_Reactive  REAL
#   SWG2_SOC       REAL
#
#   SWG3_DateTime  TEXT
#   SWG3_Active    REAL
#   SWG3_Reactive  REAL
#   SWG3_SOC       REAL
#
# HARD RULES (SECTION 5):
# ❌ NO UI rendering
# ❌ NO st.session_state mutation
# ❌ NO SWG data insertion
#
# GUARANTEE:
# ✅ After this section, the correct SWG_YYYY table EXISTS
# ✅ Schema mismatches FAIL FAST
# =============================================================================

# =============================================================================
# 5.1 — Authoritative CREATE TABLE SQL
# =============================================================================
def get_wide_table_create_sql(table_name: str) -> str:
    """
    Return CREATE TABLE SQL for the SWG wide table.

    Design decisions:
    - TEXT for DateTime (canonical string format)
    - REAL for numeric values
    - NULL allowed (independent SWG arrival)
    - No defaults (logic controls insertion)
    """
    assert_valid_year_table_name(table_name)

    return f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        {DB_PRIMARY_KEY_COL} INTEGER PRIMARY KEY AUTOINCREMENT,

        SWG1_DateTime TEXT NULL,
        SWG1_Active   REAL NULL,
        SWG1_Reactive REAL NULL,
        SWG1_SOC      REAL NULL,

        SWG2_DateTime TEXT NULL,
        SWG2_Active   REAL NULL,
        SWG2_Reactive REAL NULL,
        SWG2_SOC      REAL NULL,

        SWG3_DateTime TEXT NULL,
        SWG3_Active   REAL NULL,
        SWG3_Reactive REAL NULL,
        SWG3_SOC      REAL NULL
    );
    """.strip()


# =============================================================================
# 5.2 — Performance Index Definitions
# =============================================================================
def get_wide_table_indexes_sql(table_name: str) -> List[str]:
    """
    Return index creation SQL statements.

    Index strategy:
    - Index DateTime columns for each SWG
    - Improves TODAY preview & filtering
    """
    assert_valid_year_table_name(table_name)

    indexes: List[str] = []
    for col in ("SWG1_DateTime", "SWG2_DateTime", "SWG3_DateTime"):
        idx_name = f"idx_{table_name.lower()}_{col.lower()}"
        indexes.append(
            f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({col});"
        )

    return indexes


# =============================================================================
# 5.3 — Schema Introspection Helpers
# =============================================================================
def table_exists(table_name: str) -> bool:
    """Return True if table exists."""
    assert_valid_year_table_name(table_name)

    sql = """
    SELECT name
    FROM sqlite_master
    WHERE type='table' AND name = ?
    LIMIT 1;
    """

    with db_session(read_only=True) as conn:
        cur = conn.cursor()
        cur.execute(sql, (table_name,))
        return cur.fetchone() is not None


def get_table_columns(table_name: str) -> List[str]:
    """Return ordered list of column names."""
    assert_valid_year_table_name(table_name)

    with db_session(read_only=True) as conn:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name});")
        rows = cur.fetchall()

    cols: List[str] = []
    for r in rows:
        if isinstance(r, sqlite3.Row):
            cols.append(r["name"])
        else:
            cols.append(r[1])

    return cols


def get_table_info(table_name: str) -> List[Dict[str, Any]]:
    """Return full PRAGMA table_info as dict list."""
    assert_valid_year_table_name(table_name)

    with db_session(read_only=True) as conn:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name});")
        rows = cur.fetchall()

    info: List[Dict[str, Any]] = []
    for r in rows:
        if isinstance(r, sqlite3.Row):
            info.append(dict(r))
        else:
            info.append(
                {
                    "cid": r[0],
                    "name": r[1],
                    "type": r[2],
                    "notnull": r[3],
                    "dflt_value": r[4],
                    "pk": r[5],
                }
            )
    return info


# =============================================================================
# 5.4 — STRICT Schema Validator (Fail Fast)
# =============================================================================
def validate_wide_schema_or_raise(table_name: str) -> None:
    """
    Validate table schema EXACTLY matches contract.

    Rules:
    - Must exist
    - Must contain PK + 12 wide columns
    - No missing columns
    - No extra columns
    - PK must be __id
    """
    assert_valid_year_table_name(table_name)

    if not table_exists(table_name):
        raise RuntimeError(
            "❌ SCHEMA VALIDATION FAILED\n"
            f"Table does not exist: {table_name}"
        )

    actual_cols = get_table_columns(table_name)
    expected_cols = list(SWG_WIDE_COLS_WITH_PK)

    actual_set = set(actual_cols)
    expected_set = set(expected_cols)

    missing = [c for c in expected_cols if c not in actual_set]
    extra = [c for c in actual_cols if c not in expected_set]

    if missing or extra:
        raise RuntimeError(
            "❌ SCHEMA MISMATCH DETECTED\n"
            f"Table: {table_name}\n"
            f"Missing columns: {missing}\n"
            f"Extra columns: {extra}\n"
            f"Expected: {expected_cols}\n"
            f"Actual: {actual_cols}"
        )

    # Validate primary key
    info = get_table_info(table_name)
    pk_cols = [c for c in info if int(c.get("pk", 0)) == 1]

    if not pk_cols or pk_cols[0]["name"] != DB_PRIMARY_KEY_COL:
        raise RuntimeError(
            "❌ PRIMARY KEY VIOLATION\n"
            f"Expected PK: {DB_PRIMARY_KEY_COL}\n"
            f"Detected PK columns: {pk_cols}"
        )

    # Column order warning (non-fatal)
    if actual_cols != expected_cols:
        LOGGER.warning(
            "⚠️ Column order differs from contract (non-fatal)\n"
            f"Expected: {expected_cols}\n"
            f"Actual:   {actual_cols}"
        )


# =============================================================================
# 5.5 — Schema Creator (Idempotent)
# =============================================================================
def ensure_yearly_wide_table(table_name: str) -> None:
    """
    Ensure the SWG_YYYY wide table exists and is valid.
    """
    assert_valid_year_table_name(table_name)

    create_sql = get_wide_table_create_sql(table_name)
    index_sqls = get_wide_table_indexes_sql(table_name)

    with db_session(read_only=False) as conn:
        cur = conn.cursor()
        try:
            cur.execute(create_sql)
            for ix in index_sqls:
                cur.execute(ix)
            conn.commit()
        except Exception as exc:
            conn.rollback()
            raise RuntimeError(
                "❌ FAILED TO CREATE / VERIFY WIDE TABLE\n"
                f"Table: {table_name}\n"
                f"Error: {type(exc).__name__}: {exc}"
            )

    validate_wide_schema_or_raise(table_name)


# =============================================================================
# 5.6 — Current Year Bootstrap
# =============================================================================
def ensure_current_year_table_exists() -> str:
    """
    Ensure current year's SWG_YYYY table exists.
    """
    table_name = resolve_current_year_table_name()
    ensure_yearly_wide_table(table_name)
    return table_name


# =============================================================================
# 5.7 — Boot-Time Schema Bootstrap (FAIL FAST)
# =============================================================================
def bootstrap_schema_or_raise() -> str:
    """
    Boot-time schema bootstrap.
    """
    try:
        table_name = ensure_current_year_table_exists()
        LOGGER.info(f"✅ Schema ready: {table_name}")
        return table_name
    except Exception as exc:
        raise RuntimeError(
            "❌ SCHEMA BOOTSTRAP FAILED\n"
            f"Error: {type(exc).__name__}: {exc}"
        )


# =============================================================================
# 5.8 — Execute Bootstrap Immediately
# =============================================================================
CURRENT_YEAR_TABLE_NAME: str = bootstrap_schema_or_raise()

# =============================================================================
# END SECTION 5
# =============================================================================

# =============================================================================
# SECTION 6 — Save & Update Repository
# (FINAL VERSION • FILL_NULL_QUEUE + SAFE UPDATE • ENTERPRISE LOCK)
# =============================================================================
# PURPOSE:
# - Provide the ONLY write/update path into SWG_DATA.db
# - Support BOTH:
#     ✅ New inserts (FILL_NULL_QUEUE)
#     ✅ Controlled updates from dashboard edits
# - Guarantee:
#     ✅ No overwrite of unrelated SWG data
#     ✅ No historical data corruption
#     ✅ TODAY-ONLY enforcement
#     ✅ Schema safety
#
# ABSOLUTE RULES (SECTION 6):
# ❌ NO UI rendering
# ❌ NO st.session_state mutation
# ❌ NO schema changes
#
# ALL DB WRITES MUST PASS THROUGH THIS SECTION
# =============================================================================

# =============================================================================
# 6.1 — Low-Level SQL Executors (Authoritative)
# =============================================================================
def execute_sql(
    sql: str,
    params: Optional[Tuple[Any, ...]] = None,
    *,
    read_only: bool = False,
    commit: bool = False,
    many: bool = False,
    many_params: Optional[List[Tuple[Any, ...]]] = None,
) -> None:
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("SQL must be a non-empty string")

    try:
        with db_session(read_only=read_only) as conn:
            cur = conn.cursor()

            if many:
                if not many_params:
                    raise ValueError("many=True requires many_params")
                cur.executemany(sql, many_params)
            else:
                cur.execute(sql, params or ())

            if commit:
                conn.commit()

    except Exception as exc:
        raise RuntimeError(
            "❌ SQL EXECUTION FAILED\n"
            f"SQL: {sql}\n"
            f"Params: {params}\n"
            f"Error: {type(exc).__name__}: {exc}"
        )


def fetch_one(
    sql: str,
    params: Optional[Tuple[Any, ...]] = None,
    *,
    read_only: bool = True,
) -> Optional[Dict[str, Any]]:
    try:
        with db_session(read_only=read_only) as conn:
            cur = conn.cursor()
            cur.execute(sql, params or ())
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as exc:
        raise RuntimeError(
            "❌ FETCH_ONE FAILED\n"
            f"SQL: {sql}\n"
            f"Params: {params}\n"
            f"Error: {type(exc).__name__}: {exc}"
        )


def fetch_all(
    sql: str,
    params: Optional[Tuple[Any, ...]] = None,
    *,
    read_only: bool = True,
) -> List[Dict[str, Any]]:
    try:
        with db_session(read_only=read_only) as conn:
            cur = conn.cursor()
            cur.execute(sql, params or ())
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    except Exception as exc:
        raise RuntimeError(
            "❌ FETCH_ALL FAILED\n"
            f"SQL: {sql}\n"
            f"Params: {params}\n"
            f"Error: {type(exc).__name__}: {exc}"
        )

# =============================================================================
# 6.2 — Numeric & Payload Validators (PURE)
# =============================================================================
def _validate_numeric(
    name: str,
    value: Optional[float],
    min_v: float,
    max_v: float,
) -> Optional[float]:
    if value is None:
        return None

    try:
        v = float(value)
    except Exception:
        raise ValueError(f"{name} must be numeric")

    if v < min_v or v > max_v:
        raise ValueError(f"{name} out of range ({min_v} → {max_v})")

    return round(v, NUMERIC_MAX_DECIMALS)


def _validate_swg_payload(
    *,
    swg_id: str,
    dt: str,
    active: Optional[float],
    reactive: Optional[float],
    soc: Optional[float],
) -> Dict[str, Any]:
    if swg_id not in SWG_IDS:
        raise ValueError(f"Invalid SWG ID: {swg_id}")

    ensure_db_datetime_format(dt)
    assert_today_only(dt, context=f"{swg_id} write")

    return {
        "datetime": dt,
        "active": _validate_numeric("Active", active, LIMIT_ACTIVE_MIN, LIMIT_ACTIVE_MAX),
        "reactive": _validate_numeric("Reactive", reactive, LIMIT_REACTIVE_MIN, LIMIT_REACTIVE_MAX),
        "soc": _validate_numeric("SOC", soc, LIMIT_SOC_MIN, LIMIT_SOC_MAX),
    }

# =============================================================================
# 6.3 — FILL_NULL_QUEUE Slot Resolver
# =============================================================================
def _find_oldest_null_slot(
    table_name: str,
    swg_id: str,
) -> Optional[int]:
    assert_valid_year_table_name(table_name)

    dt_col, a_col, r_col, soc_col = SWG_COLS_BY_ID[swg_id]

    sql = f"""
    SELECT {DB_PRIMARY_KEY_COL}
    FROM {table_name}
    WHERE
        {dt_col} IS NULL AND
        {a_col} IS NULL AND
        {r_col} IS NULL AND
        {soc_col} IS NULL
    ORDER BY {DB_PRIMARY_KEY_COL} ASC
    LIMIT 1;
    """

    row = fetch_one(sql)
    return int(row[DB_PRIMARY_KEY_COL]) if row else None

# =============================================================================
# 6.4 — Insert Empty Wide Row
# =============================================================================
def _insert_empty_wide_row(table_name: str) -> int:
    assert_valid_year_table_name(table_name)

    execute_sql(
        f"INSERT INTO {table_name} DEFAULT VALUES;",
        commit=True,
    )

    row = fetch_one(
        f"""
        SELECT {DB_PRIMARY_KEY_COL}
        FROM {table_name}
        ORDER BY {DB_PRIMARY_KEY_COL} DESC
        LIMIT 1;
        """
    )

    if not row:
        raise RuntimeError("Failed to obtain inserted row ID")

    return int(row[DB_PRIMARY_KEY_COL])

# =============================================================================
# 6.5 — Fill SWG Slot (INSERT PATH)
# =============================================================================
def _fill_swg_slot(
    *,
    table_name: str,
    row_id: int,
    swg_id: str,
    payload: Dict[str, Any],
) -> None:
    dt_col, a_col, r_col, soc_col = SWG_COLS_BY_ID[swg_id]

    sql = f"""
    UPDATE {table_name}
    SET
        {dt_col} = ?,
        {a_col} = ?,
        {r_col} = ?,
        {soc_col} = ?
    WHERE {DB_PRIMARY_KEY_COL} = ?;
    """

    execute_sql(
        sql,
        params=(
            payload["datetime"],
            payload["active"],
            payload["reactive"],
            payload["soc"],
            row_id,
        ),
        commit=True,
    )

# =============================================================================
# 6.6 — PUBLIC API: INSERT SWG DATA (FILL_NULL_QUEUE)
# =============================================================================
def save_repository_add_swg_row(
    *,
    swg_id: str,
    dt: str,
    active: Optional[float],
    reactive: Optional[float],
    soc: Optional[float],
) -> int:
    payload = _validate_swg_payload(
        swg_id=swg_id,
        dt=dt,
        active=active,
        reactive=reactive,
        soc=soc,
    )

    table_name = resolve_yearly_table_name(dt)

    row_id = _find_oldest_null_slot(table_name, swg_id)

    if row_id is None:
        row_id = _insert_empty_wide_row(table_name)

    _fill_swg_slot(
        table_name=table_name,
        row_id=row_id,
        swg_id=swg_id,
        payload=payload,
    )

    LOGGER.info(f"✅ INSERT {swg_id} → row {row_id}")
    return row_id

# =============================================================================
# 6.7 — PUBLIC API: UPDATE EXISTING SWG ROW (EDIT PATH)
# =============================================================================
def save_repository_update_swg_row(
    *,
    row_id: int,
    swg_id: str,
    dt: str,
    active: Optional[float],
    reactive: Optional[float],
    soc: Optional[float],
) -> None:
    if not isinstance(row_id, int) or row_id <= 0:
        raise ValueError("Invalid row_id")

    payload = _validate_swg_payload(
        swg_id=swg_id,
        dt=dt,
        active=active,
        reactive=reactive,
        soc=soc,
    )

    table_name = resolve_yearly_table_name(dt)
    dt_col, a_col, r_col, soc_col = SWG_COLS_BY_ID[swg_id]

    sql = f"""
    UPDATE {table_name}
    SET
        {dt_col} = ?,
        {a_col} = ?,
        {r_col} = ?,
        {soc_col} = ?
    WHERE {DB_PRIMARY_KEY_COL} = ?;
    """

    execute_sql(
        sql,
        params=(
            payload["datetime"],
            payload["active"],
            payload["reactive"],
            payload["soc"],
            row_id,
        ),
        commit=True,
    )

    LOGGER.info(f"✏️ UPDATE {swg_id} → row {row_id}")

# =============================================================================
# 6.8 — Defensive Guarantees
# =============================================================================
def _section_6_contract_assertions() -> None:
    assert MERGE_MODE == "FILL_NULL_QUEUE"
    assert TODAY_ONLY_ENFORCED is True
    assert len(SWG_IDS) == 3
    assert DB_PRIMARY_KEY_COL == "__id"

_section_6_contract_assertions()

LOGGER.info("✅ SECTION 6 loaded successfully — INSERT & UPDATE locked.")
# =============================================================================
# END SECTION 6
# =============================================================================
# =============================================================================
# =============================================================================
# SECTION 7 — Session State Initialization
# (FINAL VERSION • One-Page Workflow • Edit-Safe • Rerun-Proof)
# =============================================================================
# PURPOSE:
# - Initialize ALL Streamlit session_state keys safely
# - Guarantee stable behavior across reruns
# - Support:
#     ✅ Insert workflow
#     ✅ Edit-from-dashboard workflow
#     ✅ Copy / Edit / Apply cycle
# - Prevent:
#     ❌ Accidental state reset
#     ❌ Duplicate writes
#     ❌ Lost user edits
#
# HARD RULES (SECTION 7):
# ❌ NO UI rendering
# ❌ NO database access
# ❌ NO SQL execution
#
# GUARANTEE:
# ✅ After this section, UI (Section 8+) can safely read/write session_state
# =============================================================================

# =============================================================================
# 7.1 — Internal Helper: Safe Init (NEVER overwrite)
# =============================================================================
def _init_session_key(key: str, default: Any) -> None:
    """
    Initialize a session_state key ONLY if it does not exist.
    This function is rerun-safe and NEVER overwrites user data.
    """
    if key not in st.session_state:
        st.session_state[key] = default


# =============================================================================
# 7.2 — Core Page Lifecycle Flags
# =============================================================================
_init_session_key(SSK_PAGE_READY, False)
_init_session_key(SSK_LAST_ACTION, None)


# =============================================================================
# 7.3 — Datetime Input (Authoritative)
# =============================================================================
# Default = current local time, rounded to minute
_default_dt = safe_local_now().replace(second=0, microsecond=0)

_init_session_key(
    SSK_INPUT_DATETIME,
    _default_dt.strftime(DT_STORAGE_FORMAT),
)


# =============================================================================
# 7.4 — SWG Input Buffers (INSERT PATH)
# =============================================================================
# IMPORTANT:
# - None ≠ 0
# - None means "not entered yet"
# - Widgets will bind to these keys later (Section 10)

_init_session_key(SSK_INPUT_SWG1_ACTIVE, None)
_init_session_key(SSK_INPUT_SWG1_REACTIVE, None)
_init_session_key(SSK_INPUT_SWG1_SOC, None)

_init_session_key(SSK_INPUT_SWG2_ACTIVE, None)
_init_session_key(SSK_INPUT_SWG2_REACTIVE, None)
_init_session_key(SSK_INPUT_SWG2_SOC, None)

_init_session_key(SSK_INPUT_SWG3_ACTIVE, None)
_init_session_key(SSK_INPUT_SWG3_REACTIVE, None)
_init_session_key(SSK_INPUT_SWG3_SOC, None)


# =============================================================================
# 7.5 — Preview & Editing State
# =============================================================================
# PREVIEW_DF:
# - Holds TODAY wide-table preview
# - Source of truth for dashboard editor
#
# EDIT_BUFFER_DF:
# - Editable copy used by st.data_editor
# - Allows change detection

_init_session_key(SSK_PREVIEW_DF, None)
_init_session_key("edit_buffer_df", None)


# =============================================================================
# 7.6 — Text Generation & Edit Pipeline
# =============================================================================
# GENERATED_TEXT:
# - Auto-generated dispatch message
#
# EDITED_TEXT:
# - User-modified message
# - Clipboard-ready

_init_session_key(SSK_GENERATED_TEXT, "")
_init_session_key(SSK_EDITED_TEXT, "")


# =============================================================================
# 7.7 — Edit / Refresh Control Flags
# =============================================================================
# These flags CONTROL rerun behavior.
# They prevent Streamlit from:
# - Regenerating text while user is editing
# - Reloading preview after partial edits

_init_session_key("needs_preview_refresh", True)
_init_session_key("needs_text_regeneration", True)
_init_session_key("has_unsaved_edits", False)


# =============================================================================
# 7.8 — Edit Tracking (Row-Level)
# =============================================================================
# Tracks which DB rows were edited in UI
# Used to apply UPDATE safely

_init_session_key("edited_row_ids", set())


# =============================================================================
# 7.9 — Defensive Session Integrity Check
# =============================================================================
def _validate_session_state_integrity() -> None:
    """
    Fail fast if ANY required session key is missing.
    This prevents silent UI corruption.
    """
    required_keys = [
        # Core
        SSK_PAGE_READY,
        SSK_LAST_ACTION,

        # Datetime
        SSK_INPUT_DATETIME,

        # SWG Inputs
        SSK_INPUT_SWG1_ACTIVE, SSK_INPUT_SWG1_REACTIVE, SSK_INPUT_SWG1_SOC,
        SSK_INPUT_SWG2_ACTIVE, SSK_INPUT_SWG2_REACTIVE, SSK_INPUT_SWG2_SOC,
        SSK_INPUT_SWG3_ACTIVE, SSK_INPUT_SWG3_REACTIVE, SSK_INPUT_SWG3_SOC,

        # Preview & Edit
        SSK_PREVIEW_DF,
        "edit_buffer_df",

        # Text
        SSK_GENERATED_TEXT,
        SSK_EDITED_TEXT,

        # Control Flags
        "needs_preview_refresh",
        "needs_text_regeneration",
        "has_unsaved_edits",
        "edited_row_ids",
    ]

    missing = [k for k in required_keys if k not in st.session_state]

    if missing:
        raise RuntimeError(
            "❌ SESSION STATE INITIALIZATION FAILED\n"
            f"Missing keys: {missing}"
        )

_validate_session_state_integrity()


# =============================================================================
# 7.10 — Controlled Reset Utilities (STREAMLIT-SAFE)
# =============================================================================
def reset_insert_inputs() -> None:
    """
    Reset SWG input widgets SAFELY.

    Streamlit rule:
    ❌ Do NOT assign to session_state after widget creation
    ✅ Remove keys instead (pop)
    """
    for k in (
        SSK_INPUT_SWG1_ACTIVE,
        SSK_INPUT_SWG1_REACTIVE,
        SSK_INPUT_SWG1_SOC,
        SSK_INPUT_SWG2_ACTIVE,
        SSK_INPUT_SWG2_REACTIVE,
        SSK_INPUT_SWG2_SOC,
        SSK_INPUT_SWG3_ACTIVE,
        SSK_INPUT_SWG3_REACTIVE,
        SSK_INPUT_SWG3_SOC,
    ):
        if k in st.session_state:
            st.session_state.pop(k)


def reset_edit_state() -> None:
    """
    Reset edit-related flags AFTER successful DB UPDATE.
    """
    st.session_state["has_unsaved_edits"] = False
    st.session_state["edited_row_ids"] = set()
    st.session_state["needs_preview_refresh"] = True
    st.session_state["needs_text_regeneration"] = True


# =============================================================================
# 7.11 — Mark Page Ready (UI MAY START)
# =============================================================================
st.session_state[SSK_PAGE_READY] = True

LOGGER.info("✅ SECTION 7 loaded successfully — session state locked & Streamlit-safe.")
# =============================================================================
# END SECTION 7
# =============================================================================

# =============================================================================
# SECTION 8 — UI Styling & CSS
# (FINAL VERSION • Enterprise Dashboard • One-Page • Streamlit Safe)
# =============================================================================
# PURPOSE:
# - Define the GLOBAL visual identity of the dashboard
# - Provide reusable, stable CSS classes for:
#     ✅ Header + Live Clock (same height)
#     ✅ Input panels (SWG1 / SWG2 / SWG3)
#     ✅ Editable preview table
#     ✅ Action buttons (Insert / Apply Edit / Copy)
# - Ensure:
#     ✅ No layout shift on rerun
#     ✅ Premium enterprise appearance
#     ✅ CSS-only (NO LOGIC)
#
# HARD RULES (SECTION 8):
# ❌ NO database access
# ❌ NO SQL
# ❌ NO session_state mutation
# ❌ NO business logic
#
# GUARANTEE:
# ✅ Safe to re-run on every Streamlit refresh
# =============================================================================

# =============================================================================
# 8.1 — Enterprise CSS Injection (Single Source of Truth)
# =============================================================================
def inject_enterprise_ui_css() -> None:
    css = """
    <style>
    /* =====================================================================
       ROOT DESIGN TOKENS
       ===================================================================== */
    :root {
        --bg-main-1: #020617;
        --bg-main-2: #020f2a;

        --panel-bg-1: rgba(9, 32, 72, 0.92);
        --panel-bg-2: rgba(13, 45, 100, 0.78);

        --border-soft: rgba(120, 180, 255, 0.25);
        --border-strong: rgba(120, 180, 255, 0.55);

        --text-main: rgba(255,255,255,0.96);
        --text-muted: rgba(170,200,255,0.75);

        --blue-main: #2563eb;
        --blue-soft: #3b82f6;
        --green-ok: #22c55e;
        --red-bad: #ef4444;
        --yellow-warn: #facc15;

        --radius-xl: 22px;
        --radius-lg: 18px;
        --radius-md: 14px;
        --radius-sm: 10px;

        --shadow-strong: 0 22px 48px rgba(0,0,0,0.60);
        --shadow-soft: 0 12px 26px rgba(0,0,0,0.45);

        --font-main: ui-sans-serif, system-ui, -apple-system,
                     "Segoe UI", Roboto, Helvetica, Arial;
    }

    /* =====================================================================
       GLOBAL BACKGROUND
       ===================================================================== */
    html, body {
        background:
            radial-gradient(900px 520px at 15% -10%, rgba(59,130,246,0.22), transparent 60%),
            radial-gradient(700px 420px at 95% 0%, rgba(56,189,248,0.15), transparent 55%),
            linear-gradient(180deg, var(--bg-main-1), var(--bg-main-2)) !important;

        color: var(--text-main) !important;
        font-family: var(--font-main);
        height: 100%;
        overflow-x: hidden;
    }

    .stApp {
        background: transparent !important;
        min-height: 100vh !important;
    }

    /* =====================================================================
       STREAMLIT CHROME CLEANUP
       ===================================================================== */
    header, footer {
        visibility: hidden;
        height: 0px;
    }

    section.main {
        padding-top: 0.8rem !important;
        padding-bottom: 1.2rem !important;
    }

    .block-container {
        max-width: 98vw !important;
        padding: 0.6rem !important;
    }

    div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"] {
        background: transparent !important;
    }

    /* =====================================================================
       TYPOGRAPHY
       ===================================================================== */
    h1, h2, h3, h4 {
        color: var(--text-main) !important;
        font-weight: 900 !important;
        letter-spacing: 0.4px;
        margin-bottom: 0.3rem;
    }

    h5, h6 {
        color: var(--text-muted) !important;
        font-weight: 700 !important;
    }

    p, span, label, div {
        color: var(--text-main);
        font-size: 13px;
    }

    small {
        color: var(--text-muted);
    }

    /* =====================================================================
       HEADER + CLOCK ROW (MATCHED HEIGHT)
       ===================================================================== */
    .pd-header-row {
        display: grid;
        grid-template-columns: 1fr 360px;
        gap: 14px;
        margin-bottom: 14px;
    }

    .pd-header-card {
        height: 140px;
        padding: 18px 20px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* =====================================================================
       PREMIUM PANELS / CARDS
       ===================================================================== */
    .pd-card {
        background: linear-gradient(180deg, var(--panel-bg-1), var(--panel-bg-2));
        border-radius: var(--radius-lg);
        border: 1px solid var(--border-soft);
        box-shadow: var(--shadow-strong);
        padding: 16px 18px;
        margin-bottom: 14px;
        backdrop-filter: blur(10px);
    }

    .pd-card-tight {
        background: linear-gradient(180deg, rgba(9,32,72,0.95), rgba(13,45,100,0.80));
        border-radius: var(--radius-md);
        border: 1px solid var(--border-soft);
        box-shadow: var(--shadow-soft);
        padding: 12px 14px;
        margin-bottom: 12px;
        backdrop-filter: blur(10px);
    }

    /* =====================================================================
       INPUTS (TEXT / NUMBER / SELECT)
       ===================================================================== */
    input, textarea {
        background: rgba(10, 38, 86, 0.90) !important;
        color: var(--text-main) !important;
        border-radius: var(--radius-sm) !important;
        border: 1px solid var(--border-soft) !important;
    }

    input:focus, textarea:focus {
        outline: none !important;
        border-color: var(--blue-soft) !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.30) !important;
    }

    div[data-baseweb="select"] > div {
        background: rgba(10, 38, 86, 0.90) !important;
        border-radius: var(--radius-sm) !important;
        border: 1px solid var(--border-soft) !important;
        color: var(--text-main) !important;
    }

    /* =====================================================================
       BUTTONS (ENTERPRISE STANDARD)
       ===================================================================== */
    div.stButton > button {
        background: linear-gradient(180deg, #2563eb, #1e40af) !important;
        color: white !important;
        border-radius: var(--radius-md) !important;
        border: 1px solid var(--border-strong) !important;
        font-weight: 900 !important;
        letter-spacing: 0.4px;
        box-shadow: var(--shadow-soft);
        transition: all 0.15s ease-in-out;
    }

    div.stButton > button:hover {
        transform: translateY(-1px);
        background: linear-gradient(180deg, #3b82f6, #2563eb) !important;
        box-shadow: var(--shadow-strong);
    }

    div.stButton > button:active {
        transform: scale(0.98);
    }

    /* =====================================================================
       DATAFRAME / DATA_EDITOR STYLING
       ===================================================================== */
    thead th {
        background: rgba(12,42,90,0.98) !important;
        color: white !important;
        font-weight: 900 !important;
        text-align: center !important;
    }

    tbody td {
        background: rgba(7,22,50,0.88) !important;
        color: rgba(255,255,255,0.92) !important;
        text-align: center !important;
    }

    /* =====================================================================
       STATUS PILLS
       ===================================================================== */
    .pd-pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .pd-pill {
        padding: 6px 12px;
        border-radius: 999px;
        border: 1px solid var(--border-soft);
        background: rgba(5, 14, 32, 0.40);
        font-size: 12px;
        font-weight: 800;
        color: var(--text-muted);
    }

    .pd-pill-green {
        background: rgba(34,197,94,0.22);
        border-color: rgba(34,197,94,0.55);
        color: #dcfce7;
    }

    .pd-pill-red {
        background: rgba(239,68,68,0.22);
        border-color: rgba(239,68,68,0.55);
        color: #fee2e2;
    }

    /* =====================================================================
       SCROLLBAR (SUBTLE)
       ===================================================================== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(120,180,255,0.35);
        border-radius: 8px;
    }

    ::-webkit-scrollbar-track {
        background: transparent;
    }
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)

# =============================================================================
# 8.2 — Execute CSS Injection (SAFE ON EVERY RERUN)
# =============================================================================
inject_enterprise_ui_css()

LOGGER.info("🎨 SECTION 8 loaded successfully — enterprise UI locked.")
# =============================================================================
# END SECTION 8
# =============================================================================

# =============================================================================
# SECTION 9 — Header + Live Clock (BLUE GLASS • SIDE-BY-SIDE • FINAL)
# =============================================================================
# GUARANTEE:
# - Header and clock are in the SAME ROW
# - Same height (140px)
# - Same BLUE glass style
# - No Streamlit column bugs
# - No reruns for clock
# =============================================================================

# =============================================================================
# 9.1 — Stable App Start Time
# =============================================================================
_PD_APP_START_KEY = "__pd_app_started_at__"

if _PD_APP_START_KEY not in st.session_state:
    st.session_state[_PD_APP_START_KEY] = safe_local_now()

_PD_APP_STARTED_AT: datetime = st.session_state[_PD_APP_START_KEY]

# =============================================================================
# 9.2 — Header + Clock HTML (ONE CONTAINER • BLUE THEME)
# =============================================================================
def build_header_with_clock_html(started_at: datetime, tz_label: str) -> str:
    start_iso = started_at.strftime("%Y-%m-%dT%H:%M:%S")
    start_label = started_at.strftime("%Y-%m-%d %H:%M:%S")

    return f"""
    <style>
      .pd-top-row {{
        display:grid;
        grid-template-columns: 1fr 360px;
        gap:14px;
        margin-bottom:16px;
      }}

      /* =========================================================
         BLUE GLASS CARD (HEADER + CLOCK)
         ========================================================= */
      .pd-blue-glass {{
        height:140px;
        border-radius:18px;
        border:1px solid rgba(120,180,255,0.45);
        background: linear-gradient(
          135deg,
          rgba(37,99,235,0.28),
          rgba(2,12,36,0.94)
        );
        box-shadow:
          0 18px 42px rgba(0,0,0,0.55),
          inset 0 0 0 1px rgba(59,130,246,0.35);
        padding:16px 18px;
        box-sizing:border-box;
        color: rgba(240,248,255,0.97);
        font-family: ui-sans-serif, system-ui, -apple-system,
                     "Segoe UI", Roboto, Arial;
      }}

      .pd-header {{
        display:flex;
        flex-direction:column;
        justify-content:center;
      }}

      .pd-title {{
        font-size:22px;
        font-weight:980;
        letter-spacing:0.35px;
        display:flex;
        align-items:center;
        gap:10px;
      }}

      .pd-sub {{
        margin-top:6px;
        font-size:13px;
        color:#bfdbfe;
        line-height:1.4;
      }}

      .pd-pill-row {{
        margin-top:10px;
        display:flex;
        gap:8px;
      }}

      .pd-pill {{
        padding:6px 12px;
        border-radius:999px;
        font-size:12px;
        font-weight:800;
        border:1px solid rgba(120,180,255,0.45);
        background: rgba(37,99,235,0.25);
        color:#e0f2fe;
      }}

      /* =========================================================
         CLOCK
         ========================================================= */
      .pd-clock {{
        display:flex;
        flex-direction:column;
        justify-content:space-between;
        text-align:right;
      }}

      .pd-clock-time {{
        font-size:28px;
        font-weight:980;
        letter-spacing:0.9px;
      }}

      .pd-clock-meta {{
        font-size:12px;
        color:#c7ddff;
        line-height:1.4;
      }}
    </style>

    <div class="pd-top-row">
      <!-- LEFT: HEADER -->
      <div class="pd-blue-glass pd-header">
        <div class="pd-title">⚡ SWG Power Dispatch Dashboard</div>
        <div class="pd-sub">
          Single-Page • Queue-Safe Merge • SQLite Persistent Storage<br/>
          Operator Input • Live Preview • Editable Dispatch Log
        </div>
        <div class="pd-pill-row">
          <div class="pd-pill">DB: {DB_FILENAME}</div>
          <div class="pd-pill">Mode: LIVE</div>
          <div class="pd-pill">Merge: {MERGE_MODE}</div>
        </div>
      </div>

      <!-- RIGHT: CLOCK -->
      <div class="pd-blue-glass pd-clock">
        <div style="font-weight:900;">⏱ LIVE CLOCK</div>
        <div class="pd-clock-time" id="pd_clock_time">--:--:--</div>
        <div class="pd-clock-meta">
          <span id="pd_clock_date">----</span> • {tz_label}<br/>
          Started: {start_label}<br/>
          Uptime: <span id="pd_clock_uptime">00:00:00</span>
        </div>
      </div>
    </div>

    <script>
      (function() {{
        const startedAt = new Date("{start_iso}");
        function pad(n) {{ return String(n).padStart(2,"0"); }}

        function tick() {{
          const now = new Date();
          const diff = Math.floor((now - startedAt)/1000);

          document.getElementById("pd_clock_time").textContent =
            `${{pad(now.getHours())}}:${{pad(now.getMinutes())}}:${{pad(now.getSeconds())}}`;

          document.getElementById("pd_clock_date").textContent =
            `${{now.getFullYear()}}-${{pad(now.getMonth()+1)}}-${{pad(now.getDate())}}`;

          document.getElementById("pd_clock_uptime").textContent =
            `${{pad(Math.floor(diff/3600))}}:${{pad(Math.floor(diff%3600/60))}}:${{pad(diff%60)}}`;
        }}

        tick();
        setInterval(tick, 1000);
      }})();
    </script>
    """

# =============================================================================
# 9.3 — Render Section
# =============================================================================
st.components.v1.html(
    build_header_with_clock_html(
        started_at=_PD_APP_STARTED_AT,
        tz_label=DEFAULT_TIMEZONE_LABEL,
    ),
    height=160,
)

LOGGER.info("🔵 SECTION 9 loaded — BLUE header & clock aligned.")
# =============================================================================
# END SECTION 9
# =============================================================================
# =============================================================================
# SECTION 10 — FULL DASHBOARD UI (DISPATCH FORMAT v2)
# =============================================================================

# =============================================================================
# 10.0 — LOCAL UI CSS
# =============================================================================
st.markdown("""
<style>
.swg-bar{border-radius:16px;padding:14px;margin-bottom:14px;
box-shadow:0 14px 34px rgba(0,0,0,.45)}
.swg-green{background:linear-gradient(135deg,#064e3b,#22c55e)}
.swg-blue{background:linear-gradient(135deg,#1e3a8a,#3b82f6)}
.swg-orange{background:linear-gradient(135deg,#7c2d12,#fb923c)}
.swg-title{font-weight:900;letter-spacing:.4px;margin-bottom:8px}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 10.1 — SAFE HELPERS
# =============================================================================
def _safe_float(v):
    try:
        s = str(v).strip()
        return None if s == "" else float(s)
    except Exception:
        return None


def _load_today_preview_df(dt_str: str) -> pd.DataFrame:
    if not dt_str:
        return pd.DataFrame()

    try:
        start, end = get_today_range_strings()
        table = resolve_yearly_table_name(dt_str)

        sql = f"""
        SELECT *
        FROM {table}
        WHERE
            (SWG1_DateTime BETWEEN ? AND ?)
         OR (SWG2_DateTime BETWEEN ? AND ?)
         OR (SWG3_DateTime BETWEEN ? AND ?)
        ORDER BY {DB_PRIMARY_KEY_COL} DESC
        LIMIT 50
        """

        rows = fetch_all(sql, (start, end, start, end, start, end))
        return pd.DataFrame(rows)

    except Exception as e:
        st.error(f"Preview load failed: {e}")
        return pd.DataFrame()


# =============================================================================
# 10.2 — DISPATCH MESSAGE FORMAT (NEW)
# =============================================================================
def _generate_message_from_row(row: pd.Series) -> str:
    lines = ["START"]

    dt = (
        row.get("SWG1_DateTime")
        or row.get("SWG2_DateTime")
        or row.get("SWG3_DateTime")
    )

    if not dt:
        return ""

    lines.append(f"TIME={dt[:16]}")
    lines.append("")

    total_p = 0.0
    total_q = 0.0

    for swg in SWG_IDS:
        dt_c, a_c, q_c, s_c = SWG_COLS_BY_ID[swg]

        if pd.isna(row.get(dt_c)):
            continue

        p = float(row.get(a_c) or 0)
        q = float(row.get(q_c) or 0)
        soc = float(row.get(s_c) or 0)

        total_p += p
        total_q += q

        swg_no = swg.replace("SWG", "SWG0")

        lines.append(
            f"#{swg_no}: "
            f"P={int(p) if p.is_integer() else p}Mw, "
            f"Q={int(q) if q.is_integer() else q}Mvar, "
            f"SOC={int(soc) if soc.is_integer() else soc}%"
        )

    lines.append("")
    lines.append(
        f"#TOTAL:P={int(total_p) if total_p.is_integer() else total_p}Mw, "
        f"Q={int(total_q) if total_q.is_integer() else total_q}Mvar"
    )

    return "\n".join(lines)


# =============================================================================
# 10.3 — SECTION HEADER
# =============================================================================
st.markdown("""
<div class="pd-card">
<h3>🧾 INPUT DATA PANELS — SWG1 / SWG2 / SWG3</h3>
<small>TODAY ONLY • QUEUE SAFE • DATABASE BACKED</small>
</div>
""", unsafe_allow_html=True)

left, right = st.columns([3.2, 1.6], gap="large")

# =============================================================================
# LEFT — INPUT + TABLE
# =============================================================================
with left:
    c1, c2, c3 = st.columns(3, gap="medium")

    def render_swg_bar(swg, label, css, kA, kQ, kS, btn):
        st.markdown(f"<div class='swg-bar {css}'>", unsafe_allow_html=True)
        st.markdown(f"<div class='swg-title'>⚡ {label}</div>", unsafe_allow_html=True)

        a = st.text_input("Active Power (MW)", key=kA)
        q = st.text_input("Reactive Power (Mvar)", key=kQ)
        s = st.text_input("SOC (%)", key=kS)

        if st.button(f"ADD {label}", key=btn, use_container_width=True):
            save_repository_add_swg_row(
                swg_id=swg,
                dt=st.session_state[SSK_INPUT_DATETIME],
                active=_safe_float(a),
                reactive=_safe_float(q),
                soc=_safe_float(s),
            )
            reset_insert_inputs()
            st.session_state["needs_preview_refresh"] = True
            st.success(f"{label} saved")
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with c1:
        render_swg_bar("SWG1","SWG01","swg-green",
                       SSK_INPUT_SWG1_ACTIVE,SSK_INPUT_SWG1_REACTIVE,SSK_INPUT_SWG1_SOC,BTN_ADD_SWG1)
    with c2:
        render_swg_bar("SWG2","SWG02","swg-blue",
                       SSK_INPUT_SWG2_ACTIVE,SSK_INPUT_SWG2_REACTIVE,SSK_INPUT_SWG2_SOC,BTN_ADD_SWG2)
    with c3:
        render_swg_bar("SWG3","SWG03","swg-orange",
                       SSK_INPUT_SWG3_ACTIVE,SSK_INPUT_SWG3_REACTIVE,SSK_INPUT_SWG3_SOC,BTN_ADD_SWG3)

    # ---------------- TABLE PREVIEW ----------------
    st.markdown("<div class='pd-card-tight'><b>📊 TABLE PREVIEW — TODAY (DB)</b></div>",
                unsafe_allow_html=True)

    if st.session_state.get("needs_preview_refresh", True):
        df = _load_today_preview_df(st.session_state[SSK_INPUT_DATETIME])
        st.session_state[SSK_PREVIEW_DF] = df
        st.session_state["edit_buffer_df"] = df.copy()
        st.session_state["needs_preview_refresh"] = False
        st.session_state["needs_text_regeneration"] = True

    if st.session_state[SSK_PREVIEW_DF].empty:
        st.info("No data yet for today.")
    else:
        edited = st.data_editor(
            st.session_state["edit_buffer_df"],
            num_rows="fixed",
            use_container_width=True,
            height=280,
        )
        if not edited.equals(st.session_state["edit_buffer_df"]):
            st.session_state["edit_buffer_df"] = edited
            st.session_state["has_unsaved_edits"] = True


# =============================================================================
# RIGHT — MESSAGE / APPLY / COPY
# =============================================================================
with right:
    st.markdown("<div class='pd-card-tight'><b>📝 MESSAGE SUMMARY & EDIT</b></div>",
                unsafe_allow_html=True)

    if (
        st.session_state.get("needs_text_regeneration")
        and not st.session_state[SSK_PREVIEW_DF].empty
    ):
        row = st.session_state[SSK_PREVIEW_DF].iloc[0]
        msg = _generate_message_from_row(row)
        st.session_state[SSK_GENERATED_TEXT] = msg
        st.session_state[SSK_EDITED_TEXT] = msg
        st.session_state["needs_text_regeneration"] = False

    st.text_area(
        "Dispatch",
        key=SSK_EDITED_TEXT,
        height=260,
        label_visibility="collapsed",
    )

    if st.button("💾 APPLY EDIT", key=BTN_APPLY_EDIT, use_container_width=True):
        for _, row in st.session_state["edit_buffer_df"].iterrows():
            row_id = int(row[DB_PRIMARY_KEY_COL])
            for swg in SWG_IDS:
                dt_c,a_c,q_c,s_c = SWG_COLS_BY_ID[swg]
                if not pd.isna(row.get(dt_c)):
                    save_repository_update_swg_row(
                        row_id=row_id,
                        swg_id=swg,
                        dt=row.get(dt_c),
                        active=row.get(a_c),
                        reactive=row.get(q_c),
                        soc=row.get(s_c),
                    )
        reset_edit_state()
        st.success("Database updated")
        st.rerun()

    if st.button("📋 COPY TEXT", key=BTN_COPY_TEXT, use_container_width=True):
        st.code(st.session_state[SSK_EDITED_TEXT], language="text")
        st.success("Copied — ready for Telegram / Discord")

# =============================================================================
# SECTION 11 — DATA EXPORT & DOWNLOAD (CUSTOM HTML • GREEN THEME)
# =============================================================================
# FEATURES:
# - TRUE custom UI (NO st.download_button)
# - CSV / XLSX / JSON
# - All GREEN buttons
# - Read-only
# - TODAY only
# - Enterprise-grade styling
# =============================================================================

import base64
import io
import json

# =============================================================================
# 11.0 — CUSTOM DOWNLOAD CSS (ENTERPRISE GREEN)
# =============================================================================
st.markdown(
    """
    <style>
    /* ============================================================
       CUSTOM DOWNLOAD BUTTONS
       ============================================================ */

    .dl-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 22px;
        margin-top: 12px;
    }

    .dl-btn {
        height: 44px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;

        font-weight: 900;
        letter-spacing: 0.4px;
        font-size: 14px;
        text-decoration: none !important;
        color: #ecfdf5 !important;

        background: linear-gradient(
            180deg,
            #16a34a,
            #15803d
        );

        border: 1px solid rgba(34,197,94,0.65);

        box-shadow:
            0 10px 26px rgba(0,0,0,0.55),
            inset 0 0 0 1px rgba(34,197,94,0.35);

        transition: all .15s ease;
    }

    .dl-btn:hover {
        filter: brightness(1.08);
        transform: translateY(-1px);
        box-shadow:
            0 14px 32px rgba(0,0,0,0.65),
            inset 0 0 0 1px rgba(34,197,94,0.55);
    }

    .dl-btn:active {
        transform: translateY(0);
        filter: brightness(.97);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# 11.1 — LOAD TODAY DATA (READ-ONLY)
# =============================================================================
def _load_today_export_df() -> pd.DataFrame:
    start, end = get_today_range_strings()
    table = resolve_yearly_table_name(safe_local_now())

    sql = f"""
    SELECT *
    FROM {table}
    WHERE
        (SWG1_DateTime BETWEEN ? AND ?)
        OR (SWG2_DateTime BETWEEN ? AND ?)
        OR (SWG3_DateTime BETWEEN ? AND ?)
    ORDER BY {DB_PRIMARY_KEY_COL} ASC;
    """

    rows = fetch_all(
        sql,
        params=(start, end, start, end, start, end),
    )

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    cols = [DB_PRIMARY_KEY_COL] + [
        c for c in SWG_WIDE_COLS if c in df.columns
    ]
    return df[cols]


# =============================================================================
# 11.2 — FILE BUILDERS (PURE)
# =============================================================================
def _build_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def _build_json_bytes(df: pd.DataFrame) -> bytes:
    return json.dumps(
        df.to_dict(orient="records"),
        indent=2,
        default=str,
    ).encode("utf-8")


def _build_xlsx_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()

    engine = None
    if AVAILABLE_XLSXWRITER:
        engine = "xlsxwriter"
    elif AVAILABLE_OPENPYXL:
        engine = "openpyxl"
    else:
        raise RuntimeError("XLSX export requires xlsxwriter or openpyxl")

    with pd.ExcelWriter(buf, engine=engine) as writer:
        df.to_excel(writer, index=False, sheet_name="SWG_TODAY")

    return buf.getvalue()


# =============================================================================
# 11.3 — SECTION HEADER
# =============================================================================
st.markdown(
    """
    <div class="pd-card">
      <h3>⬇️ DATA EXPORT — TODAY</h3>
      <small>PURE HTML • CSV / XLSX / JSON • READ-ONLY</small>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# 11.4 — PREPARE DOWNLOAD FILES
# =============================================================================
df_export = _load_today_export_df()

if df_export.empty:
    st.info("No data available for download today.")
else:
    csv_b64 = base64.b64encode(
        _build_csv_bytes(df_export)
    ).decode()

    json_b64 = base64.b64encode(
        _build_json_bytes(df_export)
    ).decode()

    xlsx_b64 = base64.b64encode(
        _build_xlsx_bytes(df_export)
    ).decode()

    # =============================================================================
    # 11.5 — CUSTOM DOWNLOAD BUTTONS (HTML)
    # =============================================================================
    st.markdown(
        f"""
        <div class="dl-row">

          <a class="dl-btn"
             download="SWG_TODAY_{get_today_date().strftime('%Y%m%d')}.csv"
             href="data:text/csv;base64,{csv_b64}">
             ⬇️ DOWNLOAD CSV
          </a>

          <a class="dl-btn"
             download="SWG_TODAY_{get_today_date().strftime('%Y%m%d')}.xlsx"
             href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{xlsx_b64}">
             ⬇️ DOWNLOAD XLSX
          </a>

          <a class="dl-btn"
             download="SWG_TODAY_{get_today_date().strftime('%Y%m%d')}.json"
             href="data:application/json;base64,{json_b64}">
             ⬇️ DOWNLOAD JSON
          </a>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="pd-card-tight">
          <b>Rows:</b> {len(df_export)} &nbsp;|&nbsp;
          <b>Date:</b> {get_today_date().strftime(DATE_STORAGE_FORMAT)}
        </div>
        """,
        unsafe_allow_html=True,
    )

LOGGER.info("⬇️ SECTION 11 loaded — CUSTOM HTML download ready.")
# =============================================================================
# END SECTION 11
# =============================================================================

# =============================================================================
# SECTION 12 — EDITABLE DATA (DASHBOARD ↔ DB SYNC)
# (FINAL • TODAY ONLY • EDIT SAFE • ENTERPRISE)
# =============================================================================
# PURPOSE:
# - Allow operator to EDIT today’s data directly
# - Changes update BOTH:
#     ✅ SQLite database
#     ✅ Dashboard state
# - Edits affect:
#     • Preview
#     • Dispatch message
#     • Downloaded files (Section 11)
#
# HARD RULES:
# ❌ No schema changes
# ❌ No historical edits
# ❌ No silent DB writes
# =============================================================================

# =============================================================================
# 12.1 — Section Header
# =============================================================================
st.markdown(
    """
    <div class="pd-card">
      <h3>✏️ EDIT TODAY DATA — LIVE SYNC</h3>
      <small>
        Dashboard ↔ Database • TODAY ONLY • Explicit Apply Required
      </small>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# 12.2 — Load Editable Dataset (TODAY ONLY)
# =============================================================================
def _load_today_editable_df() -> pd.DataFrame:
    """
    Load TODAY data for editing.
    Read-only query; updates happen via repository.
    """
    start, end = get_today_range_strings()
    table = resolve_yearly_table_name(safe_local_now())

    sql = f"""
    SELECT *
    FROM {table}
    WHERE
        (SWG1_DateTime BETWEEN ? AND ?)
     OR (SWG2_DateTime BETWEEN ? AND ?)
     OR (SWG3_DateTime BETWEEN ? AND ?)
    ORDER BY {DB_PRIMARY_KEY_COL} ASC;
    """

    rows = fetch_all(
        sql,
        params=(start, end, start, end, start, end),
    )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Enforce column order
    ordered_cols = [DB_PRIMARY_KEY_COL] + [
        c for c in SWG_WIDE_COLS if c in df.columns
    ]

    return df[ordered_cols]


# =============================================================================
# 12.3 — Initialize Edit Buffer (Rerun Safe)
# =============================================================================
if "editable_df" not in st.session_state:
    st.session_state["editable_df"] = _load_today_editable_df()

if "editable_df_original" not in st.session_state:
    st.session_state["editable_df_original"] = (
        st.session_state["editable_df"].copy()
        if st.session_state["editable_df"] is not None
        else None
    )

# =============================================================================
# 12.4 — Empty State
# =============================================================================
if st.session_state["editable_df"].empty:
    st.info("No data available for editing today.")
    st.stop()

# =============================================================================
# 12.5 — Editable Data Editor
# =============================================================================
edited_df = st.data_editor(
    st.session_state["editable_df"],
    use_container_width=True,
    num_rows="fixed",
    height=360,
)

# Detect changes
if not edited_df.equals(st.session_state["editable_df"]):
    st.session_state["editable_df"] = edited_df
    st.session_state["has_unsaved_edits"] = True

# =============================================================================
# 12.6 — Apply Changes to Database
# =============================================================================
st.markdown("<br/>", unsafe_allow_html=True)

apply_col, refresh_col = st.columns([1.2, 1.0])

with apply_col:
    if st.button(
        "💾 APPLY CHANGES TO DATABASE",
        use_container_width=True,
        disabled=not st.session_state.get("has_unsaved_edits", False),
    ):
        df_new = st.session_state["editable_df"]
        df_old = st.session_state["editable_df_original"]

        updated_rows = 0

        for idx, new_row in df_new.iterrows():
            old_row = df_old.loc[idx]

            row_id = int(new_row[DB_PRIMARY_KEY_COL])

            for swg in SWG_IDS:
                dt_c, a_c, r_c, s_c = SWG_COLS_BY_ID[swg]

                # Only update if this SWG exists in this row
                if pd.isna(new_row.get(dt_c)):
                    continue

                # Detect field-level changes
                changed = False
                for col in (dt_c, a_c, r_c, s_c):
                    if not pd.isna(new_row[col]) or not pd.isna(old_row[col]):
                        if normalize_to_none(new_row[col]) != normalize_to_none(old_row[col]):
                            changed = True
                            break

                if not changed:
                    continue

                save_repository_update_swg_row(
                    row_id=row_id,
                    swg_id=swg,
                    dt=new_row[dt_c],
                    active=new_row[a_c],
                    reactive=new_row[r_c],
                    soc=new_row[s_c],
                )

                updated_rows += 1

        # Reset state
        st.session_state["editable_df_original"] = df_new.copy()
        st.session_state["has_unsaved_edits"] = False

        # Force refresh downstream sections
        st.session_state["needs_preview_refresh"] = True
        st.session_state["needs_text_regeneration"] = True

        st.success(f"✅ Database updated successfully ({updated_rows} SWG updates)")
        st.rerun()

with refresh_col:
    if st.button("🔄 RELOAD FROM DATABASE", use_container_width=True):
        st.session_state["editable_df"] = _load_today_editable_df()
        st.session_state["editable_df_original"] = (
            st.session_state["editable_df"].copy()
        )
        st.session_state["has_unsaved_edits"] = False
        st.success("Reloaded from database")
        st.rerun()

# =============================================================================
# 12.7 — Operator Safety Notice
# =============================================================================
st.markdown(
    """
    <div class="pd-card-tight">
      ⚠️ <b>Important:</b><br/>
      • Only TODAY data can be edited<br/>
      • Changes affect dispatch message & downloads<br/>
      • Use “Reload” to discard unsaved changes
    </div>
    """,
    unsafe_allow_html=True,
)

LOGGER.info("✏️ SECTION 12 loaded — editable data fully synchronized.")
# =============================================================================
# END SECTION 12
# =============================================================================
