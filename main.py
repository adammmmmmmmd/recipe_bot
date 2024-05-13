from googletrans import Translator
import requests
from sqlalchemy import text
import telebot
import telebot.apihelper

from config import TELEGRAM_TOKEN, MEAL_BASE_URL


try:
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
    bot_info = bot.get_me()
except telebot.apihelper.ApiTelegramException:
    print("Ошибка токена, проверьте его на правильность")
    bot.stop_bot()
else:
    print("Бот авторизован")


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    """Отправляет пользователю два сообщения: приветствие, 
    а также просьбу отправить название блюда.
    """
    text = (
        f'Привет! Этот бот позволяет получить рецепт '
        f'интересующего вас блюда.'
    )
    bot.reply_to(message, text)
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Введите название блюда: ')


@bot.message_handler(func=lambda m: True)
def handle_meal(message):
    """Ожидает сообщение пользователя. При получении сообщения отправляет
    пользователю сообщение с информацией о начале поиска.
    """
    bot.send_message(message.chat.id, 'Получено. Начинаю поиск.')
    get_meal_name(message)


def get_meal_url(meal_name):
    """Переводит название блюда на английский. Составляет url для 
    последующего осуществления запроса.
    """
    translator = Translator()
    print(translator.translate(meal_name))
    translated_meal_name = str(translator.translate(meal_name).text)
    url = f'{MEAL_BASE_URL}{translated_meal_name}'
    return url


def get_meal_info(meal_name):
    """Запрашивает данные через api с помощью url."""
    url = get_meal_url(meal_name)
    response = requests.get(url)
    return response


def send_search_failed(message):
    """Отправляет пользователю сообщение об неудачном получении данных.
    """
    text = 'Не удалось получить данные'
    bot.reply_to(message, text)
    exit()


def get_meal_name(message):
    """Формирует и отправляет пользователю ответ о поиске запрошенного 
    блюда в зависимости от успешности поиска.
    """
    meal_name = message.text
    response = get_meal_info(meal_name)
    if response.status_code == 200:
        data = response.json()
        product_list = list()
        measure_list = list()
        try:
            ingridients = data["meals"][0]
            extra_fields = ['idMeal',
                            'strMeal',
                            'strCategory',
                            'strDrinkAlternate',
                            'strCategory',
                            'strArea',
                            'strInstructions',
                            'strMealThumb',
                            'strTags',
                            'strYoutube',
                            'strSource',
                            'strImageSource',
                            'strCreativeCommonsConfirmed',
                            'dateModified']
            for ingridient in ingridients:
                if ingridient not in extra_fields and ingridient.startswith('strIngredient') and ingridients.get(ingridient):
                    product_list.append(ingridients.get(ingridient))
            print(product_list)

            for ingridient in ingridients:
                if ingridient not in extra_fields and ingridient.startswith('strMeasure') and ingridients.get(ingridient):
                    measure_list.append(ingridients.get(ingridient))
            print(measure_list) 
            zipped_product_list = zip(product_list, measure_list)
            zipped_product_list = list(zipped_product_list)
            print(zipped_product_list)
        except IndexError:
            print('Блюдо не найдено')
            send_search_failed(message)
        msg_text = (
            f'Рецепт {meal_name}:\nИнгридиенты:\n{list(zipped_product_list)}'
        )
        bot.reply_to(message, msg_text)
    else:
        bot.reply_to(message, f'Блюдо {meal_name} не найдено\n')


def main():
    bot.infinity_polling()


if __name__ == '__main__':
    main()
