# Проект МАРС

## О проекте

МАРС - Мобильная Автоматическая Рейтинговая Система - проект, призванный автоматизировать выставление оценок учащимся (например, при их устном ответе на уроке) при помощи Computer Vision.

**Программная** часть проекта состоит из пяти основных модулей:
  - **face_rec.py** - отвечает за распознавания лиц (библиотеки OpenCV, face_recognition)
    + **faces_library** - папка с фотографиями учеников
  - **Графический интерфейс** проекта для конечного пользователя - сайт, написанный на Python Flask:
  	- **app.py** - основной файл визуализации, в нём прописаны все отслеживаемые страницы и взаимодействие с БД.
  	- **instance/mars.db** - база данных, содержащая таблицы необходимой сатйту информацией:
  	  + _Teacher_ - таблица, содержащая информацию об учителях (ID, имя, логин и хэш пароля)
  	  + _Student_ - содержит информацию об учениках (ID, имя, класс, ID учителя)
  	  + _Mark_ - содержит информацию о "плюсиках" выставленных ученикам. Каждая запись имеет вид:
  	    > _ID плюсика - ID ученика - Дата (в численном формате вида ГГГГММДД)_
    - **utils.py** - вспомогательные функции
    - **static** - папка, содержащая .html, .css и .ico файлы сайта. Также в ней хранится важная папка **undefined_image_cache**, в которой сохраняются все нераспознанные ученики с возможностью их потом распознать.
    - **templates** - папка с шаблонами сайта
  - **mars.apk** - (отдельный [репозиторий](http://github.com/MersennexTwister/android-project-mars)) приложение,взаимодействующее с сайтом (фактически - замена Raspberry)
  - **RPI - файлы** - (отдельный [репозиторий](http://github.com/MersennexTwister/rpi-project-mars)) модуль, код которого находится на _Raspberry Pi_ и которых осуществляет захват (библиотека **cv2**) изображения и отправку его на сайт (библиотека **requests**)

**Аппаратная** состоит из камеры и кнопки, подключенных к микрокомпьютеру _Raspberry Pi_. При нажатии на кнопку делается снимок, который обрабатывается и отправляется на сайт, где и происходит распознавание.

## Установка

Если вы ставите систему на Ubuntu, можете воспользоваться скриптом быстрой установки

```console
$ wget -O auto.sh "https://raw.githubusercontent.com/MersennexTwister/project-mars/main/auto.sh"
$ chmod +x auto.sh
$ sudo ./auto.sh
```
