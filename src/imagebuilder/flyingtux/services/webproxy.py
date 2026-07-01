from metux.util.fs import mkdir
from os_service import Base
from os.path import basename, dirname

class WebProxy(Base):

    def write_acl(self, fn):
        acl_ip = ('%s_ip' % self.my_appname)
        mkdir(dirname(fn))
        with open(fn, "w") as f:
            f.write("acl %s src %s\n" % (acl_ip, self.my_runner.ip_address))
            cnt = 0
            for wl in self['whitelist']:
                acl_url = '%s_wl%d' % (self.my_appname, cnt)
                f.write("acl %s url_regex %s\n" % (acl_url, wl))
                f.write("http_access allow %s %s\n" % (acl_ip, acl_url))
                cnt = cnt+1

    def compute(self):
        self.my_appname = self.get_app_name()
        proxy = self.my_runner.start_web_proxy()
        self.info("web proxy is: "+proxy)
        self.add_env('http_proxy', proxy)
        self.add_env('https_proxy', proxy)
        self.add_env('ftp_proxy', proxy)
#        self.write_acl(
#            self.my_runner['TARGET::dynconf-dir']+
#            '/squid/%s.conf' % self.my_appname)
        self.write_acl(self.my_runner['TARGET::web-proxy::conf-source']+'/%s.conf' % self.my_appname)
