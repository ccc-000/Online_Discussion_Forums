import json


def json2Request(json_str: str):
    dict_in = json.loads(json_str)
    return dict2Request(dict_in)


def dict2Request(input_dic: dict):
    return Request(
        command=input_dic["command"],
        user=input_dic["user"],
        parameters=input_dic["parameters"]
    )


def json2Response(json_str: str):
    dict_in = json.loads(json_str)
    return dict2Response(dict_in)


def dict2Response(input_dic: dict):
    return Response(
        code=input_dic["code"],
        message=input_dic["message"]
    )


class Request:

    def __init__(self, command: str = "", user: str = "", parameters: dict = {}):
        self.command = command
        self.user = user
        self.parameters = parameters

    def __dict__(self):
        return {
            'command': self.command,
            'user': self.user,
            'parameters': self.parameters
        }

    def to_json(self):
        return json.dumps(self.__dict__())


# The response schema from server.
# Arguments:
#   code: 0 -> unknown error
#         1 -> successful
#         2 -> permission denied
#         3 -> Unknown user.
#
#   message: from server.
class Response:
    def __init__(self, code: int = 0, message: str = ""):
        self.code = code
        self.message = message

    def __dict__(self):
        return {
            'code': self.code,
            'message': self.message
        }

    def to_json(self):
        return json.dumps(self.__dict__())
