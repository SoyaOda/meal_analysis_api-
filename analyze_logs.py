#!/usr/bin/env python3
"""
食事分析API ログ分析ツール

使用例:
python analyze_logs.py --report                    # 基本レポート生成
python analyze_logs.py --export sessions.csv       # CSVエクスポート
python analyze_logs.py --slow --threshold 5000     # 5秒以上の遅いセッションを分析
python analyze_logs.py --errors                    # エラーパターン分析
python analyze_logs.py --days 7                    # 過去7日間のデータのみ分析
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートを追加
sys.path.append(str(Path(__file__).parent))

from app.utils.log_analyzer import create_log_analyzer

def main():
    parser = argparse.ArgumentParser(
        description="食事分析API ログ分析ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--log-dir", 
        default="logs", 
        help="ログディレクトリパス (デフォルト: logs)"
    )
    
    # 分析タイプ
    parser.add_argument(
        "--report", 
        action="store_true", 
        help="基本分析レポートを表示"
    )
    
    parser.add_argument(
        "--export", 
        metavar="FILE", 
        help="セッションデータをCSVファイルにエクスポート"
    )
    
    parser.add_argument(
        "--slow", 
        action="store_true", 
        help="遅いセッションを分析"
    )
    
    parser.add_argument(
        "--threshold", 
        type=float, 
        default=10000, 
        help="遅いセッションの閾値 (ミリ秒, デフォルト: 10000)"
    )
    
    parser.add_argument(
        "--errors", 
        action="store_true", 
        help="エラーパターンを分析"
    )
    
    # 時間フィルタ
    parser.add_argument(
        "--days", 
        type=int, 
        help="過去N日間のデータのみ分析"
    )
    
    parser.add_argument(
        "--start-date", 
        help="開始日時 (ISO形式: YYYY-MM-DD または YYYY-MM-DD HH:MM:SS)"
    )
    
    parser.add_argument(
        "--end-date", 
        help="終了日時 (ISO形式: YYYY-MM-DD または YYYY-MM-DD HH:MM:SS)"
    )
    
    args = parser.parse_args()
    
    # 最低1つのアクションが必要
    if not any([args.report, args.export, args.slow, args.errors]):
        args.report = True  # デフォルトでレポート表示
    
    try:
        analyzer = create_log_analyzer(args.log_dir)
    except ValueError as e:
        print(f"❌ エラー: {e}")
        return 1
    
    # 日付フィルタの準備
    start_date = None
    end_date = None
    
    if args.days:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        print(f"📅 過去{args.days}日間のデータを分析 ({start_date.strftime('%Y-%m-%d')} 〜 {end_date.strftime('%Y-%m-%d')})")
    
    if args.start_date:
        try:
            # YYYY-MM-DD HH:MM:SS または YYYY-MM-DD の形式を受け入れ
            if len(args.start_date) == 10:  # YYYY-MM-DD
                start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
            else:  # YYYY-MM-DD HH:MM:SS
                start_date = datetime.strptime(args.start_date, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print(f"❌ 無効な開始日時形式: {args.start_date}")
            return 1
    
    if args.end_date:
        try:
            if len(args.end_date) == 10:  # YYYY-MM-DD
                end_date = datetime.strptime(args.end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            else:  # YYYY-MM-DD HH:MM:SS
                end_date = datetime.strptime(args.end_date, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print(f"❌ 無効な終了日時形式: {args.end_date}")
            return 1
    
    # 各分析実行
    if args.report:
        print("\n" + "="*60)
        print("📊 食事分析API ログレポート")
        print("="*60)
        
        report = analyzer.generate_report(start_date, end_date)
        print(report)
    
    if args.export:
        print("\n📁 CSVエクスポート中: {args.export}")
        try:
            analyzer.export_to_csv(args.export, start_date, end_date)
            print(f"✅ エクスポート完了: {args.export}")
        except Exception as e:
            print(f"❌ エクスポートエラー: {e}")
    
    if args.slow:
        print("\n🐌 遅いセッション分析 (閾値: {args.threshold}ms)")
        slow_sessions = analyzer.find_slow_sessions(args.threshold)
        
        if not slow_sessions:
            print("✅ 遅いセッションは見つかりませんでした")
        else:
            print(f"⚠️  {len(slow_sessions)}個の遅いセッションが見つかりました:")
            
            for i, session in enumerate(slow_sessions[:10], 1):
                duration = session.get('total_duration_ms', 0)
                session_id = session.get('session_id', 'unknown')
                start_time = session.get('start_time', 'unknown')
                
                print(f"  {i}. セッション {session_id[:8]}... - {duration:.1f}ms ({start_time})")
                
                # 各フェーズの時間内訳を表示
                phase1 = session.get('phase1_duration_ms', 0)
                usda = session.get('usda_search_duration_ms', 0)
                phase2 = session.get('phase2_duration_ms', 0)
                nutrition = session.get('nutrition_calc_duration_ms', 0)
                
                print(f"     └ Phase1: {phase1:.1f}ms, USDA: {usda:.1f}ms, Phase2: {phase2:.1f}ms, 栄養計算: {nutrition:.1f}ms")
    
    if args.errors:
        print("\n🚨 エラーパターン分析")
        error_patterns = analyzer.find_error_patterns()
        
        if not error_patterns:
            print("✅ エラーは見つかりませんでした")
        else:
            print(f"⚠️  {len(error_patterns)}種類のエラーが見つかりました:")
            
            for error, session_ids in sorted(error_patterns.items(), key=lambda x: len(x[1]), reverse=True):
                count = len(session_ids)
                print(f"\n  📌 {error} ({count}回)")
                
                # 最初の5つのセッションIDを表示
                for session_id in session_ids[:5]:
                    print(f"     - セッション: {session_id}")
                
                if len(session_ids) > 5:
                    print(f"     ... および他{len(session_ids) - 5}件")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 