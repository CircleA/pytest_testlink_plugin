import os
from contextlib import contextmanager
from datetime import datetime

from testlink.testlinkapi import TestlinkAPIClient
from testlink.testlinkhelper import TestLinkHelper as TLHelper


class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class TestLinkHelper(metaclass=Singleton):

    def __init__(self, **kwargs):
        self.__project_name = kwargs.get('project_name')
        self.__test_plan_name = kwargs.get('test_plan')
        self.__build_id = None
        self.__build_name = kwargs.get('build_name')
        self.__project_id = None
        self.__test_plan_id = None
        self.__test_link_api_url = kwargs.get('testlink_url')
        self.__test_link_api_secret_key = kwargs.get('testlink_secret_key')
        self.api = TLHelper(server_url=self.__test_link_api_url,
                            devkey=self.__test_link_api_secret_key).connect(TestlinkAPIClient)
        self.request = None

    def __check_connect(self):
        if not self.api.checkDevKey():
            raise ConnectionError("Неправильный api_secret_key для TestLink")

    def __create_product_version_to_execute(self, test_plan_id: str, notes=None) -> int:
        """
        Создает сборку в TestLink по параметрам
        """
        date_to_product = datetime.utcnow().strftime("%Y-%m-%d")
        build_id = self.api.createBuild(testplanid=test_plan_id, buildname=self.__build_name,
                                        buildnotes=notes, releasedate=date_to_product)[0]['id']
        return build_id

    def create_tests_run(self):
        """
        Создает тестовый прогон
        """
        self.__check_connect()
        self.__test_plan_id = self.api.getTestPlanByName(self.__project_name, self.__test_plan_name)[0]['id']
        self.__build_id = self.__create_product_version_to_execute(self.__test_plan_id)

    def report_result(self, test_case_id: str, notes: str, status: str, steps: list, duration: float = 0) -> int:
        """
        Проставляет результат выполнения тест-кейса в TestLink
        """
        try:
            self.api.reportTCResult(
                testcaseexternalid=test_case_id,
                testplanid=self.__test_plan_id,
                status=status,
                steps=steps,
                buildid=self.__build_id,
                platformname=None,
                notes=notes,
                execduration=duration,
                overwrite=False
            )
        except Exception as e:
            print(str(e))
            return -1

    def upload_attachments(self, attachments_temp_dir: str):
        results_ids = \
            list(map(lambda x: x[0]['full_external_id'],
                     self.api.getTestCasesForTestPlan(testplanid=self.__test_plan_id).values()))
        for test_case_id in results_ids:
            screenshot_path = os.path.join(attachments_temp_dir, '{}.png'.format(test_case_id))
            if os.path.exists(screenshot_path):
                try:
                    last_execution_of_test_case = self.api.getLastExecutionResult(
                        testcaseexternalid=test_case_id,
                        testplanid=self.__test_plan_id,
                        buildname=self.__build_name)[0]['id']
                    self.api.uploadExecutionAttachment(
                        executionid=last_execution_of_test_case, title='Test fail',
                        attachmentfile=screenshot_path)
                except Exception as e:
                    print(e)
                    pass

    def get_latest_execution_results(self):
        results_statuses = \
            list(map(lambda x: x[0]['exec_status'],
                     self.api.getTestCasesForTestPlan(testplanid=self.__test_plan_id).values()))
        results = {
            "passed": len(list(filter(lambda x: x == 'p', results_statuses))),
            "failed": len(list(filter(lambda x: x == 'f', results_statuses))),
            "blocked": len(list(filter(lambda x: x == 'b', results_statuses))),
            "not_run": len(list(filter(lambda x: x == 'n', results_statuses))),
            "total": len(results_statuses)
        }
        return results

    @property
    def step(self):

        @contextmanager
        def _step(request):
            if not hasattr(request, 'steps'):
                setattr(request, 'steps', [])
                current_step_index = 1
            else:
                current_step_index = len(getattr(self.request, 'steps')) + 1

            current_step = {
                "step_number": current_step_index,
                "result": None,
                "notes": None
            }

            try:

                yield

                current_step['result'] = 'p'

            except Exception as error:
                if isinstance(error, AssertionError):
                    error = str(error).split('\nassert')[0]
                else:
                    error = str(error)
                current_step['result'] = 'f'
                current_step['notes'] = error
                raise

            finally:
                request.steps.append(current_step)

        return _step(self.request)
