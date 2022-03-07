import streamlit as st
import dhlab.text as dh
import dhlab.api.dhlab_api as api
import gnl as gnl
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from PIL import Image
import requests
from streamlit_agraph import agraph, TripleStore, Config, Node, Edge


colors =  ['#DC143C','#FFA500',
           '#F0E68C','#BC8F8F','#32CD32',
           '#D2691E','#3CB371','#00CED1',
           '#00BFFF','#8B008B','#FFC0CB',
           '#FF00FF','#FAEBD7']

def word_to_colors(comm):
    word_to_color = dict()
    for i, e in enumerate(comm.values()):
        for x in e:
            word_to_color[x] = colors[i % len(colors)]
    return word_to_color


@st.cache(suppress_st_warning=True, show_spinner = False)
def create_nodes_and_edges_config(g, community_dict):
    """create nodes and edges from a networkx graph for streamlit agraph, classes Nodes, Edges and Config must be imported"""
    cmap = word_to_colors(community_dict)
    nodes = []
    edges = []
    for i in g.nodes(data = True):
        nodes.append(Node(id=i[0], size=100, color=cmap[i[0]]) )
    for i in g.edges(data = True):
        edges.append(Edge(source=i[0], target=i[1], type="CURVE_SMOOTH", color = "#ADD8E6"))

    config = Config(height=500,
                nodeHighlightBehavior=True,
                highlightColor="#F7A7A6", 
                directed=True, 
                collapsible=True)
    
    return nodes, edges, config


@st.cache(suppress_st_warning=True, show_spinner = False)
def theme_book(urn = None, reference = None, chunksize= 1000, maxval = 0.9, minval = 0.2):
    chunk0 = dh.Chunks(urn= crp.corpus.urn[0], chunks = chunksize)
    df0 = pd.DataFrame(chunk0.chunks).transpose().fillna(0)
    count0 = df0.sum(axis = 1)
    if not reference is None: 
        relevance0 = ((count0/count0.sum())/(reference[reference.columns[0]]/reference[reference.columns[0]].sum())).dropna()
    else:
        units = df0/df0
        (rows, cols) = units.shape
        words_from_chunks = units[minval < units.sum(axis = 1)/cols][units.sum(axis = 1)/cols < maxval].index
        relevance0 = count0.loc[words_from_chunks]/count0.loc[words_from_chunks].sum()
    words = relevance0.sort_values(ascending=False).head(250).index
    prod = df0.loc[words].dot(df0.loc[words].transpose())
    return prod


@st.cache(suppress_st_warning=True, show_spinner = False)
def get_corpus(freetext=None, title=None, from_year=1900, to_year=2020):
    c = dh.Corpus(freetext=freetext, title=title,from_year=from_year, to_year=to_year)
    return c.corpus


# select URN

if stikkord == '':
    stikkord = None
corpus = get_corpus(freetext=stikkord, from_year=period[0], to_year=period[1])

#choices = [', '.join([str(z) for z in x]) for x in corpus[['authors','title', 'year','urn']].values.tolist()]
choices = corpus[['authors','title', 'year','urn']]
valg = st.selectbox("Velg et dokument", choices)

# create graph and themes
prod = theme_book(urn = crp.corpus.urn[0], reference = None, maxval = 0.4, chunksize=300)
G = nx.from_pandas_adjacency(prod)
nodes, edges, config = create_nodes_and_edges_config(G, gnl.community_dict(G))

# show graph
st.markdown("## Graph")
agraph(nodes, edges, config)

# show themes
st.markdown("## Themes")
gnl.show_communities(G)