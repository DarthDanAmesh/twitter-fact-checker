import streamlit as st
import pandas as pd

st.title("NLTK Twitter Analysis")
# create a context manager for the twitter data
# https://ipython.ai/understanding-context-managers-in-python/ or https://book.pythontips.com/en/latest/context_managers.html
class TwitaFile:
    def __init__(self, filename, method, encoding=None):
        self.file_obj = open(filename, method, encoding=None)

    def __enter__(self):
        return self.file_obj
    
    def __exit__(self, type, value, traceback):
        if self.file_obj:
            self.file_obj.close()


#https://stackoverflow.com/questions/37400974/error-unicode-error-unicodeescape-codec-cant-decode-bytes-in-position-2-3
#Trailing data error, add the lines=True argument
#https://stackoverflow.com/questions/58346195/how-to-fix-valueerror-trailing-data-during-pandas-read-json

url = r"C:\Users\danie\OneDrive\Pictures\OSINT\corpora\twitter_samples\tweets.20150430-223406.json"

#import glob
#for file in glob.glob('**/*.json', recursive=True):
    #print(file)

# using the with protocol, file will be available in globals()


# Render to the screen
st.write("Enter the number of top hashtags to display:")
# store the state of number to be displayed
st.session_state['top_n'] = st.slider('Adjust the top trending hashtags', min_value=1, max_value=30, value=10)

def print_hashtags(data):
    all_hashtags = []
    for index, row in data.iterrows():
        try:
            # in the retweeted status, get the hashtags
            hashtags = row['retweeted_status']['entities']['hashtags']
            #print(hashtags) # output is [{'indices': [4, 15], 'text': 'SNPbecause'}, {'indices': [39, 49], 'text': 'AskNicola'}, {'indices': [50, 56], 'text': 'bbcqt'}, {'indices': [57, 65], 'text': 'VoteSNP'}]
            hashtag_texts = [hashtag['text'] for hashtag in hashtags]
            #print(hashtag_texts) #output example ['SNPBecause', 'SNP', 'VoteSNP']
            all_hashtags.extend(hashtag_texts)
        except (TypeError, KeyError):
            continue

        try:
            # this is from normal (NOT Retweeted) posts (maybe?)
            entities_hashtags = [hashtag['text'] for hashtag in row['entities']['hashtags']]
            # print(entities_hashtags) #output example ['bbc', 'ukip', 'fcbgetafe', '28a', 'bugil', 'it', 'peace', 'gintama']
            # combine all_hashtag and entities_hashtag
            all_hashtags.extend(entities_hashtags)
        except (TypeError, KeyError):
            continue
    

    # get the top_n state stored in the st.session_state['top_n'] = slider statement defined above with value set at 10
    top_n_filter = st.session_state.get('top_n', 10)
    # filter only 10 results, and join the hashtags, separate them using spaces, 
    top_hashtags = pd.Series(' '.join(all_hashtags).split()).value_counts()[:top_n_filter]

    #rename axis.
    #top_hashtags.rename_axis("Top Trends")
    
    # render to screen, based on renamed axis
    st.write(top_hashtags.rename_axis("Top Trends"))

    # Count the unique occurrences of hashtags
    from collections import Counter
    hashtag_counter = Counter(all_hashtags)
    for hashtag, count in hashtag_counter.most_common(top_n_filter):
        print(f"{hashtag}: {count}")

    # Plot the top hashtags
    top_hashtags = hashtag_counter.most_common(top_n_filter)
    hashtags_df = pd.DataFrame(top_hashtags, columns=['Hashtag', 'Occurrences'])
    plot = hashtags_df.plot(kind='bar', x='Hashtag', y='Occurrences', legend=False)
    
    if st.button("See charts!", use_container_width=True):
         plot.figure #can also be replaced with: st.pyplot(plot.figure)

with TwitaFile(url, 'r', encoding="utf-8") as file:
    data = pd.read_json(file, lines=True)

print_hashtags(data)