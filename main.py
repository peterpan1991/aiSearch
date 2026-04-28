"""
主应用模块 - Flet图片搜索应用
"""
import flet as ft
import os
from ui.main_view import MainView

def main(page: ft.Page):
    """应用入口"""
    page.title = "AI图片搜索助手"
    page.window_width = 1200
    page.window_height = 800
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme_seed="#6366F1",
        font_family="Microsoft YaHei",
    )

    print('test')

    app = MainView()

    page.add(app)


if __name__ == "__main__":
    ft.run(main)
