
class AppContextManager:
    _instance = None
    _appctxt = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppContextManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def set_context(cls, appctxt):
        cls._appctxt = appctxt

    @classmethod
    def get_context(cls):
        return cls._appctxt