import requests
import json
from bs4 import BeautifulSoup
import datetime
import threading
import time as t

locker = threading.Lock()

chars = "abcdefghijklmnopqrstuvwxyz"
ru_chars = ['а', 'б', 'в', 'г', 'д', 'е', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ы', 'э', 'ю', 'я']
en_tratslit_ru_chars = ['a', 'b', 'v', 'g', 'd', 'e', 'zh', 'z', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'r', 's', 't', 'u', 'f', 'h', 'ts', 'ch', 'sh', 'sch', 'y', 'e', 'ju', 'ja']
nums = "1234567890"
spec = "!\"ьъ#$%&\'()*+,./:;<=>?@[\\]^_`{|}~\t\n\r\x0b\x0c"

count = 0
threads = []


def main():
    global count
    text = input_valid_text()
    text = translit_text(text)
    
    type = input_valid_type()
    
    if type == "2":
        count = input_valid_count()

    check_text(text, type)


def input_valid_text():
    text = ""
    while True:
        text = input("Текст: ").lower()

        text_list = text.split()
        text = '-'.join(text_list)

        for s in spec:
            text = text.replace(s, "")

        text = text.replace(' ', '-')

        good_chars = True
        for char in text:
            if char == '-': continue

            if char not in chars and char not in nums and char not in ru_chars:
                good_chars = False
                break

        if good_chars:
            break

    return text


def translit_text(text):
    text_list = []
    for char in text:
        text_list.append(char)

    for i in range(len(text_list)):
        for j in range(len(ru_chars)):
            if text_list[i] == ru_chars[j]:
                text_list[i] = en_tratslit_ru_chars[j]

    text = ""
    for char in text_list:
        text = text + char

    return text


def input_valid_type():
    type = ""

    while type != "1" and type != "2":
        type = input("1)Синхронный парс\n2)Использование потоков\n: ")

    return type


def input_valid_count():
    count = 0

    while True:
        try:
            count = int(input("Количество потоков: "))

            if count < 1:
                raise Exception

            break
        except:
            continue

    return count


def check_text(text, type):
    global threads
    global count

    url = "https://telegra.ph/"

    dates = get_dates()

    all_numbers = True

    for char in text:
        if char not in nums:
            all_numbers = False
            break

    urls = []

    for date in dates:
        urls.append(url + text + "-" + date)

    if all_numbers:
        for date in dates:
            urls.append(url + text + date)

    url_infos = []

    with open(f'{text}.json', 'w', encoding='utf-8') as file:
        json.dump(url_infos, file, indent=4, ensure_ascii=False)
    
    for url in urls:
        if type == "1":
            check_urls_and_save(text, url)
        if type == "2":
            while len(threads) >= count:
                del_not_aliveTreads(threads)

            threads.append(threading.Thread(target=check_urls_and_save, args=(text, url)))
            threads[-1].start()

    while threads_alive(threads):
        del_not_aliveTreads(threads)


def check_urls_and_save(text, url):
    index = 1
    while True:
        if check_url_and_save(text, url, index) == False:
            break

        index += 1


def check_url_and_save(text, url, index):
    if index == 1:
        _url = url
    else:
        _url = f"{url}-{index}"

    response = requests.get(_url)

    print(f"[{response.status_code}] {_url}")
    if response.status_code != 200:
        return False

    url_info = get_url_info_from_response(response)

    save(text, url_info)
    
    return True


def get_url_info_from_response(response):
    title = ""
    author = ""
    datetime = ""

    try:
        soup = BeautifulSoup(response.text, "lxml")

        header = soup.find("header", attrs={"class": "tl_article_header"})
        h1 = header.findChildren("h1" , recursive=False)[0]

        title = h1.text

        a = soup.find("a", attrs={"rel": "author"})

        author = a.text

        time = soup.find("time")

        datetime = time["datetime"]
    except Exception as ex:
        print(f"{ex}")
        return None

    url_info = {
        "url": response.url,
        "title": title,
        "author": author,
        "datetime": datetime,
    }

    return url_info


def save(text, url_info):
    with locker:
        with open(f"{text}.json", "r", encoding='utf-8') as file:
            url_infos = json.load(file)

        url_infos.append(url_info)

        with open(f'{text}.json', 'w', encoding='utf-8') as file:
            json.dump(url_infos, file, indent=4, ensure_ascii=False)


def get_dates():
    dates = []

    for month in range(1, 13):
        for day in range(1, 32):
            _month = ""
            if month > 9:
                _month += f"{month}"
            else:
                _month += f"0{month}"

            _day = ""
            if day > 9:
                _day = f"{day}"
            else:
                _day += f"0{day}"

            dates.append(_month + "-" + _day)

    return dates


def threads_alive(threads):
    for thread in threads:
        if thread.is_alive():
            return True

    return False


def del_not_aliveTreads(threads):
    for i in range(len(threads) - 1, -1, -1):
        if threads[i].is_alive() == False:
            threads.pop(i)

    return threads


if __name__ == "__main__":
    while True:
        main()