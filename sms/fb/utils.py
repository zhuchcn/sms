# In the current version of pyppeteer, the browser is closed for every ~20 
# seconds. This bug isn't fixed yet. The following work around is provided by:
# https://github.com/pyppeteer/pyppeteer2/issues/6
def disable_timeout_pyppeteer():
    import pyppeteer.connection
    original_method = pyppeteer.connection.websockets.client.connect
    def new_method(*args, **kwargs):
        kwargs['ping_interval'] = None
        kwargs['ping_timeout'] = None
        return original_method(*args, **kwargs)

    pyppeteer.connection.websockets.client.connect = new_method
