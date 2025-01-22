import requests
from requests import Response
from requests.exceptions import ConnectionError

from settings import Settings
from urlhelper import UrlHelper


class Kodi():
    player_id = None
    username = None
    password = None
    url_helper = None
    parent_params = None

    def __init__(self, username, password, ip_address, port):
        self.url_helper = UrlHelper(ip_address, port)
        self.ip_address = ip_address
        self.port = port
        self.username = username
        self.password = password
        self.parent_params = {}

    def Connect(self):
        try:
            # TODO Save settings based on response
            response = requests.get(self.url_helper.prepare_url_without_param('Player.GetActivePlayers'),
                                    auth=(self.username, self.password))
            settings = Settings()
            settings.Save({'ip_address': self.ip_address, 'port': self.port, 'username': self.username,
                           'password': self.password})
            return True
        except ConnectionError as conn_error:
            print(conn_error)
            return False

    def Handshake(self):
        try:
            self.player_id = self.GetActivePlayers()
            # print(self.player_id)
            if self.player_id is None:
                currentPlaying = 'Nothing is playing'
            else:
                currentPlaying = self.PlayerGetItem()
            return currentPlaying
        except ConnectionError as conn_error:
            # print(conn_error)
            return False

    def send_command_adapter(self, command_url: str):
        # newer version is no loger supporting everything over GET
        # have to transform into POST (dirty fix)
        # Url expected:http://192.168.0.114:8080/jsonrpc?request={"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}
        command_tuple = command_url.split("?request=")
        response = requests.post(
            command_tuple[0],
            data=command_tuple[1],
            headers={"Content-Type": "application/json"},
            auth=(self.username, self.password)
        )
        return response

    def GetActivePlayers(self):
        response = self.send_command_adapter(self.url_helper.prepare_url_without_param('Player.GetActivePlayers'))
        response = response.json()['result']
        # check if something is playing
        if len(response) == 0:
            return None
        else:
            return response[0]['playerid']

    def PlayerGetItem(self):
        params = self.url_helper.prepare_param(self.parent_params, {'name': 'playerid', 'value': self.player_id})
        response = self.send_command_adapter(self.url_helper.prepare_url_with_param('Player.GetItem', params))
        self.parent_params = {}
        response = response.json()
        return response['result']['item']['label']

    def InputBack(self):
        response = self.send_command_adapter(self.url_helper.prepare_url_without_param('Input.Back'))
        self.ParseResponse(response)

    def InputLeft(self):
        response = self.send_command_adapter(self.url_helper.prepare_url_without_param('Input.Left'))
        self.ParseResponse(response)

    def InputRight(self):
        response = self.send_command_adapter(self.url_helper.prepare_url_without_param('Input.Right'))
        self.ParseResponse(response)

    def InputSelect(self):
        response = self.send_command_adapter(self.url_helper.prepare_url_without_param('Input.Select'))
        self.ParseResponse(response)

    def InputUp(self):
        response = self.send_command_adapter(self.url_helper.prepare_url_without_param('Input.Up'))
        self.ParseResponse(response)

    def InputDown(self):
        response = self.send_command_adapter(self.url_helper.prepare_url_without_param('Input.Down'))
        self.ParseResponse(response)

    def PlayPause(self):
        params = self.url_helper.prepare_param(self.parent_params, {'name': 'playerid', 'value': self.player_id})
        response = self.send_command_adapter(self.url_helper.prepare_url_with_param('Player.PlayPause', params))
        self.parent_params = {}
        self.ParseResponse(response)

    def Stop(self):
        params = self.url_helper.prepare_param(self.parent_params, {'name': 'playerid', 'value': self.player_id})
        response = self.send_command_adapter(self.url_helper.prepare_url_with_param('Player.Stop', params))
        self.parent_params = {}
        self.ParseResponse(response)

    def Previous(self):
        parent_params = self.url_helper.prepare_param(self.parent_params, {'name': 'playerid', 'value': self.player_id})
        parent_params = self.url_helper.prepare_param(self.parent_params, {'name': 'to', 'value': 'previous'})
        response = self.send_command_adapter(self.url_helper.prepare_url_with_param('Player.GoTo', parent_params))
        self.parent_params = {}
        self.ParseResponse(response)

    def Next(self):
        parent_params = self.url_helper.prepare_param(self.parent_params, {'name': 'playerid', 'value': self.player_id})
        parent_params = self.url_helper.prepare_param(self.parent_params, {'name': 'to', 'value': 'next'})
        response = self.send_command_adapter(self.url_helper.prepare_url_with_param('Player.GoTo', parent_params))
        self.parent_params = {}
        self.ParseResponse(response)

    def SetVolume(self, vol_type):
        params = self.url_helper.prepare_param(self.parent_params, {'name': 'volume', 'value': vol_type})
        response = self.send_command_adapter(self.url_helper.prepare_url_with_param('Application.SetVolume', params))
        self.parent_params = {}
        self.ParseResponse(response)

    def MuteVolume(self, val: bool):
        params = self.url_helper.prepare_param(self.parent_params, {'name': 'mute', 'value': val})
        response = self.send_command_adapter(self.url_helper.prepare_url_with_param('Application.SetMute', params))
        self.parent_params = {}
        self.ParseResponse(response)

    def ParseResponse(self, response: Response):
        status = response.status_code
        response = response.json()
        if status > 299 or 'error' in response:
            print(F'status = {status} body = {response}')
