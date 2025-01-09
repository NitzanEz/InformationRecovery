import praw
import os
import re
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Reddit API
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
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
def search_reddit_to_excel(subreddit, query, limit=20, output_file="reddit_results.xlsx"):
    try:
        print(f"Searching Reddit for '{query}' in r/{subreddit}...")
        # Search for posts in the specified subreddit with the given query, 
        # limit the number of results, sort by controversial posts, and filter results from the last 24 hours
        results = reddit.subreddit(subreddit).search(query, limit=limit, sort='controversial', time_filter='day')

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

# Main script
if __name__ == "__main__":
    # Step 1: Search Reddit and save results
    try:
        search_reddit_to_excel("all", "Funny cats", limit=20)
    except Exception as e:
        print(f"Error during Reddit search: {e}")
