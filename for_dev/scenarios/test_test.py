import vedro

from for_dev.contexts.mocks.debug_mock import mocked_debug


class Scenario(vedro.Scenario):
    subject = "test_subject"

    def given_test_mock(self):
        debug = mocked_debug()

    def when_test_action(self):
        ...

    def then_test_result(self):
        assert True
