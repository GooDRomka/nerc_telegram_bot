import telebot
from Config import bot, userList, sentencepull, labelpull, labele_grade, unlabeled_ids,corpus_sizes
from User import User
from utils import *
from Shop import Shop
import pickle
import os
import random


def send_text_controller(message):
    Comands = {
               "выйти": "exit",
                "вернуться" : "home", "домой": "home",
                "данные из файла" : "load_new_data_file",
               "разметка данных":"labeling_start",  "загрузить данные":"load_new_data",
               "размер выборки":"data_size"
               }
    if message.text.lower() in Comands:
        userList[message.chat.id].flag = Comands[message.text.lower()]
    print(f"До ответа flag :{userList[message.chat.id].flag} message:{message.text} chat: {message.chat}")
    userList[message.chat.id].flag = answer_maker(message.chat.id, message.text)
    print(f"После ответа flag :{userList[message.chat.id].flag}")
    print("____________")
    saveState()

def start_message_controller(message):
    global userList
    userList[message.chat.id].flag = "start"
    send_text_controller(message)

def help_message_controller(message):

    bot.send_message(message.chat.id,
                     f'Бот для разметки ')

def labeling_answer_maker(_id,message = None):
    global userList, sentencepull, labelpull, labele_grade, unlabeled_ids
    try:
        if userList[_id].flag == "home":
            keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
            # keyboard1.row("разметка данных", "данные из файла", "загрузить данные")
            keyboard1.row("разметка данных", "загрузить данные")
            keyboard1.row("Выйти")
            bot.send_message(_id, "Выбери действие", reply_markup=keyboard1)
            return "wait_choise"
        # if userList[_id].flag =="load_new_data":

        if userList[_id].flag =="labeling_start":
            keyboard1 = telebot.types.ReplyKeyboardMarkup(True)
            keyboard1.row("понял", "домой")
            bot.send_message(_id, "Сейчас вам будут показываться предложения и его разметка.\n Вам нужно оценить разметку", reply_markup=keyboard1)
            return "show_sent"

        if userList[_id].flag =="show_sent":
            keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
            keyboard1.row("верно", "плохо", "хз")
            keyboard1.row("домой")
            if len(unlabeled_ids)==0:
                bot.send_message(_id, "Данных нет! Добавьте сначала данные!")
                userList[_id].flag = "home"
                return answer_maker(_id, "")
            s_id = random.choice(unlabeled_ids)
            sentence, label = sentencepull[s_id], labelpull[s_id]
            userList[_id].sentence_id = s_id
            bot.send_message(_id, listToString(sentence)+"\n"+listToString(label), reply_markup=keyboard1)
            return "wait_label"

        if userList[_id].flag =="wait_label":
            sentence_id = userList[_id].sentence_id
            if message.lower() == "верно":
                update_status(sentence_id, 1)
            elif message.lower() == "плохо":
                update_status(sentence_id, -1)
            elif message.lower() == "хз":
                update_status(sentence_id, 0)
            else:
                bot.send_message(_id, "плохая метка, попробуй еще раз")
                userList[_id].flag = "wait_label"
                return "wait_label"
            userList[_id].flag = "show_sent"
            return answer_maker(_id, "")

        if userList[_id].flag =="load_new_data":
            file = './data/english/train.txt'
            # file = userList[_id].data_path
            data = load_data(file)
            if len(data['texts']) in corpus_sizes:
                userList[_id].flag = "home"
                bot.send_message(_id, "Такой датасет мы уже получали. Его размер " + str(len(data['texts'])) + " предложений")
                return answer_maker(_id, "")
            N = len(sentencepull)
            labelpull += data['labels']
            sentencepull += data['texts']
            corpus_sizes.append(len(data['texts']))
            for i in range(len(data['texts'])):
                labele_grade.append([])
                unlabeled_ids.append(i+N)
            bot.send_message(_id, "Данные загружены! Загружено "+str(len(data['texts']))+" предложений")
            userList[_id].data_path = ""
            userList[_id].flag = "home"
            return answer_maker(_id, "")

        if userList[_id].flag =="load_new_data_file":
            bot.send_message(_id,"Отправьте файл")
            return "wait_file"

        if userList[_id].flag == "wait_file":
            if message.voice.file_id!=None:
                file_id = message.voice.file_id
                newFile = bot.get_file(file_id)
                newFile.download('voice.txt')
                bot.send_message(_id, "Данные загружены")
                userList[_id].flag = "home"
                return answer_maker(_id, "")
            else:
                bot.send_message(_id, "Ошибка, попробуй другой файл")
                return "wait_file"



    except Exception as e:
        print("labeling_answer_maker_error")
        bot.send_message(_id, "Попробуй выполнить команду еще раз")
        return userList[_id].flag

def stat_answer_maker(_id, message = None):
    global userList,labele_grade,labelpull,sentencepull
    try:
        if userList[_id].flag == "home":
            keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
            # keyboard1.row("размер выборки", "моя статистика", "Выйти")
            keyboard1.row("размер выборки",  "Выйти")
            bot.send_message(_id, "Выбери действие", reply_markup=keyboard1)
            return "wait_choise"
        if userList[_id].flag == "data_size":
            print_data_size(_id)
            userList[_id].flag = "home"
            return answer_maker(_id, "")
        if userList[_id].flag == "user_stats":
            print_user_stats(_id)
            return "home"
    except Exception as e:
        print("stat_answer_maker_error")
        bot.send_message(_id, "Попробуй выполнить команду еще раз")
        return userList[_id].flag

def answer_maker(_id, message=None):
    global userList, labele_grade, labelpull,sentencepull
    noneKey = telebot.types.ReplyKeyboardMarkup(True, True)
    noneKey.row("Домой", "Выйти")
    try:
        if userList[_id].flag == "start":
            keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
            keyboard1.row("разметка данных", "размер выборки")
            # keyboard1.row("Разметить", "Статистика")
            bot.send_message(_id, "Что будем делать", reply_markup=keyboard1)
            return "wait_type"

        if userList[_id].flag == "exit":
            userList[_id].type_user = ""
            userList[_id].flag = "start"
            return answer_maker(_id, "")

        if userList[_id].flag == "wait_type":
            if message.lower() == "разметить":
                userList[_id].type_user = "labeling_type"
                userList[_id].flag = "home"
                return answer_maker(_id, message)

            elif message.lower() == "статистика":
                userList[_id].type_user = "stat_type"
                userList[_id].flag = "home"
                return answer_maker(_id, message)
            else:
                bot.send_message(_id, "Вы ввели что-то странное")
                userList[_id].flag = "start"
                return answer_maker(_id, message)

        if userList[_id].type_user == "labeling_type":
            return labeling_answer_maker(_id,message)
        elif userList[_id].type_user=="stat_type":
            return stat_answer_maker(_id,message)
        else:
            userList[_id].flag = "start"
            return answer_maker(_id, message)
    except Exception as e:
        print("answer_maker_error")
        bot.send_message(_id, "Попробуй выполнить команду еще раз")
        return userList[_id].flag

def get_key(d, value):
    for k, v in d.items():
        if v == value:
            return k
    return False

def get_number(m, value):
    j = 0
    for i in m:
        if i == value:
            return j
        j += 1

def newUser(message):
    # print(userList.keys(), message.id, message.id not in userList.keys())
    if message.id not in userList.keys():
        user = User(message)
        userList[message.id] = user
        userList[message.id].flag = "start"

def readLineInFile(n):
     with open('state.txt') as f:
        for index, line in enumerate(f):
            if index == n:
                a = line
                return a

def saveState():
    global userList,labele_grade,labelpull,sentencepull

    f = open(r'state.txt', 'wb')
    pickle.dump(userList, f)
    # pickle.dump(labele_grade, f)
    # pickle.dump(labelpull, f)
    # pickle.dump(sentencepull, f)
    f.close()

def uploadDataFromFile():
    global userList,labele_grade,labelpull,sentencepull
    f = open(r'state.txt', 'rb')
    if os.stat("state.txt").st_size == 0:
        return False
    userList = pickle.load(f)
    # labele_grade = pickle.load(f)
    # labelpull = pickle.load(f)
    # sentencepull = pickle.load(f)
    f.close()

def update_status(id, status):
    global labele_grade
    if status!=0:
        i=0
        while i < len(unlabeled_ids):
            if unlabeled_ids[i]==id:
                del unlabeled_ids[i]
                print('элемент размечен и удален из списка ожидания')
            else:
                i += 1
    labele_grade[id].append(status)

def print_user_stats(id):
    t = 5

def print_data_size(id):
    global labele_grade,labelpull,sentencepull, unlabeled_ids

    # datasize = listToString(sentencepull)+"\n"+listToString(labelpull)+"\n"+listToString(labele_grade)
    datasize = str("Кол предложений "+ str(len(sentencepull))+ "\n" + "кол меток "+ str(len(labelpull)) + "\n" + "кол непроверенных меток "+str(len(unlabeled_ids)))
    bot.send_message(id, datasize)

def listToString(s):
    str1 = ""
    for ele in s:
        str1 += str(ele)+" "
    return str1

def load_file(message):
    if userList[message.chat.id].flag == "load_new_data":
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = "./files/" + message.document.file_name
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
        userList[message.chat.id].data_path = src
        labeling_answer_maker(message.chat.id)