"""
非同期処理のためのCloud Tasks統合
長時間実行されるVLM分析を非同期化
"""

import os
import json
import uuid
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from google.cloud import tasks_v2
from google.cloud import firestore
from google.cloud import storage

logger = logging.getLogger(__name__)


class AsyncMealAnalyzer:
    """Cloud Tasksを使用した非同期分析処理"""

    def __init__(self):
        self.project = os.getenv("GOOGLE_CLOUD_PROJECT", "new-snap-calorie")
        self.location = os.getenv("CLOUD_TASKS_LOCATION", "us-central1")
        self.queue = os.getenv("CLOUD_TASKS_QUEUE", "meal-analysis-queue")
        self.worker_url = os.getenv("WORKER_URL", "https://worker-meal-analysis.run.app")

        # Cloud Tasksクライアント
        self.tasks_client = tasks_v2.CloudTasksAsyncClient()
        self.parent = self.tasks_client.queue_path(
            self.project, self.location, self.queue
        )

        # Firestoreクライアント
        self.firestore_client = firestore.AsyncClient(project=self.project)
        self.tasks_collection = self.firestore_client.collection("meal_analysis_tasks")

        # Cloud Storageクライアント
        self.storage_client = storage.Client(project=self.project)
        self.bucket_name = os.getenv("IMAGE_BUCKET", "meal-analysis-images")
        self.bucket = self.storage_client.bucket(self.bucket_name)

    async def submit_analysis(
        self,
        image_data: bytes,
        model_id: str = "openrouter:qwen/qwen3-vl-235b-a22b-thinking",
        user_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析タスクをCloud Tasksにサブミット

        Returns:
            タスクIDとステータスURL
        """
        task_id = str(uuid.uuid4())

        try:
            # 1. 画像をCloud Storageにアップロード
            image_url = await self._upload_image(task_id, image_data)

            # 2. Firestoreに初期状態を保存
            task_data = {
                "task_id": task_id,
                "status": "pending",
                "progress": 0,
                "model_id": model_id,
                "user_context": user_context,
                "image_url": image_url,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=24)
            }

            await self.tasks_collection.document(task_id).set(task_data)

            # 3. Cloud Taskを作成
            task = {
                "http_request": {
                    "http_method": tasks_v2.HttpMethod.POST,
                    "url": f"{self.worker_url}/process",
                    "headers": {
                        "Content-Type": "application/json",
                        "X-Task-ID": task_id
                    },
                    "body": json.dumps({
                        "task_id": task_id,
                        "image_url": image_url,
                        "model_id": model_id,
                        "user_context": user_context
                    }).encode()
                }
            }

            # タスクをキューに送信
            response = await self.tasks_client.create_task(
                request={
                    "parent": self.parent,
                    "task": task
                }
            )

            logger.info(f"Task created: {task_id}")

            return {
                "task_id": task_id,
                "status": "pending",
                "status_url": f"/api/v1/tasks/{task_id}",
                "estimated_completion_time": 180  # 秒
            }

        except Exception as e:
            logger.error(f"Failed to submit analysis task: {e}")
            raise

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """タスクのステータスを取得"""
        try:
            doc = await self.tasks_collection.document(task_id).get()

            if not doc.exists:
                return {
                    "error": "Task not found",
                    "status": "not_found"
                }

            task_data = doc.to_dict()

            # 有効期限チェック
            if task_data.get("expires_at") < datetime.utcnow():
                return {
                    "status": "expired",
                    "error": "Task has expired"
                }

            # ステータスに応じたレスポンス
            if task_data["status"] == "completed":
                return {
                    "status": "completed",
                    "result": task_data.get("result"),
                    "completed_at": task_data.get("completed_at")
                }
            elif task_data["status"] == "failed":
                return {
                    "status": "failed",
                    "error": task_data.get("error_message", "Analysis failed"),
                    "failed_at": task_data.get("failed_at")
                }
            else:
                # processing or pending
                return {
                    "status": task_data["status"],
                    "progress": task_data.get("progress", 0),
                    "message": self._get_progress_message(task_data.get("progress", 0))
                }

        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            return {
                "status": "error",
                "error": "Failed to retrieve task status"
            }

    async def update_task_result(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """ワーカーからタスク結果を更新"""
        try:
            update_data = {
                "updated_at": datetime.utcnow()
            }

            if result:
                update_data.update({
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.utcnow(),
                    "progress": 100
                })
            elif error:
                update_data.update({
                    "status": "failed",
                    "error_message": error,
                    "failed_at": datetime.utcnow()
                })

            await self.tasks_collection.document(task_id).update(update_data)

        except Exception as e:
            logger.error(f"Failed to update task result: {e}")
            raise

    async def _upload_image(self, task_id: str, image_data: bytes) -> str:
        """画像をCloud Storageにアップロード"""
        blob_name = f"tasks/{task_id}/image.jpg"
        blob = self.bucket.blob(blob_name)

        # 非同期アップロード
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, blob.upload_from_string, image_data)

        # 署名付きURLを生成（24時間有効）
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=24),
            method="GET"
        )

        return url

    def _get_progress_message(self, progress: int) -> str:
        """進捗に応じたメッセージ生成"""
        if progress < 10:
            return "タスクがキューに追加されました"
        elif progress < 30:
            return "画像を分析中..."
        elif progress < 60:
            return "VLMで食品を識別中..."
        elif progress < 80:
            return "栄養情報を検索中..."
        elif progress < 100:
            return "結果を整形中..."
        else:
            return "完了しました"


class TaskWorker:
    """Cloud Tasksワーカー（別インスタンスで実行）"""

    def __init__(self):
        self.analyzer = AsyncMealAnalyzer()

    async def process_task(self, task_data: Dict[str, Any]):
        """タスクを処理"""
        task_id = task_data["task_id"]

        try:
            # 進捗更新: 開始
            await self._update_progress(task_id, 10, "processing")

            # 画像をダウンロード
            image_data = await self._download_image(task_data["image_url"])
            await self._update_progress(task_id, 30)

            # VLM分析実行
            from services.meal_analyzer import MealAnalyzer
            meal_analyzer = MealAnalyzer()

            result = await meal_analyzer.analyze_image(
                image_data,
                model_id=task_data["model_id"],
                user_context=task_data.get("user_context")
            )

            await self._update_progress(task_id, 90)

            # 結果を保存
            await self.analyzer.update_task_result(task_id, result=result)

        except Exception as e:
            logger.error(f"Task processing failed: {e}")
            await self.analyzer.update_task_result(task_id, error=str(e))

    async def _update_progress(
        self,
        task_id: str,
        progress: int,
        status: str = None
    ):
        """進捗を更新"""
        update_data = {
            "progress": progress,
            "updated_at": datetime.utcnow()
        }

        if status:
            update_data["status"] = status

        await self.analyzer.tasks_collection.document(task_id).update(update_data)

    async def _download_image(self, image_url: str) -> bytes:
        """Cloud Storageから画像をダウンロード"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                return await response.read()