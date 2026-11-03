import re

PUA = re.compile("[\ue000-\uf8ff]")

PAIRS = [
    ("Select save location.\n", "Выберите место сохранения.\n"),
    ("Select load location.\n", "Выберите место загрузки.\n"),
    ("No memory card (PS2) found.\nContinue with the game?\n", "Карта памяти (PS2) не найдена.\nПродолжить игру?\n"),
    ("Insufficient free space on memory card\n(PS2). At least %dKB of free space is\nrequired to save data.\n", "Недостаточно места на карте памяти\n(PS2). Для сохранения нужно не менее\n%dКБ свободного места.\n"),
    ("Create new save data on\nmemory card (PS2)?\nYes or No\n", "Создать новое сохранение на\nкарте памяти (PS2)?\nДа или Нет\n"),
    ("Are you sure you wish to overwrite this\nsave data?\nYes or No\n", "Вы уверены, что хотите перезаписать\nэто сохранение?\nДа или Нет\n"),
    ("Memory card (PS2) is not formatted.\nFormat memory card (PS2) and save?\n", "Карта памяти (PS2) не отформатирована.\nОтформатировать карту (PS2) и сохранить?\n"),
    ("Saving data.\nDo not remove memory card (PS2),\ncontroller, or reset/switch off the console.\n", "Идёт сохранение.\nНе извлекайте карту памяти (PS2),\nконтроллер и не выключайте консоль.\n"),
    ("Formatting memory card (PS2).\nDo not remove memory card (PS2),\ncontroller, or reset/switch off the console.\n", "Форматирование карты памяти (PS2).\nНе извлекайте карту памяти (PS2),\nконтроллер и не выключайте консоль.\n"),
    ("Save Successful\n", "Сохранение выполнено\n"),
    ("Save failed! Check memory card (PS2)\nand please try again.\n", "Ошибка сохранения! Проверьте карту\nпамяти (PS2) и попробуйте снова.\n"),
    ("Format failed! Please check memory\ncard (PS2) and try again.\n", "Ошибка форматирования! Проверьте карту\nпамяти (PS2) и попробуйте снова.\n"),
    ("No data present on memory card (PS2).\n", "На карте памяти (PS2) нет данных.\n"),
    ("No data present on memory card (PS2).\nContinue with the game?\n", "На карте памяти (PS2) нет данных.\nПродолжить игру?\n"),
    ("No data present on memory card (PS2).\nContinue without saving?\n", "На карте памяти (PS2) нет данных.\nПродолжить без сохранения?\n"),
    ("Load failed! Check memory card (PS2)\nand please try again.\n", "Ошибка загрузки! Проверьте карту\nпамяти (PS2) и попробуйте снова.\n"),
    ("Insufficient free space on memory card (PS2).\nAt least %dKB of free space is required to\nsave data. Contiune with the game?\n", "Недостаточно места на карте памяти (PS2).\nДля сохранения нужно не менее %dКБ.\nПродолжить игру?\n"),
    ("No memory card (PS2) found. At least %dKB\nof free space is required to save data.\nContinue with the game?\n", "Карта памяти (PS2) не найдена. Для сохранения\nнужно не менее %dКБ свободного места.\nПродолжить игру?\n"),
    ("Memory card (PS2) check failed! At least\n%dKB of free space is required to save data.\nContinue with the game?\n", "Ошибка проверки карты памяти (PS2)! Для\nсохранения нужно не менее %dКБ.\nПродолжить игру?\n"),
    ("Data on memory card (PS2) is broken.\n", "Данные на карте памяти (PS2) повреждены.\n"),
    ("No memory card (PS2) found. Insert\nthe memory card (PS2) that was used\nto load the saved data.\n", "Карта памяти (PS2) не найдена. Вставьте\nкарту памяти (PS2), с которой\nзагружалось сохранение.\n"),
    ("No loaded data found. Insert the\nmemory card (PS2) that was used\nto load the saved data.\n", "Загруженные данные не найдены. Вставьте\nкарту памяти (PS2), с которой\nзагружалось сохранение.\n"),
    ("Load failed! Insert the memory card\n(PS2) that was used to load the saved\ndata.\n", "Ошибка загрузки! Вставьте карту памяти\n(PS2), с которой загружалось\nсохранение.\n"),
    ("Saved data is broken. Insert the\nmemory card (PS2) that was used\nto load the saved data.\n", "Сохранение повреждено. Вставьте\nкарту памяти (PS2), с которой\nзагружалось сохранение.\n"),
    ("Memory card (PS2) was removed during\nsaving. Re-insert the memory card (PS2).\nCancel overwriting?\n", "Карта памяти (PS2) извлечена во время\nсохранения. Вставьте её снова.\nОтменить перезапись?\n"),
    ("Saved data that was loaded is not found.\nOverwrite the present saved data on\nmemory card (PS2)?\n", "Загруженное сохранение не найдено.\nПерезаписать текущее сохранение на\nкарте памяти (PS2)?\n"),
    ("Link to \"METAL GEAR ACID\" for PSP\u2122\n(PlayStation\u00aePortable).\n", "Связь с \"METAL GEAR ACID\" для PSP™\n(PlayStation®Portable).\n"),
    ("Select \"MGS3 LINK\" in \"METAL GEAR ACID\"\nfor PSP\u2122 (PlayStation\u00aePortable), and\nconnect USB cable to USB connector of\nPlayStation\u00ae2. (Refer to \"METAL GEAR ACID\"\nsoftware manual for details.)\n", "Выберите \"MGS3 LINK\" в \"METAL GEAR ACID\"\nдля PSP™ (PlayStation®Portable) и\nподключите USB-кабель к USB-разъёму\nPlayStation®2. (Подробнее в руководстве\n\"METAL GEAR ACID\".)\n"),
    ("Could not confirm connection. Remove USB cable\nfrom USB connector and redo the process.\n", "Не удалось подтвердить связь. Отключите\nUSB-кабель и повторите попытку.\n"),
    ("Incorrect game disc. Redo the process.\n", "Неверный игровой диск. Повторите попытку.\n"),
    ("You can use obtained special item by starting\ngame without turning off console or resetting game.\n", "Полученный особый предмет можно использовать,\nначав игру без выключения или сброса консоли.\n"),
    ("Monkey Shaker: Special gun\nthat knocks out monkeys.\nPress \ue082 button to aim, release\nto fire. Equipping it puts you\nin a monkey-catching mood.\n", "Монкишейкер: особое оружие,\nоглушающее обезьян.\nЗажмите кнопку {0}, чтобы целиться,\nотпустите, чтобы выстрелить.\nПробуждает охотничий азарт.\n"),
    ("Monkey Mask\nA mask that mimics a monkey.\n", "Маска обезьяны\nМаска, имитирующая обезьяну.\n"),
    ("Camouflage\nChange clothes and blend in\nwith the surroundings. Open\nthe window and press the \ue081\nbutton to change camouflage.\n", "Камуфляж\nСмените одежду, чтобы слиться\nс окружением. Откройте\nокно и нажмите кнопку {0},\nчтобы сменить камуфляж.\n"),
    ("Map\nArrows are allies, X's are\nitems. The red and blue\ncircles mark each team's goal.\n", "Карта\nСтрелки - союзники, крестики -\nпредметы. Красный и синий\nкруги - цели команд.\n"),
    ("Kerotan\nThe target item in Capture\nMissions. Open the window\nand press the \ue080 button to\ndrop.\n", "Керотан\nЦелевой предмет в миссиях\nзахвата. Откройте окно\nи нажмите кнопку {0},\nчтобы бросить.\n"),
    ("Ga-ko\nThe target item in Rescue\nMissions. Open the window\nand press the \ue080 button to\ndrop.\n", "Гако\nЦелевой предмет в миссиях\nспасения. Откройте окно\nи нажмите кнопку {0},\nчтобы бросить.\n"),
    ("Microfilm\nThe target item in Sneaking\nMissions. Open the window\nand press the \ue080 button to\ndrop.\n", "Микроплёнка\nЦелевой предмет в миссиях\nпроникновения. Откройте окно\nи нажмите кнопку {0},\nчтобы бросить.\n"),
    ("Monitor\nDisplays video from previously\ninstalled security cameras.\nPress the \ue084 and \ue087 buttons\nto switch channels.\n", "Монитор\nПоказывает изображение с\nустановленных камер наблюдения.\nКнопки {0} и {1}\nпереключают каналы.\n"),
    ("Retrieve Camouflage list from memory card (PS2)\nin MEMORY CARD slot 1. Press START button.\n", "Получить список камуфляжа с карты памяти (PS2)\nв слоте 1. Нажмите кнопку START.\n"),
    ("Reading Camouflage data from memory\ncard (PS2) in MEMORY CARD slot 1.\n", "Чтение данных камуфляжа с карты\nпамяти (PS2) в слоте 1.\n"),
    ("No Camouflage data present on memory\ncard (PS2) in MEMORY CARD slot 1.\n", "На карте памяти (PS2) в слоте 1\nнет данных камуфляжа.\n"),
    ("Loading Camouflage data from\nmemory card (PS2).\n", "Загрузка данных камуфляжа с\nкарты памяти (PS2).\n"),
    ("Error occurred loading Camouflage data from\nmemory card (PS2).\n", "Ошибка загрузки данных камуфляжа с\nкарты памяти (PS2).\n"),
    ("Loading Camouflage data from memory card\n(PS2) successfully completed.\n", "Данные камуфляжа успешно загружены\nс карты памяти (PS2).\n"),
    ("Camouflage data on memory card (PS2)\nis broken.\n", "Данные камуфляжа на карте памяти (PS2)\nповреждены.\n"),
    ("No Camouflage data present\non memory card (PS2).\n", "Нет данных камуфляжа\nна карте памяти (PS2).\n"),
    ("Turn the Dolby Pro Logic II ON / OFF.\n", "Включить или выключить Dolby Pro Logic II.\n"),
    ("Select camouflage data to save to\nmemory card (PS2).\n", "Выберите данные камуфляжа для\nсохранения на карту памяти (PS2).\n"),
    ("Save this camouflage data to memory\ncard (PS2)?\n", "Сохранить эти данные камуфляжа на\nкарту памяти (PS2)?\n"),
    ("Select MEMORY CARD slot to save\ncamouflage data.\n", "Выберите слот карты памяти для\nсохранения камуфляжа.\n"),
    ("Cancel camouflage data save?\n", "Отменить сохранение камуфляжа?\n"),
    ("Memory card (PS2) error! Please check\nmemory card (PS2) and try again.\n", "Ошибка карты памяти (PS2)! Проверьте\nкарту (PS2) и попробуйте снова.\n"),
    ("Memory card (PS2)\nalready contains this\ncamouflage data. Overwrite data?\n", "На карте памяти (PS2)\nуже есть этот камуфляж.\nПерезаписать?\n"),
    ("Create new camouflage data save file on\nmemory card (PS2)?\n", "Создать новый файл камуфляжа на\nкарте памяти (PS2)?\n"),
    ("Memory card (PS2) is not formatted.\nFormat memory card (PS2) and save\ncamouflage data?\n", "Карта памяти (PS2) не отформатирована.\nОтформатировать её и сохранить\nкамуфляж?\n"),
    ("Formatting memory card (PS2). Do not\nremove memory card (PS2), reset, or\nswitch off the console.\n", "Форматирование карты памяти (PS2). Не\nизвлекайте карту (PS2), не сбрасывайте\nи не выключайте консоль.\n"),
    ("Saving to memory card (PS2). Do not\nremove memory card (PS2), reset, or\nswitch off the console.\n", "Сохранение на карту памяти (PS2). Не\nизвлекайте карту (PS2), не сбрасывайте\nи не выключайте консоль.\n"),
    ("An error occurred while saving camouflage\ndata to memory card (PS2).\nTry saving again?\n", "Ошибка при сохранении камуфляжа на\nкарту памяти (PS2).\nПопробовать снова?\n"),
    ("Please insert memory card (PS2) to save\ncamouflage data.\n", "Вставьте карту памяти (PS2), чтобы\nсохранить камуфляж.\n"),
    ("End camouflage data download?\n", "Завершить загрузку камуфляжа?\n"),
    ("Camouflage data save successful.\nEnd camouflage data download?\n", "Камуфляж успешно сохранён.\nЗавершить загрузку камуфляжа?\n"),
    ("Insufficient free space on memory card\n(PS2). At least %dKB of free space\nis required to save Camouflage data.\n", "Недостаточно места на карте памяти\n(PS2). Для сохранения камуфляжа\nнужно не менее %dКБ.\n"),
    ("At least %dKB of free space is needed\non memory card (PS2) to save camouflage\ndata. Continue?\n", "Для сохранения камуфляжа нужно не менее\n%dКБ на карте памяти (PS2).\nПродолжить?\n"),
    ("Memory card (PS2) not found.\nPlease insert memory card (PS2).\nTry saving again?\n", "Карта памяти (PS2) не найдена.\nВставьте карту памяти (PS2).\nПопробовать снова?\n"),
]


def table():
    out = {}
    for en, ru in PAIRS:
        icons = PUA.findall(en)
        if ru.count("{") != len(icons):
            raise SystemExit(f"icon mismatch: {en!r}")
        out[en.encode("utf-8")] = ru.format(*icons).encode("utf-8")
    return out
