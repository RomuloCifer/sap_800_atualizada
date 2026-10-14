"""
Leitura de XML de NF-e (nfeProc) para campos usados na automação.

Issuer SAP (ex.: 513088) NÃO vem neste XML — fica para Excel/mapeamento depois.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


class XmlClipboardFalhou(Exception):
    """
    Ctrl+C do XML não trouxe conteúdo válido.
    A automação deve parar SEM gravar Status no Excel (deixa Pendente).
    """

    pass


@dataclass
class ItemNFe:
    n_item: int
    codigo: str
    descricao: str
    cfop: str
    quantidade: float
    preco_unitario: float
    valor_produto: float


@dataclass
class DadosNFe:
    invoice: str
    serie: str
    recipient_cnpj: str
    recipient_cnpj_fmt: str
    recipient_sufixo: str  # ex.: 0015-60 (filial + DV)
    recipient_filial: str  # ex.: 0015 — só os 4 dígitos da filial (Business Place)
    recipient_nome: str
    issue_date: str  # DD.MM.YYYY
    protocol_number: str
    protocol_date: str  # DD.MM.YYYY
    protocol_time: str  # HH:MM:SS
    protocol_line: str  # "nProt DD.MM.YYYY HH:MM:SS"
    cfop: str  # do 1º item (ou único CFOP se todos iguais)
    cfops: List[str]
    valor: float
    valor_fmt: str  # 1,730.36
    chave_acesso: str
    emit_cnpj: str
    emit_nome: str
    issuer_sap: Optional[str] = None  # não vem do XML
    itens: List[ItemNFe] = field(default_factory=list)

    def to_dict(self):
        # type: () -> Dict[str, Any]
        d = asdict(self)
        return d


def _local(tag):
    # type: (str) -> str
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _text(el):
    # type: (Optional[ET.Element]) -> str
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def _find_text(root, path):
    # type: (ET.Element, str) -> str
    """path com tags locais separadas por /, ignora namespace."""
    cur = root  # type: Optional[ET.Element]
    for part in path.split("/"):
        if cur is None:
            return ""
        nxt = None
        for child in list(cur):
            if _local(child.tag) == part:
                nxt = child
                break
        cur = nxt
    return _text(cur)


def _find_all(root, local_name):
    # type: (ET.Element, str) -> List[ET.Element]
    return [el for el in root.iter() if _local(el.tag) == local_name]


def formatar_cnpj(digitos):
    # type: (str) -> str
    d = re.sub(r"\D", "", digitos or "")
    if len(d) != 14:
        return digitos or ""
    return "{}.{}.{}/{}-{}".format(d[0:2], d[2:5], d[5:8], d[8:12], d[12:14])


def sufixo_cnpj(digitos):
    # type: (str) -> str
    """Últimos 6 dígitos no formato NNNN-NN (ex.: 0015-60)."""
    d = re.sub(r"\D", "", digitos or "")
    if len(d) < 6:
        return d
    return "{}-{}".format(d[-6:-2], d[-2:])


def filial_cnpj(digitos):
    # type: (str) -> str
    """
    Filial do CNPJ: 4 dígitos após a barra (BBBB em AA.AAA.AAA/BBBB-CC).
    Ex.: 00.907.845/0015-60 → 0015 (pode ser 0001, 0016, etc.).
    """
    d = re.sub(r"\D", "", digitos or "")
    if len(d) != 14:
        # fallback: tenta pegar 4 dígitos antes dos 2 finais
        if len(d) >= 6:
            return d[-6:-2]
        return d
    return d[8:12]


def formatar_data_br(iso_dt):
    # type: (str) -> str
    """2025-11-13T14:09:00-03:00 -> 13.11.2025"""
    if not iso_dt:
        return ""
    raw = iso_dt.strip()
    try:
        # Aceita com ou sem timezone
        if "T" in raw:
            base = raw.split("T", 1)[0]
        else:
            base = raw[:10]
        dt = datetime.strptime(base, "%Y-%m-%d")
        return dt.strftime("%d.%m.%Y")
    except ValueError:
        return raw


def formatar_hora(iso_dt):
    # type: (str) -> str
    """2025-11-13T14:09:16-03:00 -> 14:09:16"""
    if not iso_dt or "T" not in iso_dt:
        return ""
    hora = iso_dt.split("T", 1)[1]
    hora = re.split(r"[Zz+-]", hora)[0]
    partes = hora.split(":")
    if len(partes) >= 3:
        return "{}:{}:{}".format(partes[0], partes[1], partes[2][:2])
    return hora


def formatar_valor_us(valor):
    # type: (float) -> str
    """1730.36 -> 1,730.36"""
    return "{:,.2f}".format(float(valor))


def parse_valor(texto):
    # type: (str) -> float
    t = (texto or "").strip().replace(",", "")
    if not t:
        return 0.0
    return float(t)


def _limpar_texto_xml(xml_texto):
    # type: (str) -> str
    texto = (xml_texto or "").replace("\x00", "").strip()
    if texto.startswith("\ufeff"):
        texto = texto.lstrip("\ufeff")
    if not texto.lstrip().startswith("<"):
        idx = texto.find("<")
        if idx >= 0:
            texto = texto[idx:]
    return texto


def _re_tag(texto, nome):
    # type: (str, str) -> str
    """Primeira ocorrência de <nome>valor</nome> (com ou sem namespace)."""
    pat = r"<(?:\w+:)?{0}(?:\s[^>]*)?>([^<]*)</(?:\w+:)?{0}>".format(re.escape(nome))
    m = re.search(pat, texto, flags=re.IGNORECASE)
    return (m.group(1).strip() if m else "")


def _juntar_descricao_item(x_prod, inf_ad_prod):
    # type: (str, str) -> str
    """
    Descrição como na DANFE: xProd + " / " + infAdProd (quando existir).
    Ex.: "MOLDE DE INJECAO PLASTICA TE / 29-0337353-00000"
    """
    base = (x_prod or "").strip()
    extra = (inf_ad_prod or "").strip()
    if not extra:
        return base
    if not base:
        return extra
    return "{} / {}".format(base, extra)


def _re_tag_dentro(texto, bloco, nome):
    # type: (str, str, str) -> str
    """Tag dentro do primeiro bloco <bloco>... (funciona mesmo com XML truncado)."""
    m = re.search(
        r"<(?:\w+:)?{}\b[^>]*>([\s\S]{{0,12000}})".format(re.escape(bloco)),
        texto,
        flags=re.IGNORECASE,
    )
    if not m:
        return ""
    trecho = m.group(1)
    fecha = re.search(
        r"</(?:\w+:)?{}>".format(re.escape(bloco)),
        trecho,
        flags=re.IGNORECASE,
    )
    if fecha:
        trecho = trecho[: fecha.start()]
    return _re_tag(trecho, nome)


def _montar_dados(
    invoice,
    serie,
    dest_cnpj,
    dest_nome,
    emit_cnpj,
    emit_nome,
    n_prot,
    dh_emi,
    dh_rec,
    chave,
    v_nf,
    cfops,
    itens,
):
    # type: (str, str, str, str, str, str, str, str, str, str, str, List[str], List[ItemNFe]) -> DadosNFe
    valor = parse_valor(v_nf) if v_nf else 0.0
    cfop_principal = cfops[0] if cfops else ""
    if cfops and len(set(cfops)) == 1:
        cfop_principal = cfops[0]
    prot_date = formatar_data_br(dh_rec)
    prot_time = formatar_hora(dh_rec)
    protocol_line = "{} {} {}".format(n_prot, prot_date, prot_time).strip()
    return DadosNFe(
        invoice=invoice,
        serie=serie,
        recipient_cnpj=re.sub(r"\D", "", dest_cnpj),
        recipient_cnpj_fmt=formatar_cnpj(dest_cnpj),
        recipient_sufixo=sufixo_cnpj(dest_cnpj),
        recipient_filial=filial_cnpj(dest_cnpj),
        recipient_nome=dest_nome,
        issue_date=formatar_data_br(dh_emi),
        protocol_number=n_prot,
        protocol_date=prot_date,
        protocol_time=prot_time,
        protocol_line=protocol_line,
        cfop=cfop_principal,
        cfops=list(cfops),
        valor=valor,
        valor_fmt=formatar_valor_us(valor) if v_nf else "",
        chave_acesso=chave,
        emit_cnpj=re.sub(r"\D", "", emit_cnpj),
        emit_nome=emit_nome,
        issuer_sap=None,
        itens=list(itens),
    )


def _parse_nfe_etree(texto):
    # type: (str) -> DadosNFe
    root = ET.fromstring(texto)

    invoice = _find_text(root, "NFe/infNFe/ide/nNF") or _find_text(root, "infNFe/ide/nNF")
    serie = _find_text(root, "NFe/infNFe/ide/serie") or _find_text(root, "infNFe/ide/serie")
    dh_emi = _find_text(root, "NFe/infNFe/ide/dhEmi") or _find_text(root, "infNFe/ide/dhEmi")

    dest_cnpj = _find_text(root, "NFe/infNFe/dest/CNPJ") or _find_text(root, "infNFe/dest/CNPJ")
    dest_nome = _find_text(root, "NFe/infNFe/dest/xNome") or _find_text(root, "infNFe/dest/xNome")

    emit_cnpj = _find_text(root, "NFe/infNFe/emit/CNPJ") or _find_text(root, "infNFe/emit/CNPJ")
    emit_nome = _find_text(root, "NFe/infNFe/emit/xNome") or _find_text(root, "infNFe/emit/xNome")

    n_prot = _find_text(root, "protNFe/infProt/nProt")
    dh_rec = _find_text(root, "protNFe/infProt/dhRecbto")
    chave = _find_text(root, "protNFe/infProt/chNFe")
    if not chave:
        for el in root.iter():
            if _local(el.tag) == "infNFe":
                chave = (el.attrib.get("Id") or "").replace("NFe", "", 1)
                break

    v_nf = _find_text(root, "NFe/infNFe/total/ICMSTot/vNF") or _find_text(
        root, "infNFe/total/ICMSTot/vNF"
    )

    itens = []  # type: List[ItemNFe]
    cfops = []  # type: List[str]
    for det in _find_all(root, "det"):
        n_item = int(det.attrib.get("nItem") or "0")
        prod = None
        for child in list(det):
            if _local(child.tag) == "prod":
                prod = child
                break
        if prod is None:
            continue
        cfop = codigo = desc = ""
        qcom = vun = vprod = "0"
        for child in list(prod):
            name = _local(child.tag)
            if name == "CFOP":
                cfop = _text(child)
            elif name == "cProd":
                codigo = _text(child)
            elif name == "xProd":
                desc = _text(child)
            elif name == "qCom":
                qcom = _text(child)
            elif name == "vUnCom":
                vun = _text(child)
            elif name == "vProd":
                vprod = _text(child)
        # infAdProd é irmão de <prod> dentro de <det> (texto extra da DANFE)
        inf_ad = ""
        for child in list(det):
            if _local(child.tag) == "infAdProd":
                inf_ad = _text(child)
                break
        desc = _juntar_descricao_item(desc, inf_ad)
        if cfop:
            cfops.append(cfop)
        itens.append(
            ItemNFe(
                n_item=n_item,
                codigo=codigo,
                descricao=desc,
                cfop=cfop,
                quantidade=float(qcom or 0),
                preco_unitario=float(vun or 0),
                valor_produto=float(vprod or 0),
            )
        )

    return _montar_dados(
        invoice,
        serie,
        dest_cnpj,
        dest_nome,
        emit_cnpj,
        emit_nome,
        n_prot,
        dh_emi,
        dh_rec,
        chave,
        v_nf,
        cfops,
        itens,
    )


def _parse_nfe_regex(texto):
    # type: (str) -> DadosNFe
    """
    Fallback quando o XML do SAP vem truncado / tag mismatched.
    Extrai só os campos que a automação precisa.
    """
    invoice = _re_tag(texto, "nNF")
    serie = _re_tag(texto, "serie")
    dh_emi = _re_tag(texto, "dhEmi")
    n_prot = _re_tag(texto, "nProt")
    dh_rec = _re_tag(texto, "dhRecbto")
    chave = _re_tag(texto, "chNFe")
    if not chave:
        m = re.search(r'Id\s*=\s*"NFe(\d{44})"', texto)
        if m:
            chave = m.group(1)
    v_nf = _re_tag(texto, "vNF")

    dest_cnpj = _re_tag_dentro(texto, "dest", "CNPJ")
    dest_nome = _re_tag_dentro(texto, "dest", "xNome")
    emit_cnpj = _re_tag_dentro(texto, "emit", "CNPJ")
    emit_nome = _re_tag_dentro(texto, "emit", "xNome")

    itens = []  # type: List[ItemNFe]
    cfops = []  # type: List[str]
    for m_det in re.finditer(
        r"<(?:\w+:)?det\b([^>]*)>([\s\S]*?)</(?:\w+:)?det>",
        texto,
        flags=re.IGNORECASE,
    ):
        attrs, corpo = m_det.group(1), m_det.group(2)
        m_n = re.search(r'nItem\s*=\s*"(\d+)"', attrs, flags=re.IGNORECASE)
        n_item = int(m_n.group(1)) if m_n else len(itens) + 1
        cfop = _re_tag(corpo, "CFOP")
        if cfop:
            cfops.append(cfop)
        itens.append(
            ItemNFe(
                n_item=n_item,
                codigo=_re_tag(corpo, "cProd"),
                descricao=_juntar_descricao_item(
                    _re_tag(corpo, "xProd"), _re_tag(corpo, "infAdProd")
                ),
                cfop=cfop,
                quantidade=float(_re_tag(corpo, "qCom") or 0),
                preco_unitario=float(_re_tag(corpo, "vUnCom") or 0),
                valor_produto=float(_re_tag(corpo, "vProd") or 0),
            )
        )
    if not cfops:
        cfops = re.findall(
            r"<(?:\w+:)?CFOP(?:\s[^>]*)?>([^<]*)</(?:\w+:)?CFOP>",
            texto,
            flags=re.IGNORECASE,
        )
        cfops = [c.strip() for c in cfops if c.strip()]

    if not dest_cnpj:
        raise ValueError(
            "XML do clipboard incompleto: nao achei CNPJ do destinatario (dest). "
            "Confira se o Ctrl+A / Ctrl+C pegou o XML inteiro."
        )
    if not invoice and not chave:
        raise ValueError(
            "XML do clipboard incompleto: nao achei nNF nem chave de acesso."
        )

    return _montar_dados(
        invoice,
        serie,
        dest_cnpj,
        dest_nome,
        emit_cnpj,
        emit_nome,
        n_prot,
        dh_emi,
        dh_rec,
        chave,
        v_nf,
        cfops,
        itens,
    )


def _salvar_dump_clipboard(texto, motivo):
    # type: (str, str) -> Path
    pasta = Path(__file__).resolve().parent.parent / "runs"
    pasta.mkdir(exist_ok=True)
    path = pasta / "clipboard_xml_ultimo.txt"
    path.write_text(
        "<!-- motivo: {} -->\n{}".format(motivo, texto or ""),
        encoding="utf-8",
        errors="replace",
    )
    return path


def parse_nfe_xml(xml_texto):
    # type: (str) -> DadosNFe
    if not (xml_texto or "").strip():
        raise ValueError("XML vazio.")

    texto = _limpar_texto_xml(xml_texto)

    try:
        return _parse_nfe_etree(texto)
    except ET.ParseError as exc:
        dump = _salvar_dump_clipboard(texto, "ParseError: {}".format(exc))
        try:
            dados = _parse_nfe_regex(texto)
            # ok com fallback
            return dados
        except Exception as exc2:
            raise ValueError(
                "Falha ao ler XML do SAP ({}). Tentativa regex: {}. "
                "Dump salvo em {}.".format(exc, exc2, dump)
            )


def parse_nfe_file(caminho):
    # type: (Union[str, Path]) -> DadosNFe
    path = Path(caminho)
    return parse_nfe_xml(path.read_text(encoding="utf-8"))


def _clipboard_parece_xml_nfe(texto):
    # type: (Optional[str]) -> bool
    t = (texto or "").strip()
    if len(t) < 40:
        return False
    low = t.lower()
    if "<" not in t:
        return False
    # NF-e / CT-e / nfeProc / cteProc (SAP às vezes cola trecho grande)
    marcadores = (
        "nfeproc",
        "infnfe",
        "cteproc",
        "infcte",
        "<nfe",
        "<cte",
        "nfe:",
        "cte:",
    )
    return any(m in low for m in marcadores)


def ler_clipboard_xml_ou_falhar():
    # type: () -> str
    """
    Lê o clipboard após Ctrl+C. Se vazio/inválido → XmlClipboardFalhou
    (parar sem gravar Status).
    """
    import pyperclip

    try:
        texto = pyperclip.paste()
    except Exception as exc:
        raise XmlClipboardFalhou(
            "Nao consegui ler o clipboard apos Ctrl+C: {}".format(exc)
        )
    if not _clipboard_parece_xml_nfe(texto):
        dump = _salvar_dump_clipboard(texto or "", "Ctrl+C XML falhou / clipboard invalido")
        raise XmlClipboardFalhou(
            "Ctrl+C do XML nao funcionou (clipboard vazio ou sem XML de NF-e/CT-e). "
            "Automacao parada — Status no Excel NAO foi alterado. "
            "Dump: {}".format(dump)
        )
    return texto or ""


def parse_nfe_clipboard(texto_clipboard=None):
    # type: (Optional[str]) -> DadosNFe
    """Lê XML do clipboard (após Ctrl+C no SAP) ou de texto passado."""
    if texto_clipboard is None:
        texto_clipboard = ler_clipboard_xml_ou_falhar()
    try:
        return parse_nfe_xml(texto_clipboard or "")
    except XmlClipboardFalhou:
        raise
    except Exception as exc:
        dump = _salvar_dump_clipboard(
            texto_clipboard or "", "parse falhou apos Ctrl+C: {}".format(exc)
        )
        raise XmlClipboardFalhou(
            "Ctrl+C do XML nao trouxe XML valido: {}. "
            "Automacao parada — Status no Excel NAO foi alterado. "
            "Dump: {}".format(exc, dump)
        ) from exc
