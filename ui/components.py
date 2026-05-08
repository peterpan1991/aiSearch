"""
UI组件模块
"""
import flet as ft
from pathlib import Path
from typing import Callable, List
from ui.constants import COLORS

class SearchModeSelector(ft.Container):
    """搜索模式选择器"""

    def __init__(self, on_mode_change: Callable = None):
        super().__init__()
        self.on_mode_change_callback = on_mode_change
        self.current_mode = "semantic"

        self.ocr_button = ft.Button(
            content=ft.Row([
                ft.Icon(ft.Icons.ABC, size=16),
                ft.Text("文字搜索", size=12),
            ], spacing=5),
            on_click=lambda e: self._select_mode("ocr"),
            style=ft.ButtonStyle(
                bgcolor=COLORS['text_light'],
                color="#FFFFFF",
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )

        self.semantic_button = ft.Button(
            content=ft.Row([
                ft.Icon(ft.Icons.PSYCHOLOGY_ALT, size=16),
                ft.Text("语义搜索", size=12),
            ], spacing=5),
            on_click=lambda e: self._select_mode("semantic"),
            style=ft.ButtonStyle(
                bgcolor=COLORS['accent'],
                color="#FFFFFF",
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )

        self.content = ft.Row([
            ft.Text("搜索模式:", size=13, weight=ft.FontWeight.W_400),
            self.semantic_button,
            self.ocr_button,            
        ], spacing=10)

    def _select_mode(self, mode: str):
        """选择搜索模式"""
        if self.current_mode == mode:
            return

        self.current_mode = mode

        if mode == "ocr":
            self.ocr_button.style.bgcolor = COLORS['accent']
            self.semantic_button.style.bgcolor = COLORS['text_light']
        else:
            self.ocr_button.style.bgcolor = COLORS['text_light']
            self.semantic_button.style.bgcolor = COLORS['accent']

        self.ocr_button.update()
        self.semantic_button.update()

        if self.on_mode_change_callback:
            self.on_mode_change_callback(mode)

    def get_mode(self) -> str:
        """获取当前模式"""
        return self.current_mode


class SearchBar(ft.Container):
    """搜索栏组件"""

    def __init__(self, on_search: Callable[[str], None], on_build_index: Callable = None):
        super().__init__()
        self.on_search_callback = on_search
        self.on_build_index_callback = on_build_index

        self.search_field = ft.TextField(
            hint_text="输入关键字搜索图片...",
            expand=True,
            border_color=COLORS['border'],
            focused_border_color=COLORS['accent'],
            on_submit=self._handle_search,
        )

        self.search_button = ft.Button(
            icon=ft.Icons.SEARCH,
            content="搜索",
            on_click=self._handle_search,
            style=ft.ButtonStyle(
                bgcolor=COLORS['success'],
                color="#FFFFFF",
                padding=15,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )

        self.index_button = ft.Button(
            icon=ft.Icons.BUILD,
            content="建立索引",
            on_click=self._handle_build_index,
            style=ft.ButtonStyle(
                bgcolor=COLORS['accent'],
                color="#FFFFFF",
                padding=15,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )

        self.content = ft.Row(
            controls=[
                self.search_field,
                self.index_button,
                self.search_button,
            ],
            spacing=10,
        )

    def set_enabled(self, enabled: bool):
        """设置搜索按钮启用/禁用状态"""
        self.search_button.disabled = not enabled
        self.search_button.update()

    def set_index_button_enabled(self, enabled: bool):
        """设置建立索引按钮启用/禁用状态"""
        self.index_button.disabled = not enabled
        self.index_button.update()

    def _handle_search(self):
        """处理搜索"""
        keyword = self.search_field.value
        self.on_search_callback(keyword)

    def _handle_build_index(self):
        """处理建立索引"""
        if self.on_build_index_callback:
            self.on_build_index_callback()


class FolderSelector(ft.Container):
    """文件夹选择器组件"""

    def __init__(self, on_folder_selected: Callable[[str], None]):
        super().__init__()
        self.on_folder_selected_callback = on_folder_selected
        self.folder_path_value = ""

        self.test_field = ft.TextField(
            read_only=True,
            expand=True,
            prefix_icon="folder",
            hint_text="点击右侧按钮选择文件夹",
            border_color=COLORS['border'],
            focused_border_color=COLORS['accent'],
        )

        self.button = ft.IconButton(
            on_click=self._select_folder,
            icon=ft.Icons.DRIVE_FOLDER_UPLOAD,
            selected_icon=ft.Icons.DRIVE_FOLDER_UPLOAD_ROUNDED,
            tooltip="浏览文件夹",
        )

        self.content = ft.Row([
            self.test_field,
            self.button,
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    async def _select_folder(self):
        path = await ft.FilePicker().get_directory_path()
        if path:
            self.folder_path_value = path
            self.test_field.value = path
            self.on_folder_selected_callback(path)

    def set_status(self, status: str):
        """设置状态信息"""
        self.status_label.value = status
        self.update()

class ResultGrid(ft.Container):
    """结果网格组件"""

    def __init__(self, on_item_click=None):
        super().__init__()
        self.results: List = []
        self.on_item_click_callback = on_item_click
        self.expand = True
        self.width = None
        self.grid_view = ft.GridView(
            expand=True,
            runs_count=6,
            spacing=8,
        )

        self.empty_placeholder = ft.Container(
            content=ft.Column([
                ft.Text("结果将显示在这里", size=14, color=ft.Colors.GREY),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
            alignment=ft.Alignment.CENTER,
        )

        self.content = self.empty_placeholder if not self.results else self.grid_view

    def set_results(self, results: List):
        """设置搜索结果"""
        self.results = results
        if not results:
            self.empty_placeholder = ft.Container(
                content=ft.Column([
                    ft.Text("没有找到匹配的结果", size=14, color=ft.Colors.GREY),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
                alignment=ft.Alignment.CENTER
            )
            self.content = self.empty_placeholder
        else:
            self.grid_view.controls = [self._create_result_item(r) for r in results]
            self.content = ft.Container(content=self.grid_view, expand=True)
        self.update()

    def _create_result_item(self, file_item):
        """创建结果项"""
        def handle_click(e):
            if self.on_item_click_callback:
                self.on_item_click_callback(file_item)

        container = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Image(
                        src=file_item.path,
                        fit=ft.BoxFit.COVER,
                    ),
                    height=170,
                    border_radius=5,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                ),                
                ft.Text(
                    f"相似度: {file_item.similarity:.2%}" if file_item.similarity else "",
                    size=9,
                    color=ft.Colors.GREY_600,
                ),
                ft.Text(
                    Path(file_item.path).name,
                    size=10,
                    tooltip=file_item.path,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    max_lines=1,
                ),
            ], spacing=2),
            width=180,
            height=220,
            border_radius=8,
            bgcolor=COLORS['bg_primary'],
            padding=5,
            on_click=handle_click,
        )
        return container


class StatusBar(ft.Container):
    """状态栏组件"""

    def __init__(self):
        super().__init__()
        self.status_text = ft.Text("就绪", size=12, color=ft.Colors.GREY)
        self.progress_bar = ft.ProgressBar(visible=False, color=COLORS['success'])
        self.content = ft.Column(
            controls=[
                self.status_text,
                self.progress_bar
            ],
        )

    def set_status(self, message: str):
        """设置状态消息"""
        self.status_text.value = message
        self.status_text.update()

    def show_progress(self, visible: bool = True):
        """显示或隐藏加载条"""
        self.progress_bar.visible = visible
        self.progress_bar.update()
