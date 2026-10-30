from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any

from modules.parsing import parse_bool, parse_number, parse_text
from modules.schema import BY_NAME

_WS = re.compile(r"\s+")
_PUNCT_EDGE = re.compile(r"^[\s\W_]+|[\s\W_]+$")
_COMPANY_SUFFIX = re.compile(
    r"\b(sdn\.?\s*bhd\.?|bhd\.?|pte\.?\s*ltd\.?|co\.?,?\s*ltd\.?|ltd\.?|llc|inc\.?|"
    r"corp\.?|corporation|gmbh|s\.?a\.?|plc|pvt\.?)\b", re.IGNORECASE)

_DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%d-%m-%Y", "%d/%m/%Y",
                 "%d.%m.%Y", "%m/%d/%Y", "%m-%d-%Y", "%d-%m-%y", "%d/%m/%y",
                 "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y",
                 "%d%b%Y", "%Y%m%d")

CURRENCY_ALIASES = {"RM": "MYR", "$": "USD", "US$": "USD", "USD$": "USD",
                    "€": "EUR", "£": "GBP", "S$": "SGD", "RMB": "CNY", "¥": "JPY"}


def norm_text(v: Any) -> str | None:
    if v is None:
        return None
    if parse_text(v) is None:
        return None              # "N/A", "-", "not found" are nulls, not values
    s = unicodedata.normalize("NFKC", str(v))
    s = _WS.sub(" ", s).strip().lower()
    s = _PUNCT_EDGE.sub("", s)
    return s or None


def norm_company(v: Any) -> str | None:
    s = norm_text(v)
    if s is None:
        return None
    s = _COMPANY_SUFFIX.sub("", s)
    s = _WS.sub(" ", s).strip(" .,-")
    return s or None


def norm_number(v: Any) -> float | None:
    return parse_number(v)       # shared with the extraction contract


def norm_money(v: Any) -> float | None:
    n = norm_number(v)
    return None if n is None else round(n, 2)


def norm_date(v: Any) -> str | None:
    if v is None:
        return None
    s = _WS.sub(" ", str(v)).strip().rstrip(".,")
    for f in _DATE_FORMATS:
        try:
            return datetime.strptime(s, f).date().isoformat()
        except ValueError:
            continue
    return norm_text(s)      # unparseable: compare as text, do not silently drop


def norm_currency(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip().upper()
    return CURRENCY_ALIASES.get(s, s) or None


def norm_bool(v: Any) -> bool | None:
    return parse_bool(v)         # None == "not attempted", distinct from False


_BY_RULE = {"text": norm_text, "date": norm_date, "money": norm_money,
            "number": norm_number, "bool": norm_bool,
            "passthrough": lambda v: v}

_BY_FIELD = {"shipper_name": norm_company, "consignee_name": norm_company,
             "carrier_name": norm_company, "currency": norm_currency}


def norm_field(name: str, v: Any) -> Any:
    if name in _BY_FIELD:
        return _BY_FIELD[name](v)
    spec = BY_NAME.get(name)
    return _BY_RULE.get(spec.norm if spec else "text", norm_text)(v)


def norm_schema(d: dict[str, Any]) -> dict[str, Any]:
    out = {k: norm_field(k, v) for k, v in d.items() if k in BY_NAME}
    if isinstance(out.get("line_items"), list):
        out["line_items"] = [norm_line_item(r) for r in out["line_items"]
                             if isinstance(r, dict)]
    return out


def norm_line_item(row: dict[str, Any]) -> dict[str, Any]:
    from modules.schema import LINE_ITEM_SPECS
    specs = {s.name: s for s in LINE_ITEM_SPECS}
    out: dict[str, Any] = {}
    for k, spec in specs.items():
        out[k] = _BY_RULE[spec.norm](row.get(k))
    return out
