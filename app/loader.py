api_key = 'AIzaSyCHbUeQLgUxniHqyWtEUZ2eTJ4mvs5-nqY'

import numpy as np

#from eventregistry import *

from lxml.html import fromstring
from requests import get
import lxml.html
import urllib.request, urllib.parse
import json
import requests
import sys
import pickle
import pandas as pd
import nltk


def query_er(claim):
    er = EventRegistry(apiKey = api_key)
    q = QueryArticlesIter(conceptUri = er.getConceptUri(claim))

    res = []
    for art in q.execQuery(er, sortBy = "date"):
        res.append(art)

    return res


def query_er2(claim):
    er = EventRegistry(apiKey = api_key)
    q = QueryArticles()
    # set the date limit of interest
    q.setDateLimit(datetime.date(2014, 4, 16), datetime.date(2014, 4, 28))
    # find articles mentioning the company Apple
    q.addConcept(er.getConceptUri("Apple"))
    # return the list of top 30 articles, including the concepts, categories and article image
    q.addRequestedResult(RequestArticlesInfo(page = 1, count = 30,
        returnInfo = ReturnInfo(articleInfo = ArticleInfoFlags(concepts = True, categories = True, image = True))))
    res = er.execQuery(q)

def get_title(url):

    try:
        page = urllib.request.urlopen(url)
        t = lxml.html.parse(page)
        return t.find(".//title").text
    except Exception as e:
        print("Unexpected error:", e)
        return ""

def get_source(url):
    return url[ url.find('www') + 0 : url.find('.com') + 4]

def web_search(claim):
    url = 'https://www.google.com/search?'

    final_url = url + urllib.parse.urlencode({'q': claim})

    raw = get(final_url).text
    page = fromstring(raw)

    res = []

    for result in page.cssselect(".r a"):
        url = result.get("href")
        if url.startswith("/url?"):
            url = parse_qs(urlparse(url).query)['q']
        res.append(url[0])

    return res

def web_search_title(claim):
    links = web_search(claim)
    titles = [get_title(l) for l in links]
    sources = [get_source(l) for l in links]

    return (links, titles, sources)



def query_b(claim, use_cache=False):
    """
    get search results (from google)
    use_cache: if the claim is in the train data, skip google search
    """
    res_code = 0
    error = None
    list_claim = pickle.load(open('list_claim.pkl', 'rb'), encoding="utf8")
    if use_cache and claim in list_claim:
        # claim in the dataset, load it
        data_all = pd.read_csv('edata_all.csv')
        rel_data = data_all[ data_all.claimHeadline == claim]
        sources = rel_data.source.tolist()
        titles = rel_data.articleHeadline.tolist()
        links = rel_data.url.tolist()
        res = {'items': [{'displayLink': s, 'title': t, 'link': l} for s, t, l in zip(sources, titles, links)]}
        return res, error

    try:
        subscription_key = "INSERT YOUR KEY HERE"
        search_url = "https://api.cognitive.microsoft.com/bing/v7.0/search"
        search_term = claim;

        headers = {"Ocp-Apim-Subscription-Key": subscription_key,}
        params = {"q": search_term, "textDecorations": True, "textFormat": "HTML"}
    
        response = requests.get(search_url, headers=headers, params=params)
        res_code = response.status_code
        response.raise_for_status()

        search_results = response.json()
        res = search_results

        if len(res['webPages']['value']) == 0: raise Exception("no bing res")
    except Exception as e:
        if (res_code == 403 or res_code == 429):
            error = 'Results may not be reliable'
        # fall back to directly scrape
        print(e)
        print("fall back to directly scrape")
        (links, titles, sources) = web_search_title(claim)
        res = {'items': [{'displayLink': s, 'title': t} for s, t in zip(sources, titles)]}

    return res, error

def process_b(b, claim):
    sources = []
    headlines= []
    urls = []

    if ('webPages' in b.keys()):
        for i in b['webPages']['value']:
            source_t = urllib.parse.urlsplit(i['url'])
            source = source_t[1]

            try:
                headline = i['name']
            except:
                headline = i['url']

            sources.append(source)
            headlines.append(headline)

            urls.append(str(i['url']))
    else:
        for i in b['items']:
            source = i['displayLink']
            try:
                headline = i['pagemap']['newsarticle'][0]['headline']
            except:
                headline = i['title']

            sources.append(source)
            headlines.append(headline)

            urls.append(str(i['link']))


    n = len(sources)

    df = pd.DataFrame({ 'claimHeadline': [claim] * n, \
                        'articleHeadline': headlines, \
                        'claimId': [0] * n, \
                        'articleId': range(n) } )

    return (sources, df, urls)

from .features import *

train_data1, X1, train_data2, X2, test_data, X_test = get_data()
# train_data = features.get_dataset('url-versions-2015-06-14-clean-train.csv')
# X, y = features.split_data(train_data)
# X = feaures.p.pipeline.fit_transform(X)

def get_feature_names():
    fu = p.pipeline.steps[0][1]
    bow_transform = fu.transformer_list[0][1]
    vocab = bow_transform.cv.vocabulary_
    v = {v:k for (k, v) in vocab.items()}
    fn = [v[i] for i in range(len(v))]
    fn += ['QuestionMark',
           'Word2VecSimilaritySemantic',
           'AlignedPPDBSemantic',
           'NegationAlignment',
           'DependencyRootDepth 1',
           'DependencyRootDepth 2'
           ]
    fn += ['SVOTransform ' + str(i) for i in range(12)]
    return fn
    

def get_features(df):
    xt = p.pipeline.transform(df)
    return xt

def get_features_ch(claim, headline):
    df = pd.DataFrame({ 'claimHeadline': [claim], \
                        'articleHeadline': [headline], \
                        'claimId': [0], \
                        'articleId': [0] } )

    xt = p.pipeline.transform(df)
    return xt

def get_claim_f(dic_s, sources, stances, l = 724):
    f = np.zeros((1, l))
    for so, st in zip(sources, stances):
        if so not in dic_s: continue
        sid = dic_s[so] - 1 # 1-index to 0-index
        f[0, sid] = st

    return f


def get_rep(dic_s, sources, clf):
    res = []
    for so in sources:
        if so not in dic_s:
            res.append(0)
            continue
        sid = dic_s[so] - 1 # 1-index to 0-index
        rep = sum(abs(clf.coef_[:, sid]))
        rep = 1 if rep > 1 else rep
        rep = -1 if rep < -1 else rep
        res.append(rep)
    return res

def get_coef(dic_s, sources, clf):
    res = []
    for so in sources:
        if so not in dic_s:
            res.append(0)
            continue
        sid = dic_s[so] - 1 # 1-index to 0-index
        coef = clf.coef_[0, sid]
        res.append(coef)
    return res


def get_highlight(clf_stance, xt, df):
    fn = pickle.load(open('feature_names.pkl', 'rb'), encoding="utf8")
    n = len(df)
    hh = []
    for i in range(n):
        headline = ' ' + df.articleHeadline[i] + ' '
        x = xt[i,:]
        for j in np.nonzero(x)[1]:
            if max(clf_stance.coef_[:, j]) > 0.1:
                #color = ['#fdae61', '#ffffbf', '#abd9e9'][np.argmax(clf_stance.coef_[:, j])]
                stance_class = ['stance_deny', 'stance_neutral', 'stance_support'][np.argmax(clf_stance.coef_[:, j])]
                if headline.lower().find(' ' + fn[j] + ' ') > -1:
                    start = headline.lower().find(' ' + fn[j] + ' ') + 1
                    end = start + len(fn[j])
                    headline = headline[:end] + '</span>' + headline[end:]
                    #headline = headline[:start] + '<span style="background-color: {}">'.format(color) + headline[start:]
                    headline = headline[:start] + '<span class={}>'.format(stance_class) + headline[start:]
        hh.append(headline[1:-1])
    return hh


def answer_loader(claim, res_b, for_api = False):
    """
    for_api: return results for api call
    """
    #(cmv, dic_s) = pickle.load(open('save_cmv_dics.pkl'))
    with open('save_clf.pkl', 'rb') as f:
        (clf_vera, clf_stance, dic_s) = pickle.load(f, encoding="latin1")

    (sources, df, urls) = process_b(res_b, claim)
    xt = get_features(df)

    stances = clf_stance.predict(xt)
    claim_f = get_claim_f(dic_s, sources, stances)

    vera = clf_vera.predict_proba(claim_f)
    rep = get_rep(dic_s, sources, clf_vera)

    clf_vera_coef = get_coef(dic_s, sources, clf_vera)
    clf_vera_intc = clf_vera.intercept_

    if for_api:
        stances_p = clf_stance.predict_proba(xt)
        
        # extract crowd label
        (res, score, aid) = pickle.load(open('crowd_labs.pkl', 'rb'), encoding="latin1")
        crowd_stance_lab = []
        for i, row in df.iterrows():
            headline = row['articleHeadline'].lower()
            if headline in aid:
                a = aid[headline]
                if a in score:
                    crowd_stance_lab.append(score[a])
                else:
                    crowd_stance_lab.append(-2)
            else:
                crowd_stance_lab.append(-2)
            
        hh = get_highlight(clf_stance, xt, df)        
        return (sources, df, vera, stances_p, rep, clf_vera_coef, clf_vera_intc, urls, crowd_stance_lab, hh)

    return (sources, df, vera)


def gen_res_str(sources, df, vera):
    headlines = df.articleHeadline

    res = ""
    for s, h in zip(sources, headlines):
        res = res + s + ': ' + h + '<br>'

    pf = int(vera[0][0]* 100)
    pu = int(vera[0][1]* 100)
    pt = int(vera[0][2]* 100)
    res = res + 'Predict veracity: ' + str(pf) + '% False, ' + \
                                    str(pu) + '% Unknown, ' +  \
                                    str(pt) + '% True, '

    return res


def web_search2(claim):
    url = 'https://www.google.com/search?'

    final_url = url + urllib.parse.urlencode({'q': claim})

    response = requests.get(final_url)

    html = response.text

    return html