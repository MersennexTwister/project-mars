# Проект МАРС

МАРС - Мобильная Автоматическая Рейтинговая Система - проект, призванный автоматизировать выставление оценок учащимся (например, при их устном ответе на уроке) при помощи Computer Vision

**Программная** часть проекта состоит из трех основных модулей:
  - **FaceRec** - отвечает за распознавания лиц (библиотеки OpenCV, face_recognition)
    - **faces** - папка с фотографиями учеников
  - **Spreadsheet** - работа с Google-таблицей (API GoogleSheets)
  - **interlayer** - объединяет FaceRec и Spreadsheet вместе

**Аппаратная** состоит из камеры и кнопки, подключенных к микрокомпьютеру Raspberry Pi. При нажатии на кнопку делается снимок, который отправляется на сайт, и там обрабатывается.

**Графический интерфейс** проекта для конечного пользователя - сайт, написанный на flask:
  - **visual.py** - основной файл визуализации, в нём прописаны все отслеживаемые страницы и взаимодействие с БД.
  - **data.db** - база данных, содержащая 2 таблицы: **Teacher** и **Student**. В таблице **Teacher** содержится информация об именах, логинах и паролях учителей. В таблице **Student** - информация об именах и ID учеников с указанием, какой ученик у какого учителя.
  - **static** - папка, содержащая .html, .css и .ico файлы сайта.