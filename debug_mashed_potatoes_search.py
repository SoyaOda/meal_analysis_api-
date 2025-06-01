import asyncio
import json
from app.services.usda_service import USDAService, get_usda_service
from app.core.config import get_settings
from app.api.v1.schemas.meal import USDACandidateQuery

async def debug_mashed_potatoes_tiered_search():
    settings = get_settings()
    usda_service = get_usda_service()
    
    print('=== USDA階層検索デバッグ: Mashed Potatoes ===')
    
    # Phase1クエリ候補を模擬
    mock_candidate = USDACandidateQuery(
        query_term="Potatoes, mashed, prepared",
        granularity_level='dish',
        original_term="Mashed Potatoes",
        reason_for_query="Standard dish query following USDA hierarchical format."
    )
    
    try:
        print(f'Phase1候補: {mock_candidate.query_term}')
        print(f'粒度レベル: {mock_candidate.granularity_level}')
        print()
        
        # 階層検索実行
        print('🔍 階層検索を実行中...')
        tiered_results = await usda_service.execute_tiered_usda_search(
            phase1_candidate=mock_candidate,
            brand_context=None,
            max_results_cap=15
        )
        
        print(f'階層検索結果: {len(tiered_results)} 件')
        print()
        
        # 結果を詳細表示
        for i, result in enumerate(tiered_results):
            tier_info = f" (Tier {getattr(result, 'search_tier', 'N/A')})" if hasattr(result, 'search_tier') else ""
            query_used = f" Query: {getattr(result, 'search_query_used', 'N/A')}" if hasattr(result, 'search_query_used') else ""
            
            print(f'{i+1}. FDC ID: {result.fdc_id}{tier_info}')
            print(f'   Description: {result.description}')
            print(f'   Data Type: {result.data_type}')
            print(f'   Score: {result.score}')
            print(f'   Brand: {result.brand_owner or "N/A"}')
            print(f'   {query_used}')
            
            # SR Legacy項目を特に注目
            if result.data_type == "SR Legacy" and "mashed" in result.description.lower():
                print(f'   ⭐ SR Legacy Mashed Potato Entry Found!')
            
            # Combo meal項目を識別
            if any(combo in result.description.lower() for combo in ["with", "&", "and", "meal", "dinner", "plate"]):
                print(f'   ⚠️  Combo meal detected')
            
            print()
            
        # SR Legacy項目の有無を確認
        sr_legacy_items = [r for r in tiered_results if r.data_type == "SR Legacy"]
        mashed_potato_items = [r for r in tiered_results if "mashed" in r.description.lower() and "potato" in r.description.lower()]
        standalone_mashed = [r for r in mashed_potato_items if not any(combo in r.description.lower() for combo in ["with", "&", "and", "meal", "dinner", "plate"])]
        
        print('=== 分析結果 ===')
        print(f'総検索結果: {len(tiered_results)}')
        print(f'SR Legacy項目: {len(sr_legacy_items)}')
        print(f'Mashed Potato項目: {len(mashed_potato_items)}')
        print(f'Standalone Mashed Potato: {len(standalone_mashed)}')
        
        if standalone_mashed:
            print('\n✅ 適切なStandalone Mashed Potato項目:')
            for item in standalone_mashed:
                print(f'   - FDC {item.fdc_id}: {item.description} ({item.data_type})')
        else:
            print('\n❌ 適切なStandalone Mashed Potato項目が見つかりません')
            
        # 直接検索との比較
        print('\n=== 直接検索との比較 ===')
        direct_results = await usda_service.search_foods_rich(
            query='Potatoes, mashed, prepared',
            page_size=10,
            data_types=['Foundation', 'SR Legacy', 'FNDDS', 'Branded'],
            require_all_words=True
        )
        
        print(f'直接検索結果: {len(direct_results)} 件')
        direct_sr_legacy = [r for r in direct_results if r.data_type == "SR Legacy"]
        print(f'直接検索SR Legacy: {len(direct_sr_legacy)}')
        
        if direct_sr_legacy:
            print('直接検索で見つかったSR Legacy項目:')
            for item in direct_sr_legacy[:3]:
                print(f'   - FDC {item.fdc_id}: {item.description}')
                
        # 階層検索で除外された理由を推測
        missing_sr_items = [item for item in direct_sr_legacy if item.fdc_id not in [r.fdc_id for r in tiered_results]]
        if missing_sr_items:
            print(f'\n⚠️  階層検索で除外されたSR Legacy項目: {len(missing_sr_items)}')
            for item in missing_sr_items[:3]:
                print(f'   - FDC {item.fdc_id}: {item.description}')
    
    except Exception as e:
        print(f'エラー: {e}')

if __name__ == "__main__":
    asyncio.run(debug_mashed_potatoes_tiered_search()) 