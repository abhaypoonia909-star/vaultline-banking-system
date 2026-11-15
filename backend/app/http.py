from flask import request


def client_ip():
    return request.remote_addr or "unknown"
