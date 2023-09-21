"""
Define custom exceptions
"""
class Base(Exception):
    def __init__(self, *args, **kwargs):
        self.msg = (list(args)[0:1] + [""])[0]
        super(Base, self).__init__(*args, **kwargs)

    def __repr__(self):
        return repr(self.msg)

class UnknownTypeException(Base):
    _def_message = "Unknown type {}."

    def __init__(self, tp, msg=None):
        self._def_message = msg or self._def_message
        msg = self._def_message.format(tp)
        super(UnknownTypeException, self).__init__(msg)



class DataNotReady(Base):
    pass


class FileDoesNotExist(Base):
    pass


class FileExist(Base):
    pass

class SignError(Base):
    pass

class FileTypeNotAllow(Base):
    pass

class FileSizeLimit(Base):
    pass

class DoesNotExist(Base):
    pass

class ServerError(Base):
    pass

class FileNotSync(Base):
    pass

class JsonParseError(Base):
    pass
