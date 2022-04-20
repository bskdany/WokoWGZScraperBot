import requests
from bs4 import BeautifulSoup
import time
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update

def main():
    #setup of telegram api to listen updates
    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher
    
    #setup of /start command
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    
    #setup of /help command
    help_handler = CommandHandler('help', help)
    dispatcher.add_handler(help_handler)
    
    #setup of messagge receiver
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)
    
    #bot is started
    updater.start_polling()
    
    #60 second loop that runs forever
    while True:
        getThatShit()
        time.sleep(60)

#function that scraps the website  
def getThatShit():

    #a list of already present advertisements is loaded
    file = open("existing.txt","r+")
    existingAdv = file.read()
    
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

        #looks for a link (is stole this)
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
        if identifierToken not in existingAdv:
            #message is sent
            sendMessage(finalMsg,price)
            #token is written to the list of tokens
            file.write(identifierToken+"\n")
            print("Found New Adv")
    file.close()
    print("Done")

#function that runs when /start is entered
def start(update: Update, context: CallbackContext):

    #the id of the user is taken
    chat_id = update.message.chat_id
    
    #checks if the id is in the list of autorized ids
    if str(chat_id) in idList:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Bot is working as usual")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Ops, you are not autorized yet. Send this number "+str(chat_id)+" to @bskdany to be whitelisted. Cheers.")

#function that runs when /help is entered
def help(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Write your max price like this: 'max price NUMBER'\nDon't put letters or anything because it will break")

#function that elaborates messages that aren't commands  
def echo(update: Update, context: CallbackContext):

    #if message is structured as needed
    if  update.message.text[:10] == "max price ":
        #user id and price inputed are taken
        chat_id = update.message.chat_id
        maxPrice = update.message.text[10:]

        #every id is checked to see a match
        counter = 0
        while counter <len(idList):

            #if an id is found then the max price for that user is set
            if idList[counter]==str(chat_id):
                idList[counter+1]=maxPrice

                #new max price is written to the txt file
                file1 = open("idList.txt","w")
                toWrite=""

                #commas and newlines are added to match the original
                counter1 = 0
                for i in idList:
                    toWrite = toWrite+i
                    if counter1%2 == 1 :
                        toWrite=toWrite+"\n"
                    else:
                        toWrite=toWrite+","
                    counter1 +=1
                toWrite = toWrite[:-1]

                #file is overwritten with new data
                file1.write(toWrite)
                file1.close()

                #response to the user of a complete action
                context.bot.send_message(chat_id=update.effective_chat.id, text="Max price set to "+str(maxPrice))
            counter+=1
    #if the command is misspelled a message is sent
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You misspelled the command") 

#function that sends the adv to the user        
def sendMessage(message,price):
    #every max price associated with every id is checked with the adv price
    counter = 0
    while counter <len(idList):
        if int(idList[counter+1]) >= int(price):
            #if the max price is higher the adv is sent in chat
            requests.get("https://api.telegram.org/bot"+token+"/sendMessage?chat_id="+idList[counter]+"&text={}".format(message))
        counter +=2

#function that reads the ids and max prices and puts them in an array
def getIdList():
    #file is processed
    file = open("idList.txt","r")
    temp = file.read()
    file.close()

    #string is cleared from special characters
    temp = temp.replace('\n', ',')
    temp = temp+"1"
    idList = []
    d = ""
    counter = 1
    for i in temp:
        if i == "," or counter==len(temp):
            idList.append(d)
            d=""
        else:
            d += i
        counter+=1
    return idList

#user data
token = "YOUR TOKEN"
idList = getIdList()
print(idList)

if __name__ == '__main__':
    main()