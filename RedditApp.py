import streamlit as st
import pandas
import requests
import re
from string import punctuation
from collections import Counter
from nltk.corpus import stopwords
try:
    stop_words = stopwords.words("english")
    stop_words.extend(['im','dont','cant','would','could','like','also','really'])
except:
    import nltk
    nltk.download('stopwords')
    stop_words = stopwords.words("english")
    stop_words.extend(['im','dont','cant','would','could','like','also','really'])

# Define Functions
def clean_up(txt):
    # simple clean up of text: lowercase + ignore ascii errors
    txt = txt.lower()
    txt = txt.encode('ascii', 'ignore').decode()
    return txt

def remove_punc(txt):
    txt = txt.replace("\n", " ")
    txt = ''.join([char for char in txt if char not in punctuation])
    return txt

def remove_stopwords(txt):
    txt = ' '.join([word for word in txt.split(' ') if word not in stop_words])
    return txt

def get_reddit(subreddit,listing,limit,timeframe):
    try:
        base_url = f'https://oauth.reddit.com/r/{subreddit}/{listing}.json?limit={limit}&t={timeframe}'
        request = requests.get(base_url, headers = headers)
    except:
        print('An Error Occured')
    return request.json()

if __name__ == '__main__':
    # Request API authorization
    auth = requests.auth.HTTPBasicAuth('<Reddit API user>', '<Reddit API password>')
    data = {'grant_type': 'password',
            'username': '<reddit username>',
            'password': '<reddit password>'}
    headers = {'User-Agent': 'MyBot'}
    res = requests.post('https://www.reddit.com/api/v1/access_token', auth=auth, data=data, headers=headers)
    TOKEN = res.json()['access_token']
    headers = {**headers, **{'Authorization': f"bearer {TOKEN}"}}
    requests.get('https://oauth.reddit.com/api/v1/me', headers=headers)

    # STREAMLIT App Start-up
    st.write('''
        ## Simple sub-reddit Word Count
        ''')

    with st.sidebar.form("selection_form"):
        st.write("Customize your scrape below: ")
        subreddit = st.text_input(
            'Enter subreddit name: r/', 
            value='worldnews',
            help='for /r/pics, enter "pics"')
        listing = st.select_slider(
            'Select order of posts',
            options=['top', 'hot', 'new', 'controversial'],
            value='top')
        timeframe = st.select_slider(
            'Select timeframe of posts to scrape',
            options=['day', 'week', 'month', 'year'],
            value='day')
        limit = st.slider(
            'Select number of posts to scrape',
            min_value=1,max_value=100,value=25,
            help='limits the number of comments to scrape')    
        submitted = st.form_submit_button("Submit & Run")
        if submitted:
            stop_words.append(subreddit.lower())

    with st.spinner('Wait for it...'):
        r_titles = get_reddit(subreddit,listing,limit,timeframe)
        # Write each title string to txt
        f = open('the_file.txt','w+')
        for post in r_titles['data']['children']:
            f.write(' '+clean_up(post['data']['title']))

        #Get comments from each reddit-post
        for post in r_titles['data']['children']:
            article = post['data']['id']
            sort = 'top' # confidence, top, new, controversial, old, random, qa, live
            def get_comment(subreddit,article,limit,sort):
                try:
                    base_url = f'https://oauth.reddit.com/r/{subreddit}/comments/{article}.json?limit={limit}&sort={sort}'
                    request = requests.get(base_url, headers = headers)
                except:
                    print('An Error Occured')
                return request.json()
    
            r_comment = get_comment(subreddit,article,limit,sort)
            for post in r_comment[1]['data']['children']:
                if post['kind'] != 'more':
                    f.write('\n'+clean_up(post['data']['body']))
        f.close()

        with open('the_file.txt',mode='r') as open_file:
            f = open_file.read()

        # remove punctuation and split words
        f_clean = remove_punc(f)
        f_clean = remove_stopwords(f_clean)
        f_clean = re.findall('[^\W]+',f_clean)

        c = Counter(f_clean)
        df = pandas.DataFrame(c.most_common(25),columns=['Word','Hits'])
        df
    
    st.write('Word counts for the ',listing,'-',limit,' posts in /r/',subreddit,' from the past ',timeframe)
    st.success('Done!')

    st.write("Author's Webpage [Click Here](https://dnie44.github.io/)")