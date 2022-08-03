# Guess365 LINE BOT 使用手冊
- 提供[Guess365](https://guess365.cc/ "Guess365")用戶多種優質便利服務。例如，加入Line的會員將享有平台預測機器人的即時明牌通知、好手PK等功能。<br/>
- Github : [https://github.com/Guess365/Jake/tree/main/Guess365%20LineBot](https://github.com/Guess365/Jake/tree/main/Guess365%20LineBot)
# 好手PK
會員點擊圖文選單的**好手PK**，會跳出**我要PK**、**戰績查詢**兩種功能，選擇我要PK將會從MLB隨機挑選盤口，並顯示選選單提供會員點選。
![alt text](https://i.imgur.com/IQNnoyY.jpeg)
會員選擇的PK賽事，經由後台排程將回隨機推播給其他用戶，用戶可點選挑戰來激活PK。
<p align="center">
<img src="https://i.imgur.com/u9wtWtE.jpeg"  style="width:320px;"/>
<br/>

當賽果結算後，將會通知PK結果給用戶。
</p>
<p align="center">
<img src="https://i.imgur.com/hBAYpqb.jpeg"  style="width:620px;"/>
<br/>
</p>

# 購買套餐(暫)
會員點擊圖文選單的**查詢訂閱**，會跳出**加值套餐**清單，讓會員購買套餐。
<p align="left">
<img src="https://i.imgur.com/n4igE76.png"  style="width:180px;"/>
<img src="https://i.imgur.com/yc8FRRV.png"  style="width:180px;"/>
<img src="https://i.imgur.com/jsnuOSp.png"  style="width:180px;"/>
</p>

# 預測即時通知服務
```Python
import requests
from requests.auth import HTTPBasicAuth

url = 'http://ecocoapidev1.southeastasia.cloudapp.azure.com/UserMemberSellingPushMessage'
data = {"SubscribeLevels":"free/gold",
        "predict_winrate":"85%",
        "title":"MLB機器人",
        "body_data":"2021賽寄回測|-150000|100過1|1",
        "TournamentText_icon":"https://upload.wikimedia.org/wikipedia/zh/thumb/2/2a/Major_League_Baseball.svg/1200px-Major_League_Baseball.svg.png",
        "body_image":"https://i.imgur.com/uxR7RNP.png",
        "predlist":[
                    {"account":"koer3743",
                    "password":"er3p5eak97",
                    "GroupOptionCode":20,
                    "OptionCode":2,
                    "EventCode":"119890397",
                    "predict_type":"Selling",
                    "HomeOdds":4.5,
                    "AwayOdds":1.1,
                    "HomeConfidence":"30%",
                    "AwayConfidence":"70%"}]}

response = requests.post(url, data = data, auth=HTTPBasicAuth('guess365', 'er3p5eak97'), verify=False).text
```
## JSON參數

參數  | 用途
------------- | -------------
SubscribeLevels | 推播會員範圍(e.g. "free/gold/platinum")
predict_winrate  | 開頭頁-當前預測準確度(e.g. "75%") 
title  | 開頭頁-標題
body_data  | 開頭頁-詳細資料(e.g. "2021賽寄回測|-150000|100過1|1")
TournamentText_icon  | 開頭頁-聯盟LOGO URL
body_image  | 開頭頁-詳細資料圖片
predlist | 每一筆預測
predlist-account  | 帳戶
predlist-password  | 密碼
predlist-GroupOptionCode  | 盤口編號
predlist-OptionCode  | 選擇方
predlist-EventCode  | 賽事編號
predlist-PredictType  | 預測類型('Forecast' or 'Selling')
predlist-HomeOdds  | 自訂主場賠率
predlist-AwayOdds  | 自訂客場賠率
predlist-HomeConfidence  | 自訂主場預測信心度
predlist-AwayConfidence  | 自訂客場預測信心度

## Layout

![alt text](https://i.imgur.com/q00uBaz.png)

# 消息通知服務
網址 : https://ecocoapidev1.southeastasia.cloudapp.azure.com/UserMemberPushMessage <br/>

![alt text](https://i.imgur.com/W55u9Ug.jpeg)
訪問上述網址即可進去Guess365訊息推播功能，功能選項包含**傳送對象**可以選擇特定會員、**選擇貼圖**可以傳送貼圖、**傳輸內容**可以傳送消息內容。
# 預測戰績通知
網址 : https://ecocoapidev1.southeastasia.cloudapp.azure.com/PredictResultsPushMessage <br/>
![alt text](https://i.imgur.com/1YtqXBu.jpeg) <br/>
<p align="center">
<img src="https://i.imgur.com/AZrWY7Z.jpeg"  style="width:320px;"/><br/>
</p>

## 網址參數
參數  | 用途
------------- | -------------
[DateBetween]可選 | 設定推播預測日期範圍(e.g. "2022-5-16~2022-5-18") 預設為昨日 
[member]可選 | 設定推播的會員戰績(e.g. "MA890101,winwin666,adsads2323") 預設為"MA890101,winwin666,adsads2323"
