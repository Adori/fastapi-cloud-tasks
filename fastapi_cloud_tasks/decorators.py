def task_default_options(**kwargs):
    def wrapper(fn):
        fn._delayOptions = kwargs
        return fn

    return wrapper
