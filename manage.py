from Info import create_app

app = create_app('product')


@app.route('/')
def index():
    # session['a1'] = 'python'
    # app.Redis_sto.set('a1', 'xiaoyifan')
    return 'index111'


if __name__ == '__main__':
    app.run()
