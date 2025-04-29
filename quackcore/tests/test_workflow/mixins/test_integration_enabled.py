# quackcore/tests/test_workflow/mixins/test_integration_enabled.py

import quackcore.integrations.core as core_int
from quackcore.integrations.core.base import BaseIntegrationService
from quackcore.workflow.mixins.integration_enabled import IntegrationEnabledMixin


class DummyService(BaseIntegrationService):
    def __init__(self):
        self.initialized = False

    def initialize(self):
        self.initialized = True


class Host(IntegrationEnabledMixin[DummyService]):
    pass


def test_resolve_none(monkeypatch):
    monkeypatch.setattr(core_int, "get_integration_service", lambda t: None)
    h = Host()
    assert h.resolve_integration(DummyService) is None
    assert h.get_integration_service() is None


def test_resolve_and_initialize(monkeypatch):
    svc = DummyService()
    monkeypatch.setattr(core_int, "get_integration_service", lambda t: svc)
    h = Host()
    ret = h.resolve_integration(DummyService)
    assert ret is svc
    assert svc.initialized is True
    # subsequent call returns same
    assert h.get_integration_service() is svc
