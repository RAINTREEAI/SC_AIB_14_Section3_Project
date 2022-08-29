from flask import Flask, render_template, request
import requests
import json
import pickle
import psycopg2

def getSearchBook(keyword):
    #api Key
    TTBKey = "ttbraintree10101841001"
    book_search = []
    # QueryType : 신간 전체
    # SearchTarget : 중고
    # SubSearchTarget : 도서
    # MaxResults : 50개 출력
    # start : i page부터
    # output : json
    # OptResult : 해당 상품에 등록된 중고상품 정보
    url = f"http://www.aladin.co.kr/ttb/api/ItemSearch.aspx?ttbkey={TTBKey}&Query={keyword}&QueryType=Keyword&MaxResults=1&start=1&SearchTarget=Book&output=js&Version=20131101"
    
    res = requests.get(url)
    items = json.loads(res.text)['item']
    
    # itemId 아이디
    # title 제목
    # link 결과와 관련된 알라딘 페이지
    # author 지은이
    # pubDate 출판일
    # isbn isbn코드
    # priceSales 판매가
    # priceStandard 정가
    # stockstatus 재고상태
    # cover 커버
    # categoryId 카테고리 아이디
    # categoryName 카테고리 이름
    # publisher 출판사
    # salesPoint 판매지수
    # adult 성인 등급 여부
    # customerReviewRank 회원리뷰평점
    # bestRank 베스트셀러 순위 정보
    # usedList < aladinUsed < itemCount 알라딘 직접 배송 보유 상품수
    # usedList < aladinUsed < minPrice 알라딘 직접 배송 최저가
    # usedList < userUsed< itemCount 회원 직접 배송 보유 상품수
    # usedList < userUsed< minPrice  회원 직접 배송 최저가
    for item in items:
        book_dict = {}
        book_dict['title'] = item['title']
        book_dict['author'] = item['author'].split(',')[0].split('(')[0]
        book_dict['pubDate'] = item['pubDate']
        book_dict['cover'] = item['cover']
        book_dict['priceStandard'] = item['priceStandard']
        book_dict['categoryName'] = item['categoryName'].split('>')[3] if len(item['categoryName'].split('>')) > 3 else item['categoryName'].split('>')[2]
        book_dict['publisher'] = item['publisher']
        book_dict['salesPoint'] = item['salesPoint']
        book_dict['customerReviewRank'] = item['customerReviewRank']
        try:
            book_dict['bestRank'] = item['bestRank']
        except:
            book_dict['bestRank'] = 0

        book_search.append(book_dict)

    return book_search

def dbcon():
    host = 'arjuna.db.elephantsql.com'
    user = 'qvuafktk'
    password = 'LdetCHWFFCBBmPrYzjYR_n2NOnPKpCsg'
    database = 'qvuafktk'

    connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    return connection

def create_table():
    conn = dbcon()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS usersearch (
                    title           VARCHAR,
                    pubDate         INT,
                    priceStandard   INT,
                    ReviewRank      INT,
                    pricePredict    INT)
                """)
    conn.commit()
    conn.close()

def insert_data(title, pubDate, priceStandard, ReviewRank, pricePredict):
    conn = dbcon()
    cur = conn.cursor()
    setdata = (title, pubDate, priceStandard, ReviewRank, pricePredict)
    cur.execute("INSERT INTO usersearch VALUES (%s, %s, %s, %s, %s)", setdata)
    conn.commit()
    conn.close()

def create_app():
    
    with open('used_book_price/model/model.pkl','rb') as pickle_file:
        model = pickle.load(pickle_file)
    app = Flask(__name__)

    app.config['JSON_AS_ASCII'] = False

    # 메인 페이지 라우팅
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # 도서 검색 페이지 라우팅
    @app.route('/search')
    def search():
        return render_template('search.html')

    # 도서 겸색 결과 처리
    @app.route('/search/result', methods = ['POST', 'GET'])
    def result():
        keyword = str(request.args.get('keyword'))
        bookInfo = getSearchBook(keyword)
            
        return render_template('result.html', info=bookInfo)

    # 직접 입력 페이지 라우팅
    @app.route('/direct')
    def direct():
        return render_template('direct.html')

    # 검색 > 데이터 예측 처리
    @app.route('/predict', methods=['POST'])
    def search_pred():
        data1 = request.form['pubDate']
        data2 = request.form['priceStandard']
        data3 = request.form['ReviewRank']
        data4 = request.form['title']
        arr = [[int(data1), int(data2), int(data3)]]
        pred = model.predict(arr)
        create_table()
        insert_data(data4, data1, data2, data3, int(pred.round(-2)))

        return render_template('predict.html', data=int(pred.round(-2)))

    # 직접 입력 > 데이터 예측 처리
    @app.route('/predict', methods=['POST'])
    def pred():
        data1 = request.form['pubDate']
        data2 = request.form['priceStandard']
        data3 = request.form['ReviewRank']
        data4 = request.form['title']
        arr = [[int(data1), int(data2), int(data3)]]
        pred = model.predict(arr)
        create_table()
        insert_data(data4, data1, data2, data3, int(pred.round(-2)))

        return render_template('predict.html', data=int(pred.round(-2))), 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8000, debug=True)