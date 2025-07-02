# Expert Tips Test Data Generator

This collection of scripts generates comprehensive test data for expert tips in the backend system. The scripts create posts with `metadata.type = "expert_tips"` that match the frontend Tip interface requirements.

## Available Scripts

### 1. Python Database Script (`generate_expert_tips_data.py`)
**Direct database access using Beanie ODM**

```bash
# Run the Python database script
python generate_expert_tips_data.py
```

**Features:**
- Direct database connection using Beanie ODM
- Creates test user and authenticates
- Generates 30 diverse expert tips
- Comprehensive content with markdown formatting
- Real-time verification and reporting
- Full error handling and logging

**Requirements:**
- Python 3.8+
- All backend dependencies installed
- MongoDB connection configured

### 2. Python API Script (`generate_expert_tips_api.py`)
**HTTP API-based generation using aiohttp**

```bash
# Ensure FastAPI server is running
cd /home/nadle/projects/Xai_Community/v5/backend
python -m uvicorn main:app --reload

# Run the Python API script
python generate_expert_tips_api.py
```

**Features:**
- Uses FastAPI REST endpoints
- Async HTTP requests with aiohttp
- User registration and authentication
- API response validation
- Same comprehensive content as database script

**Requirements:**
- Python 3.8+ with aiohttp
- FastAPI server running on localhost:8000

### 3. JavaScript API Script (`generate_expert_tips.js`)
**Node.js HTTP API-based generation**

```bash
# Ensure FastAPI server is running
cd /home/nadle/projects/Xai_Community/v5/backend
python -m uvicorn main:app --reload

# Run the JavaScript script
node generate_expert_tips.js
```

**Features:**
- Cross-platform JavaScript/Node.js
- Uses fetch API for HTTP requests
- Similar functionality to Python API script
- Easy to understand and modify

**Requirements:**
- Node.js 14+ (with fetch support) or Node.js 12+ with node-fetch
- FastAPI server running on localhost:8000

## Generated Data Structure

Each expert tip includes:

### Post Fields
- `title`: Dynamic titles based on category and expert
- `content`: Rich markdown content with detailed guidance
- `service`: "residential_community"
- `slug`: Auto-generated URL-friendly identifier

### Metadata Fields
- `type`: "expert_tips" (identifies as expert tip)
- `category`: One of 10 categories (인테리어, 생활팁, 요리, etc.)
- `tags`: 3 relevant tags based on category
- `expert_name`: Expert's name
- `expert_title`: Expert's professional title
- `views_count`: Random realistic view count (150-2500)
- `likes_count`: Random like count (10-15% of views)
- `saves_count`: Random save count (5-8% of views)
- `is_new`: Boolean indicating if tip is within last 7 days
- `visibility`: "public"
- `editor_type`: "markdown"

## Expert Categories

The generator includes 10 comprehensive categories:

1. **인테리어** (Interior Design)
   - 방 꾸미기, 가구 배치, 색상 선택, 조명, 수납, 소품

2. **생활팁** (Life Tips)
   - 청소, 정리정돈, 절약, 효율성, 생활습관, 건강

3. **요리** (Cooking)
   - 레시피, 요리법, 식재료, 주방용품, 건강식, 간편식

4. **육아** (Childcare)
   - 아이 돌보기, 교육, 놀이, 건강관리, 소통, 성장

5. **반려동물** (Pet Care)
   - 반려견, 반려묘, 건강관리, 훈련, 용품, 놀이

6. **가드닝** (Gardening)
   - 식물 키우기, 베란다, 화분, 물주기, 흙, 햇빛

7. **DIY** (Do It Yourself)
   - 만들기, 수리, 조립, 도구, 재료, 창작

8. **건강** (Health)
   - 운동, 스트레칭, 영양, 수면, 스트레스, 관리

9. **재정관리** (Financial Management)
   - 절약, 투자, 가계부, 적금, 보험, 계획

10. **취미** (Hobbies)
    - 독서, 음악, 영화, 게임, 수집, 체험

## Expert Profiles

10 diverse expert profiles with specializations:

- **김민수** - 인테리어 디자이너 (인테리어, DIY)
- **박영희** - 생활컨설턴트 (생활팁)
- **이준호** - 요리연구가 (요리, 건강)
- **최수진** - 육아전문가 (육아)
- **정민아** - 반려동물 훈련사 (반려동물, 건강)
- **홍길동** - 가드닝 전문가 (가드닝, 생활팁)
- **서지혜** - DIY 크리에이터 (DIY, 인테리어)
- **강태우** - 헬스 트레이너 (건강)
- **윤소영** - 재정관리 전문가 (재정관리)
- **한승우** - 취미생활 큐레이터 (취미, 생활팁)

## Content Quality

Each generated tip includes:

### Structured Content
- Clear headings and sections
- Step-by-step instructions
- Practical examples
- Safety considerations
- Success tips

### Realistic Engagement
- Variable view counts (150-2500)
- Proportional likes and saves
- Recent vs. older content mix
- New content indicators

### SEO-Friendly
- Keyword-rich titles
- Relevant tags
- Category-based organization
- Search-optimized content

## Verification

All scripts include verification functionality:

- **Count Verification**: Confirms expected number of tips created
- **Category Analysis**: Shows distribution across categories
- **Expert Analysis**: Shows tips per expert
- **Data Integrity**: Validates required fields and structure

## API Integration

The generated tips work seamlessly with:

- **Frontend Tip Interface**: Matches expected data structure
- **Search and Filtering**: Supports category and tag filtering
- **Pagination**: Compatible with list endpoints
- **User Interactions**: Ready for likes, saves, views tracking

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```
   Error: MongoDB connection failed
   Solution: Check MongoDB Atlas connection string and network access
   ```

2. **Authentication Failed**
   ```
   Error: Failed to create/authenticate user
   Solution: Ensure FastAPI server is running and accessible
   ```

3. **Permission Denied**
   ```
   Error: 403 Forbidden
   Solution: Check user authentication and permissions
   ```

### Debug Mode

Add debug logging to any script:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

```javascript
// Add detailed console logging
console.log('Debug:', response.status, await response.text());
```

## Customization

### Modify Content
Edit the `EXPERT_TIP_TEMPLATES` dictionary to add new templates or modify existing ones.

### Adjust Categories
Update `EXPERT_CATEGORIES` to add new categories or modify keywords.

### Change Expert Profiles
Modify `EXPERT_PROFILES` to add new experts or change specializations.

### Scale Generation
Change `num_tips` parameter to generate more or fewer tips.

## Frontend Integration

The generated expert tips are designed to work with the frontend Tip interface:

```typescript
interface Tip {
  id: number;
  title: string;
  content: string;
  expert_name: string;
  expert_title: string;
  created_at: string;
  category: string;
  tags: string[];
  views_count: number;
  likes_count: number;
  saves_count: number;
  is_new: boolean;
}
```

## Production Considerations

### Data Quality
- Review generated content for appropriateness
- Verify expert information accuracy
- Check for duplicate or similar content

### Performance
- Monitor database performance during bulk creation
- Consider batch processing for large datasets
- Implement rate limiting for API-based generation

### Maintenance
- Regularly update content templates
- Add new expert profiles periodically
- Monitor engagement metrics for realistic adjustments

---

**Note**: These scripts are designed for development and testing purposes. For production use, consider implementing proper content review workflows and data validation processes.