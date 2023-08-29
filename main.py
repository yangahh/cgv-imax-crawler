from datetime import datetime
import time

from decouple import config
import pymysql
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# slack message send
def post_message(token, channel, text):
    message_text = f'{text} -> http://cgv.kr/Rr3x5KGj'
    requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel, "text": message_text},
    )


DB_PASSWORD = config('DB_PASSWORD')

# Mysql connect
conn = pymysql.connect(
    db='cgv',
    user='root',
    password=DB_PASSWORD,
    host='localhost',
    port=3306,
    charset='utf8',
)

# database cursor
cursor = conn.cursor()

# table check
cursor.execute('USE cgv;')
cursor.execute('CREATE TABLE IF NOT EXISTS `imax_movie_last_date` (`id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY, `title` VARCHAR(100), `last_date` DATE);')


# URL of the theater page
CGV_THEATER_URL = 'http://www.cgv.co.kr/theaters/?areacode=01&theaterCode=0013'  # CGV 용산아이파크몰
MOVIE_TITLE = '오펜하이머'

select_last_date_sql = """SELECT last_date FROM imax_movie_last_date WHERE title = '""" + MOVIE_TITLE + """';"""
cursor.execute(select_last_date_sql)
res = cursor.fetchall()
last_date = res[-1][0] if len(res) > 0 else datetime.today().date()


options = webdriver.ChromeOptions()
options.add_argument("--headless=new")  # chrome driver version +115
# options.add_argument("--headless")  # linux
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument("--disable-gpu")
options.add_experimental_option("useAutomationExtension", False)
options.add_experimental_option("excludeSwitches", ['enable-automation'])

DRIVER_PATH = config('DRIVER_PATH', '/usr/local/bin/chromedriver')
SLACK_TOKEN = config('SLACK_TOKEN')

driver = webdriver.Chrome(executable_path=DRIVER_PATH, options=options)
driver.delete_all_cookies()
time.sleep(1)

driver.get(url=CGV_THEATER_URL)
innerIframe = driver.find_element(By.ID, "ifrm_movie_time_table")
driver.switch_to.frame(innerIframe)
date_chuck_list = driver.find_element(By.CSS_SELECTOR, "#slider").find_elements(By.CLASS_NAME, "item-wrap")

is_finded = False

for i in range(len(date_chuck_list)):
    # refresh element
    date_chuck_list = driver.find_element(By.CSS_SELECTOR, "#slider").find_elements(By.CLASS_NAME, "item-wrap")
    dates = date_chuck_list[-1-i].find_elements(By.CLASS_NAME, 'day')
    for j in range(len(dates)):
        # refresh element
        date_chuck_list = driver.find_element(By.CSS_SELECTOR, "#slider").find_elements(By.CLASS_NAME, "item-wrap")
        dates = date_chuck_list[-1-i].find_elements(By.CLASS_NAME, 'day')
        date = dates[-1-j]

        month = int(date.find_element(By.TAG_NAME, 'span').get_attribute('innerText').strip()[:-1])
        day = int(date.find_element(By.TAG_NAME, 'strong').get_attribute('innerText').strip())

        date_a = date.find_element(By.TAG_NAME, 'a')
        driver.execute_script("arguments[0].click();", date_a)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'sect-showtimes')))

        showtimes_section = driver.find_element(By.CLASS_NAME, 'sect-showtimes')
        movies_and_halls = showtimes_section.find_elements(By.CLASS_NAME, 'col-times')
        for movie_and_halls in movies_and_halls:
            movie = movie_and_halls.find_element(By.CLASS_NAME, 'info-movie')
            title = movie.find_element(By.TAG_NAME, 'a').get_attribute('innerText')
            if title == MOVIE_TITLE:
                halls = movie_and_halls.find_elements(By.CLASS_NAME, 'info-hall')
                for hall in halls:
                    hall_name = hall.find_element(By.TAG_NAME, 'li').get_attribute('innerText')
                    if hall_name == 'IMAX LASER 2D':
                        new_last_date = datetime(datetime.today().year, month, day).date()
                        if last_date < new_last_date:
                            last_date = new_last_date
                            post_message(SLACK_TOKEN, "#용아맥", last_date)
                            insert_sql = """
                                INSERT INTO imax_movie_last_date(title, last_date) 
                                VALUES('""" + MOVIE_TITLE + """', '""" + str(last_date) + """');
                            """
                            cursor.execute(insert_sql)
                            conn.commit()
                        is_finded = True
                        break
            if is_finded:
                break
        if is_finded:
            break
    if is_finded:
        break

post_message(SLACK_TOKEN, "#용아맥", last_date)
driver.quit()
cursor.close()
