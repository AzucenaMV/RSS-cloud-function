import feedparser
from bs4 import BeautifulSoup
import re 
import pandas as pd
from google.cloud import language_v1
from google.cloud.language_v1 import enums

urls = ["http://feeds.bbci.co.uk/news/world/rss.xml",
        "http://www.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "http://feeds.reuters.com/reuters/topNews",
        "http://rss.cnn.com/rss/cnn_topstories.rss"
        ]

def rss_parser(tag, max_entries = 10, urls = urls):
  """
  It parses the urls and return a table with all the news that contains the tag word.
  """
  news = {}
  for url in urls:
    feed = feedparser.parse(url)
    for post in feed.entries:
      title = post.title.lower()
      date = post.get("published","")
      if (re.search(tag,title)) and (date != ""):
        aux = BeautifulSoup(post.description)
        text = re.sub("\n","",aux.get_text())
        news[post.link] = [date,post.title,text]
  if not news:
    return None
  else:
    table = pd.DataFrame.from_dict(news,orient='index', columns = ['raw_date','title','description'])
    table['date'] = pd.to_datetime(table.raw_date, infer_datetime_format=True) 
    table.sort_values(by=['date'],ascending=False,inplace = True)
    return table.head(max_entries)
    
def news_rss(request):
    """
    Takes JSON Payload {"tag": "coronavirus"} and returns a string with all the news
    """
    request_json = request.get_json()
    if request_json and 'tag' in request_json:
      tag = request_json['tag']
      res = rss_parser(tag)
      output = []
      if res is not None:
        for index, row in res.iterrows():
          score = round(sentiment_analysis(row['description']),2)
          output.append("Date: {} \nTitle: {} \nDescription: {} \nSentiment score: {} \nLink: {}\n".format(row['raw_date'],row['title'],row['description'],score,index))
        return "\n".join(output)
      else:
        return "No news were found with the tag: {}".format(tag)
    else:
      return "No payload"

def sentiment_analysis(text="YOUR_TEXT_FOR_SENTIMENT_ANALYSIS"):
    """
    This function receives a text and uses Google API to get the sentiment score
    """
    client = language_v1.LanguageServiceClient()
    type_ = enums.Document.Type.PLAIN_TEXT
    language = "en"
    document = {"content": text, "type": type_, "language":language}
    encoding_type = enums.EncodingType.UTF8

    response = client.analyze_sentiment(
        document, 
        encoding_type=encoding_type
        )
    return response.document_sentiment.score
