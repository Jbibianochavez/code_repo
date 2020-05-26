import time
import unittest
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

class Fgg_ATS(unittest.TestCase):

   def setUp(self):
       self.driver = webdriver.Chrome()

   def test_checkout(self):
       """Testing remote starter check out - Checkout should be successful"""
       userinfo = {'fname':'test',
                    'lname':'user',
                    'email':'test_user@test.com',
                    'phone':'(402)555-5555',
                    'address':'6001 Dodge St',
                    'city':'Omaha',
                    'state':'Ne',
                    'zip':'68182',
                    'year':'2017',
                    'Make':'Ford',
                    'model':'F-150'
                    }
       cc = {'cc_num':'4500600000000061',
                'cvv':'123',
                'exp':'02/24'}
       driver = self.driver
       driver.get('https://team4uno.pythonanywhere.com/')     #pulls up the homepage
       time.sleep(1)
       remotestarter = driver.find_element_by_xpath('/html/body/div[2]/div[1]/div[1]/div/a')      #remote starter link
       remotestarter.click()
       time.sleep(1)
       addtocart = driver.find_element_by_xpath('/html/body/div[2]/div/div[2]/div/div/form/button')        #add to cart button
       time.sleep(1)
       addtocart.click()    #adding to cart

       orderbutton = driver.find_element_by_xpath('/html/body/div[2]/div/div/div[4]/div/div[2]/div/button[1]/a')   #find order button
       orderbutton.send_keys(Keys.PAGE_DOWN)
       time.sleep(1)
       orderbutton.click()  #click on order button
       try:
           fname = driver.find_element_by_xpath('//*[@id="id_order_firstname"]')
           lname = driver.find_element_by_xpath('//*[@id="id_order_lastname"]')
           fname.send_keys(userinfo['fname'])
           lname.send_keys(userinfo['lname'])
           email = driver.find_element_by_xpath('//*[@id="id_order_email"]')
           phone = driver.find_element_by_xpath('//*[@id="id_order_phone_number"]')
           address = driver.find_element_by_xpath('//*[@id="id_order_address"]')
           city = driver.find_element_by_xpath('//*[@id="id_order_city"]')
           city.send_keys(Keys.PAGE_DOWN)
           state = driver.find_element_by_xpath('//*[@id="id_order_state"]')
           zipcode = driver.find_element_by_xpath('//*[@id="id_order_zipcode"]')
           year = driver.find_element_by_xpath('//*[@id="id_order_year"]')
           make = driver.find_element_by_xpath('//*[@id="id_order_make"]')
           model = driver.find_element_by_xpath('//*[@id="id_order_model"]')
           order_nextbutton = driver.find_element_by_xpath('/html/body/div[3]/div/div[2]/div[1]/form/button')
           orderbutton.send_keys(Keys.PAGE_DOWN)
       except:
            pass
       #Sending order form fields
       email.send_keys(userinfo['email'])
       phone.send_keys(userinfo['phone'])
       address.send_keys(userinfo['address'])
       city.send_keys(userinfo['city'])
       state.send_keys(userinfo['state'])
       zipcode.send_keys(userinfo['zip'])
       year.send_keys(userinfo['year'])
       make.send_keys(userinfo['Make'])
       model.send_keys(userinfo['model'])
       time.sleep(2)
       order_nextbutton.click()
       #time.sleep(4)
       #Sends CC #
       WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@id='braintree-hosted-field-number']")))
       WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//input[@class='number' and @id='credit-card-number']"))).send_keys(cc['cc_num'])
       #sends CVV
       driver.switch_to.default_content()
       WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@id='braintree-hosted-field-cvv']")))
       WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//input[@class='cvv' and @id='cvv']"))).send_keys(cc['cvv'])
       #sends EXP date
       driver.switch_to.default_content()
       WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[@id='braintree-hosted-field-expirationDate']")))
       WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//input[@class='expirationDate' and @id='expiration']"))).send_keys(cc['exp'])
       time.sleep(.5)
       driver.switch_to.default_content()
       driver.find_element_by_id("payment").submit()
       time.sleep(4)

       print("Success!")


if __name__ == "__main__":
   unittest.main()
