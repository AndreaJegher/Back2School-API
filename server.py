from app import app
import os

if __name__ == '__main__':
    app.secret_key = 'fl4sk_1s_fun_t0_us3'
    app.run(threaded=True, use_reloader=True)
