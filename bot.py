import logging
import os
import json
import requests
from telegram import Update
from telegram.ext import (ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext)
from dotenv import load_dotenv
from translator import run_spider, ReversoContextScraperSpider

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

token = os.getenv('TOKEN')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(text='Olá, bem vindo(a) ao bot de utilidades.\n'
                                         'Envie /help para ver a lista de comandos disponíveis!',
                                    reply_to_message_id=update.message.id)


async def help_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(text='Comandos:\n'
                                         '/start - Inicia o bot\n'
                                         '/help - Mostra a descrição de todos os comandos\n'
                                         '/cotacao moeda - Mostra a cotação atual da moeda escolhida,'
                                         ' (dólar ou euro). Por exemplo: /cotacao dólar\n'
                                         '/traducao palavras - Traduz do inglês para o português as palavras'
                                         ' digitadas, podendo separar por vírgulas e espaço.\n'
                                         '/clima cidade, sigla do estado - Retorna a temperatura atual na '
                                         'cidade/estado especificados. Ex: Rio de Janeiro, RJ',
                                    reply_to_message_id=update.message.id)


async def cotacao(update: Update, context: CallbackContext):
    requisicao = requests.get('https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL').json()
    # last_message = update.message.text.lower().strip()
    if context.args:
        currency = ''.join(context.args).lower()
        currencies = {
            'USD': ['dolar', 'usd', 'dólar'],
            'EUR': ['euro', 'eur'],
        }
        quote = None
        for key, values in currencies.items():
            if currency in values:
                quote = requisicao[f'{key}BRL']['ask']
        if not quote:
            await update.message.reply_text('Moeda inválida ou não disponível!',
                                            reply_to_message_id=update.message.id)
        else:
            await update.message.reply_text(text=f'Cotação do {currency} nesse momento: R${float(quote):.2f}',
                                            reply_to_message_id=update.message.id)
    else:
        await update.message.reply_text('Digite uma moeda válida como parâmetro.')


async def traducao(update: Update, context: CallbackContext):
    if context.args:
        words = list(context.args)
        print(words)
        words = ' '.join(words).split(',')
        print(words)
        run_spider(ReversoContextScraperSpider, words)
        with open('last_translate.json', encoding='utf-8') as translate_file:
            data = json.load(translate_file)
            print(data, len(data))
            if not data:
                await update.message.reply_text(f'Ops, não foi possível traduzir nenhuma palavra.')
            else:
                for datum in data:
                    word_json = str(datum['Palavra']).strip()
                    translate_json = ', '.join(datum['Tradução'])
                    await update.message.reply_text(f'Tradução de {word_json} = {translate_json}')
                if len(data) < len(words):
                    await update.message.reply_text(f'Atenção!! *Não foi possível traduzir uma ou mais palavras da lista.*')

    else:
        await update.message.reply_text('Utilize uma palavra ou mais palavras como parâmetro.')


async def clima(update: Update, context: CallbackContext):
    api_key = os.getenv('API_KEY')
    if context.args:
        print(context.args)
        argumentos_formatados = ' '.join(context.args).split(',')
        city = argumentos_formatados[0]
        state = argumentos_formatados[1]
        country = 'Brasil'
        lang = 'pt-br'

        current_weather_data = requests.get(f'https://api.openweathermap.org/data/2.5/weather?'
                                            f'q={city},{state},{country}&appid={api_key}&units=metric&lang={lang}').json()
        current_temp = current_weather_data['main']['temp']
        await update.message.reply_text(f'Temperatura atual para {city}, {state} - {country} \n➡ {current_temp}º C')
    else:
        await update.message.reply_text('Siga o padrão de parâmetros para ver o clima. Na dúvida, digite "/help".')


if __name__ == '__main__':
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_me))
    application.add_handler(CommandHandler('cotacao', cotacao))
    application.add_handler(CommandHandler('traducao', traducao))
    application.add_handler(CommandHandler('clima', clima))

    application.run_polling()
