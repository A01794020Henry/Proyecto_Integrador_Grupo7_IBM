#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrae definiciones SPN del PDF J1939-71 y genera j1939_71_reference.json para RAG.

Patrón esperado por bloque (insensible a mayúsculas/minúsculas):
    spn<id> - <Nombre> - <Descripción>
    Data Length: <n> <bytes/bits>
    Resolution: <factor> <unidad>/bit , <offset> offset
    Data Range: <min> to <max> <unidad?>
    Type: <Measured/Status/...>
    Suspect Parameter Number: <id>
    Parameter Group Number: [<pgn1>] [<pgn2>] ...

El parser es heurístico para ser robusto ante variaciones del PDF; genera la lista
de "spns" encontrada y una lista "pgns" mínima basada en la asociación SPN->PGN
(sin posiciones bit; esas provendrán del DBC).

Uso (PowerShell):
    py .\build_j1939_json.py \
        --pdf "c:\Users\henry\Documents\GitHub\Proyecto_Integrador_Grupo7_IBM\Entrega4_Precision_Semantica_y_Contextualizacion_Eventos_Vehiculares\J1939-71.pdf" \
        --out "c:\Users\henry\Documents\GitHub\Proyecto_Integrador_Grupo7_IBM\Entrega4_Precision_Semantica_y_Contextualizacion_Eventos_Vehiculares\j1939_71_reference.json"
"""
from __future__ import annotations
import argparse
import datetime
import json
import re
from pathlib import Path


def try_read_pdf_preview(pdf_path: Path, pages: int = 3) -> str:
    try:
        import pdfplumber  # type: ignore
    except Exception:
        return ""
    if not pdf_path.exists():
        return ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            n = min(pages, len(pdf.pages))
            texts = []
            for i in range(n):
                txt = pdf.pages[i].extract_text() or ""
                texts.append(txt)
            return "\n---\n".join(texts)
    except Exception:
        return ""

def ensure_package(pkg: str) -> None:
    try:
        __import__(pkg)
    except Exception:
        import subprocess, sys
        print(f"Instalando dependencia {pkg}…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

def read_pdf_all_text(pdf_path: Path) -> str:
    try:
        import pdfplumber  # type: ignore
    except Exception:
        return ""
    if not pdf_path.exists():
        return ""
    chunks: list[str] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for pg in pdf.pages:
                chunks.append(pg.extract_text() or "")
        return "\n\n".join(chunks)
    except Exception:
        return ""

def _num(s: str) -> float | None:
    s2 = s.strip().replace(",", "")
    try:
        return float(s2)
    except Exception:
        return None

def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def parse_spn_blocks(full_text: str) -> list[dict]:
    if not full_text:
        return []
    block_re = re.compile(
        r"(?is)\bspn\s*([0-9]{3,6})\s*-\s*(.+?)\s*-\s*(.+?)\s*"
        r"Data\s+Length:\s*([^\n]+)\n"
        r"Resolution:\s*([^\n]+)\n"
        r"Data\s+Range:\s*([^\n]+)\n"
        r"Type:\s*([^\n]+)\n"
        r"Suspect\s+Parameter\s+Number:\s*([0-9]{3,6})\n"
        r"Parameter\s+Group\s+Number:\s*([^\n]+?)\s*(?=\n\s*spn\s*[0-9]{3,6}\s*-|\Z)"
    )

    items: list[dict] = []
    for m in block_re.finditer(full_text):
        spn_id = int(m.group(1))
        name = _clean_text(m.group(2))
        desc = _clean_text(m.group(3))
        data_len_line = m.group(4).strip()
        resolution_line = m.group(5).strip()
        range_line = m.group(6).strip()
        type_line = m.group(7).strip()
        pgn_line = m.group(9).strip()

        # Data Length -> bits
        bits_len: int | None = None
        mlen = re.search(r"([0-9.,]+)\s*(bytes?|bits?)", data_len_line, re.I)
        if mlen:
            n = _num(mlen.group(1)) or 0
            unit = (mlen.group(2) or "").lower()
            bits_len = int(round(n * 8)) if "byte" in unit else int(round(n))

        # Resolution -> escala, unidades, offset
        scale: float | None = None
        units: str | None = None
        offset: float | None = None
        mres = re.search(r"([\-0-9.,]+)\s*([^\s,]+)?\s*/\s*bit.*?([\-0-9.,]+)\s*offset", resolution_line, re.I)
        if mres:
            scale = _num(mres.group(1))
            units = (mres.group(2) or "").strip() or None
            offset = _num(mres.group(3))

        # Data Range -> min, max, unidad (opcional)
        rmin: float | None = None
        rmax: float | None = None
        units_range: str | None = None
        mrange = re.search(r"([\-0-9.,]+)\s*to\s*([\-0-9.,]+)\s*([^\s%°A-Za-z]*)?\s*([%°A-Za-z]+)?", range_line, re.I)
        if mrange:
            rmin = _num(mrange.group(1))
            rmax = _num(mrange.group(2))
            units_range = (mrange.group(4) or mrange.group(3) or "").strip() or None
        if not units and units_range:
            units = units_range

        # Tipo
        if re.search(r"measured", type_line, re.I):
            spn_type = "Medido"
        elif re.search(r"status|state", type_line, re.I):
            spn_type = "Estado"
        else:
            spn_type = _clean_text(type_line)

        # PGNs
        pgns = [int(x) for x in re.findall(r"\[\s*([0-9]{5})\s*\]", pgn_line)]

        items.append({
            "spn": spn_id,
            "name": name,
            "description": desc,
            "units": units,
            "data_length_bits": bits_len,
            "resolution": scale,
            "offset": offset,
            "range": {"min": rmin, "max": rmax} if (rmin is not None or rmax is not None) else None,
            "type": spn_type,
            "pgns": pgns,
            "states": None,
            "notes": None,
        })

    return items

def iter_pages_text(pdf_path: Path, engine: str = "fitz"):
    """Genera el texto por página usando PyMuPDF (fitz) por defecto (más rápido).
    Si no está disponible o falla, cae a pdfplumber.
    """
    if engine == "fitz":
        try:
            ensure_package("pymupdf")
            import fitz  # type: ignore
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    yield page.get_text("text") or ""
            return
        except Exception:
            print("Aviso: PyMuPDF falló; usando pdfplumber…")
    # Fallback pdfplumber
    try:
        import pdfplumber  # type: ignore
    except Exception:
        ensure_package("pdfplumber")
        import pdfplumber  # type: ignore # noqa: F401
    with pdfplumber.open(pdf_path) as pdf:  # type: ignore
        for p in pdf.pages:
            yield p.extract_text() or ""

def parse_spn_blocks_stream(
    pdf_path: Path,
    engine: str = "fitz",
    max_pages: int | None = None,
    chunk_pages: int = 10,
    verbose: bool = True,
):
    """Parseo por streaming: concatena el texto de N páginas por chunk y aplica el regex.
    Conserva un tail para capturar bloques que cruzan páginas.
    """
    pattern = re.compile(
        r"(?is)\bspn\s*([0-9]{3,6})\s*-\s*(.+?)\s*-\s*(.+?)\s*"
        r"Data\s+Length:\s*([^\n]+)\n"
        r"Resolution:\s*([^\n]+)\n"
        r"Data\s+Range:\s*([^\n]+)\n"
        r"Type:\s*([^\n]+)\n"
        r"Suspect\s+Parameter\s+Number:\s*([0-9]{3,6})\n"
        r"Parameter\s+Group\s+Number:\s*([^\n]+?)\s*(?=\n\s*spn\s*[0-9]{3,6}\s*-|\Z)"
    )
    items: list[dict] = []
    tail = ""
    buf = []
    count_pages = 0
    for txt in iter_pages_text(pdf_path, engine=engine):
        count_pages += 1
        buf.append(txt or "")
        if max_pages and count_pages >= max_pages:
            if verbose:
                print(f"Límite de páginas alcanzado: {max_pages}")
            break
        if len(buf) >= chunk_pages:
            chunk = tail + "\n\n".join(buf)
            # Guardamos tail de seguridad (2k chars) por si hay corte de bloque
            tail = chunk[-2000:]
            for m in pattern.finditer(chunk):
                spn_id = int(m.group(1))
                name = _clean_text(m.group(2))
                desc = _clean_text(m.group(3))
                data_len_line = m.group(4).strip()
                resolution_line = m.group(5).strip()
                range_line = m.group(6).strip()
                type_line = m.group(7).strip()
                pgn_line = m.group(9).strip()

                bits_len = None
                mlen = re.search(r"([0-9.,]+)\s*(bytes?|bits?)", data_len_line, re.I)
                if mlen:
                    n = _num(mlen.group(1)) or 0
                    unit = (mlen.group(2) or "").lower()
                    bits_len = int(round(n * 8)) if "byte" in unit else int(round(n))

                scale = None
                units = None
                offset = None
                mres = re.search(r"([\-0-9.,]+)\s*([^\s,]+)?\s*/\s*bit.*?([\-0-9.,]+)\s*offset", resolution_line, re.I)
                if mres:
                    scale = _num(mres.group(1))
                    units = (mres.group(2) or "").strip() or None
                    offset = _num(mres.group(3))

                rmin = None
                rmax = None
                units_range = None
                mrange = re.search(r"([\-0-9.,]+)\s*to\s*([\-0-9.,]+)\s*([^\s%°A-Za-z]*)?\s*([%°A-Za-z]+)?", range_line, re.I)
                if mrange:
                    rmin = _num(mrange.group(1))
                    rmax = _num(mrange.group(2))
                    units_range = (mrange.group(4) or mrange.group(3) or "").strip() or None
                if not units and units_range:
                    units = units_range

                if re.search(r"measured", type_line, re.I):
                    spn_type = "Medido"
                elif re.search(r"status|state", type_line, re.I):
                    spn_type = "Estado"
                else:
                    spn_type = _clean_text(type_line)

                pgns = [int(x) for x in re.findall(r"\[\s*([0-9]{5})\s*\]", pgn_line)]

                items.append({
                    "spn": spn_id,
                    "name": name,
                    "description": desc,
                    "units": units,
                    "data_length_bits": bits_len,
                    "resolution": scale,
                    "offset": offset,
                    "range": {"min": rmin, "max": rmax} if (rmin is not None or rmax is not None) else None,
                    "type": spn_type,
                    "pgns": pgns,
                    "states": None,
                    "notes": None,
                })
            if verbose:
                print(f"Procesadas {count_pages} páginas; SPNs hasta ahora: {len(items)}")
            buf = []
    # Procesar resto
    if buf:
        chunk = tail + "\n\n".join(buf)
        for m in pattern.finditer(chunk):
            spn_id = int(m.group(1))
            name = _clean_text(m.group(2))
            desc = _clean_text(m.group(3))
            data_len_line = m.group(4).strip()
            resolution_line = m.group(5).strip()
            range_line = m.group(6).strip()
            type_line = m.group(7).strip()
            pgn_line = m.group(9).strip()

            bits_len = None
            mlen = re.search(r"([0-9.,]+)\s*(bytes?|bits?)", data_len_line, re.I)
            if mlen:
                n = _num(mlen.group(1)) or 0
                unit = (mlen.group(2) or "").lower()
                bits_len = int(round(n * 8)) if "byte" in unit else int(round(n))

            scale = None
            units = None
            offset = None
            mres = re.search(r"([\-0-9.,]+)\s*([^\s,]+)?\s*/\s*bit.*?([\-0-9.,]+)\s*offset", resolution_line, re.I)
            if mres:
                scale = _num(mres.group(1))
                units = (mres.group(2) or "").strip() or None
                offset = _num(mres.group(3))

            rmin = None
            rmax = None
            units_range = None
            mrange = re.search(r"([\-0-9.,]+)\s*to\s*([\-0-9.,]+)\s*([^\s%°A-Za-z]*)?\s*([%°A-Za-z]+)?", range_line, re.I)
            if mrange:
                rmin = _num(mrange.group(1))
                rmax = _num(mrange.group(2))
                units_range = (mrange.group(4) or mrange.group(3) or "").strip() or None
            if not units and units_range:
                units = units_range

            if re.search(r"measured", type_line, re.I):
                spn_type = "Medido"
            elif re.search(r"status|state", type_line, re.I):
                spn_type = "Estado"
            else:
                spn_type = _clean_text(type_line)

            pgns = [int(x) for x in re.findall(r"\[\s*([0-9]{5})\s*\]", pgn_line)]

            items.append({
                "spn": spn_id,
                "name": name,
                "description": desc,
                "units": units,
                "data_length_bits": bits_len,
                "resolution": scale,
                "offset": offset,
                "range": {"min": rmin, "max": rmax} if (rmin is not None or rmax is not None) else None,
                "type": spn_type,
                "pgns": pgns,
                "states": None,
                "notes": None,
            })
        if verbose:
            print(f"Procesamiento finalizado; páginas: {count_pages}; SPNs extraídos: {len(items)}")
    return items

def build_json_from_spns(now_iso: str, spn_items: list[dict]) -> dict:
    # Mapear PGN -> señales (SPNs)
    pgn_map: dict[int, dict] = {}
    for spn in spn_items:
        for pgn in spn.get("pgns", []) or []:
            if pgn not in pgn_map:
                pgn_map[pgn] = {
                    "pgn": pgn,
                    "name": None,
                    "data_length_bytes": None,
                    "data_page": None,
                    "pdu_format": None,
                    "pdu_specific": None,
                    "default_priority": None,
                    "transmission_rate": None,
                    "signals": [],
                    "notes": "Estructura mínima inferida desde definiciones SPN; completar con DBC.",
                }
            pgn_map[pgn]["signals"].append({
                "spn": spn.get("spn"),
                "name": spn.get("name"),
                "start_bit": None,
                "length": spn.get("data_length_bits"),
                "endianness": "Intel",
                "units": spn.get("units"),
                "scale": spn.get("resolution"),
                "offset": spn.get("offset"),
                "min": (spn.get("range") or {}).get("min"),
                "max": (spn.get("range") or {}).get("max"),
                "dbc_link": {"message": None, "signal": None},
            })

    pgn_list = list(pgn_map.values())

    return {
        "metadata": {
            "standard": "SAE J1939-71",
            "description": "Capa de Aplicación J1939: directrices, definiciones de SPN/PGN y campos para enlazar con DBC. Archivo de referencia para modelos RAG.",
            "source_document": "Entrega4_Precision_Semantica_y_Contextualizacion_Eventos_Vehiculares/J1939-71.pdf",
            "created_at": now_iso,
            "language": "es",
            "schema_version": "1.0.0",
        },
        "guidelines": {
            "signal_characterization": {
                "latency_recommendations": "Minimizar la latencia entre adquisición y transmisión. Documentar latencia y jitter esperados por parámetro.",
                "time_base": "Algunos PGN dependen del ángulo del cigüeñal/velocidad de motor (sincronizados a fase).",
            },
            "message_format": {
                "pgn": "El Número de Grupo de Parámetros (PGN) identifica el mensaje y su contenido lógico.",
                "data_types": [
                    "ASCII (ISO/IEC 8859-1 / Latin-1)",
                    "Datos escalados (factor + offset)",
                    "Estados de función (bitfields/enumeraciones)",
                ],
                "byte_order": "Little-endian (LSB primero) salvo indicación contraria en el SPN/PGN.",
                "measured_vs_state": "Cada SPN se clasifica como 'Medido' o 'Estado'.",
            },
            "charset": {
                "name": "ISO/IEC 8859-1 (Latin-1)",
                "notes": "Para campos de texto/ASCII se recomienda Latin-1. Limitar a ASCII imprimible cuando aplique.",
            },
            "parameter_ranges": {
                "general": "Definir rango válido, valores para 'no disponible' y 'error/indeterminado' según el tipo de dato.",
                "common_conventions": [
                    "Para 1 byte: 0..254 suelen mapear a valores/estados válidos, y 255 (0xFF) suele indicar 'no disponible'.",
                    "Para múltiples bytes escalados: usar todo el rango útil, reservando el máximo para 'no disponible' cuando aplique.",
                    "Los valores exactos de 'error'/'no disponible' pueden ser específicos del SPN; ver la definición del SPN.",
                ],
            },
            "slot_allocation": {
                "scaling": "Definir resolución (factor), offset y límites. Preferir escalas que maximicen el uso del rango sin saturación.",
                "limits_and_offsets": "Explicitar min/max físicos y el offset aplicado.",
            },
            "adding_parameters_to_groups": {
                "grouping": "Agregar nuevos parámetros a PGNs existentes cuando sea lógico; mantener posiciones y alineación de bytes/bits estables.",
                "compatibility": "Evitar romper compatibilidad hacia atrás; documentar cambios en posiciones/tamaños.",
            },
            "transmission_rates": {
                "nominal_rates": ["10 ms", "20 ms", "100 ms", "1 s", "a demanda"],
                "notes": [
                    "Elegir tasas periódicas vs. por evento según la dinámica del parámetro.",
                    "Mensajes dependientes del cigüeñal se envían conforme a la velocidad del motor.",
                ],
            },
            "naming_conventions": {
                "multi_component": "Para parámetros con múltiples instancias, añadir índice/ubicación (ej.: 'temperatura_escape_1', 'temperatura_escape_2').",
                "clarity": "Mantener nombres consistentes con J1939 para facilitar el cruce con DBC/SPN.",
            },
            "multi_source_notes": {
                "source_priority": "Si un parámetro tiene múltiples fuentes (ECU diferentes), definir reglas de prioridad y reconciliación.",
                "provenance": "Registrar la ECU origen (Source Address) y la estrategia de selección.",
            },
        },
        "dbc_linkage": {
            "can_id_composition": "ID 29 bits = Prioridad(3) | Reservado(1) | Data Page(1) | PDU Format(8) | PDU Specific(8) | Source Address(8)",
            "fields_mapping": {
                "dbc_message": {
                    "name": "Nombre del mensaje en DBC (habitualmente el nombre del PGN)",
                    "can_id": "Identificador CAN extendido de 29 bits",
                    "pgn": "Número PGN",
                    "source_address": "0-255",
                    "pdu_format": "0-255",
                    "pdu_specific": "0-255",
                    "priority": "0-7",
                },
                "dbc_signal": {
                    "name": "Nombre de la señal en DBC (alineado con nombre SPN)",
                    "spn": "Número SPN",
                    "start_bit": "Bit de inicio (convención Intel/little-endian)",
                    "length": "Longitud en bits",
                    "endianness": "Intel (little-endian) salvo indicación contraria",
                    "scale": "Factor (resolución)",
                    "offset": "Offset",
                    "min": "Mínimo físico",
                    "max": "Máximo físico",
                    "units": "Unidades",
                },
            },
            "matching_strategy": [
                "Cruzar por SPN (clave primaria semántica).",
                "Verificar unidades, resolución y offset.",
                "Usar nombre del PGN y señal como respaldo, cuidando sinónimos.",
                "Confirmar posiciones (start_bit/length) desde el DBC, no desde este archivo.",
            ],
        },
        "spns": spn_items,
        "pgns": pgn_list,
        "traceability": {
            "sections": {
                "5.1": "Directrices generales (latencia, formato, charset, rangos, slots, agrupación, tasas, nomenclatura, multi-fuente).",
                "5.2": "Definiciones de parámetros (SPN): nombre, descripción, longitud, escala, rango, tipo, SPN, PGN.",
                "5.3": "Definiciones de grupos (PGN): nombre, tasa, longitud, DP/PDU, prioridad, lista de SPNs con posiciones.",
            }
        },
    }


def build_json(now_iso: str) -> dict:
    return {
        "metadata": {
            "standard": "SAE J1939-71",
            "description": "Capa de Aplicación J1939: directrices, definiciones de SPN/PGN y campos para enlazar con DBC. Archivo de referencia para modelos RAG.",
            "source_document": "Entrega4_Precision_Semantica_y_Contextualizacion_Eventos_Vehiculares/J1939-71.pdf",
            "created_at": now_iso,
            "language": "es",
            "schema_version": "1.0.0",
        },
        "guidelines": {
            "signal_characterization": {
                "latency_recommendations": "Minimizar la latencia entre adquisición y transmisión. Documentar latencia y jitter esperados por parámetro.",
                "time_base": "Algunos PGN dependen del ángulo del cigüeñal/velocidad de motor (sincronizados a fase).",
            },
            "message_format": {
                "pgn": "El Número de Grupo de Parámetros (PGN) identifica el mensaje y su contenido lógico.",
                "data_types": [
                    "ASCII (ISO/IEC 8859-1 / Latin-1)",
                    "Datos escalados (factor + offset)",
                    "Estados de función (bitfields/enumeraciones)",
                ],
                "byte_order": "Little-endian (LSB primero) salvo indicación contraria en el SPN/PGN.",
                "measured_vs_state": "Cada SPN se clasifica como 'Medido' o 'Estado'.",
            },
            "charset": {
                "name": "ISO/IEC 8859-1 (Latin-1)",
                "notes": "Para campos de texto/ASCII se recomienda Latin-1. Limitar a ASCII imprimible cuando aplique.",
            },
            "parameter_ranges": {
                "general": "Definir rango válido, valores para 'no disponible' y 'error/indeterminado' según el tipo de dato.",
                "common_conventions": [
                    "Para 1 byte: 0..254 suelen mapear a valores/estados válidos, y 255 (0xFF) suele indicar 'no disponible'.",
                    "Para múltiples bytes escalados: usar todo el rango útil, reservando el máximo para 'no disponible' cuando aplique.",
                    "Los valores exactos de 'error'/'no disponible' pueden ser específicos del SPN; ver la definición del SPN.",
                ],
            },
            "slot_allocation": {
                "scaling": "Definir resolución (factor), offset y límites. Preferir escalas que maximicen el uso del rango sin saturación.",
                "limits_and_offsets": "Explicitar min/max físicos y el offset aplicado.",
            },
            "adding_parameters_to_groups": {
                "grouping": "Agregar nuevos parámetros a PGNs existentes cuando sea lógico; mantener posiciones y alineación de bytes/bits estables.",
                "compatibility": "Evitar romper compatibilidad hacia atrás; documentar cambios en posiciones/tamaños.",
            },
            "transmission_rates": {
                "nominal_rates": ["10 ms", "20 ms", "100 ms", "1 s", "a demanda"],
                "notes": [
                    "Elegir tasas periódicas vs. por evento según la dinámica del parámetro.",
                    "Mensajes dependientes del cigüeñal se envían conforme a la velocidad del motor.",
                ],
            },
            "naming_conventions": {
                "multi_component": "Para parámetros con múltiples instancias, añadir índice/ubicación (ej.: 'temperatura_escape_1', 'temperatura_escape_2').",
                "clarity": "Mantener nombres consistentes con J1939 para facilitar el cruce con DBC/SPN.",
            },
            "multi_source_notes": {
                "source_priority": "Si un parámetro tiene múltiples fuentes (ECU diferentes), definir reglas de prioridad y reconciliación.",
                "provenance": "Registrar la ECU origen (Source Address) y la estrategia de selección.",
            },
        },
        "dbc_linkage": {
            "can_id_composition": "ID 29 bits = Prioridad(3) | Reservado(1) | Data Page(1) | PDU Format(8) | PDU Specific(8) | Source Address(8)",
            "fields_mapping": {
                "dbc_message": {
                    "name": "Nombre del mensaje en DBC (habitualmente el nombre del PGN)",
                    "can_id": "Identificador CAN extendido de 29 bits",
                    "pgn": "Número PGN",
                    "source_address": "0-255",
                    "pdu_format": "0-255",
                    "pdu_specific": "0-255",
                    "priority": "0-7",
                },
                "dbc_signal": {
                    "name": "Nombre de la señal en DBC (alineado con nombre SPN)",
                    "spn": "Número SPN",
                    "start_bit": "Bit de inicio (convención Intel/little-endian)",
                    "length": "Longitud en bits",
                    "endianness": "Intel (little-endian) salvo indicación contraria",
                    "scale": "Factor (resolución)",
                    "offset": "Offset",
                    "min": "Mínimo físico",
                    "max": "Máximo físico",
                    "units": "Unidades",
                },
            },
            "matching_strategy": [
                "Cruzar por SPN (clave primaria semántica).",
                "Verificar unidades, resolución y offset.",
                "Usar nombre del PGN y señal como respaldo, cuidando sinónimos.",
                "Confirmar posiciones (start_bit/length) desde el DBC, no desde este archivo.",
            ],
        },
        "spns": [
            {
                "spn": 190,
                "name": "Velocidad del motor",
                "description": "Velocidad del cigüeñal del motor.",
                "units": "rpm",
                "data_length_bits": 16,
                "resolution": 0.125,
                "offset": 0,
                "range": {"min": 0, "max": 8000},
                "type": "Medido",
                "pgns": [61444],
                "states": None,
                "notes": "Valores exactos de rango/NA pueden variar por versión; confirmar con DBC/ECU.",
                "example_only": True,
            },
            {
                "spn": 110,
                "name": "Temperatura del refrigerante del motor",
                "description": "Temperatura del refrigerante en el motor.",
                "units": "°C",
                "data_length_bits": 8,
                "resolution": 1,
                "offset": -40,
                "range": {"min": -40, "max": 210},
                "type": "Medido",
                "pgns": [65262],
                "states": None,
                "notes": "Suele mapear 0..250 -> -40..210 °C; valores tope reservados para NA/error según SPN.",
                "example_only": True,
            },
        ],
        "pgns": [
            {
                "pgn": 61444,
                "name": "Control/Estado motor 1 (EEC1)",
                "data_length_bytes": 8,
                "data_page": 0,
                "pdu_format": None,
                "pdu_specific": None,
                "default_priority": 3,
                "transmission_rate": "rápida (sincronizada a motor cuando aplique)",
                "signals": [
                    {
                        "spn": 190,
                        "name": "Velocidad del motor",
                        "start_bit": None,
                        "length": 16,
                        "endianness": "Intel",
                        "units": "rpm",
                        "scale": 0.125,
                        "offset": 0,
                        "min": 0,
                        "max": 8000,
                        "dbc_link": {"message": None, "signal": None},
                    }
                ],
                "notes": "Posiciones exactas (start_bit/byte) deben confirmarse en el DBC objetivo.",
                "example_only": True,
            },
            {
                "pgn": 65262,
                "name": "Temperatura del motor 1 (ET1)",
                "data_length_bytes": 8,
                "data_page": 0,
                "pdu_format": None,
                "pdu_specific": None,
                "default_priority": 6,
                "transmission_rate": "periódica (típicamente ms a s, según ECU)",
                "signals": [
                    {
                        "spn": 110,
                        "name": "Temperatura del refrigerante del motor",
                        "start_bit": None,
                        "length": 8,
                        "endianness": "Intel",
                        "units": "°C",
                        "scale": 1,
                        "offset": -40,
                        "min": -40,
                        "max": 210,
                        "dbc_link": {"message": None, "signal": None},
                    }
                ],
                "notes": "Completar con otras temperaturas (aceite, combustible) según versión del estándar/ECU.",
                "example_only": True,
            },
        ],
        "traceability": {
            "sections": {
                "5.1": "Directrices generales (latencia, formato, charset, rangos, slots, agrupación, tasas, nomenclatura, multi-fuente).",
                "5.2": "Definiciones de parámetros (SPN): nombre, descripción, longitud, escala, rango, tipo, SPN, PGN.",
                "5.3": "Definiciones de grupos (PGN): nombre, tasa, longitud, DP/PDU, prioridad, lista de SPNs con posiciones.",
            }
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera JSON de referencia J1939-71 para RAG")
    default_pdf = Path(r"c:\\Users\\henry\\Documents\\GitHub\\Proyecto_Integrador_Grupo7_IBM\\Entrega4_Precision_Semantica_y_Contextualizacion_Eventos_Vehiculares\\J1939-71.pdf")
    default_out = Path(r"c:\\Users\\henry\\Documents\\GitHub\\Proyecto_Integrador_Grupo7_IBM\\Entrega4_Precision_Semantica_y_Contextualizacion_Eventos_Vehiculares\\j1939_71_reference.json")
    parser.add_argument("--pdf", type=Path, default=default_pdf, help="Ruta al PDF J1939-71")
    parser.add_argument("--out", type=Path, default=default_out, help="Ruta de salida JSON")
    parser.add_argument("--engine", choices=["fitz", "pdfplumber"], default="fitz", help="Motor de extracción de texto (fitz=rápido)")
    parser.add_argument("--max-pages", type=int, default=None, help="Máximo de páginas a procesar (para pruebas)")
    parser.add_argument("--chunk-pages", type=int, default=10, help="Tamaño de chunk de páginas para el parser streaming")
    parser.add_argument("--quiet", action="store_true", help="Menos salida en consola")
    args = parser.parse_args()

    # Asegura que pdfplumber esté disponible para leer el PDF
    ensure_package("pdfplumber")

    preview = try_read_pdf_preview(args.pdf)
    if preview:
        print("PDF leído correctamente (previsualización 300 chars):\n", preview[:300])
    else:
        print("Aviso: no se extrajo texto del PDF (o falta pdfplumber). Intentando lectura completa…")

    verbose = not args.quiet
    spn_items = parse_spn_blocks_stream(
        args.pdf,
        engine=args.engine,
        max_pages=args.max_pages,
        chunk_pages=args.chunk_pages,
        verbose=verbose,
    )
    if verbose:
        print(f"SPNs extraídos: {len(spn_items)}")

    now_iso = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    payload = build_json_from_spns(now_iso, spn_items)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("JSON escrito en:", args.out)


if __name__ == "__main__":
    main()
