import functools
import random
import os

__all__ = (
    'get_send_handler',
    'get_recv_handler'
)

def _partial(func, *_args, **_kwargs):
    def fixed(*args, **kwargs):
        return func(*_args, *args, **_kwargs, **kwargs)
    return fixed

def send_photo(payload, ctx):
    user_id, arg = payload['user_id'], payload['arg']
    with open(arg, 'rb') as f:
        ctx.bot.send_photo(user_id, f)
    os.remove(arg)

def send_text(payload, ctx):
    user_id, arg = payload['user_id'], payload['arg']
    ctx.bot.send_message(user_id, arg)

def send_sticker(payload, ctx):
    user_id, arg = payload['user_id'], payload['arg']
    ctx.bot.send_sticker(user_id, arg)

SEND_HANDLERS = {
    'text': send_text,
    'photo': send_photo,
    'sticker': send_sticker
}

def get_send_handler(payload):
    handler = SEND_HANDLERS.get(payload['type'])
    if handler:
        return _partial( handler, payload)

def recv_text(message):
    return message.text

def recv_photo(message):
    print(message.photo)
    path = "temp_{0}.jpg".format(random.randint(100000, 999999))
    message.photo[-1].get_file().download(path)
    return path

def recv_sticker(message):
    return message.sticker.file_id

RECV_HANDLERS = {
    'text': recv_text,
    'photo': recv_photo,
    'sticker': recv_sticker
}

def get_recv_handler(message):
    for m_type, handler in RECV_HANDLERS.items():
        if getattr(message, m_type):
            return m_type, handler
    return None, None
