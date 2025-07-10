#!/usr/bin/env python3
"""Initialize bookmark counts for existing posts in the database."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from motor.motor_asyncio import AsyncIOMotorClient
from nadle_backend.config import settings


async def initialize_bookmark_counts():
    """Initialize bookmark_count field for all existing posts."""
    try:
        # Initialize database connection
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        print("✅ Database connection established")
        
        # Get posts and user_reactions collections
        posts_collection = db[settings.posts_collection]
        reactions_collection = db[settings.user_reactions_collection]
        
        # Get all posts using raw MongoDB queries to avoid validation issues
        posts_cursor = posts_collection.find({})
        posts = await posts_cursor.to_list(length=None)
        print(f"📊 Found {len(posts)} posts to process")
        
        if not posts:
            print("ℹ️ No posts found in database")
            return
        
        updated_count = 0
        
        for post in posts:
            post_id = str(post["_id"])
            
            # Check if bookmark_count field exists and is not None
            if post.get('bookmark_count') is not None:
                print(f"⏭️ Post {post_id[:8]}... already has bookmark_count: {post.get('bookmark_count')}")
                continue
            
            # Count actual bookmarks for this post
            bookmark_count = await reactions_collection.count_documents({
                "target_type": "post",
                "target_id": post_id,
                "bookmarked": True
            })
            
            # Update post with bookmark count
            await posts_collection.update_one(
                {"_id": post["_id"]},
                {"$set": {"bookmark_count": bookmark_count}}
            )
            
            updated_count += 1
            print(f"✅ Updated post {post_id[:8]}... - bookmark_count: {bookmark_count}")
        
        print(f"\n🎉 Successfully initialized bookmark counts for {updated_count} posts")
        
        # Verify the update
        print("\n🔍 Verification:")
        posts_with_bookmark_count = await posts_collection.count_documents({"bookmark_count": {"$exists": True}})
        print(f"Posts with bookmark_count field: {posts_with_bookmark_count}")
        
        total_bookmarks_cursor = posts_collection.aggregate([
            {"$match": {"bookmark_count": {"$exists": True}}},
            {"$group": {"_id": None, "total": {"$sum": "$bookmark_count"}}}
        ])
        total_bookmarks_result = await total_bookmarks_cursor.to_list(length=1)
        total_bookmarks = total_bookmarks_result[0]["total"] if total_bookmarks_result else 0
        print(f"Total bookmarks across all posts: {total_bookmarks}")
        
    except Exception as e:
        print(f"❌ Error initializing bookmark counts: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close database connection
        client.close()
        print("🔌 Database connection closed")


async def main():
    """Main function."""
    print("🚀 Starting bookmark count initialization...")
    await initialize_bookmark_counts()
    print("✨ Bookmark count initialization completed!")


if __name__ == "__main__":
    asyncio.run(main())