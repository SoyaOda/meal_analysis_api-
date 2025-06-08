#!/usr/bin/env python3
"""
依存関係追跡スクリプト (改良版)

test_local_nutrition_search_v2.pyが実際に使用する全ファイルを網羅的に特定します：
1. 静的解析：import文の解析
2. 動的追跡：実行時に読み込まれるファイル
3. APIテスト場合：対応するサーバー側依存関係も追跡
"""

import ast
import os
import sys
import json
import importlib.util
from pathlib import Path
from typing import Set, List, Dict, Any

class DependencyTracer:
    def __init__(self, root_file: str, project_root: str = "."):
        self.root_file = root_file
        self.project_root = Path(project_root).resolve()
        self.traced_files: Set[Path] = set()
        self.data_files: Set[Path] = set()
        self.config_files: Set[Path] = set()
        self.import_errors: List[str] = []
        self.server_files: Set[Path] = set()  # サーバー側ファイル
        
    def trace_all_dependencies(self) -> Dict[str, List[str]]:
        """全ての依存関係を追跡"""
        print(f"🔍 Tracing dependencies for: {self.root_file}")
        print(f"📁 Project root: {self.project_root}")
        print("-" * 60)
        
        # メインファイルから開始
        root_path = Path(self.root_file).resolve()
        self._trace_python_file(root_path)
        
        # APIテストファイルの場合、サーバー側の依存関係も追跡
        if self._is_api_test_file(root_path):
            print("🌐 Detected API test file - tracing server dependencies...")
            self._trace_server_dependencies()
        
        # 結果を分類
        project_files = []
        server_files = []
        external_files = []
        missing_files = []
        
        for file_path in self.traced_files:
            if file_path.exists():
                if self._is_in_project(file_path):
                    project_files.append(str(file_path.relative_to(self.project_root)))
                else:
                    external_files.append(str(file_path))
            else:
                missing_files.append(str(file_path))
        
        # サーバーファイルを追加
        for file_path in self.server_files:
            if file_path.exists():
                server_files.append(str(file_path.relative_to(self.project_root)))
            else:
                missing_files.append(str(file_path))
        
        return {
            "project_python_files": sorted(project_files),
            "server_files": sorted(server_files),
            "data_files": sorted([str(f.relative_to(self.project_root)) for f in self.data_files if f.exists()]),
            "config_files": sorted([str(f.relative_to(self.project_root)) for f in self.config_files if f.exists()]),
            "external_files": sorted(external_files),
            "missing_files": sorted(missing_files),
            "import_errors": self.import_errors
        }
    
    def _is_api_test_file(self, file_path: Path) -> bool:
        """ファイルがAPIテストファイルかどうかチェック"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # APIテストの特徴を検出
            return ('requests.' in content and 
                    'BASE_URL' in content and 
                    ('localhost' in content or 'api/v1' in content))
        except:
            return False
    
    def _trace_server_dependencies(self):
        """サーバー側の依存関係を追跡"""
        # app_v2のメインアプリケーションファイルを追跡
        app_paths = [
            self.project_root / "app_v2" / "main" / "app.py",
            self.project_root / "app_v2" / "api" / "routes.py", 
            self.project_root / "app_v2" / "api" / "meal_analysis.py",
            self.project_root / "app_v2" / "pipeline" / "orchestrator.py",
            self.project_root / "app_v2" / "components" / "local_nutrition_search.py",
            self.project_root / "app_v2" / "config" / "settings.py"
        ]
        
        # 実際に存在するファイルのみ追跡
        for app_file in app_paths:
            if app_file.exists():
                self._trace_server_file(app_file)
        
        # app_v2ディレクトリ全体を走査
        app_v2_dir = self.project_root / "app_v2"
        if app_v2_dir.exists():
            for py_file in app_v2_dir.rglob("*.py"):
                if py_file.name != "__pycache__":
                    self._trace_server_file(py_file)
        
        # nutrition_db_experimentのデータファイルを追跡
        self._trace_nutrition_db_data()
    
    def _trace_nutrition_db_data(self):
        """nutrition_db_experimentのデータファイルを追跡"""
        nutrition_db_dir = self.project_root / "nutrition_db_experiment"
        if nutrition_db_dir.exists():
            print("🗃️ Tracing nutrition_db_experiment files...")
            
            # データベースファイルは膨大なので除外
            # db_files = [
            #     "nutrition_db/dish_db.json",
            #     "nutrition_db/ingredient_db.json",
            #     "nutrition_db/branded_db.json",
            #     "nutrition_db/unified_nutrition_db.json"
            # ]
            # 
            # for db_file in db_files:
            #     db_path = nutrition_db_dir / db_file
            #     if db_path.exists():
            #         self.data_files.add(db_path)
            #         print(f"🗂️ Data file: {db_path.relative_to(self.project_root)}")
            
            # Pythonモジュールファイル（検索システム）
            search_service_dir = nutrition_db_dir / "search_service"
            if search_service_dir.exists():
                for py_file in search_service_dir.rglob("*.py"):
                    if py_file.name != "__pycache__":
                        self._trace_server_file(py_file)
            
            # 設定ファイル
            config_files = [
                "config.py",
                "settings.json",
                "nutrition_database_specification.md"
            ]
            
            for config_file in config_files:
                config_path = nutrition_db_dir / config_file
                if config_path.exists():
                    self.config_files.add(config_path)
                    print(f"⚙️ Config file: {config_path.relative_to(self.project_root)}")
    
    def _trace_server_file(self, file_path: Path):
        """サーバーファイルを追跡し、その依存関係も解析"""
        if file_path in self.server_files or file_path in self.traced_files:
            return
            
        self.server_files.add(file_path)
        print(f"🌐 Server file: {file_path.relative_to(self.project_root)}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # AST解析でimport文を抽出
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._resolve_server_import(alias.name, file_path)
                        
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._resolve_server_import(node.module, file_path, node.level)
                
                # ファイル読み込み操作を検出
                elif isinstance(node, ast.Call):
                    self._detect_file_operations(node, file_path)
                    
        except Exception as e:
            error_msg = f"Error parsing server file {file_path}: {str(e)}"
            print(f"❌ {error_msg}")
            self.import_errors.append(error_msg)
    
    def _resolve_server_import(self, module_name: str, current_file: Path, level: int = 0):
        """サーバーファイルのimport文を解決"""
        try:
            if level > 0:  # 相対import
                current_dir = current_file.parent
                for _ in range(level - 1):
                    current_dir = current_dir.parent
                
                if module_name:
                    module_path = current_dir / module_name.replace('.', '/')
                else:
                    module_path = current_dir
            else:  # 絶対import
                # app_v2内のimportを優先
                if module_name.startswith('app_v2.'):
                    module_path = self.project_root / module_name.replace('.', '/')
                else:
                    module_path = self.project_root / module_name.replace('.', '/')
                
                # 外部ライブラリの場合はスキップ
                if not self._is_project_module(module_path):
                    return
            
            # Pythonファイルとして解決を試行
            possible_files = [
                module_path.with_suffix('.py'),
                module_path / '__init__.py'
            ]
            
            for py_file in possible_files:
                if py_file.exists() and self._is_in_project(py_file):
                    self._trace_server_file(py_file)
                    break
                    
        except Exception as e:
            error_msg = f"Error resolving server import '{module_name}': {str(e)}"
            self.import_errors.append(error_msg)
    
    def _trace_python_file(self, file_path: Path) -> None:
        """Pythonファイルの依存関係を追跡"""
        if file_path in self.traced_files:
            return
            
        if not file_path.exists():
            print(f"❌ Missing: {file_path}")
            return
            
        self.traced_files.add(file_path)
        print(f"📄 Tracing: {file_path.relative_to(self.project_root) if self._is_in_project(file_path) else file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # AST解析でimport文を抽出
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._resolve_import(alias.name, file_path)
                        
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._resolve_import(node.module, file_path, node.level)
                    
                # ファイル読み込み操作を検出
                elif isinstance(node, ast.Call):
                    self._detect_file_operations(node, file_path)
                    
        except Exception as e:
            error_msg = f"Error parsing {file_path}: {str(e)}"
            print(f"❌ {error_msg}")
            self.import_errors.append(error_msg)
    
    def _resolve_import(self, module_name: str, current_file: Path, level: int = 0) -> None:
        """import文からファイルパスを解決"""
        try:
            if level > 0:  # 相対import
                # 相対importの解決
                current_dir = current_file.parent
                for _ in range(level - 1):
                    current_dir = current_dir.parent
                
                if module_name:
                    module_path = current_dir / module_name.replace('.', '/')
                else:
                    module_path = current_dir
            else:  # 絶対import
                # プロジェクト内のモジュールを優先
                module_path = self.project_root / module_name.replace('.', '/')
                
                # 標準ライブラリやサードパーティの場合
                if not self._is_project_module(module_path):
                    try:
                        spec = importlib.util.find_spec(module_name)
                        if spec and spec.origin and spec.origin != 'built-in':
                            external_path = Path(spec.origin)
                            if external_path.exists():
                                self.traced_files.add(external_path)
                    except (ImportError, ModuleNotFoundError):
                        pass
                    return
            
            # Pythonファイルとして解決を試行
            possible_files = [
                module_path.with_suffix('.py'),
                module_path / '__init__.py'
            ]
            
            for py_file in possible_files:
                if py_file.exists() and self._is_in_project(py_file):
                    self._trace_python_file(py_file)
                    break
                    
        except Exception as e:
            error_msg = f"Error resolving import '{module_name}': {str(e)}"
            self.import_errors.append(error_msg)
    
    def _detect_file_operations(self, node: ast.Call, current_file: Path) -> None:
        """ファイル操作（open, json.load等）を検出"""
        try:
            # open() 呼び出し
            if (isinstance(node.func, ast.Name) and node.func.id == 'open') or \
               (isinstance(node.func, ast.Attribute) and node.func.attr == 'open'):
                if node.args and isinstance(node.args[0], ast.Constant):
                    file_path = self._resolve_file_path(node.args[0].value, current_file)
                    if file_path:
                        self.data_files.add(file_path)
            
            # json.load, yaml.load等の検出
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in ['load', 'loads', 'read_text', 'read_bytes']:
                    # 前の引数を確認（ファイルパスの可能性）
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            file_path = self._resolve_file_path(arg.value, current_file)
                            if file_path:
                                self.data_files.add(file_path)
                                
        except Exception:
            pass  # ファイル操作の検出エラーは無視
    
    def _resolve_file_path(self, path_str: str, current_file: Path) -> Path:
        """文字列パスを絶対パスに解決"""
        path = Path(path_str)
        
        if path.is_absolute():
            return path
        else:
            # 相対パス - 現在のファイルからの相対またはプロジェクトルートからの相対
            candidates = [
                current_file.parent / path,
                self.project_root / path
            ]
            
            for candidate in candidates:
                if candidate.exists():
                    return candidate.resolve()
                    
            # 存在しなくても追跡対象として返す
            return (current_file.parent / path).resolve()
    
    def _is_in_project(self, file_path: Path) -> bool:
        """ファイルがプロジェクト内にあるかチェック"""
        try:
            file_path.relative_to(self.project_root)
            return True
        except ValueError:
            return False
    
    def _is_project_module(self, module_path: Path) -> bool:
        """モジュールがプロジェクト内のモジュールかチェック"""
        return module_path.exists() or (module_path.parent.exists() and 
                                        any(module_path.parent.glob(f"{module_path.name}.*")))

def create_enhanced_architecture_analyzer(dependencies: Dict[str, List[str]]) -> str:
    """依存関係追跡結果を基に改良されたアーキテクチャ分析スクリプトを生成"""
    
    script_content = '''#!/usr/bin/env python3
"""
ローカル栄養データベース検索システム アーキテクチャ分析 (依存関係追跡版)

実際にtest_local_nutrition_search_v2.pyから追跡された依存関係に基づいて
正確なファイル分析を実行します。
"""

import os
import datetime
from pathlib import Path
from typing import Dict, List

def get_file_content(file_path: str) -> str:
    """ファイル内容を安全に読み取る"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"ERROR: ファイルを読み取れませんでした: {str(e)}"

def analyze_traced_dependencies():
    """追跡された依存関係に基づくアーキテクチャ分析"""
    
    # 実際に追跡された依存関係
    traced_dependencies = ''' + repr(dependencies) + '''
    
    # ファイルを機能別に分類
    files_to_analyze = {
        "🎯 実行起点ファイル": [
            "test_local_nutrition_search_v2.py"
        ],
        "🏗️ プロジェクト内Pythonファイル": traced_dependencies["project_python_files"],
        "🌐 サーバー側ファイル": traced_dependencies["server_files"],
        "⚙️ 設定ファイル": traced_dependencies["config_files"]
    }
    
    # 出力ファイル名（タイムスタンプ付き）
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"traced_nutrition_architecture_{timestamp}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        # ヘッダー情報
        out_f.write("=" * 80 + "\\n")
        out_f.write("MEAL ANALYSIS API v2.0 - 依存関係追跡版アーキテクチャ分析\\n")
        out_f.write("=" * 80 + "\\n")
        out_f.write(f"生成日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
        out_f.write(f"追跡起点: test_local_nutrition_search_v2.py\\n")
        out_f.write(f"総追跡ファイル数: {len(traced_dependencies['project_python_files']) + len(traced_dependencies['server_files']) + len(traced_dependencies['config_files'])}\\n")
        out_f.write("=" * 80 + "\\n\\n")
        
        # 依存関係概要
        out_f.write("📊 DEPENDENCY TRACE SUMMARY\\n")
        out_f.write("-" * 40 + "\\n")
        out_f.write(f"✅ Project Python Files: {len(traced_dependencies['project_python_files'])}\\n")
        out_f.write(f"🌐 Server Files: {len(traced_dependencies['server_files'])}\\n")
        out_f.write(f"⚙️ Config Files: {len(traced_dependencies['config_files'])}\\n")
        out_f.write(f"🗃️ Data Files (excluded): {len(traced_dependencies['data_files'])}\\n")
        out_f.write(f"🌍 External Files: {len(traced_dependencies['external_files'])}\\n")
        out_f.write(f"❌ Missing Files: {len(traced_dependencies['missing_files'])}\\n")
        if traced_dependencies['import_errors']:
            out_f.write(f"⚠️ Import Errors: {len(traced_dependencies['import_errors'])}\\n")
        out_f.write("\\n")
        
        # エラーと欠損ファイルの報告
        if traced_dependencies['missing_files']:
            out_f.write("❌ MISSING FILES\\n")
            out_f.write("-" * 20 + "\\n")
            for missing in traced_dependencies['missing_files']:
                out_f.write(f"- {missing}\\n")
            out_f.write("\\n")
        
        if traced_dependencies['import_errors']:
            out_f.write("⚠️ IMPORT ERRORS\\n")
            out_f.write("-" * 20 + "\\n")
            for error in traced_dependencies['import_errors']:
                out_f.write(f"- {error}\\n")
            out_f.write("\\n")
        
        # 各カテゴリーのファイル分析
        for category, file_list in files_to_analyze.items():
            if not file_list:
                continue
                
            out_f.write(f"{category}\\n")
            out_f.write("=" * 60 + "\\n\\n")
            
            for file_path in file_list:
                out_f.write(f"📄 FILE: {file_path}\\n")
                out_f.write("-" * 50 + "\\n")
                
                if os.path.exists(file_path):
                    # ファイル情報
                    file_stat = os.stat(file_path)
                    file_size = file_stat.st_size
                    mod_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
                    
                    out_f.write(f"ファイルサイズ: {file_size:,} bytes\\n")
                    out_f.write(f"最終更新: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
                    out_f.write(f"存在: ✅\\n\\n")
                    
                    # ファイル内容（データファイルの場合は制限）
                    if file_path.endswith('.json') and file_size > 1024*1024:  # 1MB以上のJSONは概要のみ
                        out_f.write("CONTENT: (Large JSON file - showing structure only)\\n")
                        try:
                            import json
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                            if isinstance(data, list):
                                out_f.write(f"Array with {len(data)} items\\n")
                                if data:
                                    out_f.write(f"Sample item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Non-dict items'}\\n")
                            elif isinstance(data, dict):
                                out_f.write(f"Object with keys: {list(data.keys())}\\n")
                        except:
                            out_f.write("Could not parse JSON structure\\n")
                    else:
                        out_f.write("CONTENT:\\n")
                        out_f.write("```\\n")
                        content = get_file_content(file_path)
                        out_f.write(content)
                        out_f.write("\\n```\\n")
                    out_f.write("\\n")
                else:
                    out_f.write("存在: ❌ ファイルが見つかりません\\n\\n")
                
                out_f.write("=" * 60 + "\\n\\n")
        
        # 統計情報
        out_f.write("📊 ANALYSIS STATISTICS\\n")
        out_f.write("-" * 40 + "\\n")
        total_files = sum(len(files) for files in files_to_analyze.values() if files)
        existing_files = sum(1 for files in files_to_analyze.values() if files for f in files if os.path.exists(f))
        
        out_f.write(f"総ファイル数: {total_files}\\n")
        out_f.write(f"存在ファイル数: {existing_files}\\n")
        out_f.write(f"分析完了時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
        out_f.write("\\nこのファイルには、test_local_nutrition_search_v2.py実行時に\\n")
        out_f.write("実際に使用される全ファイルの内容が含まれています。\\n")
        
    return output_file, total_files, existing_files

def main():
    """メイン実行関数"""
    print("🔍 依存関係追跡版アーキテクチャ分析開始...")
    print("-" * 60)
    
    try:
        output_file, total_files, existing_files = analyze_traced_dependencies()
        
        print(f"✅ 分析完了!")
        print(f"📁 出力ファイル: {output_file}")
        print(f"📊 総ファイル数: {total_files}")
        print(f"✅ 存在ファイル数: {existing_files}")
        
        if existing_files < total_files:
            missing = total_files - existing_files
            print(f"⚠️  見つからないファイル: {missing}個")
        
        # ファイルサイズを表示
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"📄 出力ファイルサイズ: {file_size:,} bytes")
        
        print("\\n🎉 依存関係追跡版アーキテクチャ分析が完了しました!")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
'''
    
    return script_content

def main():
    """メイン実行関数"""
    if len(sys.argv) < 2:
        print("Usage: python trace_dependencies.py <target_file>")
        print("Example: python trace_dependencies.py test_local_nutrition_search_v2.py")
        sys.exit(1)
    
    target_file = sys.argv[1]
    
    if not os.path.exists(target_file):
        print(f"❌ Target file not found: {target_file}")
        sys.exit(1)
    
    # 依存関係を追跡
    tracer = DependencyTracer(target_file)
    dependencies = tracer.trace_all_dependencies()
    
    # 結果を表示
    print("\n" + "="*60)
    print("📊 DEPENDENCY TRACE RESULTS")
    print("="*60)
    
    for category, files in dependencies.items():
        if files:
            print(f"\n{category.upper()} ({len(files)}):")
            for file in files[:10]:  # 最初の10個のみ表示
                print(f"  - {file}")
            if len(files) > 10:
                print(f"  ... and {len(files) - 10} more")
    
    # 改良されたアーキテクチャ分析スクリプトを生成
    script_content = create_enhanced_architecture_analyzer(dependencies)
    
    output_script = "analyze_traced_architecture.py"
    with open(output_script, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"\n✅ Enhanced architecture analyzer created: {output_script}")
    print(f"🚀 Run it with: python {output_script}")

if __name__ == "__main__":
    main() 