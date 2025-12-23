#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Startup Data Loader for Cloud Run

Cloud Storageから起動時にFAISSデータをダウンロードする
"""

import logging
import asyncio
from pathlib import Path
from google.cloud import storage

logger = logging.getLogger(__name__)


class DataLoader:
    """Cloud StorageからFAISSデータをダウンロード"""

    def __init__(
        self,
        bucket_name: str = "new-snap-calorie-faiss-data",
        gcs_prefix: str = "faiss/",
        local_dir: str = "/tmp/faiss"
    ):
        """
        Args:
            bucket_name: Cloud Storageバケット名
            gcs_prefix: バケット内のプレフィックス
            local_dir: ローカルダウンロード先
        """
        self.bucket_name = bucket_name
        self.gcs_prefix = gcs_prefix
        self.local_dir = Path(local_dir)

    async def download_if_needed(self) -> Path:
        """
        必要な場合のみダウンロード（既に存在する場合はスキップ）

        Returns:
            ダウンロード先ディレクトリパス
        """
        # 既にダウンロード済みかチェック
        marker_file = self.local_dir / ".downloaded"
        if marker_file.exists():
            logger.info(f"✅ FAISS data already exists in {self.local_dir}")
            return self.local_dir

        logger.info(f"📥 Downloading FAISS data from gs://{self.bucket_name}/{self.gcs_prefix}")

        try:
            # ディレクトリ作成
            self.local_dir.mkdir(parents=True, exist_ok=True)

            # Cloud Storageクライアント初期化
            client = storage.Client()
            bucket = client.bucket(self.bucket_name)

            # ファイル一覧取得
            blobs = list(bucket.list_blobs(prefix=self.gcs_prefix))
            logger.info(f"📦 Found {len(blobs)} files to download")

            # 並列ダウンロード（最大10並列）
            semaphore = asyncio.Semaphore(10)
            tasks = []

            for blob in blobs:
                if blob.name.endswith('/'):  # ディレクトリはスキップ
                    continue
                task = self._download_blob(blob, semaphore)
                tasks.append(task)

            # 全ファイルダウンロード待機
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # エラーチェック
            errors = [r for r in results if isinstance(r, Exception)]
            if errors:
                logger.error(f"❌ {len(errors)} download errors occurred")
                for error in errors[:5]:  # 最初の5件のみログ
                    logger.error(f"  - {error}")
                raise RuntimeError(f"Download failed with {len(errors)} errors")

            # 完了マーカー作成
            marker_file.write_text("downloaded")

            # ダウンロード統計
            total_size = sum(r for r in results if isinstance(r, int))
            logger.info(f"✅ Successfully downloaded {len(tasks)} files ({total_size / 1024 / 1024:.1f} MB)")

            return self.local_dir

        except Exception as e:
            logger.error(f"❌ Failed to download FAISS data: {e}", exc_info=True)
            raise

    async def _download_blob(self, blob: storage.Blob, semaphore: asyncio.Semaphore) -> int:
        """
        単一ファイルをダウンロード（並列制御付き）

        Args:
            blob: Cloud Storage Blob
            semaphore: 並列制御用セマフォ

        Returns:
            ダウンロードしたファイルサイズ（bytes）
        """
        async with semaphore:
            # GCSパス内のprefixを除去してローカルパスを決定
            relative_path = blob.name.replace(self.gcs_prefix, "", 1)
            local_path = self.local_dir / relative_path

            # 親ディレクトリ作成
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # ダウンロード（同期関数を非同期で実行）
            await asyncio.to_thread(
                blob.download_to_filename,
                str(local_path)
            )

            file_size = local_path.stat().st_size
            logger.debug(f"  ✓ {relative_path} ({file_size / 1024:.1f} KB)")

            return file_size


async def load_faiss_data(
    bucket_name: str = "new-snap-calorie-faiss-data",
    gcs_prefix: str = "faiss/",
    local_dir: str = "/tmp/faiss"
) -> Path:
    """
    FAISS データをCloud Storageからロード

    Args:
        bucket_name: Cloud Storageバケット名
        gcs_prefix: バケット内のプレフィックス
        local_dir: ローカルダウンロード先

    Returns:
        ダウンロード先ディレクトリパス
    """
    loader = DataLoader(
        bucket_name=bucket_name,
        gcs_prefix=gcs_prefix,
        local_dir=local_dir
    )

    return await loader.download_if_needed()


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    async def test():
        result = await load_faiss_data()
        print(f"✅ Data loaded to: {result}")

    asyncio.run(test())
