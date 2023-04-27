from selenium import webdriver
from time import sleep
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import sqlite3


class GSEScraper:
    def __init__(self) -> None:
        self.driver = self.__init_chromedriver()
        self.__open_database("vocabulary.db")

    def process(self, start, end):
        print(f"processing words between {start} - {end}")
        page_number = 1
        self.__load_page(self.driver, page_number, start, end)
        last_page = False

        while not last_page:
            tds = self.driver.find_elements(
                By.XPATH, '/html/body/div[1]/div[1]/section[2]/section/div[2]/div/vocabulary-table/table/tbody/tr/td')
            i = 0
            for values in range(0, int(len(tds)/6)-1):

                # set vars and use class private methdos to linesplit and strip unwanted strings in resulting array
                # OR just strip unwanted strings
                gse = self.__strstrp(tds[i+3].text)
                cefr = self.__strstrp(tds[i+4].text)
                vocab = self.__linestripsplit(tds[i].text)
                topics = self.__linestripsplit(tds[i+1].text)
                gram = self.__linestripsplit(tds[i+2].text)

                # for example here we could invoke another function to do the inserting into db
                self.__insert_or_update_word_into_sqlite(
                    gse, cefr, vocab, topics, gram)

                print(
                    f"vocabulary: {vocab}\nTopics array: {topics} \nGrammatical category: {gram} \nGSE: {gse} \nCEFR: {cefr}")
                print('')
                i += 7

            next_links = self.driver.find_elements(
                By.LINK_TEXT, value="Next page")
            if len(next_links) < 1:
                last_page = True
            else:
                page_number += 1
                self.__load_page(self.driver, page_number, start, end)

    def close(self):
        self.driver.close()
        self.cursor.close()
        self.conn.close()

    def __open_database(self, filepath):
        self.conn = sqlite3.connect(filepath)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS  link_table (id integer PRIMARY KEY, gse integer NOT NULL, cefr text NOT NULL );")
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS  vocabulary_table (id integer PRIMARY KEY, link_table_id integer NOT NULL, word text NOT NULL, FOREIGN KEY (link_table_id) REFERENCES link_table (id) );")
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS  topics_table ( id integer PRIMARY KEY, link_table_id integer NOT NULL, description text NOT NULL, FOREIGN KEY (link_table_id) REFERENCES link_table (id) );")
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS  categories_table ( id integer PRIMARY KEY, link_table_id integer NOT NULL, description text NOT NULL, FOREIGN KEY (link_table_id) REFERENCES link_table (id) );")

    def __insert_or_update_word_into_sqlite(self, gse, cefr, vocab, topics, gram):
        # 1. insert into link_table(gse, cefr):
        self.cursor.execute(
            "INSERT INTO link_table (gse, cefr) VALUES (?, ?)", (gse, cefr))
        # 2. select and store the ID for the last inserted row in link_table
        last_Id_row = self.cursor.execute("SELECT MAX(id) FROM link_table")
        lastID = last_Id_row.fetchone()[0]
        # Insert the rest into respective tables.
        for i in range(len(vocab)):
            self.cursor.execute(
                "INSERT INTO vocabulary_table (link_table_id, word) VALUES (?, ?)", (lastID, vocab[i]))
        for i in range(len(topics)):
            self.cursor.execute(
                "INSERT INTO topics_table (link_table_id, description) VALUES (?, ?)", (lastID, topics[i]))
        for i in range(len(gram)):
            self.cursor.execute(
                "INSERT INTO categories_table (link_table_id, description) VALUES (?, ?)", (lastID, gram[i]))
        # Can be for example another method/function that takes as parameter the table and the tuple
        self.conn.commit()
        return

    def __linestripsplit(self, input_string):
        string_list = input_string.split('\n')
        for i, item_string in enumerate(string_list):
            string_list[i] = self.__strstrp(item_string)
        return string_list

    def __strstrp(self, input_string: str):
        # in order substrings to strip
        items = ["especially AmE", "especially BrE", "AmE", "BrE", "*"]
        for item in items:
            input_string = input_string.replace(item, "")
        return input_string

    def __init_chromedriver(self):
        driver = webdriver.Chrome()
        return driver

    # class private method
    def __load_page(self, driver, page_number, start_level, end_level):
        # load the page
        url = f"https://www.english.com/gse/teacher-toolkit/user/vocabulary?page={page_number}&sort=gse;asc&gseRange={start_level};{end_level}&audience=GL"
        driver.get(url)
        try:
            WebDriverWait(driver, 90).until(
                EC.presence_of_element_located((By.CLASS_NAME, "create-pdf"))
            )
        except Exception as ex:
            raise ex

        elements = driver.find_elements(By.XPATH, "//h3")
        for element in elements:
            if element.get_attribute('translate') == "LABEL.SORRY_NO_ITEMS_FOUND":
                return 1
        if driver.current_url != url:
            return 1
        return 0


def main():
    highs = [22, 30, 36, 43, 51, 59, 67, 76, 85, 90]
    start = 10

    scraper = GSEScraper()

    for end in highs:
        scraper.process(start, end)
        start = end + 1

    scraper.close()


if __name__ == "__main__":
    main()
