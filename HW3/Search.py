import praw
import os
import re
import pandas as pd
from dotenv import load_dotenv
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load environment variables
load_dotenv()

# Initialize Reddit API
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

# Define stopwords and lemmatizer
STOPWORDS = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

# Function to clean text
def clean_text(text):
    text = re.sub(r"[^\w\s]", "", text)  # Remove special characters
    text = text.lower()  # Convert to lowercase
    words = text.split()
    filtered_words = [lemmatizer.lemmatize(word) for word in words if word not in STOPWORDS]
    return " ".join(filtered_words)

# Function to search Reddit and save results to Excel
def search_reddit_to_excel(subreddit, query, limit=20, output_file="reddit_results.xlsx"):
    results = reddit.subreddit(subreddit).search(
        query=query, limit=limit, sort="hot", time_filter="day"
    )
    data = []
    for post in results:
        post_time = pd.to_datetime(post.created_utc, unit="s")  # Convert to datetime
        data.append({
            "Title": post.title,
            "Body": post.selftext,
            "Upvotes": post.score,
            "Comments": post.num_comments,
            "Subreddit": post.subreddit.display_name,
            "Post Time (UTC)": post_time,
        })
    df = pd.DataFrame(data)
    df.to_excel(output_file, index=False)
    print(f"Results saved to {output_file}")

# Function to calculate TF-IDF and rank posts based on engagement
def calculate_tfidf_with_engagement(input_file="reddit_results.xlsx", query="Funny cats"):
    # Load data
    df = pd.read_excel(input_file)
    
    # Combine title and body into a single content column
    df["Content"] = (df["Title"].astype(str) + " " + df["Body"].fillna("")).apply(clean_text)

    # TF-IDF calculation
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df["Content"])
    query_vector = vectorizer.transform([clean_text(query)])
    df["Relevance"] = cosine_similarity(query_vector, tfidf_matrix).flatten()

    # Normalize engagement score using total-based normalization
    total_upvotes = df["Upvotes"].sum() or 1
    total_comments = df["Comments"].sum() or 1
    df["Engagement Score"] = (
        0.7 * df["Upvotes"] / total_upvotes + 0.3 * df["Comments"] / total_comments
    )

    # Combine relevance and engagement
    df["PageRank"] = 0.7 * df["Relevance"] + 0.3 * df["Engagement Score"]

    # Rank posts
    ranked_df = df.sort_values(by="PageRank", ascending=False)

    # Save ranked results
    ranked_df.to_excel("ranked_results.xlsx", index=False)
    print("Ranked results saved to 'ranked_results.xlsx'")

# Main script
if __name__ == "__main__":
    # Step 1: Search Reddit and save results
    search_reddit_to_excel("all", "Funny cats", limit=10)

    # Step 2: Calculate TF-IDF and rank posts
    calculate_tfidf_with_engagement(query="Funny cats")
