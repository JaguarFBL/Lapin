import os
import json
import re
import logging
from google import genai
from google.genai import types as genai_types

logger = logging.getLogger("ai")


class AIClient:
    """Client IA basé sur Google Gemini (nouveau SDK google.genai)."""

    def __init__(self, model: str = "gemini-3-flash-preview"):
        api_key = os.environ.get("GEMINI_API_KEY")
        logger.info("Initialisation AIClient, GEMINI_API_KEY présente: %s", bool(api_key))
        if not api_key:
            err = ("Variable d'environnement GEMINI_API_KEY manquante. "
                   "Définis-la avec : $env:GEMINI_API_KEY = 'ta_cle'")
            logger.error(err)
            raise RuntimeError(err)
        self.client = genai.Client(api_key=api_key)
        self.model = model
        logger.info("AIClient prêt, modèle: %s", model)

    async def generate(self, prompt: str, system_instruction: str = "", use_web_search: bool = False) -> str:
        logger.info("=== APPEL GEMINI ===")
        logger.info("Modèle: %s | WebSearch: %s", self.model, use_web_search)
        logger.info("System prompt: %s", system_instruction[:200] if system_instruction else "(aucun)")
        logger.info("Prompt (%d caractères): %s...", len(prompt), prompt[:300])
        try:
            kwargs = dict(model=self.model, contents=prompt)

            config_kwargs = {}
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction
            if use_web_search:
                config_kwargs["tools"] = [
                    genai_types.Tool(google_search=genai_types.GoogleSearch())
                ]
            if config_kwargs:
                kwargs["config"] = genai_types.GenerateContentConfig(**config_kwargs)

            response = await self.client.aio.models.generate_content(**kwargs)

            if response.candidates:
                grounding = response.candidates[0].grounding_metadata
                if grounding and grounding.grounding_chunks:
                    logger.info("Grounding — %d sources web utilisées:", len(grounding.grounding_chunks))
                    for chunk in grounding.grounding_chunks:
                        if chunk.web:
                            logger.info("  · %s", chunk.web.uri)

            logger.info("Réponse Gemini reçue (%d caractères)", len(response.text))
            logger.info("Réponse texte: %s", response.text[:500])
            return response.text
        except Exception as exc:
            logger.error("ERREUR Gemini: %s", exc, exc_info=True)
            raise

    async def generate_json(
        self, prompt: str, system_instruction: str = "", use_web_search: bool = False
    ) -> dict:
        logger.info("generate_json (web_search=%s): envoi à Gemini...", use_web_search)
        texte = await self.generate(prompt, system_instruction, use_web_search=use_web_search)
        logger.info("Parsing JSON depuis la réponse...")
        try:
            data = self._extraire_json(texte)
            logger.info("JSON parsé avec succès: %s", json.dumps(data, ensure_ascii=False)[:300])
            return data
        except json.JSONDecodeError as exc:
            logger.error("Erreur parsing JSON: %s", exc)
            logger.error("Texte reçu: %s", texte)
            raise

    @staticmethod
    def _extraire_json(texte: str) -> dict:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", texte)
        if match:
            texte = match.group(1).strip()

        texte = texte.strip()
        if texte.startswith("```"):
            texte = texte.strip("`").strip()
        if texte.lower().startswith("json"):
            texte = texte[4:].strip()

        return json.loads(texte)
