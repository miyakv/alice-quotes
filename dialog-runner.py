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


def try_again(res, btns):
    res['response']['text'] = "Попробуй ещё раз"
    res['response']['buttons'] = btns


def function_manager(res, req):
    user_id = req['session']['user_id']
    if req['request']['original_utterance'] == "Цитата по автору" or sessionStorage[user_id]["status"] == 1:
        get_quote_by_author(res, req)
    else:
        res['response']['text'] = '*{}*'.format(req['request']['original_utterance'].lower())


def get_help(res):
    res['response']['text'] = 'Тебе никто не поможет, вухвхвахаха.  \
                              Лучше просто ответь на предыдущий вопрос'


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Меня зовут Алиса. И я не люблю разговаривать ' \
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
        if req['request']['original_utterance'].lower() == 'помощь':
            get_help(res)
            return
        elif first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'

        elif sessionStorage[user_id]['language'] is None:
            sessionStorage[user_id]['first_name'] = first_name
            res['response']['text'] = f'{first_name.title()}, выбери язык. Я цитирую ' \
                                      f'по-английски и по-испански, но автора и тему можно выбирать по-русски!'
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

    elif sessionStorage[user_id]['first_usage']:
        if sessionStorage[user_id]['language'] is None:
            if req['request']['original_utterance'].lower() in ["английский", "испанский", "русский"]:
                lang = req['request']['original_utterance'].lower()
                sessionStorage[user_id]['language'] = translate(lang)
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
        res['response']['text'] = f"Приятно познакомиться, {sessionStorage[user_id]['first_name'].title()}, я могу найти тебе любую цитату на любую тему (почти)!" \
                                  f"Выбери что-то из ниже приведенных функций"
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
        sessionStorage[user_id]['first_usage'] = False
    else:
        options = ['цитата по автору', 'случайная цитата', 'цитата дня']
        if sessionStorage[user_id]['language'] is None:
            if req['request']['original_utterance'].lower() in ["английский", "испанский", "русский"]:
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
            return

        elif req['request']['original_utterance'].lower() in options or sessionStorage[user_id]["status"] != 0:
            function_manager(res, req)
        elif req['request']['original_utterance'].lower() == "помощь":
            get_help(res)
            main_menu(res)
            return
        else:
            troll(res, req)
            main_menu(res)
            return
 

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



def troll(res, req):
    troll_data = frozenset(['Тебе стоит попробовать снова'])
    user_id = req['session']['user_id']
    used = sessionStorage[user_id]["used_trolls"]
    if troll_data == used:
        res['response']['text'] = "{}, выбери что-то уже".\
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
   response = requests.get(url, params=params)
   logging.info(response.json())
   return response.json()["text"][0]


def get_quote_by_author(res, req):
    user_id = req['session']['user_id']
    if sessionStorage[user_id]["status"] == 0:
        res['response']['text'] = "Какого автора ищем? (Язык ответа - {})".format(sessionStorage[user_id]["language"])
        sessionStorage[user_id]["status"] = 1

    elif sessionStorage[user_id]["status"] == 1:
        data = req['request']['original_utterance'].lower()
        if data not in ["ещё цитату", "сменить автора", "в меню", "помощь"]:
            data = translate(data)
            sessionStorage[user_id]["author"] = data
            quote = random.choice(wikiquotes_api.get_quotes(data, sessionStorage[user_id]['language']))
            res['response']['text'] = f'Вот, что я нашла! {quote}'
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
        else:
            if data == "помощь":
                get_help(res)
                return
            elif data == "сменить автора":
                sessionStorage[user_id]["status"] = 0
                get_quote_by_author(res, req)
            elif data == "ещё цитату":
                quote = random.choice(wikiquotes_api.get_quotes(sessionStorage[user_id]['author'], sessionStorage[user_id]['language']))
                res['response']['text'] = f'Вот, что я нашла! {quote}'
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
                	}
                ]
            elif data == "в меню":
                sessionStorage[user_id]["status"] = 0
                res['response']["text"] = "Что будем делать далее?"
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
                function_manager(res, req)



def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()
