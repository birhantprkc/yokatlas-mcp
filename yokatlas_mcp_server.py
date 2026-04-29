"""
YOKATLAS MCP Server - Turkish Higher Education Atlas API (yokatlas-py v0.6.0+)

YÖK Atlas tercih kılavuzu JSON API'sine MCP üzerinden erişim sağlar.
Lisans/önlisans programları arar, üniversite/program/il lookup tablolarını sunar.

Önemli: v0.6.0 ile YÖK Atlas Nisan 2026 SPA geçişi sonrası detaylı atlas
verileri (cinsiyet/lise alanı dağılımı, akademisyen ünvan dağılımı, KPSS
yıllara göre, vb.) site genelinden kaldırıldığı için API tarafından da
sunulmuyor. Search response'u her programa ait 4 yıllık (current + 3 history)
temel istatistikleri içerir.
"""

from __future__ import annotations

import asyncio
import atexit
import logging
from typing import Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from yokatlas_py import AsyncYokAtlasClient, SearchFilters
from yokatlas_py.exceptions import (
    APIError,
    LookupError as YokLookupError,
    NotFoundError,
    RateLimitError,
    YokAtlasError,
)

__all__ = ["app", "main"]

logger = logging.getLogger(__name__)

app = FastMCP(
    name="YOKATLAS API Server",
    instructions=(
        "MCP server for the Turkish Higher Education Atlas (YÖKATLAS) tercih "
        "kılavuzu JSON API. Provides smart-search over bachelor's and "
        "associate-degree programs (4-year stats per program) and lookup "
        "tables for universities, program groups, and cities."
    ),
)


# ---------------------------------------------------------------------------
# Async client (lazy singleton)
# ---------------------------------------------------------------------------

_client: AsyncYokAtlasClient | None = None
_client_lock = asyncio.Lock()


async def _get_client() -> AsyncYokAtlasClient:
    global _client
    if _client is None:
        async with _client_lock:
            if _client is None:
                _client = AsyncYokAtlasClient()
    return _client


def _cleanup_client() -> None:
    global _client
    if _client is None:
        return
    try:
        asyncio.run(_client.aclose())
    except RuntimeError:
        # Event loop already closed during interpreter shutdown.
        pass


atexit.register(_cleanup_client)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DEGREE_TO_BIRIM_TURU: dict[str, int] = {"bachelor": 46, "associate": 47}


def _format_yok_error(exc: YokAtlasError) -> dict[str, Any]:
    """Render a yokatlas-py exception as a structured error dict."""
    if isinstance(exc, YokLookupError):
        return {
            "error": "lookup_failed",
            "details": str(exc),
            "name": exc.name,
            "kind": exc.kind,
            "suggestions": exc.suggestions,
        }
    if isinstance(exc, RateLimitError):
        return {
            "error": "rate_limit",
            "details": str(exc),
            "status_code": exc.status_code,
        }
    if isinstance(exc, NotFoundError):
        return {
            "error": "not_found",
            "details": str(exc),
            "status_code": exc.status_code,
        }
    if isinstance(exc, APIError):
        return {
            "error": "api_error",
            "details": str(exc),
            "status_code": exc.status_code,
            "body": exc.body,
        }
    return {"error": "yokatlas_error", "details": str(exc)}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@app.tool()
async def search_programs(
    degree_type: Literal["bachelor", "associate"] | None = Field(
        default=None,
        description=(
            "Program level: 'bachelor' (lisans, birim_turu_id=46) or "
            "'associate' (önlisans, birim_turu_id=47). Omit to return both."
        ),
    ),
    puan_turu: Literal["SAY", "SÖZ", "EA", "DİL", "TYT", "SOZ", "DIL"] | None = Field(
        default=None,
        description=(
            "Score type. SAY (Science), SÖZ/SOZ (Verbal), EA (Equal Weight), "
            "DİL/DIL (Language), TYT (basic placement, used for associate "
            "degree). ASCII variants (SOZ/DIL) are auto-normalized."
        ),
    ),
    universite: str | None = Field(
        default=None,
        description=(
            "University name with smart fuzzy matching (e.g. 'boğaziçi' → "
            "'BOĞAZİÇİ ÜNİVERSİTESİ'). Turkish-aware normalization."
        ),
    ),
    program: str | None = Field(
        default=None,
        description=(
            "Program group name with smart fuzzy matching (e.g. 'bilgisayar' "
            "→ 'Bilgisayar Mühendisliği'). Matches the program-group field."
        ),
    ),
    il: str | None = Field(
        default=None,
        description="City name with smart fuzzy matching (e.g. 'ankara').",
    ),
    universite_turu: Literal["DEVLET", "VAKIF"] | None = Field(
        default=None,
        description="University type: DEVLET (state) or VAKIF (foundation).",
    ),
    kilavuz_kodu: int | None = Field(
        default=None,
        description=(
            "ÖSYM kılavuz kodu — filters to a single program. Use this for "
            "single-program lookup (e.g. 102210277)."
        ),
    ),
    min_basari_sirasi: int | None = Field(
        default=None,
        description="Minimum success ranking (lower bound, inclusive).",
    ),
    max_basari_sirasi: int | None = Field(
        default=None,
        description="Maximum success ranking (upper bound, inclusive).",
    ),
    page: int = Field(
        default=0,
        ge=0,
        description="Page number, 0-indexed.",
    ),
    size: int = Field(
        default=20,
        ge=1,
        le=500,
        description="Page size (max 500).",
    ),
    sort_by: str = Field(
        default="basariSirasi",
        description=(
            "Sort field (camelCase). Common values: basariSirasi, minPuan, "
            "kontenjan, gkY (yerleşen)."
        ),
    ),
    direction: Literal["ASC", "DESC"] = Field(
        default="ASC",
        description="Sort direction.",
    ),
) -> dict[str, Any]:
    """
    Search YÖKATLAS programs with smart fuzzy matching across the whole
    tercih kılavuzu (lisans + önlisans).

    Each result already contains 4-year statistics (current year + 3
    historical years): kontenjan, yerlesen, min_puan, basari_sirasi,
    KPSS scores, academic-staff counts.

    Use `kilavuz_kodu` to fetch a single program.
    """
    filter_kwargs: dict[str, Any] = {}

    if degree_type is not None:
        filter_kwargs["birim_turu_id"] = _DEGREE_TO_BIRIM_TURU[degree_type]
    if puan_turu is not None:
        filter_kwargs["puan_turu"] = puan_turu
    if universite is not None:
        filter_kwargs["universite"] = universite
    if program is not None:
        filter_kwargs["program"] = program
    if il is not None:
        filter_kwargs["il"] = il
    if universite_turu is not None:
        filter_kwargs["universite_turu"] = universite_turu
    if kilavuz_kodu is not None:
        filter_kwargs["kilavuz_kodu"] = kilavuz_kodu
    if min_basari_sirasi is not None:
        filter_kwargs["min_basari_sirasi"] = min_basari_sirasi
    if max_basari_sirasi is not None:
        filter_kwargs["max_basari_sirasi"] = max_basari_sirasi

    try:
        filters = SearchFilters(**filter_kwargs)
    except Exception as exc:
        logger.warning("Invalid search filters: %s", exc)
        return {"error": "invalid_filters", "details": str(exc)}

    try:
        client = await _get_client()
        result_page = await client.search(
            filters,
            page=page,
            size=size,
            sort_by=sort_by,
            direction=direction,
        )
        return result_page.model_dump(mode="json")
    except YokAtlasError as exc:
        logger.warning("YÖKATLAS error in search_programs: %s", exc)
        return _format_yok_error(exc)
    except Exception as exc:
        logger.exception("Unexpected error in search_programs")
        return {"error": "internal_error", "details": str(exc)}


@app.tool()
async def list_universities() -> dict[str, Any]:
    """
    List all universities known to YÖKATLAS (≈221 entries).

    Returns each university's `universite_id` (int) and `universite_adi`
    (str). Useful for resolving fuzzy university names to IDs or for
    populating UI selectors.
    """
    try:
        client = await _get_client()
        unis = await client.list_universities()
        return {
            "count": len(unis),
            "universities": [u.model_dump(mode="json") for u in unis],
        }
    except YokAtlasError as exc:
        logger.warning("YÖKATLAS error in list_universities: %s", exc)
        return _format_yok_error(exc)
    except Exception as exc:
        logger.exception("Unexpected error in list_universities")
        return {"error": "internal_error", "details": str(exc)}


@app.tool()
async def list_program_groups() -> dict[str, Any]:
    """
    List all program groups (birim grupları) — i.e. the canonical program
    names used in YÖKATLAS (e.g. 'Bilgisayar Mühendisliği', 'Tıp').

    Each entry has `birim_grup_id` (int), `birim_grup_adi` (str), and
    `puan_turu` (str). Useful for discovering valid program filter values.
    """
    try:
        client = await _get_client()
        groups = await client.list_program_groups()
        return {
            "count": len(groups),
            "program_groups": [g.model_dump(mode="json") for g in groups],
        }
    except YokAtlasError as exc:
        logger.warning("YÖKATLAS error in list_program_groups: %s", exc)
        return _format_yok_error(exc)
    except Exception as exc:
        logger.exception("Unexpected error in list_program_groups")
        return {"error": "internal_error", "details": str(exc)}


@app.tool()
async def list_cities() -> dict[str, Any]:
    """
    List all Turkish cities (iller) recognized by YÖKATLAS.

    Each entry has `il_kodu` (int) and `il_adi` (str).
    """
    try:
        client = await _get_client()
        cities = await client.list_cities()
        return {
            "count": len(cities),
            "cities": [c.model_dump(mode="json") for c in cities],
        }
    except YokAtlasError as exc:
        logger.warning("YÖKATLAS error in list_cities: %s", exc)
        return _format_yok_error(exc)
    except Exception as exc:
        logger.exception("Unexpected error in list_cities")
        return {"error": "internal_error", "details": str(exc)}


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    """Main entry point for the YOKATLAS MCP server."""
    app.run()


if __name__ == "__main__":
    main()
