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

server = web_config.testing().server
database = web_config.testing().database
user = web_config.testing().username
password = web_config.testing().password

line_bot_api = LineBotApi('m7qBREk83jz41g0bcIftPx/DIQNmSZHZ/Ga6B5BbpkVfalpJmPiU4J08fS7GqL5JF2u9poLdjPfOd/uwkLi4qHh1SJkWnBhokHhOYALpfx89easIBmfRz6SijjLLS/hNnR9CSCl3ypNZX1MN46S9zwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('c96d65cbc79817b766a2defec1dbef48')

def get_ConnectionFromDB():
    db = pymssql.connect(server, user, password, database)
    cursor = db.cursor(as_dict=True)
    return db, cursor

def invitePK(cursor):
    print(datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000'), '開始進行邀請推播')
    PKs = get_PKNotMatch(cursor, isUserId2=True)
    for PK in PKs:
        try:
            invitePKFlex = set_invitePKFlex(PK,cursor)
            print(PK['UserId2'])
            line_bot_api.push_message(get_LineUserMember(cursor, UserId=PK['UserId2']),FlexSendMessage('PK邀請',invitePKFlex))
            SQL = f"""UPDATE [dbo].[LinePlayerPK] SET [isPushed] = {1}
                      where id = {PK['id']}
                  """
            print(SQL)
            cursor.execute(SQL)
            db.commit()
        except:
            print('不存在的用戶---')
            traceback.print_exc()

def get_Quotations(cursor):
    SQL = "SELECT * From LinePKQuotations"
    cursor.execute(SQL)
    results = cursor.fetchall()
    results = pd.DataFrame(results)
    return list(results['Quotation'])

def set_invitePKFlex(PK,cursor):

    corpus = get_Quotations(cursor)

    invitePKFlex= json.load(open('static/LineInvitePKFlex.json', 'r', encoding='utf-8'))
    teamlogos = pd.read_csv('static/teamlogos.csv',encoding='big5')
    HomeTeam = TeamNameCorrection(PK['HomeTeam'])
    AwayTeam = TeamNameCorrection(PK['AwayTeam'])
    # 比賽時間
    invitePKFlex['body']['contents'][0]['contents'][0]['contents'][0]['text'] = PK['MatchTime'].strftime("%Y-%m-%d %H:%M")
    # 主隊名稱
    invitePKFlex['body']['contents'][2]['contents'][0]['contents'][0]['text'] = HomeTeam
    # 主隊LOGO
    invitePKFlex['body']['contents'][1]['contents'][0]['contents'][0]['url'] = \
        teamlogos[teamlogos['name'] == HomeTeam].iloc[0, 3] if len(
            teamlogos[teamlogos['name'] == HomeTeam]) > 0 else 'https://i.imgur.com/x31phAh.jpeg'

    # 客隊名稱
    invitePKFlex['body']['contents'][2]['contents'][1]['contents'][0]['text'] = AwayTeam
    # 客隊LOGO
    invitePKFlex['body']['contents'][1]['contents'][2]['contents'][0]['url'] = \
        teamlogos[teamlogos['name'] == AwayTeam].iloc[0, 3] if len(
            teamlogos[teamlogos['name'] == AwayTeam]) > 0 else 'https://i.imgur.com/x31phAh.jpeg'
    # 盤口
    invitePKFlex['body']['contents'][3]['contents'][0]['text'] = \
        "🏁 " + get_TypeCname(PK['SportCode'], PK['GroupOptionCode'],cursor)
    # 賠率
    invitePKFlex['body']['contents'][4]['contents'][0]['contents'][0]['text'] = PK['HomeOdds']
    invitePKFlex['body']['contents'][4]['contents'][2]['contents'][0]['text'] = PK['AwayOdds']
    # 下狠話
    invitePKFlex['body']['contents'][6]['contents'][0]['text'] = corpus[random.randint(0, len(corpus) - 1)].strip()
    # LABEL1
    invitePKFlex['body']['contents'][5]['contents'][0]['text'] = f"😁來自{get_member(PK['UserId1'])}的狠話😁"
    # LABEL2
    Option2 = Reverse_OptionCode(PK['Option1'], PK['SportCode'], PK['GroupOptionCode'], HomeTeam, AwayTeam)
    invitePKFlex['body']['contents'][7]['contents'][1]['contents'][0]['text'] = \
        f"{get_member(PK['UserId1'])}已經下注{Mapping_OptionCode(PK['Option1'],PK['SportCode'],PK['GroupOptionCode'],HomeTeam,AwayTeam)}，" \
        f"您要挺{Mapping_OptionCode(Option2,PK['SportCode'],PK['GroupOptionCode'],HomeTeam,AwayTeam)}嗎!?"
    # ACTION
    invitePKFlex['footer']['contents'][0]['contents'][0]['action']['data'] = \
        f'''@PK邀請選擇=['id':'{PK['id']}','Option2':'{Option2}','LineUniqueID':'{get_LineUserMember(cursor, UserId=PK['UserId1'])}','HomeTeam':'{HomeTeam}','AwayTeam':'{AwayTeam}','GroupOptionName':'{get_TypeCname(PK['SportCode'], PK['GroupOptionCode'],cursor)}']'''  # 主
    print(invitePKFlex)
    return invitePKFlex


def matchPK(cursor, db=None):
    print(datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000'),'開始進行配對')
    PKs = get_PKNotMatch(cursor,isUserId2=False)
    LineUserMembers = get_LineUserMember(cursor)

    for PK in PKs:
        try:
            UserId1 = PK['UserId1']
            LineUserMembers = pd.DataFrame(LineUserMembers)
            LineUserMember = random.choice(LineUserMembers[LineUserMembers.UserId != UserId1].to_dict('records'))
            SQL = f"""UPDATE [dbo].[LinePlayerPK] SET [UserId2] = '{LineUserMember['UserId']}', [Match_dd] = '{datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000')}'
                      where id = {PK['id']}
                   """
            print(SQL)
            cursor.execute(SQL)
            db.commit()

        except:
            traceback.print_exc()

def get_PKNotMatch(cursor, isUserId2, db=None):
    if isUserId2 == False:
        '''
        取得所有未配對列表
        isAutoMatch=0:手動, UserId2 is null, MatchEntry.MatchTime >= NOW()
        '''
        SQL = f"""SELECT *　FROM [dbo].[LinePlayerPK] 
                  inner join MatchEntry on [dbo].[LinePlayerPK].EventCode = MatchEntry.EventCode
                  where isAutoMatch=0 and UserId2 is null and MatchEntry.MatchTime >= '{datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000')}'
               """
        print(SQL)
        cursor.execute(SQL)
        results = cursor.fetchall()
        return results
    elif isUserId2 == True:
        '''
         取得所有未推播邀請列表
         isPushed=0, UserId2 is not null, MatchEntry.MatchTime >= NOW()
         '''
        SQL = f"""SELECT *　FROM [dbo].[LinePlayerPK] 
                  inner join MatchEntry on [dbo].[LinePlayerPK].EventCode = MatchEntry.EventCode
                  where isPushed=0 and UserId2 is not null and MatchEntry.MatchTime >= '{datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.000')}'
               """
        cursor.execute(SQL)
        results = cursor.fetchall()
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


def TeamNameCorrection(Eng_TeamName):
    Eng_TeamName = Eng_TeamName.replace(r"'", r"''")
    sql = f"SELECT name FROM teams where team = '{Eng_TeamName}' ;"

    cursor.execute(sql)
    result = cursor.fetchone()
    if result:
        return result['name']
    else:
        return None

def get_member(UserId):
    sql = f"select * from UserMember where UserId = '{UserId}'"
    cursor.execute(sql)
    result = cursor.fetchone()
    if result:
        return result['member']
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

def Reverse_OptionCode(OptionCode,SportCode,GroupOptionCode,HomeTeam,AwayTeam):
    if SportCode == '1' and GroupOptionCode in ('55'):
        texts = [OptionCode.split('/')[0].strip(), OptionCode.split('/')[1].strip()]
        if not texts[0] == 'Draw' and not texts[1] == 'Draw':
            return HomeTeam+'/Draw'
        elif not texts[0] == 'Draw' and texts[1] == 'Draw':
            return 'X'
        elif texts[0] == 'Draw' and not texts[1] == 'Draw':
            return 'Draw/'+AwayTeam
    else:
        if OptionCode == '1':
            return '2'
        elif OptionCode == '2':
            return '1'
        elif OptionCode == 'X':
            return '2'
        elif OptionCode == 'Over':
            return 'Under'
        elif OptionCode == 'Under':
            return 'Over'
    return None

if __name__ == '__main__':

    db, cursor = get_ConnectionFromDB()
    matchPK(cursor=cursor,db=db)
    invitePK(cursor=cursor)

    cursor.close()
    db.close()