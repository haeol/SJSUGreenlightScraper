# San Jose State Greenlight scraper objects
# Written by Kevin Tom

import threading
import Queue
import re

import mechanize
from bs4 import BeautifulSoup

class GreenlightSession(object):
    
    def __init__(self, username='', password=''):
        self.username = username
        self.password = password
        self.browser = mechanize.Browser()

        if username and password:
            self.login()


    def login(self):
        self.browser.open('http://wpe.sjsu.edu/greenlight/html/login.html')
        self.browser.select_form(name='empirical')
        self.browser.form['userID'] = self.username
        self.browser.form['userPW'] = self.password
        response = self.browser.submit()
        

    def browse(self, url):
        return self.browser.open(url).read()


class GreenlightScraper(object):
    
    # only around 400 organizations, small data set

    def __init__(self, greenlightSession, threads=5):
        '''
        orgs = {
            'name' : {
                'classification' : 'string',
                'officers' : [],
                'description' : 'string'
            }
        }
        '''
        self.session = greenlightSession
        self.orgs = {}
        self.max_threads = threads

        # One queue for failed requests, other for successful requests
        self.queue = Queue.Queue()
        self.queue2 = Queue.Queue()

        self.purpose_matcher = re.compile('Purpose: ([\s\S]+?)(?=(?:<br><br>|<br\/><br\/>))')

    
    def scrape(self, retry=10):

        self.scrape_directory()
        self.scrape_organizations()
        print('Retrying scrape session on failed requests')

        while retry > 0:
            print('Retry attempts remaining: ' + str(retry))
            if self.retry_scrape():
                break
            retry -= 1
        return bool(retry)


    def scrape_directory(self):

        url = 'http://wpe.sjsu.edu/greenlight/pages/public/'
        directory = 'http://wpe.sjsu.edu/greenlight/pages/public/directory.php'

        soup = BeautifulSoup(self.session.browse(directory), 'html.parser')
        div = soup.find_all('div', {'id' : 'col_1_of_2_land'})

        for table_html in div:
            table = table_html.find_all('tr')
            for row in table:
                tds = row.find_all('td')
                if tds:
                    self.orgs[tds[0].text] = {}
                    self.orgs[tds[0].text]['classification'] = tds[1].text
                    self.orgs[tds[0].text]['officers'] = []

                    link = row.find_all(href=True)[0]['href'].replace(' ', '%20')
                    print("Enqueuing: " + tds[0].text)
                    self.queue.put( ( tds[0].text, url + link ) ) 


    def scrape_organizations(self):

        for i in xrange(self.max_threads):
            t = threading.Thread(target=self.thread_worker)
            t.daemon = True
            t.start()

        print('Thread waiting')
        self.queue.join()
        print('Done\n\n')


    def scrape_org(self, link):

        print('Processing organization: ' + link[0]) # org name

        try:
            soup = BeautifulSoup(self.session.browse(link[1]), 'html.parser')
            div = soup.find_all('div', {'id' : 'col_1_of_2_land'})
            description = re.search(self.purpose_matcher, str(div[0])).group(1).replace('\n\n', '\n')
            self.orgs[link[0]]['description'] = description

            for table_html in div:
                table = table_html.find_all('tr')

                for admin in table:
                    # Role,         First Name,   Last Name,    Email
                    # info[0].text, info[1].text, info[2].text, info[3].text]
                    info = admin.find_all('td')
                    if info:
                        self.orgs[link[0]]['officers'].append(info[3].text)

        except AttributeError as e:
            print e
            self.queue2.put(link)
            print 'Error, putting to queue2'
        except URLError as e:
            print(e)
            self.queue2.put(link)
            print 'URL Error, putting into queue2'


    def thread_worker(self):
        while True:
            link = self.queue.get()
            self.scrape_org(link)
            self.queue.task_done()


    def retry_scrape(self):
        print('Failed scrapes: ' + str(self.queue2.qsize()))
        if self.queue2.qsize() > 0:
            holder = self.queue
            self.queue = self.queue2
            self.queue2 = holder

        while not self.queue.empty():
            self.scrape_org(self.queue.get())

        if not self.queue2.empty():
            print('Still need to retry')

        return self.queue2.empty()
        

