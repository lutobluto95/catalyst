import pandas
import numpy as np
import re
import seaborn as sns
from wordcloud import WordCloud
import contractions

# make date range
def dateRange(start_date: str, end_date: str) -> str:
    return f"createdatutc >= '{start_date}' and createdatutc <= '{end_date} 23:59:59'"

# remove blank rows, get hashtag, and organic counts. 'aho' - get (a)ll/(h)ashtag/(o)rganic counts groupwise
def getKPICount(df: pandas.DataFrame, group_wise=False, aho='all'):
    
    dfa = df.copy()
    first = dfa.createdatutc.min()
    last = dfa.createdatutc.max()
    
    # mentions
    dfa.textlower = dfa.textlower.replace('', np.NaN)
    dfa = dfa.dropna(axis=0, subset=['textlower'])
    dfa = dfa.drop_duplicates(subset=['sourceid'])
    dfa_0 = dfa.shape[0]

    # hashtag df
    df_hash = dfa[dfa["textlower"].str.contains("#")]
    df_h0 = df_hash.shape[0]

    # organic count
    df_org = dfa[~dfa["textlower"].str.contains("#")]
    df_nh0 = df_org.shape[0]

    if aho == 'all': df = dfa.copy()
    elif aho == 'hashtag': df = df_hash.copy()
    elif aho == 'organic': df = df_org.copy()
    else: raise ValueError("aho can only be 'all', 'hashtag', or 'organic'")

    # monthwise count
    dfm = df['createdatutc'].dt.strftime('%B-%Y').value_counts().sort_index().reset_index()
    dfm.columns = ['createdatutc','Count']
    dfm.createdatutc = pandas.to_datetime(dfm.createdatutc)
    dfm = dfm.sort_values('createdatutc')
    dfm.createdatutc = dfm.createdatutc.dt.strftime('%b-%y')
    dfm = dfm.set_index('createdatutc').transpose().reset_index()
    # dfm[dfm.columns[1:]].to_clipboard(index=False,header=False)
    dfm.rename_axis(None,axis=1,inplace=True)
    dfm.rename(columns={'index':'Keywords'}, inplace=True)
    
    # group wise count
    if group_wise == True:
        grpbyc = df.groupby(['groupid'])[['groupid']].count()
        grpbyc.rename(columns={'groupid':'Count'}, inplace=True)
        grpbyc.reset_index(inplace=True)
        grpbyc.columns=['groupid','Count']
        return dfa, dfa_0, df_h0, df_nh0, first, last, dfm, grpbyc
    else: return dfa, dfa_0, df_h0, df_nh0, first, last, dfm, None


# print all the fetched numbers
def printCount(kpi, count, hashtag, organic, first, last, dfm, grpbyc):
    print(
        f"{kpi}: {count}",
        f"\n{kpi} #: {hashtag}",
        f"\n{kpi} organic: {organic}",
        "\n",
        f"\nFirst timestamp: {str(first)}",
        f"\nLast timestamp: {str(last)}",
        f"\n\nMonthwise {kpi}\n",
        f"{dfm}"
        )
    if grpbyc is not None:
        # grpbyc.to_clipboard(index=False)
        print(f"\nGroup wise {kpi}:\n",grpbyc)

# get transformations for a specific keyword from the model
def makeTransformations(keyword, filename='model.xlsx', sheetname='keywords', ilike=True, model=True):
       
    il_var = 'ILIKE'
    if ilike == False: il_var = 'LIKE'

    if model:
        keywords = pandas.read_excel(filename, sheet_name=sheetname)
        keywords.columns = keywords.iloc[0]
        keywords = keywords[1:]
        tformations = keywords[keywords.Keywords == keyword]['Transformations']
        try: tformations = list(tformations)[0].split(',')
        except IndexError:
            raise IndexError('keyword not found in the model')
    else: tformations = keyword.split(',')
        
    tformations = ["'%" + t.strip().lower().replace("'","''").replace('_',' ') + "%'" for t in tformations]
    tformations = f'TEXTLOWER {il_var} ' + f' OR TEXTLOWER {il_var} '.join(tformations)
    return tformations

# reference conversations
def printReferenceConv(df, start_index=0, num_conv=5):
    width = 80
    print('Reference Conversations')
    print('\u2500'*width)
    [print(text+'\n'+('\u2500'*width)) for text in df.textlower[start_index:start_index+num_conv]]

# sentiments
mentions_master = pandas.DataFrame(['positive','neutral','negative'],columns=['senti'])

def calculateSentiments(df: pandas.DataFrame, month_wise=False)-> pandas.DataFrame:
    if month_wise == False:
        m = df.groupby('senti').textlower.count().reset_index()
        m = mentions_master.merge(m, 'left', 'senti')
        m.columns = ['senti','Count']
        m.fillna(0, inplace=True)
        float_columns = m.select_dtypes(float).columns
        m[float_columns] = m[float_columns].astype('int32')
        return m
    else:
        m = df.copy()
        m['createdatutc'] = m['createdatutc'].astype('datetime64[M]')
        m = m.groupby(['createdatutc','senti']).textlower.count().unstack(level=0)
        m.columns = m.columns.strftime('%b-%y')
        m = mentions_master.merge(m, 'left', 'senti')
        m.fillna(0, inplace=True)
        float_columns = m.select_dtypes(float).columns
        m[float_columns] = m[float_columns].astype('int32')
        return m

# get model transformations
def makeModelTransformations(model: pandas.DataFrame)-> str:
    raw_mtx = model[model.Main_Subset == 'Main'].Transformations.tolist()
    mtx = ''
    for keyword_tx in raw_mtx:
        for raw_tx in keyword_tx.split(','):
            mod_tx = makeTransformations(raw_tx, model=False) + ' OR '
            mtx += mod_tx 
    return mtx[:-4]

# make dictionary of keywords and their transformations to get keyword mentions
def makeKeywordDict(model):
    d = {}
    schars = r'.^$*+-?()[]{}|/\'"'
    for i in range(model.shape[0]):
        key = model.Keywords.iloc[i]
        trans = [x.strip() for x in model.Transformations.iloc[i].split(',')]
        if key in d.keys():
            d[key].extend(trans)
        else:
            d[key] = trans
        # print(f'{key}: {d[key]}')
        d[key] = list(set(d[key]))
    
    for key, tf in d.items():
        new_tfs = []
        for t in tf:
            for char in schars:
                t = t.replace(char, fr'\{char}')
            new_tfs.append(t)
        d[key] = '|'.join(new_tfs).lower().replace('%','.*').replace('_',' ')
    
    return d

# convert sql transformations to regex transformations
def convertToRegex(word: str) -> dict:
    d = {}
    trans = [x.strip() for x in word.split(',')]
    trans = '|'.join(trans).lower().replace('%','.*').replace('_',' ')
    d['custom_word'] = trans
    return d


# make 1_0 dataframe
def makeOneZeroDataFrame(df: pandas.DataFrame, model_dict: dict) -> pandas.DataFrame:
    df1_0 = df.copy()
    for key,value in model_dict.items():
        pattern = re.compile(value, flags=re.DOTALL|re.I)
        df1_0[key] = np.int8(df1_0.textlower.str.contains(pattern))
    return df1_0

# get keyword mentions
def getMention(keyword: str, df: pandas.DataFrame):
    return df[df[keyword] == 1]

# get brands sov
def calculateSOV(Keywords: list, df: pandas.DataFrame):
    sov_df = pandas.DataFrame(np.sum(df[Keywords], axis=0)).reset_index()
    sov_df.columns = ['Keywords', 'Mentions']
    return sov_df

# wordcloud functions
def removeNoandPn(text: str):
    pattern = re.compile(r'[0-9!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~]+')
    return re.sub(pattern, '', text)
    
def remove_emojis(text: str):
    emojis = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
                      "]+", re.UNICODE)
    return re.sub(emojis, '', text)

def preprocess(text: str):
    text = text.replace('\n',' ')
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = contractions.fix(text)
    text = removeNoandPn(text)
    text = remove_emojis(text)
    return text

def generateWordCloud(text: str, stopwords=None, max_words=200, min_font_size=4, max_font_size=None, random_state=None):
    cmap = sns.cubehelix_palette(start=.1, rot=.5, dark=0, light=.6, gamma=1.8, hue=1, as_cmap=True)
    wordcloud = WordCloud(
        font_path='assets/Abel-Regular.ttf',
        width=600,
        height=400,
        background_color='#FFFFFF',
        collocations=False,
        colormap=cmap,
        max_words=max_words,
        min_font_size=min_font_size,
        max_font_size=max_font_size,
        prefer_horizontal=0.8,
        margin=4,
        random_state=random_state,
        stopwords=set(pandas.read_csv('assets/stop-word-list.csv', header=None).iloc[:,0].astype('str').tolist())
    )
    image = wordcloud.generate(text)
    return image.to_array()

# get group id and post id from kol or group links
def getGroupandPostIDs(url: str)-> tuple:
    """Takes either fb group link or kol link as input and returns a tuple containing group id, post id (in case of kol link),\n
    and True/False whether link has numeric group id or group name in the link.\n
    If kol link is provided but post id is not found, or group link is provided but groupid is missing (numeric or name), an error will be raised.

    Args:
        url (str): Provide either group link or kol link.\n
        e.g. kol link - https://www.facebook.com/groups/<group_id>/permalink/<post_id>/\n
             kol link- https://m.facebook.com/groups/<group_id>/posts/<post_id>/\n
             group link - https://facebook.com/groups/<group_id>/

    Raises:
        ValueError: kol link without post id
        ValueError: group link without group id

    Returns:
        tuple: (groupid, postid, True/False)
    """
    if re.search('permalink|posts', url, flags=re.I):
        pattern = re.compile(r"groups/(\S+)/(permalink|posts)/(\d*)/?", flags=re.I)
        search = re.search(pattern, url)
        grpid = search.group(1)
        postid = search.group(3)
        if postid == '': raise ValueError('link doesn\'t have post id')
        return grpid, postid, grpid.isnumeric()
    else:
        pattern = re.compile(r"groups/([0-9a-zA-Z.]*)/?", flags=re.I)
        search = re.search(pattern, url)
        grpid = search.group(1)
        if grpid == '': raise ValueError('link doesn\'t have group id')
        return grpid, grpid.isnumeric()