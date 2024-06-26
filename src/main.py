import os
from flask import Flask, request
import telebot
import time
from helper.log import log
from helper.api import apc_home, apc_comic_images, apc_comic_info, apc_search, images_to_pdf, nh_comic_images, hr_comic_images

app = Flask(__name__)
bot = telebot.TeleBot(os.getenv('bot_token'), threaded=False)
previous_message_ids = []

# Bot route to handle incoming messages
@app.route('/bot', methods=['POST'])
def telegram():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200

# Handler for the '/start' command
@bot.message_handler(commands=['start'])
def start_command(message):
    response_text = "Hello! Welcome to this bot!\n\n"
    response_text += "For help, use the command /help."
    bot.reply_to(message, response_text)

# Handler for the '/help' command
@bot.message_handler(commands=['help'])
def help_command(message):
    response_text = "Here are the available commands:\n\n"
    response_text += "/start - Start the bot.\n"
    response_text += "/help - Show this help message.\n"
    response_text += "/new - View latest Comics.\n"
    response_text += "/s query - search for Comics.\n"
    response_text += "/all {n} comic - Fetch all volumes of the comic, from starting chapter n.\n"
    bot.reply_to(message, response_text)

@bot.message_handler(commands=['new'])
def handle_com(message):
    if message.message_id in previous_message_ids:  
         return  
    previous_message_ids.append(message.message_id)
    full_list = apc_home()
    for item in full_list:
        cap = f"{item['title']} \n{item['rating']}⭐\n\n🌐 <code>{item['link']}</code>\n\nLatest Chapter\n{item['chapter']}\n📌 <code>{item['chapter_url']}</code>"
        image = item['img']
        bot.send_photo(message.chat.id, image, caption = str(cap), parse_mode='HTML')
    

@bot.message_handler(commands=['random'])
def handle_nh_random(message):
    if message.message_id in previous_message_ids:  
         return  
    previous_message_ids.append(message.message_id)
    
    url = 'https://nhentai.to/random'
    
    try:
        images = nh_comic_images(url)
        pages = str(len(images)) + ' Pages'
        bot.reply_to(message, pages)
        
        pdf, passed = images_to_pdf(images, url.split('/')[-1]) 
        
        caption = f"{passed} Pages were passed" if passed != 0 else "Complete"
        with open(pdf, 'rb') as pdf_file:
            bot.send_document(message.chat.id, pdf_file, caption = caption)
    except Exception as e:
        bot.reply_to(message, e)


@bot.message_handler(func=lambda message: message.text.startswith('https://hentairead.com/hentai/'))
def handle_nh(message):
    if message.message_id in previous_message_ids:  
         return  
    previous_message_ids.append(message.message_id)
    
    url = message.text
    
    try:
        images = hr_comic_images(url)
        pages = str(len(images)) + ' Pages'
        bot.reply_to(message, pages)
        
        pdf, passed = images_to_pdf(images, url.split('/')[-1]) 
        
        caption = f"{passed} Pages were passed" if passed != 0 else "Complete"
        with open(pdf, 'rb') as pdf_file:
            bot.send_document(message.chat.id, pdf_file, caption = caption)
    except Exception as e:
        bot.reply_to(message, e)

@bot.message_handler(func=lambda message: message.text.startswith('https://nhentai.to/g/'))
def handle_nh(message):
    if message.message_id in previous_message_ids:  
         return  
    previous_message_ids.append(message.message_id)
    
    url = message.text
    images = nh_comic_images(url)
    pages = str(len(images)) + ' Pages'
    bot.reply_to(message, pages)
    
    pdf, passed = images_to_pdf(images, url.split('/')[-1]) 
    
    caption = f"{passed} Pages were passed" if passed != 0 else "Complete"
    with open(pdf, 'rb') as pdf_file:
        bot.send_document(message.chat.id, pdf_file, caption = caption)

@bot.message_handler(func=lambda message: message.text.startswith('https://allporncomic.com/porncomic/'))
def handle_singles(message):
    if message.message_id in previous_message_ids:  
         return  
    previous_message_ids.append(message.message_id)
    
    url = message.text
    parts = url.replace('https://allporncomic.com/porncomic/', '').split('/')
    
    try:
        if len(parts) == 2:
            title, image, summary, rating, genres, chapters = apc_comic_info(url)
            bot.send_photo(message.chat.id, image, caption = f'⭕{title}⭕\n\n📖Summary \n{summary} \n\n⭐Rating \n{rating}\n\n🛑Genres\n{genres}')
            response = 'LATEST MANGA RELEASES -> \n\n\n'
            n = 0
            for chapter in chapters:
                n+=1
                response += f"{chapter['title']} \n📌 <code>{chapter['url']}</code> \n\n"
                if n % 10 == 0:
                    bot.send_message(message.chat.id, response, parse_mode='HTML')
                    response = ''
            if response != '':
                bot.reply_to(message, response, parse_mode='HTML')
                
        if len(parts) == 3:
            images = apc_comic_images(url)
            pages = str(len(images)) + ' Pages'
            bot.reply_to(message, pages)
            pdf, passed = images_to_pdf(images, parts[-2])
            caption = f"{passed} Pages were passed" if passed != 0 else "Complete"
            with open(pdf, 'rb') as pdf_file:
                bot.send_document(message.chat.id, pdf_file, caption = caption)
    except Exception as e:
        bot.reply_to(message, e)

'''     n = 0
        for img in images:
            n+=1
            time.sleep(0.2)
            try:
                bot.send_photo(message.chat.id, img)
            except:
                bot.send_message(message.chat.id, 'pass')
            if n%20 == 0:
                bot.send_message(message.chat.id, f'{n} Pages Completed')
        bot.send_message(message.chat.id, 'Comic Completed')
'''


@bot.message_handler(func=lambda message: message.text.startswith('/s'))
def handle_search(message):
    text = message.text
    query = text.replace('_', ' ').split()
    try:
        n = int(query[0].replace('/s', ''))
    except ValueError:
        n = 1
    query = '+'.join(query[1:]).strip()
    if not query:
        return

    heading, results = apc_search(query, n)
    if not results:
        bot.reply_to(message, "No results found.")
        return

    bot.reply_to(message, heading)  # Assuming results[0] contains the heading

    for item in results:
        caption = f"⭕{item['title']}⭕\n{item['rating']}⭐\n\n🌐 <code>{item['url']}</code>\n\nStatus: {item['status']}\n\n🛑Genres\n{item['genres']}\n\nLatest Chapter\n{item['chapter']}\n📌 <code>{item['chapter_url']}</code>"
        bot.send_photo(message.chat.id, item['image'], caption=caption, parse_mode='HTML')

    next_page_command = f"/s{n+1}_{query.replace('+', '_')}"
    bot.reply_to(message, next_page_command)

@bot.message_handler(func=lambda message: message.text.startswith('/all '))
def handle_multiple(message):
    if message.message_id in previous_message_ids:  
         return  
    previous_message_ids.append(message.message_id)

    text = message.text
    query = text.replace('/all', '',1).strip().split()

    if query[1]:
        n = query[0]
        webcomic = query[1]
    else:
        n = 0
        webcomic = query[0]

    title, image, summary, rating, genres, chapters = apc_comic_info(webcomic)
    bot.send_photo(message.chat.id, image, caption = f'⭕{title}⭕\n\n📖Summary \n{summary} \n\n⭐Rating \n{rating}\n\n🛑Genres\n{genres}')
    
    chapters.reverse()
    chapters = chapters[int(n):]
    
    try:
        bot.send_message(message.chat.id, str(len(chapters)) + ' Chapters')
        for chapter in chapters:
            url = chapter['url']
            title = chapter['title']
            images = apc_comic_images(url)
            pages = title + '\n📃 ' + str(len(images)) + ' Pages'
            bot.send_message(message.chat.id, pages)
            pdf, passed = images_to_pdf(images, chapter['title'])
            caption = f"{passed} Pages were passed" if passed != 0 else "Complete"
            with open(pdf, 'rb') as pdf_file:
                bot.send_document(message.chat.id, pdf_file, caption = caption)
    except Exception as e:
        bot.reply_to(message, e)
