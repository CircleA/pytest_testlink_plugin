# Как пользоваться ?
Плагин дает возможность репортить результаты тестов в TestLink, 
с поддержкой шагов и аттачей в виде скринов браузера в момент падения теста.

Плагин добавляет к **_pytest_** следующие параметры:
```
--testlink  <-- флаг в виде "true" или "false", отвечающий за использование TestLink
--testlink-url <-- url до api-endpoint TestLink
--testlink-secret-key <-- TestLink api secret key
--testlink-project <-- Имя проекта в TestLink для которого будут запущены тесты
--testlink-test-plan <-- Имя тест-плана в TestLink для которого будут запущены тесты 
                         (тест-план должен находится в проекте который 
                          задается с помощью --testlink-project)
--testlink-build-name <-- Название тестового прогона который создаст в плагин, 
                          и в который будут репортиться результаты тестов
```

Для каждого теста, результаты которого вы хотите видеть в TestLink необходимо вешать тестовую марку
`@pytest.mark.testlink("centr-123")`, где `centr-123 - id теста из TestLink`

Поддержка шагов доступана через `with pytest.testlink.step`

`with pytest.testlink.step` Имеет автоинкремент шага (соответсвенно не нужно писать номер шага)

_Пример теста с использованием плагина:_
```
@pytest.mark.testlink("centr-977")
def test_verify_centering_region_by_0_0(self, page_object, open_regions_popup, region_data_0_0):
    with pytest.testlink.step:
        regions_popup = open_regions_popup()
        regions_popup.fill_search_name_input(region_data_0_0['name'])
        regions_popup.wait_regions_data_load()
        region = regions_popup.get_table_row_items()[0]

    with pytest.testlink.step:
        region.show_on_map()
        footer = page_object.footer
        footer.check_coordinates(
            latitude=region_data_0_0['center_point_latitude'],
            longitude=region_data_0_0['center_point_longitude']
        )
```

Для поддержки прикрепления скриншотов браузера в момент падения тестов, 
необходимо в глобальный conftest.py либо в conftest.py, который относится только к ui-тестам добавить следующую фикстуру
```
@pytest.yield_fixture(scope='function', autouse=True)
def screener_of_fail(request):
    yield

    # здесь нужно делать скриншот и класть его локально
    setattr(request.node, 'fail_screenshot', screen_path)  # screen_path - путь до скрина
```