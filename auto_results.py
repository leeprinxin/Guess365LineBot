import random
import linebot
from linebot import  LineBotApi, WebhookHandler
from linebot.models import TemplateSendMessage, ConfirmTemplate, MessageTemplateAction, PostbackEvent, MessageEvent, TextMessage, TextSendMessage, BubbleContainer, ImageComponent, BoxComponent, TextComponent, ImageSendMessage,IconComponent, ButtonComponent, SeparatorComponent, FlexSendMessage, URIAction,PostbackAction
from linebot.models import MessageEvent, TextMessage, PostbackEvent, TextSendMessage, TemplateSendMessage, ConfirmTemplate, MessageTemplateAction, ButtonsTemplate, PostbackTemplateAction, URITemplateAction, CarouselTemplate, CarouselColumn, ImageCarouselTemplate, ImageCarouselColumn
import pandas as pd
import requests,bs4
import json
from datetime import datetime
from datetime import datetime,timezone,timedelta
import traceback, pymssql
import time
from time import sleep
import web_config

line_bot_api = LineBotApi('m7qBREk83jz41g0bcIftPx/DIQNmSZHZ/Ga6B5BbpkVfalpJmPiU4J08fS7GqL5JF2u9poLdjPfOd/uwkLi4qHh1SJkWnBhokHhOYALpfx89easIBmfRz6SijjLLS/hNnR9CSCl3ypNZX1MN46S9zwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('c96d65cbc79817b766a2defec1dbef48')

server = web_config.testing().server
database = web_config.testing().database
user = web_config.testing().username
password = web_config.testing().password

def get_ConnectionFromDB():
    db = pymssql.connect(server, user, password, database)
    cursor = db.cursor(as_dict=True)
    return db, cursor

def set_results(cursor,db):
    print(datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000'), '開始更新賽果')
    print(datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000'), '取得所有已開賽，且已選擇PK')
    PKs = get_LinePlayerPK(cursor)
    for PK in PKs:
        try:
            print('*'*10, f"取得Id {PK['id']}的賽果，{PK['EventCode']}",'*'*10)
            MatchResult = get_MatchResult(PK['EventCode'],cursor)
            # MatchResult = {'HomeScore':2,'AwayScore':5}
            Result = None
            if MatchResult == None:
                print(f"Id:{PK['id']} 沒賽果")
                continue
            if PK['SportCode'] == '1' and PK['GroupOptionCode'] in ('55'):#雙勝彩
                pass
            elif PK['Option1'] in ('1','2','X') and PK['SpecialBetValue'] == '' : # 不讓分
                if float(MatchResult['HomeScore']) > float(MatchResult['AwayScore']) :
                    if PK['Option1'] == '1':
                        Result = 'UserId1'
                    elif PK['Option2'] == '1':
                        Result = 'UserId2'
                    else:
                        Result = 'X'
                elif float(MatchResult['HomeScore']) < float(MatchResult['AwayScore']):
                    if PK['Option1'] == '2':
                        Result = 'UserId1'
                    elif PK['Option2'] == '2':
                        Result = 'UserId2'
                    else:
                        Result = 'X'
                elif float(MatchResult['HomeScore']) == float(MatchResult['AwayScore']):
                    if PK['Option1'] == 'X':
                        Result = 'UserId1'
                    elif PK['Option2'] == 'X':
                        Result = 'UserId2'
                    else:
                        Result = 'X'
            elif PK['Option1'] in ('1','2','X') and PK['SpecialBetValue'] != '' : # 讓分
                print(MatchResult)
                if float(MatchResult['HomeScore']) > float(MatchResult['AwayScore'])+float(PK['SpecialBetValue']):
                    if PK['Option1'] == '1':
                        Result = 'UserId1'
                    elif PK['Option2'] == '1':
                        Result = 'UserId2'
                    else:
                        Result = 'X'
                elif float(MatchResult['HomeScore']) < float(MatchResult['AwayScore'])+float(PK['SpecialBetValue']):
                    if PK['Option1'] == '2':
                        Result = 'UserId1'
                    elif PK['Option2'] == '2':
                        Result = 'UserId2'
                    else:
                        Result = 'X'
                elif float(MatchResult['HomeScore']) == float(MatchResult['AwayScore'])+float(PK['SpecialBetValue']):
                    if PK['Option1'] == 'X':
                        Result = 'UserId1'
                    elif PK['Option2'] == 'X':
                        Result = 'UserId2'
                    else:
                        Result = 'X'
            elif PK['Option1'] in ('Over','Under')  : # 大小
                if float(MatchResult['HomeScore']) + float(MatchResult['AwayScore']) > float(PK['SpecialBetValue']):
                    if PK['Option1'] == 'Over':
                        Result = 'UserId1'
                    elif PK['Option2'] == 'Over':
                        Result = 'UserId2'
                    else:
                        Result = 'X'
                elif float(MatchResult['HomeScore']) + float(MatchResult['AwayScore']) < float(PK['SpecialBetValue']):
                    if PK['Option1'] == 'Under':
                        Result = 'UserId1'
                    elif PK['Option2'] == 'Under':
                        Result = 'UserId2'
                    else:
                        Result = 'X'
                elif float(MatchResult['HomeScore']) + float(MatchResult['AwayScore']) == float(PK['SpecialBetValue']):
                    if PK['Option1'] == 'X':
                        Result = 'X'
                    elif PK['Option2'] == 'X':
                        Result = 'X'
                    else:
                        Result = 'X'
            if Result is not None:
                SQL = f"UPDATE LinePlayerPK SET Result = '{Result}' WHERE id = {PK['id'] }"
                cursor.execute(SQL)
                db.commit()
                print(SQL)
        except:
            traceback.print_exc()

def set_GPlus(cursor,db):
    print(datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000'), '開始更新GPlus')
    print(datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000'), '取得所有已完賽，且已選擇PK')
    PKs = get_LinePlayerPK(cursor,result=1)
    for PK in PKs:
        try:
            capital = float(PK['GplusPoint'])
            print('*'*10, f"取得Id {PK['id']}PK勝負",'*'*10)
            Result = PK['Result']
            if Result == 'UserId1':
               if PK['Option1'] in ('1','Over'):
                   profit = capital*float(PK['HomeOdds'])
               elif PK['Option1'] in ('2','Under'):
                   profit = capital * float(PK['AwayOdds'])
               else:
                   profit = -1
               SQL = f"UPDATE [dbo].[LinePlayerPK] SET [GPlus] = {profit} where [id]={PK['id']}"
               cursor.execute(SQL)
               db.commit()
               print(SQL)


            elif Result == 'UserId2':
                if PK['Option2'] in ('1', 'Over'):
                    profit = capital * float(PK['HomeOdds'])
                elif PK['Option2'] in ('2', 'Under'):
                    profit = capital * float(PK['AwayOdds'])
                else:
                    profit = -1

                SQL = f"UPDATE [dbo].[LinePlayerPK] SET [GPlus] = {profit} where [id]={PK['id']}"
                cursor.execute(SQL)
                db.commit()
                print(SQL)
            else:
                SQL = f"UPDATE [dbo].[LinePlayerPK] SET [GPlus] = {-1} where [id]={PK['id']}"
                cursor.execute(SQL)
                db.commit()
                print(SQL)

        except:
            traceback.print_exc()

def push_results(cursor,db):
    print(datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000'), '開始通知PK賽果')
    print(datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000'), '取得所有已完賽，且已選擇PK')
    PKs = get_LinePlayerPK(cursor, result=1)
    PKs = pd.DataFrame(PKs)
    if len(PKs) > 0:
        UserIds = pd.concat([PKs['UserId1'], PKs['UserId2']]).unique()
        for UserId in UserIds:
            try:
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
                                        "url": "https://i.imgur.com/dTg8Y2r.png",
                                        "size": "full",
                                        "aspectMode": "cover",
                                        "aspectRatio": "1:1.6",
                                        "gravity": "top"
                                    }
                                ],
                                "paddingAll": "0px"
                            }
                        }
                    ]
                }
                PKsfilter = PKs[(PKs['UserId1'] == UserId) | (PKs['UserId2'] == UserId)]
                for PKfilter in PKsfilter.to_dict('records'):
                    print(PKfilter)
                    Carousel["contents"] += [get_LinePlayerPKResultFlex(PKfilter)]

                print(get_LineUserMember(cursor,UserId = UserId))
                print(Carousel)
                line_bot_api.push_message(get_LineUserMember(cursor,UserId = UserId), FlexSendMessage('PK賽果通知', Carousel))
            except:
                traceback.print_exc()


def get_LinePlayerPKResultFlex(PKfilter):
    LinePlayerPKResultFlex = json.load(open('static/LinePlayerPKResultFlex.json', 'r', encoding='utf-8'))
    teamlogos = pd.read_csv('static/teamlogos.csv', encoding='big5')
    HomeTeam, AwayTeam = TeamNameCorrection(PKfilter['HomeTeam'],cursor), TeamNameCorrection(PKfilter['AwayTeam'],cursor)
    # 開賽時間
    LinePlayerPKResultFlex['body']['contents'][0]['contents'][0]['contents'][0]['text'] = '開賽時間：' + PKfilter['MatchTime'].strftime("%Y-%m-%d %H:%M")
    # 主隊LOGO
    LinePlayerPKResultFlex['body']['contents'][1]['contents'][0]['contents'][0]['url'] = \
        teamlogos[teamlogos['name'] == HomeTeam].iloc[0, 3] if len(
            teamlogos[teamlogos['name'] == HomeTeam]) > 0 else 'https://i.imgur.com/x31phAh.jpeg'
    # 主隊名稱
    LinePlayerPKResultFlex['body']['contents'][2]['contents'][0]['contents'][0]['text'] = HomeTeam
    # 主隊賠率
    LinePlayerPKResultFlex['body']['contents'][4]['contents'][0]['contents'][0]['text'] = PKfilter['HomeOdds']

    # 客隊LOGO
    LinePlayerPKResultFlex['body']['contents'][1]['contents'][2]['contents'][0]['url'] = \
        teamlogos[teamlogos['name'] == AwayTeam].iloc[0, 3] if len(
            teamlogos[teamlogos['name'] == AwayTeam]) > 0 else 'https://i.imgur.com/x31phAh.jpeg'
    # 客隊名稱
    LinePlayerPKResultFlex['body']['contents'][2]['contents'][1]['contents'][0]['text'] = AwayTeam
    # 客隊賠率
    LinePlayerPKResultFlex['body']['contents'][4]['contents'][2]['contents'][0]['text'] = PKfilter['AwayOdds']
    # 盤口
    LinePlayerPKResultFlex['body']['contents'][3]['contents'][0]['text'] = "🏁" + get_TypeCname(PKfilter['SportCode'],PKfilter['GroupOptionCode'], cursor)

    if PKfilter['Result'] == 'UserId1':
        # 勝方上
        LinePlayerPKResultFlex['body']['contents'][6]['contents'][0]['contents'][0]['contents'][0]['text'] = get_member(PKfilter['UserId1'], cursor)
        # 敗方下
        LinePlayerPKResultFlex['body']['contents'][6]['contents'][2]['contents'][0]['contents'][0]['text'] = get_member(PKfilter['UserId2'], cursor)
    else:
        # 勝方上
        LinePlayerPKResultFlex['body']['contents'][6]['contents'][0]['contents'][0]['contents'][0]['text'] = get_member(PKfilter['UserId2'], cursor)
        # 敗方下
        LinePlayerPKResultFlex['body']['contents'][6]['contents'][2]['contents'][0]['contents'][0]['text'] = get_member(PKfilter['UserId1'], cursor)

    return LinePlayerPKResultFlex

def get_LinePlayerPK(cursor,result = None):
    if result == None:
        SQL = f'''Select * From LinePlayerPK inner join MatchEntry on LinePlayerPK.EventCode = MatchEntry.EventCode 
        Where UserId1 is not null and UserId2 is not null and Option1 is not null and Option2 is not null and Result is null '''
        cursor.execute(SQL)
        PKs = cursor.fetchall()
        return PKs
    else:
        SQL = f'''Select * From LinePlayerPK inner join MatchEntry on LinePlayerPK.EventCode = MatchEntry.EventCode 
        Where  Result is not null and GPlus is null'''
        cursor.execute(SQL)
        PKs = cursor.fetchall()
        return PKs

def get_MatchResult(EventCode, cursor):
    SQL = f'''Select * From MatchResults where EventCode = '{EventCode}' and isChecked=1 '''
    print(SQL)
    cursor.execute(SQL)
    results = cursor.fetchone()
    return results

def get_LineUserMember(cursor, UserId=None):
    if UserId == None:
        '''
        取得所有玩家用戶名單
        '''
        SQL = f"select * from [dbo].[LineUserMember] "
        cursor.execute(SQL)
        results = cursor.fetchall()
        return results
    elif UserId != None:
        '''
        取得指定玩家用戶名單
        '''
        SQL = f"select * from [dbo].[LineUserMember] where UserId = '{UserId}' "
        cursor.execute(SQL)
        result = cursor.fetchone()
        if result:
            return result['LineUniqueID']
        else:
            return None

def get_TypeCname(SportCode,GroupOptionCode, cursor):
    sql = f'''SELECT [SportCode],[Type],[Type_cname],[Play_Name],[GroupOptionCode1] FROM [dbo].[GroupOptionCode] 
                where [SportCode]='{SportCode}' and  GroupOptionCode1='{GroupOptionCode}' '''
    cursor.execute(sql)
    result = cursor.fetchone()
    if result:
        return result['Type_cname']
    else:
        return None

def get_member(UserId, cursor):
    sql = f"select * from UserMember where UserId = '{UserId}'"
    cursor.execute(sql)
    result = cursor.fetchone()
    if result:
        return result['member']
    else:
        return None

def TeamNameCorrection(Eng_TeamName, cursor):
    Eng_TeamName = Eng_TeamName.replace(r"'", r"''")
    sql = f"SELECT name FROM teams where team = '{Eng_TeamName}' ;"
    cursor.execute(sql)
    result  = cursor.fetchone()
    if result:
        return result['name']
    else:
        return None

if __name__ == '__main__':
    db, cursor = get_ConnectionFromDB()
    set_results(cursor=cursor,db=db)
    push_results(cursor=cursor, db=db)
    set_GPlus(cursor=cursor, db=db)
    cursor.close()
    db.close()