#!/usr/bin/env python3
"""IVD knowledge-graph lookup for medical-vertical course segmentation (L2).

Confirms terminology / system membership against the IVD knowledge tree and
returns authoritative reference values from a built-in table BEFORE segmentation.

Two sources are combined:
  1. ivd-knowledge-tree.json  — the course-structure knowledge graph (domains,
     nodes, test_parameters, courses). Path resolved via: --json arg >
     $IVD_KNOWLEDGE_TREE > auto-discovery of known locations.
  2. Built-in REFERENCE_RANGES — adult reference ranges for common CBC /
     coagulation / urinalysis / biochemistry / immunoassay parameters. Marked
     `needs_medical_review`: publish-time values must be re-checked against the
     authoritative textbook / clinical guideline / local lab reference interval.

Usage:
  python3 ivd-lookup.py "RBC"                 # exact / fuzzy lookup (JSON out)
  python3 ivd-lookup.py "血常规" --human       # human-readable output
  python3 ivd-lookup.py "凝血"                 # system-level lookup
  python3 ivd-lookup.py --list-systems        # list available systems
  python3 ivd-lookup.py --check "RBC 4.5-5.5×10¹²/L"   # verify a written value
  python3 ivd-lookup.py "RBC" --json /path/to/ivd-knowledge-tree.json

Exit codes: 0 = found (or valid check), 2 = not found / uncertain, 1 = usage error.

Never invents a value: if nothing matches, the output is `matched: false` with
`uncertain: true` and the span must be flagged for human confirmation.
"""

import argparse
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Built-in authoritative reference table (adult, common parameters).
# Confidence `needs_medical_review` = correct starting point, MUST be verified
# against the authoritative textbook / guideline / lab reference before publish.
# ---------------------------------------------------------------------------
REFERENCE_RANGES = [
    # ---- 血液检验 (hematology / CBC) ----
    {"abbr": "WBC", "zh": "白细胞计数", "en": "White Blood Cell Count",
     "system": "hematology", "system_zh": "血液检验",
     "value": "4.0–10.0", "unit": "×10⁹/L",
     "note": "方案权威示例值", "confidence": "needs_medical_review"},
    {"abbr": "RBC", "zh": "红细胞计数", "en": "Red Blood Cell Count",
     "system": "hematology", "system_zh": "血液检验",
     "value": "4.5–5.5", "unit": "×10¹²/L",
     "note": "方案权威示例值；性别差异参考：男性 4.3–5.8、女性 3.8–5.1，发布前按教材审核",
     "confidence": "needs_medical_review"},
    {"abbr": "HGB", "zh": "血红蛋白", "en": "Hemoglobin",
     "system": "hematology", "system_zh": "血液检验",
     "value": "男 130–175 / 女 115–150", "unit": "g/L",
     "note": "性别差异显著，发布前须确认成人/儿童分组",
     "confidence": "needs_medical_review"},
    {"abbr": "HCT", "zh": "血细胞比容", "en": "Hematocrit",
     "system": "hematology", "system_zh": "血液检验",
     "value": "男 40–50% / 女 35–45%", "unit": "%",
     "note": "", "confidence": "needs_medical_review"},
    {"abbr": "PLT", "zh": "血小板计数", "en": "Platelet Count",
     "system": "hematology", "system_zh": "血液检验",
     "value": "125–350", "unit": "×10⁹/L",
     "note": "方案示例值", "confidence": "needs_medical_review"},
    {"abbr": "MCV", "zh": "平均红细胞体积", "en": "Mean Corpuscular Volume",
     "system": "hematology", "system_zh": "血液检验",
     "value": "80–100", "unit": "fL", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "MCH", "zh": "平均血红蛋白量", "en": "Mean Corpuscular Hemoglobin",
     "system": "hematology", "system_zh": "血液检验",
     "value": "27–34", "unit": "pg", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "MCHC", "zh": "平均血红蛋白浓度", "en": "Mean Corpuscular Hemoglobin Concentration",
     "system": "hematology", "system_zh": "血液检验",
     "value": "316–354", "unit": "g/L", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "RDW-CV", "zh": "红细胞体积分布宽度", "en": "Red Cell Distribution Width",
     "system": "hematology", "system_zh": "血液检验",
     "value": "11.6–14.6", "unit": "%", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "RET", "zh": "网织红细胞", "en": "Reticulocyte",
     "system": "hematology", "system_zh": "血液检验",
     "value": "0.5–1.5", "unit": "%", "note": "成人；新生儿期显著偏高", "confidence": "needs_medical_review"},
    {"abbr": "NRBC", "zh": "有核红细胞", "en": "Nucleated Red Blood Cell",
     "system": "hematology", "system_zh": "血液检验",
     "value": "0", "unit": "/100 WBC",
     "note": "正常成人外周血为 0；出现即异常（新生儿期除外）", "confidence": "needs_medical_review"},
    {"abbr": "NEUT", "zh": "中性粒细胞", "en": "Neutrophil",
     "system": "hematology", "system_zh": "血液检验",
     "value": "40–75", "unit": "%", "note": "白细胞分类百分比", "confidence": "needs_medical_review"},
    {"abbr": "LYM", "zh": "淋巴细胞", "en": "Lymphocyte",
     "system": "hematology", "system_zh": "血液检验",
     "value": "20–40", "unit": "%", "note": "白细胞分类百分比", "confidence": "needs_medical_review"},
    {"abbr": "MONO", "zh": "单核细胞", "en": "Monocyte",
     "system": "hematology", "system_zh": "血液检验",
     "value": "3–8", "unit": "%", "note": "白细胞分类百分比", "confidence": "needs_medical_review"},
    {"abbr": "EO", "zh": "嗜酸性粒细胞", "en": "Eosinophil",
     "system": "hematology", "system_zh": "血液检验",
     "value": "0.5–5", "unit": "%", "note": "白细胞分类百分比", "confidence": "needs_medical_review"},
    {"abbr": "BASO", "zh": "嗜碱性粒细胞", "en": "Basophil",
     "system": "hematology", "system_zh": "血液检验",
     "value": "0–1", "unit": "%", "note": "白细胞分类百分比", "confidence": "needs_medical_review"},
    # ---- 凝血检验 (coagulation) ----
    {"abbr": "PT", "zh": "凝血酶原时间", "en": "Prothrombin Time",
     "system": "coagulation", "system_zh": "凝血检验",
     "value": "11–14", "unit": "s", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "INR", "zh": "国际标准化比值", "en": "International Normalized Ratio",
     "system": "coagulation", "system_zh": "凝血检验",
     "value": "0.8–1.2", "unit": "", "note": "治疗性抗凝靶区间另计（如 2.0–3.0）", "confidence": "needs_medical_review"},
    {"abbr": "APTT", "zh": "活化部分凝血活酶时间", "en": "Activated Partial Thromboplastin Time",
     "system": "coagulation", "system_zh": "凝血检验",
     "value": "25–35", "unit": "s", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "TT", "zh": "凝血酶时间", "en": "Thrombin Time",
     "system": "coagulation", "system_zh": "凝血检验",
     "value": "16–18", "unit": "s", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "FIB", "zh": "纤维蛋白原", "en": "Fibrinogen",
     "system": "coagulation", "system_zh": "凝血检验",
     "value": "2.0–4.0", "unit": "g/L", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "D-Dimer", "zh": "D-二聚体", "en": "D-Dimer",
     "system": "coagulation", "system_zh": "凝血检验",
     "value": "<0.5", "unit": "mg/L", "note": "FEU；升高提示纤溶激活，非特异性", "confidence": "needs_medical_review"},
    {"abbr": "AT-III", "zh": "抗凝血酶Ⅲ", "en": "Antithrombin III",
     "system": "coagulation", "system_zh": "凝血检验",
     "value": "80–120", "unit": "%", "note": "", "confidence": "needs_medical_review"},
    # ---- 尿液检验 (urinalysis) ----
    {"abbr": "SG", "zh": "尿比重", "en": "Specific Gravity",
     "system": "urinalysis", "system_zh": "尿液检验",
     "value": "1.003–1.030", "unit": "", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "尿pH", "zh": "尿酸碱度", "en": "Urine pH",
     "system": "urinalysis", "system_zh": "尿液检验",
     "value": "4.5–8.0", "unit": "", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "尿蛋白", "zh": "尿蛋白定性", "en": "Urine Protein",
     "system": "urinalysis", "system_zh": "尿液检验",
     "value": "阴性", "unit": "", "note": "24h 尿蛋白 <150 mg", "confidence": "needs_medical_review"},
    {"abbr": "尿糖", "zh": "尿糖定性", "en": "Urine Glucose",
     "system": "urinalysis", "system_zh": "尿液检验",
     "value": "阴性", "unit": "", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "尿酮体", "zh": "尿酮体定性", "en": "Urine Ketone",
     "system": "urinalysis", "system_zh": "尿液检验",
     "value": "阴性", "unit": "", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "尿胆原", "zh": "尿胆原", "en": "Urobilinogen",
     "system": "urinalysis", "system_zh": "尿液检验",
     "value": "阴性～弱阳性", "unit": "", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "尿胆红素", "zh": "尿胆红素", "en": "Urine Bilirubin",
     "system": "urinalysis", "system_zh": "尿液检验",
     "value": "阴性", "unit": "", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "尿RBC", "zh": "尿红细胞", "en": "Urine Red Blood Cell",
     "system": "urinalysis", "system_zh": "尿液检验",
     "value": "0–3", "unit": "/HPF", "note": "镜检高倍视野", "confidence": "needs_medical_review"},
    {"abbr": "尿WBC", "zh": "尿白细胞", "en": "Urine White Blood Cell",
     "system": "urinalysis", "system_zh": "尿液检验",
     "value": "0–5", "unit": "/HPF", "note": "镜检高倍视野", "confidence": "needs_medical_review"},
    # ---- 生化检验 (biochemistry) ----
    {"abbr": "ALT", "zh": "丙氨酸氨基转移酶", "en": "Alanine Aminotransferase",
     "system": "biochemistry", "system_zh": "生化检验",
     "value": "7–40", "unit": "U/L", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "AST", "zh": "天冬氨酸氨基转移酶", "en": "Aspartate Aminotransferase",
     "system": "biochemistry", "system_zh": "生化检验",
     "value": "8–40", "unit": "U/L", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "TBIL", "zh": "总胆红素", "en": "Total Bilirubin",
     "system": "biochemistry", "system_zh": "生化检验",
     "value": "3.4–17.1", "unit": "μmol/L", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "ALB", "zh": "白蛋白", "en": "Albumin",
     "system": "biochemistry", "system_zh": "生化检验",
     "value": "40–55", "unit": "g/L", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "TP", "zh": "总蛋白", "en": "Total Protein",
     "system": "biochemistry", "system_zh": "生化检验",
     "value": "60–80", "unit": "g/L", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "Cr", "zh": "血肌酐", "en": "Creatinine",
     "system": "biochemistry", "system_zh": "生化检验",
     "value": "男 57–111 / 女 41–81", "unit": "μmol/L",
     "note": "性别差异", "confidence": "needs_medical_review"},
    {"abbr": "BUN", "zh": "尿素氮", "en": "Blood Urea Nitrogen",
     "system": "biochemistry", "system_zh": "生化检验",
     "value": "2.9–8.2", "unit": "mmol/L", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "FPG", "zh": "空腹血糖", "en": "Fasting Plasma Glucose",
     "system": "biochemistry", "system_zh": "生化检验",
     "value": "3.9–6.1", "unit": "mmol/L", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "TC", "zh": "总胆固醇", "en": "Total Cholesterol",
     "system": "biochemistry", "system_zh": "生化检验",
     "value": "<5.2", "unit": "mmol/L", "note": "理想水平", "confidence": "needs_medical_review"},
    {"abbr": "TG", "zh": "甘油三酯", "en": "Triglyceride",
     "system": "biochemistry", "system_zh": "生化检验",
     "value": "<1.7", "unit": "mmol/L", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "HDL-C", "zh": "高密度脂蛋白胆固醇", "en": "HDL Cholesterol",
     "system": "biochemistry", "system_zh": "生化检验",
     "value": ">1.0", "unit": "mmol/L", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "LDL-C", "zh": "低密度脂蛋白胆固醇", "en": "LDL Cholesterol",
     "system": "biochemistry", "system_zh": "生化检验",
     "value": "<3.4", "unit": "mmol/L", "note": "理想水平", "confidence": "needs_medical_review"},
    # ---- 免疫检验 (immunoassay) ----
    {"abbr": "CRP", "zh": "C反应蛋白", "en": "C-Reactive Protein",
     "system": "immunoassay", "system_zh": "免疫检验",
     "value": "<8", "unit": "mg/L", "note": "常规方法；hs-CRP 另见心血管风险分层", "confidence": "needs_medical_review"},
    {"abbr": "hs-CRP", "zh": "超敏C反应蛋白", "en": "High-Sensitivity CRP",
     "system": "immunoassay", "system_zh": "免疫检验",
     "value": "<3", "unit": "mg/L", "note": "心血管风险分层参考", "confidence": "needs_medical_review"},
    {"abbr": "AFP", "zh": "甲胎蛋白", "en": "Alpha-Fetoprotein",
     "system": "immunoassay", "system_zh": "免疫检验",
     "value": "<7", "unit": "ng/mL", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "CEA", "zh": "癌胚抗原", "en": "Carcinoembryonic Antigen",
     "system": "immunoassay", "system_zh": "免疫检验",
     "value": "<5", "unit": "ng/mL", "note": "非吸烟者", "confidence": "needs_medical_review"},
    {"abbr": "CA125", "zh": "糖类抗原125", "en": "Carbohydrate Antigen 125",
     "system": "immunoassay", "system_zh": "免疫检验",
     "value": "<35", "unit": "U/mL", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "CA19-9", "zh": "糖类抗原19-9", "en": "Carbohydrate Antigen 19-9",
     "system": "immunoassay", "system_zh": "免疫检验",
     "value": "<37", "unit": "U/mL", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "PSA", "zh": "前列腺特异性抗原", "en": "Prostate-Specific Antigen",
     "system": "immunoassay", "system_zh": "免疫检验",
     "value": "<4", "unit": "ng/mL", "note": "", "confidence": "needs_medical_review"},
    {"abbr": "HBsAg", "zh": "乙肝表面抗原", "en": "Hepatitis B Surface Antigen",
     "system": "immunoassay", "system_zh": "免疫检验",
     "value": "阴性", "unit": "", "note": "定性判读", "confidence": "needs_medical_review"},
    {"abbr": "HCV-Ab", "zh": "丙肝抗体", "en": "Hepatitis C Antibody",
     "system": "immunoassay", "system_zh": "免疫检验",
     "value": "阴性", "unit": "", "note": "定性判读", "confidence": "needs_medical_review"},
    # ---- 分子检验 (molecular) ----
    {"abbr": "分子定量", "zh": "分子定量检测", "en": "Molecular Quantitative Assay",
     "system": "molecular", "system_zh": "分子检验",
     "value": "依赖试剂盒/平台", "unit": "",
     "note": "定量参考值依试剂说明书与平台，发布前必须人工确认", "confidence": "needs_medical_review"},
]

# 权威系统清单（与 ivd-knowledge-tree.json domains 对齐）
SYSTEMS = [
    {"id": "general", "zh": "通识基础", "en": "General"},
    {"id": "hematology", "zh": "血液检验", "en": "Hematology"},
    {"id": "coagulation", "zh": "凝血检验", "en": "Coagulation"},
    {"id": "urinalysis", "zh": "尿液检验", "en": "Urinalysis"},
    {"id": "immunoassay", "zh": "免疫检验", "en": "Immunoassay"},
    {"id": "biochemistry", "zh": "生化检验", "en": "Biochemistry"},
    {"id": "molecular", "zh": "分子检验", "en": "Molecular"},
]

# 常见同义/别名 → 规范系统 id
SYSTEM_ALIASES = {
    "血常规": "hematology", "血液": "hematology", "血细胞": "hematology",
    "cbc": "hematology", "hematology": "hematology",
    "凝血": "coagulation", "coagulation": "coagulation", "pt": "coagulation",
    "尿液": "urinalysis", "尿常规": "urinalysis", "尿沉渣": "urinalysis", "urinalysis": "urinalysis",
    "免疫": "immunoassay", "肿瘤标志物": "immunoassay", "immunoassay": "immunoassay",
    "生化": "biochemistry", "肝功能": "biochemistry", "肾功能": "biochemistry", "biochemistry": "biochemistry",
    "分子": "molecular", "pcr": "molecular", "ngs": "molecular", "molecular": "molecular",
}


def norm(s):
    """Normalize a query for matching: upper, strip, collapse whitespace."""
    return re.sub(r"\s+", "", s.upper())


def find_knowledge_tree(explicit=None):
    """Resolve the ivd-knowledge-tree.json path."""
    candidates = []
    if explicit:
        candidates.append(explicit)
    env = os.environ.get("IVD_KNOWLEDGE_TREE")
    if env:
        candidates.append(env)
    here = os.path.dirname(os.path.abspath(__file__))
    candidates += [
        os.path.join(here, "..", "references", "ivd-knowledge-tree.json"),
        os.path.join(here, "..", "ivd-knowledge-tree.json"),
        "/home/sysmex/worktrees/ai-shifu-dev/docs/generated/ivd-knowledge-tree.json",
        "docs/generated/ivd-knowledge-tree.json",
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return os.path.abspath(c)
    return None


def load_graph(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def graph_lookup(graph, query):
    """Search the knowledge graph for domains/nodes/test_parameters matching query."""
    if not graph:
        return {"status": "not_found", "reason": "knowledge tree not readable"}
    q = norm(query)
    # system alias expansion (e.g. 血常规 → hematology, 凝血 → coagulation)
    alias_system_ids = set()
    for alias, sid in SYSTEM_ALIASES.items():
        if q and q == norm(alias):
            alias_system_ids.add(sid)
    matched_domains = []
    matched_nodes = []
    matched_params = []
    for dom in graph.get("domains", []):
        dom_hit = dom.get("id") in alias_system_ids
        for n in dom.get("nodes", []):
            node_hit = False
            for tp in n.get("metadata", {}).get("test_parameters", []):
                if q and q in norm(tp):
                    matched_params.append(tp)
                    node_hit = True
            if q and (q in norm(n.get("name", "")) or q in norm(n.get("id", ""))):
                node_hit = True
            if node_hit:
                matched_nodes.append({
                    "id": n.get("id"), "name": n.get("name"),
                    "difficulty": n.get("difficulty"),
                    "test_parameters": n.get("metadata", {}).get("test_parameters", []),
                    "instrument_models": n.get("metadata", {}).get("instrument_models", []),
                    "courses": [c.get("title") for c in n.get("courses", [])],
                })
                dom_hit = True
        # system-level match (domain name / id / description)
        if q and (q in norm(dom.get("name", "")) or q in norm(dom.get("id", ""))
                  or q in norm(dom.get("description", ""))):
            matched_domains.append({"id": dom.get("id"), "name": dom.get("name"),
                                    "node_count": len(dom.get("nodes", []))})
            dom_hit = True
        if dom_hit and not any(m.get("id") == dom.get("id") for m in matched_domains):
            matched_domains.append({"id": dom.get("id"), "name": dom.get("name"),
                                    "node_count": len(dom.get("nodes", []))})
    return {
        "status": "found" if (matched_domains or matched_nodes) else "no_match",
        "matched_domains": matched_domains,
        "matched_nodes": matched_nodes,
        "matched_test_parameters": sorted(set(matched_params)),
    }


def ref_lookup(query):
    """Look up built-in reference ranges for a parameter/system query."""
    q = norm(query)
    # system-level match FIRST (e.g. 血常规/凝血/生化 → whole system table)
    sys_id = None
    for alias, sid in SYSTEM_ALIASES.items():
        if q and q == norm(alias):
            sys_id = sid
            break
    if sys_id:
        return [r for r in REFERENCE_RANGES if r["system"] == sys_id], "system"
    # then exact / fuzzy parameter match
    hits = []
    for r in REFERENCE_RANGES:
        if q and (q == norm(r["abbr"]) or q == norm(r["zh"]) or q == norm(r["en"])
                  or (q in norm(r["abbr"])) or (q in norm(r["zh"]))):
            hits.append(r)
    if hits:
        return hits, "parameter"
    return [], None


def check_value(text):
    """--check: verify a written reference value like 'RBC 4.5-5.5×10¹²/L'."""
    # extract leading abbreviation
    m = re.match(r"^([A-Za-z][A-Za-z0-9\-]*)\s*(.*)$", text.strip())
    if not m:
        return {"valid": False, "reason": "cannot parse parameter abbreviation"}
    abbr, rest = m.group(1), m.group(2).strip()
    hits, kind = ref_lookup(abbr)
    if not hits:
        return {"valid": False, "reason": f"unknown parameter '{abbr}'",
                "uncertain": True, "human_review_required": True}
    r = hits[0]
    # normalize dashes and whitespace for comparison
    def normval(s):
        s = re.sub(r"[\-\u2010\u2011\u2012\u2013\u2014–—]", "-", s)
        return re.sub(r"\s+", "", s)
    expected = normval(f"{r['value']} {r['unit']}".strip())
    provided = normval(rest)
    if expected == provided:
        return {"valid": True, "parameter": r["abbr"], "expected": expected,
                "provided": provided, "confidence": r["confidence"]}
    return {"valid": False, "parameter": r["abbr"],
            "expected": expected, "provided": provided,
            "confidence": r["confidence"], "human_review_required": True,
            "reason": "value differs from built-in reference — must be human-confirmed"}


def main():
    ap = argparse.ArgumentParser(description="IVD knowledge-graph + reference-value lookup")
    ap.add_argument("query", nargs="?", help="检验项目/系统/术语关键词 (e.g. RBC, 血常规, 凝血)")
    ap.add_argument("--json", dest="json_path", help="ivd-knowledge-tree.json 路径")
    ap.add_argument("--list-systems", action="store_true", help="列出可用系统")
    ap.add_argument("--check", metavar="VALUE", help="校验已写参考值，如 'RBC 4.5-5.5×10¹²/L'")
    ap.add_argument("--human", action="store_true", help="输出人类可读文本")
    args = ap.parse_args()

    if args.list_systems:
        out = {"systems": SYSTEMS}
        if args.human:
            for s in SYSTEMS:
                print(f"{s['id']:<14} {s['zh']} / {s['en']}")
            return 0
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if args.check:
        result = check_value(args.check)
        code = 0 if result.get("valid") else 2
        if args.human:
            if result.get("valid"):
                print(f"PASS  {result['parameter']}: {result['provided']} (confidence={result['confidence']})")
            else:
                print(f"REVIEW {result.get('reason')} | expected={result.get('expected')} provided={result.get('provided')}")
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return code

    if not args.query:
        ap.error("query 必填 (或使用 --list-systems / --check)")

    graph_path = find_knowledge_tree(args.json_path)
    graph = load_graph(graph_path) if graph_path else None
    gres = graph_lookup(graph, args.query)

    refs, ref_kind = ref_lookup(args.query)
    matched = (gres["status"] == "found") or bool(refs)
    # uncertain only when BOTH graph and reference values miss — otherwise the
    # built-in table still grounds the span and the value is usable for drafting
    no_ref = not refs
    no_graph = gres["status"] in ("not_found", "no_match")
    uncertain = no_ref and no_graph

    result = {
        "query": args.query,
        "matched": matched,
        "uncertain": uncertain,
        "human_review_required": no_ref or (no_graph and not refs),
        "knowledge_graph": {
            "status": gres["status"],
            "source": os.path.basename(graph_path) if graph_path else None,
            "matched_domains": gres["matched_domains"],
            "matched_nodes": gres["matched_nodes"],
            "matched_test_parameters": gres["matched_test_parameters"],
        },
        "reference_values": {
            "found": bool(refs),
            "match_kind": ref_kind,
            "entries": refs,
        },
        "note": "图谱查不到或参考值未命中时，该 span 标记 uncertain(high)，保留源文，交人工确认；禁止自行编造参考值",
    }
    if args.human:
        print(f"query: {args.query}")
        print(f"matched: {matched} | uncertain: {uncertain}")
        print(f"knowledge_graph: {gres['status']}"
              + (f" ({os.path.basename(graph_path)})" if graph_path else ""))
        for d in gres["matched_domains"]:
            print(f"  system: {d['id']} {d['name']} (nodes={d['node_count']})")
        for n in gres["matched_nodes"][:5]:
            print(f"  node: {n['id']} {n['name']} params={n['test_parameters']}")
        print(f"reference_values: {'found' if refs else 'NOT FOUND'}")
        for r in refs[:20]:
            print(f"  {r['abbr']:<10} {r['zh']:<12} {r['value']} {r['unit']}  [{r['system']}] conf={r['confidence']}")
        return 0 if matched else 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if matched else 2


if __name__ == "__main__":
    sys.exit(main())
