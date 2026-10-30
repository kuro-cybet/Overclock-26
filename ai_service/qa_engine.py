import logging
from typing import List, Optional
from ai_service.llama_client import llama_client
from ai_service.schemas import AnswerResponse

logger = logging.getLogger("ai_service.qa_engine")

PREDEFINED_FALLBACK = (
    "Sorry, I couldn't find reliable information about your query.\n\n"
    "Please try rephrasing your question or contact the concerned department for assistance."
)

QA_SYSTEM_PROMPT = """You are the official CampusOps University AI Assistant.
Answer the user's question concisely, professionally, and accurately using ONLY the provided verified context.

Guidelines:
1. Ground your answer strictly in the provided Context.
2. If the context contains the answer, summarize it clearly in 1 to 3 sentences suitable for WhatsApp messaging.
3. If source URLs are provided, mention the primary reference link.
4. If the provided Context does NOT contain sufficient, reliable information to answer the question, do NOT invent or speculate. Instead, reply EXACTLY with the token: [FALLBACK_TRIGGER]
"""

class QAEngine:
    async def answer(
        self,
        query: str,
        context: Optional[str] = None,
        source_urls: Optional[List[str]] = None,
        sender_role: str = "student"
    ) -> AnswerResponse:
        clean_context = (context or "").strip()
        source_refs = source_urls or []

        # If no context was provided from CampusOps DB or web search, return fallback immediately
        if not clean_context:
            return AnswerResponse(
                answer=PREDEFINED_FALLBACK,
                grounded=False,
                source_refs=[],
                confidence=0.0,
                fallback_required=True
            )

        messages = [
            {"role": "system", "content": QA_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"User Role: {sender_role}\n"
                    f"Question: \"{query}\"\n\n"
                    f"Verified Context:\n{clean_context}\n\n"
                    f"Source References:\n{', '.join(source_refs) if source_refs else 'Internal Knowledgebase'}"
                )
            }
        ]

        try:
            raw_output = await llama_client.chat_completion(
                messages=messages,
                temperature=0.2,
                max_tokens=400
            )
            answer_text = raw_output.strip()

            if "[FALLBACK_TRIGGER]" in answer_text or not answer_text:
                return AnswerResponse(
                    answer=PREDEFINED_FALLBACK,
                    grounded=False,
                    source_refs=[],
                    confidence=0.0,
                    fallback_required=True
                )

            # Append source link if available and not already in answer
            if source_refs and not any(ref in answer_text for ref in source_refs):
                answer_text += f"\n\nSource: {source_refs[0]}"

            return AnswerResponse(
                answer=answer_text,
                grounded=True,
                source_refs=source_refs,
                confidence=0.92,
                fallback_required=False
            )
        except Exception as e:
            logger.warning(f"Llama inference failed during Q&A: {e}")
            # If context was high-quality institutional info, return concise extract as backup
            if len(clean_context) > 20 and ("timing" in clean_context.lower() or "procedure" in clean_context.lower()):
                summary = clean_context.split("\n")[0]
                if source_refs:
                    summary += f"\n\nSource: {source_refs[0]}"
                return AnswerResponse(
                    answer=summary,
                    grounded=True,
                    source_refs=source_refs,
                    confidence=0.85,
                    fallback_required=False
                )

            return AnswerResponse(
                answer=PREDEFINED_FALLBACK,
                grounded=False,
                source_refs=[],
                confidence=0.0,
                fallback_required=True
            )

qa_engine = QAEngine()

