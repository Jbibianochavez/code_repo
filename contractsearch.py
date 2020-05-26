# -*- coding: utf-8 -*-
"""
Created on Fri Dec 27 11:55:56 2019

@author: Jose.Bibiano-Chavez
"""

import mechanize
import threading
import json
import csv
from lib_personal import creds
local_creds = creds.user_creds()


#######################################################################
## Change Log:                                                       ##
## 12/27/19: Takes a Contract Number and provides a report. Meant to ##
##           quickly check eq type for contract numbers from a BU    ##
## 2/3/2020: Saving creds to keyring and uploading to github.        ##
##                                                                   ##
#######################################################################



SUB_BASE_URL = ('')




class ThreadCompleteOTAP(threading.Thread):
    """Threaded Url Grab"""
    def __init__(self):
        threading.Thread.__init__(self)
        self.myData = None
        self.myopener = mechanize.Browser()
        self.OTAP = False
        self.username = ''
        self.password = ''

    ##Logs into sub admin portal##
    def browserLogin(self):
        self.username = local_creds.get_cred(creds.FN_SUBS_USER)
        self.password = local_creds.get_cred(creds.FN_SUBS_PASS)
        res = self.myopener.open(SUB_BASE_URL)
        wait = self.myopener.select_form(nr=0)
        self.myopener['Username'] = self.username
        self.myopener['Password'] = self.password
        res = self.myopener.submit()
        wait = None

    ##Takes care of various browser settings##
    def browserCleanup(self):
        self.myopener = None
        self.myopener = mechanize.Browser()
        self.myopener.set_handle_robots(False)
        self.myopener.set_handle_equiv(True)
        self.myopener.set_handle_redirect(True)
        self.myopener.set_handle_referer(True)
        self.myopener.set_handle_robots(False)
        self.myopener.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)


    ##Opens and checks contract number##
    def adjustsub(self):
        while True:
            ##Establishing initial connection and logging in##
            self.browserCleanup()
            self.browserLogin()
            try:
                contract_num = input("Please enter your contract number: ").upper()
                ##Opens Contractsearch Report.csv and writes each contract number the user inputs##
                with open('.//Contractsearch Report.csv', 'a') as outcsv:
                    writer = csv.writer(outcsv, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
                    writer.writerow([contract_num])
                print("Getting Contract Number: "+contract_num+"\n")
                ##Opens OrderQueue List##
                orderQlink = ('')
                payload = ('keyword=%s&startUtc=2018-12-23&endUtc=') % contract_num
                ##Posting list because it does not take a get##
                post = self.myopener.open(orderQlink,data = payload)
                orderQlist = (str(post.read()))
            except:
                print("Contract number: " + contract_num + " does not exit, try again")
                continue
            data = orderQlist.split("'")[1]
            data1 = data.replace("\\","")
            json_data = json.loads(data1)
            count = 1
            for i in json_data:
                orderid = (i['id'])
                orderinfolink= ("/%s")%orderid
                orderinforeq = self.myopener.open(orderinfolink)
                orderinfo = str(orderinforeq.read())
                data111 = orderinfo.replace("\\","")
                data1111 = data111.replace("'"," ")
                orderinfo_json = json.loads(data1111[2:-1])
                for b in orderinfo_json['lineItems']:
                    base = b['dealerBaseCost']
                    volsavings = b['volumeSavings']
                    ARsavings = b['autoRenewSavings']
                    coupon = b['couponSavings']
                    billtodealersavings = b['billToDealerSavings']
                    volsavepercent = (volsavings/base)*100
                    total = 0
                    if volsavings != 0:
                        total = base - volsavings
                    elif billtodealersavings !=0:
                        total = base - billtodealersavings
                    elif ARsavings != 0:
                        total = base - ARsavings
                    elif volsavings != 0 and billtodealersavings !=0:
                        total = (base - volsavings) - billtodealersavings
                    elif volsavings != 0 and ARsavings !=0:
                        tot = (base - volsavings)
                        total = tot - ARsavings
                    elif coupon != 0:
                        total = base - coupon
                    else:
                        total = base

                    print("Equipment #"+str(count))
                    print("Equipment Name: "+b['equipmentName'])
                    print("RTU Type: "+b['dataPlanName'])
                    print("WRID: "+b['rtuSerialNumber'])
                    print("Product: "+b['productName'])
                    print("Length: "+str(b['termLength']['months']))
                    print("Dealer Base Cost: $"+str(b['dealerBaseCost']))
                    print("Volume Savings: "+str(volsavepercent)+"%")
                    print("Bill To Dealer Savings: $"+str(billtodealersavings))
                    print("Coupon Savings: $"+str(coupon))
                    print("Total Cost: $"+str(total)+"\n")
                    count+=1
                    continue




    def splashScreen(self):
        print ("""
  ____            _                  _     _   _                 _                  ____ _               _
 / ___|___  _ __ | |_ _ __ __ _  ___| |_  | \ | |_   _ _ __ ___ | |__   ___ _ __   / ___| |__   ___  ___| | __
| |   / _ \| '_ \| __| '__/ _` |/ __| __| |  \| | | | | '_ ` _ \| '_ \ / _ \ '__| | |   | '_ \ / _ \/ __| |/ /
| |__| (_) | | | | |_| | | (_| | (__| |_  | |\  | |_| | | | | | | |_) |  __/ |    | |___| | | |  __/ (__|   <
 \____\___/|_| |_|\__|_|  \__,_|\___|\__| |_| \_|\__,_|_| |_| |_|_.__/ \___|_|     \____|_| |_|\___|\___|_|\_\

""")

        pass

    def mainManualRun(self,isAutomated):
        self.splashScreen()


    def run(self):
        self.mainManualRun(False)


if __name__ == '__main__':
    t = None
    t = ThreadCompleteOTAP()
    t.setDaemon(False)
    t.start()
    t.adjustsub()
    t.join()
