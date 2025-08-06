import nltk
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# MongoDB connection string
uri = "mongodb+srv://alejandrocanomn:" + \
    os.getenv("DB_PASSWORD") + \
    "@cluster0.vlqder.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


# Download required NLTK data (updated for newer NLTK versions)
def ensure_nltk_data():
    """Ensure all required NLTK data is downloaded"""
    required_packages = ['punkt', 'punkt_tab']

    for package in required_packages:
        try:
            nltk.data.find(f'tokenizers/{package}')
            print(f"✅ NLTK {package} already available")
        except LookupError:
            print(f"📥 Downloading NLTK {package}...")
            nltk.download(package, quiet=True)
            print(f"✅ NLTK {package} downloaded successfully")


# Download NLTK data
ensure_nltk_data()


class SimpleNLP:
    def __init__(self):
        """Initialize with MongoDB connection"""
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        self.db = self.client.canadian_tire_scraper
        self.review_collection = self.db.reviews

    def process_review_nlp(self, review_id, concatenate_text=False):
        """Process review text and update the existing review document with NLP data"""

        # Find the existing review document
        review = self.review_collection.find_one({"review_id": review_id})

        if not review:
            print(f"❌ Review with ID {review_id} not found")
            return None

        # Get text data from the review
        title = review.get("title", "")
        body = review.get("body", "")

        # Prepare text for processing
        if concatenate_text:
            # Concatenate title and body
            full_text = f"{title} {body}" if title else body
        else:
            # Process only the body
            full_text = body

        if not full_text.strip():
            print(f"⚠️ No text content found for review {review_id}")
            return None

        # Sentence segmentation
        sentences = nltk.sent_tokenize(full_text)

        # Word tokenization
        words = nltk.word_tokenize(full_text)

        # Update the existing review document with NLP data
        update_data = {
            "sentences": sentences,
            "words": words,
            "nlp_processed_at": datetime.now(),
            "nlp_concatenated": concatenate_text,
            "nlp_text_used": full_text
        }

        # Update the document in MongoDB
        result = self.review_collection.update_one(
            {"review_id": review_id},
            {"$set": update_data}
        )

        if result.modified_count > 0:
            print(f"✅ Review {review_id} updated with NLP data")
            print(
                f"   📝 Text: '{full_text[:100]}{'...' if len(full_text) > 100 else ''}'")
            print(
                f"   📊 Found {len(sentences)} sentences and {len(words)} words")
            return {
                "review_id": review_id,
                "sentences_count": len(sentences),
                "words_count": len(words),
                "updated": True
            }
        else:
            print(f"⚠️ No changes made to review {review_id}")
            return None

    def process_all_reviews(self, concatenate_text=False, skip_processed=True):
        """Process all reviews in the collection"""

        # Build query filter
        query_filter = {}
        if skip_processed:
            # Skip reviews that already have NLP data
            query_filter["sentences"] = {"$exists": False}

        reviews = list(self.review_collection.find(query_filter))

        if not reviews:
            if skip_processed:
                print("✅ All reviews already processed with NLP data")
            else:
                print("❌ No reviews found in the database")
            return []

        print(f"🔄 Processing {len(reviews)} reviews with NLP...")

        results = []
        for i, review in enumerate(reviews, 1):
            review_id = review.get("review_id", "unknown")
            print(f"\n📝 Processing review {i}/{len(reviews)}: {review_id}")

            result = self.process_review_nlp(review_id, concatenate_text)
            if result:
                results.append(result)

        return results

    def get_nlp_stats(self):
        """Get statistics about NLP processing"""
        total_reviews = self.review_collection.count_documents({})
        processed_reviews = self.review_collection.count_documents(
            {"sentences": {"$exists": True}})

        stats = {
            "total_reviews": total_reviews,
            "processed_reviews": processed_reviews,
            "unprocessed_reviews": total_reviews - processed_reviews,
            "processing_percentage": (processed_reviews / total_reviews * 100) if total_reviews > 0 else 0
        }

        return stats

    def get_sample_processed_review(self):
        """Get a sample of processed review to show the structure"""
        sample = self.review_collection.find_one(
            {"sentences": {"$exists": True}})
        return sample


# Example usage
if __name__ == "__main__":
    nlp = SimpleNLP()

    print("🚀 Starting NLP processing for reviews...")
    print("=" * 50)

    # Get initial stats
    initial_stats = nlp.get_nlp_stats()
    print(f"📊 Initial Stats:")
    print(f"   Total reviews: {initial_stats['total_reviews']}")
    print(f"   Already processed: {initial_stats['processed_reviews']}")
    print(f"   Pending processing: {initial_stats['unprocessed_reviews']}")
    print(
        f"   Processing percentage: {initial_stats['processing_percentage']:.1f}%")

    if initial_stats['unprocessed_reviews'] > 0:
        print(
            f"\n🔄 Processing {initial_stats['unprocessed_reviews']} unprocessed reviews...")

        # Process all unprocessed reviews (concatenating title + body)
        results = nlp.process_all_reviews(
            concatenate_text=True, skip_processed=True)

        print(f"\n✅ Processing completed!")
        print(f"📈 Successfully processed: {len(results)} reviews")

        # Get final stats
        final_stats = nlp.get_nlp_stats()
        print(f"\n📊 Final Stats:")
        print(f"   Total reviews: {final_stats['total_reviews']}")
        print(f"   Processed reviews: {final_stats['processed_reviews']}")
        print(
            f"   Processing percentage: {final_stats['processing_percentage']:.1f}%")

        # Show sample of processed review
        sample = nlp.get_sample_processed_review()
        if sample:
            print(f"\n📝 Sample processed review structure:")
            print(f"   Review ID: {sample.get('review_id')}")
            print(f"   Reviewer: {sample.get('reviewer')}")
            print(f"   Title: {sample.get('title')}")
            print(
                f"   Body: {sample.get('body', '')[:100]}{'...' if len(sample.get('body', '')) > 100 else ''}")
            print(f"   Sentences count: {len(sample.get('sentences', []))}")
            print(f"   Words count: {len(sample.get('words', []))}")
            print(f"   Sample sentences: {sample.get('sentences', [])[:2]}")
    else:
        print(f"\n✅ All reviews already processed!")

        # Show sample anyway
        sample = nlp.get_sample_processed_review()
        if sample:
            print(f"\n📝 Sample processed review:")
            print(f"   Review ID: {sample.get('review_id')}")
            print(f"   Sentences: {len(sample.get('sentences', []))}")
            print(f"   Words: {len(sample.get('words', []))}")

    nlp.client.close()
    print(f"\n🎉 NLP processing completed!")
