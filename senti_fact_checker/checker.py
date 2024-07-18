import pandas as pd
from bs4 import BeautifulSoup
import unicodedata
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from nltk import bigrams
from tavily import TavilyClient

tavily = TavilyClient(api_key="REPLACE WITH YOUR KEY")

#Place the 'r' when using system path to convert to raw string
#https://stackoverflow.com/questions/37400974/error-unicode-error-unicodeescape-codec-cant-decode-bytes-in-position-2-3
url = r"C:\Users\danie\OneDrive\Pictures\OSINT\corpora\twitter_samples\tweets.20150430-223406.json"

#Trailing data error, add the lines=True argument
#https://stackoverflow.com/questions/58346195/how-to-fix-valueerror-trailing-data-during-pandas-read-json
with open(url, 'r', encoding='utf-8') as f:
    data = pd.read_json(url, lines=True)
#print(data.head)
    #r"C:\Users\danie\OneDrive\Pictures\OSINT\corpora\twitter_samples\tweets.20150430-223406.csv", index=False

# ... existing code ...

def parse_anchor(tag):
    soup = BeautifulSoup(tag, 'html.parser')
    anchor = soup.find('a')
    return anchor.text.strip() if anchor else "0"

data['parsed_source'] = data['source'].apply(parse_anchor)

def print_user_data(row):
    try:
        print("User Data \n")
        user_data_fields = [
            ("Verified status", row['user']['verified']),
            ("Screen name", row['user']['screen_name']),
            ("Statuses count", row['user']['statuses_count']),
            ("Post ID", row['user']['id_str']),
            ("User Posted at", row['user']['created_at']),
            ("No. Followers", row['user']['followers_count']),
            ("Friends count", row['user']['friends_count']),
            ("Description", row['user']['description']),
            ("Timezone", row['user']['time_zone']),
            ("User geo", row['geo']),
            ("User Location", row['user']['location']),
            ("User listed count", row['user']['listed_count']),
            ("User Profile link", row['user']['profile_image_url_https']),
            ("User notifications", row['user']['notifications'])
        ]
        for field, value in user_data_fields:
            print(f"{field}: {value}")
        print("\n")
    except KeyError as e:
        print(f"Error processing user data: {e}")

def print_influencer_data(row):
    try:
        print("Influencer data:")
        influencer_data_fields = [
            ("X ID", row['retweeted_status']['id']),
            ("Influencer, Verified status", row['retweeted_status']['user']['verified']),
            ("Influencer, Screen name", row['retweeted_status']['user']['screen_name']),
            ("Influencer No. Followers", row['retweeted_status']['user']['followers_count']),
            ("Influencer Friends count", row['retweeted_status']['user']['friends_count']),
            ("Influencer Description", row['retweeted_status']['user']['description']),
            ("Influencer Timezone", row['retweeted_status']['user']['time_zone']),
            ("Influencer User geo", row['retweeted_status']['geo'])
        ]
        for field, value in influencer_data_fields:
            print(f"{field}: {value}")
        print("\n")
    except TypeError as e:
        print(f"Error processing influencer data: {e}")

def print_influential_posts_data(row):
    print("\n")
    try:
        print("Influencial posts data:")
        influential_posts_fields = [
            ("Influencer Post created", row['retweeted_status']['text']),
            ("Influencer Posted at", row['retweeted_status']['created_at'])
        ]
        for field, value in influential_posts_fields:
            print(f"{field}: {value}")
        
        # Perform sentiment analysis
        sia = SentimentIntensityAnalyzer()
        sentiment_scores = sia.polarity_scores(row['retweeted_status']['text'])
        print("Sentiment scores:", sentiment_scores)
        
        # Categorize the sentiment
        sentiment = "Positive" if sentiment_scores['compound'] >= 0.05 else "Negative" if sentiment_scores['compound'] <= -0.05 else "Neutral"
        print("Sentiment category:", sentiment)
        print("\n")
        
    except TypeError as e:
        print(f"Error processing influential posts data: {e}")

def print_all_user_posts(data, screen_name):
    # Initialize the VADER sentiment analyzer
    sia = SentimentIntensityAnalyzer()

    print("\nAll posts by user:", screen_name)
    user_posts = data[data['user'].apply(lambda x: x['screen_name'] == screen_name)]

    all_texts = []

    for index, row in user_posts.iterrows():
        try:
            print(f"Post {index + 1}:")
            print("Post ID:", row['id_str'])
            print("Post content:", row['text'])
            print("Posted at:", row['created_at'])
            
            # Perform sentiment analysis
            sentiment_scores = sia.polarity_scores(row['text'])
            print("Sentiment scores:", sentiment_scores)
            
            # Categorize the sentiment
            sentiment = "Positive" if sentiment_scores['compound'] >= 0.05 else "Negative" if sentiment_scores['compound'] <= -0.05 else "Neutral"
            print("Sentiment category:", sentiment)
            print("\n")
            
        except KeyError as e:
            print(f"Error processing user post data: {e}")

    return all_texts

def search_mentions(data, screen_name):
    # Initialize the VADER sentiment analyzer
    sia = SentimentIntensityAnalyzer()

    all_texts = []
    print(f"\nSearching for mentions of {screen_name} in the entire dataset:")
    for index, row in data.iterrows():
        try:
            if screen_name in row['text']:
                print(f"Mention found in post {index + 1}:")
                print("Post content:", row['text'])
                print("Posted at:", row['created_at'])
                print("Mentioned by:", row['user']['screen_name'])
                print("Mentioned by location:", row['user']['location'])
                print("Favourites count:", row['favorite_count'])
                
                # Perform sentiment analysis
                sentiment_scores = sia.polarity_scores(row['text'])
                print("Sentiment scores:", sentiment_scores)
                
                # Categorize the sentiment
                sentiment = "Positive" if sentiment_scores['compound'] >= 0.05 else "Negative" if sentiment_scores['compound'] <= -0.05 else "Neutral"
                print("Sentiment category:", sentiment)                
                print("\n")
                
        except KeyError as e:
            print(f"Error processing mention data: {e}")

    return all_texts

def search_influential_post(data, post_text):
    response = tavily.search(query="What can be done to improve the situation mentioned in this post: " + post_text)
    context = [{"url": obj["url"], "content": obj["content"]} for obj in response['results']]
    print(f"Search results for the post: {post_text}")
    for result in context:
        print(f"URL: {result['url']}")
        print(f"Content: {result['content']}\n")

"""
def plot_bigrams(all_texts, screen_name):
    bigram_series = pd.Series([word for sublist in pd.Series(all_texts).dropna().apply(lambda x: [i for i in bigrams(x.split())]).tolist() for word in sublist]).value_counts()
    plt.suptitle(f'Top 10 Bigrams for user: {screen_name}', fontsize=18)
    bigram_series[:10].plot(kind='bar')
    plt.show()
"""

def print_hashtags(data, top_n=10):
    all_hashtags = []
    for index, row in data.iterrows():
        try:
            hashtags = row['retweeted_status']['entities']['hashtags']
            hashtag_texts = [hashtag['text'] for hashtag in hashtags]
            all_hashtags.extend(hashtag_texts)
        except (TypeError, KeyError):
            continue

        try:
            entities_hashtags = [hashtag['text'] for hashtag in row['entities']['hashtags']]
            all_hashtags.extend(entities_hashtags)
        except (TypeError, KeyError):
            continue

    # Count the unique occurrences of hashtags
    from collections import Counter
    hashtag_counter = Counter(all_hashtags)
    print(f"Top {top_n} unique hashtag occurrences:")
    for hashtag, count in hashtag_counter.most_common(top_n):
        print(f"{hashtag}: {count}")
    print("\n")

    # Plot the top hashtags
    top_hashtags = hashtag_counter.most_common(top_n)
    hashtags_df = pd.DataFrame(top_hashtags, columns=['Hashtag', 'Occurrences'])
    hashtags_df.plot(kind='bar', x='Hashtag', y='Occurrences', legend=False)
    plt.tight_layout()
    plt.grid(False)
    plt.suptitle('Top 10 Hashtags', fontsize=12)
    plt.show()

def filter_by_screen_name(data, screen_name):
    return data[data['user'].apply(lambda x: x['screen_name'] == screen_name)]

# Precompute filtered data for faster retrieval
filtered_data_cache = {}

def get_filtered_data(data, screen_name):
    if screen_name not in filtered_data_cache:
        filtered_data_cache[screen_name] = filter_by_screen_name(data, screen_name)
    return filtered_data_cache[screen_name]

# Iterate over each row in the dataset and print the data
def display_data(data):
    display_options = {
        1: print_user_data,
        2: print_influencer_data,
        3: print_influential_posts_data,
        4: print_hashtags,
        5: print_all_user_posts,
        6: search_mentions,
        7: search_influential_post
    }

    while True:
        print("Select the data you want to display:")
        print("1: User Data")
        print("2: Influencer Data")
        print("3: Influential Posts Data")
        print("4: Hashtags")
        print("5: All User Posts")
        print("6: Search Mentions")
        print("7: Search Influential Post")
        print("0: Exit")
        user_choice = input("Enter the number corresponding to your choice: ").strip().lower()
        if user_choice == "0":
            break

        try:
            user_choice = int(user_choice)
            if user_choice in display_options:
                if user_choice == 5:
                    screen_name = input("Enter the screen name to display all posts: ")
                    all_texts = print_all_user_posts(data, screen_name)
                    #plot_bigrams(all_texts, screen_name)
                elif user_choice == 4:
                    top_n = int(input("Enter the number of top hashtags to display (e.g., 10 or 20): "))
                    print_hashtags(data, top_n)
                elif user_choice == 6:
                    screen_name = input("Enter the screen name to search mentions: ")
                    search_mentions(data, screen_name)
                elif user_choice == 7:
                    post_text = input("Enter the text of the influential post to search: ")
                    search_influential_post(data, post_text)
                else:
                    screen_name_filter = input("Enter a screen name to filter by (or press Enter to skip): ")
                    if screen_name_filter:
                        filtered_data = get_filtered_data(data, screen_name_filter)
                        for index, row in filtered_data.iterrows():
                            print(f"Displaying data for row {index}:")
                            display_options[user_choice](row)
                            search_tavily = input("Do you want to search Tavily for this row? (yes/no): ").strip().lower()
                            if search_tavily == "yes":
                                post_text = row['text']
                                search_influential_post(data, post_text)
                    else:
                        for index, row in data.iterrows():
                            print(f"Displaying data for row {index}:")
                            display_options[user_choice](row)
                            search_tavily = input("Do you want to search Tavily for this row? (yes/no): ").strip().lower()
                            if search_tavily == "yes":
                                post_text = row['text']
                                search_influential_post(data, post_text)
            else:
                print("Invalid choice. Please select a valid option.")
        except ValueError:
            print("Invalid input. Please enter a number.")

display_data(data)


all_text = " ".join(data['text'])
#print(all_text)  # Join all text with spaces as separators

# Generate WordCloud
wc = WordCloud(background_color="white")
wc.generate(all_text)

# Display the WordCloud
plt.figure(figsize=(8, 8))
plt.imshow(wc)
plt.axis("off")
plt.show()


# version contains filtering mechanism
# ... existing code ...
