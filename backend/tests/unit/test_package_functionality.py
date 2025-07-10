#!/usr/bin/env python3
"""
Test script for nadle_backend package functionality.
Tests various aspects of the installed package to ensure proper operation.
"""

def test_basic_import():
    """Test basic package import."""
    print("=== Basic Import Test ===")
    try:
        import nadle_backend
        print("✓ Successfully imported nadle_backend")
        print(f"✓ Version: {nadle_backend.__version__}")
        print(f"✓ Author: {nadle_backend.__author__}")
        print(f"✓ License: {nadle_backend.__license__}")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_package_info():
    """Test package information function."""
    print("\n=== Package Info Test ===")
    try:
        import nadle_backend
        info = nadle_backend.get_package_info()
        print("✓ Package info retrieved successfully:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        return True
    except Exception as e:
        print(f"✗ Package info test failed: {e}")
        return False


def test_configuration():
    """Test configuration system."""
    print("\n=== Configuration Test ===")
    try:
        import nadle_backend
        settings = nadle_backend.settings
        print("✓ Settings imported successfully")
        print(f"✓ API Title: {settings.api_title}")
        print(f"✓ Environment: {settings.environment}")
        print(f"✓ Database: {settings.database_name}")
        print(f"✓ Port: {settings.port}")
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_database_components():
    """Test database related components."""
    print("\n=== Database Components Test ===")
    try:
        import nadle_backend
        
        # Test database connection object
        database = nadle_backend.database
        print("✓ Database connection object imported")
        
        # Test IndexManager
        index_manager = nadle_backend.IndexManager
        print("✓ IndexManager class imported")
        
        return True
    except Exception as e:
        print(f"✗ Database components test failed: {e}")
        return False


def test_models():
    """Test data models."""
    print("\n=== Models Test ===")
    try:
        import nadle_backend
        
        # Test core models
        User = nadle_backend.User
        Post = nadle_backend.Post
        Comment = nadle_backend.Comment
        
        print("✓ User model imported")
        print("✓ Post model imported")
        print("✓ Comment model imported")
        
        # Test model attributes (basic validation)
        print(f"✓ User model name: {User.__name__}")
        print(f"✓ Post model name: {Post.__name__}")
        print(f"✓ Comment model name: {Comment.__name__}")
        
        return True
    except Exception as e:
        print(f"✗ Models test failed: {e}")
        return False


def test_individual_imports():
    """Test importing individual modules."""
    print("\n=== Individual Imports Test ===")
    success_count = 0
    total_tests = 0
    
    # Test services
    modules_to_test = [
        ("nadle_backend.services.auth_service", "AuthService"),
        ("nadle_backend.services.posts_service", "PostsService"),
        ("nadle_backend.services.comments_service", "CommentsService"),
        ("nadle_backend.repositories.user_repository", "UserRepository"),
        ("nadle_backend.repositories.post_repository", "PostRepository"),
        ("nadle_backend.utils.jwt", "JWTManager"),
        ("nadle_backend.utils.password", "PasswordManager"),
    ]
    
    for module_name, class_name in modules_to_test:
        total_tests += 1
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✓ {module_name}.{class_name}")
            success_count += 1
        except Exception as e:
            print(f"✗ {module_name}.{class_name}: {e}")
    
    print(f"\nIndividual imports: {success_count}/{total_tests} successful")
    return success_count == total_tests


def test_environment_isolation():
    """Test that package works independently of development environment."""
    print("\n=== Environment Isolation Test ===")
    try:
        import sys
        import nadle_backend
        
        # Check that we're not importing from the development directory
        package_path = nadle_backend.__file__
        print(f"✓ Package loaded from: {package_path}")
        
        if ".venv" in package_path and "site-packages" in package_path:
            print("✓ Package loaded from virtual environment (not development directory)")
            return True
        else:
            print("⚠ Package might be loaded from development directory")
            return False
            
    except Exception as e:
        print(f"✗ Environment isolation test failed: {e}")
        return False


def main():
    """Run all tests and summarize results."""
    print("Testing nadle_backend package functionality...\n")
    
    tests = [
        test_basic_import,
        test_package_info,
        test_configuration,
        test_database_components,
        test_models,
        test_individual_imports,
        test_environment_isolation,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Package is working correctly.")
        return True
    else:
        print("⚠ Some tests failed. Check the details above.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)