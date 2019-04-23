from flask import Flask, request
import logging
import json
import random
from wikiquotes import wikiquotes_api

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

sessionStorage = {}


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


def game():
    pass

def get_help(res):
    res['response']['text'] = 'Тебе никто не поможет, вухвхвахаха.  \
                              Лучше просто ответь на предыдущий вопрос'


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Меня зовут Алиса. И я не люблю разговаривать с незнакомыми людьми. Назови своё имя!'
        res['response']['buttons'] = [{
                    'title': 'Помощь',
                    'hide': False
                }]
        sessionStorage[user_id] = {
            'first_name': None,
            'language': None,
            'first_usage': True}
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if req['request']['original_utterance'].lower() == 'помощь':
            get_help(res)
            return
        elif first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'

        elif sessionStorage[user_id]['language'] is None:
            sessionStorage[user_id]['first_name'] = first_name
            res['response']['text'] = f'{first_name.title()}, выбери язык. Я цитирую по-английски и по-испански, но автора и тему можно выбирать по-русски!'
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
                    'title': 'Помощь',
                    'hide': True
                }
            ]

    elif sessionStorage[user_id]['first_usage']:
        res['response']['text'] = f"Приятно познакомиться, {sessionStorage[user_id]['first_name'].title()}, я могу найти тебе любую цитату на любую тему (почти)!"
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

    else:
        game()


def translate(name):
    return name


def get_quote_by_author(res, req):
    user_id = req['session']['user_id']
    quote = wikiquotes_api.get_quotes(translate(req['request']['original_utterance'].capitalize()), sessionStorage[user_id]['language'])
    res['response']['text'] = f'Вот, что я нашла! {quote}'
    res['response']['buttons'] = [
                {
                    'title': f"Цитата автора {req['request']['original_utterance'].capitalize()}",
                    'hide': True
                },
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


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name', то возвращаем её значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()
