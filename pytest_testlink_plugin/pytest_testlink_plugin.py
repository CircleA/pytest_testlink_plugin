import pytest

from pytest_testlink_plugin.testlink_helper import TestLinkHelper


def pytest_addoption(parser):
    group = parser.getgroup("pytest_testlink_plugin")
    group.addoption('--testlink', dest='--testlink', action='store')
    group.addoption('--testlink-url', dest='--testlink-url', action='store')
    group.addoption('--testlink-secret-key', dest='--testlink-secret-key', action='store')
    group.addoption('--testlink-project', dest='--testlink-project', action='store')
    group.addoption('--testlink-test-plan', dest='--testlink-test-plan', action='store')
    group.addoption('--testlink-build-name', dest='--testlink-build-name', action='store')


def pytest_configure(config):
    config.addinivalue_line("markers", "testlink: test integrated with pytest_testlink_plugin")
    tl_helper = TestLinkHelper(
        testlink_url=config.getoption('--testlink-url'),
        testlink_secret_key=config.getoption('--testlink-secret-key'),
        project_name=config.getoption('--testlink-project'),
        test_plan=config.getoption('--testlink-test-plan'),
        build_name=config.getoption('--testlink-build-name')
    )
    setattr(pytest, 'testlink', tl_helper)
    if is_use_testlink(config) and not hasattr(config, 'workerinput'):
        tl_helper.create_tests_run()


def is_use_testlink(config):
    return config.getoption('--testlink') == 'true'


def pytest_report_header(config):
    if is_use_testlink(config):
        testlink_url = config.getoption('--testlink-url').replace('/testlink/lib/api/xmlrpc/v1/xmlrpc.php', '')
        return "Отчет будет доступен в TestLink ({0}), проект - {1}, тест-план - {2}, прогон - '{3}'".format(
            testlink_url, config.getoption('--testlink-project'), config.getoption('--testlink-test-plan'),
            config.getoption('--testlink-build-name'))
    else:
        return "Запуск тестов без интеграции с TestLink."


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()
    setattr(rep, "testlink_test_case_id", get_test_link_id(item))
    setattr(rep, "testlink_fail_screenshot", getattr(item, 'fail_screenshot', None))
    setattr(rep, "testlink_test_case_steps", getattr(item, 'steps', None))


def get_test_link_id(item) -> str:
    """
    Вытаскивает значение марки testlink из ноды
    """
    test_link_test_case_id = "unknown"
    test_link_marks = list(filter(lambda x: x.name == "testlink", item.own_markers))
    try:
        test_link_test_case_id = test_link_marks[0].args[0]
    except IndexError:
        pass
    return test_link_test_case_id


def pytest_report_teststatus(report, config):
    if is_use_testlink(config):
        # Passed
        if not report.failed and report.when == 'call':
            pytest.testlink.report_result(
                report.testlink_test_case_id, '', 'p', report.testlink_test_case_steps)

        else:
            # Skipped and failed on preconditions
            if report.when == 'setup' and report.failed or report.when == 'setup' and report.skipped:
                pytest.testlink.report_result(
                    report.testlink_test_case_id, report.longreprtext, 'b', report.testlink_test_case_steps)

            # Failed
            elif report.when == 'call' and report.failed:
                pytest.testlink.report_result(
                    report.testlink_test_case_id, report.longreprtext, 'f', report.testlink_test_case_steps)

            # Failed on teardown
            elif report.when == 'teardown' and report.failed:
                pytest.testlink.report_result(
                    report.testlink_test_case_id, report.longreprtext, 'f', report.testlink_test_case_steps)


@pytest.fixture(autouse=True)
def add_request(request):
    setattr(pytest.testlink, "request", request.node)
