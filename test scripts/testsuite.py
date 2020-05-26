#Python Modules
import os
import unittest
import time
import HTMLTestRunner
#Test Modules
import test_fggapp_add_products
import Slideshow_test
import Remote_starter_checkout
import working_stero_checkout_test
import home_page_links
import working_tint_checkout_test
import working_failed_payment


def pre_test():
    """Pre-test: adding products"""
    fggapp = test_fggapp_add_products.fggapp_driver()    
    fggapp.login()
    tint = os.path.dirname(os.path.realpath(__file__)) + "/App_photos/tint.jpg"     #finds picture for products
    stereo = os.path.dirname(os.path.realpath(__file__)) + "/App_photos/stereo.jpg"
    starter = os.path.dirname(os.path.realpath(__file__)) + "/App_photos/starter.jpg"
    fggapp.add_tint(tint)   #adding ting
    fggapp.add_stereo(stereo)   #adding stereo
    fggapp.add_remote_start(starter)    #Adding remote starter
    fggapp.clean_up()
    time.sleep(2)

def suite():
    """FGG test suite"""
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(home_page_links))     #non checkout tests
    suite.addTests(loader.loadTestsFromModule(Slideshow_test))
    """Checkout tests"""
    suite.addTests(loader.loadTestsFromModule(Remote_starter_checkout))  #Checkout tests
    suite.addTests(loader.loadTestsFromModule(working_stero_checkout_test))
    suite.addTests(loader.loadTestsFromModule(working_tint_checkout_test))   
    suite.addTests(loader.loadTestsFromModule(working_failed_payment))
    dateTimeStamp = time.strftime('%m_%d_%y %H-%M')     #Gets current time stamp
    reportName = './/FGG_test_' + dateTimeStamp + '.html'  #Names report
    outfile = open(reportName, "w")     #Creates report file
 
    runner = HTMLTestRunner.HTMLTestRunner(    #Writes report file in HTML format
            stream=outfile,
            title='FGG Automated Test Suite Report',
            description='This is an automated test for our Final Sprint.',
            verbosity=2
        )
    runner.run(suite)     #Runs suite

if __name__ == '__main__':
    pre_test()
    suite()
