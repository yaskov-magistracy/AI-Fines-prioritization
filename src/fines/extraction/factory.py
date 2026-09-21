from fines.config import Settings
from fines.extraction.base import Extractor
from fines.extraction.rule_based import RuleBasedExtractor


def get_extractor(settings: Settings) -> Extractor:
    if settings.extractor_backend == "llm":
        from fines.extraction.llm import LLMExtractor

        return LLMExtractor(settings.llm_base_url, settings.llm_api_key, settings.llm_model)
    return RuleBasedExtractor()
