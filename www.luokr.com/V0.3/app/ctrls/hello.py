#coding=utf-8

from basic import BasicCtrl

class HelloCtrl(BasicCtrl):
    def get(self):
        self.write('Hello! ' + self.timer().strftime('%F %TT%Z', self.timer().localtime(self.stime())))
