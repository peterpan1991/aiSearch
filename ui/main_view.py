"""
UI主视图模块
"""
import flet as ft
import threading
from pathlib import Path
from ui.components import SearchBar, SearchModeSelector, FolderSelector, ResultGrid, StatusBar
from services.file_service import FileService
from services.search_service import SearchService, SearchMode
from ui.constants import COLORS

@ft.control
class MainView(ft.Container):
    """主视图容器"""

    def init(self):
        self.expand = True
        self.file_service = FileService()
        self.search_service = SearchService()

        # 初始化UI组件
        self.folder_selector = FolderSelector(on_folder_selected=self.on_folder_selected)
        self.search_mode = SearchModeSelector(on_mode_change=self.on_search_mode_change)
        self.search_bar = SearchBar(on_search=self.on_search)
        self.result_grid = ResultGrid(on_item_click=self.on_item_click)
        self.status_bar = StatusBar()

        # # 构建界面
        self.content = ft.Column([
            self.create_card(ft.Column([
                self.folder_selector,
                self.search_mode,
                self.search_bar,
            ], spacing=10), expand=False),
            self.create_card(self.result_grid),
            self.status_bar,
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
            self.search_bar.set_enabled(True)
            self.update()
            return

        self.status_bar.set_status(f"找到 {len(image_files)} 张图片，开始OCR和语义向量处理...")
        self.search_bar.set_enabled(False)
        self.update()

        # 在后台线程执行处理，避免阻塞UI
        def process_worker():
            self.search_service.process_images(image_files, self.on_process_progress)

            # 处理完成后在主线程更新UI
            def on_complete():
                self.status_bar.set_status(f"处理完成，共 {len(image_files)} 张图片")
                self.result_grid.set_results(image_files)
                self.search_bar.set_enabled(True)
                self.update()

            self.page.run_thread(on_complete)

        thread = threading.Thread(target=process_worker, daemon=True)
        thread.start()

    def on_process_progress(self, current: int, total: int, filename: str):
        """处理进度回调"""
        def update_progress():
            self.status_bar.set_status(f"正在处理: {current}/{total} - {filename}")
            self.update()

        self.page.run_thread(update_progress)

    def on_search_mode_change(self, mode: str):
        """搜索模式切换"""
        self.current_search_mode = mode
        self.status_bar.set_status(f"切换到{mode}搜索模式")
        self.update()

    def on_search(self, keyword: str):
        """搜索处理"""
        mode = self.search_mode.get_mode()
        mode_name = "文字" if mode == "ocr" else "语义"
        self.status_bar.set_status(f"{mode_name}搜索: {keyword}")
        self.update()

        # 根据模式选择搜索方法
        search_mode = SearchMode.OCR if mode == "ocr" else SearchMode.SEMANTIC
        results = self.search_service.search(keyword, mode=search_mode)

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