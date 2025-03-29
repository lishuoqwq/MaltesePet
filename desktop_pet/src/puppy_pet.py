"""
线条小狗桌面宠物 - 单文件版本
将所有类和功能合并到一个文件中，避免模块导入问题
"""
import os
import sys
import random
import shutil
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QWidget, QMenu, QLabel, QFileDialog, QSystemTrayIcon, QInputDialog, QMessageBox
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QMovie, QMouseEvent, QIcon, QPixmap, QPainter, QColor, QBrush


class GifManager:
    def __init__(self):
        """初始化GIF管理器"""
        # 尝试确定资源目录的位置
        if getattr(sys, 'frozen', False):
            # 如果是打包后的程序
            base_path = Path(sys._MEIPASS)
        else:
            # 如果是开发环境
            base_path = Path(__file__).parent.parent
        
        self.gif_dir = base_path / 'resources' / 'gifs'
        
        # 确保目录存在
        self.gif_dir.mkdir(parents=True, exist_ok=True)
        
        # 如果是打包后程序，需要创建用户数据目录
        if getattr(sys, 'frozen', False):
            user_data_dir = Path(os.path.expanduser("~")) / "AppData" / "Local" / "线条小狗桌面宠物"
            self.user_gif_dir = user_data_dir / "gifs"
            self.user_gif_dir.mkdir(parents=True, exist_ok=True)
            self.config_dir = user_data_dir
        else:
            self.user_gif_dir = self.gif_dir
            self.config_dir = base_path
        
        self.default_gif = None
        self.config_file = self.config_dir / "config.json"
        self.custom_order = []
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.custom_order = config.get('gif_order', [])
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                self.custom_order = []
    
    def save_config(self):
        """保存配置文件"""
        try:
            config = {
                'gif_order': self.custom_order
            }
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_gif_list(self):
        """获取所有可用的GIF动画列表"""
        gif_files = []
        
        # 获取内置GIF
        for file in self.gif_dir.glob('*.gif'):
            # 使用统一的路径格式（正斜杠）
            gif_files.append(str(file).replace('\\', '/'))
        
        # 如果用户GIF目录与内置GIF目录不同，添加用户GIF
        if self.user_gif_dir != self.gif_dir:
            for file in self.user_gif_dir.glob('*.gif'):
                # 使用统一的路径格式（正斜杠）
                gif_files.append(str(file).replace('\\', '/'))
        
        # 如果有自定义顺序，按自定义顺序排序
        if self.custom_order:
            # 确保自定义顺序中的路径也使用统一格式
            self.custom_order = [gif.replace('\\', '/') for gif in self.custom_order]
            
            # 过滤掉不存在的文件
            self.custom_order = [gif for gif in self.custom_order if gif in gif_files]
            
            # 获取未在自定义顺序中的文件
            other_gifs = [gif for gif in gif_files if gif not in self.custom_order]
            
            # 合并结果：先显示自定义顺序的，再显示其他的
            gif_files = self.custom_order + other_gifs
        
        return gif_files
    
    def get_default_gif(self):
        """获取默认GIF动画路径"""
        if not self.default_gif:
            gif_files = self.get_gif_list()
            if gif_files:
                self.default_gif = gif_files[0]
            else:
                raise FileNotFoundError("没有找到任何GIF动画文件")
        return self.default_gif
    
    def add_gif(self, gif_path):
        """添加新的GIF动画"""
        if not os.path.exists(gif_path):
            raise FileNotFoundError(f"文件不存在: {gif_path}")
        
        # 复制GIF文件到资源目录
        filename = os.path.basename(gif_path)
        target_path = self.user_gif_dir / filename
        
        # 如果文件已存在，直接返回
        if target_path.exists():
            return str(target_path)
        
        # 复制文件
        shutil.copy2(gif_path, target_path)
        
        return str(target_path)
    
    def remove_gif(self, gif_path):
        """删除GIF动画"""
        # 标准化路径
        gif_path = gif_path.replace('\\', '/')
        
        # 尝试通过路径删除
        if os.path.exists(gif_path):
            # 如果在自定义顺序中，先移除
            for path in self.custom_order[:]:
                if path.replace('\\', '/') == gif_path or os.path.basename(path) == os.path.basename(gif_path):
                    self.custom_order.remove(path)
            
            self.save_config()
                
            # 删除文件
            os.remove(gif_path)
            
            # 重置默认GIF（如果需要）
            if self.default_gif == gif_path:
                self.default_gif = None
            
            return True
            
        # 如果直接路径不存在，尝试通过文件名匹配
        filename = os.path.basename(gif_path)
        
        # 在所有目录中查找
        for directory in [self.gif_dir, self.user_gif_dir]:
            target = directory / filename
            if target.exists():
                # 如果在自定义顺序中，先移除
                for path in self.custom_order[:]:
                    if os.path.basename(path) == filename:
                        self.custom_order.remove(path)
                
                self.save_config()
                    
                # 删除文件
                os.remove(target)
                
                # 重置默认GIF（如果需要）
                if self.default_gif and os.path.basename(self.default_gif) == filename:
                    self.default_gif = None
                
                return True
                
        return False
    
    def set_custom_order(self, order):
        """设置自定义GIF播放顺序"""
        self.custom_order = order
        self.save_config()


class PetWindow(QWidget):
    def __init__(self):
        super().__init__()
        # 设置窗口属性
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  # 无边框
            Qt.WindowType.Tool |                 # 工具窗口
            Qt.WindowType.WindowStaysOnTopHint   # 置顶
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 透明背景
        
        # 初始化GIF管理器
        self.gif_manager = GifManager()
        
        # 设置窗口大小
        self.resize(150, 150)  # 默认大小为150×150
        
        # 创建标签用于显示GIF
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.resize(self.size())
        
        # 初始化动画
        self.movie = QMovie()
        self.movie.finished.connect(self.movie.start)  # 循环播放
        self.label.setMovie(self.movie)
        
        # 鼠标拖动相关变量
        self.is_dragging = False
        self.drag_position = QPoint()
        
        # 自动切换GIF动画的定时器和设置
        self.auto_switch_enabled = False
        self.auto_switch_interval = 2 * 60 * 1000  # 默认2分钟切换一次（毫秒）
        self.auto_switch_timer = QTimer(self)
        self.auto_switch_timer.timeout.connect(self.switch_to_next_gif)
        
        # 初始化右键菜单
        self.context_menu = QMenu(self)
        self.init_context_menu()
        
        # 加载默认动画
        try:
            self.load_animation(self.gif_manager.get_default_gif())
        except FileNotFoundError:
            print("警告：没有找到GIF动画文件，请将GIF文件放入resources/gifs目录")
    
    def init_context_menu(self):
        """初始化右键菜单"""
        # 添加动画切换子菜单
        self.animations_menu = self.context_menu.addMenu("切换动画")
        self.update_animation_menu(self.animations_menu)
        
        # 添加GIF管理子菜单
        gif_manage_menu = self.context_menu.addMenu("GIF管理")
        
        # 导入GIF
        import_action = gif_manage_menu.addAction("导入GIF")
        import_action.triggered.connect(self.import_gif)
        
        # 删除当前GIF
        delete_action = gif_manage_menu.addAction("删除当前GIF")
        delete_action.triggered.connect(self.delete_current_gif)
        
        # 自定义GIF顺序
        order_action = gif_manage_menu.addAction("自定义播放顺序")
        order_action.triggered.connect(self.customize_gif_order)
        
        # 添加自动切换GIF功能
        auto_switch_menu = self.context_menu.addMenu("自动切换")
        
        # 启用/禁用自动切换
        self.auto_switch_action = auto_switch_menu.addAction("启用自动切换")
        self.auto_switch_action.setCheckable(True)
        self.auto_switch_action.setChecked(self.auto_switch_enabled)
        self.auto_switch_action.triggered.connect(self.toggle_auto_switch)
        
        # 设置切换时间间隔
        intervals = [("30秒", 30), ("1分钟", 60), ("2分钟", 120), ("5分钟", 300)]
        interval_menu = auto_switch_menu.addMenu("切换间隔")
        for name, seconds in intervals:
            action = interval_menu.addAction(name)
            action.triggered.connect(lambda checked, s=seconds: self.set_auto_switch_interval(s))
        
        # 添加调整大小子菜单
        size_menu = self.context_menu.addMenu("调整大小")
        for size in [50, 100, 150, 200]:
            action = size_menu.addAction(f"{size}x{size}")
            # 设置150为默认选中状态
            if size == 150:
                action.setCheckable(True)
                action.setChecked(True)
            action.triggered.connect(lambda checked, s=size: self.resize_pet(s))
        
        # 添加其他菜单项
        self.context_menu.addSeparator()
        exit_action = self.context_menu.addAction("退出")
        exit_action.triggered.connect(self.close)
    
    def update_animation_menu(self, menu):
        """更新动画菜单"""
        menu.clear()
        for gif_name in self.gif_manager.get_gif_list():
            action = menu.addAction(os.path.basename(gif_name))
            action.triggered.connect(lambda checked, name=gif_name: self.load_animation(name))
    
    def import_gif(self):
        """导入GIF文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择GIF文件", "", "GIF文件 (*.gif)"
        )
        if file_path:
            try:
                # 添加GIF到管理器
                new_gif_path = self.gif_manager.add_gif(file_path)
                # 加载新添加的GIF
                self.load_animation(new_gif_path)
                # 更新菜单
                self.update_animation_menu(self.animations_menu)
            except Exception as e:
                print(f"导入GIF文件失败: {e}")
    
    def delete_current_gif(self):
        """删除当前GIF"""
        current_gif = self.movie.fileName()
        if not current_gif:
            QMessageBox.warning(self, "警告", "没有正在播放的GIF文件")
            return
        
        # 获取当前GIF的绝对路径，并标准化格式
        current_gif = os.path.abspath(current_gif).replace('\\', '/')
        current_filename = os.path.basename(current_gif)
            
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除当前GIF文件 '{current_filename}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 获取GIF列表(删除前)
            gif_list = self.gif_manager.get_gif_list()
            # 转换所有路径为绝对路径并标准化
            gif_list = [os.path.abspath(gif).replace('\\', '/') for gif in gif_list]
            
            if len(gif_list) <= 1:
                QMessageBox.warning(self, "警告", "至少保留一个GIF文件，无法删除")
                return
            
            # 打印调试信息
            print(f"当前GIF: {current_gif}")
            print(f"GIF列表: {gif_list}")
                
            try:
                # 通过文件名匹配而不是完整路径
                found = False
                current_index = 0
                
                for i, gif_path in enumerate(gif_list):
                    if os.path.basename(gif_path) == current_filename:
                        current_index = i
                        found = True
                        break
                
                if not found:
                    raise ValueError(f"找不到文件名为 {current_filename} 的GIF")
                
                # 先切换到其他GIF再删除
                next_index = (current_index + 1) % len(gif_list) if len(gif_list) > 1 else 0
                next_gif = gif_list[next_index]
                
                # 立即停止当前动画并切换
                self.movie.stop()
                self.movie.setFileName('')  # 清空当前文件
                
                # 等待一小段时间确保文件被释放
                QTimer.singleShot(100, lambda: self._complete_deletion(current_gif, next_gif))
            except ValueError as e:
                print(f"删除GIF时出错：{e}")
                print(f"当前GIF: {current_gif}")
                print(f"GIF列表: {gif_list}")
                QMessageBox.warning(self, "错误", f"无法找到当前GIF文件: {current_filename}")
                
    def _complete_deletion(self, gif_to_delete, next_gif):
        """完成GIF删除过程"""
        try:
            # 删除GIF
            if self.gif_manager.remove_gif(gif_to_delete):
                # 更新菜单
                self.update_animation_menu(self.animations_menu)
                
                # 加载下一个GIF
                self.load_animation(next_gif)
                
                QMessageBox.information(self, "成功", "GIF文件已成功删除")
            else:
                QMessageBox.warning(self, "失败", "GIF文件删除失败")
                
                # 如果删除失败，仍然切换到下一个GIF
                self.load_animation(next_gif)
        except Exception as e:
            print(f"完成删除过程时出错: {e}")
            # 确保切换到下一个GIF
            self.load_animation(next_gif)
    
    def customize_gif_order(self):
        """自定义GIF播放顺序"""
        gif_list = self.gif_manager.get_gif_list()
        if not gif_list:
            QMessageBox.warning(self, "警告", "没有可用的GIF文件")
            return
        
        # 准备GIF列表（只显示文件名）
        gif_names = [os.path.basename(gif) for gif in gif_list]
        gif_name_to_path = {os.path.basename(gif): gif for gif in gif_list}
        
        # 显示排序对话框
        text, ok = QInputDialog.getText(
            self, 
            "自定义播放顺序", 
            "请输入GIF文件的序号，用逗号分隔（例如：2,1,3）\n当前顺序：\n" + "\n".join([f"{i+1}. {name}" for i, name in enumerate(gif_names)]),
            text=",".join([str(i+1) for i in range(len(gif_names))])
        )
        
        if ok and text:
            try:
                # 解析用户输入的序号
                indices = [int(idx.strip()) - 1 for idx in text.split(',')]
                
                # 验证序号是否有效
                if any(idx < 0 or idx >= len(gif_names) for idx in indices):
                    QMessageBox.warning(self, "错误", "序号无效，请输入1到{}的数字".format(len(gif_names)))
                    return
                
                # 检查是否所有GIF都被包含
                if len(indices) != len(gif_names):
                    QMessageBox.warning(self, "错误", "序号数量不匹配，请确保包含所有GIF文件")
                    return
                
                # 创建新的顺序
                new_order = [gif_list[idx] for idx in indices]
                
                # 保存新顺序
                self.gif_manager.set_custom_order(new_order)
                
                # 更新菜单
                self.update_animation_menu(self.animations_menu)
                
                QMessageBox.information(self, "成功", "GIF播放顺序已更新")
                
            except ValueError:
                QMessageBox.warning(self, "错误", "请输入有效的数字序号")
    
    def resize_pet(self, size):
        """调整宠物大小"""
        self.resize(size, size)
        self.label.resize(size, size)
        
        # 重新加载动画以适应新大小
        current_path = self.movie.fileName()
        if current_path:
            self.load_animation(current_path)
            
        # 更新菜单项选中状态
        size_menu = [action for action in self.context_menu.actions() if action.menu() and "调整大小" in action.text()][0].menu()
        for action in size_menu.actions():
            action_size = int(action.text().split('x')[0])
            action.setChecked(action_size == size)
    
    def toggle_auto_switch(self, enabled):
        """切换自动切换GIF功能的启用状态"""
        self.auto_switch_enabled = enabled
        if enabled:
            self.auto_switch_timer.start(self.auto_switch_interval)
            print(f"已启用自动切换GIF功能，间隔: {self.auto_switch_interval // 1000}秒")
        else:
            self.auto_switch_timer.stop()
            print("已禁用自动切换GIF功能")
    
    def set_auto_switch_interval(self, seconds):
        """设置自动切换的时间间隔（秒）"""
        # 将秒转换为毫秒，并确保是整数
        self.auto_switch_interval = int(seconds * 1000)
        print(f"已设置自动切换间隔为: {seconds}秒")
        
        # 如果定时器已启动，重新设置时间
        if self.auto_switch_enabled:
            self.auto_switch_timer.start(self.auto_switch_interval)
    
    def switch_to_next_gif(self):
        """切换到下一个GIF动画"""
        gif_list = self.gif_manager.get_gif_list()
        if not gif_list:
            return
            
        # 获取当前GIF的文件名
        current_gif = self.movie.fileName()
        
        if current_gif and current_gif in gif_list:
            # 找到当前GIF在列表中的位置
            current_index = gif_list.index(current_gif)
            # 计算下一个GIF的索引
            next_index = (current_index + 1) % len(gif_list)
        else:
            # 如果当前GIF不在列表中，随机选择一个
            next_index = random.randint(0, len(gif_list) - 1)
        
        # 加载下一个GIF
        next_gif = gif_list[next_index]
        self.load_animation(next_gif)
        print(f"已自动切换到下一个GIF动画: {os.path.basename(next_gif)}")
    
    def load_animation(self, gif_path):
        """加载GIF动画"""
        # 标准化路径格式
        gif_path = gif_path.replace('\\', '/')
        
        if not os.path.exists(gif_path):
            print(f"错误：GIF文件不存在 - {gif_path}")
            return
            
        self.movie.stop()
        self.movie.setFileName(gif_path)
        self.movie.setScaledSize(self.size())
        self.movie.start()
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        elif event.button() == Qt.MouseButton.RightButton:
            self.context_menu.exec(event.globalPosition().toPoint())
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件"""
        if self.is_dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.auto_switch_timer.stop()  # 停止定时器
        self.movie.stop()
        super().closeEvent(event)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, pet_window):
        """初始化系统托盘图标"""
        super().__init__()
        self.pet_window = pet_window
        
        # 创建托盘图标菜单
        self.menu = QMenu()
        self.init_menu()
        
        # 设置托盘图标
        self.setup_icon()
        self.setContextMenu(self.menu)
        
        # 连接信号
        self.activated.connect(self.on_tray_icon_activated)
    
    def setup_icon(self):
        """设置托盘图标"""
        # 直接指定到doraemon.jpg
        doraemon_icon = Path(__file__).parent.parent / "resources" / "icons" / "doraemon.jpg"
        
        # 如果指定的图标存在，直接使用
        if doraemon_icon.exists():
            self.setIcon(QIcon(str(doraemon_icon)))
            print(f"已加载指定托盘图标: {doraemon_icon}")
            return
            
        # 作为备选，搜索图标目录
        icon_dir = Path(os.path.expanduser("~")) / "Desktop" / "线条小狗桌面宠物" / "desktop_pet" / "resources" / "icons"
        
        # 检查目录是否存在
        if not icon_dir.exists():
            # 如果指定目录不存在，则使用相对路径
            icon_dir = Path(__file__).parent.parent / "resources" / "icons"
            if not icon_dir.exists():
                icon_dir.mkdir(parents=True, exist_ok=True)
        
        # 查找所有图片文件，优先搜索jpg文件
        jpg_files = list(icon_dir.glob("*.jpg"))
        if jpg_files:
            self.setIcon(QIcon(str(jpg_files[0])))
            print(f"已加载托盘图标(jpg): {jpg_files[0]}")
            return
            
        # 其他格式的图片文件
        other_icon_files = list(icon_dir.glob("*.png")) + list(icon_dir.glob("*.ico")) + list(icon_dir.glob("*.gif"))
        if other_icon_files:
            self.setIcon(QIcon(str(other_icon_files[0])))
            print(f"已加载托盘图标: {other_icon_files[0]}")
            return
            
        # 如果没有找到图片文件，会回退到创建默认图标的方式
        self.create_default_icon()
    
    def create_default_icon(self):
        """创建默认图标"""
        # 创建一个16x16的像素图
        icon_pixmap = QPixmap(16, 16)
        icon_pixmap.fill(Qt.GlobalColor.transparent)  # 设置透明背景
        
        # 创建绘图器
        painter = QPainter(icon_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 画一个可爱的小狗图标（简单的圆形）
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#F5D0A9")))  # 浅棕色
        painter.drawEllipse(2, 2, 12, 12)  # 画一个圆形
        
        # 画眼睛
        painter.setBrush(QBrush(QColor("#000000")))
        painter.drawEllipse(5, 6, 2, 2)  # 左眼
        painter.drawEllipse(9, 6, 2, 2)  # 右眼
        
        # 画嘴巴
        painter.setPen(QColor("#000000"))
        painter.drawLine(6, 10, 10, 10)
        
        painter.end()
        
        # 设置图标
        self.setIcon(QIcon(icon_pixmap))
        print("使用默认托盘图标")
    
    def init_menu(self):
        """初始化托盘菜单"""
        # 显示/隐藏
        show_action = self.menu.addAction("显示")
        show_action.triggered.connect(self.pet_window.show)
        
        hide_action = self.menu.addAction("隐藏")
        hide_action.triggered.connect(self.pet_window.hide)
        
        # 分隔符
        self.menu.addSeparator()
        
        # 退出
        exit_action = self.menu.addAction("退出")
        exit_action.triggered.connect(self.quit_application)
    
    def on_tray_icon_activated(self, reason):
        """托盘图标被激活时的处理"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.pet_window.isVisible():
                self.pet_window.hide()
            else:
                self.pet_window.show()
    
    def quit_application(self):
        """退出应用程序"""
        self.hide()
        self.pet_window.close()
        QApplication.quit()


def ensure_gif_exists():
    """确保至少有一个GIF文件"""
    from PIL import Image, ImageDraw
    from io import BytesIO
    
    gif_manager = GifManager()
    if not gif_manager.get_gif_list():
        # 如果没有GIF文件，创建一个简单的GIF
        try:
            # 创建一个简单的GIF，大小设为150×150
            frames = []
            size = 150  # 修改默认大小为150×150
            for i in range(10):
                # 创建帧
                img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                # 绘制狗狗头部，等比例放大
                center = size // 2
                radius = int(size * 0.4)  # 头部半径
                draw.ellipse([center - radius, center - radius, 
                              center + radius, center + radius], 
                             fill=(245, 208, 169, 255))
                
                # 绘制眼睛
                eye_size = max(1, int(size * 0.06))
                eye_offset = (i % 5) - 2  # 眼睛位置偏移，模拟眨眼
                eye_y = center - int(size * 0.05) + eye_offset
                left_eye_x = center - int(size * 0.15)
                right_eye_x = center + int(size * 0.15) - eye_size
                
                draw.ellipse([left_eye_x, eye_y, left_eye_x + eye_size, eye_y + eye_size], 
                             fill=(0, 0, 0, 255))
                draw.ellipse([right_eye_x, eye_y, right_eye_x + eye_size, eye_y + eye_size], 
                             fill=(0, 0, 0, 255))
                
                # 绘制嘴巴
                mouth_y = center + int(size * 0.15)
                mouth_left = center - int(size * 0.1)
                mouth_right = center + int(size * 0.1)
                mouth_width = max(1, int(size * 0.03))
                
                draw.line([mouth_left, mouth_y, mouth_right, mouth_y], 
                         fill=(0, 0, 0, 255), width=mouth_width)
                
                frames.append(img)
            
            # 保存GIF
            gif_path = gif_manager.user_gif_dir / "default_dog.gif"
            frames[0].save(
                gif_path,
                format='GIF',
                append_images=frames[1:],
                save_all=True,
                duration=100,  # 100ms每帧
                loop=0         # 无限循环
            )
            print(f"已创建默认GIF动画: {gif_path}")
        except Exception as e:
            print(f"无法创建默认GIF: {e}")


def main():
    """主程序入口"""
    # 确保至少有一个GIF文件
    ensure_gif_exists()
    
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setQuitOnLastWindowClosed(False)
    
    # 创建宠物窗口
    pet_window = PetWindow()
    pet_window.show()
    
    # 创建系统托盘图标
    tray_icon = TrayIcon(pet_window)
    tray_icon.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == '__main__':
    main() 