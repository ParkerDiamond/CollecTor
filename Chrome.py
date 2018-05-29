import sys
import subprocess
import psutil
import signal
import logging
from pyvirtualdisplay import Display

from Tor import Tor

import selenium
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logger = logging.getLogger()

class Chrome:

    driver = '/usr/bin/chromedriver'
    arguments = ['--timeout=100',
                '--bwsi',
                '--disable-application-cache',
                '--dns-prefetch-disable',
                '--disable-web-security',
                '--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE localhost"']

    exclusions = ["disable-web-resources","disable-background-networking"]

    #extensions = ["/home/cubia/Khoshekh/scripts/extensions/ublock_origin.crx"]
    extensions = []

    socks_port = None
    browser = None

    def __init__(self, socks_port='9050', **kwargs):
        self.socks_port = socks_port

        for key,value in kwargs.items():
            setattr(self, key, value)
        
        self.arguments.append('--proxy-server=socks5://localhost:{0}'.format(self.socks_port))
        options = webdriver.ChromeOptions()

        for argument in self.arguments:
            options.add_argument(argument)

        options.add_experimental_option('excludeSwitches', self.exclusions)

        for extension in self.extensions:
            options.add_extension(extension)

        capabilities = options.to_capabilities()
        self.browser = webdriver.Chrome(self.driver, desired_capabilities = capabilities)

        self.browser.set_window_position(0, 0)
        self.browser.set_window_size(800, 600)
        self.browser.set_script_timeout(30)
        self.browser.set_page_load_timeout(30)

    class CustomTimeoutException(Exception):
        pass

    def timeout(self, signum, frame):
        raise self.CustomTimeoutException('Reached a timeout set by the user')

    def get(self, url, timeout=30):
        signal.signal(signal.SIGALRM, self.timeout)
        try:
            signal.alarm(timeout)
            self.browser.get(url)
            signal.alarm(0)
        except self.CustomTimeoutException as ex:
            pass

    def stop(self):
        signal.signal(signal.SIGALRM, self.timeout)
        try:
            signal.alarm(5)
            self.browser.quit()
            signal.alarm(0)
        except self.CustomTimeoutException as ex:
            pass

        if self.browser.service.process:
            try:
                parent = psutil.Process(self.browser.service.process.pid)
                children = parent.children(recursive=True)
                for child in children:
                    subprocess.Popen(['sudo','kill','-9',str(child.pid)])            
                subprocess.Popen(['sudo','kill','-15',str(parent.pid)])            
            except psutil.NoSuchProcess:
                return

if __name__ == "__main__":
    logger.log(logging.DEBUG,'STARTING DEBUG TEST OF CHROME WRAPPER')

    TorWrapper = Tor('','9050','7001')
    tor_proc, tor_ctrl = TorWrapper.start()
    if not (tor_proc and tor_ctrl):
        sys.exit()

    display = Display(visible=0,size=(800,600))
    display.start()
    chromeWrapper = Chrome('7001', driver = '/home/cubia/chromedriver')
    chromeWrapper.get('https://torguard.net/whats-my-ip.php')
    chromeWrapper.stop()
    display.sendstop()
    del(display)

    tor_proc.kill()

    logger.log(logging.DEBUG,'FINISHED DEBUG TEST OF CHROME WRAPPER')
