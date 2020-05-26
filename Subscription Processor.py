import mechanize
import threading
import json
import csv
import time
from datetime import date
from msvcrt import getch
from lib_personal import creds
local_creds = creds.user_creds()

#########################################################################
## Change Log:                                                         ##
## 01/02/2020 Created to process subscriptions with dollar amounts and ##
##            put on hold $0 transactions.                             ##
##                                                                     ##
#########################################################################

today = date.today()
SUB_BASE_URL = ('')
SUB_API_URL = ('/api')
today = date.today()


class ThreadCompleteOTAP(threading.Thread):
    """Threaded Url Grab"""
    def __init__(self):
        threading.Thread.__init__(self)
        self.myData = None
        self.myopener = mechanize.Browser()
        self.OTAP = False

    def browserLogin(self):
        self.username = local_creds.get_cred(creds.FN_SUBS_USER)
        self.password = local_creds.get_cred(creds.FN_SUBS_PASS)
        res = self.myopener.open(SUB_BASE_URL)
        wait = self.myopener.select_form(nr=0)
        self.myopener['Username'] = self.username
        self.myopener['Password'] = self.password
        res = self.myopener.submit()
        wait = None


    def browserCleanup(self):
        self.myopener = None
        self.myopener = mechanize.Browser()
        self.myopener.set_handle_robots(False)
        self.myopener.set_handle_equiv(True)
        self.myopener.set_handle_redirect(True)
        self.myopener.set_handle_referer(True)
        self.myopener.set_handle_robots(False)
        self.myopener.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)



    def adjustsub(self):
        processed = 0
        onholdcount = 0
        lenum = 0
        noactnum = 0

        """ initializes browser and logs into sub portal"""
        self.browserCleanup()
        self.browserLogin()
        print("Getting Order Queue List\n")

        """gets order queue"""
        orderQlink = ('')
        post = self.myopener.open(orderQlink,data = 'startUtc=2020-01-30&endUtc=')
        orderQlist = (str(post.read()))

        """fixes escape characters and ' in pos 0"""
        data1 = orderQlist.replace("\\","")
        json_data = json.loads(data1[2:-1])
        
        for i in json_data:

            """checks if the order is not a $0 order, is pending, and not a mail in check"""
            if i['status'] == "Pending" and i['total'] != 0.0 and i['paymentType'] != 'MailInCheck':
                print("Pre-Job Report: ")
                print ("\nStatus: " + i['status'] + "\nTotal: " + str(i['total']) + "\n")

                """makes link with subscription id"""
                process = ('/%s?')%i['id']

                #checks po number field for LE couon codes
                if i['paymentType'] == 'BillToDealer':
                    checklink = ('/%s?')%i['id']
                    order = self.myopener.open(checklink)
                    checkorder = (str(order.read()))
                    data2 = checkorder.replace("\\","")
                    order_json = json.loads(data2[2:-1])
                    couponcheck = order_json['purchaseOrderNumber']
                    if order_json['purchaseOrderNumber'] == None or couponcheck[0:2] != 'le'  or couponcheck[0:2] != 'LE' or couponcheck[0:2] != 'Le' and order_json['dealerAccountNumber'] != None or order_json['dealerAccountNumber'] != '':
                        """Posts process link for the sub id"""
                        self.myopener.open(process, data = '')
                        print("Job Complete, printing to report in parent directory.\n")
                        processed+=1

                        """Writes orderto CSV report"""
                        with open('..//AutoProcessed.csv', 'a') as outcsv:
                            writer = csv.writer(outcsv, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
                            writer.writerow(['Processed',i['invoiceNumber'],i['transactionDateUtc'].split('T')[0],i['total'],today])
                    else:
                        print("There is a LE number in the SO number. Please check this.")
                        print(order_json['invoiceNumber'])
                        print(couponcheck)
                        print(couponcheck[0:2])
                        lenum+=1
                        if order_json['dealerAccountNumber'] != None or order_json['dealerAccountNumber'] != '':
                            print("The following invoice does not have a dealer account number")
                            print(order_json['invoiceNumber'])
                            noactnum+=1
                            
                else:
                    self.myopener.open(process, data = '')
                    print("Job Complete, printing to report in parent directory.\n")
                    processed+=1
                    """Writes orderto CSV report"""
                    with open('..//AutoProcessed.csv', 'a') as outcsv:
                        writer = csv.writer(outcsv, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
                        writer.writerow(['Processed',i['invoiceNumber'],i['transactionDateUtc'].split('T')[0],i['total'],today])

            """checks if order is pending and is a $0 transaction and that it is not a mail in check"""
            if i['status'] == "Pending" and i['total'] == 0.0 and i['paymentType'] != 'MailInCheck':
                print("Pre-Job Report: ")
                print ("\nStatus: " + i['status'] + "\nTotal: " + str(i['total']) + "\n")

                """Makes link with sub id"""
                onhold = ('/%s?')% i['id']

                """#get request with sub id"""
                self.myopener.open(onhold)
                onholdcount+=1

                """Writes orderto CSV report"""
                with open('..//AutoProcessed.csv', 'a') as outcsv:
                    writer = csv.writer(outcsv, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
                    writer.writerow(['On Hold',i['invoiceNumber'],i['transactionDateUtc'].split('T')[0],i['total'],today])
                    print("Job Complete, printing to report in parent directory.\n")

        """Command Line post-job report"""
        total = processed + onholdcount
        print("Post Job report: ")
        print("Total Orders: " + str(total) + "\nOrders Processed: " + str(processed) + "\nOrders On Hold: " + str(onholdcount) + "\n\nPress any key to quit")
        print("LE numbers found: " + str(lenum))
        print("Contracts with no acct number: " + str(noactnum))
        print("This will check again")
        getch()
        


    def splashScreen(self):
        print ("""
 ____        _           ____
/ ___| _   _| |__       |  _ \ _ __ ___   ___ ___  ___ ___  ___  _ __
\___ \| | | | '_ \      | |_) | '__/ _ \ / __/ _ \/ __/ __|/ _ \| '__|
 ___) | |_| | |_) |     |  __/| | | (_) | (_|  __/\__ \__ \ (_) | |
|____/ \__,_|_.__/      |_|   |_|  \___/ \___\___||___/___/\___/|_|


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
    while True:
        t.adjustsub()
        continue
    t.join()
