from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from .errors import PredictionConfigurationError


class EvidenceProviderRegistry:
    def __init__(self, providers: Iterable[object] = ()) -> None:
        self._providers: Dict[str, object] = {}
        for provider in providers:
            self.register(provider)

    def register(self, provider: object) -> None:
        provider_id = str(getattr(provider, "provider_id", "")).strip()
        version = str(getattr(provider, "version", "")).strip()
        if not provider_id or not version or not callable(getattr(provider, "evaluate", None)):
            raise PredictionConfigurationError(
                "Evidence providers require provider_id, version, and evaluate()"
            )
        if provider_id in self._providers:
            raise PredictionConfigurationError(f"Duplicate evidence provider: {provider_id}")
        self._providers[provider_id] = provider

    def resolve(
        self,
        provider_ids: Iterable[str],
        *,
        profile_key: Optional[str] = None,
        expected_versions: Optional[Dict[str, str]] = None,
    ) -> List[object]:
        requested = tuple(provider_ids)
        requested_set = set(requested)
        resolved: List[object] = []
        for provider_id in requested:
            provider = self._providers.get(provider_id)
            if provider is None:
                raise PredictionConfigurationError(
                    f"Prediction profile references unknown provider: {provider_id}"
                )
            expected = (expected_versions or {}).get(provider_id)
            actual = str(getattr(provider, "version"))
            if expected and actual != expected:
                raise PredictionConfigurationError(
                    f"Provider {provider_id} version mismatch: profile requires "
                    f"{expected}, registry has {actual}"
                )
            supported = tuple(getattr(provider, "supported_profiles", ()) or ())
            if profile_key and supported and profile_key not in supported:
                raise PredictionConfigurationError(
                    f"Provider {provider_id}@{actual} does not support profile {profile_key}"
                )
            missing_dependencies = set(
                getattr(provider, "required_providers", ()) or ()
            ).difference(requested_set)
            if missing_dependencies:
                raise PredictionConfigurationError(
                    f"Provider {provider_id} requires missing providers: "
                    f"{', '.join(sorted(missing_dependencies))}"
                )
            resolved.append(provider)
        return resolved

    def versions(self, provider_ids: Iterable[str]) -> Dict[str, str]:
        return {
            provider_id: str(getattr(provider, "version"))
            for provider_id, provider in (
                (provider_id, self._providers.get(provider_id))
                for provider_id in provider_ids
            )
            if provider is not None
        }
