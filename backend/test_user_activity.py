"""Test script to check user activity data for specific accounts."""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def login(email: str, password: str):
    """Login and get access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"Login failed for {email}: {response.status_code} - {response.text}")
            return None

async def get_user_activity(token: str, page: int = 1, limit: int = 50):
    """Get user activity data."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/users/me/activity",
            params={"page": page, "limit": limit},
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get activity: {response.status_code} - {response.text}")
            return None

async def get_user_posts(token: str, page: int = 1, limit: int = 50):
    """Get all posts by current user."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/posts/my-posts",
            params={"page": page, "limit": limit},
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get posts: {response.status_code} - {response.text}")
            return None

async def analyze_user_activity(email: str, password: str):
    """Analyze activity for a specific user."""
    print(f"\n{'='*60}")
    print(f"Analyzing activity for: {email}")
    print(f"{'='*60}")
    
    # Login
    token = await login(email, password)
    if not token:
        return
    
    # Get activity data
    activity = await get_user_activity(token)
    if not activity:
        return
    
    # Get direct posts data for comparison
    posts_data = await get_user_posts(token)
    
    print("\n📊 ACTIVITY SUMMARY:")
    print(f"Total Posts: {activity['pagination']['posts']['total_count']}")
    print(f"Total Comments: {activity['pagination']['comments']['total_count']}")
    print(f"Total Reactions: {activity['pagination']['reactions']['total_count']}")
    
    # Analyze posts by type
    print("\n📝 POSTS BY TYPE:")
    for post_type, posts in activity['posts'].items():
        if posts:
            print(f"\n{post_type}: {len(posts)} posts")
            for post in posts[:3]:  # Show first 3
                print(f"  - [{post['id']}] {post['title']} (created: {post['created_at'][:10]})")
    
    # Analyze comments
    print("\n💬 COMMENTS:")
    if activity['comments']:
        print(f"Total comments: {len(activity['comments'])}")
        # Group by subtype
        normal_comments = [c for c in activity['comments'] if not c.get('subtype')]
        service_inquiries = [c for c in activity['comments'] if c.get('subtype') == 'service_inquiry']
        service_reviews = [c for c in activity['comments'] if c.get('subtype') == 'service_review']
        
        print(f"  - Normal comments: {len(normal_comments)}")
        print(f"  - Service inquiries: {len(service_inquiries)}")
        print(f"  - Service reviews: {len(service_reviews)}")
        
        print("\nFirst 5 comments:")
        for comment in activity['comments'][:5]:
            subtype = f" [{comment['subtype']}]" if comment.get('subtype') else ""
            print(f"  - {comment['content'][:50]}...{subtype} (on: {comment.get('post_title', 'Unknown')})")
    
    # Analyze reactions
    print("\n👍 REACTIONS:")
    reaction_types = ['reaction-likes', 'reaction-dislikes', 'reaction-bookmarks']
    for reaction_type in reaction_types:
        if reaction_type in activity:
            total = sum(len(items) for items in activity[reaction_type].values())
            print(f"\n{reaction_type}: {total} total")
            for page_type, reactions in activity[reaction_type].items():
                if reactions:
                    print(f"  - {page_type}: {len(reactions)}")
    
    # Compare with direct posts API
    if posts_data and 'items' in posts_data:
        print(f"\n🔍 DIRECT POSTS API COMPARISON:")
        print(f"Direct API total: {posts_data['total']}")
        print(f"Activity API total: {activity['pagination']['posts']['total_count']}")
        
        if posts_data['total'] != activity['pagination']['posts']['total_count']:
            print("⚠️  MISMATCH DETECTED!")
    
    # Save full data for analysis
    filename = f"activity_{email.replace('@', '_at_')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            "email": email,
            "timestamp": datetime.now().isoformat(),
            "activity": activity,
            "direct_posts": posts_data
        }, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Full data saved to: {filename}")

async def main():
    """Run analysis for both accounts."""
    accounts = [
        ("ktsfrank@naver.com", "Kts137900!"),
        ("jung-su@example.com", "Kjs0821!")
    ]
    
    for email, password in accounts:
        await analyze_user_activity(email, password)
        await asyncio.sleep(1)  # Small delay between requests

if __name__ == "__main__":
    asyncio.run(main())