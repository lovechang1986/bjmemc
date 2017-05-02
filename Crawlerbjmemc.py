# -*- coding: utf-8 -*-
import urllib2
import re
import base64
from datetime import date, time, datetime, timedelta

from bs4 import BeautifulSoup as bsp
import pandas
from pandas import DataFrame
import pymongo

"""
A crawler to crawl data from http://zx.bjmemc.com.cn/

Author : rogerclark
"""

class bjmemc(object):

    def __init__(self):
        # baseURL is the source of mainpage, jsURL is the source of mainjs
        # status == 0,download not success, status == 2, all download success
        self.baseURL = 'http://zx.bjmemc.com.cn/getAqiList.shtml?timestamp='
        self.jsURL = 'http://zx.bjmemc.com.cn/js/public_controller.js'
        self.status = {'mainPage':'default',
                       'mainjs':'default',
                       }

    def CheckStatus(self):
        # Check the download progess
        pass

    def GetPage(self, retry = 3):
        # Download mainPage and mainjs
        requestHTML = urllib2.Request(url = self.baseURL)
        requestJS = urllib2.Request(url = self.jsURL)
        if retry > 0:
            try:
                mainPage = urllib2.urlopen(requestHTML).read()
                mainjs = urllib2.urlopen(requestJS).read()
                if isinstance(mainPage, str) and (len(mainPage) > 1):
                    self.status['mainPage'] = 'OK'
                    print 'Getting main page success\n'
                if isinstance(mainjs, str) and (len(mainjs) > 1):
                    self.status['mainjs'] = 'OK'
                    print 'Getting js page success\n'

            except urllib2.URLError as e:
                print 'Error occurred in downloading page'
                if hasattr(e, 'code'):
                    print 'error code:', e.code, e.reason, '\n'
                time.sleep(3)
                return bjmemc.GetPage(retry - 1)
        else:
            print 'Can not download'
        # mainPage: the mainpage of website, a str object, containing the air monitoring data
        # mainjs: the main javascript of website, a str file, containing the station's chinese name and ID
        return mainPage, mainjs

    def Screen(self, mainjs = None, mainPage = None):
        # screening air condition raw data from mainPage, location data from mainjs
        # got location data from mainjs
        stationLine = re.findall('stationList\s=\s\'\{"Table":\[(\{.*?\})\]\}\'', mainjs)
        stationName = re.findall('"StationName":"(.*?)"', stationLine[1])
        stationNum = re.findall('"StationNumber":"(.*?)"', stationLine[1])

        # got air condition raw data from mainPage
        rawData = re.findall('var\swfelkfbnx\s=\seval\(\"\(\"\+b\.decode\(\'(.*?)\'\)', mainPage)

        # got the data's date
        rawDataTime = re.findall('gxDate\s=\sdate_gs_03.*?\+b\.decode\(\'(.*?)\'\)\)', mainPage)[0]
        # stationName: a list object, which contained the name of all air monitoring station
        # stationNum: a list object, which contained the ID of all air monitoring station
        # rawData: a str object, the raw data crawled from mainPage, encoding with base64 coding system
        # rawDataTime: a str object, the raw timestamps crawled from mainPage, encoding with base64 coding system
        return stationName, stationNum, rawData, rawDataTime

    def ScreenRawData(self, rawdata = None):
        # screen air condition data from rawData
        transData = base64.decodestring(rawdata[0])
        transDataLine = re.findall('\[\{(.*?)\}\]', transData)[0]

        findID = re.findall('"id":(\d{1,})', transDataLine) # the ID of air station
        #findID_num = [int(i) for i in findID]
        findAQI = re.findall('"aqi":(\d{0,})', transDataLine)# the AQI of air condition
        findAQI_num = [float(i) for i in findAQI]
        findFirst = re.findall('"first":"(.*?)"', transDataLine)# the primary pollutant

        findAQINO2 = re.findall('"no2":(\d{0,})', transDataLine)# the AQI of NO2
        findNO2 = re.findall('"no2_01":(\d{0,})', transDataLine)# the concentration of NO2
        findAQINO2_num = [float(i) for i in findAQINO2]
        findNO2_num = [float(i) for i in findNO2]


        findAQIpm10 = re.findall('"pm10":(\d{0,})', transDataLine)
        findpm10 = re.findall('"pm10_01":(\d{0,})', transDataLine)
        findAQIpm10_num = [float(i) for i in findAQIpm10]
        findpm10_num = [float(i) for i in findpm10]

        findAQIpm2 = re.findall('"pm2":(\d{0,})', transDataLine)
        findpm2 = re.findall('"pm2_01":(\d{0,})', transDataLine)
        findAQIpm2_num = [float(i) for i in findAQIpm2]
        findpm2_num = [float(i) for i in findpm2]

        findAQISO2 = re.findall('"so2":(\d{0,})', transDataLine)
        findSO2 = re.findall('"so2_01":(\d{0,})', transDataLine)
        findAQISO2_num = [float(i) for i in findAQISO2]
        findSO2_num = [float(i) for i in findSO2]

        findAQIO3 = re.findall('"o3":(\d{0,})', transDataLine)
        findO3 = re.findall('"o3_01":(\d{0,})', transDataLine)
        findAQIO3_num = [float(i) for i in findAQIO3]
        findO3_num = [float(i) for i in findO3]

        findAQICO = re.findall('"co":(\d{0,})', transDataLine)
        findCO = re.findall('"co_01":(0\.\d{0,}|\d{0,})', transDataLine) # the concentration of CO may contain decimals
        findAQICO_num = [float(i) for i in findAQICO]
        findCO_num = [float(i) for i in findCO]

        allData = {"id":findID, "aqi":findAQI_num, "first":findFirst, "NO2aqi":findAQINO2_num,
                   "NO2":findNO2_num, "pm10aqi":findAQIpm10_num, "pm10":findpm10_num, "pm2aqi":findAQIpm2_num,
                   "pm2":findpm2_num, "SO2aqi":findAQISO2_num, "SO2":findSO2_num, "O3aqi":findAQIO3_num,
                   "O3":findO3_num, "COaqi":findAQICO_num, "CO":findCO_num}

        return allData

    def MergeData(self, stationName = None, stationNum = None, rawDataTime = None, allData = None):
        # Reconstruct and merge data use pandas.DataFrame
        allStation = []
        timeList = []
        dataTable = allData
        timeStamp = base64.decodestring(rawDataTime)
        for i in allData['id']:
            if stationNum.__contains__(i):
                index = stationNum.index(i)
                siteName = stationName[index]
                allStation.append(siteName)
            else:
                allStation.append(str(i))
            timeList.append(timeStamp)
        dataTable['siteName'] = allStation
        dataTable['dataTime'] = timeList
        dataTable = DataFrame(dataTable)
        # dataTable is a pandas.DataFrame object, which contains the air monitoring data of all site(50)
        return dataTable

    def AddDatabase(self, dataTable = None):
        # add data to mongodb
        # the route of airstaion database is bjmemc.airdata.<files>
        # the route of datalog database is bjmemc.datalog.<files>
        client = pymongo.MongoClient() # initializing a MongoClient
        db = client.bjmemc # the name of database
        collection = db.airdata # the name of an database's air data collection
        dataLog = db.datalog # the name of database's data log collection
        errorlist = []
        #succlist = []
        now = datetime.now()
        str_now = now.strftime('%Y-%m-%d %H:%M:%S')

        data_iter = dataTable.iterrows()
        for row in data_iter:
            post = row[1].to_dict()
            check_data = collection.find_one({'id':post['id'], 'dataTime':post['dataTime']})
            log = {'siteName': post['siteName'],
                   'id': post['id'],
                   'dataTime': post['dataTime'],
                   'status': 'default',
                   'reason': 'default',
                   'data_id': 'default',
                   'log_time': str_now}
            if check_data != None:
                print 'find Duplicate data, insert failure'
                log['status'],log['reason'] = 'Failure', 'duplicate'
                message_log = dataLog.insert_one(log)
                errorlist.append(log)
                print 'write data log:', message_log.inserted_id

            else:
                log['status'] = 'success'
                message = collection.insert_one(post)
                message_log = dataLog.insert_one(log)
                print 'insert is OK:', message.inserted_id
                print 'write data log:', message_log.inserted_id

        return errorlist

    def runOnetask(self):
        mp, mj = self.GetPage()
        stname, stnum, rawdata, rawtime = self.Screen(mj, mp)
        alldata = self.ScreenRawData(rawdata)
        datatable = self.MergeData(stationName = stname,
                                   stationNum = stnum,
                                   rawDataTime = rawtime,
                                   allData = alldata)
        errorlist = self.AddDatabase(datatable)
        return errorlist






# test code
if __name__ == '__main__':
    t = bjmemc()
    er = t.runOnetask()
    print len(er)














