# Бот-викторина
Данный бот создан с использованием `vk_api` и `python-telegram-bot`.  
Пользователь бота отвечает на вопросы и накапливает очки.  

## Установка
Клонируйте репозиторий и войдите в корневую директорию:
```sh
git clone https://github.com/ilyashirko/quiz_bot && cd quiz_bot
```
для того чтобы развернуть проект вам понадобится `python==3.8` и `poetry==1.2.0`. Установите зависимости:
```sh
poetry install
```
## Настройка переменных окружения
Пример в `.env.example`.  
`ADMIN_TELEGRAM_ID=` - telegram id администратора бота, который будет получать логи.  
`TELEGRAM_BOT_TOKEN=` - токен телеграм бота получаемый в [BotFather](https://t.me/botfather).  
`VK_BOT_TOKEN=` - токен vk бота получаемый при настройке сообщества.  
`REDIS_HOST=` - хост базы redis (по умолчанию - `localhost`).  
`REDIS_PORT=` - порт базы redis (по умолчанию - `6379`).  
`REDIS_PASSWORD=` - пароль базы redis (по умолчанию - `None`).  
`ANSWER_RATIO_BORDER=` - порог точности ответа (по умолчанию - `0.9`)