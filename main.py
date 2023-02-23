# GUI application to delete SIPs from the AV SIP Generator
# The script requires config.py to run
# A compiled stand-alone executable is available to downloaded from [url]

from requests.packages import urllib3
import wx
import requests
import json
import os
import config
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class MainFrame(wx.Frame):

    def __init__(self):
        super().__init__(parent=None, style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER | wx.STAY_ON_TOP,
                         title="Delete SIP", size=(200, 180))
        panel = wx.Panel(self)

        self.URL = config.URL
        self.USER = config.USER
        self.HOLD = config.HOLD
        self.sip_id = None

        font = wx.Font(10, wx.DECORATIVE, wx.DEFAULT, wx.NORMAL)
        bold_font = wx.Font(11, wx.DECORATIVE, wx.DEFAULT, wx.NORMAL)

        sip_text = wx.StaticText(panel, label='Enter SIP ID')
        sip_text.SetFont(font)

        self.enter_id = wx.TextCtrl(panel, size=(100, 25), style=wx.TE_CENTRE)

        button = wx.Button(panel, label='DELETE', size=(150, 50))
        button.SetFont(bold_font)
        button.Bind(wx.EVT_BUTTON, self.confirm_dialog)

        v_box = wx.BoxSizer(wx.VERTICAL)
        v_box.Add(sip_text, 0, wx.TOP | wx.CENTRE, 5)
        v_box.Add(self.enter_id, 0, wx.ALL | wx.CENTRE, 5)
        v_box.Add(button, 0, wx.ALL | wx.CENTRE, 5)

        v_box.Add((-1, 25))

        panel.SetSizer(v_box)

        self.report = self.CreateStatusBar(1)
        # self.report.SetStatusText('WARNING: delete is irreversible')
        self.Show()

        self.message = ''
        self.please_confirm = wx.MessageDialog(panel, self.message, caption='WARNING', style=wx.YES_NO | wx.CENTRE)

    def get_sip_status(self):
        self.sip_id = self.enter_id.GetValue()
        check_url = '{}/SIP/{}'.format(self.URL, self.sip_id)
        c = requests.get(check_url, verify=False)

        return c

    def confirm_dialog(self, event):
        sip_data = self.get_sip_status()
        status = sip_data.status_code

        if status == 200:
            data = json.loads(sip_data.text)
            sami_shelfmark = data['SamiCallNumber']
            sami_title = data['SamiTitle']
            message = 'SIP {}\n' \
                      '{}\n' \
                      '{}\n \n' \
                      'Click Confirm to DELETE\n \n' \
                      'WARNING: this will delete all data including audio files\n'  \
                      'The process is irreversible'.format(self.sip_id, sami_shelfmark, sami_title)

            self.please_confirm.SetMessage(message)
            self.please_confirm.SetYesNoLabels('&Confirm', '&Cancel')
            time.sleep(0.5)
            confirm_action = self.please_confirm.ShowModal()

            if confirm_action == wx.ID_YES:
                self.delete_sip()
            else:
                return

        elif status == 404:
            self.report.PushStatusText('{} does not exist'.format(self.sip_id))
            time.sleep(1)
            self.enter_id.Clear()
        else:
            self.report.PushStatusText('ERROR unable to to delete - status code: {}'.format(status))
            self.enter_id.write = ''

    def delete_sip(self):
        del_url = '{}/SIPs/SIP/{}/{}'.format(self.URL, self.USER, self.sip_id)

        d = requests.delete(del_url, verify=False)
        sip_folder = '\\{}\{}'.format(self.HOLD, self.sip_id)

        status = self.get_sip_status()
        if status.status_code == 404:
            if os.path.exists(sip_folder):
                try:
                    os.rmdir(sip_folder)
                    self.report.PushStatusText('{} DELETED'.format(self.sip_id))
                except Exception as e:
                    self.report.PushStatusText('{}: exception raised {}'.format(self.sip_id, e))
                    time.sleep(1)
                    self.enter_id.Clear()
            else:
                self.report.PushStatusText('{} DELETED'.format(self.sip_id))
                time.sleep(1)
                self.enter_id.Clear()
        else:
            get_error = json.loads(d.text)
            error = get_error['Errors']
            self.report.PushStatusText('ERROR unable to delete {}'.format(self.sip_id))
            time.sleep(1)
            self.enter_id.Clear()


if __name__ == '__main__':
    app = wx.App()
    frame = MainFrame()
    app.MainLoop()
