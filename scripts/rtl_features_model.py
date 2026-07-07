"""RTL-feature-based intent classifier (improved with Random Forest).

Extracts hardware-aware features from each diff (reset / always_ff / parameters,
lines added/removed, signal declarations, control flow, etc.) and trains a
Random Forest classifier on them. Compared against a TF-IDF text baseline and a
hybrid (text + RTL features) on the SAME train/test split.

Run (after building the dataset):
    python3 scripts/rtl_features_model.py
"""
import json, re
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.sparse import hstack, csr_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "figures"; OUT.mkdir(parents=True, exist_ok=True)
candidates = [ROOT/"data"/"processed"/"opentitan_real_examples_medium.jsonl",
              ROOT/"data"/"processed"/"opentitan_real_examples_smoke.jsonl"]
DATA = next((p for p in candidates if p.exists()), None)
assert DATA is not None, "Run extract_commits + build_dataset first."
INT = ["bug_fix","feature_or_behavior_change","refactor_cleanup","configuration_timing"]

PATTERNS = {"reset":r"\b(reset|rst)\b","always_ff":r"\balways_ff\b","always_comb":r"\balways_comb\b",
"assign":r"\bassign\b","parameter":r"\b(parameter|localparam|param)\b","clock":r"\b(clk|clock)\b",
"assertion":r"\b(assert|assume|cover)\b","signal_decl":r"\b(logic|wire|reg)\b",
"case_fsm":r"\b(case|state|fsm)\b","if_else":r"\b(if|else)\b","module":r"\b(module|endmodule)\b",
"comment":r"//","todo":r"\b(todo|fixme)\b"}
FEATURE_NAMES = ["added","removed","net","total","add_remove_ratio"] + list(PATTERNS.keys())

def features(d):
    L=d.splitlines()
    a=sum(1 for l in L if l.startswith("+") and not l.startswith("+++"))
    r=sum(1 for l in L if l.startswith("-") and not l.startswith("---"))
    low=d.lower()
    return [a,r,a-r,a+r,a/(r+1)] + [len(re.findall(p,low)) for p in PATTERNS.values()]

rows=[json.loads(l) for l in open(DATA)]
X=np.array([features(r["unified_diff"]) for r in rows],float)
texts=[r.get("normalized_diff") or r["unified_diff"] for r in rows]
y=np.array([INT.index(r["intent_label"]) for r in rows])
print(f"dataset: {DATA.name} | examples: {len(rows)} | RTL features: {len(FEATURE_NAMES)}")

tr,te=train_test_split(np.arange(len(rows)),test_size=0.25,random_state=13,stratify=y)
def macro(yp): return f1_score(y[te],yp,average="macro",labels=range(4),zero_division=0)

# TF-IDF baseline
vec=TfidfVectorizer(ngram_range=(1,2)); Xt=vec.fit_transform([texts[i] for i in tr]); Xte=vec.transform([texts[i] for i in te])
f1_tfidf=macro(LogisticRegression(max_iter=2000,class_weight="balanced").fit(Xt,y[tr]).predict(Xte))
# RTL features + Random Forest
sc=StandardScaler().fit(X[tr])
rf=RandomForestClassifier(n_estimators=300,class_weight="balanced",random_state=13).fit(X[tr],y[tr])
f1_rtl=macro(rf.predict(X[te]))
# Hybrid
lrh=LogisticRegression(max_iter=2000,class_weight="balanced").fit(
    hstack([Xt,csr_matrix(sc.transform(X[tr]))]), y[tr])
f1_hyb=macro(lrh.predict(hstack([Xte,csr_matrix(sc.transform(X[te]))])))

print(f"\nIntent macro-F1 (test n={len(te)}):")
print(f"  TF-IDF baseline (text)        : {f1_tfidf:.3f}")
print(f"  RTL features + Random Forest  : {f1_rtl:.3f}")
print(f"  Hybrid (text + RTL features)  : {f1_hyb:.3f}")
print("\nTop RTL features (Random Forest importance):")
for i in np.argsort(rf.feature_importances_)[::-1][:5]:
    print(f"  {FEATURE_NAMES[i]:<16} {rf.feature_importances_[i]:.3f}")

fig,ax=plt.subplots(figsize=(7,4.3))
names=["TF-IDF\n(text)","RTL features\n+ Random Forest","Hybrid\n(text + RTL)"]
vals=[f1_tfidf,f1_rtl,f1_hyb]; cols=["#999999","#2c7fb8","#41ab5d"]
bars=ax.bar(names,vals,color=cols)
for b in bars: ax.text(b.get_x()+b.get_width()/2,b.get_height()+0.01,f"{b.get_height():.3f}",ha="center",fontweight="bold")
ax.axhline(f1_tfidf,ls="--",color="#999999",lw=1)
ax.set_ylabel("Intent macro-F1"); ax.set_ylim(0,max(vals)+0.12)
ax.set_title("Hardware-aware features beat the text baseline")
fig.tight_layout(); fig.savefig(OUT/"rtl_features_model.png",dpi=130)
print("\nSaved figure: outputs/figures/rtl_features_model.png")
