import json
import os
import pprint
import re
import time
from urllib import parse

import requests as req
from bs4 import BeautifulSoup as bs

# # 隨機取得 User-Agent
# from fake_useragent import UserAgent
# ua = UserAgent(cache=True) # cache=True 表示從已經儲存的列表中提取

'''放置 金庸小說 metadata 的資訊'''
listData = []

'''小庸小說的網址'''
url = 'https://www.bookwormzz.com/zh/'

'''設定標頭'''
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
}

# 沒有放置 txt 檔的資料夾，就建立起來
folderPath = 'jinyong'
if not os.path.exists(folderPath):
    os.makedirs(folderPath)

# 取得小說的主要連結
def getMainLinks():
    # 走訪首頁
    res = req.get(url, headers = headers)
    soup = bs(res.text, "lxml")
    
    # 取得主要連結
    a_elms = soup.select('a[data-ajax="false"]')
    
    # 整理主要連結資訊
    for a in a_elms:
        listData.append({
            "title": a.get_text(),
            "link": url + parse.unquote( a['href'] ) + '#book_toc',
            "sub": [] # 為了放置各個章回小說的內頁資料，下一個步驟會用到
        })

# 取得所有小說的獨立連結
def getSubLinks():
    for i in range( len(listData) ):
        # 走訪章回小說內頁
        res = req.get(listData[i]['link'], headers = headers)
        soup = bs(res.text, "lxml")
        a_elms = soup.select('div[data-theme="b"][data-content-theme="c"] a[rel="external"]')
        
        # 若是走訪網頁時，選擇不到特定的元素，視為沒有資料，continue 到 for 的下一個 index 去
        if len(a_elms) > 0:
            for a in a_elms:
                listData[i]['sub'].append({
                    "sub_title": a.get_text(),
                    "sub_link": url + parse.unquote( a['href'] )
                })
        else:
            continue

# 建立金庸小說的 json 檔
def saveJson():
    with open(f"{folderPath}/jinyong.json", "w", encoding="utf-8") as file:
        file.write( json.dumps(listData, ensure_ascii=False) )

# 將金庸小說所有章回的內容，各自寫到 txt 與 json 中
def writeTxt():
    # 稍候建立 train.json 前的程式變數
    listContent = []

    # 開啟 金庸小說 metadata 的 json 檔
    with open(f"{folderPath}/jinyong.json", "r", encoding="utf-8") as file:
        strJson = file.read()

    # 走訪所有章回的小說文字內容
    listResult = json.loads(strJson)
    for i in range(len(listResult)):
        for j in range(len(listResult[i]['sub'])):
            res = req.get(listResult[i]['sub'][j]['sub_link'], headers = headers)
            soup = bs(res.text, "lxml")
            div = soup.select_one('div#html > div')
            strContent = div.get_text()
            
            # 資料預處理
            strContent = re.sub(r" |\r|\n|　|\s", '', strContent)

            # 決定 txt 的檔案名稱
            fileName = f"{listResult[i]['title']}_{listResult[i]['sub'][j]['sub_title']}.txt"
            
            # 將小說內容存到 txt 中
            with open(f"{folderPath}/{fileName}", "w", encoding="utf-8") as file:
                file.write(strContent)

            # 額外將小說內容放到 list 當中，建立 train.json
            listContent.append(strContent)

    # 延伸之後的教學，在此建立訓練資料
    with open(f"{folderPath}/train.json", "w", encoding="utf-8") as file:
        file.write( json.dumps(listContent, ensure_ascii=False) )

# 主程式
if __name__ == "__main__":
    time1 = time.time()
    getMainLinks()
    getSubLinks()
    saveJson()
    writeTxt()
    print(f"執行總花費時間: {time.time() - time1}")