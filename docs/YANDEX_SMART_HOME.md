# Яндекс Умный дом (Yaha Cloud)

Интеграция MagicAir создаёт стандартный объект `fan`, поэтому Яндекс Умный дом
автоматически поддерживает включение, выключение и шесть скоростей Tion
4S. Ниже приведена расширенная настройка, которая объединяет в одном устройстве
Яндекса:

- включение и выключение бризера;
- скорости 1–6;
- ручной и автоматический режимы;
- нагрев и целевую температуру;
- приток наружного воздуха и рециркуляцию.

Настройка рассчитана на актуальную интеграцию
[Yandex Smart Home](https://github.com/dext0r/yandex_smart_home) с облачным
подключением Yaha Cloud.

## 1. Узнайте идентификаторы объектов

Откройте **Настройки → Инструменты разработчика → Состояния** и найдите объекты
Tion 4S. Понадобятся:

| Назначение | Пример идентификатора |
| --- | --- |
| Основное устройство | `fan.tion_breezer_4s` |
| Нагрев | `switch.tion_breezer_4s_heater` |
| Целевая температура | `number.tion_breezer_4s_target_temperature` |
| Рециркуляция | `switch.tion_breezer_4s_recirculation` |

Названия в вашей системе могут отличаться. Используйте реальные
идентификаторы, а не примеры из таблицы.

## 2. Добавьте расширенную конфигурацию

Добавьте этот блок в `configuration.yaml` и замените все четыре
идентификатора на свои:

```yaml
yandex_smart_home:
  entity_config:
    fan.tion_breezer_4s:
      name: Бризер
      type: ventilation.fan
      modes:
        fan_speed:
          quiet: '16%'
          low: '33%'
          medium: '50%'
          normal: '66%'
          high: '83%'
          turbo: '100%'
        program:
          normal: 'normal'
          auto: 'auto'
        ventilation_mode:
          supply_air: 'off'
          fan_only: 'on'
      custom_toggles:
        keep_warm:
          state_entity_id: switch.tion_breezer_4s_heater
          turn_on:
            action: switch.turn_on
            entity_id: switch.tion_breezer_4s_heater
          turn_off:
            action: switch.turn_off
            entity_id: switch.tion_breezer_4s_heater
      custom_ranges:
        temperature:
          state_entity_id: number.tion_breezer_4s_target_temperature
          set_value:
            action: number.set_value
            entity_id: number.tion_breezer_4s_target_temperature
            data:
              value: '{{ value }}'
          range:
            min: 0
            max: 30
            precision: 1
      custom_modes:
        ventilation_mode:
          state_entity_id: switch.tion_breezer_4s_recirculation
          set_mode:
            action: 'switch.turn_{{ mode }}'
            entity_id: switch.tion_breezer_4s_recirculation
```

Если `yandex_smart_home:` уже существует, не добавляйте второй раздел с таким
же именем. Перенесите только содержимое `entity_config` в существующий раздел.

## 3. Выберите объект для передачи

В настройках интеграции **Яндекс Умный дом → Объекты для передачи в УДЯ**
выберите основной объект `fan.tion_breezer_4s`.

Вспомогательные `switch`, `number` и `select` передавать отдельно не требуется:
они уже используются как возможности основного устройства. Это предотвращает
появление нескольких карточек одного бризера в приложении Яндекса.

## 4. Примените изменения

1. Проверьте конфигурацию Home Assistant.
2. Откройте **Настройки → Инструменты разработчика → YAML** и выполните
   **Перезагрузку конфигурации YAML** для Яндекс Умного дома. Если такого пункта
   нет, перезапустите Home Assistant.
3. В приложении **Дом с Алисой** нажмите **+ → Устройство умного дома → Yaha
   Cloud → Обновить список устройств**.

После синхронизации Алиса должна понимать команды наподобие:

- «Включи бризер»;
- «Установи тихую скорость на бризере»;
- «Включи автоматический режим на бризере»;
- «Включи поддержание тепла на бризере»;
- «Установи температуру бризера 22 градуса».

Названия режимов скорости задаются словарём Яндекса и не равны номерам 1–6.
Соответствие приведено в YAML-блоке выше.
