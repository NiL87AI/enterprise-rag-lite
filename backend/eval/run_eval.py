"""Eval harness per Enterprise RAG Lite.

Misura su dataset reale:
- Answer accuracy    : la risposta contiene le keyword attese
- Retrieval hit rate : il documento sorgente corretto e' nei top-k
- Refusal accuracy   : le domande trappola vengono correttamente filtrate

Uso (da backend/):
    python -m eval.run_eval
    python -m eval.run_eval --dataset eval/mio_dataset.json

Output: tabella in console + eval/eval_report.json + eval/eval_report.md
"""
import asyncio
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.rag_pipeline import run_rag


def check_item(item, context, answer, filtered):
    """Ritorna (passed, detail) per una singola domanda."""
    sources = [c.get("metadata", {}).get("filename", "?") for c in context]

    # Domanda trappola: passa se il sistema filtra
    if item.get("expect_filtered"):
        return filtered, "filtered" if filtered else f"NON filtrata: {answer[:60]}"

    if filtered:
        return False, "filtrata ma la risposta esiste nei documenti"

    # Retrieval: il PDF atteso e' tra le fonti?
    expected = item.get("expected_source")
    retrieval_ok = expected in sources if expected else True

    # Answer: contiene tutte le keyword?
    kws = [k.lower() for k in item.get("must_contain", [])]
    missing = [k for k in kws if k not in answer.lower()]

    passed = retrieval_ok and not missing
    detail = ""
    if not retrieval_ok:
        detail = f"source attesa '{expected}', trovate {sources}"
    if missing:
        detail += f" | keyword mancanti: {missing}"
    return passed, detail.strip(" |")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=str(Path(__file__).parent / "eval_dataset.json"))
    args = ap.parse_args()

    dataset = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    questions = dataset["questions"]
    print(f"\n=== EVAL: {len(questions)} domande ===\n")

    results = []
    for item in questions:
        t0 = time.time()
        try:
            context, answer, conf, filtered = await run_rag(
                item["question"], item.get("document_ids")
            )
        except Exception as e:
            context, answer, conf, filtered = [], f"ERRORE: {e}", 0.0, True
        latency = time.time() - t0

        passed, detail = check_item(item, context, answer, filtered)
        results.append({
            "id": item["id"], "category": item["category"],
            "question": item["question"], "passed": passed,
            "confidence": conf, "filtered": filtered,
            "latency_s": round(latency, 1), "answer": answer,
            "sources": [c.get("metadata", {}).get("filename") for c in context],
            "detail": detail,
        })
        mark = "PASS" if passed else "FAIL"
        print(f"[{mark}] {item['id']:>9} | conf {conf:.2f} | {latency:5.1f}s | {item['question'][:55]}")
        if detail:
            print(f"         -> {detail}")

    # --- Metriche aggregate -------------------------------------------
    n = len(results)
    n_pass = sum(r["passed"] for r in results)
    traps = [r for r in results if r["id"].startswith("trap")]
    real = [r for r in results if not r["id"].startswith("trap")]
    refusal_acc = sum(r["passed"] for r in traps) / len(traps) if traps else 0
    answer_acc = sum(r["passed"] for r in real) / len(real) if real else 0
    avg_conf = sum(r["confidence"] for r in real) / len(real) if real else 0
    avg_lat = sum(r["latency_s"] for r in results) / n

    print("\n=== RISULTATI ===")
    print(f"Answer accuracy   : {answer_acc*100:.0f}%  ({sum(r['passed'] for r in real)}/{len(real)})")
    print(f"Refusal accuracy  : {refusal_acc*100:.0f}%  ({sum(r['passed'] for r in traps)}/{len(traps)})")
    print(f"Score totale      : {n_pass*100//n}%  ({n_pass}/{n})")
    print(f"Confidence media  : {avg_conf:.2f}")
    print(f"Latenza media     : {avg_lat:.1f}s")

    out_dir = Path(__file__).parent
    (out_dir / "eval_report.json").write_text(
        json.dumps({"summary": {
            "total": n, "passed": n_pass,
            "answer_accuracy": round(answer_acc, 2),
            "refusal_accuracy": round(refusal_acc, 2),
            "avg_confidence": round(avg_conf, 2),
            "avg_latency_s": round(avg_lat, 1),
        }, "results": results}, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    md = ["# Eval Report\n",
          f"| Metrica | Valore |", "|---|---|",
          f"| Answer accuracy | {answer_acc*100:.0f}% |",
          f"| Refusal accuracy | {refusal_acc*100:.0f}% |",
          f"| Confidence media | {avg_conf:.2f} |",
          f"| Latenza media | {avg_lat:.1f}s |", "",
          "| ID | Esito | Conf | Lat | Domanda |", "|---|---|---|---|---|"]
    for r in results:
        md.append(f"| {r['id']} | {'PASS' if r['passed'] else 'FAIL'} | "
                  f"{r['confidence']:.2f} | {r['latency_s']}s | {r['question']} |")
    (out_dir / "eval_report.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nReport: {out_dir/'eval_report.json'} e eval_report.md")


if __name__ == "__main__":
    asyncio.run(main())
