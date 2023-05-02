import streamlit as st
import dhlab.text as dh
import dhlab.api.dhlab_api as api
from dhlab.nbtokenizer import tokenize
import gnl
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from PIL import Image, ImageEnhance
import requests
from streamlit_agraph import agraph, TripleStore, Config, Node, Edge
import re
from collections import Counter

maxlen = 250
antall_dokument = 30


@st.cache(suppress_st_warning=True, show_spinner = False)
def theme_book(urn = None, reference = None, chunksize= 1000, max_words=250, maxval = 0.9, minval = 0.2, relevance=5):
    chunk0 = dh.Chunks(urn= urn, chunks = chunksize)
    df0 = pd.DataFrame(chunk0.chunks).transpose().fillna(0)
    count0 = df0.sum(axis = 1)
    if not reference is None: 
        relevance0 = ((count0/count0.sum())/(reference[reference.columns[0]]/reference[reference.columns[0]].sum())).dropna()
        relevance0 = relevance0[relevance0 > relevance]
    else:
        units = df0/df0
        (rows, cols) = units.shape
        words_from_chunks = units[minval < units.sum(axis = 1)/cols][units.sum(axis = 1)/cols < maxval].index
        relevance0 = count0.loc[words_from_chunks]/count0.loc[words_from_chunks].sum()
    words = relevance0.sort_values(ascending=False).head(max_words).index
    prod = df0.loc[words].dot(df0.loc[words].transpose())
    return prod, words

@st.cache(suppress_st_warning=True, show_spinner = False)
def theme_book_txt(text = None, reference = None, chunksize= 1000, max_words=250, maxval = 0.9, minval = 0.2, relevance=5):
    text_words = tokenize(text)
    chunks = [Counter(text_words[i:i + chunksize]) for i in range(0,len(text_words), chunksize)]
    df0 = pd.DataFrame(chunks).transpose().fillna(0)
#    st.write("dataramme", df0)
    count0 = df0.sum(axis = 1)
#    st.write('counts', count0)
    if not reference is None: 
        relevance0 = ((count0/count0.sum())/(reference[reference.columns[0]]/reference[reference.columns[0]].sum())).dropna()
        relevance0 = relevance0[relevance0 > relevance]
    else:
        units = df0/df0
        (rows, cols) = units.shape
        words_from_chunks = units[minval < units.sum(axis = 1)/cols][units.sum(axis = 1)/cols < maxval].index
        relevance0 = count0.loc[words_from_chunks]/count0.loc[words_from_chunks].sum()
    words = relevance0.sort_values(ascending=False).head(max_words).index
    prod = df0.loc[words].dot(df0.loc[words].transpose())
    return prod, words

@st.cache(suppress_st_warning=True, show_spinner = False)
def theme_book_list(urn = None, words = None, chunksize= 1000):
    chunk0 = dh.Chunks(urn= urn, chunks = chunksize)
    df0 = pd.DataFrame(chunk0.chunks).transpose().fillna(0)
    count0 = df0.sum(axis = 1)
    prod = []
    small_list = [x for x in words[:maxlen] if x in df0.index]
    if small_list != []:
        prod = df0.loc[small_list].dot(df0.loc[small_list].transpose())
    return prod


@st.cache(suppress_st_warning=True, show_spinner = False)
def get_corpus(freetext=None, title=None, number = 20):
    if not freetext is None:
        c = dh.Corpus(freetext=freetext, title=title, limit = number)
    else:
        c = dh.Corpus(doctype="digibok", limit = number)
    return c.corpus

@st.cache(suppress_st_warning=True, show_spinner = False)
def totals(n = 300000):
    return api.totals(n)

st.set_page_config(layout="wide")



header1,_, header2 = st.columns([2,4,2])
with header1:
    st.title('Temaer i tekst')
    st.markdown("""[DH ved Nasjonalbiblioteket](https://nb.no/dh-lab)""")
    
with header2:
    im = Image.open("DHlab_logo_web_en_black.png").convert('RGBA')
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(.4)
    im.putalpha(alpha)
    st.image(im, width = 300)
    
st.write('---')
# select URN
# Using the "with" syntax


corpus_defined = False
text_defined = False

icol1, icol2 = st.columns([1,3])
with icol1:
    method = st.selectbox(
        "Metode for å angi tekst", 
        options=['Stikkord', 'Urnliste', 'Excelkorpus', 'Tekstinput'], 
        help="Lim inn en tekst med URNer, eller last opp et excelark med korpus"
        " lagd for eksempel med https://beta.nb.no/dhlab/korpus/, "
        "eller antyd en grupper tekster ved hjelp av stikkord"
    )

with icol2:
    if method == 'Urnliste':
        urner = st.text_area(
            "Lim inn URNer:","", 
            help="Lim tekst med URNer. Teksten trenger ikke å være formatert, "
            "og kan inneholde mer enn URNer"
        )
        if urner != "":
            urns = re.findall("URN:NBN[^\s.,]+", urner)
            if urns != []:
                corpus_defined = True
                corpus = dh.Corpus(doctype='digibok',limit=0)
                corpus.extend_from_identifiers(urns)
                corpus = corpus.corpus
                #st.write(corpus)
            else:
                st.write('Fant ingen URNer')
                
    elif method == 'Excelkorpus':
        uploaded_file = st.file_uploader(
            "Last opp et korpus", 
            help="Dra en fil over hit, fra et nedlastningsikon, "
            "eller velg fra en mappe"
        )
        if uploaded_file is not None:
            corpus_defined = True
            dataframe = pd.read_excel(uploaded_file)
            corpus = dh.Corpus(doctype='digibok',limit=0)
            corpus.extend_from_identifiers(list(dataframe.urn))
            corpus = corpus.corpus
    elif method == "Tekstinput":
        text = st.text_area("Lim inn tekst her:", "")
        text_defined = True
    else:
        stikkord = st.text_input(
            'Angi noen stikkord for å forme et utvalg tekster','', 
            help="Skriv inn for eksempel forfatter og tittel for bøker, "
            "eller avisnavn for aviser." 
            "For aviser kan dato skrives på formatet YYYYMMDD."
        )

        if stikkord == '':
            stikkord = None
        corpus_defined = True
        corpus = get_corpus(freetext=stikkord)

if corpus_defined:
    choices = [', '.join([str(z) for z in x]) 
               for x in corpus[['authors','title', 'year','urn']].values.tolist()]
elif text_defined == True:
    choices = []
else:
    choices = []
        
 #, from_year=period[0], to_year=period[1])
urn = []
min_chunk = 5 if text_defined else 300

#relevance_list = st.checkbox("Bruk automatisk ordliste", value = True, help="klikk for å legge inn egen kommaseparert ordlist")

#if relevance_list:
    
with st.form(key='my_form'):
    refsz, chunksz, relcutz = st.columns([1,1,1])
    with refsz:
        refsize = st.number_input("Størrelse på referansekorpus", 
                              min_value = 20000, max_value = 500000, value = 200000, help="Referansekorpuset er en frekvensliste over norske ord i bøker og aviser. I analysen fungerer det sånn at ord som ikke er i referansen vil ikke tas med. Størrelsen på referansekorpuset er delvis med på å bestemme hvor mange ord som blir med i analysen. Det kan ha inntil 500 000 ord.")
        ref = totals(refsize)
    with chunksz:
        chunksize = st.number_input(f"Størrelse på tekstdeler ({min_chunk} og oppover)", 
                                min_value = min_chunk, value = 1000, help="Teksten deles opp i biter slik at ord som står i samme del blir knyttet sammen. Jo oftere to ord står sammen jo større er sjansen for at ender opp i samme tema")
    with relcutz:
        relevance = st.number_input("Angi grense på forskjell", min_value = 0,max_value = 1000, value = 5, help="Forskjellen beregnes som en forskjell i antall forekomster av ord i teksten sammenlignet med referansekorpuset, så om et ord forekommer x % i teksten og y % i referansen vil kravet sikre at x/y er større en verdien som angis. Jo høyere verdi, desto færre ord blir med i struktureringen")
        
    #antall_dokument = st.number_input("Antall dokument fra 10 til 100", 
    #                                  min_value = 10, max_value = 100, value = 20)
    if corpus_defined == True:
        #corpus = get_corpus(freetext=stikkord, number = antall_dokument)
        choices = [', '.join([str(z) for z in x]) for x in corpus[['authors','title', 'year','urn']].values.tolist()]
        valg = st.selectbox("Velg et dokument", choices)
        urn = valg.split(', ')[-1]

    submit_button = st.form_submit_button(label='Klikk her når alt er klart!')

    #create graph and themes
    if submit_button:
        if corpus_defined:
            prod, words = theme_book(urn = urn, reference = ref, maxval = 0.4, chunksize= chunksize, relevance=relevance)
        elif text_defined:
            prod, words = theme_book_txt(text = text, reference = ref, maxval = 0.4, chunksize = chunksize, relevance=relevance)
        try:
            G = nx.from_pandas_adjacency(prod)
            comm =  gnl.community_dict(G)
        except:
            comm = dict()


        col1, col2 = st.columns(2)
        with col1:
            st.markdown("## Tematiske grupper")
            st.write('\n\n'.join(['**{label}** {value}'.format(label = key, value = ', '.join(comm[key])) for key in comm]))
        with col2:
            st.markdown("## Ord for gruppering")
            st.markdown("_Basert på en sammenligning av input-tekst med referansekorpus_")
            st.write(', '.join([w for w in words]))

# else:

#     with st.form(key='my_form'):

#         words = st.text_input("Angi en liste av ord skilt med komma", "")
#         try:
#             wordlist = [x.strip() for x in words.split(',')]
#         except:
#             wordlist = []

#         chunksize = st.number_input("Størrelse på chunk (300 og oppover)", min_value = 300, value = 1000)

#         #antall_dokument = st.number_input("Antall dokument fra 10 til 100", min_value = 10, max_value = 100, value = 20)
#         #corpus = get_corpus(freetext=stikkord, number = antall_dokument)
    
#         choices = [', '.join([str(z) for z in x]) for x in corpus[['authors','title', 'year','urn']].values.tolist()]
#         valg = st.selectbox("Velg et dokument", choices)
#         urn = valg.split(', ')[-1]
#         submit_button = st.form_submit_button(label='Finn tema!')

#         # create graph and themes
#         if submit_button:
#             if corpus_defined:
#                 prod, _ = theme_book(urn = urn, reference = ref, maxval = 0.4, chunksize= chunksize)
#             elif text_defined:
#                 prod, _ = theme_book_txt(text = text, reference = ref, maxval = 0.4, chunksize = chunksize)
#             try:
#                 G = nx.from_pandas_adjacency(prod)
#                 comm =  gnl.community_dict(G)
#             except:
#                 comm = dict()
 
#             st.markdown("## Temaer")
#             st.write('\n\n'.join(['**{label}** {value}'.format(label = key, value = ', '.join(comm[key])) for key in comm]))



