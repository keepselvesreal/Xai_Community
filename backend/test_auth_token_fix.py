"""Test script to verify authentication token handling after fixes."""

import asyncio
import httpx
import json
from datetime import datetime


async def test_auth_flow():
    """Test complete authentication flow."""
    base_url = "http://localhost:8000/api"
    
    # Test credentials
    test_email = f"test_{datetime.now().timestamp()}@example.com"
    test_password = "Test123456!"
    
    async with httpx.AsyncClient() as client:
        # 1. Register a new user
        print("1. Testing registration...")
        register_response = await client.post(
            f"{base_url}/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "user_handle": f"test_{int(datetime.now().timestamp())}",
                "display_name": "Test User"
            }
        )
        
        if register_response.status_code == 201:
            print("✓ Registration successful")
            print(f"  Response: {register_response.json()}")
        else:
            print(f"✗ Registration failed: {register_response.status_code}")
            print(f"  Error: {register_response.text}")
            return
        
        # 2. Login with the registered user
        print("\n2. Testing login...")
        login_data = {
            "username": test_email,  # OAuth2PasswordRequestForm expects 'username'
            "password": test_password
        }
        
        login_response = await client.post(
            f"{base_url}/auth/login",
            data=login_data,  # Form data, not JSON
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code == 200:
            print("✓ Login successful")
            login_data = login_response.json()
            access_token = login_data.get("access_token")
            print(f"  Token received: {access_token[:20]}...")
            print(f"  Token type: {login_data.get('token_type')}")
        else:
            print(f"✗ Login failed: {login_response.status_code}")
            print(f"  Error: {login_response.text}")
            return
        
        # 3. Test token storage simulation (what frontend does)
        print("\n3. Testing token storage...")
        # Simulate JSON stringification issue
        json_stringified = json.dumps(access_token)
        print(f"  JSON stringified token: {json_stringified[:30]}...")
        
        # Simulate fix - parse if JSON stringified
        if json_stringified.startswith('"') and json_stringified.endswith('"'):
            fixed_token = json.loads(json_stringified)
            print(f"  Fixed token: {fixed_token[:20]}...")
        else:
            fixed_token = json_stringified
        
        # 4. Get user profile with token
        print("\n4. Testing profile fetch with token...")
        profile_response = await client.get(
            f"{base_url}/auth/profile",
            headers={"Authorization": f"Bearer {fixed_token}"}
        )
        
        if profile_response.status_code == 200:
            print("✓ Profile fetch successful")
            user_data = profile_response.json()
            print(f"  User email: {user_data.get('email')}")
            print(f"  User handle: {user_data.get('user_handle')}")
        else:
            print(f"✗ Profile fetch failed: {profile_response.status_code}")
            print(f"  Error: {profile_response.text}")
        
        # 5. Test with incorrectly formatted token (with quotes)
        print("\n5. Testing with JSON stringified token (should fail)...")
        bad_profile_response = await client.get(
            f"{base_url}/auth/profile",
            headers={"Authorization": f"Bearer {json_stringified}"}
        )
        
        if bad_profile_response.status_code == 401:
            print("✓ Correctly rejected malformed token")
            print(f"  Error: {bad_profile_response.json().get('detail')}")
        else:
            print(f"✗ Unexpected response: {bad_profile_response.status_code}")
        
        # 6. Test creating a post with authentication
        print("\n6. Testing authenticated API call (create post)...")
        post_response = await client.post(
            f"{base_url}/posts/",  # Add trailing slash to avoid redirect
            json={
                "title": "Test Post After Auth Fix",
                "content": "This post tests that authentication is working correctly after token storage fixes.",
                "service": "community",
                "metadata": {
                    "type": "자유게시판",
                    "tags": ["test", "authentication"],
                    "is_notice": False,
                    "is_expert": False,
                    "file_ids": []
                }
            },
            headers={"Authorization": f"Bearer {fixed_token}"}
        )
        
        if post_response.status_code == 201:
            print("✓ Post created successfully")
            post_data = post_response.json()
            print(f"  Post slug: {post_data.get('slug')}")
            print(f"  Author: {post_data.get('author', {}).get('user_handle')}")
        else:
            print(f"✗ Post creation failed: {post_response.status_code}")
            print(f"  Error: {post_response.text}")


if __name__ == "__main__":
    print("Testing Authentication Token Handling")
    print("=" * 50)
    asyncio.run(test_auth_flow())
    print("\n" + "=" * 50)
    print("Test complete!")