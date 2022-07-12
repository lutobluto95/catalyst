from random import randint
from unicodedata import category
import pandas as pd
import streamlit as st
from datetime import date
import queries
import CSUtilities as csu
from time import time
import matplotlib.pyplot as plt



st.set_page_config(layout="wide")


st.header('Catalyst')

st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child{
        width: 325px;
    }
    [data-testid="stSidebar"][aria-expanded="false"] > div:first-child{
        width: 325px;
        margin-left: -325px;
    }
     
    """,
    unsafe_allow_html=True,
)



# hide_dataframe_row_index = """
#             <style>
#             .row_heading.level0 {display:none}
#             .blank {display:none}
#             </style>
#             """

# st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)


state = st.session_state

if 'today' not in state: state.today = date.today()
if 'query_flag' not in state: state.query_flag = False
if 'group_ids' not in state: state.group_ids = None
if 'tx' not in state: state.tx = None
if 'date_range' not in state: state.date_range = None
if 'submit_choice' not in state: state.submit_choice = False
if 'model_choice' not in state: state.model_choice = 'Yes'
if 'onezerodump' not in state: state.onezerodump = pd.DataFrame()
if 'all_sov_brands' not in state: state.all_sov_brands = []
if 'sov_brands' not in state: state.sov_brands = []
if 'sov' not in state: state.sov = pd.DataFrame(columns=['Brands', 'Mentions'])
if 'mentions' not in state: state.mentions = pd.DataFrame()
if 'mall' not in state: state.mall = 0
if 'mh' not in state: state.mh = 0
if 'mo' not in state: state.mo = 0
if 'mftimestamp' not in state: state.mftimestamp = state.today
if 'mltimestamp' not in state: state.mltimestamp = state.today
if 'm_monthwise' not in state: state.m_monthwise = pd.DataFrame()
if 'grpbym' not in state: state.grpbym = pd.DataFrame()
if 'bc' not in state: state.bc = pd.DataFrame()
if 'bcall' not in state: state.bcall = 0
if 'bch' not in state: state.bch = 0
if 'bco' not in state: state.bco = 0
if 'bcftimestamp' not in state: state.bcftimestamp = state.today
if 'bcltimestamp' not in state: state.bcltimestamp = state.today
if 'bc_monthwise' not in state: state.bc_monthwise = pd.DataFrame()
if 'grpbybc' not in state: state.grpbybc = pd.DataFrame()
if 'model_tx' not in state: state.model_tx = ''
if 'catconv' not in state: state.catconv = pd.DataFrame()
if 'catconvall' not in state: state.catconvall = 0
if 'catconvh' not in state: state.catconvh = 0
if 'catconvo' not in state: state.catconvo = 0
if 'ccftimestamp' not in state: state.ccftimestamp = state.today
if 'ccltimestamp' not in state: state.ccltimestamp = state.today
if 'cc_monthwise' not in state: state.cc_monthwise = pd.DataFrame()
if 'grpbycc' not in state: state.grpbycc = pd.DataFrame()
if 'sentiments_df' not in state: state.sentiments_df = pd.DataFrame()
if 'positive' not in state: state.positive = 0
if 'neutral' not in state: state.neutral = 0
if 'negative' not in state: state.negative = 0
if 'new_mentions' not in state: state.new_mentions = pd.DataFrame()
if 'dl_filename' not in state: state.dl_filename = 'init'
if 'wc_text' not in state: state.wc_text = ''
if 'wc_image' not in state: state.wc_image = None
if 'wc_state' not in state: state.wc_state = 100




model_choice = False

with st.sidebar:
    st.header('Inputs')
    model_file = st.file_uploader('Upload Model', type=['xlsx','xlsm'], accept_multiple_files=False)

    st.header('Date Range')
    col1, col2 = st.columns(2)
    with col1: start_date = st.date_input("Start Date",)
    with col2: end_date = st.date_input("End Date")
    if start_date > end_date: st.warning('selected start date is after end date')

    if model_file:
        
        state.date_range = f"createdatutc >= '{start_date.strftime('%Y-%m-%d')}' and createdatutc <= '{end_date.strftime('%Y-%m-%d')} 23:59:59'"

        sheet_names = pd.ExcelFile(model_file).sheet_names

        st.header('Groups')
        group_sheet = st.selectbox('Select Group Sheet', sheet_names)

        groups = pd.read_excel(model_file, sheet_name=group_sheet)
        group_col = st.selectbox('Group IDs Column', groups.columns)
        
        st.write(f'Groups Count:\t{groups.shape[0]}')
        state.group_ids = groups[group_col].dropna()

        start_index = 1 if len(sheet_names) > 1 else 0
        st.header('Model')
        model_sheet = st.selectbox('Select Model Sheet', sheet_names, index=start_index)

        
    
        if model_sheet is not None:
            model = pd.read_excel(model_file, sheet_name=model_sheet)
            cat_name = model.columns[0]
            model.columns = model.iloc[0,:]
            model = model.iloc[1:,:]
            if 'Transformations' not in model.columns: st.warning('selected sheet doesn\'t appear to be a model file') 
            

            
            # state.model_choice = st.radio('Use Model?', ['Yes', 'No'])

            # with st.form(key='tx_form'):
            #     if state.model_choice == 'No':
            #         word = st.text_input('Enter word(s) separated by comma to make transformations')
            #     else:
            #         try: word = st.selectbox('Search keyword in model', model.Keywords)
            #         except AttributeError: pass
            #     state.submit_choice = st.form_submit_button('Make Transformations')
            # if state.submit_choice:
            #     state.model_choice = True if state.model_choice == 'Yes' else False
            #     if state.model_choice:
                    
            #         if model_file is None: st.warning('Please select model first')
            #         else:
            #             try: 
            #                 state.tx = csu.makeTransformations(word, filename=model_file, sheetname=model_sheet, model=True)
            #             except IndexError: st.warning('Keyword not in model')
            #             with st.expander('Transformations'):    
            #                 st.code(state.tx)
                    
            #     else:
            #         state.tx = csu.makeTransformations(word, model=False)
            #         with st.expander('Transformations'):    
            #             st.code(state.tx)
            # if (state.model_choice == 'Yes' or state.model_choice is True) and 'Keywords' in model.columns:
            #     state.all_sov_brands =  model[((model.Category == 'Brands') | (model.Category == 'Brand')) & (model.Keywords != word)].Keywords
            #     state.sov_brands = st.multiselect('Select Brands (Leave blank for all Brands)', state.all_sov_brands)

            if 'Keywords' in model.columns:
                st.write(f'Model: {cat_name}&nbsp;&nbsp;&nbsp;&nbsp;Keywords: {model.shape[0]}')        
                with st.expander('View Model'): st.dataframe(model)
                st.header('Transformations')
                word = st.selectbox('Choose brand', model[(model.Category == 'Brands') | (model.Category == 'Brand')].Keywords)
                state.all_sov_brands =  model[((model.Category == 'Brands') | (model.Category == 'Brand')) & (model.Keywords != word)].Keywords
                state.sov_brands = st.multiselect('Competitors (Leave blank to consider all brands)', state.all_sov_brands)

# if st.button('Generate Query'):
#     st.write(state.tx)
#     st.write(state.group_ids)
#     st.write(state.date_range)
#     if state.model_tx is not None and state.group_ids is not None and state.date_range is not None:
#         with st.expander('Query'):
#             state.model_tx = csu.makeModelTransformations(model)
#             st.code(queries.generateSQL('conv',state.group_ids, state.model_tx, state.date_range))
#     else: st.warning('Make sure you have selected groups and brand')

if st.button('Generate Report'):
    try:
        with queries.makeConnection(**st.secrets.db_info) as con:
            with st.spinner('Running Query....'):
                state.query_flag = True
                tick = time()
                # if state.model_choice is True or state.model_choice == 'Yes':   
                state.model_tx = csu.makeModelTransformations(model)
                state.catconv = queries.executeQuery(con, queries.generateSQL('conv',state.group_ids, state.model_tx, state.date_range))
                state.onezerodump = csu.makeOneZeroDataFrame(state.catconv, csu.makeKeywordDict(model))
                state.mentions = csu.getMention(word, state.onezerodump)
                post_ids = set(state.mentions[state.mentions.type == 'Post'].sourceid)
                state.bc = pd.concat([state.mentions, state.catconv[state.catconv.parentsourceid.isin(post_ids)]], ignore_index=True).drop_duplicates(subset=['sourceid'])
                state.wc_text = csu.preprocess(' '.join(state.bc.textlower.values))
                # else: 
                #     state.catconv = queries.executeQuery(con, queries.generateSQL('conv',state.group_ids, state.tx, state.date_range))
                #     state.onezerodump = csu.makeOneZeroDataFrame(state.catconv, csu.convertToRegex(word))
                #     state.mentions = csu.getMention('custom_word', state.onezerodump)
                state.sentiments_df = csu.calculateSentiments(state.mentions, False)
                state.positive = state.sentiments_df[state.sentiments_df.senti == 'positive'].Count.values[0]
                state.neutral = state.sentiments_df[state.sentiments_df.senti == 'neutral'].Count.values[0]
                state.negative = state.sentiments_df[state.sentiments_df.senti == 'negative'].Count.values[0]      
                tock = time()
            st.success(f'Done! execution time: {round(tock - tick, 2)} seconds')
        con.close()
    except Exception as e:
        st.write(e)
        con.close()

    try: state.mentions, state.mall, state.mh, state.mo, state.mftimestamp, state.mltimestamp, state.m_monthwise, state.grpbym = csu.getKPICount(state.mentions, group_wise=False, aho='all')
    except AttributeError: state.mall = state.mh = state.mo = 0
    try: state.bc, state.bcall, state.bch, state.bco, state.bcftimestamp, state.bcltimestamp, state.bc_monthwise, state.grpbybc = csu.getKPICount(state.bc, group_wise=False, aho='all')
    except AttributeError: state.bcall = state.bch = state.bco = 0
    try: state.catconv, state.catconvall, state.catconvh, state.catconvo, state.ccftimestamp, state.ccltimestamp, state.cc_monthwise, state.grpbycc = csu.getKPICount(state.catconv, group_wise=False, aho='all')
    except AttributeError: state.catconvall = state.catconvh = state.catconvo = 0

@st.cache
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8-sig")

col1, col2, col3 = st.columns(3)

# if state.model_choice is False or state.model_choice == 'No':
#     conv_word = mentions_word = ''
# else:
conv_word = 'Category'
mentions_word = 'Brand'

with col1:
    st.metric(f'{conv_word} Conversations', value=state.catconvall)
    st.write(f'\# {conv_word} Conversations:\t{state.catconvh}')
    st.write(f'Organic {conv_word} Conversations:\t{state.catconvo}')

with col2:
    st.metric(f'{mentions_word} Mentions', value=state.mall)
    st.write(f'\# Mentions:\t{state.mh}')
    st.write(f'Organic Mentions:\t{state.mo}')

if conv_word == 'Category':
    with col3:
        st.metric('Brand Conversations', value=state.bcall)
        st.write(f'\# Brand Conversations:\t{state.bch}')
        st.write(f'Organic Brand Conversations:\t{state.bco}')


st.write('')
# col1, col2, col3 = st.columns(3)
with col1:
    st.write('')
    st.write('##### Share of Voice')
    sov_cont = st.empty()

    if state.query_flag is True:# and (state.model_choice is True or state.model_choice == 'Yes'):
        
        if state.sov_brands == []:
            try: state.sov = csu.calculateSOV(state.all_sov_brands, state.onezerodump)
            except KeyError: pass
        else:
            try: state.sov = csu.calculateSOV(state.sov_brands, state.onezerodump)
            except KeyError: pass
        st.dataframe(state.sov, height=325)
    else:
        sov_cont.write('<nothing to show yet>')



# col1, col2, col3 = st.columns([1,3,4])

with col2:
    st.write('')
    st.write('##### Sentiments')
    if state.mentions.empty is False:
        try: st.download_button('Download',data=convert_df(state.mentions.loc[:,['groupid','createdatutc','textlower','senti']]), file_name=f'mentions {state.today}.csv')
        except KeyError: pass
        sentiments_cont = st.empty()
        sentiments_cont.write(f"Positive: {state.positive}&nbsp;&nbsp;&nbsp;&nbsp;Neutral: {state.neutral}&nbsp;&nbsp;&nbsp;&nbsp;Negative: {state.negative}")

        new_mentions = st.file_uploader('Upload updated mentions file', type=['csv'], accept_multiple_files=False)

        if st.button('Refresh') and new_mentions:
            state.new_mentions = pd.read_csv(new_mentions)
            state.new_mentions = csu.calculateSentiments(state.new_mentions, False)
            state.positive = state.new_mentions[state.new_mentions.senti == 'positive'].Count.values[0]
            state.neutral = state.new_mentions[state.new_mentions.senti == 'neutral'].Count.values[0]
            state.negative = state.new_mentions[state.new_mentions.senti == 'negative'].Count.values[0]        
            sentiments_cont.write(f"Positive: {state.positive}&nbsp;&nbsp;&nbsp;&nbsp;Neutral: {state.neutral}&nbsp;&nbsp;&nbsp;&nbsp;Negative:\t{state.negative}")
    else: st.write('<nothing to show yet>')


@st.cache
def generateWordCloud(text, max_words=200, min_font_size=4, max_font_size=84, random_state=100):
    return csu.generateWordCloud(text, max_words=max_words, min_font_size=min_font_size, max_font_size=max_font_size, random_state=random_state)

with col3:
    st.write('')
    st.write('##### Word Cloud')
    # max_words = st.slider('Maximum words', 50, 200, value=150, step=10)
    # min_font_size = st.slider('Minimum Font Size', 1, 24, value=4, step=1)
    # max_font_size = st.slider('Maximum Font Size', 32, 100, value=84, step=4)

# with col3:
#     st.markdown('#')
#     st.markdown('###')
    wc_cont = st.container()
    if state.bc.empty is False:
        if st.button(key='wc_refresh', label='Refresh'):
            state.wc_state = randint(0, 100)
        if state.wc_text != '':
            state.wc_image = generateWordCloud(state.wc_text, random_state=state.wc_state)#, max_words, min_font_size, max_font_size, random_state=state.wc_state)
            fig = plt.figure(figsize=(6,4))
            plt.imshow(state.wc_image, interpolation='bilinear')
            plt.axis('off')
            wc_cont.pyplot(fig, clear_figure=True)
            plt.close()
    else: st.write('<nothing to show yet>')


st.write('')
col1, col2 = st.columns([1,2])
with col1:
    st.write('##### Downloads')
    downloadable_files = ['catconv','catconv1_0','brandconv'] if state.query_flag is True else None
    dl_file = pd.DataFrame()
    if state.query_flag:
        # if conv_word == '': downloadable_files.remove('brandconv') 
        state.dl_filename = st.selectbox('Choose File', downloadable_files)
        if state.dl_filename == 'catconv' : dl_file = state.catconv.loc[:,['groupid','createdatutc','textlower','senti']]
        elif state.dl_filename == 'catconv1_0': dl_file = state.onezerodump
        elif state.dl_filename == 'brandconv': dl_file = state.bc.loc[:,['groupid','createdatutc','textlower','senti']]
        try: st.download_button('Download',data=convert_df(dl_file), file_name=f'{state.dl_filename} {state.today}.csv')
        except KeyError: pass
    else:
        st.info('No Data to download')

col2.write('Preview (100 Rows)') 
if state.query_flag: col2.dataframe(dl_file.iloc[:100], height=140)
else: col2.info('nothing to show yet')


    
