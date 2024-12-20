from models import TrainType

# Блоки для проверки каждого типа состава
TRAIN_BLOCKS = {
    # Электрички
    TrainType.EP2D: [
        "Тормозное оборудование",
        "Ходовая часть",
        "Электрооборудование",
        "Система управления",
        "Двери и окна",
        "Салон",
        "Кабина машиниста"
    ],
    TrainType.EP3D: [
        "Тормозное оборудование",
        "Ходовая часть",
        "Электрооборудование",
        "Система управления",
        "Двери и окна",
        "Салон",
        "Кабина машиниста",
        "Система кондиционирования"
    ],
    # Рельсовые автобусы
    TrainType.RA1: [
        "Двигатель",
        "Тормозное оборудование",
        "Ходовая часть",
        "Трансмиссия",
        "Двери и окна",
        "Салон",
        "Кабина машиниста"
    ],
    TrainType.RA2: [
        "Двигатель",
        "Тормозное оборудование",
        "Ходовая часть",
        "Трансмиссия",
        "Двери и окна",
        "Салон",
        "Кабина машиниста",
        "Система управления"
    ],
    TrainType.RA3: [
        "Двигатель",
        "Тормозное оборудование",
        "Ходовая часть",
        "Трансмиссия",
        "Двери и окна",
        "Салон",
        "Кабина машиниста",
        "Система управления",
        "Система кондиционирования"
    ]
}

# Описания для каждого блока
BLOCK_DESCRIPTIONS = {
    "Тормозное оборудование": "Проверка работоспособности тормозной системы, состояния тормозных колодок и дисков",
    "Ходовая часть": "Проверка состояния колесных пар, букс, рессор и других элементов ходовой части",
    "Электрооборудование": "Проверка электрических систем, проводки, освещения и электронных компонентов",
    "Система управления": "Проверка пульта управления, систем безопасности и контроля",
    "Двери и окна": "Проверка механизмов открывания/закрывания дверей, уплотнителей, стеклопакетов",
    "Салон": "Проверка состояния сидений, поручней, напольного покрытия, внутренней отделки",
    "Кабина машиниста": "Проверка оборудования кабины, приборов, системы связи",
    "Система кондиционирования": "Проверка работы климатической системы, вентиляции",
    "Двигатель": "Проверка состояния двигателя, топливной системы, систем охлаждения и смазки",
    "Трансмиссия": "Проверка состояния коробки передач, карданной передачи, редукторов"
}

# Критерии проверки для каждого блока
BLOCK_CHECKLIST = {
    "Тормозное оборудование": [
        "Проверить толщину тормозных колодок",
        "Проверить работу компрессора",
        "Проверить герметичность пневмосистемы",
        "Проверить работу стояночного тормоза"
    ],
    "Ходовая часть": [
        "Проверить состояние колесных пар",
        "Проверить состояние букс",
        "Проверить состояние рессор",
        "Проверить состояние шкворневых узлов"
    ],
    "Электрооборудование": [
        "Проверить работу освещения",
        "Проверить состояние проводки",
        "Проверить работу электрических систем",
        "Проверить состояние аккумуляторных батарей"
    ],
    "Система управления": [
        "Проверить работу пульта управления",
        "Проверить работу систем безопасности",
        "Проверить работу информационных систем",
        "Проверить работу радиосвязи"
    ],
    "Двери и окна": [
        "Проверить работу механизмов дверей",
        "Проверить состояние уплотнителей",
        "Проверить состояние стеклопакетов",
        "Проверить работу системы блокировки дверей"
    ],
    "Салон": [
        "Проверить состояние сидений",
        "Проверить состояние поручней",
        "Проверить состояние напольного покрытия",
        "Проверить состояние внутренней отделки"
    ],
    "Кабина машиниста": [
        "Проверить состояние кресла машиниста",
        "Проверить работу контрольных приборов",
        "Проверить работу системы связи",
        "Проверить состояние лобового стекла"
    ],
    "Система кондиционирования": [
        "Проверить работу климатической установки",
        "Проверить состояние фильтров",
        "Проверить работу вентиляции",
        "Проверить температурный режим"
    ],
    "Двигатель": [
        "Проверить уровень масла",
        "Проверить состояние фильтров",
        "Проверить работу системы охлаждения",
        "Проверить состояние приводных ремней"
    ],
    "Трансмиссия": [
        "Проверить уровень масла в КПП",
        "Проверить состояние карданной передачи",
        "Проверить состояние редукторов",
        "Проверить работу механизма переключения передач"
    ]
}
