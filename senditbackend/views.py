from django.http import HttpResponse

import json
import pymysql
import datetime

f = open('../senditsecrets.JSON', 'r')
secrets = json.load(f)


def get_db():
    return pymysql.connect(secrets['host'],
                           secrets['user'],
                           secrets['password'],
                           secrets['db'])


def validate_date(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def validate_integer(integer_text):
    try:
        int(integer_text)
        return True
    except ValueError:
        return False


def index(request):
    return HttpResponse(json.dumps({'version': 1.2}))


def addscore(request):
    params = request.POST
    if all(x in params for x in ['username', 'score', 'date']):
        username = params['username']
        score = params['score']
        date = params['date']
        if not validate_date(date):
            error = create_error(2, 'Invalid date')
            return HttpResponse(json.dumps(error, indent=4))
        if not validate_integer(score):
            error = create_error(3, 'Invalid score')
            return HttpResponse(json.dumps(error, indent=4))
        db = get_db()
        cur = db.cursor()
        sql = """
        INSERT INTO `scores` (`id`, `username`, `score`, `date`) VALUES (DEFAULT, %s, %s, %s)
        """
        try:
            cur.execute(sql, (username, score, date))
            db.commit()
            return HttpResponse()
        except pymysql.Error as e:
            print(e)
            db.rollback()
            error = create_error(4, 'Database error')
            return HttpResponse(json.dumps(error, indent=4))
    else:
        error = create_error(1, 'Insufficient parameters')
        return HttpResponse(json.dumps(error, indent=4))


def scores(request):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM `scores` ORDER BY `score` DESC LIMIT 50")
    results = cur.fetchall()

    data = []
    for row in results:
        data.append({'username': row[1], 'score': row[2], 'date': str(row[3])})

    return HttpResponse(json.dumps(data, indent=4, default=json))


def create_error(error_code, error_description):
    return {'Error': {'Code': error_code, 'Description': error_description}}
