import praw
import os
import re
import pandas as pd
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Reddit API
reddit = praw.Reddit(
    # This is getting data from .env file
    client_id = os.getenv("REDDIT_CLIENT_ID"),
    client_secret = os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent = os.getenv("REDDIT_USER_AGENT"),
)

print("Reddit API initialized. Read-only mode:", reddit.read_only)

# Define stopwords
STOPWORDS = set([
    "and", "or", "the", "is", "in", "to", "a", "of", "on", "for", "with", "it", "as", "at", "this", "that",
    "an", "be", "are", "by", "was", "were", "from", "has", "have", "had", "but", "not", "you", "we", "they", "he", "she", "i", "me", "my"
])

# Function to clean text (remove emojis, stopwords, special characters)
def clean_text(text):
    # Remove emojis and special characters
    text = re.sub(r"[^\w\s]", "", text)
    # Convert to lowercase
    text = text.lower()
    # Remove stopwords
    words = text.split()
    filtered_words = [word for word in words if word not in STOPWORDS]
    return " ".join(filtered_words)

# Function to search Reddit and save results to Excel
def search_reddit_to_excel(subreddit, query, limit, output_file="reddit_results.xlsx"):
    try:
        print(f"Searching Reddit for '{query}' in r/{subreddit}...")
        # Search for posts in the specified subreddit with the given query, 
        # limit the number of results, sort by controversial posts, and filter results from the last 24 hours
        # results = reddit.subreddit(subreddit).search(query, limit=limit, sort='controversial', time_filter='day')
        # results = reddit.subreddit(subreddit).search(query, limit=limit)
        results = reddit.subreddit(subreddit).search(
            query=query,
            limit=limit,
            sort="hot",
            # time_filter="hour" # Fetch posts from the last few hours (Reddit API uses 'hour', which gets the most recent content)
            # time_filter="day"
            time_filter="month"            
        )

        data = []
        for post in results:
            data.append({
                "Title": post.title,
                "Body": post.selftext,  # Include post body
                "Reddit Post URL": f"https://reddit.com{post.permalink}",
                "Score": post.score,
                "Subreddit": post.subreddit.display_name,
            })
        
        if data:
            # Save results to Excel
            df = pd.DataFrame(data)
            df.to_excel(output_file, index=False)
            print(f"Results saved to {output_file}")
        else:
            print(f"No results found for '{query}' in r/{subreddit}")
    
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

# Function to build an inverted index with word locations and save as DataFrame
def build_inverse_index_with_locations(input_file="reddit_results.xlsx"):
    try:
        # Read the data from the Excel file
        df = pd.read_excel(input_file)
        
        # Store the inverted index (word -> [list of (post_index, word_position)])
        inverted_index = {}

        # Iterate over posts and build inverted index with positions
        for post_index, row in df.iterrows():
            title = str(row["Title"])
            body = str(row["Body"])
            content = title + " " + body

            # Clean the content (remove stopwords, special characters)
            cleaned_content = clean_text(content)
            words = cleaned_content.split()

            for word_position, word in enumerate(words):
                # Add the word and its position to the inverted index
                if word not in inverted_index:
                    inverted_index[word] = []
                inverted_index[word].append(post_index + 1)  # Store post index (1-indexed)
        
        # Create a DataFrame to store the word and corresponding post-location information
        word_post_data = []

        # Get the top 15 words by frequency (from the cleaned content of all posts)
        all_text = " ".join(df["Title"].astype(str) + " " + df["Body"].astype(str))
        cleaned_text = clean_text(all_text)
        word_counts = Counter(cleaned_text.split())
        common_words = word_counts.most_common(15)

        # Loop through the common words and get their post locations
        for word, _ in common_words:
            if word in inverted_index:
                # Aggregate all posts where the word appears
                post_list = inverted_index[word]
                # Join posts with commas
                post_string = ",".join(map(str, sorted(set(post_list))))  # Remove duplicates and sort the posts
                word_post_data.append({"word": word, "posts": post_string})

        # Convert to DataFrame
        word_post_df = pd.DataFrame(word_post_data)

        # Save the DataFrame to Excel
        word_post_df.to_excel("word_post_locations.xlsx", index=False)
        print("\nInverted Index with Word Locations saved to 'word_post_locations.xlsx'.")
    
    except Exception as e:
        print(f"An error occurred while building the inverted index: {e}")
        raise

# Function to calculate TF-IDF
def calculate_tfidf(input_file="reddit_results.xlsx", query="Funny cats"):
    try:
        # Read the data from the Excel file
        df = pd.read_excel(input_file)
        df["Content"] = df["Title"].astype(str) + " " + df["Body"].astype(str)
        cleaned_content = df["Content"].apply(clean_text)
        
        # Vectorize the cleaned content
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(cleaned_content)
        terms = vectorizer.get_feature_names_out()
        
        # Calculate TF-IDF for the query terms
        query_terms = clean_text(query).split()
        print("\nTF-IDF Scores for Query Terms:")
        for term in query_terms:
            if term in terms:
                term_index = vectorizer.vocabulary_.get(term)
                tfidf_score = tfidf_matrix[:, term_index].toarray().sum()
                print(f"{term}: {tfidf_score}")
            else:
                print(f"{term}: Not found in the results.")
    
    except Exception as e:
        print(f"An error occurred while calculating TF-IDF: {e}")
        raise

# Main script
if __name__ == "__main__":
    # Step 1: Search Reddit and save results
    try:
        search_reddit_to_excel("all", "Funny cats", limit=1000)
    except Exception as e:
        print(f"Error during Reddit search: {e}")
    
    # Step 2: Build an inverted index with word locations and save to Excel
    try:
        build_inverse_index_with_locations()
    except Exception as e:
        print(f"Error during inverted index creation: {e}")
    
    # Step 3: Calculate TF-IDF
    try:
        calculate_tfidf(query="Funny cats")
    except Exception as e:
        print(f"Error during TF-IDF calculation: {e}")
