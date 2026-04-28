"""
UI主视图模块
"""
import flet as ft
import threading
from pathlib import Path
from ui.components import SearchBar, FolderSelector, ResultGrid, StatusBar
from services.file_service import FileService
from services.ocr_service import OCRService
from ui.constants import COLORS

@ft.control
class MainView(ft.Container):
    """主视图容器"""

    def init(self):
        self.expand = True
        self.file_service = FileService()
        self.ocr_service = OCRService()

        # 初始化UI组件
        self.folder_selector = FolderSelector(on_folder_selected=self.on_folder_selected)
        self.search_bar = SearchBar(on_search=self.on_search)
        self.result_grid = ResultGrid(on_item_click=self.on_item_click)
        self.status_bar = StatusBar()

        # # 构建界面
        self.content = ft.Column([
            self.create_card(ft.Column([
                self.folder_selector,
                self.search_bar,
                self.status_bar,
            ], spacing=10), expand=False),
            self.create_card(self.result_grid),
        ])
    
    def create_card(self, contents, expand=True):
        return ft.Container(
            content=contents,
            bgcolor=COLORS['card'],
            border_radius=12,
            padding=25,
            border=ft.Border.all(1, COLORS['border']),
            expand=expand,
        )

    def on_folder_selected(self, folder_path: str):
        """文件夹选择后的处理"""
        self.search_bar.set_enabled(False)
        self.status_bar.set_status(f"正在扫描文件夹: {folder_path}")
        self.update()

        # 扫描文件
        files = self.file_service.scan_folder(folder_path)
        image_files = [f for f in files if f.is_image()]

        if not image_files:
            self.status_bar.set_status("没有找到图片文件")
            self.update()
            return

        self.status_bar.set_status(f"找到 {len(image_files)} 张图片，开始OCR识别...")
        self.search_bar.set_enabled(False)  # 禁用搜索按钮
        self.update()

        # 在后台线程执行OCR识别，避免阻塞UI
        def ocr_worker():
            self.ocr_service.process_images(image_files, self.on_ocr_progress)

            # OCR完成后在主线程更新UI
            def on_complete():
                self.status_bar.set_status(f"OCR识别完成，共处理 {len(image_files)} 张图片")
                self.result_grid.set_results(image_files)
                self.search_bar.set_enabled(True)  # 启用搜索按钮
                self.update()

            self.page.run_thread(on_complete)

        thread = threading.Thread(target=ocr_worker, daemon=True)
        thread.start()

    def on_ocr_progress(self, current: int, total: int, file_name: str):
        """OCR进度回调"""
        # 从后台线程更新UI需要使用 thread_safe_callback
        def update_progress():
            self.status_bar.set_status(f"正在识别: {current}/{total} - {file_name}")
            self.update()

        self.page.run_thread(update_progress)

    def on_search(self, keyword: str):
        """搜索处理"""
        self.status_bar.set_status(f"搜索: {keyword}")
        self.update()

        # 执行搜索
        results = self.ocr_service.search(keyword)

        self.status_bar.set_status(f"找到 {len(results)} 个结果")
        self.result_grid.set_results(results)
        self.update()

    def on_item_click(self, file_item):
        """图片点击事件 - 显示预览"""
        self.show_image_preview(file_item)

    def show_image_preview(self, file_item):
        """显示图片预览弹窗"""
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                file_item.name,
                size=16,
                weight=ft.FontWeight.W_500,
            ),
            content=ft.Container(
                content=ft.Image(
                    src=file_item.path,
                    fit=ft.BoxFit.CONTAIN,
                ),
                width=self.page.window_width * 0.8,
                height=self.page.window_height * 0.8,
            ),
            actions=[
                ft.TextButton(
                    "关闭",
                    on_click=lambda e: self.page.pop_dialog()
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

    def show_message(self, title, message):
        """显示消息对话框"""
        dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[ft.TextButton("确定", on_click=lambda e: self.page.pop_dialog())],
            open=True,
        )
        self.page.show_dialog(dialog)