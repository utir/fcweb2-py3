from flask import session, render_template, redirect, url_for, request,Markup, jsonify, make_response
from run import app
import json
import pickle
import random
from .server import *
import numpy as np
import pandas as pd
import markdown2

AMAZON_HOST_TEST = "https://workersandbox.mturk.com/mturk/externalSubmit"
AMAZON_HOST =  "https://www.mturk.com/mturk/externalSubmit"
TASK_TIME = 600000

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('form_submit.html', error=None)

@app.route('/results/', methods=['GET', 'POST'])
def results():
    claim=request.form['claim']
    if (not claim and request.form["button"] != "Try a Random Claim"):
        return redirect(url_for('.index', error='Error: Please enter a claim.'))
    print ("Query string is")
    print(claim)
    print(request.form["button"])

    if request.form["button"] == "Try a Random Claim":
        list_claims = pickle.load(open('list_claim.pkl', 'rb'), encoding="utf8")
        claim = random.choice(list_claims)

    res = api_call(claim, use_cache=True)
    #res_str = json.dumps(res, indent=4, sort_keys=True)
    headlines = [a['headlines'] for a in res['articles']]
    headlines = res['hh']
    sources = [a['sources'] for a in res['articles']]
    stances = [ [s for s in a['stance'] ] for a in res['articles']]
    stances = [ np.argmax(s) - 1  for s in stances] # stance = -1, 0, 1
    crowd_stance = res['crowd_stance']
    #stances = [ s[2] - s[0] for s in stances]
    #print stances
    veracity = [v*100 for v in res['veracity']]
    rep   = [a['reputation'] for a  in res['articles']]
    urls   = [u for u  in res['urls']]
    n = len(sources)
    error = res['error']

    return render_template("results.html", headlines=[Markup(headline) for headline in headlines], sources=sources, n=n,\
        veracity=veracity, stances=stances, claim=claim, rep=rep, urls=urls, crowd_stance=crowd_stance, error=res['error'])

@app.route('/demo')
def demo():
    return render_template('demo.html')

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/source_page/')
def source_page():
    source = request.args['source']

    data_all = pd.read_csv('edata_all.csv')
    rel_data = data_all[data_all.source==source]

    n = rel_data.shape[0] #This is how many articles we have for this source

    claims = []
    articles = []
    article_urls = []
    stances = []
    claim_veracities = []

    for i in range(n):
        claims = rel_data.claimHeadline.tolist()
        articles = rel_data.articleHeadline.tolist()
        article_urls = rel_data.url.tolist()
        stances = rel_data.articleHeadlineStance.tolist()
        claim_veracities = rel_data.claimTruth.tolist()

    return render_template("source_page.html", num_rows = n, source = source, claims = claims, \
            articles = articles, article_urls = article_urls, stances = stances,
claim_veracities = claim_veracities)

def load_route_response(
    request,
    instructions_html,
    static_stance, 
    static_reputation, 
    dynamic_stance, 
    dynamic_reputation, 
    veracity_prediction, 
    show_urls,
    static_bias,
    bias_prediction,
    countdown_length,
    amazon_url):

    dataset = pd.read_csv('claim_evidence_code_compatible.csv', encoding='utf-8', dtype=str)
    dataset_d = dataset.to_dict(orient="index")
    num_claims = len(dataset['claimHeadline'].unique())
    # print(hp_d)

    hit_data = {
        "workerId":request.args.get("workerId"),
        "assignmentId": request.args.get("assignmentId"),
        "amazon_host": AMAZON_HOST,
        "hitId": request.args.get("hitId"),
        "turkSubmitTo": request.args.get("turkSubmitTo")
    }
    print(hit_data)

    consent_html = markdown2.markdown_path('consent.md')

    resp = make_response(render_template("modular-experiment.html", 
        hit_data=hit_data,
        claim_data=dataset_d,
        num_claims=num_claims,
        consentMd=consent_html,
        instructionsMd=instructions_html,
        static_stance=static_stance,
        static_reputation=static_reputation,
        dynamic_stance=dynamic_stance,
        dynamic_reputation=dynamic_reputation,
        veracity_prediction=veracity_prediction,
        show_urls=show_urls,
        static_bias=static_bias,
        bias_prediction=bias_prediction,
        tooltip_veracity_predictor="Based on the articles below (along with their stance and reputation), we predict the correctness of the claim ",
        tooltip_overall_leaning="Based on the news sources (along with their political leaning and reputation), we calculate the political leaning of the correctness prediction algorithm",
        tooltip_relevant_articles="We put the claim into popular search engines and gather articles related to the claim",
        tooltip_stance="We predict if the article denies or supports the claim. You may click on the wrench icon to override the algorithm prediction in the cases when the algorithm is wrong (note that the icon may not be available in all cases)",
        tooltip_predicted_reputation="We predict the reputation of the source. (Negative means low, 0 means unknown and positive means high; ranges from -1 to 1)",
        tooltip_political_bias="We show the political leaning of a news source based on the bias ratings available on https://www.allsides.com/media-bias/media-bias-ratings",
        countdown_length=countdown_length,
        amazon_url=amazon_url))

    resp.headers['x-frame-options'] = 'anything'

    return resp

@app.route('/experiment/modular/testing')
def modular_testing():
    if request.args.get("assignmentID") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        pass
    else:
        pass

    instructions_html = markdown2.markdown_path('task-instructions/control-instructions.md')

    resp = load_route_response(
        request=request,
        instructions_html =  instructions_html,
        static_stance=False,
        static_reputation=False,
        dynamic_stance=True,
        dynamic_reputation=True,
        veracity_prediction=True,
        show_urls=True,
        static_bias=True,
        bias_prediction=True,
        countdown_length=TASK_TIME,
        amazon_url=AMAZON_HOST_TEST)

    return resp

@app.route('/experiment/modular/baseline')
def modular_baseline():
    if request.args.get("assignmentID") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        pass
    else:
        pass

    resp = load_route_response(
        request=request,
        instructions_html = markdown2.markdown_path('task-instructions/control-instructions-baseline.md'), 
        static_stance=False,
        static_reputation=False,
        dynamic_stance=False,
        dynamic_reputation=False,
        veracity_prediction=False,
        show_urls=True,
        static_bias=False,
        bias_prediction=False,
        countdown_length=TASK_TIME,
        amazon_url=AMAZON_HOST)

    return resp

@app.route('/experiment/modular/control')
def modular_control():
    if request.args.get("assignmentID") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        pass
    else:
        pass

    resp = load_route_response(
        request=request,
        instructions_html = markdown2.markdown_path('task-instructions/control-instructions-control.md'), 
        static_stance=False,
        static_reputation=False,
        dynamic_stance=False,
        dynamic_reputation=False,
        veracity_prediction=True,
        show_urls=True,
        static_bias=False,
        bias_prediction=False,
        countdown_length=TASK_TIME,
        amazon_url=AMAZON_HOST)

    return resp

# 

@app.route('/experiment/modular/static_trans')
def static_trans():
    if request.args.get("assignmentID") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        pass
    else:
        pass

    resp = load_route_response(
        request=request,
        instructions_html = markdown2.markdown_path('task-instructions/control-instructions-static-trans.md'), 
        static_stance=True,
        static_reputation=True,
        dynamic_stance=False,
        dynamic_reputation=False,
        veracity_prediction=True,
        show_urls=True,
        static_bias=False,
        bias_prediction=False,
        countdown_length=TASK_TIME,
        amazon_url=AMAZON_HOST)

    return resp

@app.route('/experiment/modular/dynamic_trans')
def dynamic_trans():
    if request.args.get("assignmentID") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        pass
    else:
        pass

    resp = load_route_response(
        request=request,
        instructions_html = markdown2.markdown_path('task-instructions/control-instructions-dynamic-trans.md'), 
        static_stance=False,
        static_reputation=False,
        dynamic_stance=True,
        dynamic_reputation=True,
        veracity_prediction=True,
        show_urls=True,
        static_bias=False,
        bias_prediction=False,
        countdown_length=TASK_TIME,
        amazon_url=AMAZON_HOST)

    return resp

@app.route('/experiment/modular/source_leaning')
def source_leaning():
    if request.args.get("assignmentID") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        pass
    else:
        pass

    resp = load_route_response(
        request=request,
        instructions_html = markdown2.markdown_path('task-instructions/control-instructions-baseline.md'), 
        static_stance=False,
        static_reputation=False,
        dynamic_stance=True,
        dynamic_reputation=True,
        veracity_prediction=True,
        show_urls=True,
        static_bias=True,
        bias_prediction=False,
        countdown_length=TASK_TIME,
        amazon_url=AMAZON_HOST)

    return resp

@app.route('/experiment/modular/overall_leaning')
def overall_leaning():
    if request.args.get("assignmentID") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        pass
    else:
        pass

    resp = load_route_response(
        request=request,
        instructions_html = markdown2.markdown_path('task-instructions/control-instructions-basline.md'), 
        static_stance=False,
        static_reputation=False,
        dynamic_stance=True,
        dynamic_reputation=True,
        veracity_prediction=True,
        show_urls=True,
        static_bias=True,
        bias_prediction=True,
        countdown_length=TASK_TIME,
        amazon_url=AMAZON_HOST)

    return resp

@app.route('/experiment/modular/only_veracity')
def modular_only_veracity():
    if request.args.get("assignmentID") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        pass
    else:
        pass

    resp = load_route_response(
        request=request,
        instructions_html = markdown2.markdown_path('task-instructions/control-instructions.md'), 
        static_stance=False,
        static_reputation=False,
        dynamic_stance=False,
        dynamic_reputation=False,
        veracity_prediction=True,
        show_urls=True,
        static_bias=False,
        bias_prediction=False,
        countdown_length=600000,
        amazon_url=AMAZON_HOST)

    return resp

## Older routes -- might neeed them Later
# @app.route('/experiment/modular/g1')
# def modular_g1():
#     if request.args.get("assignmentID") == "ASSIGNMENT_ID_NOT_AVAILABLE":
#         pass
#     else:
#         pass

#     resp = load_route_response(
#         request=request,
#         instructions_html = markdown2.markdown_path('task-instructions/g1-instructions.md'), 
#         static_stance=True,
#         static_reputation=False,
#         dynamic_stance=False,
#         dynamic_reputation=False,
#         veracity_prediction=False,
#         show_urls=True,
#         static_bias=False,
#         bias_prediction=False,
#         countdown_length=TASK_TIME,
#         amazon_url=AMAZON_HOST)

#     return resp

# @app.route('/experiment/modular/g2')
# def modular_g2():
#     if request.args.get("assignmentID") == "ASSIGNMENT_ID_NOT_AVAILABLE":
#         pass
#     else:
#         pass

#     resp = load_route_response(
#         request=request,
#         instructions_html = markdown2.markdown_path('task-instructions/g2-instructions.md'), 
#         static_stance=True,
#         static_reputation=True,
#         dynamic_stance=False,
#         dynamic_reputation=False,
#         veracity_prediction=False,
#         show_urls=True,
#         static_bias=False,
#         bias_prediction=False,
#         countdown_length=TASK_TIME,
#         amazon_url=AMAZON_HOST)

#     return resp

# @app.route('/experiment/modular/g4')
# def modular_g4():
#     if request.args.get("assignmentID") == "ASSIGNMENT_ID_NOT_AVAILABLE":
#         pass
#     else:
#         pass

#     resp = load_route_response(
#         request=request,
#         instructions_html = markdown2.markdown_path('task-instructions/control-instructions.md'), 
#         static_stance=True,
#         static_reputation=True,
#         dynamic_stance=False,
#         dynamic_reputation=False,
#         veracity_prediction=True,
#         show_urls=True,
#         static_bias=False,
#         bias_prediction=False,
#         countdown_length=TASK_TIME,
#         amazon_url=AMAZON_HOST)

#     return resp

# @app.route('/experiment/modular/g5')
# def modular_g5():
#     if request.args.get("assignmentID") == "ASSIGNMENT_ID_NOT_AVAILABLE":
#         pass
#     else:
#         pass

#     resp = load_route_response(
#         request=request,
#         instructions_html = markdown2.markdown_path('task-instructions/control-instructions.md'), 
#         static_stance=False,
#         static_reputation=True,
#         dynamic_stance=True,
#         dynamic_reputation=False,
#         veracity_prediction=True,
#         show_urls=True,
#         static_bias=False,
#         bias_prediction=False,
#         countdown_length=TASK_TIME,
#         amazon_url=AMAZON_HOST)

#     return resp
