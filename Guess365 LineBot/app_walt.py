from flask import request, abort, render_template
from linebot import  LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TemplateSendMessage, ConfirmTemplate, MessageTemplateAction, PostbackEvent, MessageEvent, TextMessage, TextSendMessage, BubbleContainer, ImageComponent, BoxComponent, TextComponent, ImageSendMessage,IconComponent, ButtonComponent, SeparatorComponent, FlexSendMessage, URIAction,PostbackAction
from linebot.models import MessageEvent, TextMessage, PostbackEvent, TextSendMessage, TemplateSendMessage, ConfirmTemplate, MessageTemplateAction, ButtonsTemplate, PostbackTemplateAction, URITemplateAction, CarouselTemplate, CarouselColumn, ImageCarouselTemplate, ImageCarouselColumn
from urllib.parse import parse_qsl
import pandas as pd
import numpy as np
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask import Flask, request, jsonify, make_response, redirect, url_for
import json
import traceback
from datetime import datetime, timedelta, timezone
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS
import requests, time
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import quote, quote_plus
import pyodbc
from flask import Flask, flash, redirect, url_for
import random
import pytz
utc = pytz.UTC
import web_config



app = Flask(__name__)
line_bot_api = LineBotApi('m7qBREk83jz41g0bcIftPx/DIQNmSZHZ/Ga6B5BbpkVfalpJmPiU4J08fS7GqL5JF2u9poLdjPfOd/uwkLi4qHh1SJkWnBhokHhOYALpfx89easIBmfRz6SijjLLS/hNnR9CSCl3ypNZX1MN46S9zwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('c96d65cbc79817b766a2defec1dbef48')
liffid = '1657052500-YjkyPLpP'
domain_name = '0d37-220-130-85-186.ngrok.io'
secret_key = 'er3p5eak97'

'''
[1]初始化
'''
db = SQLAlchemy()
CORS(app)
auth = HTTPBasicAuth()
server   = web_config.testing().server
username = web_config.testing().username
password = web_config.testing().password
database = web_config.testing().database
driver   = '/home/linuxbrew/.linuxbrew/lib/libtdsodbc.so'
port     = '1433'

odbc_str = 'DRIVER='+driver+';SERVER='+server+';PORT='+port+';DATABASE='+database+';UID='+username+';PWD='+password
connect_str = 'mssql+pyodbc:///?odbc_connect='+quote_plus(odbc_str)
db.init_app(app)

'''
[2]安全性設定
'''

users = [
    {'username': 'jake', 'password': generate_password_hash('000jk'), 'password_2': '000jk'}
]
@auth.verify_password
def verify_password(username, password):
    for user in users:
        if user['username'] == username:
            if check_password_hash(user['password'], password):
                return True
    return False

'''
[3]推播功能
'''
@app.route("/UserMemberSellingPushMessage", methods=['POST'])
@auth.login_required
def send_UserMemberSellingPushMessage():
    try:
       # 取得會員輸入資料
       data = request.get_json()
       auth_username = auth.username()
       SubscribeLevels = data['SubscribeLevels']
       header=dict(
       predict_winrate = data['predict_winrate'],
       title = data['title'],
       TournamentText_icon = data['TournamentText_icon'],
       body_data=data['body_data'],
       body_image = data['body_image'])

       # 先傳送請求
       response = requests.post('http://192.168.10.177:5000/PredictMatchEntrys/',json=data, auth=(users[0]['username'],users[0]['password_2']),verify=False).text
       print(response)
       response = json.loads(response)
       # 判斷請求是否成功，成功代表資料無誤
       if 'PredictSQL' in response.keys():
            LineBotAutoPredictionLogs = pd.DataFrame(get_LineBotAutoPredictionLog(SubscribeLevels=SubscribeLevels.split('/')))
            if LineBotAutoPredictionLogs.shape[0] > 0:
                LineUniqueIDs = list(set(LineBotAutoPredictionLogs['LineUniqueID']))
                content = f"{response['PredictSQL']}"
                Flex_Message = set_FlexTemplateMessage(content, header)
                print(Flex_Message)
                line_bot_api.multicast(LineUniqueIDs, FlexSendMessage('predict', Flex_Message))
                write_LineBotPushMessage('linebot', auth_username, content, SubscribeLevels)

                return jsonify({'response': f'Successfully pushed to {SubscribeLevels} members.'})
            else:
                return jsonify({'response': 'Successfully pushed, but no matching members.'})
       else:
           return jsonify({'response': [{'Predict API Error Info': response['response']}]})
    except:
        return jsonify({'response': [{'Error Info': traceback.format_exc()}]})


@app.route("/UserMemberPushMessage", methods=['GET','POST'])
@auth.login_required
def send_UserMemberPushMessage():
    auth_username = auth.username()
    LineUserMembers = get_LineUserMember()
    if request.method == 'POST':
        content = request.form['content']
        user_select = request.form['user_select']
        selected_icon_text = request.form['selected-text']
        if content != '' and selected_icon_text != '-1':
            if user_select == '所有人':
                user_select = pd.DataFrame(LineUserMembers)
                user_select = list(user_select['LineUniqueID'])
                if len(user_select) > 0:
                    line_bot_api.multicast(user_select, [TextSendMessage(text=content),
                                                         ImageSendMessage(original_content_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg',
                                                                          preview_image_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg')])
                    write_LineBotPushMessage('manual', auth_username, content ,'all')
                    flash('傳送成功(文字+貼圖)')
                else:
                    flash('沒有用戶')
            elif user_select == 'Level-1用戶':
                user_select = pd.DataFrame(LineUserMembers)
                user_select = list(user_select[user_select['Level']==1]['LineUniqueID'])
                if len(user_select) > 0:
                    line_bot_api.multicast(user_select, [TextSendMessage(text=content),
                                                         ImageSendMessage(original_content_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg',
                                                                          preview_image_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg')])
                    write_LineBotPushMessage('manual', auth_username, content,'Level-1')
                    flash('傳送成功(文字+貼圖)')
                else:
                    flash('沒有用戶')
            else:
                user_select = json.loads(user_select.replace('\'','\"'))['LineUniqueID']
                line_bot_api.multicast([user_select], [TextSendMessage(text=content),
                                                       ImageSendMessage(original_content_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg',
                                                                        preview_image_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg')])
                write_LineBotPushMessage('manual', auth_username, content,user_select)
                flash('傳送成功(文字+貼圖)')
        elif content != '' and selected_icon_text == '-1':
            if user_select == '所有人':
                user_select = pd.DataFrame(LineUserMembers)
                user_select = list(user_select['LineUniqueID'])
                if len(user_select) > 0:
                    line_bot_api.multicast(user_select, TextSendMessage(text=content))
                    write_LineBotPushMessage('manual', auth_username, content,'all')
                    flash('傳送成功(文字)')
                else:
                    flash('沒有用戶')
            elif user_select == 'Level-1用戶':
                user_select = pd.DataFrame(LineUserMembers)
                user_select = list(user_select[user_select['Level']==1]['LineUniqueID'])
                if len(user_select) > 0:
                    line_bot_api.multicast(user_select, TextSendMessage(text=content))
                    write_LineBotPushMessage('manual', auth_username, content,'Level-1')
                    flash('傳送成功(文字)')
                else:
                    flash('沒有用戶')
            else:
                user_select = json.loads(user_select.replace('\'','\"'))['LineUniqueID']
                line_bot_api.multicast([user_select], TextSendMessage(text=content))
                write_LineBotPushMessage('manual', auth_username, content,user_select)
                flash('傳送成功(文字)')
        elif content == '' and selected_icon_text != '-1':
            if user_select == '所有人':
                user_select = pd.DataFrame(LineUserMembers)
                user_select = list(user_select['LineUniqueID'])
                if len(user_select) > 0:
                    line_bot_api.multicast(user_select, ImageSendMessage(original_content_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg',
                                                                         preview_image_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg'))
                    write_LineBotPushMessage('manual', auth_username, content,'all')
                    flash('傳送成功(貼圖)')
                else:
                    flash('沒有用戶')
            elif user_select == 'Level-1用戶':
                user_select = pd.DataFrame(LineUserMembers)
                user_select = list(user_select[user_select['Level']==1]['LineUniqueID'])
                if len(user_select) > 0:
                    line_bot_api.multicast(user_select, ImageSendMessage(original_content_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg',
                                                                         preview_image_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg'))
                    write_LineBotPushMessage('manual', auth_username, content,'Level-1')
                    flash('傳送成功(貼圖)')
                else:
                    flash('沒有用戶')
            else:
                user_select = json.loads(user_select.replace('\'','\"'))['LineUniqueID']
                line_bot_api.multicast([user_select], ImageSendMessage(original_content_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg',
                                                        preview_image_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg'))
                write_LineBotPushMessage('manual', auth_username, content,user_select)
                flash('傳送成功(貼圖)')
        else:
            flash('傳送失敗，請填寫文字或貼圖')
        return render_template('Sellings.html',**locals())
    return render_template('Sellings.html',**locals())

@app.route("/PredictResultsPushMessage", methods=['GET','POST'])
@auth.login_required
def send_PredictResultsPushMessage():
    # 取得驗證帳戶、LineId
    auth_username = auth.username()
    LineUserMembers = get_LineUserMember()

    if request.method == 'GET':
        # 檢查是否有填寫參數
        accounts = request.values.get('member')
        DateBetween = request.values.get('DateBetween')
        # 沒填寫accounts，則賦予預設值
        if accounts == None:
            accounts = 'MA890101,winwin666,adsads2323'
        # DateBetween，則使用無指定路由
        if DateBetween == None:
            PredictResults = requests.get(f'http://192.168.10.177:5000/PredictResults/{accounts}', auth=(users[0]['username'],users[0]['password_2']),verify=False).text
            PredictResults = json.loads(PredictResults)['responese']
        else:
            PredictResults = requests.get(f'http://192.168.10.177:5000/PredictResults/{accounts}/{DateBetween}', auth=(users[0]['username'],users[0]['password_2']),verify=False).text
            PredictResults = json.loads(PredictResults)['responese']

        return render_template('Predict.html', **locals())

    elif request.method == 'POST':
        content = request.form['content']
        user_select = request.form['user_select']
        selected_icon_text = request.form['selected-text']
        predict_content = request.form['predict_content']
        if content != '' and selected_icon_text != '-1':
            if user_select == '所有人':
                user_select = pd.DataFrame(LineUserMembers)
                user_select = list(user_select['LineUniqueID'])
                if len(user_select) > 0:
                    line_bot_api.multicast(user_select, [TextSendMessage(text=content),
                                                         ImageSendMessage(original_content_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg',
                                                                          preview_image_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg'),
                                                         FlexSendMessage('set_PredictResults',set_PredictResultsFlex(predict_content))])
                    write_LineBotPushMessage('manual', auth_username, content ,'all')
                    flash('傳送成功(文字+貼圖)')
                else:
                    flash('沒有用戶')
            elif user_select == 'Level-1用戶':
                user_select = pd.DataFrame(LineUserMembers)
                user_select = list(user_select[user_select['Level']==1]['LineUniqueID'])
                if len(user_select) > 0:
                    line_bot_api.multicast(user_select, [TextSendMessage(text=content+'\n'+predict_content),
                                                         ImageSendMessage(original_content_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg',
                                                                          preview_image_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg'),
                                                         FlexSendMessage('set_PredictResults',set_PredictResultsFlex(predict_content))])
                    write_LineBotPushMessage('manual', auth_username, content,'Level-1')
                    flash('傳送成功(文字+貼圖)')
                else:
                    flash('沒有用戶')
            else:
                user_select = json.loads(user_select.replace('\'','\"'))['LineUniqueID']
                line_bot_api.multicast([user_select], [TextSendMessage(text=content+'\n'+predict_content),
                                                       ImageSendMessage(original_content_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg',
                                                                        preview_image_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg'),
                                                       FlexSendMessage('set_PredictResults',set_PredictResultsFlex(predict_content))])
                write_LineBotPushMessage('manual', auth_username, content,user_select)
                flash('傳送成功(文字+貼圖)')
        elif content != '' and selected_icon_text == '-1':
            if user_select == '所有人':
                user_select = pd.DataFrame(LineUserMembers)
                user_select = list(user_select['LineUniqueID'])
                if len(user_select) > 0:
                    line_bot_api.multicast(user_select, [TextSendMessage(text=content),
                                                         FlexSendMessage('set_PredictResults',set_PredictResultsFlex(predict_content))])
                    write_LineBotPushMessage('manual', auth_username, content,'all')
                    flash('傳送成功(文字)')
                else:
                    flash('沒有用戶')
            elif user_select == 'Level-1用戶':
                user_select = pd.DataFrame(LineUserMembers)
                user_select = list(user_select[user_select['Level']==1]['LineUniqueID'])
                if len(user_select) > 0:
                    line_bot_api.multicast(user_select, [TextSendMessage(text=content),
                                                         FlexSendMessage('set_PredictResults',set_PredictResultsFlex(predict_content))])
                    write_LineBotPushMessage('manual', auth_username, content,'Level-1')
                    flash('傳送成功(文字)')
                else:
                    flash('沒有用戶')
            else:
                user_select = json.loads(user_select.replace('\'','\"'))['LineUniqueID']
                line_bot_api.multicast([user_select], [TextSendMessage(text=content),
                                                     FlexSendMessage('set_PredictResults',set_PredictResultsFlex(predict_content))])
                write_LineBotPushMessage('manual', auth_username, content,user_select)
                flash('傳送成功(文字)')
        elif content == '' and selected_icon_text != '-1':
            if user_select == '所有人':
                user_select = pd.DataFrame(LineUserMembers)
                user_select = list(user_select['LineUniqueID'])
                if len(user_select) > 0:
                    line_bot_api.multicast(user_select, [ImageSendMessage(original_content_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg',
                                                                            preview_image_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg'),
                                                         FlexSendMessage('set_PredictResults',set_PredictResultsFlex(predict_content))])
                    flash('傳送成功(貼圖)')
                else:
                    flash('沒有用戶')
            elif user_select == 'Level-1用戶':
                user_select = pd.DataFrame(LineUserMembers)
                user_select = list(user_select[user_select['Level']==1]['LineUniqueID'])
                if len(user_select) > 0:
                    line_bot_api.multicast(user_select, [ImageSendMessage(original_content_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg',
                                                                            preview_image_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg'),
                                                         FlexSendMessage('set_PredictResults',set_PredictResultsFlex(predict_content))])
                    write_LineBotPushMessage('manual', auth_username, content,'Level-1')
                    flash('傳送成功(貼圖)')
                else:
                    flash('沒有用戶')
            else:
                user_select = json.loads(user_select.replace('\'','\"'))['LineUniqueID']
                line_bot_api.multicast([user_select], [ImageSendMessage(original_content_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg',
                                                                            preview_image_url=f'https://{domain_name}/static/sticker/{selected_icon_text}.jpg'),
                                                       FlexSendMessage('set_PredictResults',set_PredictResultsFlex(predict_content))])
                write_LineBotPushMessage('manual', auth_username, content,user_select)
                flash('傳送成功(貼圖)')
        else:

            flash('傳送失敗，請填寫文字或貼圖')

        return redirect(url_for('send_PredictResultsPushMessage')+request.form['parameter'])

'''
[4]登入功能
'''
#LIFF靜態頁面
@app.route('/page')
def page():
    auth_username = users[0]['username']
    auth_password = users[0]['password_2']
    return render_template('index.html',liffid = liffid, domain_name=domain_name, username=auth_username,  password=auth_password)

@app.route('/login', methods=['POST'])
@auth.login_required
def Login():
    data = request.get_json()
    text = data.get('text')
    response = manageForm(text)
    return jsonify({'response':response})

'''
[5]LineBot訊息回覆設定
'''
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    newLineUniqueID = event.source.user_id
    mtext = event.message.text

    if mtext == '@登入會員':
        LoginOptionCarousel(event, newLineUniqueID)
    elif mtext == '@關於我':
        UserMemberInfo = get_UserMemberInfo(newLineUniqueID)
        set_UserMemberInfo(event, UserMemberInfo )
    elif mtext == '@加值套餐':
        PaymentOptionCarousel(event)
    elif mtext == '@好手PK':
        LinePlayerPKCarousel(event)
    elif mtext == '@我要PK':
        plays = get_PlayerPKGame()
        set_PlayerPKFlexTemplateMessage(event=event,plays=plays)
    elif mtext == '@查詢戰績':
        UserMemberInfo = get_UserMemberInfo(newLineUniqueID)
        get_PlayerPKStandings(UserMemberInfo['UserId'], event)
    else:
        write_ReplyMessage(mtext, newLineUniqueID)

@handler.add(PostbackEvent)
def handle_postback(event):
    newLineUniqueID = event.source.user_id

    backdata = dict(parse_qsl(event.postback.data))
    print(backdata)
    payment = backdata.get('@加值套餐')
    pkselect = backdata.get('@PK選擇')
    pkinviteselect = backdata.get('@PK邀請選擇')
    if payment:
        UserMemberInfo = get_UserMemberInfo(newLineUniqueID)
        if UserMemberInfo['UserId'] != None:
            add_LineBotAutoPrediction(UserMemberInfo['UserId'],payment)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='成功購買！'))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='請先登入！'))
    elif pkselect:
        UserMemberInfo = get_UserMemberInfo(newLineUniqueID)
        if UserMemberInfo['UserId'] != None:
            data = json.loads(pkselect.replace('[','{').replace(']','}').replace('\'','\"'))
            isSuccess = add_LinePlayerPK(UserMemberInfo['UserId'],data,event)
            if isSuccess:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='隨機挑選對手中!'))

        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='請先登入！'))
    elif pkinviteselect:
        UserMemberInfo = get_UserMemberInfo(newLineUniqueID)
        if UserMemberInfo['UserId'] != None:
            print(pkinviteselect)
            print(pkinviteselect.replace('[','{').replace(']','}').replace('\'','\"'))

            data = json.loads(pkinviteselect.replace('[','{').replace(']','}').replace('\'','\"'))

            isSuccess = update_invite_LinePlayerPK(UserMemberInfo['UserId'],data,event)
            if isSuccess:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='成功登入挑戰!'))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='請先登入！'))
def set_UserMemberInfo(event, UserMemberInfo):
    FlexMessage = json.load(open('static/Flex.json', 'r', encoding='utf-8'))
    # koer3741(kobe廟報明牌)
    FlexMessage['body']['contents'][0]['contents'][0]['contents'][0]['text'] = f"{UserMemberInfo['member']}({UserMemberInfo['nickname']})"
    # 訂閱等級 : 鑽石
    FlexMessage['body']['contents'][0]['contents'][0]['contents'][1]['text'] = f"訂閱等級 : {UserMemberInfo['SubscribeLevel']}"
    # 訂閱時間:2022/5/10~2022/8/10
    FlexMessage['body']['contents'][0]['contents'][0]['contents'][2]['text'] = f"訂閱時間:{UserMemberInfo['SubscribeStart_dd']}~{UserMemberInfo['SubscribeEnd_dd']}"
    # 已付款(2022/8/5)
    FlexMessage['body']['contents'][0]['contents'][0]['contents'][3]['text'] = f"{UserMemberInfo['Payment_dd']}({UserMemberInfo['isPayment']})"

    line_bot_api.reply_message(event.reply_token, FlexSendMessage('profile', FlexMessage))

def LinePlayerPKCarousel(event):
    try:
        message = TemplateSendMessage(
            alt_text='好手PK選單',
            template=ImageCarouselTemplate(
                columns=[
                    ImageCarouselColumn(
                        image_url=f'https://i.imgur.com/skF2dBb.png',
                        action=MessageTemplateAction(
                            text='@我要PK'
                        )
                    ),
                    ImageCarouselColumn(
                        image_url=f'https://i.imgur.com/LH6xrN6.png',
                        action=MessageTemplateAction(
                            text='@查詢戰績'
                        )
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

def PaymentOptionCarousel(event):
    try:
        message = TemplateSendMessage(
            alt_text='加值選單',
            template=ImageCarouselTemplate(
                columns=[
                    ImageCarouselColumn(
                        image_url=f'https://i.imgur.com/n4igE76.png',
                        action=PostbackTemplateAction(
                            data='@加值套餐=free'
                        )
                    ),
                    ImageCarouselColumn(
                        image_url=f'https://i.imgur.com/yc8FRRV.png',
                        action=PostbackTemplateAction(
                            data='@加值套餐=gold'
                        )
                    ),
                    ImageCarouselColumn(
                    image_url=f'https://i.imgur.com/jsnuOSp.png',
                    action=PostbackTemplateAction(
                            data='@加值套餐=platinum'
                        )
                    )
                ]

            )
        )
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

def LoginOptionCarousel(event, LineUniqueID):  # 圖片轉盤
    try:
        newLineUniqueID, UserId = get_LineUserMember(LineUniqueID=LineUniqueID)
        if newLineUniqueID == None and UserId == None :
            message = TemplateSendMessage(
                alt_text='登入會員選單',
                template=ImageCarouselTemplate(
                    columns=[
                        ImageCarouselColumn(
                            image_url=f'https://i.imgur.com/4VnQlzK.png',
                            action=URITemplateAction(uri='https://liff.line.me/'+liffid)
                        ),
                        ImageCarouselColumn(
                            image_url=f'https://i.imgur.com/Its5kYL.png',
                            action=MessageTemplateAction(
                                text='@關於我'
                            )
                        )
                    ]
                )
            )
        else:
            message = TemplateSendMessage(
                alt_text='登入會員選單',
                template=ImageCarouselTemplate(
                    columns=[
                        ImageCarouselColumn(
                            image_url=f'https://i.imgur.com/83WDsfv.png',
                            action=MessageTemplateAction(
                                text='@已經登入'
                            )
                        ),
                        ImageCarouselColumn(
                            image_url=f'https://i.imgur.com/Its5kYL.png',
                            action=MessageTemplateAction(
                                text='@關於我'
                            )
                        )
                    ]
                )
            )
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

def manageForm(mtext):
    try:
        flist = mtext[3:].split('/')
        account = flist[0]
        password = flist[1]
        newLineUniqueID = flist[2]
        UserId = get_UserMember(account, password)[0]
        LineUniqueID_1 = get_LineUserMember(UserId=UserId)[0]
        LineUniqueID_2 = get_LineUserMember(LineUniqueID=newLineUniqueID)[0]
        print(LineUniqueID_1,LineUniqueID_2)
        # 用戶登入後，將LineID與帳號綁定，並寫入LineUserMember
        if UserId and LineUniqueID_1 == None and LineUniqueID_2 == None:
            add_LineUserMember(UserId, newLineUniqueID)
            return "成功登入會員"
        elif UserId and LineUniqueID_1 != None and LineUniqueID_2 != None :
            return "error_1"
        elif UserId and LineUniqueID_1 != None and LineUniqueID_2 == None :
            return "error_2"
        elif UserId and LineUniqueID_1 == None and LineUniqueID_2 != None :
            return "error_1"
        else:
            return "error_3"
    except:
        traceback.print_exc()
        return "error_4"
'''
[6]資料庫存取
'''
# 檢查是否有會員,存在則回傳UserId，反之回傳None
def get_UserMember( account=None, password=None, UserId=None):
    try:
        if account != None and password != None:
            print(f"select * from UserMember where member = '{account}' and Password = '{password}' ")
            result = dict(db.engine.execute(f"select * from UserMember where member = '{account}' and Password = '{password}' ").mappings().one())
            return result['UserId'], result['member'], result['nickname']
        elif UserId != None:
            print(f"select * from UserMember where UserId = '{UserId}' ")
            result = dict(db.engine.execute(f"select * from UserMember where UserId = '{UserId}' ").mappings().one())

            return result['UserId'], result['member'], result['nickname']
    except:
        return [None,None,None]

# isBind = True，檢查會員是否有登入,存在則回傳LineUniqueID，反之回傳None
# isBind = False，檢查會員是否已經有加入官方Line,存在則回傳LineUniqueID，反之回傳None
def get_LineUserMember(UserId=None,LineUniqueID=None):
    if UserId:
        try:
            print(f"select * from LineUserMember where UserId = '{UserId}' ")
            result = dict(db.engine.execute(f"select * from [dbo].[LineUserMember] where [UserId] = '{UserId}' ").mappings().one())
            return result['LineUniqueID'],result['UserId']
        except:
            return [None,None]
    elif LineUniqueID:
        try:
            print(f"select * from LineUserMember where LineUniqueID = '{LineUniqueID}' ")
            result = dict(db.engine.execute(f"select * from [dbo].[LineUserMember] where [LineUniqueID] = '{LineUniqueID}' ").mappings().one())
            return result['LineUniqueID'],result['UserId']
        except:
            return [None,None]
    else:
        try:
            print(f"select * from LineUserMember ")
            result = db.engine.execute(f"select * from [dbo].[LineUserMember] ").mappings().all()
            for idx in range(len(result)):
                result[idx] = dict(result[idx])
            return result
        except:
            return []


def add_LineUserMember(UserId, newLineUniqueID):
    Insert_SQL = f"INSERT INTO [dbo].[LineUserMember] ([LineUniqueID],[Level],[UserId]) VALUES('{newLineUniqueID}','{0}','{UserId}')"
    print(Insert_SQL)
    db.engine.execute(Insert_SQL)

def get_LineBotAutoPredictionLog(UserId=None, SubscribeLevels=[], all = 0):
    if UserId!=None and all==0:
        try:
            SQL = f"select Top 1 * from LineBotAutoPrediction where [UesrId] = '{UserId}' order by SubscribeStart_dd desc"
            print(SQL)
            result = dict(db.engine.execute(SQL).mappings().one())
            return result['UesrId'], result['SubscribeLevel'], result['SubscribeStart_dd'], result['SubscribeEnd_dd'], result['isPayment'], result['Payment_dd']
        except:
            traceback.print_exc()
            return [None, None, None, None, None, None]
    elif SubscribeLevels!=[]:
        try:
            SQL = f''' SELECT　SubscribeLevel, LineUniqueID FROM LineBotAutoPrediction
                       inner join LineUserMember on  LineBotAutoPrediction.UesrId = LineUserMember.UserId
                       where SubscribeLevel　in ({str(SubscribeLevels).replace('[','').replace(']','')}) and isPayment = 'Yes' and SubscribeEnd_dd > '{datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000')}'
                       order by Payment_dd desc'''
            print(SQL)
            results = db.engine.execute(SQL).mappings().all()
            for idx in range(len(results)):
                results[idx] = dict(results[idx])
            return results
        except:
            traceback.print_exc()
            return []
    elif UserId!=None and all==1:
        try:
            SQL = f"select * from LineBotAutoPrediction where [UesrId] = '{UserId}' and isPayment='Yes' order by SubscribeStart_dd desc"
            print(SQL)
            results = db.engine.execute(SQL).mappings().all()
            for idx in range(len(results)):
                results[idx] = dict(results[idx])
            return results
        except:
            traceback.print_exc()
            return []


def get_UserMemberInfo(LineUniqueID):
    newLineUniqueID,UserId = get_LineUserMember(LineUniqueID=LineUniqueID)
    # 若newLineUniqueID,UserId都存在，代表已經登入
    if newLineUniqueID and UserId:
        UserMember = get_UserMember(UserId=UserId)
        LineBotAutoPrediction = get_LineBotAutoPredictionLog(UserId)
        return dict(LineUniqueID=newLineUniqueID,
             UserId=UserId,
             member=UserMember[1],
             nickname=UserMember[2],
             SubscribeLevel=LineBotAutoPrediction[1],
             SubscribeStart_dd=LineBotAutoPrediction[2],
             SubscribeEnd_dd=LineBotAutoPrediction[3],
             isPayment=LineBotAutoPrediction[4],
             Payment_dd=LineBotAutoPrediction[5])
    else:
        return dict(LineUniqueID=None,
             UserId=None,
             member=None,
             nickname=None,
             SubscribeLevel=None,
             SubscribeStart_dd=None,
             SubscribeEnd_dd=None,
             isPayment=None,
             Payment_dd=None)

def add_LineBotAutoPrediction(UesrId,SubscribeLevel):
    SubscribeStart_dd = datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000')
    SubscribeEnd_dd = (datetime.now().astimezone(timezone(timedelta(hours=8)))+timedelta(days=30)).replace(hour=23,minute=59,second=59).strftime('%Y-%m-%d %H:%M:%S.000')
    Payment_dd = SubscribeStart_dd
    isPayment = 'Yes'
    # 檢查當前付費紀錄，如果有則把Payment設成No
    if len(get_LineBotAutoPredictionLog(UserId=UesrId, all=1))>0:
        Update_SQL = f'''UPDATE  [dbo].[LineBotAutoPrediction] SET [isPayment]='No' WHERE UesrId = '{UesrId}' '''
        print(Update_SQL)
        db.engine.execute(Update_SQL)
    Insert_SQL = f'''INSERT INTO [dbo].[LineBotAutoPrediction] ([SubscribeLevel],[SubscribeStart_dd],[SubscribeEnd_dd],[isPayment],[Payment_dd],[UesrId]) 
    VALUES(N'{SubscribeLevel}','{SubscribeStart_dd}','{SubscribeEnd_dd}','{isPayment}','{Payment_dd}','{UesrId}') '''
    print(Insert_SQL)
    db.engine.execute(Insert_SQL)

def write_ReplyMessage(content, LineUniqueID):
    content = r"%s"%content
    Insert_SQL = f"INSERT INTO [dbo].[LineUserMemberReplyMessage] ([Content],[dd],[LineUniqueID]) VALUES(N'{content}','{datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000')}','{LineUniqueID}')"
    print(Insert_SQL)
    db.engine.execute(Insert_SQL)

def write_LineBotPushMessage(type,from_account,content,target_users):
    content = r"%s"%content
    content = content.replace('\'', '\"')
    Insert_SQL = f"INSERT INTO [dbo].[LineBotPushMessage] ([Content],[type],[from_account],[target_users],[dd]) VALUES(N'{content}','{type}','{from_account}','{target_users}','{datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000')}')"
    print(Insert_SQL)
    db.engine.execute(Insert_SQL)

def set_FlexTemplateMessage(content,header):
    PredictCarouselFlex = json.load(open('static/PredictCarouselFlex.json', 'r', encoding='utf-8'))
    teamlogos = pd.read_csv('static/teamlogos.csv',encoding='big5')
    '''
    編輯開頭頁
    '''
    # LOGO
    PredictCarouselFlex['contents'][0]['body']['contents'][0]['contents'][0]['url']=header['TournamentText_icon']
    # 準確度標題-1
    PredictCarouselFlex['contents'][0]['body']['contents'][1]['contents'][0]['contents'][0]['text']=header['title']
    # 準確度標題-2
    PredictCarouselFlex['contents'][0]['body']['contents'][1]['contents'][1]['contents'][0]['text']=header['predict_winrate']
    # 準確度值
    PredictCarouselFlex['contents'][0]['body']['contents'][2]['contents'][0]['width']=header['predict_winrate']
    # 4個值
    body_data = header['body_data'].split("|")
    PredictCarouselFlex['contents'][0]['body']['contents'][3]['contents'][0]['text']=body_data[0]
    PredictCarouselFlex['contents'][0]['body']['contents'][3]['contents'][1]['contents'][0]['contents'][1]['text']=body_data[1]
    PredictCarouselFlex['contents'][0]['body']['contents'][3]['contents'][2]['contents'][0]['contents'][1]['text']=body_data[2]
    PredictCarouselFlex['contents'][0]['body']['contents'][3]['contents'][3]['contents'][0]['contents'][1]['text']=body_data[3]
    # 回測圖
    PredictCarouselFlex['contents'][0]['body']['contents'][4]['contents'][0]['url']=header['body_image']
    '''
    編輯預測頁
    '''
    PredictFlexs = []
    for subtext in content.split('------------------')[:-1]:
        PredictFlex = json.load(open('static/PredictFlex.json', 'r', encoding='utf-8'))
        s = subtext.find('{')
        e = subtext.find('}')
        pred = json.loads(subtext[s:e+1].replace('\'','\"'))
        # 開賽時間
        PredictFlex['body']['contents'][0]['contents'][0]['contents'][0]['text']='開賽時間：'+pred['MatchTime']
        # 主隊LOGO
        PredictFlex['body']['contents'][1]['contents'][0]['contents'][0]['url']=\
            teamlogos[teamlogos['name']==pred['HomeTeam']].iloc[0,3]  if len(teamlogos[teamlogos['name']==pred['HomeTeam']])>0 else 'https://i.imgur.com/x31phAh.jpeg'
        # 主隊名稱
        PredictFlex['body']['contents'][2]['contents'][0]['contents'][0]['text']=pred['HomeTeam']
        # 主隊賠率
        PredictFlex['body']['contents'][4]['contents'][0]['contents'][0]['text']=pred['Odds'][0]
        # 主隊勝率
        PredictFlex['body']['contents'][5]['contents'][0]['contents'][0]['text']=pred['Confidence'][0]

        # 客隊LOGO
        PredictFlex['body']['contents'][1]['contents'][2]['contents'][0]['url'] = \
            teamlogos[teamlogos['name']==pred['AwayTeam']].iloc[0,3]  if len(teamlogos[teamlogos['name']==pred['AwayTeam']])>0 else 'https://i.imgur.com/x31phAh.jpeg'
        # 客隊名稱
        PredictFlex['body']['contents'][2]['contents'][1]['contents'][0]['text']=pred['AwayTeam']
        # 客隊賠率
        PredictFlex['body']['contents'][4]['contents'][2]['contents'][0]['text']=pred['Odds'][1]
        # 客隊勝率
        PredictFlex['body']['contents'][5]['contents'][2]['contents'][0]['text']=pred['Confidence'][1]

        # 信心度條
        PredictFlex['body']['contents'][6]['contents'][0]['width'] = pred['Confidence'][0]
        # 盤口
        PredictFlex['body']['contents'][3]['contents'][0]['text']="🏁"+pred['GroupOptionName'].strip()
        # 預測
        PredictFlex['body']['contents'][7]['contents'][0]['contents'][1]['text']=pred['OptionCode'].strip()
        PredictFlexs.append(PredictFlex)
    '''
    串接
    '''
    PredictCarouselFlex['contents'] = PredictCarouselFlex['contents'] + PredictFlexs
    return PredictCarouselFlex

def get_Quotations():
    SQL = "SELECT * From LinePKQuotations"
    results = db.engine.execute(SQL).mappings().all()
    for idx in range(len(results)):
        results[idx] = dict(results[idx])  # 將 Mapping 轉型為 dict
    results = pd.DataFrame(results)
    return list(results['Quotation'])

def set_PlayerPKFlexTemplateMessage(plays,event):
    try:
        corpus = get_Quotations()

        teamlogos = pd.read_csv('static/teamlogos.csv', encoding='big5')
        Carousel = {
            "type": "carousel",
            "contents": [
                {
                  "type": "bubble",
                  "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                      {
                        "type": "image",
                        "url": "https://i.imgur.com/gbrKQji.jpeg",
                        "size": "full",
                        "aspectMode": "cover",
                        "aspectRatio": "2:3.5",
                        "gravity": "top"
                      }
                    ],
                    "paddingAll": "0px"
                  }
                }
            ]
        }
        for play in plays:
            LinePlayerPKFlex_self = json.load(open('static/LinePlayerPKFlex_self.json', 'r', encoding='utf-8'))
            # 比賽時間
            LinePlayerPKFlex_self['body']['contents'][0]['contents'][0]['contents'][0]['text'] = play['MatchTime'][:-7]
            # 主隊名稱
            LinePlayerPKFlex_self['body']['contents'][2]['contents'][0]['contents'][0]['text'] = play['HomeTeam'][1]
            # 主隊徽
            LinePlayerPKFlex_self['body']['contents'][1]['contents'][0]['contents'][0]['url'] = \
                teamlogos[teamlogos['name']==play['HomeTeam'][1]].iloc[0,3]  if len(teamlogos[teamlogos['name']==play['HomeTeam'][1]])>0 else 'https://i.imgur.com/x31phAh.jpeg'
            # 客隊名稱
            LinePlayerPKFlex_self['body']['contents'][2]['contents'][1]['contents'][0]['text'] = play['AwayTeam'][1]
            # 客隊徽
            LinePlayerPKFlex_self['body']['contents'][1]['contents'][2]['contents'][0]['url'] = \
                teamlogos[teamlogos['name']==play['AwayTeam'][1]].iloc[0,3]  if len(teamlogos[teamlogos['name']==play['AwayTeam'][1]])>0 else 'https://i.imgur.com/x31phAh.jpeg'
            # 盤口
            LinePlayerPKFlex_self['body']['contents'][3]['contents'][0]['text'] = \
                "🏁 "+get_TypeCname(play['SportCode'], play['odds'][0]['GroupOptionCode'])
            # 賠率
            LinePlayerPKFlex_self['body']['contents'][4]['contents'][0]['contents'][0]['text']  = play['odds'][0]['OptionRate'] # 主
            LinePlayerPKFlex_self['body']['contents'][4]['contents'][2]['contents'][0]['text']  = play['odds'][1]['OptionRate'] # 客
            # 下狠話
            LinePlayerPKFlex_self['body']['contents'][7]['contents'][0]['text'] = corpus[random.randint(0,len(corpus)-1)].strip()
            # LABEL
            LinePlayerPKFlex_self['footer']['contents'][0]['action']['label']  = \
                Mapping_OptionCode(play['odds'][0]['OptionCode'] , play['SportCode'], play['odds'][0]['GroupOptionCode'], play['HomeTeam'][1], play['AwayTeam'][1])
            LinePlayerPKFlex_self['footer']['contents'][1]['action']['label']  = \
                Mapping_OptionCode(play['odds'][1]['OptionCode'], play['SportCode'], play['odds'][0]['GroupOptionCode'],play['HomeTeam'][1], play['AwayTeam'][1])
            # ACTION
            LinePlayerPKFlex_self['footer']['contents'][0]['action']['data']  = \
                f'''@PK選擇=['EventCode':'{play['EventCode']}','OptionCode':'{play['odds'][0]['OptionCode']}','GroupOptionCode':'{play['odds'][0]['GroupOptionCode']}','HomeOdds':'{play['odds'][0]['OptionRate']}','AwayOdds':'{play['odds'][1]['OptionRate']}','SpecialBetValue':'{play['odds'][0]['SpecialBetValue']}']''' # 主
            LinePlayerPKFlex_self['footer']['contents'][1]['action']['data']  = \
                f'''@PK選擇=['EventCode':'{play['EventCode']}','OptionCode':'{play['odds'][1]['OptionCode']}','GroupOptionCode':'{play['odds'][0]['GroupOptionCode']}','HomeOdds':'{play['odds'][0]['OptionRate']}','AwayOdds':'{play['odds'][1]['OptionRate']}','SpecialBetValue':'{play['odds'][0]['SpecialBetValue']}']''' # 客
            Carousel["contents"] += [LinePlayerPKFlex_self]

        if len(plays)>0:
            print(Carousel)
            line_bot_api.reply_message(event.reply_token, FlexSendMessage("PK",Carousel))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage("目前沒有提供PK項目"))
    except:
        traceback.print_exc()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))


def get_PlayerPKStandings(UserId, event):
    Standings = {'勝': 0, '敗': 0, '未開賽': 0}

    SQL = f''' SELECT Result　FROM [GoHit].[dbo].[LinePlayerPK] where  UserId1 = '{UserId}' '''
    results = db.engine.execute(SQL).mappings().all()
    for result in results:
        if result['Result'] == 'UserId1':
            Standings['勝'] +=1
        if result['Result'] == 'UserId2':
            Standings['敗'] +=1
        if result['Result'] == None:
            Standings['未開賽'] +=1

    SQL = f''' SELECT Result　FROM [GoHit].[dbo].[LinePlayerPK] where  UserId2 = '{UserId}' '''
    results = db.engine.execute(SQL).mappings().all()
    for result in results:
        if result['Result'] == 'UserId2':
            Standings['勝'] +=1
        if result['Result'] == 'UserId1':
            Standings['敗'] +=1
        if result['Result'] == None:
            Standings['未開賽'] +=1

    line_bot_api.reply_message(event.reply_token, TextSendMessage(f"{Standings['勝']}勝{Standings['敗']}敗"))

def get_PlayerPKGame():
    try:
        # https://ecocoapidev1.southeastasia.cloudapp.azure.com/MatchEntryInfo/DateBetween/NBA/any
        MatchEntrys = requests.get('http://192.168.10.177:5000/MatchEntryInfo/DateBetween/MLB/any',verify=False, auth=(users[0]['username'],users[0]['password_2'])).text
        MatchEntrys = json.loads(MatchEntrys)['response']
        random.shuffle(MatchEntrys)
        play_num = len(MatchEntrys)
        plays = []
        c = 0
        for idx in range(play_num):
            if MatchEntrys[idx]['TournamentText'] == 'MLB':
                GroupOptionCodeList = ['20','228','60']
                random.shuffle(GroupOptionCodeList)
                for GroupOptionCode in GroupOptionCodeList:
                    odds_list = []
                    for odds in MatchEntrys[idx]['odds']:
                        if str(odds['GroupOptionCode']) == str(GroupOptionCode):
                            odds_list += [odds]
                    if 4>c and odds_list != []:
                        temp = MatchEntrys[idx].copy()
                        temp['odds'] = odds_list
                        plays.append(temp)
                        c+=1
                        if c == random.randint(1,4-1):
                            break
        return plays
    except:
        traceback.print_exc()
        return []

def get_TypeCname(SportCode,GroupOptionCode):
    sql = f'''SELECT [SportCode],[Type],[Type_cname],[Play_Name],[GroupOptionCode1] FROM [dbo].[GroupOptionCode] 
                where [SportCode]='{SportCode}' and  GroupOptionCode1='{GroupOptionCode}' '''
    results = db.engine.execute(sql).mappings().all()
    for idx in range(len(results)):
        results[idx] = dict(results[idx])  # 將 Mapping 轉型為 dict
    if len(results)>0:
        return results[0]['Type_cname']
    else:
        return None

def Mapping_OptionCode(OptionCode,SportCode,GroupOptionCode,HomeTeam,AwayTeam):
    if SportCode == '1' and GroupOptionCode in ('55'):
        texts = [OptionCode.split('/')[0].strip(), OptionCode.split('/')[1].strip()]
        if not texts[0] == 'Draw' and not texts[1] == 'Draw':
            return '平手'
        elif not texts[0] == 'Draw' and texts[1] == 'Draw':
            return HomeTeam+'/平手'
        elif texts[0] == 'Draw' and not texts[1] == 'Draw':
            return '平手/'+AwayTeam
    else:
        if OptionCode == '1':
            return HomeTeam
        elif OptionCode == '2':
            return AwayTeam
        elif OptionCode == 'X':
            return '平手'
        elif OptionCode == 'Over':
            return '大分'
        elif OptionCode == 'Under':
            return '小分'

    return None

def add_LinePlayerPK(UserId, data, event):
    try:
        SQL = f"SELECT count(id) as count FROM [dbo].[LinePlayerPK] where UserId1='{UserId}' " \
              f"and created_dd >= '{datetime.now().astimezone(timezone(timedelta(hours=8))).replace(hour=0,minute=0,second=0).strftime('%Y-%m-%d %H:%M:%S.000')}'" \
              f"and created_dd <= '{datetime.now().astimezone(timezone(timedelta(hours=8))).replace(hour=23, minute=59, second=59).strftime('%Y-%m-%d %H:%M:%S.000')}'"
        results = db.engine.execute(SQL).mappings().all()
        if results[0]['count'] <= 5:
            Insert_SQL = f"INSERT INTO [dbo].[LinePlayerPK] ([UserId1],[EventCode],[Option1],[GroupOptionCode],[isAutoMatch],[isPushed],[created_dd],[HomeOdds],[AwayOdds],[SpecialBetValue]) " \
                         f"VALUES(N'{UserId}','{data['EventCode']}','{data['OptionCode']}','{data['GroupOptionCode']}','{False}','{False}','{datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000')}'," \
                         f"'{data['HomeOdds']}','{data['AwayOdds']}','{data['SpecialBetValue']}')"
            print(Insert_SQL)
            db.engine.execute(Insert_SQL)
            return True
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='今日選擇額度已經超過上限！'))
            return False
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='已經重複選擇！'))
        return False

def update_invite_LinePlayerPK(UserId, data, event):

    try:
        SQL = f"SELECT * FROM [dbo].[LinePlayerPK] " \
              f"inner join MatchEntry on LinePlayerPK.EventCode = MatchEntry.EventCode " \
              f"where id = {data['id']} "

        result = db.engine.execute(SQL).mappings().one()

        if result['Option2'] == None and result['UserId2'] != None and result['MatchTime'].replace(tzinfo=utc) >= datetime.now().astimezone(timezone(timedelta(hours=8))).replace(tzinfo=utc):
            SQL = f"UPDATE [dbo].[LinePlayerPK] SET Option2 = '{data['Option2']}' where id = {data['id']} "
            db.engine.execute(SQL)
            line_bot_api.push_message(data['LineUniqueID'],TextSendMessage(f"{get_member(UserId)}已確認您的邀請!"))
            return True
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'您已經點選或比賽已開打'))
            return False
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'Id{data["id"]}錯誤！'))
        traceback.print_exc()
        return False

def get_member(UserId):
    sql = f"select * from UserMember where UserId = '{UserId}'"
    results = db.engine.execute(sql).mappings().all()
    for idx in range(len(results)):
        results[idx] = dict(results[idx])  # 將 Mapping 轉型為 dict
    if len(results)>0:
        return results[0]['member']
    else:
        return None

def set_PredictResultsFlex(contents):
    PredictResultsFlex = json.load(open('static/PredictResultsFlex.json', 'r', encoding='utf-8'))
    PredictResultsFlex["body"]["contents"][0]["text"] = contents
    return PredictResultsFlex

if __name__ == '__main__':
    app.secret_key = secret_key
    app.run(port=803,debug=True)
