class ViewItem:
    def __init__(self, name, lable, fmt):
        self.name = name
        self.lable = lable
        self.fmt = fmt

    def __json__(self):
        return {
            "name": self.name,
            "lable": self.lable,
        }


class InputItem:
    def __init__(self, name, lable, fmt):
        self.name = name
        self.lable = lable
        self.fmt = fmt

    def __json__(self):
        return {
            "name": self.name,
            "lable": self.lable,
        }


class ViewDef:
    def __init__(self, name, lable, items):
        self.name = name
        self.lable = lable
        self.items = items

    def __json__(self):
        return {
            "name": self.name,
            "lable": self.lable,
            "items": [item.__json__() for item in self.items],
        }
