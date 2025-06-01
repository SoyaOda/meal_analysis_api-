#!/usr/bin/env python3
import sys
import os
sys.path.append(os.getcwd())
from app.services.usda_service import USDAService

def test_structured_query_approach():
    usda_service = USDAService()
    
    # Test cases for structured query components
    test_cases = [
        {
            "name": "Ground Beef",
            "components": ["Beef", "ground", "cooked"],
            "original": "Ground beef"
        },
        {
            "name": "Penne Pasta", 
            "components": ["Pasta", "penne", "cooked"],
            "original": "Penne pasta"
        },
        {
            "name": "Caesar Salad",
            "components": ["Salad", "Caesar", "prepared"], 
            "original": "Caesar Salad"
        },
        {
            "name": "Mashed Potatoes",
            "components": ["Potatoes", "mashed", "prepared"],
            "original": "Mashed Potatoes"
        }
    ]
    
    print("=== Structured Query Component Testing ===\n")
    
    for test_case in test_cases:
        print(f"🔍 Testing: {test_case['name']}")
        print(f"Components: {test_case['components']}")
        print(f"Original: {test_case['original']}")
        print("-" * 50)
        
        # Generate tier queries from components
        tier_queries = usda_service.generate_tier_queries(test_case['components'])
        
        print("Generated Tier Queries:")
        for tier, query in tier_queries.items():
            print(f"  Tier {tier}: '{query}'")
        
        print()
        
        # Test parsing back to components
        tier1_query = tier_queries.get(1, "")
        parsed_components = usda_service.parse_query_components(tier1_query)
        print(f"Parsed back to components: {parsed_components}")
        
        # Verify round-trip accuracy
        rebuilt_query = usda_service.build_query_from_components(parsed_components)
        print(f"Rebuilt query: '{rebuilt_query}'")
        
        is_accurate = rebuilt_query == tier1_query
        print(f"Round-trip accuracy: {'✅ PASS' if is_accurate else '❌ FAIL'}")
        
        print("\n" + "="*70 + "\n")

    # Test legacy string vs new structured approach
    print("=== Legacy vs Structured Comparison ===\n")
    
    legacy_query = "Beef, ground, cooked"
    components = ["Beef", "ground", "cooked"]
    
    print(f"Legacy String Approach: '{legacy_query}'")
    
    # Legacy method
    tier2_legacy = usda_service._simplify_query_term(legacy_query)
    tier3_legacy = usda_service._generalize_query_term(
        type('MockCandidate', (), {'query_term': legacy_query})()
    )
    
    print(f"  Tier 2 (legacy): '{tier2_legacy}'")
    print(f"  Tier 3 (legacy): '{tier3_legacy}'")
    
    print(f"\nStructured Component Approach: {components}")
    
    # New structured method
    tier_queries_new = usda_service.generate_tier_queries(components)
    
    print(f"  Tier 1: '{tier_queries_new.get(1, '')}'")
    print(f"  Tier 2: '{tier_queries_new.get(2, '')}'") 
    print(f"  Tier 3: '{tier_queries_new.get(3, '')}'")
    
    # Compare results
    print(f"\nComparison:")
    print(f"  Tier 2 match: {'✅' if tier2_legacy == tier_queries_new.get(2, '') else '❌'}")
    print(f"  Tier 3 match: {'✅' if tier3_legacy == tier_queries_new.get(3, '') else '❌'}")

if __name__ == '__main__':
    test_structured_query_approach() 