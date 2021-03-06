from flask import Flask, request
import logging
import json
from wikiquotes import wikiquotes_api
import requests
import random
import sys

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

sessionStorage = {}
sys.setrecursionlimit(1500)


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return json.dumps(response)


def check_help(req):
    if req['request']['original_utterance'].lower() in ['помощь', "что делать?", "что делать"]:
        return 1
    elif req['request']['original_utterance'].lower() in ["что ты умеешь", "что ты умеешь?"]:
        return 2
    else:
        return 0


def try_again(res, btns):
    res['response']['text'] = "Попробуй ещё раз"
    res['response']['buttons'] = btns


def function_manager(res, req):
    user_id = req['session']['user_id']
    if check_help(req) == 2:
        res['response']['text'] = 'Я могу выполнить одну из задач: найти цитату по автору,' \
                                      'прислать случайную цитату или цитату дня. Введи то, что я предложила ранее.'
        return
    if req['request']['original_utterance'].lower() == "цитата по автору" or \
            sessionStorage[user_id]["status"] == 1:
        get_quote_by_author(res, req)
    elif req['request']['original_utterance'].lower() == "цитата дня":
        day_quote(res, req)
    elif req['request']['original_utterance'].lower() == 'случайная цитата':
        random_quote(res, req)

    else:
        logging.info('403 ' + req['request']['original_utterance'])
        res['response']['text'] = '*{}*'.format(
            req['request']['original_utterance'].lower())


def day_quote(res, req):
    user_id = req['session']['user_id']
    if sessionStorage[user_id]['language'] == 'Russian':
        quote = translate_en(wikiquotes_api.quote_of_the_day("english")[0])
        author = translate_en(wikiquotes_api.quote_of_the_day("english")[1])
    else:
        quote, author = wikiquotes_api.quote_of_the_day(
            sessionStorage[user_id]['language'])
    res['response']['text'] = quote + ' (c) ' + author
    main_menu(res)


def random_quote(res, req):
    user_id = req['session']['user_id']
    url = "http://api.forismatic.com/api/1.0/"
    params = {
        "method": "getQuote",
        "format": "json",
        "lang": 'ru'
    }
    response = requests.get(url, params).json()
    quote = response["quoteText"]
    author = response["quoteAuthor"]
    logging.info(sessionStorage[user_id]['language'])
    if sessionStorage[user_id]['language'] == 'Russian':
        res['response']['text'] = quote + ' (c) ' + author
    elif sessionStorage[user_id]['language'] == 'Spanish':
        res['response']['text'] = translate_es(quote) + ' (c) ' + translate_es(author)
    else:
        res['response']['text'] = translate(quote) + ' (c) ' + translate(
            author)
    main_menu(res)


def day_quote_menu(res):
    res['response']['buttons'] = [
        {
            'title': 'Справка про автора',
            'hide': True
        },
        {
            'title': 'Перевести',
            'hide': True
        },
        {
            'title': 'В меню',
            'hide': True
        },
        {
            'title': 'Помощь',
            'hide': True
        }
    ]
    return


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response'][
            'text'] = 'Привет! Меня зовут Алиса. И я не люблю разговаривать ' \
                      'с незнакомыми людьми. Назови своё имя!'
        res['response']['buttons'] = [{
            'title': 'Помощь',
            'hide': False
        }]
        sessionStorage[user_id] = {
            "first_name": None,
            'language': None,
            'first_usage': True,
            'used_trolls': set(),
            "status": 0,
            "author": None}
        return

    if sessionStorage[user_id]["first_name"] is None:
        first_name = get_first_name(req)
        if check_help(req) == 2:
            res['response']['text'] = 'Я могу выполнить одну из задач: найти цитату по автору,' \
                                  'прислать случайную цитату или цитату дня. Напиши своё имя.'
            return
        if check_help(req) == 1:
            res['response']['text'] = 'Напиши своё имя.'
            return

        elif first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'

        elif sessionStorage[user_id]['language'] is None:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = f'{first_name.title()}, выбери язык. Я цитирую ' \
                          f'по-английски и по-испански, но автора и тему можно выбирать по-русски!'
            choose_language(res)

    elif sessionStorage[user_id]['first_usage']:
        if sessionStorage[user_id]['language'] is None:
            if req['request']['original_utterance'].lower() in ["английский",
                                                                "испанский",
                                                                "русский"]:
                lang = req['request']['original_utterance'].lower()
                sessionStorage[user_id]['language'] = translate(lang)
            if check_help(req) == 2:
                res['response']['text'] = 'Я могу выполнить одну из задач: найти цитату по автору,' \
                                      'прислать случайную цитату или цитату дня. Выбери язык, на котором я буду присылать тебе цитаты.'
                choose_language(res)
                return
            elif check_help(req) == 1:
                res['response']['text'] = 'Выбери язык, на котором я буду присылать тебе цитаты.'
                choose_language(res)
                return
            else:
                logging.info(req['request']['original_utterance'].lower())
                try_again(res, [
                    {
                        'title': 'Английский',
                        'hide': True
                    },
                    {
                        'title': 'Испанский',
                        'hide': True
                    },
                    {
                        'title': 'Русский',
                        'hide': True
                    },
                    {
                        'title': 'Помощь',
                        'hide': True
                    }
                ])
        res['response'][
            'text'] = f"Приятно познакомиться, {sessionStorage[user_id]['first_name'].title()}, я могу найти тебе любую цитату на любую тему (почти)!" \
                      f"Выбери что-то из ниже приведенных функций"
        main_menu(res)
        sessionStorage[user_id]['first_usage'] = False
    else:
        options = ['цитата по автору', 'случайная цитата', 'цитата дня']
        if sessionStorage[user_id]['language'] is None:
            if check_help(req) == 2:
                res['response']['text'] = 'Я могу выполнить одну из задач: найти цитату по автору,' \
                                      'прислать случайную цитату или цитату дня. Выбери язык, на котором я ' \
                                          'буду присылать тебе цитаты.'
                choose_language(res)
                return
            if req['request']['original_utterance'].lower() in ["английский",
                                                                "испанский",
                                                                "русский"]:
                lang = req['request']['original_utterance'].lower()
                sessionStorage[user_id]['language'] = translate(lang)
                logging.info(sessionStorage[user_id]['language'])
                res['response']["text"] = "Успешно! Что будем делать далее?"
                res['response']['buttons'] = [
                    {
                        'title': 'Цитата по автору',
                        'hide': True
                    },
                    {
                        'title': 'Случайная цитата',
                        'hide': True
                    },
                    {
                        'title': 'Цитата дня',
                        'hide': True
                    },
                    {
                        'title': 'Сменить язык',
                        'hide': True
                    },
                    {
                        'title': 'Помощь',
                        'hide': True
                    }
                ]
                return
            elif check_help(req) == 1:
                res['response']['text'] = 'Выбери язык, на котором я буду присылать тебе цитаты.'
                choose_language(res)
                return
            else:
                logging.info(req['request']['original_utterance'].lower())
                try_again(res, [
                    {
                        'title': 'Английский',
                        'hide': True
                    },
                    {
                        'title': 'Испанский',
                        'hide': True
                    },
                    {
                        'title': 'Русский',
                        'hide': True
                    },
                    {
                        'title': 'Помощь',
                        'hide': True
                    }
                ])
                return
        elif req['request']['original_utterance'].lower() == "сменить язык":
            sessionStorage[user_id]["language"] = None
            res['response']['text'] = 'Выбери язык. Я цитирую ' \
                                      'по-английски и по-испански, но автора и тему можно выбирать по-русски!'
            choose_language(res)
            return

        elif req['request']['original_utterance'].lower() in options or \
                sessionStorage[user_id]["status"] != 0:
            function_manager(res, req)
        elif check_help(req) == 2:
            res['response']['text'] = 'Я могу выполнить одну из задач: найти цитату по автору,' \
                                      'прислать случайную цитату или цитату дня. Выбери задачу, а я её решу!'
            main_menu(res)

        elif check_help(req) == 1:
            res['response']['text'] = 'Нажав на кнопку "Цитата по автору", ты сможешь выбрать автора, и я пришлю его цитату' \
                                      ' Нажав на кнопку "Случайная цитата", ты получишь случайную цитату.' \
                                      ' Нажав на кнопку "Цитата дня", ты получишь цитату дня с главной страницы Викицитатника в зависимости от выбранного языка.' \
                                      ' Нажав на кнопку "Сменить язык", ты сможешь заново выбрать язык цитат.'
            main_menu(res)
            return
        else:
            troll(res, req)
            main_menu(res)
            return


def choose_language(res):
    res['response']['buttons'] = [
        {
            'title': 'Английский',
            'hide': True
        },
        {
            'title': 'Испанский',
            'hide': True
        },
        {
            'title': 'Русский',
            'hide': True
        },
        {
            'title': 'Помощь',
            'hide': True
        }
    ]


def main_menu(res):
    res['response']['buttons'] = [
        {
            'title': 'Цитата по автору',
            'hide': True
        },
        {
            'title': 'Случайная цитата',
            'hide': True
        },
        {
            'title': 'Цитата дня',
            'hide': True
        },
        {
            'title': 'Сменить язык',
            'hide': True
        },
        {
            'title': 'Помощь',
            'hide': True
        }
    ]
    return


def troll(res, req):
    troll_data = frozenset(['Тебе стоит попробовать снова'])
    user_id = req['session']['user_id']
    used = sessionStorage[user_id]["used_trolls"]
    if troll_data == used:
        res['response']['text'] = "{}, выбери что-то уже". \
            format(sessionStorage[user_id]['first_name'].capitalize())
    for text in troll_data:
        if text not in used:
            res['response']['text'] = text
            sessionStorage[user_id]["used_trolls"].add(text)
            break


def translate(text):
    url = "https://translate.yandex.net/api/v1.5/tr.json/translate"
    params = {
        "key": "trnsl.1.1.20190416T141124Z.ac418fee0118467f.aba009a704b3253811d92e3b09cf11769e239b66",
        "text": text,
        "lang": 'en',
        "format": 'plain'
    }
    try:
        response = requests.get(url, params=params)
        logging.info(response.json())
        data = response.json()["text"][0]
    except Exception as e:
        logging.info(e)
        return text
    return data


def translate_en(text):
    url = "https://translate.yandex.net/api/v1.5/tr.json/translate"
    params = {
        "key": "trnsl.1.1.20190416T141124Z.ac418fee0118467f.aba009a704b3253811d92e3b09cf11769e239b66",
        "text": text,
        "lang": 'ru',
        "format": 'plain'
    }
    response = requests.get(url, params=params)
    logging.info(response.json())
    return response.json()["text"][0]


def translate_es(text):
    url = "https://translate.yandex.net/api/v1.5/tr.json/translate"
    params = {
        "key": "trnsl.1.1.20190416T141124Z.ac418fee0118467f.aba009a704b3253811d92e3b09cf11769e239b66",
        "text": text,
        "lang": 'es',
        "format": 'plain'
    }
    response = requests.get(url, params=params)
    logging.info(response.json())
    return response.json()['text'][0]


def search_author_in_wikipedia(res, req):
    user_id = req['session']['user_id']
    text = sessionStorage[user_id]['author']
    url = 'https://ru.wikipedia.org/w/api.php'
    params = {
        "action": 'opensearch',
        "search": translate_en(text),
        "limit": 1,
        "format": 'json',
        "inprop": 'url'
    }
    response = requests.get(url, params=params)
    logging.info(response.json())
    result = list(response.json())[1][0], list(response.json())[2][0], \
        list(response.json())[3][0]
    res['response']['text'] = f'Насколько я знаю, {result[0]} - {result[1]}, ' \
                              f'Больше об этом человеке можно узнать здесь: {result[2]}'
    res['response']['buttons'] = [
        {
            'title': "Ещё цитату",
            'hide': True
        },
        {
            'title': 'Сменить автора',
            'hide': True
        },
        {
            'title': 'В меню',
            'hide': True
        },
        {
            'title': 'Помощь',
            'hide': True
        }]


def get_quote_by_author(res, req):
    user_id = req['session']['user_id']
    if sessionStorage[user_id]["status"] == 0:
        res['response'][
            'text'] = "Какого автора ищем? (Язык ответа - {})".format(
            sessionStorage[user_id]["language"])
        res['response']['buttons'] = [
            {
                'title': "Путин",
                'hide': True
            },
            {
                'title': 'Ницше',
                'hide': True
            },
            {
                'title': 'Хайям',
                'hide': True
            },
            {
                'title': 'Ганди',
                'hide': True
            }]
        sessionStorage[user_id]["status"] = 1

    elif sessionStorage[user_id]["status"] == 1:
        data = req['request']['original_utterance'].lower()
        if data not in ["ещё цитату", "сменить автора", "в меню", "помощь",
                        "кто это?", "что делать"]:

            data = translate(data)
            logging.info(data)
            sessionStorage[user_id]["author"] = data
            lang = sessionStorage[user_id]['language']
            if lang == 'Russian':
                lang = 'English'
            quote = random.choice(wikiquotes_api.get_quotes(data, lang))
            while len(quote) > 350:
                quote = random.choice(wikiquotes_api.get_quotes(data, lang))
            if sessionStorage[user_id]["language"] == 'Russian':
                quote = translate_en(quote)

            res['response']['text'] = f'Вот, что я нашла! {quote}'
            res['response']['buttons'] = [
                {
                    'title': "Кто это?",
                    'hide': True
                },
                {
                    'title': "Ещё цитату",
                    'hide': True
                },
                {
                    'title': 'Сменить автора',
                    'hide': True
                },
                {
                    'title': 'В меню',
                    'hide': True
                },
                {
                    'title': 'Помощь',
                    'hide': True
                }]
        else:
            if check_help(req) == 1:
                if not sessionStorage[user_id]["author"]:
                    res['response']['text'] = 'Выбери автора цитаты'
                    res['response']['buttons'] = [
                    {
                        'title': "Путин",
                        'hide': True
                    },
                    {
                        'title': 'Ницше',
                        'hide': True
                    },
                    {
                        'title': 'Хайям',
                        'hide': True
                    },
                    {
                        'title': 'Ганди',
                        'hide': True
                    }]
                    return
                else:
                    res['response']['text'] = 'Нажав на кнопку "Кто это?", ты получишь информацию про автора.' \
                                  ' Нажав на кнопку "Ещё цитату", ты получишь цитату выбранного ранее автора.' \
                                  ' Нажав на кнопку "Сменить автора", ты сможешь заново выбрать автора.' \
                                  ' Нажав на кнопку "В меню", ты выйдешь в главное меню.'
                    res['response']['buttons'] = [
                    {
                        'title': "Кто это?",
                        'hide': True
                    },
                    {
                        'title': "Ещё цитату",
                        'hide': True
                    },
                    {
                        'title': 'Сменить автора',
                        'hide': True
                    },
                    {
                        'title': 'В меню',
                        'hide': True
                    },
                    {
                        'title': 'Помощь',
                        'hide': True
                    }
                    ]
                    return
            if data == "сменить автора":
                sessionStorage[user_id]["status"] = 0
                get_quote_by_author(res, req)
            elif data == "кто это?":
                search_author_in_wikipedia(res, req)
            elif data == "ещё цитату":
                data = sessionStorage[user_id]["author"]
                logging.info(data)
                lang = sessionStorage[user_id]['language']
                if lang == 'Russian':
                    lang = 'English'
                quote = random.choice(wikiquotes_api.get_quotes(data, lang))
                while len(quote) > 350:
                    quote = random.choice(wikiquotes_api.get_quotes(data, lang))
                if sessionStorage[user_id]["language"] == 'Russian':
                    quote = translate_en(quote)
                res['response']['text'] = f'Вот, что ещё я нашла! {quote}'
                res['response']['buttons'] = [
                    {
                        'title': "Кто это?",
                        'hide': True
                    },
                    {
                        'title': "Ещё цитату",
                        'hide': True
                    },
                    {
                        'title': 'Сменить автора',
                        'hide': True
                    },
                    {
                        'title': 'В меню',
                        'hide': True
                    },
                    {
                        'title': 'Помощь',
                        'hide': True
                    }
                ]
            elif data == "в меню":
                sessionStorage[user_id]["status"] = 0
                res['response']["text"] = "Что будем делать далее?"
                main_menu(res)
                function_manager(res, req)


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()
