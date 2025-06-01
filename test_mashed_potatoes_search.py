import asyncio
from app.services.usda_service import USDAService, get_usda_service
from app.core.config import get_settings

async def test_mashed_potatoes_search():
    settings = get_settings()
    usda_service = get_usda_service()
    
    print('=== USDA検索テスト: Potatoes, mashed, prepared ===')
    
    try:
        # 基本検索
        results = await usda_service.search_foods_rich(
            query='Potatoes, mashed, prepared',
            page_size=10,
            data_types=['Foundation', 'SR Legacy', 'FNDDS', 'Branded'],
            require_all_words=True
        )
        
        print(f'基本検索結果: {len(results)} 件')
        for i, result in enumerate(results[:8]):
            print(f'{i+1}. FDC ID: {result.fdc_id}')
            print(f'   Description: {result.description}')
            print(f'   Data Type: {result.data_type}')
            print(f'   Score: {result.score}')
            print(f'   Brand: {result.brand_owner or "N/A"}')
            print()
            
        # より広い検索
        print('=== より広い検索: mashed potatoes ===')
        results2 = await usda_service.search_foods_rich(
            query='mashed potatoes',
            page_size=10,
            data_types=['Foundation', 'SR Legacy', 'FNDDS', 'Branded'],
            require_all_words=False
        )
        
        print(f'広い検索結果: {len(results2)} 件')
        for i, result in enumerate(results2[:8]):
            print(f'{i+1}. FDC ID: {result.fdc_id}')
            print(f'   Description: {result.description}')
            print(f'   Data Type: {result.data_type}')
            print(f'   Score: {result.score}')
            print()
            
        # さらに簡単な検索
        print('=== シンプル検索: potatoes ===')
        results3 = await usda_service.search_foods_rich(
            query='potatoes',
            page_size=10,
            data_types=['Foundation', 'SR Legacy', 'FNDDS'],
            require_all_words=False
        )
        
        print(f'シンプル検索結果: {len(results3)} 件')
        for i, result in enumerate(results3[:5]):
            if 'mashed' in result.description.lower():
                print(f'{i+1}. FDC ID: {result.fdc_id}')
                print(f'   Description: {result.description}')
                print(f'   Data Type: {result.data_type}')
                print(f'   Score: {result.score}')
                print()
    
    except Exception as e:
        print(f'エラー: {e}')

if __name__ == "__main__":
    asyncio.run(test_mashed_potatoes_search()) 