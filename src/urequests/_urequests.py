# urequests.py


class Response:
    def __init__(self, text="", status_code=200):
        self.text = text
        self.status_code = status_code

    def json(self):
        return {}

    def close(self):
        pass


def get(url, **kwargs):
    return Response()


def post(url, **kwargs):
    return Response()


def put(url, **kwargs):
    return Response()


def delete(url, **kwargs):
    return Response()
