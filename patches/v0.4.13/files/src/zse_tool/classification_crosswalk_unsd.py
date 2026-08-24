from __future__ import annotations

import io, re
from typing import Any
from openpyxl import load_workbook

class AdapterError(RuntimeError): pass

def _h(v: Any) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(v or "").casefold()).split())


def _code(v: Any) -> str | None:
    if v is None: return None
    if isinstance(v, float) and v.is_integer(): v = int(v)
    m = re.fullmatch(r"[A-Za-z]?([0-9]{1,4})", str(v).strip().replace(" ", "").replace("'", ""))
    return m.group(1).zfill(4) if m else None


def _headers(ws: Any) -> tuple[int,int,int,int|None,int|None] | None:
    best = None
    for row in range(1, min(ws.max_row, 30) + 1):
        vals = {c:_h(ws.cell(row,c).value) for c in range(1, min(ws.max_column,40)+1)}
        a=[c for c,t in vals.items() if "isic" in t and ("rev 4" in t or "rev4" in t) and "code" in t and "title" not in t]
        b=[c for c,t in vals.items() if "isic" in t and ("rev 5" in t or "rev5" in t) and "code" in t and "title" not in t]
        if a and b:
            change=next((c for c,t in vals.items() if ("change" in t or "gsim" in t) and ("type" in t or "category" in t)),None)
            note=next((c for c,t in vals.items() if ("description" in t or "note" in t) and ("change" in t or "content" in t)),None)
            best=(row+1,a[0],b[0],change,note); break
    return best


def parse_unsd_isic_rev4_rev5_xlsx(data: bytes) -> list[dict[str,Any]]:
    try: wb=load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception as exc: raise AdapterError(f"invalid UNSD workbook: {exc}") from exc
    candidates=[]
    for ws in wb.worksheets:
        hdr=_headers(ws)
        if not hdr: continue
        start,a,b,ch,no=hdr; rows=[]; seen=set(); blanks=0
        for r in range(start,ws.max_row+1):
            x,y=_code(ws.cell(r,a).value),_code(ws.cell(r,b).value)
            if not x and not y:
                blanks+=1
                if blanks>=25 and rows: break
                continue
            blanks=0
            if not x or not y: continue
            change=" ".join(str(ws.cell(r,ch).value).split()) if ch and ws.cell(r,ch).value is not None else None
            note=" ".join(str(ws.cell(r,no).value).split()) if no and ws.cell(r,no).value is not None else None
            key=(x,y,change,note)
            if key in seen: continue
            seen.add(key); rows.append({"from_code":x,"to_code":y,"official_change_type":change,"official_note":note})
        if rows: candidates.append(rows)
    if not candidates: raise AdapterError("ISIC Rev.4/Rev.5 table not found in workbook")
    return max(candidates,key=lambda rows:(len({x['from_code'] for x in rows}),len({x['to_code'] for x in rows}),len(rows)))

