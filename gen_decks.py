#!/usr/bin/env python3
"""Gera seed-decks.js a partir dos materiais HTML do repositório.

Reconhece dois formatos de DATA embutido nos HTMLs:
- súmulas: {"sections":[{"num","theme"/"tema","enunciado","resumo"/"simples",...}]}
- lei anotada: {"titulos":[...], "u":{"art-1":{"rotulo","tema","chamada","texto":[...]}}}
"""
import json, glob, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))

# deck (nome amigável) por arquivo de lei anotada
LEI_DECKS = {
    "CF88-arts-1-a-19-apostila.html": "CF/88 · Arts. 1º a 19",
    "CodigoCivil-arts-1-a-120-apostila.html": "Código Civil · Parte Geral",
    "CPC-2015-arts-1-a-63-apostila.html": "CPC/2015 · Arts. 1º a 63",
    "Lei-8245-1991-Locacoes-apostila.html": "Lei de Locações",
    "Lei-9514-1997-SFI-alienacao-fiduciaria-imovel-apostila.html": "Lei 9.514/97 · SFI",
    "DL-911-1969-alienacao-fiduciaria-apostila.html": "DL 911/69",
    "Lei-9985-2000-SNUC-apostila.html": "SNUC",
    "Lei-6938-1981-PNMA-apostila.html": "PNMA",
}

def extract_data(path):
    txt = open(path, encoding="utf-8").read()
    i = txt.find("DATA=")
    if i < 0:
        return None
    s = txt[i + 5:]
    depth = 0
    for j, ch in enumerate(s):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
    try:
        return json.loads(s[: j + 1])
    except Exception:
        return None

def txt_of(item):
    rot = (item.get("rot") or "").strip()
    t = (item.get("txt") or "").strip()
    return (rot + " " + t).strip() if rot else t

decks = {}

# ── súmulas vinculantes ──
for f in sorted(glob.glob(os.path.join(ROOT, "Sumulas-Vinculantes-*.html"))):
    d = extract_data(f)
    if not d:
        continue
    for sec in d.get("sections", []):
        res = (sec.get("resumo") or "").strip()
        enun = (sec.get("enunciado") or "").strip()
        a = res or enun
        if res and enun and res != enun:
            a = res + "\n\n📜 Enunciado: " + enun
        decks.setdefault("Súmulas Vinculantes", []).append(
            {"q": f"SV {sec['num']} — {sec.get('theme','')}: o que estabelece?", "a": a})

# ── súmulas TSE (só vigentes) ──
tse = os.path.join(ROOT, "Sumulas-TSE-estudo-por-questoes.html")
d = extract_data(tse)
if d:
    for sec in d.get("sections", []):
        if (sec.get("status") or "").lower().startswith("cancel"):
            continue
        enun = (sec.get("enunciado") or "").strip()
        simp = (sec.get("simples") or "").strip()
        a = simp + "\n\n📜 Enunciado: " + enun if simp and simp != enun else enun
        decks.setdefault("Súmulas TSE", []).append(
            {"q": f"Súmula TSE {sec['num']} — {sec.get('tema','')} ({sec.get('grupo','')}): o que diz?", "a": a})

# ── leis anotadas (artigos) ──
for fname, deck in LEI_DECKS.items():
    path = os.path.join(ROOT, fname)
    if not os.path.exists(path):
        continue
    d = extract_data(path)
    if not d or "u" not in d:
        continue
    arts = d["u"]
    # preserva a ordem dos títulos/capítulos quando disponível
    ordem = []
    for t in d.get("titulos", []):
        for cap in t.get("capitulos", []):
            ordem += cap.get("ids", [])
    if not ordem:
        ordem = list(arts.keys())
    for aid in ordem:
        art = arts.get(aid)
        if not art:
            continue
        rot = art.get("rotulo") or aid
        tema = art.get("tema") or art.get("titulo") or ""
        chamada = (art.get("chamada") or "").strip()
        corpo = "\n".join(txt_of(i) for i in art.get("texto", []) if txt_of(i))
        a = (chamada + "\n\n📜 " + corpo).strip() if chamada else corpo
        if not a:
            continue
        decks.setdefault(deck, []).append(
            {"q": f"{deck} · {rot} — {tema}: o que dispõe?", "a": a})

out = ("/* Decks gerados automaticamente por gen_decks.py — não editar à mão */\n"
       "const SEED_DECKS=" + json.dumps(decks, ensure_ascii=False) + ";\n")
open(os.path.join(ROOT, "seed-decks.js"), "w", encoding="utf-8").write(out)
print({k: len(v) for k, v in decks.items()})
print("total:", sum(len(v) for v in decks.values()), "cards")
