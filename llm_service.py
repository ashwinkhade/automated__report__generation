"""
LLM Service.

Wraps OpenAI / LangChain calls to produce:
- Executive summaries
- Natural-language insights
- Strategic recommendations
- Q&A chatbot answers about a generated report

Gracefully degrades to deterministic templated text if no OPENAI_API_KEY is set
so the system remains demoable offline.
"""
from __future__ import annotations
import json
import logging
from typing import Dict, Any, List, Optional
from backend.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """LLM-powered natural language generation for reports."""

    def __init__(self):
        self.client = None
        self.enabled = bool(settings.OPENAI_API_KEY)
        if self.enabled:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.warning("Failed to initialize OpenAI client: %s", e)
                self.enabled = False

    # ---------------- internal helper ----------------

    def _chat(self, system: str, user: str, *, json_mode: bool = False) -> str:
        if not self.enabled or not self.client:
            return ""
        try:
            kwargs: Dict[str, Any] = dict(
                model=settings.OPENAI_MODEL,
                temperature=settings.OPENAI_TEMPERATURE,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = self.client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except Exception as e:
            logger.exception("LLM call failed: %s", e)
            return ""

    # ---------------- public methods ----------------

    def generate_report_narrative(self, analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Produce summary + insights + recommendations from analytics dict."""
        kpis = analytics.get("kpis", {})
        meta = analytics.get("meta", {})

        if not self.enabled:
            return self._fallback_narrative(kpis, meta)

        system = (
            "You are a senior business analyst writing concise, data-driven weekly "
            "executive reports. Output strict JSON with keys: summary (string, 4-6 "
            "sentences), insights (array of 4-6 short bullet strings), "
            "recommendations (array of 3-5 short action items)."
        )
        user = (
            "Analytics JSON:\n"
            f"{json.dumps({'kpis': kpis, 'meta': meta, 'summary_stats': analytics.get('summary_stats', {})}, default=str)}\n\n"
            "Write the report content. Focus on revenue trends, growth, top categories, "
            "and risks. Be specific, cite numbers from the KPIs."
        )

        raw = self._chat(system, user, json_mode=True)
        try:
            data = json.loads(raw)
            return {
                "summary": data.get("summary", "").strip(),
                "insights": [str(x) for x in data.get("insights", [])],
                "recommendations": [str(x) for x in data.get("recommendations", [])],
            }
        except Exception:
            logger.warning("Failed to parse LLM JSON, using fallback. Raw: %s", raw[:200])
            return self._fallback_narrative(kpis, meta)

    def answer_question(self, question: str, context: Dict[str, Any]) -> str:
        """Chatbot: answer a question grounded in a report's analytics."""
        if not self.enabled:
            return self._fallback_answer(question, context)
        system = (
            "You are an analytics assistant. Answer the user's question using only "
            "the provided report context (KPIs, insights, recommendations). "
            "If the data does not contain the answer, say so. Keep replies concise."
        )
        user = (
            f"Report context:\n{json.dumps(context, default=str)[:6000]}\n\n"
            f"Question: {question}"
        )
        out = self._chat(system, user)
        return out.strip() or self._fallback_answer(question, context)

    # ---------------- fallbacks ----------------

    @staticmethod
    def _fallback_narrative(kpis: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        total_rev = kpis.get("total_revenue")
        growth = kpis.get("week_over_week_growth_pct")
        records = kpis.get("total_records", 0)
        cats = kpis.get("unique_categories")

        parts = [f"This weekly report analyzes {records:,} records."]
        if total_rev is not None:
            parts.append(f"Total revenue across the dataset is ${total_rev:,.2f}.")
        if growth is not None:
            direction = "growth" if growth >= 0 else "decline"
            parts.append(f"Week-over-week we observed a {abs(growth):.2f}% {direction}.")
        if cats:
            parts.append(f"Activity spans {cats} distinct segments.")
        summary = " ".join(parts)

        insights = []
        if total_rev is not None:
            insights.append(f"Revenue total of ${total_rev:,.2f} sets the baseline for upcoming targets.")
        if growth is not None:
            insights.append(
                f"WoW change of {growth:.2f}% indicates "
                + ("momentum" if growth > 0 else "softening demand") + "."
            )
        if "average_value" in kpis:
            insights.append(f"Average value per record is ${kpis['average_value']:,.2f}.")
        if cats:
            insights.append(f"Concentration across {cats} segments suggests diversification opportunities.")
        if not insights:
            insights = ["Data successfully ingested and cleaned for analysis."]

        recs = [
            "Double down on the top-performing segments identified in the charts.",
            "Investigate any week-over-week decline in revenue and run a root-cause analysis.",
            "Set automated alerts when KPIs deviate >10% from the trailing-4-week mean.",
        ]
        return {"summary": summary, "insights": insights, "recommendations": recs}

    @staticmethod
    def _fallback_answer(question: str, context: Dict[str, Any]) -> str:
        kpis = context.get("kpis", {})
        if "revenue" in question.lower() and "total_revenue" in kpis:
            return f"Total revenue is ${kpis['total_revenue']:,.2f}."
        if "growth" in question.lower() and "week_over_week_growth_pct" in kpis:
            return f"Week-over-week growth is {kpis['week_over_week_growth_pct']:.2f}%."
        return ("LLM is not configured. Set OPENAI_API_KEY in the environment to enable "
                "natural-language Q&A. Meanwhile, please refer to the KPIs and charts.")


# singleton
llm_service = LLMService()
