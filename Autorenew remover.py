import mechanize
import threading
import json
import csv
from msvcrt import getch
from requests.auth import HTTPBasicAuth
from datetime import date
import requests
today = date.today()
from lib_personal import creds
local_creds = creds.user_creds()

##########################################################################
## Change Log:                                                          ##
## 01/09/2020 Removes Auto Renew for all instances of the WRID. If a    ##
##            year is missed AR will still be processed.                ##
##                                                                      ##
## 3/25/2020 Added a loop to create a list of multiple RTUs/Customers   ##
##           that want to be adjusted instead of processing one by one. ## 
##                                                                      ##
## 4/1/2020 Added some error checking for AIMS, soil moisture stations, ##
##          and verifies if name is the same as the one searched to     ## 
##          avoid issues with simliar names.                            ##
##                                                                      ##
##########################################################################

SUB_BASE_URL = ('')
SUB_API_URL = ('')
SUB_COUPONS_URL = ('')
MANSUB = ('')
SUB_COUPONS_GRID_URL = ('=')

"""Checks and return RTU type from API"""
def rtutype(rtuid):
        username = local_creds.get_cred(creds.FN_PROD_USER)
        password = local_creds.get_cred(creds.FN_PROD_PASS)
        print(rtuid)
        URL = ('/%s') % str(rtuid)
        res = requests.get(URL,auth = HTTPBasicAuth(username,password))
        data = (res.text)
        json_data = json.loads(data)
        rtutype = json_data['mfg_rtu_id']
        frmwretype = json_data['firmware_type']
        uid = json_data['uid']
        if rtutype == 33 or rtutype == 35 and frmwretype != 'ERTU':
            return 'Cellular'
        elif rtutype == 34:
            return 'Radio'
        elif frmwretype == 'ERTU':
            return 'Ethernet'
        elif uid == 'FIELD':
            return 'Field'


class ThreadCompleteOTAP(threading.Thread):

    """Threaded Url Grab"""
    def __init__(self):
        threading.Thread.__init__(self)
        self.myData = None
        self.myopener = mechanize.Browser()
        self.OTAP = False
        self.username = ''
        self.password = ''


    """Logs into subadmin portal"""
    def browserLogin(self):
        """Prompts for credentials use local creds to use keyring"""
        self.username = local_creds.get_cred(creds.FN_SUBS_USER)
        self.password = local_creds.get_cred(creds.FN_SUBS_PASS)
        res = self.myopener.open(SUB_BASE_URL)
        wait = self.myopener.select_form(nr=0)
        self.myopener['Username'] = self.username
        self.myopener['Password'] = self.password
        res = self.myopener.submit()
        wait = None

    """Cleans up some of the browser functions"""
    def browserCleanup(self):
        self.myopener = None
        self.myopener = mechanize.Browser()
        self.myopener.set_handle_robots(False)
        self.myopener.set_handle_equiv(True)
        self.myopener.set_handle_gzip(True)
        self.myopener.set_handle_redirect(True)
        self.myopener.set_handle_referer(True)
        self.myopener.set_handle_robots(False)
        self.myopener.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)



    """Auto renew remover"""
    def Remover(self,WRID,Comment):
        self.browserCleanup()
        self.browserLogin()

        """Gets search criteria from user and creates request"""
        print('Getting data, please wait...')
        managesub = ('')%WRID
        post = self.myopener.open(managesub)
        manage = (str(post.read()))

        """Takes care of "Dirty json" """
        data1 = manage.replace("\\","")
        data2 = data1.replace("/","")
        data3 = data2.replace("  ","")
        data4 = data3.replace(" ","")
        data5 = data4.replace(".","")
        json_data = json.loads(data5[2:-1])
        for i in json_data:

            """Gets manage subscription api for given ID"""
            managsubapi = ('%s')%i['id']
            managesublist = self.myopener.open(managsubapi)
            subscription = (str(managesublist.read()))
            sub = subscription.replace("\\","")
            manageapi_json = json.loads(sub[2:-1])
            print(manageapi_json['customerName'])
            print('\nRTU Number: '+i['rtuSerialNumber'])
            print('Record Number: '+i['id'])
            print ('Pivot Type: '+manageapi_json['type'])
            if '000' in WRID or '-' in WRID:
                if manageapi_json['rtuName'] != WRID:
                    print("WRID Error, Result and search value do not match.")
                    continue
                else:
                    pass
            else:
                if manageapi_json['customerName'] != WRID:
                    print("Error, Result and search value do not match.")
                    continue
                else:
                    pass
            if manageapi_json['type'] == 'Soil Water Station' or i['rtuSerialNumber'] == '00005EF7' or manageapi_json['type'] == 'Pivot / AIMS' or manageapi_json['type'] == 'Pivot / PIVOT CONTROL LT':
                if manageapi_json['type'] == 'Pivot / AIMS':
                    print("Incompatiable with AIMS")
                    continue
                if manageapi_json['type'] == 'Soil Water Station':
                    print("incompatible with Moisture stations")
                    continue
                continue
            """Gets all package profiles"""
            URL3 = ('')
            pkgrequest = self.myopener.open(URL3)
            pkgprofile = str(pkgrequest.read())
            pkgpro_json = json.loads(pkgprofile[2:-1])
            try:
                rtutyp = rtutype(manageapi_json['rtuId'])
            except:
                print("Cannot find rtu number ", i['rtuSerialNumber'])
                with open('..//not_removed.csv', 'a') as outcsv:
                    writer = csv.writer(outcsv, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
                    writer.writerow([manageapi_json['rtuName'],manageapi_json['customerName'],manageapi_json['startDateUtc'].split('T')[0],today])
                    print("Change not made, Passing")
                    continue
            count=0
            while True:
                try:

                    """Gets package cellular NAI package profiles"""
                    if rtutyp == 'Cellular' or rtutyp == 'Field':
                        if 'PIVOT CONTROL' in manageapi_json['type'] and 'LT' not in manageapi_json['type']:
                            if 'Cellular' in pkgpro_json[count]['internalName'] and 'NAI' in pkgpro_json[count]['internalName'] and 'Pivot Control' in pkgpro_json[count]['internalName']:
                                    packageurl = SUB_BASE_URL + SUB_API_URL + 'PackageProfiles/' + pkgpro_json[count]['id']
                                    profile = self.myopener.open(packageurl)
                                    apiprofile = str(profile.read())
                                    prepayload = json.dumps(manageapi_json)
                                    payload = prepayload.replace('"selectedPackageProfile": null','"selectedPackageProfile":%s')%apiprofile[2:-1]

                        elif 'VISION' in manageapi_json['type']:
                            if pkgpro_json[count]['internalName'] == 'Premium for Pivots (Cellular) for NAI Dealers':
                                if 'VISION' in pkgpro_json[count]['productNames'][1]:
                                    packageurl = SUB_BASE_URL + SUB_API_URL + 'PackageProfiles/' + pkgpro_json[count]['id']
                                    profile = self.myopener.open(packageurl)
                                    apiprofile = str(profile.read())
                                    prepayload = json.dumps(manageapi_json)
                                    payload = prepayload.replace('"selectedPackageProfile": null','"selectedPackageProfile":%s')%apiprofile[2:-1]

                        elif 'BOSS' in manageapi_json['type']:
                            if pkgpro_json[count]['internalName'] == 'Premium for Pivots (Cellular) for NAI Dealers':
                                if 'BOSS' in pkgpro_json[count]['productNames'][0]:
                                    packageurl = SUB_BASE_URL + SUB_API_URL + 'PackageProfiles/' + pkgpro_json[count]['id']
                                    profile = self.myopener.open(packageurl)
                                    apiprofile = str(profile.read())
                                    prepayload = json.dumps(manageapi_json)
                                    payload = prepayload.replace('"selectedPackageProfile": null','"selectedPackageProfile":%s')%apiprofile[2:-1]

                        elif '700SERIES' in manageapi_json['type'] or '500SERIES' in manageapi_json['type']:
                            if pkgpro_json[count]['internalName'] == 'Premium for Pivots (Cellular) for NAI Dealers':
                                if '700' in pkgpro_json[count]['productNames'][0] or '500' in pkgpro_json[count]['productNames'][0]:
                                    print(pkgpro_json[count])
                                    packageurl = SUB_BASE_URL + SUB_API_URL + 'PackageProfiles/' + pkgpro_json[count]['id']
                                    profile = self.myopener.open(packageurl)
                                    apiprofile = str(profile.read())
                                    prepayload = json.dumps(manageapi_json)
                                    payload = prepayload.replace('"selectedPackageProfile": null','"selectedPackageProfile":%s')%apiprofile[2:-1]

                        elif manageapi_json['type'] == 'Field' :
                                if pkgpro_json[count]['internalName'] == 'FieldNET Advisor (Premium) - NAI/BU':
                                    print('Getting Package Profile info for FieldNet Advisor')
                                    packageurl = SUB_BASE_URL + SUB_API_URL + 'PackageProfiles/' + pkgpro_json[count]['id']
                                    profile = self.myopener.open(packageurl)
                                    apiprofile = str(profile.read())
                                    prepayload = json.dumps(manageapi_json)
                                    payload = prepayload.replace('"selectedPackageProfile": null','"selectedPackageProfile":%s')%apiprofile[2:-1]
                    """Checks if RTU is radio"""
                    if rtutyp == 'Radio' or rtutyp == 'Ethernet':
                        if 'PIVOT CONTROL' in manageapi_json['type']:
                            if pkgpro_json[count]['internalName'] == 'Premium for Pivot Control (Ethernet/Radio) for NAI Dealers':
                                    packageurl = SUB_BASE_URL + SUB_API_URL + 'PackageProfiles/' + pkgpro_json[count]['id']
                                    profile = self.myopener.open(packageurl)
                                    apiprofile = str(profile.read())
                                    prepayload = json.dumps(manageapi_json)
                                    payload = prepayload.replace('"selectedPackageProfile": null','"selectedPackageProfile":%s')%apiprofile[2:-1]

                        elif '700SERIES' in manageapi_json['type'] or '500SERIES' in manageapi_json['type']:
                            if pkgpro_json[count]['internalName'] == 'Premium for Pivots (Ethernet/Radio) for NAI Dealers':
                                if '700' in pkgpro_json[count]['productNames'][0] or '500' in pkgpro_json[count]['productNames'][0]:
                                    print(pkgpro_json[count])
                                    packageurl = SUB_BASE_URL + SUB_API_URL + 'PackageProfiles/' + pkgpro_json[count]['id']
                                    profile = self.myopener.open(packageurl)
                                    apiprofile = str(profile.read())
                                    prepayload = json.dumps(manageapi_json)
                                    payload = prepayload.replace('"selectedPackageProfile": null','"selectedPackageProfile":%s')%apiprofile[2:-1]

                        elif 'VISION' in manageapi_json['type']:
                            if pkgpro_json[count]['internalName'] == 'Premium for Pivots (Ethernet/Radio) for NAI Dealers':
                                    packageurl = SUB_BASE_URL + SUB_API_URL + 'PackageProfiles/' + pkgpro_json[count]['id']
                                    profile = self.myopener.open(packageurl)
                                    apiprofile = str(profile.read())
                                    prepayload = json.dumps(manageapi_json)
                                    payload = prepayload.replace('"selectedPackageProfile": null','"selectedPackageProfile":%s')%apiprofile[2:-1]

                        elif 'BOSS' in manageapi_json['type']:
                            if pkgpro_json[count]['internalName'] == 'Premium for Pivots (Ethernet/Radio) for NAI Dealers':
                                    packageurl = SUB_BASE_URL + SUB_API_URL + 'PackageProfiles/' + pkgpro_json[count]['id']
                                    profile = self.myopener.open(packageurl)
                                    apiprofile = str(profile.read())
                                    prepayload = json.dumps(manageapi_json)
                                    payload = prepayload.replace('"selectedPackageProfile": null','"selectedPackageProfile":%s')%apiprofile[2:-1]
                    count+=1
                except:
                    break

            """Checks for Autorenew and disables and adds comment if true"""
            if manageapi_json['isAutoRenew'] == True:
                payload2 = payload.replace('"isAutoRenew": true','"isAutoRenew": false ')
                payload3 = payload2.replace('"comment": null','"comment": "%s"')%Comment
                paylast = ''
                """Checks if 'Basic Pivot Monitor And Control' is enabled"""
                try:    #Using a try statement to catch out of bounds error when 'Basic Pivot Monitor And Control' is not enabled
                    if manageapi_json['packageAddOns'][1]['productAddOn']['name'] == 'Basic Pivot Monitor And Control':
                        paylast = payload3
                    elif manageapi_json['packageAddOns'][0]['productAddOn']['name'] == 'Basic Pivot Monitor And Control':
                        paylast = payload3
                    elif manageapi_json['packageAddOns'][2]['productAddOn']['name'] == 'Basic Pivot Monitor And Control':
                        paylast = payload3
                except:
                    if 'BOSS' in manageapi_json['type'] or 'VISION' in manageapi_json['type'] or 'PIVOT CONTROL' in manageapi_json['type'] or '700' in manageapi_json['type'] or '500' in manageapi_json['type']:
                        paylast = payload3.replace('"productAddOnId":"ec7b58fd-8021-4d4f-8224-a514f50fb4e5","checkedByDefault":true','"productAddOnId":"ec7b58fd-8021-4d4f-8224-a514f50fb4e5","checkedByDefault":"false"')
                    else:
                        with open('..//not_removed.csv', 'a') as outcsv:
                            writer = csv.writer(outcsv, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
                            writer.writerow([manageapi_json['rtuName'],manageapi_json['customerName'],manageapi_json['startDateUtc'].split('T')[0],today])
                            print("Change not made.")

                """headers to avoid 500 error"""
                header = {"Accept": "application/json, text/plain, */*",
                           "Origin": "https://subadmin.myfieldnet.com",
                           "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
                           "Content-Type": "application/json;charset=UTF-8",
                           "Sec-Fetch-Site": "same-origin",
                           "Sec-Fetch-Mode": "cors",
                           "Referer":"https://subadmin.myfieldnet.com/ManageSubscriptions"
                           }

                """Posting payload and headers. Writing wrid, customer name, start date, and date AR was removed to a report."""
                try:
                    """Makes sure paylast is not empty"""
                    if paylast != '':
                        #print(paylast)
                        self.myopener.open(mechanize.Request('',data = paylast, headers=header))
                        print('Removing AR... \nWriting record to report.\n')
                        with open('..//Autorenew Removed.csv', 'a') as outcsv:
                            writer = csv.writer(outcsv, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
                            writer.writerow([manageapi_json['rtuName'],manageapi_json['customerName'],manageapi_json['startDateUtc'].split('T')[0],today,Comment])
                    else:
                        print("The payload is empty.")
                        pass
                except:
                    print('\nAn error has occured posting the URL or writing the CSV')
            else:
                print('\nThis record for WRID: '+ manageapi_json['rtuName'] +' does not have Auto Renew enabled.\n')


    def splashScreen(self):
        print ("""
    _         _              ____                            ____
   / \  _   _| |_ ___       |  _ \ ___ _ __   _____      __ |  _ \ ___ _ __ ___   _____   _____ _ __
  / _ \| | | | __/ _ \ _____| |_) / _ \ '_ \ / _ \ \ /\ / / | |_) / _ \ '_ ` _ \ / _ \ \ / / _ \ '__|
 / ___ \ |_| | || (_) |_____|  _ <  __/ | | |  __/\ V  V /  |  _ <  __/ | | | | | (_) \ V /  __/ |
/_/   \_\__,_|\__\___/      |_| \_\___|_| |_|\___| \_/\_/   |_| \_\___|_| |_| |_|\___/ \_/ \___|_|

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
    count = 0
    """Loop to input another WRID when initial job is complete"""
    while True:
        complete = 0
        print("Enter 'x' to when you are done entering RTU #'s or customer names\n")
        wrid_list = []
        while True:
            if complete > 0:
                break
            WRID = input('Enter your WRID (ex:00003324) or Customer Name: ')
            if WRID == 'x': #Checks if value is X
                Comment = input('Enter your comment: ')
                while len(wrid_list)>=0:
                    try:
                        t.Remover(wrid_list[count],Comment)
                        count+=1 
                    except:
                        print("Complete")
                        complete+=1
                        break
            else:
                wrid_list.append(WRID)

        cont = input('Would you like to remove Auto Renew from a different device?(y/n) ').upper()
        if cont == 'Y':
            count = 0
            continue
        else:
            getch()
            quit()
    t.join()
