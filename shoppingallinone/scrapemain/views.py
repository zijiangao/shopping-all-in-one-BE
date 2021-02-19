from django.http import JsonResponse, HttpResponse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import json
from bs4 import BeautifulSoup
import re

# Create your views here.


def get_product(request,product_id):
    lazada_data = get_product_from_lazada(product_id)
    shopee_data = get_product_from_shopee(product_id)
    data={
        "lazada": lazada_data,
        "shopee": shopee_data
    }
    return HttpResponse(json.dumps(data), content_type="application/json")


def get_product_from_lazada(product_id):
    capabilities = DesiredCapabilities.CHROME
    # capabilities["loggingPrefs"] = {"performance": "ALL"}  # chromedriver < ~75
    capabilities["goog:loggingPrefs"] = {"performance": "ALL"}  # chromedriver 75+
    driver = webdriver.Chrome("./chromedriver.exe",
                              desired_capabilities=capabilities, )
    driver.get("https://www.lazada.sg/")
    time.sleep(0.2)
    elem = driver.find_element_by_name("q")
    time.sleep(0.2)
    elem.send_keys(product_id)
    time.sleep(0.2)
    elem.send_keys(Keys.RETURN)
    time.sleep(0.2)
    browser_log = driver.get_log("performance")

    def process_browser_log_entry(entry):
        response = json.loads(entry['message'])['message']
        return response

    lazada_events = [process_browser_log_entry(entry) for entry in browser_log]
    lazada_events = [event for event in lazada_events if 'Network.response' in event['method']]
    json_tag=[]
    for index, lazada_event in enumerate(lazada_events):
        if lazada_event['method'] == "Network.responseReceived":
            if "https://www.lazada.sg/catalog/?q" in lazada_event['params']['response']['url']:
                response_new = driver.execute_cdp_cmd('Network.getResponseBody',
                                                      {'requestId': lazada_events[index]["params"]["requestId"]})
                soup = BeautifulSoup(response_new['body'], "html.parser")
                json_tag = soup.findAll('script', text=re.compile(r"window.pageData"))
                json_tag = str(json_tag[0])[24:-9]
                json_tag = json.loads(json_tag)

    driver.close()
    return json_tag['mods']['listItems']


def get_product_from_shopee(product_id):
    capabilities = DesiredCapabilities.CHROME
    capabilities["goog:loggingPrefs"] = {"performance": "ALL"}  # chromedriver 75+
    driver = webdriver.Chrome("./chromedriver.exe",
                              desired_capabilities=capabilities, )

    driver.get("https://shopee.sg/")
    time.sleep(1)
    elem = driver.find_element_by_class_name("shopee-searchbar-input__input")
    time.sleep(1)
    elem.send_keys(product_id)
    time.sleep(1)
    elem.send_keys(Keys.RETURN)
    time.sleep(1)
    browser_log = driver.get_log("performance")

    def process_browser_log_entry(entry):
        response = json.loads(entry['message'])['message']
        return response

    events = [process_browser_log_entry(entry) for entry in browser_log]
    events = [event for event in events if 'Network.response' in event['method']]

    response_new=[]
    for index, event in enumerate(events):

        if event['method'] == "Network.responseReceived":
            if "https://shopee.sg/api/v2/search_items/?by" in event['params']['response']['url']:

                response_new = driver.execute_cdp_cmd('Network.getResponseBody',
                                                      {'requestId': events[index]["params"]["requestId"]})
                response_new = json.loads(response_new['body'])
    shopee_base_img_url = "https://cf.shopee.sg/file/"
    for item in response_new['items']:
        item['price'] = item['price']/100000
        item['image'] = shopee_base_img_url+item['image']
        item['productUrl'] = "https://shopee.sg/"+re.sub(r' ', '-', item['name'])+"-i."+str(item['shopid'])+"."+str(item['itemid'])

    driver.close()
    return response_new['items']