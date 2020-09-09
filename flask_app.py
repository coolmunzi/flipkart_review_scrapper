from flask import Flask, render_template, url_for, request, redirect
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo

app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        searchString = request.form['content']
        try:
            client = pymongo.MongoClient("mongodb+srv://munjal:munjal@cluster0.1jkuo.mongodb.net/crawler_db?retryWrites=true&w=majority")
            crawlerdb=client.get_database('crawler_db')
            db = crawlerdb.crawler_col
            reviews = db[searchString].find({})
            if reviews.count() > 0:
                return render_template('results.html', reviews=reviews)
            else:
                table = db[searchString]
                filename = searchString + ".csv"
                fw = open(filename, "w")
                headers = "Product, Customer Name, Rating, Heading, Comment \n"
                fw.write(headers)
                reviews = []

                def scrap_html(review_link):
                    reviews_page = requests.get(review_link)
                    reviews_html = bs(reviews_page.text, "html.parser")
                    commentboxes = reviews_html.find_all('div', {'class': "_1PBCrt"})  # Getting View All Reviews

                    for commentbox in commentboxes:
                        try:
                            name = commentbox.find('p', {"class": "_3LYOAd _3sxSiS"}).text

                        except:
                            name = 'No Name'

                        try:
                            rating = commentbox.div.div.div.div.text

                        except:
                            rating = 'No Rating'

                        try:
                            commentHead = commentbox.div.div.p.text
                        except:
                            commentHead = 'No Comment Heading'
                        try:
                            custComment = commentbox.find('div', {"class": "qwjRop"}).div.div.text
                        except:
                            custComment = 'No Customer Comment'
                        fw.write(
                            searchString + "," + name.replace(",", ":") + "," + rating + "," + commentHead.replace(",",
                                                                                                                   ":") + "," + custComment.replace(
                                ",", ":") + "\n")
                        mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
                                  "Comment": custComment}
                        x = table.insert_one(mydict)
                        reviews.append(mydict)

                # Find the search string in flipkart
                flipkart_url = "https://www.flipkart.com/search?q=" + searchString
                uClient = uReq(flipkart_url)
                flipkartPage = uClient.read()
                uClient.close()
                flipkart_html = bs(flipkartPage, "html.parser")
                bigboxes = flipkart_html.findAll("div", {"class": "bhgxx2 col-12-12"})

                #Going to 1st product page
                del bigboxes[0:3]
                box = bigboxes[0]
                productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
                prodRes = requests.get(productLink)
                prod_html = bs(prodRes.text, "html.parser")

                # Going to first page of reviews and scrapping reviews
                allReviewbutton= prod_html.find("div", {"class" : "swINJg _3nrCtb"})
                first_page_reviews="https://www.flipkart.com" + allReviewbutton.parent['href']
                scrap_html(first_page_reviews)

                def find_next(review_link):
                    reviews_page = requests.get(review_link)
                    reviews_html = bs(reviews_page.text, "html.parser")
                    return reviews_html.find('a', {'class': '_3fVaIS'})

                #Going to next pages
                next_page = find_next(first_page_reviews)
                while(next_page):
                    review_page= "https://www.flipkart.com" + next_page['href']
                    scrap_html(review_page)
                    next_page = find_next(review_page)

                return render_template('results.html', reviews=reviews)
        except:
            return 'something is wrong'
            # return render_template('results.html')
    else:
        return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
