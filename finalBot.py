import requests
from bs4 import BeautifulSoup
import time
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update

firstRunWoko = True
firstRunWGRoom = True

def main():
    #setup of telegram api to listen updates
    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher
    
    #setup of /start command
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    
    #bot is started
    updater.start_polling()
    
    #60 second loop that runs forever
    while True:
        scrapeWoko()
        scrapeWGZimmer()
        print("Searching for new rooms...")
        time.sleep(60)

#function that scraps the Woko website  
def scrapeWoko():
    
    global firstRunWoko
    #a list of already present advertisements is loaded
    file = open("existingWoko.txt","r+")
    existingAdvWoko = file.read()
    
    #html is taken from the website
    url = 'https://www.woko.ch/en/zimmer-in-zuerich'
    headers = { 'User-Agent': 'Generic user agent' }
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')

    #advertisements are filtered from the rest
    dataHtml = soup.find_all("div", {"class": "inserat"})
    for adv in dataHtml:
        #text is cleaned
        data = adv.getText()
        text = data.replace('\r', '')
        text = text.replace('\t', '')
        text = text.replace('\n\n', '\n')
        text = text.replace('\n\n\n', '\n')

        #looks for a link (I stole this)
        a_class = adv.find_all('a')
        url = a_class[0].get('href')
        
        #gets the price from the text for later use
        ncounter = 0
        lcounter = 0
        price = ""
        for letter in text:
            if letter =="\n":
                ncounter+=1
                if ncounter==11:
                    price=text[lcounter+1:]
            lcounter+=1
        price = price[:-4]

        #a token different for every adv is taken
        identifierToken = url[-4:]
        url = "https://www.woko.ch/en/zimmer-in-zuerich" + "-details/" + identifierToken
        #final message is created
        finalMsg = text + url

        #if the adv is a new one
        if url not in existingAdvWoko:
            if firstRunWoko==False:
                #url is written to the list of urls
                file.write(url+"\n")
                print("Found New Adv")
                #message is sent
                sendMessage(finalMsg,price)
            else:
                file.write(url+"\n")
                print("Skipped because of restart")
    file.close()
    if firstRunWoko == True:
        firstRunWoko = False
        print("First run completed Woko")

##function that scraps the WGZimmer website
def scrapeWGZimmer():

    global firstRunWGRoom

    #existing urls are taken
    file = open("existingWGZimmer.txt","r+")
    existingAdvWGZimmer = file.read()

    #this website is a little bit different, I have to send
    #a post request to simulate the click of the search button
    cookies = {
        'wc_language': 'en',
        'wc_currencyLocale': 'de_CH',
        'wc_color': 'babyblue',
        'wc_email': 'info@wgzimmer.ch',
        'wc_currencySign': 'sFr.',
        'JSESSIONID': 'E4841F478C05C1CC9E81AB91300FF5E6',
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Origin': 'https://www.wgzimmer.ch',
        'Connection': 'keep-alive',
        'Referer': 'https://www.wgzimmer.ch/en/wgzimmer/search/mate.html?wgSearchStartOver=true',
        # Requests sorts cookies= alphabetically
        # 'Cookie': 'wc_language=en; wc_currencyLocale=de_CH; wc_color=babyblue; wc_email=info@wgzimmer.ch; wc_currencySign=sFr.; JSESSIONID=E4841F478C05C1CC9E81AB91300FF5E6',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        # Requests doesn't support trailers
        # 'TE': 'trailers',
    }
    
    data = {
        'query': '',
        'priceMin': '200',
        'priceMax': '700',
        'state': 'zurich-stadt',
        'permanent': 'all',
        'student': 'none',
        'typeofwg': 'all',
        'orderBy': '@sortDate',
        'orderDir': 'descending',
        'startSearchMate': 'true',
        'wgStartSearch': 'true',
        'start': '0',
    }

    #request is made
    response = requests.post('https://www.wgzimmer.ch/en/wgzimmer/search/mate.html?', headers=headers, cookies=cookies, data=data)

    #all html
    soup = BeautifulSoup(response.text,'html.parser')
    #only ads html
    adsHtml = soup.find_all("li", {"class": "search-result-entry search-mate-entry"})
   
    #for every ad  
    for adv in adsHtml:
        finalMsgArray = []

        #text is filtered and prettified (is that a word?)
        data = adv.find_all("strong")
        counter = 0
        for d in data:
            d = d.text
            if counter == 0:
                b = d[1:]
                b = "Creation date: "+b[:-13]
                finalMsgArray.append(b)
            elif d=="\n":
                a = 1
            elif counter==2:
                finalMsgArray.append("From: "+d)
            else:
                finalMsgArray.append(d)
            counter+=1
        
        #this piece of data couldn't be found in <strong>, and so I'm taking it manually
        text = adv.find_all(text=True)
        untilData = text[29]
        untilData = untilData[1:]

        temp = finalMsgArray[3]
        finalMsgArray[3] = untilData
        finalMsgArray.append(temp[1:])

        #price is filtered for later
        price = temp[5:-3]

        finalMsg = ""
        for i in finalMsgArray:
            finalMsg+=i +'\n'
        
        #url is taken
        a_class = adv.find_all('a')
        url = a_class[1].get('href')
        url = 'https://www.wgzimmer.ch' + url
        finalMsg += url + "\n"

        #if url already exists 
        if url not in existingAdvWGZimmer:

            #if its notthe first run
            if firstRunWGRoom==False:
                #message is sent
                print("Found Room Wgroom")
                sendMessage(finalMsg,price)
                #url is written to the txt file
                file.write(url+"\n")
            else:
                file.write(url+"\n")
                print("Skipped because of restart")
    
    file.close()
    if firstRunWGRoom == True:
        firstRunWGRoom = False
        print("First run completed WGRoom")


#function that runs when /start is entered
def start(update: Update, context: CallbackContext):

    #the id of the user is taken
    chat_id = update.message.chat_id
    
    #checks if the id is in the list of autorized ids
    if str(chat_id) in idList:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Account is autorized, bot is working")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Ops, you are not autorized yet. Send this number "+str(chat_id)+" to @bskdany to be whitelisted. Cheers.")

#function that sends the adv to the user        
def sendMessage(message,price):
    for id in idList:
        if int(price)<=800:
            #if the max price is higher the adv is sent in chat
            requests.get("https://api.telegram.org/bot"+token+"/sendMessage?chat_id="+id+"&text={}".format(message))
        
#function that reads the ids and max prices and puts them in an array
def getIdList():
    #file is processed
    file = open("idList.txt","r")
    temp = file.readlines()
    idList = []
    for i in temp:
        idList.append(i[:-1])
    file.close()
    return idList

#user data
token = "YOURTOKEN"
idList = getIdList()
print("Authorized Ids:")
for id in idList:
    print(id)

if __name__ == '__main__':
    main()